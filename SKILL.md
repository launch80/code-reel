---
name: code-reel
description: Generate a motion graphics video ("reel") entirely in code — HTML canvas animation rendered frame-by-frame in headless Chromium, encoded with ffmpeg, with a synthesized numpy soundtrack. Use when the user asks to make/renders a promo video, motion reel, launch video, stat animation, showreel, or a kinetic-typography/counter/chart animation. The Launch80 15s showreel is the working template.
---

# Code reel

Build a short motion-graphics video with no video editor: one HTML file draws every frame on a canvas, Playwright + headless Chromium captures frames at 60fps into ffmpeg, numpy synthesizes the soundtrack, ffmpeg muxes audio+video.

**Step 0 of every run: interview the user** (`references/interview.md`) — interactively, one question at a time with defaults offered, follow-ups when an answer opens a door; decisions echoed as a table and saved to `brief.md` before anything is scaffolded.

## 0. Three ways to use this skill (pick one)

| Mode | Who writes the content | Who writes scene code | How |
|---|---|---|---|
| **1 · Director** | an LLM composes the whole timeline from a written brief | nobody — the 8 shipped archetypes only | `python3 director.py --mode invent --brief brief.md --model <local-model>` |
| **2 · Blueprint** | you + a local LLM, iterating in an agent session | the LLM writes NEW scene types in `scene_custom.js` | read `references/blueprints.md`; the LLM adds `defineScene('name', fn)` — never fork `reel.html` |
| **3 · Fill-in-blank** | you (or the director pre-fills) | nobody | copy `templates/blank.json`, fill every `<SLOT>`, validate |

All three converge on the same frozen `timeline.json` and the same deterministic pipeline (`validate.py` → `render.py` → `audio.py` → `build.sh` → `qc.py`). The LLM never produces pixels — it produces JSON; timing lives only in the frozen file. Mode 1/3 output is byte-reproducible; mode 2 adds a `scene_custom.js` beside the project files (validate with `--allow-custom`).

```
brief ──► director.py ──► timeline.json (+_meta.json) ──► validate.py ──► render.py ──► audio.py ──► build.sh ──► qc.py
             (mode 1)        (mode 3: blank.json)          (mode 2: + scene_custom.js)      frames.mkv ─┘        reel.mp4 + qc_report.xlsx
```

## 1. Interview first (always — before any file is written)

**Open every invocation with an interactive interview.** Read `references/interview.md` and run it: one question per message, conversational — never a form dump. Cover the knobs that drive the pipeline — topic, platform/aspect, duration, on-screen claims + sources, who writes the story (director / agent / fill-in / blueprint), look (palette/HUD/grain/audio), and render plan (draft→approve→final vs straight-to-final). Follow up briefly when an answer opens a door ("match our brand" → *which site?*); skip questions the request already answered; take defaults when the user is stuck or says "just do it". Close by echoing the decision table and what happens next.

- **One question per message, then wait.** Only ask about gaps — if the request already contains `key=value` pairs or prose that answers a question, acknowledge in one line and move on. Follow-ups are allowed but stay short (one question). If the user says "just do it"/"surprise me"/"stop asking" at any point, fill the rest with defaults, echo the table, and proceed without waiting.
- **Never ask what doesn't change a file** — the score is derived, so there is no music question; aspect changes `OUT_W/OUT_H`; DPR changes wall-clock time; claims feed the QC fact-check.
- **Save the answers to `brief.md`** in the project dir — in mode 1 that exact file is the `director.py --brief` input, and it is the human record behind the QC fact-check.

Recognized keys if provided up front, and defaults:

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

If `brand` is given, extract real hex colors, font families and copy lines from that site (curl/fetch the HTML + CSS) before writing text into the reel.

**Claims without sources are a QC event, not a blocker.** If the user can't source a number yet, write the reel with it, add no `"sources"` entry (or mark it), and let the Fact Check tab flag it `Medium risk` — say so out loud in the closing echo. Never silently invent a statistic and present it as fact: placeholders stay placeholders.

## 2. Scaffold a project

```bash
PROJ=<project-dir>            # e.g. ./reel-<slug>
mkdir -p "$PROJ"
cp <skill-dir>/templates/{reel.html,render.py,audio.py,events.py,build.sh,validate.py,qc.py,director.py,timeline.json,blank.json,requirements.txt} "$PROJ/"
cp -r <skill-dir>/fonts "$PROJ/fonts"
```

One-time machine setup (check first; skip if already installed): `pip install -r requirements.txt` (playwright, numpy, openpyxl for the QC workbook; scipy optional), `python -m playwright install chromium`, `ffmpeg` on PATH.

## 3. Compose the timeline (no drawing code)

Open `references/scenes.md` in this skill directory — it is the contract for every scene type and its `p` params. The reel is defined ENTIRELY in `timeline.json`: scenes, durations, content, theme, HUD. `reel.html` derives `CUTS`/`SC`/`IMPACTS`/dispatch from it; `audio.py` derives the whole score (beats, risers, slams, typing clicks, ticks, bell) from the same file. Nothing else needs editing for a normal reel.

Core rules:

- **Timeline first.** Choose scenes for the user's narrative arc (opener → claims → proof → close is the default), assign each a `dur` that is a multiple of the beat (`60/bpm` s — 0.5s at 120bpm), and write each scene's `p` content object. Typical arc: `terminal` (1.5) → `kinetic` (2.5) → `cards` (3) → `counter` or `quote` (3) → `chart` (2.5) → `endcard` (2.5). Swap in `split` for A/B comparisons, `quote` for testimonials.
- **Recolor via `theme`** (`accent`/`hot`/`bg`/`cream`) and relabel via `hud` (brand/series/line) — do not touch palette constants. `theme` recolors the whole reel including glows, flashes and the post layer.
- **All times in `p` are relative to the scene start.** Kinetic word `offset`s, chart `impact`, quote `slam` must land on the beat grid (multiples of 0.5s at 120bpm) so hits land on beats.
- **Validate before rendering:** `python3 validate.py` — checks required params, beat-grid cuts, whole-frame boundaries, and word/impact offsets. Never run a full render with a failing validation.
- **If the user needs a scene type that doesn't exist**, do NOT edit reel.html — create `scene_custom.js` in the project dir and add `defineScene('myscene', (lt, d, p) => {...})` (all timing relative to `d`). It runs in reel.html's scope, so every motion primitive is available (`prog`, easings, `txt`, `tw`, `typed`, `rrect`, `rng`, `wipeLine`, `dashed`, `A()`/`Hh()` theme colors, `W/H/DPR`). Then `python3 validate.py timeline.json --allow-custom`. Render stills of the new scene at 25/50/75/100% of its duration before trusting it. Use `DPR`-aware `shadowBlur` (`*DPR`) and measure the FINAL string with `tw()` before positioning labels next to counters. Add the scene's `slams` via the scene's `slams:[]` field or return-time events are automatic (cuts/impacts derive from timing). Full contract + worked example: `references/blueprints.md`.
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
5. **Run QC:** `python3 qc.py reel.mp4 timeline.json` — auto-measures the technical block (codecs, color tags, frame count, loudness via ebur128, black/freeze detection, fast-start) and writes `qc_report.md` + `qc_report.xlsx` (Summary / Test Sequence / Cue Sheet / Tech Specs / Fact Check). Audio-to-cut sync is exact by construction (render + audio share `events.py`); the Fact Check tab lists every on-screen string — numeric claims need a source before publishing (add a `"sources": {"claim": "url"}` map to timeline.json to auto-verify). Fix any FAIL, re-render, re-run. Details: `references/qc.md`.

## 5. Live preview

Tell the user they can open `reel.html` in Chrome for a playable preview (space = play/pause, arrows = step a frame, draggable scrubber, sound from `audio.wav`; if `file://` blocks audio, `python -m http.server` in the project dir). After editing, they refresh; you can also run `python render.py stills` for instant checks without a full render.
