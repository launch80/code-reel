"""render — drive the compiled player in headless Chromium.

  stills   PNGs at given times                      .reel/stills/tSS.SS.png
  audit    text boxes + thumbnails per scene       .reel/audit.json  (layout lint + novelty input)
  contact  one annotated sheet of every scene      .reel/contact.png
  video    all frames, parallel workers, lossless  .reel/frames.mkv  (FFV1; build does the one lossy encode)

Every mode loads the same .reel/index.html the preview uses, so what you see
in the browser is exactly what renders.
"""
import asyncio
import base64
import json
import os
import subprocess
import sys
import tempfile

from playwright.async_api import async_playwright

ARGS = ["--allow-file-access-from-files", "--force-color-profile=srgb", "--disable-lcd-text",
        "--force-device-scale-factor=1", "--disable-gpu-vsync"]


class RenderError(Exception):
    pass


def _tl(proj):
    p = os.path.join(proj, ".reel", "timeline.resolved.json")
    if not os.path.exists(p):
        raise RenderError("not compiled — run: reel.py compile %s" % proj)
    tl = json.load(open(p))
    if tl.get("errors"):
        raise RenderError("compile has errors — fix them first:\n  " + "\n  ".join(tl["errors"]))
    return tl


async def _page(browser, proj, tl, dpr, audit=False):
    pg = await browser.new_page(viewport={"width": tl["w"], "height": tl["h"]})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    url = "file://" + os.path.join(os.path.abspath(proj), ".reel", "index.html") + "?render&dpr=%d%s" % (dpr, "&audit" if audit else "")
    await pg.goto(url)
    ok = await _eval(pg, "window.ready")
    if not ok or errors:
        msg = await _eval(pg, "window.__REEL_ERROR__ || ''")
        raise RenderError("JS error at player startup: %s %s" % (msg, " | ".join(errors[:5])))
    pg._reel_errors = errors
    return pg


async def _eval(pg, js, arg=None):
    from playwright.async_api import Error as PWError
    try:
        return await (pg.evaluate(js, arg) if arg is not None else pg.evaluate(js))
    except PWError as e:
        msg = str(e).split("\n")
        where = next((l.strip() for l in msg if ".js:" in l and "/engine/player.js" not in l), "")
        raise RenderError("JS error: %s %s" % (msg[0].replace("Page.evaluate: ", ""), where))


async def _grab(pg, t, fmt="png"):
    d = await _eval(pg, "(render(%r), document.getElementById('c').toDataURL('image/%s'))" % (float(t), fmt))
    if pg._reel_errors:
        raise RenderError("JS error while rendering t=%.3f: %s" % (t, pg._reel_errors[0]))
    return base64.b64decode(d.split(",", 1)[1])


def _launch(p):
    kw = {"args": ARGS}
    if os.environ.get("CHROME_PATH"):
        kw["executable_path"] = os.environ["CHROME_PATH"]
    return p.chromium.launch(**kw)


# ------------------------------------------------------------------ stills
async def _stills(proj, times, dpr):
    tl = _tl(proj)
    out = os.path.join(proj, ".reel", "stills")
    os.makedirs(out, exist_ok=True)
    paths = []
    async with async_playwright() as p:
        b = await _launch(p)
        pg = await _page(b, proj, tl, dpr)
        for t in times:
            t = min(max(0.0, float(t)), tl["duration"] - 1.0 / tl["fps"])
            path = os.path.join(out, "t%05.2f.png" % t)
            open(path, "wb").write(await _grab(pg, t))
            paths.append(path)
        await b.close()
    return paths


def stills(proj, times, dpr=1):
    return asyncio.run(_stills(proj, times, dpr))


def scene_sample_times(tl, fracs=(0.35, 0.62, 0.86)):
    """Times inside each scene that avoid transition windows."""
    wins = [(x["t"] - x["dur"] / 2 - 0.02, x["t"] + x["dur"] / 2 + 0.02) for x in tl["events"]["transitions"] if not x["self"]]
    wins += [(x["t"] - 0.1, x["t"] + 0.2) for x in tl["events"]["transitions"] if x["self"]]
    out = []
    for s in tl["scenes"]:
        ts = []
        for f in fracs:
            t = s["t0"] + f * s["dur"]
            for a, b in wins:
                if a <= t <= b:
                    t = a - 0.01 if t - a < b - t else b + 0.01
            t = min(max(t, s["t0"] + 0.01), s["t1"] - 0.02)
            ts.append(round(t, 3))
        out.append((s, ts))
    return out


# ------------------------------------------------------------------ audit
AUDIT_JS = """(t) => { const boxes = auditFrame(t);
  const c = document.getElementById('c'); const s = document.createElement('canvas'); s.width = 64; s.height = 36;
  const g = s.getContext('2d'); g.drawImage(c, 0, 0, 64, 36); const d = g.getImageData(0, 0, 64, 36).data;
  const lum = []; for (let i = 0; i < d.length; i += 4) lum.push(Math.round(0.299*d[i] + 0.587*d[i+1] + 0.114*d[i+2]));
  const big = document.createElement('canvas'); big.width = 480; big.height = Math.round(480 * c.height / c.width);
  const bg = big.getContext('2d'); bg.drawImage(c, 0, 0, big.width, big.height);
  const bd = bg.getImageData(0, 0, big.width, big.height).data; let lit = 0, n = 0;
  const bgc = STYLE.palette.bg; const br = parseInt(bgc.slice(1,3),16), bgg = parseInt(bgc.slice(3,5),16), bb = parseInt(bgc.slice(5,7),16);
  for (let y = Math.round(big.height*0.12); y < big.height*0.88; y++) for (let x = Math.round(big.width*0.04); x < big.width*0.96; x++) {
    const i = (y*big.width + x)*4; n++; if (Math.abs(bd[i]-br) + Math.abs(bd[i+1]-bgg) + Math.abs(bd[i+2]-bb) > 90) lit++; }
  return {boxes, lum, lit: lit / n, W, H, safe: SAFE}; }"""


def _covered(a, occ):
    ix = max(0, min(a["x1"], occ["x1"]) - max(a["x0"], occ["x0"]))
    iy = max(0, min(a["y1"], occ["y1"]) - max(a["y0"], occ["y0"]))
    return ix * iy / max(1.0, (a["x1"] - a["x0"]) * (a["y1"] - a["y0"]))


def _overlap(a, b):
    ix = max(0, min(a["x1"], b["x1"]) - max(a["x0"], b["x0"]))
    iy = max(0, min(a["y1"], b["y1"]) - max(a["y0"], b["y0"]))
    inter = ix * iy
    aa = (a["x1"] - a["x0"]) * (a["y1"] - a["y0"])
    ab = (b["x1"] - b["x0"]) * (b["y1"] - b["y0"])
    return inter / max(1.0, min(aa, ab))


def lint_boxes(boxes, W, H, safe):
    errs, warns = [], []
    # painter's order: an opaque box drawn later hides text drawn earlier underneath it
    vis = []
    for b in boxes:
        if b.get("occ"):
            vis = [v for v in vis if _covered(v, b) < 0.7]
        elif b["a"] >= 0.3 and b["scene"] != "__hud__" and (b["x1"] - b["x0"]) > 2:
            vis.append(b)
    for b in vis:
        if b.get("world"):
            continue          # world-space text (signs etc.) legitimately scrolls through the frame
        if b["x0"] < -2 or b["y0"] < -2 or b["x1"] > W + 2 or b["y1"] > H + 2:
            errs.append("text off-canvas: %r at (%d,%d)-(%d,%d)" % (b["s"], b["x0"], b["y0"], b["x1"], b["y1"]))
        elif b["x0"] < safe["l"] * 0.5 or b["x1"] > W - safe["r"] * 0.5 or b["y0"] < safe["t"] * 0.35 or b["y1"] > H - safe["b"] * 0.35:
            warns.append("text outside title-safe: %r" % b["s"])
    for i in range(len(vis)):
        for j in range(i + 1, len(vis)):
            a, b = vis[i], vis[j]
            if a["s"] == b["s"] and abs(a["x0"] - b["x0"]) < 60 and abs(a["y0"] - b["y0"]) < 60:
                continue           # ghost/glow copies of the same string
            if len(a["s"]) == 1 or len(b["s"]) == 1:
                ov = _overlap(a, b)
                if ov > 0.55:
                    errs.append("glyphs collide: %r / %r" % (a["s"], b["s"]))
                continue
            ov = _overlap(a, b)
            if ov > 0.12:
                errs.append("text overlaps (%.0f%%): %r  x  %r" % (ov * 100, a["s"], b["s"]))
    return errs, warns


async def _audit(proj, dpr):
    tl = _tl(proj)
    res = {"scenes": [], "errors": [], "warnings": []}
    async with async_playwright() as p:
        b = await _launch(p)
        pg = await _page(b, proj, tl, dpr, audit=True)
        for s, ts in scene_sample_times(tl):
            ent = {"i": s["i"], "scene": s["scene"], "name": s["name"], "custom": s["custom"], "samples": []}
            for t in ts:
                try:
                    r = await _eval(pg, AUDIT_JS, t)
                except RenderError as e:
                    raise RenderError("scene %s (%s) at t=%.2f: %s" % (s["name"], s["scene"], t, e))
                if pg._reel_errors:
                    raise RenderError("JS error in scene %s at t=%.2f: %s" % (s["name"], t, pg._reel_errors[0]))
                e, w = lint_boxes(r["boxes"], r["W"], r["H"], r["safe"])
                ent["samples"].append({"t": t, "lit": round(r["lit"], 4), "lum": r["lum"], "boxes": r["boxes"], "errors": e, "warnings": w})
                res["errors"] += ["%s @%.2fs: %s" % (s["name"], t, x) for x in e]
                res["warnings"] += ["%s @%.2fs: %s" % (s["name"], t, x) for x in w]
            if max(x["lit"] for x in ent["samples"]) < 0.004:
                res["errors"].append("%s: scene renders (nearly) blank — nothing drawn in the safe area" % s["name"])
            res["scenes"].append(ent)
        await b.close()
    # de-duplicate repeated messages
    res["errors"] = list(dict.fromkeys(res["errors"]))
    res["warnings"] = list(dict.fromkeys(res["warnings"]))
    json.dump(res, open(os.path.join(proj, ".reel", "audit.json"), "w"))
    return res


def audit(proj, dpr=1):
    return asyncio.run(_audit(proj, dpr))


# ------------------------------------------------------------------ contact sheet
def contact(proj, dpr=1, cols=4):
    from PIL import Image, ImageDraw
    tl = _tl(proj)
    plan = scene_sample_times(tl, fracs=(0.62,))
    times = [ts[0] for _, ts in plan]
    paths = stills(proj, times, dpr)
    tw_ = 480
    th = int(tw_ * tl["h"] / tl["w"])
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw_, rows * (th + 26)), (20, 20, 20))
    dr = ImageDraw.Draw(sheet)
    for k, ((s, _), path) in enumerate(zip(plan, paths)):
        im = Image.open(path).convert("RGB").resize((tw_, th))
        x, y = (k % cols) * tw_, (k // cols) * (th + 26)
        sheet.paste(im, (x, y + 26))
        dr.text((x + 6, y + 6), "%02d %s  [%s%s]  %.2f-%.2fs" % (s["i"] + 1, s["name"], s["scene"], "*" if s["custom"] else "", s["t0"], s["t1"]), fill=(230, 230, 230))
    out = os.path.join(proj, ".reel", "contact.png")
    sheet.save(out)
    return out


# ------------------------------------------------------------------ video
async def _chunk(proj, tl, dpr, f0, f1, path):
    async with async_playwright() as p:
        b = await _launch(p)
        pg = await _page(b, proj, tl, dpr)
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(tl["fps"]),
                               "-c:v", "png", "-i", "-", "-c:v", "ffv1", "-pix_fmt", "rgb24", "-compression_level", "1", path],
                              stdin=subprocess.PIPE)
        try:
            for f in range(f0, f1):
                ff.stdin.write(await _grab(pg, f / tl["fps"]))
                if f % 60 == 0:
                    print("  frame %d" % f, flush=True)
        finally:
            ff.stdin.close()
            if ff.wait() != 0:
                raise RenderError("ffmpeg failed on chunk %s" % path)
        await b.close()


async def _video(proj, dpr, workers):
    tl = _tl(proj)
    n = int(round(tl["duration"] * tl["fps"]))
    rd = os.path.join(proj, ".reel")
    tmp = tempfile.mkdtemp(prefix="chunks_", dir=rd)
    k = max(1, min(workers, n // 30 or 1))
    bounds = [round(i * n / k) for i in range(k + 1)]
    paths = [os.path.join(tmp, "c%02d.mkv" % i) for i in range(k)]
    await asyncio.gather(*[_chunk(proj, tl, dpr, bounds[i], bounds[i + 1], paths[i]) for i in range(k)])
    lst = os.path.join(tmp, "list.txt")
    open(lst, "w").write("".join("file '%s'\n" % p for p in paths))
    out = os.path.join(rd, "frames.mkv")
    r = subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", out])
    if r.returncode:
        raise RenderError("concat failed")
    for p in paths + [lst]:
        os.remove(p)
    os.rmdir(tmp)
    probe = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                            "stream=nb_read_frames", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    if probe and int(probe) != n:
        raise RenderError("frames.mkv has %s frames, expected %d" % (probe, n))
    return out


def video(proj, dpr=2, workers=None):
    workers = workers or int(os.environ.get("REEL_WORKERS", max(1, min(6, (os.cpu_count() or 2) - 1))))
    return asyncio.run(_video(proj, dpr, workers))


if __name__ == "__main__":
    print(__doc__)
    sys.exit(0)
