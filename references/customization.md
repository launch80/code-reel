# Customization map — where each knob lives

All paths relative to the scaffolded project directory. **Scene content and params are in
`references/scenes.md`** — this file covers the pipeline internals and the QA checklist.

## reel.html — structure

| Section | What it is |
|---|---|
| `@font-face` blocks (top `<style>`) | Font loading. woff2 files live in `fonts/`. Add new fonts here + copy the woff2 in. |
| `let W,H,FPS,BPM,DUR,TL` | Derived from the timeline at load (`buildTimeline`) — never hardcoded. |
| `C` / `A()` / `Hh()` | Palette + theme-color helpers (`A(a)` = accent rgba at alpha a). All colors route through `theme` in timeline.json. |
| `REG` | The scene registry — see scenes.md for the contract of each scene type. |
| `buildTimeline(tl)` | Derives `CUTS`, `SC` (HUD labels), `IMPACTS`, `DUR`, canvas size from the timeline. |
| `background(t)` | Perspective grid floor, warm glow blobs, dot matrix. |
| `hud(t)` | Corner brackets, brand line, REC dot + timecode, scene label, frame counter, progress bar with cut ticks. |
| `post(t,fi)` | Glitch slices + chromatic split at cuts, flash, scanlines, film grain, vignette, fade in/out. Runs in DEVICE pixels (identity transform) so 1px scanlines/grain stay pixel-exact at any DPR. |
| `render(t)` | Master: `background → (shake+zoom) scene → hud → post`. Sets `setTransform(DPR,…)` so all scene code stays in logical units. Dispatch is derived from the timeline. |
| `window.ready` / `loadTimeline` | Loads `window.__TIMELINE__` (injected by render.py) or fetches `timeline.json` (preview mode). |
| bottom `if(!location.search.includes('render'))` block | Live preview player. `?render` skips it. |

## render.py

- Reads `timeline.json` for `fps/dur/w/h` — no duplicated timing. `TIMELINE` env points at another file.
- `DPR` env (default 2): the canvas draws at 2x device pixels (`?render&dpr=2`) for true
  supersampled AA; frames are grabbed via `canvas.toDataURL` (the canvas bitmap —
  NOT a viewport screenshot, which would only see the top-left quarter at DPR=2).
- `python3 render.py stills 2.1,5.6,8.4` → `stills/t*.png` (fast iteration; lossless).
- `python3 render.py video` → `frames.mkv` — LOSSLESS intermediate (FFV1, RGB), never
  double-compressed; the single lossy encode happens in build.sh.
- Chromium is launched with `--force-color-profile=srgb` so output is deterministic sRGB on any host.
- `CHROME_PATH` env var overrides Playwright's Chromium.

## audio.py — fully derived, normally no edits

`audio.py` reads `timeline.json` and derives: beats from `bpm` (between the first cut
and the last cut), kick/hat/pad, risers + big impacts + 2kHz blips at cuts, impacts at
every `slams`/kinetic-word/chart-impact/quote-slam, typing clicks from `cmd`/`typing`
strings, counter ticks from the counter/chart windows, the bell from the endcard.
A hand-written `audio.json` overrides the derived events (see the docstring):
`{"beats": [...], "cuts": [...], "slams": [...], "typing": [[t,dur,n],...], "ticks": [[t0,t1],...], "bell": t}`.

## build.sh

`python3 render.py video` (lossless frames.mkv) → `python3 audio.py` → ONE lossy encode:
Lanczos downscale (2x→1x when `DPR=2`), `in_range=pc:out_range=tv`, `format=yuv420p`,
then `setparams=colorspace=bt709:color_primaries=bt709:color_trc=bt709:range=tv` — the
`setparams` filter is REQUIRED: the `-colorspace/-color_trc/-color_primaries` CLI flags
alone leave primaries/transfer untagged in modern ffmpeg, and players then guess BT.601
and colors shift. Env: `OUT` (default reel.mp4), `OUT_W/OUT_H` (default 1920×1080;
use 1080×1920 for 9:16), `DPR` (must match render.py), `CRF` (default 17).

## validate.py

`python3 validate.py [timeline.json]` — exit 0 means the timeline is renderable:
required params per scene type, cuts on the beat grid, whole-frame boundaries,
word/impact/slam offsets inside their scenes, `months`/`grow` length match.

## QA checklist (learned the hard way)

1. HUD: REC dot/label vs timecode overlap — keep them at distinct x positions (template: dot at `W-440`, label `W-422`, TC right-aligned at `W-100`).
2. Counter + unit label: measure the FINAL (widest) string, not the current one.
3. Background: no visible seam where grid floor meets glow (gradients must reach 0 alpha at the boundary, or cross it).
4. Flash alpha at cuts ≤ ~0.3, sub-impacts ≤ ~0.14 — otherwise the frame washes out.
5. Serif mask-wipe lines (`wipeLine`) need enough width margin for the full string.
6. Deterministic everything: no `Math.random()`, no `Date.now()` inside `render()`; use `rng(seed)` and `fi` (frame index).
7. `shadowBlur` is applied in DEVICE pixels by Chrome (not scaled by the CTM) — with `DPR=2` every manual `shadowBlur` must be `*DPR` or glows look half-size. `txt()` already does this.
8. Big numbers + unit labels: `cards` auto-shrinks the big-number font until the FINAL (widest) string plus unit fits the card padding — keep that loop if you change `big`/`unit` strings.
9. Kinetic annotations must not collide with the word (the scene checks the measured `wEnd` against the annotation column — keep that logic).
10. After any timing change, re-run `validate.py` and re-still at the new boundaries before committing to the full render.
11. New scene types: keep all timing relative to the scene duration `d`, and register slams in `sceneSlams()` (reel.html) + `derive_events()` (audio.py) so audio stays in sync.
