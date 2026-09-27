"""Timeline -> picture/audio event derivation. SINGLE SOURCE OF TRUTH.

Used by audio.py (synthesis) and qc.py (cue sheet). reel.html mirrors
sceneSlams()/buildTimeline() in JS — if you change one, change the other;
validate.py + qc.py will flag drift.

A timeline is:
  {name, w, h, fps, bpm, theme?, hud?,
   timeline: [{scene, dur, name?, slams?, p:{...}}], sources?: {text: url}}
"""
import json

import numpy as np


def load(path):
    return json.load(open(path))


def scene_table(TL):
    """[{i, name, scene, t0, t1, dur, p}]"""
    out, t = [], 0.0
    for i, s in enumerate(TL["timeline"]):
        d = float(s["dur"])
        out.append({"i": i, "name": (s.get("name") or s["scene"]).upper(),
                    "scene": s["scene"], "t0": t, "t1": t + d, "dur": d,
                    "p": s.get("p", {})})
        t += d
    return out


def scene_slams(s):
    """Default slam times (seconds relative to scene start), per scene type."""
    p = s.get("p", {})
    if s["scene"] == "kinetic" and p.get("words"):
        return [w[1] for w in p["words"]]
    if s["scene"] == "chart" and p.get("impact") is not None:
        return [p["impact"]]
    if s["scene"] == "quote" and p.get("slam") is not None:
        return [p["slam"]]
    return []


def typing_events(t, dur, nclicks):
    return [(t, dur, nclicks)]


def derive_events(TL):
    """Same derivation audio.py has always used: beats, cuts, slams, typing
    [(t0, dur, nclicks)], ticks [(t0, t1)], bell. Keep byte-identical behavior
    when editing — audio output depends on it."""
    BP = 60.0 / TL.get("bpm", 120)
    ev = {"beats": [], "cuts": [], "slams": [], "typing": [], "ticks": []}
    names = [s["scene"] for s in TL["timeline"]]
    starts = np.cumsum([0] + [s["dur"] for s in TL["timeline"]])[:-1]
    cuts = list(starts[1:])
    if cuts:
        ev["beats"] = list(np.arange(starts[1], cuts[-1] + 1e-6, BP)) if len(cuts) > 1 else []
        ev["cuts"] = cuts
    ev["bell"] = starts[-1] + 0.05 if names and names[-1] == "endcard" else None
    for s, st in zip(TL["timeline"], starts):
        p = s.get("p", {})
        d = s["dur"]
        for sl in (s.get("slams") or []):
            ev["slams"].append(st + sl)
        if s["scene"] == "kinetic":
            for w in p.get("words", []):
                ev["slams"].append(st + w[1])
        if s["scene"] == "chart" and p.get("impact") is not None:
            ev["slams"].append(st + p["impact"])
        if s["scene"] == "quote" and p.get("slam") is not None:
            ev["slams"].append(st + p["slam"])
        if s["scene"] == "terminal":
            n = len(p.get("cmd", ""))
            if n:
                ev["typing"] += typing_events(st + 0.12 * d, 0.36 * d, n)
        if s["scene"] == "counter":
            if p.get("promptArg"):
                ev["typing"] += typing_events(st + 0.05, 0.35, 20)
            if p.get("typing"):
                ev["typing"] += typing_events(st + 0.53 * d, 0.25 * d, len(p["typing"]))
            if p.get("big"):
                ev["ticks"].append((st + 0.3, st + 1.2))
        if s["scene"] == "chart":
            if p.get("grow"):
                ev["ticks"].append((st + 0.2, st + (p.get("impact", 0.72 * d) - 0.1)))
    return ev
