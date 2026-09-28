---
name: code-reel
description: Make an original motion-graphics or illustrated 2D video entirely in code (HTML canvas → headless Chromium → ffmpeg, synthesized soundtrack) — launch reels, promos, explainers, showreels, data stories, kinetic type, and flat-vector character/world animation (e.g. a penguin biking through town with pop-up ads). Use when the user asks for a video, reel, promo, animation, motion graphics or showreel.
---

# code-reel

Every frame is drawn by code written **for this video**. The skill is one
pipeline (`reel.py`) with gates — compile, layout audit, novelty, QC — that
run the same way whoever does the creative work: you (the agent), a local
model, or the test suite replaying a recorded session.

```
interview → brief.md → init (seed) → [brand] → claims.json → treat → pick → timeline → scenes → review → run --draft → run --final → register
             you        reel.py        reel.py   you          direct   you/user  direct   direct   reel.py   reel.py        reel.py      reel.py
```

`S=<skill dir>`; every command is `python3 $S/reel.py <cmd> <project> ...`.
Setup once: `pip install -r $S/requirements.txt && python3 -m playwright install chromium` and ffmpeg on PATH.

## 1. Interview → brief.md
Run `references/interview.md` (one question per message, defaults offered,
skip what the request already answers). Output: `brief.md` with the purpose,
format (16:9 / 9:16 / 1:1, seconds), every claim with its source, the look
(brand site / pack / "surprise me"), must-include / must-avoid.

## 2. Project, seed, brand, claims
```bash
reel.py init <proj> --seed <n> [--style <pack>] [--size 16:9|9:16|1:1]   # omit --seed for a fresh random one
reel.py brand <proj> https://brand.site        # palette + fonts + copy -> brand.json (+ suggested style override)
```
The **seed is the variation knob**: every creative choice nobody pinned
(treatment assignment, transitions, directions, key of the score, model
sampling) derives from it. Same seed + same answers = the same video; a new
seed = a different video. Write every on-screen number into `claims.json`
(`{"id": {"value", "display", "source", "url"}}`) — see `references/claims.md`.

## 3. Treatments → pick
```bash
reel.py direct <proj> treat --backend agent --candidates 3
```
The seed assigns each treatment a different style pack and structure; the
treatments must differ in metaphor too (the gate rejects look-alikes). **Look
at `.reel/treatments.png`** (one style frame each), then pick — ask the user if
they are there, otherwise choose the one that draws the brief's nouns best:
`reel.py direct <proj> pick --pick N`.

## 4. Timeline → scenes
```bash
reel.py direct <proj> timeline --backend agent     # timeline.json + claims refs, compile-gated
reel.py direct <proj> scenes   --backend agent     # one scenes/<name>.js per custom scene
```
Each scene is gated: syntax → compile → layout audit → novelty, with a repair
round that carries the exact report. After a scene passes, **open
`.reel/review/<name>.png`** and judge it like a designer; fix by editing the
file (then `reel.py review`). Custom scenes must carry the reel (`--final`
requires ≥50% of runtime); the 16 blueprints are references and occasional
building blocks. Scene API: `references/api.md`. Worlds/characters/props:
the illustration section of the API (world camera, parallax, IK rigs, props,
storefronts, anchored pop-outs) — see `examples/penguin`.

### Backends — who answers the prompts
| `--backend` | who writes | how |
|---|---|---|
| `agent` (default) | you, the agent running this skill | the command writes `.reel/llm/<key>.prompt.md`, exits **10**; read it, write `.reel/llm/<key>.answer.<json|js>`, re-run the same command |
| `ollama` / `openai` | a local model (`--model`, `--base-url`) | same prompts, same gates, answers recorded to `.reel/llm/` |
| `mock` | tests / replays | `--fixtures <dir>` of recorded answers (any past `.reel/llm/`) |

Hand-writing is fine too: edit `timeline.json` / `scenes/*.js` directly — the
same compile/audit/novelty/QC gates apply. Details: `references/director.md`.

## 5. Review (always before rendering the whole thing)
```bash
reel.py review <proj>        # contact sheet + audit + novelty + the critique checklist
```
Open `.reel/contact.png`, answer `references/critique.md` in `review.md`, fix,
repeat. Zero audit errors and novelty OK before any full render.

## 6. Render
```bash
reel.py run <proj> --draft             # DPR 1: compile → audit → render → audio → build → qc (a few minutes)
reel.py run <proj> --final --register  # DPR 2, strict claims/novelty; registers the reel in the novelty library
```
Look at 4–6 frames of the MP4 (`ffmpeg -ss <t> -i reel.mp4 -frames:v 1 f.png`),
especially mid-transition. `.reel/qc_report.xlsx` has the measured specs and
the human checklist; report its READY line to the user. Live preview:
open `<proj>/.reel/index.html` in a browser (space, arrows, scrubber, sound).

## Looks, sound, formats
- 7 style packs (`reel.py styles`): signal, editorial, swiss, blueprint, soft,
  terminal, storybook. Override any piece in `timeline.json` `"style"`:
  palette, fonts, bg, hud, post, camera, transitions, motion, glow, audio, bpm.
  Per scene: `"look": {"bg", "camera"}`, `"transition": "push"|{...}`.
  Full menu: `references/styles.md`.
- Durations in **beats** (`"beats": 4`) survive style/bpm changes; bpm must
  divide 3600 (90, 100, 120, 144, 150).
- Score presets: pulse, ambient, minimal, glitch, lofi, cinematic — every cut,
  slam, typing run and counter gets a sound; `"audio": {"track": "assets/x.mp3"}` for licensed music.
- 9:16 / 1:1: blueprints and the API are responsive (`U`, `SAFE`); still-check every scene.

## Honest scope
Draws: typography, data, diagrams, UI mockups, code, maps/routes, and flat
2D vector illustration — characters, vehicles, towns, props, camera moves
through a world. Does not do: photoreal footage, 3D renders, lip-synced
characters, or copyrighted characters/logos you don't have rights to.
