---
name: code-reel
description: Generate a motion graphics video ("reel") entirely in code — HTML canvas animation rendered frame-by-frame in headless Chromium, encoded with ffmpeg, with a synthesized numpy soundtrack. Use when the user asks to make/renders a promo video, motion reel, launch video, stat animation, showreel, or a kinetic-typography/counter/chart animation. The Launch80 15s showreel is the working template.
---

# Code reel

Build a short motion-graphics video with no video editor: one HTML file draws every frame on a canvas, Playwright + headless Chromium captures frames at 60fps into ffmpeg, numpy synthesizes the soundtrack, ffmpeg muxes audio+video.

## 1. Collect parameters

The user's request (or `/skill:code-reel ...` arguments) may include `key=value` pairs. Recognized keys and defaults:

| Key | Meaning | Default |
|---|---|---|
| `duration` | total length in seconds | `15` |
| `bpm` | beat grid; cuts must land on beats | `120` (beat = 0.5s) |
| `fps` | frame rate | `60` |
| `size` | `1920x1080` (16:9) or `1080x1920` (9:16) | `1920x1080` |
| `out` | output filename | `reel.mp4` |
| `theme` | hex accent color | `#e85d04` |
| `bg` | background hex | `#0b0b0c` |
| `fonts` | heading/body/mono/display fonts | template fonts (see §3) |
| `audio` | `on` or `off` | `on` |
| `brand` | brand name / site to match (scrape colors, fonts, copy) | — |
| free text | content: scenes, stats, numbers, taglines, end-card text | — |

If `duration`, scene content, or the key numbers/stats are missing, ask ONE short question bundling everything missing. If the user says "just do it", use the template's structure and their content, keep 15s.

If `brand` is given, extract real hex colors, font families and copy lines from that site (curl/fetch the HTML + CSS) before writing text into the reel.

## 2. Scaffold a project

```bash
PROJ=<project-dir>            # e.g. ./reel-<slug>
mkdir -p "$PROJ"
cp <skill-dir>/templates/{reel.html,render.py,audio.py,build.sh,validate.py,timeline.json,requirements.txt} "$PROJ/"
cp -r <skill-dir>/fonts "$PROJ/fonts"
```

One-time machine setup (check first; skip if already installed): `pip install -r requirements.txt`, `python -m playwright install chromium`, `ffmpeg` on PATH.

## 3. Compose the timeline (no drawing code)

Open `references/scenes.md` in this skill directory — it is the contract for every scene type and its `p` params. The reel is defined ENTIRELY in `timeline.json`: scenes, durations, content, theme, HUD. `reel.html` derives `CUTS`/`SC`/`IMPACTS`/dispatch from it; `audio.py` derives the whole score (beats, risers, slams, typing clicks, ticks, bell) from the same file. Nothing else needs editing for a normal reel.

Core rules:

- **Timeline first.** Choose scenes for the user's narrative arc (opener → claims → proof → close is the default), assign each a `dur` that is a multiple of the beat (`60/bpm` s — 0.5s at 120bpm), and write each scene's `p` content object. Typical arc: `terminal` (1.5) → `kinetic` (2.5) → `cards` (3) → `counter` or `quote` (3) → `chart` (2.5) → `endcard` (2.5). Swap in `split` for A/B comparisons, `quote` for testimonials.
- **Recolor via `theme`** (`accent`/`hot`/`bg`/`cream`) and relabel via `hud` (brand/series/line) — do not touch palette constants. `theme` recolors the whole reel including glows, flashes and the post layer.
- **All times in `p` are relative to the scene start.** Kinetic word `offset`s, chart `impact`, quote `slam` must land on the beat grid (multiples of 0.5s at 120bpm) so hits land on beats.
- **Validate before rendering:** `python3 validate.py` — checks required params, beat-grid cuts, whole-frame boundaries, and word/impact offsets. Never run a full render with a failing validation.
- **If the user needs a scene type that doesn't exist**, add `REG.myscene = (lt, d, p) => {...}` to reel.html (all timing relative to `d`), reuse the motion primitives (`prog`, easings, `txt`, `tw`, `typed`, `rrect`, `rng`, `wipeLine`, `dashed`, `A()`/`Hh()` theme colors), register it in `validate.py` + `sceneSlams()`/`derive_events()` in audio.py, and document it in scenes.md. For new scene types: `DPR`-aware `shadowBlur` (`*DPR`), and measure the FINAL string with `tw()` before positioning labels next to counters.
- **Vertical (9:16):** `"w":1080,"h":1920` in timeline.json + `OUT_W=1080 OUT_H=1920` in build.sh. The 16:9 scenes are laid out for 1920×1080; a 9:16 reel needs a vertical layout pass on the scenes (check stills closely).

## 4. Review loop (always, before full render)

1. `python3 validate.py` first, then `python3 render.py stills <times>` — pick 1–2 times per scene (mid-entrance and settled). Stills are PNG (no JPEG artifacts masking banding). Render at `DPR=2` (default) for 2x supersampled pixels; `DPR=1 python3 render.py stills ...` for quick checks.
2. Read the stills with the image tool (or build a contact sheet with `ffmpeg -i t%05.2f.jpg ...`). Check specifically for:
   - overlapping text (labels next to counters whose digits change width — measure the FINAL string with `tw()`, not the current one; the template's "tok/s" label uses `tw('888',BF)` deliberately)
   - HUD element collisions (REC dot vs timecode vs brand line)
   - visible seams in gradients/glow (e.g., grid floor meeting glow)
   - flashes washing out the frame (keep flash alpha ≤ 0.3)
   - text clipping outside its clip rect
3. Fix, re-still only the changed times, then full render: `./build.sh` (or `OUT=... ./build.sh`). It runs render.py (LOSSLESS FFV1 `frames.mkv`, 2x res with `DPR=2`), audio.py (score derived from the timeline), then ONE lossy encode (Lanczos downscale, BT.709 tags, `yuv420p`, CRF 17 — override with `CRF=`, size with `OUT_W/OUT_H`). Expect ~6–10 min for 15s at 1080p60 with `DPR=2` (~3–4 min with `DPR=1`).
4. After the full render, spot-check 3–4 frames from the MP4 (`ffmpeg -ss <t> -i reel.mp4 -frames:v 1 check.jpg`) and report the output path + duration to the user.

## 5. Live preview

Tell the user they can open `reel.html` in Chrome for a playable preview (space = play/pause, arrows = step a frame, draggable scrubber, sound from `audio.wav`; if `file://` blocks audio, `python -m http.server` in the project dir). After editing, they refresh; you can also run `python render.py stills` for instant checks without a full render.
