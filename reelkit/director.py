"""director — model-driven steps, each gated exactly like hand-written work.

  treat     brief -> K distinct treatments (style x structure x metaphor), one style frame each
  pick      choose a treatment (--pick N | auto)                       -> treatment.json
  timeline  treatment -> timeline.json + claims.json, compile-gated with repair
  scenes    one scenes/<name>.js per custom scene, gated by syntax -> compile -> audit -> novelty, with repair
  all       treat -> pick -> timeline -> scenes

Backends (--backend): openai | ollama | agent | mock   (see llm.py). The prompts,
file names, gates and repair loop are identical for all of them.
"""
import json
import os
import re
import shutil
import sys

from . import compile as K
from .llm import LLM, AwaitingAgent, LLMError

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
PROMPTS = os.path.join(SKILL, "prompts", "director")
STRUCTURES = ["hook → claim → proof → close", "problem → turn → solution → payoff", "one continuous shot through one world",
              "countdown / list (N → 1)", "before / after", "a journey (A → B, things happen on the way)",
              "question → reveal", "manifesto (a stack of statements)", "product walkthrough", "history (then → now)"]


def _t(name, **kw):
    s = open(os.path.join(PROMPTS, name + ".md")).read()
    for k, v in kw.items():
        s = s.replace("{{%s}}" % k, str(v))
    return s


def _say(*a):
    print(*a, flush=True)


def _brief(proj):
    p = os.path.join(proj, "brief.md")
    if not os.path.exists(p):
        raise LLMError("no brief.md in %s (run reel.py init)" % proj)
    return open(p).read()


def _proj_seed(proj):
    try:
        return int(json.load(open(os.path.join(proj, "timeline.json"))).get("seed", 1))
    except Exception:
        return 1


def _duration(brief):
    m = re.search(r"(\d+)\s*(?:s\b|sec|seconds)", brief)
    return int(m.group(1)) if m else 15


def _size(proj):
    try:
        tl = json.load(open(os.path.join(proj, "timeline.json")))
        return tl.get("w", 1920), tl.get("h", 1080)
    except Exception:
        return 1920, 1080


def _llm(a, proj):
    return LLM(a.backend, proj, model=a.model, base_url=a.base_url, fixtures=a.fixtures, seed=_proj_seed(proj), temperature=a.temperature)


# ------------------------------------------------------------------ treat
def step_treat(a, proj, llm):
    styles = K.styles()
    k = max(1, int(a.candidates))
    seed = _proj_seed(proj)
    r = K.rng(seed * 7 + 3)
    packs = sorted(styles)
    order = sorted(packs, key=lambda _: r())
    structs = sorted(STRUCTURES, key=lambda _: r())
    assign = "\n".join("- Treatment %d: style pack **%s**; lean toward structure \"%s\"." % (i + 1, order[i % len(order)], structs[i % len(structs)]) for i in range(k))
    brief = _brief(proj)
    user = _t("treat", K=k, BRIEF=brief, STYLES="\n".join("- %s: %s" % (n, styles[n].get("desc", "")) for n in packs),
              BLUEPRINTS=", ".join(sorted(K.blueprint_meta())), STRUCTURES="; ".join(STRUCTURES), ASSIGN=assign,
              DURATION=_duration(brief))
    out = llm.ask("treat-1", _t("system"), user, "json", temperature=0.9)
    tr = out.get("treatments") if isinstance(out, dict) else None
    problems = _check_treatments(tr, k, styles)
    if problems:
        out = llm.ask("treat-2", _t("system"), user + "\n\n## Your previous answer failed these checks — fix them\n" + "\n".join("- " + p for p in problems) +
                      "\n\nPrevious answer:\n```json\n" + json.dumps(out)[:12000] + "\n```", "json", temperature=0.7)
        tr = out.get("treatments") if isinstance(out, dict) else None
        problems = _check_treatments(tr, k, styles)
        if problems:
            raise LLMError("treatments rejected:\n  " + "\n  ".join(problems))
    json.dump({"treatments": tr}, open(os.path.join(proj, "treatments.json"), "w"), indent=1)
    sheet = style_frames(proj, tr)
    _say("wrote treatments.json (%d) and %s" % (len(tr), sheet))
    for i, t in enumerate(tr, 1):
        _say("  %d. %s — %s [%s · %s]" % (i, t.get("title"), t.get("logline"), t["style"]["pack"], t.get("structure")))
    return tr


def _check_treatments(tr, k, styles):
    p = []
    if not isinstance(tr, list) or len(tr) < k:
        return ["expected %d treatments in {\"treatments\": [...]}" % k]
    packs, metas = [], []
    for i, t in enumerate(tr, 1):
        st = (t.get("style") or {}).get("pack")
        if st not in styles:
            p.append("treatment %d: style.pack '%s' is not one of %s" % (i, st, ", ".join(sorted(styles))))
        packs.append(st)
        metas.append(set(re.findall(r"[a-z]{4,}", (t.get("metaphor") or "").lower())))
        sc = t.get("scenes") or []
        if not (2 <= len(sc) <= 9):
            p.append("treatment %d: needs 3-7 scenes (has %d)" % (i, len(sc)))
        custom = sum(s.get("beats", 0) for s in sc if s.get("kind") == "custom")
        total = sum(s.get("beats", 0) for s in sc) or 1
        if custom / total < 0.6:
            p.append("treatment %d: only %.0f%% of beats are custom scenes (need >= 70%%)" % (i, custom / total * 100))
        for s in sc:
            if not re.fullmatch(r"[a-z][a-z0-9_]*", s.get("name", "")):
                p.append("treatment %d: scene name %r must be snake_case" % (i, s.get("name")))
    if len(set(packs)) < len(packs):
        p.append("treatments must use different style packs (got %s)" % packs)
    for i in range(len(metas)):
        for j in range(i + 1, len(metas)):
            if metas[i] and metas[j] and len(metas[i] & metas[j]) / max(1, len(metas[i] | metas[j])) > 0.5:
                p.append("treatments %d and %d share the same metaphor — make them different pictures" % (i + 1, j + 1))
    return p


def style_frames(proj, tr):
    """One still per treatment: its title in its own style — a cheap look test before any scene code."""
    from . import render as R
    from PIL import Image, ImageDraw
    w, h = _size(proj)
    ims = []
    for i, t in enumerate(tr, 1):
        d = os.path.join(proj, ".reel", "treat", str(i))
        os.makedirs(d, exist_ok=True)
        style = dict(t["style"].get("overrides") or {}, pack=t["style"]["pack"])
        json.dump({"version": 2, "name": t.get("title", ""), "w": w, "h": h, "fps": 60, "seed": _proj_seed(proj), "style": style,
                   "hud": {"brand": t.get("title", "")[:18]}, "policy": {"beatGrid": False},
                   "literals": [x for x in re.findall(r"\S*\d\S*", (t.get("title", "") + " " + t.get("logline", "")))],
                   "timeline": [{"scene": "statement", "dur": 2.0, "p": {"kicker": t.get("structure", ""), "text": t.get("logline", t.get("title", "")),
                                                                          "emphasis": sorted(t.get("metaphor", "x").split(), key=len)[-1:]}}]},
                  open(os.path.join(d, "timeline.json"), "w"))
        out = K.compile_project(d)
        if out["errors"]:
            continue
        R.stills(d, [1.6], 1)
        ims.append((i, t, os.path.join(d, ".reel", "stills", "t01.60.png")))
    cols = min(3, max(1, len(ims)))
    tw_, th = 640, int(640 * h / w)
    sheet = Image.new("RGB", (cols * tw_, ((len(ims) + cols - 1) // cols) * (th + 28)), (18, 18, 18))
    dr = ImageDraw.Draw(sheet)
    for k, (i, t, pth) in enumerate(ims):
        x, y = (k % cols) * tw_, (k // cols) * (th + 28)
        sheet.paste(Image.open(pth).convert("RGB").resize((tw_, th)), (x, y + 28))
        dr.text((x + 8, y + 8), "%d. %s  [%s]" % (i, t.get("title", ""), t["style"]["pack"]), fill=(235, 235, 235))
    path = os.path.join(proj, ".reel", "treatments.png")
    sheet.save(path)
    return path


# ------------------------------------------------------------------ pick
def step_pick(a, proj):
    tr = json.load(open(os.path.join(proj, "treatments.json")))["treatments"]
    n = int(a.pick) if a.pick not in (None, "auto") else 1
    if not (1 <= n <= len(tr)):
        raise LLMError("--pick must be 1..%d" % len(tr))
    json.dump(tr[n - 1], open(os.path.join(proj, "treatment.json"), "w"), indent=1)
    _say("picked treatment %d: %s [%s]" % (n, tr[n - 1].get("title"), tr[n - 1]["style"]["pack"]))
    return tr[n - 1]


# ------------------------------------------------------------------ timeline
def step_timeline(a, proj, llm):
    t = json.load(open(os.path.join(proj, "treatment.json")))
    styles = K.styles()
    bpm = float(styles[t["style"]["pack"]].get("bpm", 120))
    w, h = _size(proj)
    brief = _brief(proj)
    bpp = "; ".join("%s(%s)" % (k, ", ".join(v.get("text", []))) for k, v in sorted(K.blueprint_meta().items()))
    user = _t("timeline", BRIEF=brief, TREATMENT=json.dumps(t, indent=1), BPM=bpm, BEAT=round(60 / bpm, 4), DURATION=_duration(brief),
              SEED=_proj_seed(proj), W=w, H=h, BLUEPRINT_PARAMS=bpp)
    key, attempt = "timeline", 1
    out = llm.ask("%s-%d" % (key, attempt), _t("system"), user, "json", temperature=0.4)
    while True:
        _write_timeline(proj, out, t)
        # scene files don't exist yet: compile with placeholder stubs for custom scenes
        errs = _compile_with_stubs(proj)
        if not errs:
            break
        if attempt > a.max_repair:
            raise LLMError("timeline still invalid after %d repairs:\n  %s" % (a.max_repair, "\n  ".join(errs)))
        attempt += 1
        _say("timeline: %d error(s) -> repair %d" % (len(errs), attempt - 1))
        out = llm.ask("%s-%d" % (key, attempt), _t("system"), user + "\n\n## Your previous answer failed compile — fix exactly these\n" +
                      "\n".join("- " + e for e in errs) + "\n\nPrevious answer:\n```json\n" + json.dumps(out)[:16000] + "\n```", "json", temperature=0.2)
    open(os.path.join(proj, ".reel", "llm", "timeline.done"), "w").write("ok")
    _say("wrote timeline.json + claims.json (compile clean with scene stubs)")
    return out


def _write_timeline(proj, out, treatment):
    tl = out.get("timeline", out) if isinstance(out, dict) else {}
    tl.setdefault("version", 2)
    tl["seed"] = _proj_seed(proj)
    tl.setdefault("style", {"pack": treatment["style"]["pack"], **(treatment["style"].get("overrides") or {})})
    json.dump(tl, open(os.path.join(proj, "timeline.json"), "w"), indent=1)
    claims = out.get("claims") if isinstance(out, dict) else None
    if isinstance(claims, dict):
        json.dump(claims, open(os.path.join(proj, "claims.json"), "w"), indent=1)


def _custom_names(proj):
    tl = json.load(open(os.path.join(proj, "timeline.json")))
    bp = K.blueprint_meta()
    seen, out = set(), []
    for s in tl.get("timeline", []):
        n = s.get("scene")
        if n and n not in bp and n not in seen:
            seen.add(n)
            out.append(n)
    return out


def _compile_with_stubs(proj):
    sd = os.path.join(proj, "scenes")
    os.makedirs(sd, exist_ok=True)
    made = []
    for n in _custom_names(proj):
        if n not in K.custom_scenes(proj):
            p = os.path.join(sd, n + ".js")
            open(p, "w").write("/* stub: written by the scenes step */\ndefineScene('%s', (lt, d, p) => {});\n" % n)
            made.append(p)
    try:
        out = K.compile_project(proj, write=False)
    finally:
        for p in made:
            os.remove(p)
    return [e for e in out["errors"] if "hard-codes" not in e]


# ------------------------------------------------------------------ scenes
def _example(seed):
    ex = sorted(os.path.join(SKILL, "prompts", "examples", f) for f in os.listdir(os.path.join(SKILL, "prompts", "examples")) if f.endswith(".js"))
    return open(ex[seed % len(ex)]).read() if ex else ""


def step_scenes(a, proj, llm, only=None):
    from . import render as R
    from . import novelty as N
    t = json.load(open(os.path.join(proj, "treatment.json")))
    tl = json.load(open(os.path.join(proj, "timeline.json")))
    brief = _brief(proj)[:3000]
    api = open(os.path.join(SKILL, "references", "api.md")).read()
    names = only or _custom_names(proj)
    scenes = tl["timeline"]
    bpm = float(tl.get("bpm", K.styles()[t["style"]["pack"]].get("bpm", 120)))
    sd = os.path.join(proj, "scenes")
    os.makedirs(sd, exist_ok=True)
    report_all = {}
    stp = os.path.join(proj, ".reel", "llm", "scenes.json")
    status = json.load(open(stp)) if os.path.exists(stp) else {}
    for idx, name in enumerate(names):
        path = os.path.join(sd, name + ".js")
        if status.get(name) == "ok" and not (only and name in only):
            continue
        asked = os.path.exists(os.path.join(proj, ".reel", "llm", "scene-%s-1.answer.js" % name))
        if os.path.exists(path) and not asked and not (only and name in only) and "stub: written" not in open(path).read():
            rep, _ = gate_scene(proj, name)            # hand-written scene: gate it, never overwrite it
            status[name] = "ok" if not rep else "hand-written, failing"
            json.dump(status, open(stp, "w"), indent=1)
            _say("scene %s: hand-written — %s" % (name, "passes gates" if not rep else "FAILS:\n  " + "\n  ".join(rep)))
            continue
        i = next(k for k, s in enumerate(scenes) if s.get("scene") == name)
        s = scenes[i]
        story = next((x for x in t.get("scenes", []) if x.get("name") == name), {})
        beats = s.get("beats") or round(s.get("dur", 2) * bpm / 60)
        neigh = "%s → [this] → %s" % (scenes[i - 1]["scene"] if i else "start", scenes[i + 1]["scene"] if i + 1 < len(scenes) else "end")
        existing = "\n".join("- scenes/%s: %s" % (os.path.basename(f), _signature(f)) for f in K.scene_files(proj) if os.path.basename(f) != name + ".js") or "(nothing yet)"
        user = _t("scene", NAME=name, BRIEF=brief, TITLE=t.get("title"), METAPHOR=t.get("metaphor"), MOTIF=t.get("motif"),
                  STYLE=t["style"]["pack"], SCENE=json.dumps(story or s, indent=1), DUR=round(beats * 60 / bpm, 3), BEATS=beats, BPM=bpm,
                  NEIGHBOURS=neigh, PARAMS=json.dumps(s.get("p", {}), indent=1), EXISTING=existing, API=api, EXAMPLE=_example(_proj_seed(proj) + idx))
        attempt = 1
        js = llm.ask("scene-%s-%d" % (name, attempt), _t("system"), user, "js", temperature=0.35)
        while True:
            open(path, "w").write(js.rstrip() + "\n")
            rep, match = gate_scene(proj, name)
            if not rep:
                _say("scene %s: passed gates (attempt %d)" % (name, attempt))
                report_all[name] = "ok"
                status[name] = "ok"
                json.dump(status, open(stp, "w"), indent=1)
                break
            if attempt > a.max_repair:
                report_all[name] = rep
                _say("scene %s: FAILED after %d repairs:\n  %s" % (name, a.max_repair, "\n  ".join(rep)))
                break
            attempt += 1
            _say("scene %s: %d problem(s) -> repair %d" % (name, len(rep), attempt - 1))
            js = llm.ask("scene-%s-%d" % (name, attempt), _t("system"),
                         user + "\n\n## Your file\n```js\n" + js + "\n```\n\n" + _t("repair", NAME=name, REPORT="\n".join("- " + r for r in rep), MATCH=match or "-"),
                         "js", temperature=0.25)
    bad = {k: v for k, v in report_all.items() if v != "ok"}
    if bad:
        raise LLMError("scenes failed gates: " + ", ".join(bad))
    return report_all


def _signature(path):
    src = open(path).read()
    names = re.findall(r"defineScene\(\s*['\"]([a-z0-9_]+)", src) + re.findall(r"^(?:function|const)\s+([A-Za-z_]\w*)", src, re.M)
    return ", ".join(names[:14]) or "(helpers)"


def gate_scene(proj, name):
    """syntax -> compile -> audit (this scene) -> novelty (this scene). Returns (problems, best_match).
    Custom scenes not written yet get temporary blank stubs so one scene can be gated at a time."""
    sd = os.path.join(proj, "scenes")
    made = []
    for n in _custom_names(proj):
        if n not in K.custom_scenes(proj):
            pth = os.path.join(sd, n + ".js")
            open(pth, "w").write("/* stub: written by the scenes step */\ndefineScene('%s', (lt, d, p) => {});\n" % n)
            made.append(pth)
    try:
        return _gate(proj, name)
    finally:
        for pth in made:
            if os.path.exists(pth) and "stub: written" in open(pth).read():
                os.remove(pth)


def _gate(proj, name):
    from . import render as R
    from . import novelty as N
    out = K.compile_project(proj)
    errs = [e for e in out["errors"] if name in e or "syntax" in e or "unknown scene" in e]
    if errs:
        return errs, None
    try:
        au = R.audit(proj)
    except R.RenderError as e:
        return [str(e)], None
    mine = [s["name"] for s in out["scenes"] if s["scene"] == name]
    probs = [e for e in au["errors"] if any(e.startswith(m + " ") or e.startswith(m + ":") for m in mine)]
    if probs:
        return probs[:12], None
    nv = N.check(proj)
    worst = max((nv["scenes"].get(m, 0) for m in mine), default=0)
    if worst >= N.THRESH:
        line = next((l for l in nv["details"] if any(l.startswith(m) for m in mine)), "")
        return ["novelty: scene looks like an existing one (similarity %.2f >= %.2f): %s" % (worst, N.THRESH, line.strip())], line
    review_strip(proj, out, name)
    return [], None


def review_strip(proj, out, name):
    """Three stills of the scene (25/55/85%) -> .reel/review/<name>.png, for the agent/human to LOOK at."""
    from . import render as R
    from PIL import Image
    s = next(x for x in out["scenes"] if x["scene"] == name)
    ts = [round(s["t0"] + f * s["dur"], 2) for f in (0.25, 0.55, 0.85)]
    paths = R.stills(proj, ts, 1)
    ims = [Image.open(p_).convert("RGB").resize((640, int(640 * out["h"] / out["w"]))) for p_ in paths]
    strip = Image.new("RGB", (640 * len(ims), ims[0].height))
    for i, im in enumerate(ims):
        strip.paste(im, (i * 640, 0))
    os.makedirs(os.path.join(proj, ".reel", "review"), exist_ok=True)
    dst = os.path.join(proj, ".reel", "review", name + ".png")
    strip.save(dst)
    _say("scene %s: review strip -> %s" % (name, dst))


# ------------------------------------------------------------------ main
def main(a):
    proj = a.proj
    try:
        llm = _llm(a, proj) if a.step != "pick" else None
        if a.step == "treat":
            step_treat(a, proj, llm)
        elif a.step == "pick":
            step_pick(a, proj)
        elif a.step == "timeline":
            step_timeline(a, proj, llm)
        elif a.step in ("scenes", "repair"):
            step_scenes(a, proj, llm, only=[x for x in (a.only or "").split(",") if x] or None)
        elif a.step == "all":
            if not os.path.exists(os.path.join(proj, "treatments.json")):
                step_treat(a, proj, llm)
            if not os.path.exists(os.path.join(proj, "treatment.json")):
                step_pick(a, proj)
            if not os.path.exists(os.path.join(proj, ".reel", "llm", "timeline.done")):
                step_timeline(a, proj, llm)
            step_scenes(a, proj, llm)
            out = K.compile_project(proj)
            _say(K.report(out))
            _say("next: reel.py review %s   then   reel.py run %s --final" % (proj, proj))
        return 0
    except AwaitingAgent as e:
        _say("AWAITING AGENT\n  prompt: %s\n  write:  %s\nthen re-run the same command." % (e.prompt_path, e.answer_path))
        return 10
    except LLMError as e:
        _say("ERROR:", e)
        return 1
