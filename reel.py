#!/usr/bin/env python3
"""code-reel — one pipeline for every harness (you, an agent, a local model, the tests).

  reel.py init <proj> [--style signal] [--size 1920x1080] [--seed N]
  reel.py styles                               list style packs
  reel.py compile <proj> [--final]             resolve + validate + derive events  -> .reel/
  reel.py stills <proj> t1,t2,... [--dpr 1]    PNG stills                          -> .reel/stills/
  reel.py audit <proj>                         layout lint + blank check           -> .reel/audit.json
  reel.py contact <proj>                       one frame per scene, annotated      -> .reel/contact.png
  reel.py novelty <proj> [--register]          similarity vs blueprints + past reels -> .reel/novelty.json
  reel.py review <proj>                        contact + audit + novelty + the critique checklist
  reel.py render <proj> [--dpr 2]              all frames (parallel, lossless)     -> .reel/frames.mkv
  reel.py audio <proj>                         score + sfx from compiled events    -> .reel/audio.wav
  reel.py build <proj> [--out reel.mp4]        the one lossy encode + loudness loop -> reel.mp4
  reel.py qc <proj>                            QC workbook                          -> .reel/qc_report.xlsx
  reel.py run <proj> [--draft|--final]         compile → audit → novelty → render → audio → build → qc
  reel.py direct <proj> <step> [--backend ...] model-driven steps (treat, pick, timeline, scenes) — see references/director.md
  reel.py status <proj>                        what has been built, what is stale

Exit codes: 0 ok · 1 failed gate · 2 usage · 10 waiting for the agent backend (answer the prompt file, re-run).
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reelkit import compile as K  # noqa: E402

SIZES = {"16:9": (1920, 1080), "9:16": (1080, 1920), "1:1": (1080, 1080), "4:5": (1080, 1350)}


def _say(*a):
    print(*a, flush=True)


def cmd_init(a):
    p = a.proj
    if os.path.exists(os.path.join(p, "timeline.json")) and not a.force:
        _say("exists: %s/timeline.json (use --force to overwrite)" % p)
        return 2
    os.makedirs(os.path.join(p, "scenes"), exist_ok=True)
    os.makedirs(os.path.join(p, "assets"), exist_ok=True)
    w, h = SIZES.get(a.size, None) or tuple(int(x) for x in a.size.lower().split("x"))
    seed = a.seed if a.seed is not None else random.SystemRandom().randrange(1, 2 ** 31)
    styles = sorted(K.styles())
    style = a.style or styles[seed % len(styles)]
    tl = {"version": 2, "name": a.name or os.path.basename(os.path.abspath(p)), "w": w, "h": h, "fps": 60,
          "seed": seed, "style": style, "hud": {"brand": a.name or "BRAND", "brand2": "", "series": "", "line": ""},
          "literals": [], "timeline": [
              {"scene": "opening", "dur": 3.0, "name": "OPENING", "p": {"title": "Replace me"}},
              {"scene": "endcard", "dur": 2.5, "name": "END", "p": {"word1": a.name or "brand", "word2": "", "serif": "", "url": "", "footer": ""}}]}
    json.dump(tl, open(os.path.join(p, "timeline.json"), "w"), indent=1)
    if not os.path.exists(os.path.join(p, "claims.json")):
        json.dump({"_doc": "every number shown on screen: {id: {value, display?, source, url?, how?, date?}} — reference as \"@id\" (value) or {{id}} (text)"},
                  open(os.path.join(p, "claims.json"), "w"), indent=1)
    sp = os.path.join(p, "scenes", "opening.js")
    if not os.path.exists(sp):
        open(sp, "w").write(OPENING_JS)
    if not os.path.exists(os.path.join(p, "brief.md")):
        open(os.path.join(p, "brief.md"), "w").write(BRIEF_MD)
    _say("initialized %s  (style %s, seed %d, %dx%d)" % (p, style, seed, w, h))
    _say("next: write brief.md, then  reel.py direct %s treat   — or edit timeline.json + scenes/*.js by hand" % p)
    return 0


OPENING_JS = """/* @meta {"name": "opening", "required": ["title"], "text": ["title"]} */
// Scene code written for THIS video. Replace with the video's own picture.
// (lt = seconds into the scene, d = scene duration, p = params from timeline.json)
defineScene('opening', (lt, d, p) => {
  const e = M.in(prog(lt, 0.1, 0.9));
  const px = fitPx(p.title, 'disp', W - SAFE.l - SAFE.r, 200 * U, 40 * U);
  txt(p.title, W / 2, H / 2 + px * 0.35, { f: F('disp', px), col: C.cream, align: 'center', a: e });
});
"""

BRIEF_MD = """# Brief

**What is this video for?** (one product/event, who watches, what they do after)

**Format:** 16:9 · 15 s

**Claims on screen** (every number + where it comes from — these go in claims.json):

| id | value | source |
|---|---|---|

**Look:** (style pack, brand site, colors — or "surprise me")

**Must include / must avoid:**
"""


def _compile(a, final=None):
    out = K.compile_project(a.proj, final=bool(getattr(a, "final", False) if final is None else final))
    _say(K.report(out))
    return out


def cmd_compile(a):
    out = _compile(a)
    if not out["errors"]:
        _say("preview: open %s" % os.path.join(os.path.abspath(a.proj), ".reel", "index.html"))
    return 1 if out["errors"] else 0


def cmd_styles(a):
    for k, v in sorted(K.styles().items()):
        _say("%-10s %s" % (k, v.get("desc", "")))
    return 0


def cmd_stills(a):
    from reelkit import render as R
    if _compile(a)["errors"]:
        return 1
    for p in R.stills(a.proj, [float(x) for x in a.times.split(",")], a.dpr):
        _say("wrote", p)
    return 0


def cmd_audit(a):
    from reelkit import render as R
    if _compile(a)["errors"]:
        return 1
    res = R.audit(a.proj, a.dpr)
    for w in res["warnings"][:30]:
        _say("WARN:", w)
    for e in res["errors"]:
        _say("ERROR:", e)
    _say("audit: %d error(s), %d warning(s) across %d scenes -> .reel/audit.json" % (len(res["errors"]), len(res["warnings"]), len(res["scenes"])))
    return 1 if res["errors"] else 0


def cmd_contact(a):
    from reelkit import render as R
    if _compile(a)["errors"]:
        return 1
    _say("wrote", R.contact(a.proj, a.dpr))
    return 0


def cmd_novelty(a):
    from reelkit import novelty as N
    res = N.check(a.proj, register=a.register)
    _say(res["summary"])
    for line in res["details"]:
        _say("  " + line)
    return 0 if res["ok"] else 1


def cmd_review(a):
    rc = cmd_audit(a)
    from reelkit import render as R
    from reelkit import novelty as N
    _say("wrote", R.contact(a.proj, 1))
    nv = N.check(a.proj)
    _say(nv["summary"])
    _say(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "references", "critique.md")).read())
    return rc or (0 if nv["ok"] else 1)


def cmd_render(a):
    from reelkit import render as R
    if _compile(a)["errors"]:
        return 1
    t = time.time()
    _say("rendering at DPR=%d ..." % a.dpr)
    _say("wrote %s (%.0fs)" % (R.video(a.proj, a.dpr, a.workers), time.time() - t))
    return 0


def cmd_audio(a):
    from reelkit import audio as AU
    if _compile(a)["errors"]:
        return 1
    out, info = AU.build_project(a.proj)
    _say("wrote %s (%s)" % (out, ", ".join("%s=%s" % kv for kv in info.items())))
    return 0


def cmd_build(a):
    from reelkit import build as B
    out, m = B.encode(a.proj, a.out and os.path.abspath(a.out))
    _say("wrote %s  (%.1f LUFS, TP %.1f dBTP)" % (out, m["I"], m["TP"]))
    return 0


def cmd_qc(a):
    from reelkit import qc as Q
    res = Q.run(a.proj, a.out and os.path.abspath(a.out))
    for f in res["fails"]:
        _say("FAIL: %s — %s %s" % f)
    _say("QC -> .reel/qc_report.xlsx · READY TO PUBLISH? %s" % res["ready"])
    return 1 if res["fails"] else 0


def cmd_run(a):
    a.final = bool(a.final)
    dpr = 1 if a.draft else a.dpr
    steps = [("compile", cmd_compile), ("audit", cmd_audit)]
    if a.final:
        steps.append(("novelty", cmd_novelty))
    for name, fn in steps:
        _say("== %s" % name)
        rc = fn(a)
        if rc:
            _say("stopped at %s (exit %d) — fix and re-run" % (name, rc))
            return rc
    a.dpr = dpr
    for name, fn in [("render", cmd_render), ("audio", cmd_audio), ("build", cmd_build), ("qc", cmd_qc)]:
        _say("== %s" % name)
        rc = fn(a)
        if rc and name != "qc":
            return rc
    if a.final and getattr(a, "register", False):
        from reelkit import novelty as N
        N.check(a.proj, register=True)
    return 0


def cmd_direct(a):
    from reelkit import director as D
    return D.main(a)


def cmd_status(a):
    rd = os.path.join(a.proj, ".reel")
    def age(f):
        p = os.path.join(rd, f) if not f.startswith("/") else f
        return time.strftime("%H:%M:%S", time.localtime(os.path.getmtime(p))) if os.path.exists(p) else "—"
    src = max([os.path.getmtime(os.path.join(a.proj, f)) for f in ("timeline.json", "claims.json") if os.path.exists(os.path.join(a.proj, f))] +
              [os.path.getmtime(os.path.join(a.proj, "scenes", f)) for f in os.listdir(os.path.join(a.proj, "scenes"))] if os.path.isdir(os.path.join(a.proj, "scenes")) else [0])
    for f in ("timeline.resolved.json", "audit.json", "novelty.json", "contact.png", "frames.mkv", "audio.wav", "../reel.mp4", "qc_report.xlsx"):
        p = os.path.join(rd, f)
        stale = os.path.exists(p) and os.path.getmtime(p) < src
        _say("%-24s %s%s" % (f.replace("../", ""), age(f), "  (stale)" if stale else ""))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, *extra):
        s = sub.add_parser(name)
        if name != "styles":
            s.add_argument("proj")
        s.set_defaults(fn=fn)
        for e in extra:
            e(s)
        return s
    add("init", cmd_init, lambda s: s.add_argument("--style"), lambda s: s.add_argument("--size", default="16:9"),
        lambda s: s.add_argument("--seed", type=int), lambda s: s.add_argument("--name"), lambda s: s.add_argument("--force", action="store_true"))
    add("styles", cmd_styles)
    add("compile", cmd_compile, lambda s: s.add_argument("--final", action="store_true"))
    add("stills", cmd_stills, lambda s: s.add_argument("times"), lambda s: s.add_argument("--dpr", type=int, default=1))
    for n, f in (("audit", cmd_audit), ("contact", cmd_contact), ("review", cmd_review)):
        add(n, f, lambda s: s.add_argument("--dpr", type=int, default=1))
    add("novelty", cmd_novelty, lambda s: s.add_argument("--register", action="store_true"))
    add("render", cmd_render, lambda s: s.add_argument("--dpr", type=int, default=2), lambda s: s.add_argument("--workers", type=int))
    add("audio", cmd_audio)
    add("build", cmd_build, lambda s: s.add_argument("--out"))
    add("qc", cmd_qc, lambda s: s.add_argument("--out"))
    add("run", cmd_run, lambda s: s.add_argument("--draft", action="store_true"), lambda s: s.add_argument("--final", action="store_true"),
        lambda s: s.add_argument("--dpr", type=int, default=2), lambda s: s.add_argument("--workers", type=int),
        lambda s: s.add_argument("--out"), lambda s: s.add_argument("--register", action="store_true"))
    add("status", cmd_status)
    d = add("direct", cmd_direct, lambda s: s.add_argument("step", choices=["treat", "pick", "timeline", "scenes", "repair", "all"]))
    for flag, kw in (("--backend", dict(default=os.environ.get("REEL_BACKEND", "agent"))), ("--model", dict(default=os.environ.get("REEL_MODEL", "qwen3:14b"))),
                     ("--base-url", dict(default=os.environ.get("LLM_BASE_URL", "http://localhost:11434"))),
                     ("--fixtures", dict(default=os.environ.get("REEL_FIXTURES"))), ("--candidates", dict(type=int, default=3)),
                     ("--pick", dict(default=None)), ("--temperature", dict(type=float, default=None)), ("--max-repair", dict(type=int, default=2))):
        d.add_argument(flag, **kw)
    a = ap.parse_args(argv)
    try:
        return a.fn(a) or 0
    except K.CompileError as e:
        _say("ERROR:", e)
        return 1
    except Exception as e:           # render/audio/build failures: one clear line, exit 1
        if type(e).__name__ in ("RenderError", "RuntimeError"):
            _say("ERROR:", e)
            return 1
        raise


if __name__ == "__main__":
    sys.exit(main())
