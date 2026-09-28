# Styles — the look is a choice, not a constant

`timeline.json` `"style"`: a pack name, or `{"pack": "<name>", ...overrides}`.

| pack | bg | hud | post | camera | transitions (pool) | motion | score | bpm |
|---|---|---|---|---|---|---|---|---|
| signal | grid | camera | film | push | glitch, flash, whip | outExpo | pulse | 120 |
| editorial | paper | editorial | paper | drift | dissolve, wipe, iris | outQuart | ambient | 90 |
| swiss | swiss | minimal | clean | static | push, slide, shutter, cut | outCubic | minimal | 120 |
| blueprint | blueprint | blueprint | clean | drift | wipe, iris, shutter | outCubic | cinematic | 100 |
| soft | mesh | none | clean | dolly | zoom, dissolve, push | spring | lofi | 90 |
| terminal | crt | terminal | crt | handheld | glitch, cut, flash | outCubic | glitch | 144 |
| storybook | gradient | none | clean | static | iris, dissolve, push | spring | lofi | 100 |

Override keys: `palette` {bg surf line text mute accent hot cream}, `fonts`
{sans mono serif disp} (bundled: DM Sans, DM Mono, Instrument Serif, Russo One,
Inter, Fraunces, IBM Plex Sans/Mono/Sans Condensed, Archivo, Archivo Black,
JetBrains Mono, Manrope, VT323, Space Grotesk, Chakra Petch), `weights`,
`bg` + `bgOpts`, `hud` (or top-level `"hud": false`), `post` + `postOpts`,
`camera`, `transitions` (pool), `transitionDur`, `motion` {in, out, move},
`glow`, `flash`, `radius`, `caps`, `audio`, `bpm`, `fadeTo`, `safe`.

Registries (engine/looks.js):
- **bg**: solid, grid, paper, swiss, blueprint, mesh, crt, dots, gradient, shader (WebGL; `bgOpts.frag` = your GLSL `vec3 shade(vec2 uv, float t)`), none
- **hud**: none, camera, minimal, editorial, blueprint, terminal
- **post**: clean, film, paper, crt, print
- **camera**: static, push, drift, handheld, dolly, punch
- **transitions**: cut, glitch, flash (self-exit) · dissolve, push, whip, wipe, zoom, iris, shutter, slide (overlap, composited from two full frames). Per scene: `"transition": {"type": "iris", "dur": 0.8, "x": 0.4, "y": 0.6}`; `dir` for push/whip/wipe/slide.
- **motion easings**: linear smooth outExpo outCubic outQuart inOut inOutSine outBack in step spring

Per-scene look: `"look": {"bg": "paper", "camera": "static", "bgOpts": {...}}`.
Audio: `"audio": {"preset": "cinematic", "key": "D"}` or `{"track": "assets/music.mp3", "gain_db": -3, "sfx": true}`.
