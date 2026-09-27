#!/usr/bin/env python3
"""LLM director — turn a written brief into a validated, frozen timeline.json.

Modes (the three ways to use the skill):
  1. invent   --mode invent   --brief brief.md      LLM composes the whole
     timeline from the brief using the 8 shipped scene archetypes.
  3. fill     --mode fill     --brief brief.md --template blank.json
     LLM (or you, by hand) fills every <SLOT> in the shipped blank template.
  (mode 2, the blueprint path, is an interactive agent session — see
   references/blueprints.md; it is not a director.py mode.)
  Test/offline: --mode from-file candidate.json — run any authored JSON
  through the same validation + repair + freeze pipeline (no LLM needed).

The LLM NEVER produces pixels. It produces JSON; the deterministic
renderer/audio pipeline produces pixels. Output is frozen: timeline.json +
director_meta.json (model, seed, prompt hash, attempts) — re-runs of the
renderer are byte-stable because timing lives only in the frozen file.

Runtime: any OpenAI-compatible server — Ollama, vLLM, LM Studio, MLX serve,
llama.cpp server. --api ollama additionally uses /api/chat + format:json.
Deterministic: temperature 0 + fixed --seed.

  python3 director.py --model qwen3:14b --mode invent --brief brief.md
  python3 director.py --model qwen3:14b --mode fill --template blank.json --brief brief.md
  python3 director.py --mode from-file my_idea.json --out timeline.json
  # then: python3 audio.py && python3 render.py stills 0.8,3.4,... && python3 render.py video && ./build.sh
"""
import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate as V

HERE = os.path.dirname(os.path.abspath(__file__))

CATALOG = """You compose motion-graphics launch reels as a strict JSON timeline.
Root: {"name","w":1920,"h":1080,"fps":60,"bpm":120,"theme":{accent,hot,bg,cream},
"hud":{brand,brand2,series,line},"timeline":[scenes]}
Scene: {"scene":TYPE,"dur":SECONDS,"name":"HUD LABEL","slams":[extra impact
offsets],"p":{params}}. HARD TIMING: dur values must land every scene boundary
on the beat grid (bpm 120 -> 0.5s steps) and total ~15s; last scene endcard.
SCENES and their params:
- terminal {prompt,cmd,title,rows:[[label,value]x4],progress{label,pct}}
- kinetic {intro (<=54 chars!), words:[[WORD,offset,("ACCENT"|"")]x3,(note),(stat)]}
- cards {header,kicker,cards:[3x {tag,big:{from,to,fmt:int|x|k|d},unit,sub (<=33 chars!),label,viz:bars|kv|ctx}],ticker{label,items[]}}
- counter {prompt,promptArg,kicker,big:{from,to,fmt},unit,sub,tagline,typing (one line)}
- chart {line,grow:[8 increasing numbers],max,months:[8],label,sub,impact:1.8,seed:1}
- quote {text,author,handle?,meta?,slam}
- split {header,cols:[2x {title,rows[],accent?}]}
- endcard {tag,word1,word2,serif,url,footer}
Style: dark bg #0b0b0c, accent #e85d04, cream text; mono uppercase tech labels,
serif italic emotional lines. Concrete numbers beat adjectives. Every claim a
viewer could fact-check should also appear in a "sources" map you emit:
{"claim text": "https://source"}. Answer with ONE JSON object, nothing else."""


def http_json(url, payload, timeout=600):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:400]
        raise SystemExit(f"director: {url} -> HTTP {e.code}: {body}\n"
                         "is the server up? check --base-url and --model (ollama list / /v1/models)")


def call_llm(args, messages):
    """One chat call, JSON-mode, temp 0, fixed seed. Returns text."""
    if args.api == "ollama":
        out = http_json(args.base_url.rstrip("/") + "/api/chat",
                        {"model": args.model, "messages": messages, "stream": False,
                         "format": "json",
                         "options": {"temperature": 0, "seed": args.seed}})
        return out.get("message", {}).get("content", "")
    payload = {"model": args.model, "messages": messages, "temperature": 0, "seed": args.seed}
    if not args.no_response_format:
        payload["response_format"] = {"type": "json_object"}
    try:
        out = http_json(args.base_url.rstrip("/") + "/v1/chat/completions", payload)
    except SystemExit as e:
        msg = str(e)
        if "response_format" in msg and not args.no_response_format:  # older llama.cpp/vLLM
            args.no_response_format = True
            print("director: server rejected response_format — retrying without it")
            return call_llm(args, messages)
        raise
    return out["choices"][0]["message"]["content"]


def extract_json(text):
    """Parse model output: plain JSON, fenced JSON, or first balanced {...}."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    start = text.find("{")
    if start < 0:
        raise ValueError("no JSON object in model output")
    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:i + 1])
    raise ValueError("unbalanced JSON in model output")


def check(doc, tmp, allow_custom):
    json.dump(doc, open(tmp, "w"), indent=1)
    errs, warns, n, t = V.validate(tmp, allow_custom=allow_custom, allow_slots=False)
    return errs, warns, n, t


def repair(args, doc, errs, user_msg, tmp):
    """One round trip: give the model its JSON + the validator errors."""
    msgs = [{"role": "system", "content": CATALOG + "\nReturn ONLY the corrected JSON."},
            {"role": "user", "content": user_msg},
            {"role": "assistant", "content": json.dumps(doc)},
            {"role": "user", "content": "The validator rejected it:\n" + "\n".join(errs) +
                                        "\nFix every error, change nothing else. Return the full corrected JSON."}]
    try:
        fixed = extract_json(call_llm(args, msgs))
    except Exception as e:
        print("director: repair failed to parse:", e)
        return None
    errs2, warns, n, t = check(fixed, tmp, args.allow_custom)
    return fixed if not errs2 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["invent", "fill", "from-file"], required=True)
    ap.add_argument("--brief", help="markdown brief (invent/fill)")
    ap.add_argument("--template", default=os.path.join(HERE, "blank.json"), help="blank.json for fill")
    ap.add_argument("--from-file", help="authored timeline JSON (from-file mode)")
    ap.add_argument("--out", default="timeline.json")
    ap.add_argument("--model", default="qwen3:14b")
    ap.add_argument("--base-url", default=os.environ.get("LLM_BASE_URL", "http://localhost:11434"))
    ap.add_argument("--api", choices=["openai", "ollama"], default=os.environ.get("LLM_API", "openai"))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--max-repair", type=int, default=1)
    ap.add_argument("--allow-custom", action="store_true", help="accept defineScene types from scene_custom.js")
    ap.add_argument("--allow-slots", action="store_true", help="don't fail on unfilled slots")
    ap.add_argument("--no-response-format", action="store_true")
    args = ap.parse_args()

    brief = open(args.brief).read() if args.brief and os.path.exists(args.brief) else (args.brief or "")
    tmp = args.out + ".candidate.json"
    attempts, used_repair = 0, False

    if args.mode == "from-file":
        doc = json.load(open(args.from_file))
    else:
        if not brief:
            raise SystemExit("director: --brief required for invent/fill")
        if args.mode == "invent":
            user = f"Brief:\n{brief}\n\nCompose a ~15s reel. Return the timeline JSON only."
        else:
            tpl = open(args.template).read()
            user = (f"Fill EVERY <SLOT> in this template from the brief. Keep the structure, "
                    f"every key, every dur, and the scene order EXACTLY as they are.\n\nBrief:\n{brief}\n\n"
                    f"Template:\n{tpl}")
        msgs = [{"role": "system", "content": CATALOG}, {"role": "user", "content": user}]
        doc = extract_json(call_llm(args, msgs))

    errs, warns, n, t = check(doc, tmp, args.allow_custom)
    tries = 0
    while errs and tries < args.max_repair and args.mode != "from-file":
        used_repair, tries = True, tries + 1
        print("director: %d validation errors -> repair round %d" % (len(errs), tries))
        fixed = repair(args, doc, errs, user if args.mode != "from-file" else "", tmp)
        if fixed is None:
            break
        doc = fixed
        errs, warns, n, t = check(doc, tmp, args.allow_custom)
    if errs and not args.allow_slots:
        for e in errs:
            print("ERROR:", e)
        print(f"director: REJECTED — candidate kept at {tmp}")
        sys.exit(1)

    # freeze
    if args.mode == "fill" or args.allow_slots:
        doc.pop("_comment", None)
    json.dump(doc, open(args.out, "w"), indent=1)
    meta_path = os.path.splitext(args.out)[0] + "_meta.json"
    meta = {"created": datetime.now(timezone.utc).isoformat(timespec="seconds"),            "mode": args.mode, "model": args.model if args.mode != "from-file" else None,
            "base_url": args.base_url if args.mode != "from-file" else None,
            "api": args.api if args.mode != "from-file" else None,
            "seed": args.seed, "repair_used": used_repair,
            "brief_sha256": hashlib.sha256(brief.encode()).hexdigest()[:16] if brief else None,
            "candidate_json_sha256": hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()[:16]}
    json.dump(meta, open(meta_path, "w"), indent=1)
    for w in warns:
        print("WARN:", w)
    if os.path.exists(tmp):
        os.remove(tmp)
    print("frozen %s (%d scenes, %.2fs) + %s" % (args.out, n, t, os.path.basename(meta_path)))
    print("next: python3 audio.py && python3 render.py stills 0.8,3.4,5.6,8.5,11.9,14.0")


if __name__ == "__main__":
    main()
