#!/usr/bin/env python3
"""LLM director — turn a written brief into a validated, frozen timeline.json.

Modes (the three ways to use the skill):
  1. invent   --mode invent   --brief brief.md      LLM composes the whole
     timeline from the brief. By default it ALSO writes a bespoke
     scene_custom.js with --bespoke N NEW scene types invented for this
     video (the uniqueness guarantee — every reel draws its own scenes),
     syntax-checked with node, validated, and probed with real stills that
     must contain pixels or the JS is repaired and re-rendered.
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


BESPOKE_SYS = """You write NEW scene types for a deterministic motion-graphics reel
engine. You output ONE JavaScript file and nothing else — no prose, no fences.

The file is scene_custom.js. It is loaded by the reel player before the
timeline is built and runs in the player's script scope. Exact shape:

  defineScene('name', (lt, d, p) => { /* draw ONE frame at time lt */ });

- name: lowercase [a-z0-9_]; never a built-in (terminal, kinetic, cards,
  counter, chart, quote, split, endcard — overriding them is refused).
- lt = seconds since the scene started (0..d); d = scene duration in seconds;
  p = a params object you document in a leading comment:
  // PARAMS name: {"title":"string","items":["..."],"seed":7}
- Draw with CSS-pixel coordinates (a DPR transform is already applied).
- NEVER: Math.random (use rng(seed) for deterministic noise), document,
  fetch, console.log, window timers; never mutate C/SC/CUTS/IMPACTS/DUR.
- All motion is relative to d: entrance = prog(lt, 0, 0.3). The scene must
  draw clearly and move for its FULL duration, not just its first 0.5s.
- Glow: ctx.shadowBlur = 24 * DPR (the transform does not scale it).
- Safe area: stay inside 96px left/right and 54px top/bottom of 1920x1080;
  HUD strips live there. Measure the FINAL string: tw(s, font) must fit.
- HUD bands are RESERVED: the template draws a top HUD strip at y=40..110 and
  a bottom HUD strip at y>H-80. Never draw text or art there. Scene titles
  belong at y >= 130 (e.g. 150), never at y < 110 or y > H-80.
- Budget: 60fps, hundreds of draws fine, 10k particles are not.

HELPERS IN SCOPE (use them; do not redefine them):
  W,H,DPR,FPS                              canvas size / device px ratio / fps
  C.or C.hot C.cream C.mute C.bg C.surf C.line      theme colors (no C.text)
  A(alpha) / Hh(alpha)                     accent / hot color as rgba string
  ACC / HOTC                               accent / hot hex strings
  prog(t,a,b)                              eased 0->1 ramp of t across [a,b]
  eOutExpo eOutCubic eInOut eOutBack eIn   easings (0-1 -> 0-1)
  clamp(x,a,b)  lerp(a,b,t)
  txt(s,x,y,{f,col,a,align,ls,glow,gcol,base})   text; align:'center'|'right';
                                                glow in px; default col C.cream
  tw(s,f,ls)                               text width in px
  typed(s,t,a,b)                           typing reveal of s over [a,b]
  cursor(x,y,t,h,w,col)                    blinking block cursor
  rrect(x,y,w,h,r)                         rounded-rect path (then fill/stroke)
  rect(x,y,w,h,col,a)                      filled rect
  wipeLine(s,x,y,wd,p,{f,col,a,ls})        reveal text left->right, p 0-1
  dashed(x1,y1,x2,y2,p,a)                  animated dashed line drawn in
  rng(seed)                                deterministic PRNG: f() -> 0-1
  fmt(n) -> '1,234';  bigFmt({from,to,fmt},v) with fmt 'int'|'x'|'k'|'d'
  SANS='"DM Sans"' MONO='"DM Mono"' SERIF='"Instrument Serif"' DISP='"Russo One"'
  fonts look like: f=`700 64px ${SANS}`; italic serif: f=`italic 40px ${SERIF}`

STYLE OF THE HOUSE (match it, don't copy a layout):
  near-black background, burnt-orange accent, cream text, mono uppercase
  small labels, one big display/serif moment, thin 1-2px strokes, glow used
  sparingly on accents. The scene must feel like it belongs in this reel and
  like it belongs to NO OTHER video: derive the metaphor from the brief's own
  nouns and verbs (a courier reel draws routes; a battery reel draws cells;
  a library reel draws stacked spines). Do NOT re-implement one of the eight
  built-ins with different colors, and do NOT draw generic bars-and-cards.

WORKED EXAMPLE (shape + style reference — invent something new):

  // PARAMS orbit: {"title":"brand","items":["a","b","c"],"seed":7}
  defineScene('orbit', (lt, d, p) => {
    const cx=W/2, cy=H/2, r=260, grow=eOutExpo(prog(lt,0,1.0));
    ctx.save();
    ctx.strokeStyle=A(0.25*grow); ctx.lineWidth=2;
    ctx.beginPath(); ctx.arc(cx,cy,r*grow,0,7); ctx.stroke();
    const rnd=rng(p.seed||7);
    (p.items||[]).forEach((it,i)=>{
      const a=-Math.PI/2+i*2*Math.PI/p.items.length+lt*0.9+rnd()*0.1;
      const x=cx+Math.cos(a)*r*grow, y=cy+Math.sin(a)*r*grow*0.55;
      ctx.shadowBlur=24*DPR; ctx.shadowColor=A(0.9);
      ctx.fillStyle=i%2?ACC:C.cream;
      ctx.beginPath(); ctx.arc(x,y,10,0,7); ctx.fill();
      txt(it.toUpperCase(),x+16,y+6,{f:`500 20px ${MONO}`,col:C.cream,ls:'2px'});
    });
    ctx.restore();
    txt((p.title||'').toUpperCase(),cx,cy+8,{f:`800 44px ${SANS}`,col:C.cream,align:'center',ls:'4px'});
  });

Return ONLY the JavaScript file contents."""


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


def call_llm_js(args, messages):
    """Chat call WITHOUT JSON mode — for raw JavaScript output."""
    if args.api == "ollama":
        out = http_json(args.base_url.rstrip("/") + "/api/chat",
                        {"model": args.model, "messages": messages, "stream": False,
                         "options": {"temperature": 0, "seed": args.seed}})
        return out.get("message", {}).get("content", "")
    out = http_json(args.base_url.rstrip("/") + "/v1/chat/completions",
                    {"model": args.model, "messages": messages, "temperature": 0, "seed": args.seed})
    return out["choices"][0]["message"]["content"]


def strip_js(text):
    t = text.strip()
    m = re.match(r"^```(?:js|javascript)?\s*(.*?)\s*```$", t, re.S)
    return m.group(1) if m else t


def node_check(js_path):
    """Syntax gate. (ok, msg). Passes if node is missing (validate.py's regex
    scan + the render probe are the real gates)."""
    import subprocess
    try:
        r = subprocess.run(["node", "--check", js_path], capture_output=True, text=True, timeout=30)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True, "node unavailable — syntax check skipped"
    return r.returncode == 0, (r.stderr or r.stdout)[:800]


def bespoke_times(doc, names):
    """{name: [(t0+0.35d, t0+0.75d), ...]} absolute probe times per bespoke scene."""
    t0, out = 0.0, {}
    for s in doc.get("timeline", []):
        d = float(s["dur"])
        if s.get("scene") in names:
            out.setdefault(s["scene"], []).append((round(t0 + 0.35 * d, 2), round(t0 + 0.75 * d, 2)))
        t0 += d
    return out


def probe_bespoke(out_dir, timeline_abs, doc, names):
    """Render real DPR=1 stills of each bespoke scene and verify it DREW
    something (center crop is away from HUD strips; blank = <120 lit px).
    Returns (ok, report). Infrastructure gaps return ok=True with a note so
    the director never blocks on a machine that cannot render."""
    import subprocess
    try:
        import numpy as np
    except ImportError:
        return True, "probe skipped — numpy not installed (render stills manually!)"
    if not all(os.path.exists(os.path.join(out_dir, f)) for f in ("reel.html", "render.py")):
        return True, "probe skipped — reel.html/render.py not beside the timeline (render stills manually!)"
    plan = bespoke_times(doc, names)
    missing = set(names) - set(plan)
    if missing:
        return False, "timeline does not use bespoke scenes: %s" % ", ".join(sorted(missing))
    env = dict(os.environ, DPR="1", TIMELINE=timeline_abs)
    times = sorted({t for pairs in plan.values() for pair in pairs for t in pair})
    r = subprocess.run([sys.executable, "render.py", "stills", ",".join("%.2f" % t for t in times)],
                       cwd=out_dir, capture_output=True, text=True, timeout=1200, env=env)
    if r.returncode != 0:
        return False, "render.py stills failed:\n" + (r.stderr or "")[-900:]
    h, w = int(doc.get("h", 1080)), int(doc.get("w", 1920))
    per_scene = {}
    for name, pairs in plan.items():
        blanks = []
        for pair in pairs:
            bad_here = []
            for t in pair:
                png = os.path.join(out_dir, "stills", "t%05.2f.png" % t)
                try:
                    p = subprocess.run(["ffmpeg", "-v", "error", "-i", png,
                                        "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                       capture_output=True, timeout=60)
                    arr = np.frombuffer(p.stdout, dtype=np.uint8).reshape(h, w, 3).astype(np.float32)
                    lum = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
                    crop = lum[int(h * 0.12):int(h * 0.88), int(w * 0.04):int(w * 0.96)]
                    lit = int((crop > 80).sum())  # content frames: ~6000+ px; blank frames: 0
                    if lit < 120:
                        bad_here.append("t=%.2f (only %d lit px)" % (t, lit))
                except Exception as e:
                    bad_here.append("t=%.2f unreadable: %s" % (t, e))
            if bad_here:
                blanks.append(" and ".join(bad_here))
        # fail only if EVERY sample pair came back blank (one pair may land
        # on a fade/flash); one bad pair is a warning
        if len(blanks) == len(pairs) and pairs:
            per_scene[name] = "BLANK: " + "; ".join(blanks)
        elif blanks:
            per_scene[name] = "WARN: partially blank: " + "; ".join(blanks)
    fails = {k: v for k, v in per_scene.items() if v.startswith("BLANK")}
    if fails:
        return False, "\n".join(fails.values())
    warns = [v for v in per_scene.values() if v.startswith("WARN")]
    return True, ("probe ok: bespoke scenes " + ", ".join(sorted(names)) + " drew real pixels" +
                  ((" | " + "; ".join(warns)) if warns else ""))


def gen_bespoke(args, brief, js_path):
    """LLM writes scene_custom.js for THIS video; node --check + defineScene
    gate with one self-repair round. Returns (js, names)."""
    user = ("Brief for the video:\n%s\n\nWrite scene_custom.js with exactly %d NEW scene "
            "types for this video. Pick metaphors only this video would draw, name them "
            "after those metaphors, and document each one's PARAMS comment. Both scenes "
            "must be usable as a full scene in a ~15s reel.") % (brief, args.bespoke)
    js = strip_js(call_llm_js(args, [{"role": "system", "content": BESPOKE_SYS},
                                     {"role": "user", "content": user}]))
    msg = ""
    for attempt in range(2):
        open(js_path, "w").write(js)
        ok, msg = node_check(js_path)
        names = re.findall(r"defineScene\(\s*['\"]([a-z][a-z0-9_]*)['\"]", js)
        builtins = {"terminal", "kinetic", "cards", "counter", "chart", "quote", "split", "endcard"}
        if ok and names and not (set(names) & builtins):
            return js, names
        if attempt:
            break
        js = strip_js(call_llm_js(args, [
            {"role": "system", "content": BESPOKE_SYS + "\nReturn ONLY the corrected JavaScript file."},
            {"role": "user", "content": user},
            {"role": "assistant", "content": js},
            {"role": "user", "content": "This file failed: %s\nFix it, keep the same scene names. "
                                        "Return the full corrected JavaScript file only." %
             (msg if not ok else ("no valid defineScene declarations" if not names
                                  else "refuses to override built-ins: " + ",".join(sorted(set(names) & builtins))))}]))
    raise SystemExit("director: bespoke JS never validated — kept at " + js_path)


def check(doc, tmp, allow_custom):
    json.dump(doc, open(tmp, "w"), indent=1)
    errs, warns, n, t = V.validate(tmp, allow_custom=allow_custom, allow_slots=False)
    return errs, warns, n, t


def repair(args, doc, errs, user_msg, tmp, bespoke_names=()):
    """One round trip: give the model its JSON + the validator errors."""
    syspt = CATALOG + "\nReturn ONLY the corrected JSON."
    if bespoke_names:
        syspt += ("\nThis timeline uses bespoke scene types defined in scene_custom.js: " +
                  ", ".join(bespoke_names) + " — keep those scenes and their params exactly.")
    msgs = [{"role": "system", "content": syspt},
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
    ap.add_argument("--bespoke", type=int, default=1,
                    help="invent mode: NEW scene types the LLM writes for this video (0 = archetypes only)")
    ap.add_argument("--no-probe", action="store_true", help="skip the render probe of bespoke scenes")
    ap.add_argument("--allow-slots", action="store_true", help="don't fail on unfilled slots")
    ap.add_argument("--no-response-format", action="store_true")
    args = ap.parse_args()

    brief = open(args.brief).read() if args.brief and os.path.exists(args.brief) else (args.brief or "")
    tmp = args.out + ".candidate.json"
    out_dir = os.path.dirname(os.path.abspath(args.out))
    attempts, used_repair = 0, False
    bespoke_js_path, bespoke_names, js = None, [], ""

    if args.mode == "from-file":
        doc = json.load(open(args.from_file))
    else:
        if not brief:
            raise SystemExit("director: --brief required for invent/fill")
        if args.mode == "invent":
            user = f"Brief:\n{brief}\n\nCompose a ~15s reel. Return the timeline JSON only."
            if args.bespoke > 0:
                # uniqueness guarantee: the LLM first draws NEW scene types for
                # this video, then composes a timeline that must use all of them
                bespoke_js_path = os.path.join(out_dir, "scene_custom.js")
                print("director: writing %d bespoke scene type(s) for this video ..." % args.bespoke)
                js, bespoke_names = gen_bespoke(args, brief, bespoke_js_path)
                args.allow_custom = True
                print("director: bespoke scenes: " + ", ".join(bespoke_names))
                user = (f"Brief:\n{brief}\n\nYou already wrote these bespoke scene types for this "
                        f"video (params in the PARAMS comments):\n\n{js}\n\n"
                        f"Compose a ~15s reel that uses ALL of them (1.5-3s each, plus the "
                        f"endcard and any built-ins you need). Return the timeline JSON only.")
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
        fixed = repair(args, doc, errs, user if args.mode != "from-file" else "", tmp, bespoke_names)
        if fixed is None:
            break
        doc = fixed
        errs, warns, n, t = check(doc, tmp, args.allow_custom)
    if errs and not args.allow_slots:
        for e in errs:
            print("ERROR:", e)
        print(f"director: REJECTED — candidate kept at {tmp}")
        sys.exit(1)

    # render probe: bespoke scenes must actually DRAW pixels (blank = the JS
    # drew off-screen or crashed) — one repair round, then reject
    probe_report = None
    if not args.no_probe:
        if bespoke_names:
            abs_out = os.path.abspath(tmp)  # candidate file — check() already wrote it
            ok, report = probe_bespoke(out_dir, abs_out, doc, bespoke_names)
            print("director: probe -> " + report)
            if not ok and js:
                print("director: repairing bespoke JS after blank render ...")
                js = strip_js(call_llm_js(args, [
                    {"role": "system", "content": BESPOKE_SYS + "\nReturn ONLY the corrected JavaScript file."},
                    {"role": "assistant", "content": js},
                    {"role": "user", "content": "The scene rendered BLANK / crashed in the render probe:\n" + report +
                        "\nMost likely causes: drawing off-screen, NaN coordinates, prog() window wrong, "
                        "or an exception in the draw body. Fix so every scene draws clearly inside the "
                        "safe area for its full duration. Keep the same scene names and params. "
                        "Return the full corrected JavaScript file only."}]))
                open(bespoke_js_path, "w").write(js)
                ok, report = probe_bespoke(out_dir, abs_out, doc, bespoke_names)
                print("director: probe 2 -> " + report)
                if not ok:
                    print("director: REJECTED — bespoke scenes never drew pixels; "
                          "kept %s and %s" % (bespoke_js_path, tmp))
                    sys.exit(2)
            probe_report = report
        elif args.mode == "from-file" and args.allow_custom:
            names = V.custom_scenes(tmp) & {s.get("scene") for s in doc.get("timeline", [])}
            if names:
                ok, probe_report = probe_bespoke(out_dir, os.path.abspath(tmp), doc, names)
                print("director: probe -> " + probe_report)
                if not ok:
                    print("director: REJECTED — custom scenes never drew pixels; fix " +
                          os.path.join(out_dir, "scene_custom.js") + " (candidate kept at " + tmp + ")")
                    sys.exit(2)

    # freeze
    if args.mode == "fill" or args.allow_slots:
        doc.pop("_comment", None)
    json.dump(doc, open(args.out, "w"), indent=1)
    meta_path = os.path.splitext(args.out)[0] + "_meta.json"
    meta = {"created": datetime.now(timezone.utc).isoformat(timespec="seconds"),            "mode": args.mode, "model": args.model if args.mode != "from-file" else None,
            "base_url": args.base_url if args.mode != "from-file" else None,
            "api": args.api if args.mode != "from-file" else None,
            "seed": args.seed, "repair_used": used_repair,
            "bespoke": ({"names": bespoke_names, "js_sha256": hashlib.sha256(js.encode()).hexdigest()[:16]}
                        if bespoke_names else None),
            "probe": probe_report,
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
