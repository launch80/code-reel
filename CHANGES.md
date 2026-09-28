# code-reel v2 — change log (branch reel-v2)

## Stage A — foundation, accuracy, style packs
- **One pipeline, one entry point:** `reel.py` (init · compile · stills · audit · contact · novelty · review · render · audio · build · qc · run · status · direct). Agents, humans, local models and the test suite all run these same commands.
- **Engine split** into `engine/` (core primitives, looks, blueprint scenes, player). Projects get a pinned copy in `.reel/engine/` at compile time; `.reel/index.html` is both the render target and the live preview (no web server needed).
- **compile** is the single source of truth: expands the style pack, resolves claims, validates every scene against its contract (blueprints via `engine/scenes.json`, project scenes via `/* @meta */`), derives ALL events (cuts, transitions, impacts, typing, ticks, bell, beats) once. The browser and the audio both read the compiled events — the old JS/Python duplicate derivation is gone.
- **Claims ledger (`claims.json`)**: every number on screen is referenced as `"@id"` / `{{id}}`; compile flags unsourced digits (warning in draft, error in `--final`), QC's Fact Check lists each claim with its source.
- **Style packs** (`engine/styles.json`): signal, editorial, swiss, blueprint, soft, terminal, storybook — each picks background, HUD, post, camera, transition pool, motion easing, fonts (15 families bundled), palette, glow, radius, score preset, bpm. Any key can be overridden; bg/camera per scene via `look`.
- **Variation seed** in every timeline: unpinned choices (transition per cut, directions, audio key) derive from it; same seed = same video.
- **Layout audit**: every `txt()` records its on-canvas box; `reel.py audit` flags overlapping text, off-canvas text, text outside title-safe, blank scenes and JS errors (with the scene + file:line). Clip regions (`clipRect`/`withClip`) and opaque occluders (`box`) are understood; world-space text (illustration layers) is exempt from off-canvas checks.
- **Blueprint scenes rewritten**: responsive (16:9 / 9:16 / 1:1), style-aware, fit-to-width text, no Launch80 defaults (terminal prompt, HUD brand, split LOCAL/CLOUD badges were hard-coded before). Counters always land exactly.
- **New blueprint scenes**: statement, code, ui, steps, milestones, logo, ranking, route.
- **Illustration toolkit** (`engine/illustrate.js`): world camera + parallax layers, keyframes, two-bone IK, motion cycles, flat-vector shape kit, bicycle prop, sky/clouds/hills/street/storefront rows/trees/lamps, anchored pop-out cards.
- **Transitions**: cut, glitch, flash, dissolve, push, whip, wipe, zoom, iris, shutter, slide — composited from two full frames; outgoing scenes don't self-exit when the transition does the work.
- **Audio**: 6 score presets (pulse, ambient, minimal, glitch, lofi, cinematic), per-transition SFX (riser/impact, whoosh, swell, click), seeded noise (byte-identical re-renders), optional licensed track.
- **Render**: parallel workers, lossless FFV1 chunks concatenated, frame count verified; JS errors surface as one clear line.
- **Build**: one lossy encode, BT.709 tags, closed-loop loudness (-14 LUFS measured on the output, not guessed).
- **QC** reads the compiled timeline + audit + novelty; tech specs measured, human checks pre-filled with timecodes.
- **Novelty** check: per-scene layout + edge fingerprints vs a library of past reels / blueprints; flags re-skins (the pi reel scores 56% re-skinned vs the Launch80 reel).
- **Tests** (`tests/`, pytest) drive the CLI exactly as an agent would: compile contracts, claims, seed variation, audio determinism + sync, per-style rendering, audit catches (overlap / off-canvas / blank / JS error), vertical layouts, end-to-end run.

## Stage B — transitions, illustration, scenes, sound
- **Transitions** composited from two full frames (bg + camera + scene): dissolve, push, whip, wipe, zoom, iris (with a focal point), shutter, slide; plus cut/glitch/flash. Each gets its own sound (whoosh, swell, riser+impact, click).
- **Illustration toolkit** in use: `examples/penguin` — a penguin rides a bicycle down Main Street (IK legs follow the pedals, scarf in the wind, blinking, head turns to each ad), four storefronts with window displays, parallax sky/hills/rooftops/street/bollards, a tracking camera, and a pop-out ad springing from each store's sign as he passes. World clock (`T_ABS`) keeps cuts continuous.
- **WebGL shader background** (`bg: "shader"`, custom GLSL via `bgOpts.frag`), falls back to 2D.
- **Worked examples for the director** (`prompts/examples/`): data as a filling GPU, kinetic type as crane-stacked crates, a courier journey — rotated by seed.
- **Accuracy**: on-screen numbers hard-coded in scene JS are flagged; claims marked placeholder are refused in `--final`; closed-loop loudness now handles true peak (compress → loudnorm → measure the MP4 → adjust).

## Stage C — director, gates, docs
- **Director** (`reel.py direct`): treat (K treatments; seed assigns each a different style pack + structure; gate rejects shared packs/metaphors), style frames sheet, pick, timeline (compile-gated with stubs), scenes (one file per scene: syntax → compile → audit → novelty, repair rounds carry the report; review strip per scene).
- **One model interface, four backends**: agent (prompt/answer files, exit 10, resumable), ollama, openai-compatible, mock (replays any recorded `.reel/llm/`). Prompts and gates identical; every exchange recorded.
- **Recorded agent session** `tests/fixtures/pi_small_core` + `examples/pi-small-core` (full transcript): the pi reel redone as a Swiss "small core" story — novelty 0% re-skinned vs the old pi reel's 64%.
- **brand** step: palette/fonts/copy from a site or saved HTML → brand.json + suggested override.
- **Novelty library** built from blueprints in 4 styles + the Launch80 and old pi reels (`tools/build_library.py`); `run --final --register` adds new reels.
- Docs rewritten around the one flow: SKILL.md, README, references (interview, api, scenes, styles, claims, director, critique, qc). Legacy `templates/` removed.
