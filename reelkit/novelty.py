"""novelty — is this reel its own picture, or a re-skin of something we've made before?

For every scene, compare its audit samples against a library of fingerprints
(the blueprint scenes in several styles + every reel registered with --register):

  layout  where the text sits: a 16x9 occupancy grid of visible text boxes
  shape   where the edges are: Sobel edge map of a 64x36 luminance thumbnail
          (palette-invariant: a recolor of the same layout still matches)

similarity = 0.55 * layout + 0.45 * shape (cosine, 0..1). A scene whose best
match (from a different reel) is >= THRESH is a re-skin. Final policy fails
the reel when re-skinned scenes cover more than MAX_SHARE of the runtime.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(os.path.dirname(HERE), "library", "fingerprints.json")
THRESH = 0.86
MAX_SHARE = 0.34


def _layout(boxes, W, H):
    g = np.zeros((9, 16))
    for b in boxes:
        if b.get("scene") == "__hud__" or b.get("a", 1) < 0.3:
            continue
        x0, x1 = max(0, b["x0"]) / W * 16, min(W, b["x1"]) / W * 16
        y0, y1 = max(0, b["y0"]) / H * 9, min(H, b["y1"]) / H * 9
        for gy in range(int(y0), min(9, int(np.ceil(y1)))):
            for gx in range(int(x0), min(16, int(np.ceil(x1)))):
                ox = min(x1, gx + 1) - max(x0, gx)
                oy = min(y1, gy + 1) - max(y0, gy)
                if ox > 0 and oy > 0:
                    g[gy, gx] += ox * oy
    return g.flatten()


def _edges(lum):
    a = np.array(lum, dtype=float).reshape(36, 64)
    a = (a - a.mean()) / (a.std() + 1e-6)
    gx = np.zeros_like(a)
    gy = np.zeros_like(a)
    gx[:, 1:-1] = a[:, 2:] - a[:, :-2]
    gy[1:-1, :] = a[2:, :] - a[:-2, :]
    e = np.hypot(gx, gy)
    # blur 3x3 so 1-cell shifts still match
    k = np.zeros_like(e)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            k += np.roll(np.roll(e, dy, 0), dx, 1)
    return k.flatten()


def _cos(a, b):
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def fingerprints(audit, reel_id, style, W, H):
    out = []
    for s in audit["scenes"]:
        for smp in s["samples"]:
            out.append({"reel": reel_id, "scene": s["name"], "type": s["scene"], "custom": s["custom"], "style": style,
                        "t": smp["t"], "layout": _layout(smp["boxes"], W, H).round(3).tolist(),
                        "shape": _edges(smp["lum"]).round(3).tolist()})
    return out


def load_lib():
    return json.load(open(LIB)) if os.path.exists(LIB) else []


def check(proj, register=False, lib=None):
    rd = os.path.join(proj, ".reel")
    tl = json.load(open(os.path.join(rd, "timeline.resolved.json")))
    ap = os.path.join(rd, "audit.json")
    if not os.path.exists(ap):
        from . import render as R
        R.audit(proj)
    audit = json.load(open(ap))
    reel_id = "%s#%s" % (tl.get("name") or os.path.basename(os.path.abspath(proj)), tl.get("seed"))
    mine = fingerprints(audit, reel_id, tl["style"]["pack"], tl["w"], tl["h"])
    lib = load_lib() if lib is None else lib
    others = [f for f in lib if f["reel"] != reel_id]
    per_scene = {}
    for f in mine:
        best = (0.0, None)
        for o in others:
            sim = 0.55 * _cos(np.array(f["layout"]), np.array(o["layout"])) + 0.45 * _cos(np.array(f["shape"]), np.array(o["shape"]))
            if sim > best[0]:
                best = (sim, o)
        cur = per_scene.get(f["scene"])
        if cur is None or best[0] > cur[0]:
            per_scene[f["scene"]] = best
    dur = {s["name"]: s["dur"] for s in tl["scenes"]}
    flagged = {k: v for k, v in per_scene.items() if v[0] >= THRESH}
    share = sum(dur.get(k, 0) for k in flagged) / (tl["duration"] or 1)
    ok = share <= MAX_SHARE
    details = []
    for s in tl["scenes"]:
        sim, o = per_scene.get(s["name"], (0, None))
        details.append("%-18s %-10s best match %.2f %s%s" % (s["name"], s["scene"], sim,
                       ("vs %s / %s (%s)" % (o["reel"], o["scene"], o["style"])) if o else "",
                       "   <- RE-SKIN" if sim >= THRESH else ""))
    res = {"ok": ok, "share_reskinned": round(share, 3), "threshold": THRESH, "max_share": MAX_SHARE,
           "summary": "novelty: %s — %.0f%% of runtime matches an existing scene (limit %.0f%%), library %d fingerprints" %
                      ("OK" if ok else "FAIL", share * 100, MAX_SHARE * 100, len(others)),
           "details": details, "scenes": {k: round(v[0], 3) for k, v in per_scene.items()}}
    json.dump(res, open(os.path.join(rd, "novelty.json"), "w"), indent=1)
    if register:
        lib = [f for f in lib if f["reel"] != reel_id] + mine
        os.makedirs(os.path.dirname(LIB), exist_ok=True)
        json.dump(lib, open(LIB, "w"))
    return res
