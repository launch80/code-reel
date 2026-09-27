#!/usr/bin/env python3
"""Render the reel — driven entirely by timeline.json (no duplicated timing).

  python3 render.py stills 1.0,4.5,9.8   -> PNG stills in ./stills/ (fast checks)
  python3 render.py video                -> frames.mkv (lossless FFV1 intermediate, 60fps)

frames.mkv is a LOSSLESS intermediate (FFV1, RGB, no chroma subsampling) — build.sh
does the single lossy encode from it, so nothing is ever double-compressed. With
DPR=2 (default) the canvas is drawn at 2x device pixels and build.sh downscales
with Lanczos to 1920x1080 for true supersampled anti-aliasing. Set DPR=1 to render 1:1.

Frames are grabbed via canvas.toDataURL (the canvas bitmap itself, full 3840x2160
at DPR=2) — NOT a viewport screenshot, which would only see the top-left quarter.

Env: DPR (default 2), TIMELINE (default ./timeline.json), CHROME_PATH (fallback
browser binary if Playwright's Chromium isn't installed).
"""
import sys, subprocess, base64, asyncio, json, os
from pathlib import Path
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
TL = json.load(open(os.environ.get("TIMELINE", HERE / "timeline.json")))
FPS = TL.get("fps", 60)
DUR = sum(s["dur"] for s in TL["timeline"])
W, H = TL.get("w", 1920), TL.get("h", 1080)
DPR = int(os.environ.get("DPR", "2"))
# Optional: point at a specific Chrome/Chromium if Playwright's isn't installed
CHROME = os.environ.get("CHROME_PATH")
TIMELINE_JSON = json.dumps(TL)


async def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("stills", "video"):
        print(__doc__); return
    mode = sys.argv[1]
    async with async_playwright() as p:
        # --force-color-profile=srgb: deterministic sRGB output regardless of host
        # display profile; keep canvas compositing grayscale (no subpixel LCD text).
        kw = {"args": ["--allow-file-access-from-files", "--force-color-profile=srgb",
                       "--disable-lcd-text", "--force-device-scale-factor=1"]}
        if CHROME: kw["executable_path"] = CHROME
        b = await p.chromium.launch(**kw)
        pg = await b.new_page(viewport={"width": W, "height": H})
        pg.on("pageerror", lambda e: print("JS ERROR:", e))
        # inject the timeline before any page script runs — reel.html builds
        # CUTS/SC/IMPACTS/DUR from it; render.py and audio.py read the same file
        await pg.add_init_script(f"window.__TIMELINE__={TIMELINE_JSON};")
        await pg.goto((HERE / "reel.html").as_uri() + f"?render&dpr={DPR}")
        await pg.evaluate("window.ready")
        grab = "document.getElementById('c').toDataURL('image/png')"
        if mode == "stills":
            out = HERE / "stills"; out.mkdir(exist_ok=True)
            times = [float(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0.8, 3.4, 5.6, 8.5, 11.9, 14.0]
            for t in times:
                # PNG (not JPEG) so the review loop sees real banding/AA artifacts
                d = await pg.evaluate(f"(render({t}),{grab})")
                (out / f"t{t:05.2f}.png").write_bytes(base64.b64decode(d.split(",")[1]))
                print("wrote", out / f"t{t:05.2f}.png")
        else:
            # Lossless intermediate: FFV1 in Matroska, RGB24. build.sh does the
            # one and only lossy encode.
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error",
                                   "-f", "image2pipe", "-framerate", str(FPS),
                                   "-c:v", "png", "-i", "-",
                                   "-c:v", "ffv1", "-pix_fmt", "rgb24",
                                   "-compression_level", "1", HERE / "frames.mkv"],
                                  stdin=subprocess.PIPE)
            n = int(round(DUR * FPS))
            try:
                for f in range(n):
                    # exact frame time from the integer frame index — never
                    # accumulates float drift; every frame is on the 60fps grid
                    d = await pg.evaluate(f"(render({f / FPS}),{grab})")
                    ff.stdin.write(base64.b64decode(d.split(",")[1]))
                    if f % 60 == 0: print(f"frame {f}/{n}", flush=True)
            finally:
                ff.stdin.close()
                if ff.wait() != 0: sys.exit(f"ffmpeg failed ({ff.returncode})")
            print("wrote frames.mkv (lossless)")
        await b.close()

asyncio.run(main())
