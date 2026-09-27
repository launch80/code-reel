#!/usr/bin/env python3
"""Validate a timeline.json against the scene contracts. Exit 0 = ok.

  python3 validate.py [path/to/timeline.json]
"""
import json, sys, os

BP_CHECK = True  # every cut must land on a beat

REQUIRED = {
    "terminal": ["cmd"],
    "kinetic": ["words"],
    "cards": ["cards"],
    "counter": ["big"],
    "chart": ["grow"],
    "quote": ["text", "author"],
    "split": ["left", "right"],
    "endcard": ["word1", "word2"],
}

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "timeline.json")
    tl = json.load(open(path))
    errs, warns = [], []
    bpm = tl.get("bpm", 120)
    fps = tl.get("fps", 60)
    beat = 60.0 / bpm
    scenes = tl.get("timeline", [])
    if not scenes:
        errs.append("timeline is empty")
    t = 0.0
    for i, s in enumerate(scenes):
        tag = f"scene[{i}] {s.get('scene','?')}"
        if s.get("scene") not in REQUIRED:
            errs.append(f"{tag}: unknown scene type (have: {', '.join(REQUIRED)})")
            t += s.get("dur", 0); continue
        if not isinstance(s.get("dur"), (int, float)) or s["dur"] <= 0:
            errs.append(f"{tag}: missing/invalid dur")
            t += s.get("dur", 0); continue
        p = s.get("p", {})
        for k in REQUIRED[s["scene"]]:
            if k not in p:
                errs.append(f"{tag}: missing required param p.{k}")
        # beat grid: every cut must be a multiple of the beat (audio sync)
        if BP_CHECK and t > 0 and abs(t / beat - round(t / beat)) > 1e-6:
            errs.append(f"{tag}: starts at {t}s — off the {60/bpm}s beat grid")
        # frames must be integers at the scene boundary
        if abs(t * fps - round(t * fps)) > 1e-6:
            errs.append(f"{tag}: starts at {t}s — not a whole frame at {fps}fps")
        for sl in s.get("slams", []):
            if not (0 <= sl < s["dur"]):
                errs.append(f"{tag}: slam {sl} outside [0, dur)")
        # per-type checks
        if s["scene"] == "kinetic":
            for w in p.get("words", []):
                if not (isinstance(w, list) and len(w) >= 2):
                    errs.append(f"{tag}: word entry must be [text, offset, ...]")
                elif not (0 <= w[1] < s["dur"]):
                    errs.append(f"{tag}: word '{w[0]}' offset {w[1]} outside scene")
        if s["scene"] == "chart":
            if p.get("months") and len(p["months"]) != len(p["grow"]):
                errs.append(f"{tag}: months ({len(p['months'])}) != grow ({len(p['grow'])}) length")
            if p.get("impact") is not None and not (0 <= p["impact"] < s["dur"]):
                errs.append(f"{tag}: impact {p['impact']} outside scene")
        if s["scene"] == "counter":
            if p.get("scope") and not (120 <= len(p["scope"]) <= 121):
                warns.append(f"{tag}: scope should be 120-121 values (got {len(p['scope'])})")
        if s["scene"] in ("cards", "counter"):
            for key in ("big",):
                if key in p and not isinstance(p[key], dict):
                    errs.append(f"{tag}: p.{key} must be {{from,to,fmt}}")
        if s["scene"] == "cards":
            for c in p.get("cards", []):
                if "big" in c and not isinstance(c["big"], dict):
                    errs.append(f"{tag}: card '{c.get('tag')}' big must be {{from,to,fmt}}")
        t += s["dur"]
    if abs(t * fps - round(t * fps)) > 1e-6:
        errs.append(f"total duration {t}s is not a whole number of frames")
    if scenes and scenes[-1].get("scene") != "endcard":
        warns.append("last scene is not 'endcard' — reel won't end on a brand card")
    if tl.get("hud") and not tl["hud"].get("brand"):
        warns.append("hud.brand missing — HUD will show defaults")

    for w in warns: print("WARN:", w)
    if errs:
        for e in errs: print("ERROR:", e)
        sys.exit(1)
    print(f"OK: {len(scenes)} scenes, {t:.2f}s, {fps}fps, {bpm}bpm (cuts on the beat grid)")

main()
