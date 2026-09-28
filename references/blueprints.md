# Blueprints — writing new scene types (mode 2)

Mode 2 is an interactive session: you + a local LLM iterate on **new scene
types** that the shipped eight archetypes can't express, rendered against the
real timeline. The LLM never touches `reel.html` and never produces pixels —
it produces one file:

```
<project>/scene_custom.js      ← defineScene('name', (lt, d, p) => {...})
```

`reel.html` loads it via a `<script>` tag before building the timeline (a missing
file is fine — no custom scenes; `fetch()` deliberately does not work here, and
`file://` fetches are CORS-blocked anyway) and it runs **in reel.html's script
scope**, so every helper below is in scope. Reference `templates/reel.html` —
the eight `REG.*` functions are the blueprints; copy their patterns.

## Contract

```js
defineScene('orbit', (lt, d, p) => {
  // lt = seconds since the scene started (0 … d)
  // d  = scene duration in seconds
  // p  = the scene's params object from timeline.json
  // draw at CSS-pixel coordinates — the canvas transform already applies DPR
});
```

1. **Only draw inside `[0, d)`.** Entrance/exit math must be relative to `d`
   (e.g. `prog(lt, 0, 0.3)`), never to absolute reel time.
2. **Never mutate** `SC`, `CUTS`, `IMPACTS`, `DUR`, `C`, `ACC`, `FPS`.
3. **Impacts:** if a key element lands at a moment that should hit the audio,
   put that offset in the scene's `"slams": [1.8]` in timeline.json —
   `events.py` reads it and the soundtrack gets the hit. (Offsets on the beat
   grid land on beats.)
4. **Text safety:** keep everything inside 90% title-safe (96px LR / 54px TB
   at 1080p), and measure the FINAL string with `tw()` before positioning
   labels next to counters whose digits change width.
5. **Glow:** `ctx.shadowBlur = 24 * DPR` — the transform doesn't scale it.
6. **Names:** lowercase, `defineScene` refuses to override built-ins.
7. **Colors:** `C.cream`/`C.text`/`C.dim`, `ACC`/`HOTC`, `A(alpha)`/`Hh(alpha)`
   for accent with alpha — so the reel recolors with `theme`.

## The helper library (in scope inside scene_custom.js)

| Helper | Purpose |
|---|---|
| `W, H, DPR, FPS` | canvas size (CSS px), device-pixel ratio, frame rate |
| `C` | theme colors: `C.or, C.hot, C.cream, C.text, C.mute, C.bg, C.surf, C.line` |
| `A(a) / Hh(a)` | accent / hot color with alpha `a` (follows `theme`) |
| `prog(t,a,b)` | eased 0→1 ramp of `t` across `[a,b]` (clamped) |
| `eOutExpo, eOutCubic, eInOut, eOutBack, eIn` | easings — pass a 0-1 value |
| `clamp(x,a,b)`, `lerp(a,b,t)` | math |
| `txt(s,x,y,{f,col,a,align,ls,glow,gcol,base})` | draw text; `f` is a font string, `align:'center'|'right'`, `glow` is px |
| `tw(s,f,ls)` | measure text width — use for every fit check |
| `typed(s,t,a,b)` | typing reveal of `s` over `[a,b]` |
| `cursor(x,y,t,h,w,col)` | blinking terminal cursor |
| `rrect(x,y,w,h,r)` | rounded-rect path (then `fill()`/`stroke()`) |
| `rect(x,y,w,h,col,a)` | filled rect |
| `wipeLine(s,x,y,wd,p,{f,col,a,ls})` | reveal text left→right with `p` 0-1 |
| `dashed(x1,y1,x2,y2,p,a)` | animated dashed line, `p` 0-1 draws it in |
| `rng(seed)` | deterministic PRNG — never use `Math.random()` |
| `fmt(n)` / `bigFmt(v,fmt)` | `1,234` / `{from,to,fmt}` counter formatting (`int`,`x`,`k`,`d`) |
| `bigFmt` + `p.big` | counters: `const v=lerp(bf.from,bf.to,eOutExpo(prog(lt,0.1,1.4)))` |

## Recommended workflow (agent + local LLM)

### The uniqueness recipe

Past reels looked alike because agents picked compositions from the eight
archetypes instead of drawing the video's own subject. When writing a bespoke
scene, mine the **brief** for the picture:

1. **List the brief's concrete nouns** (ports, cranes, containers, ships —
   not "logistics"; satellites, debris, radar — not "space").
2. **Pick the relationship to draw**: orbiting, stacking, routing, queueing,
   filling, splitting, counting down, crossing a threshold. That relationship
   is the animation.
3. **One hero moment per scene**: one big shape + 2–4 annotated details beats
   a dense dashboard. The post layer (grain, flash, vignette) adds the rest.
4. **Never re-implement an archetype** with different colors — if the result
   is "three cards with numbers", it is `cards`, delete it and go deeper into
   the brief.

## Director auto-generation (mode 1, `--bespoke N`)

`director.py --mode invent` runs the blueprint path by default: the LLM first
writes `scene_custom.js` with `N` new scene types (default 2), then composes a
timeline that must use all of them. Every gate the manual path has, the
automatic path has too:

1. **Syntax gate** — `node --check scene_custom.js`; failures are sent back to
   the model for one self-repair round.
2. **Validation gate** — the timeline is validated with `--allow-custom`, so a
   bespoke scene type must be *declared* in the JS and *used* by the timeline;
   JSON repair rounds as usual.
3. **Render probe** — each bespoke scene is rendered (DPR=1, `render.py stills`)
   at 35% and 75% of its duration; the safe-area crop must contain ≥120 lit
   pixels (luma > 80) per sample pair. A real scene draws ~6,000+ lit pixels;
   a blank/crashed scene draws 0. On failure the JS is sent back to the model
   with the probe report and re-probed; second failure ⇒ `director.py` exits 2
   and keeps the candidates for a human.
4. **Frozen metadata** — `timeline_meta.json` records the bespoke scene names,
   the JS sha256, and the probe report, so every video is auditable.

The probe is also available for the manual path: `director.py --mode from-file
timeline.json --allow-custom` probes any custom scene next to the timeline.
(`--bespoke 0` / `--no-probe` skip the respective stages — drafts only.)

## Manual workflow (agent + local LLM)

1. Scaffold the project (SKILL.md §2), copy `templates/blank.json` →
   `timeline.json`, and keep the shipped 8 scenes for v1.
2. When the user wants something the archetypes can't do, write
   `scene_custom.js` with ONE `defineScene`, referencing an existing `REG.*`
   function in `templates/reel.html` as the closest blueprint
   (`cards` for stat grids, `chart` for data-driven drawing, `split` for
   two-column layouts).
3. Reference it in `timeline.json` as `{"scene":"orbit","dur":2.5,"p":{...}}`.
4. **Validate:** `python3 validate.py timeline.json --allow-custom`
   (custom types are accepted only when `scene_custom.js` declares them).
5. **Still-check before trusting:** `python3 render.py stills` at 25/50/75/
   100% of the new scene's absolute time window (scene start + 0.25·d, …).
   Look for: overlap, clipping outside the scene, text > safe area, glow
   seams, `Math.random` usage (non-deterministic between runs — grep it).
6. Only then `python3 render.py video && ./build.sh`, then `python3 qc.py`.

## Worked example — `orbit` scene

```js
// scene_custom.js — 3 satellites orbiting a brand mark
defineScene('orbit', (lt, d, p) => {
  const cx = W / 2, cy = H / 2, r = 260;
  const grow = eOutExpo(prog(lt, 0, 1.0));
  ctx.save();
  ctx.strokeStyle = A(0.25 * grow); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(cx, cy, r * grow, 0, 7); ctx.stroke();
  const rnd = rng(p.seed || 7);
  (p.items || []).forEach((it, i) => {
    const a = -Math.PI / 2 + i * 2 * Math.PI / p.items.length + lt * 0.9 + rnd() * 0.1;
    const x = cx + Math.cos(a) * r * grow, y = cy + Math.sin(a) * r * grow * 0.55;
    ctx.shadowBlur = 24 * DPR; ctx.shadowColor = A(0.9);
    ctx.fillStyle = i % 2 ? ACC : C.cream;
    ctx.beginPath(); ctx.arc(x, y, 10, 0, 7); ctx.fill();
    txt(it.toUpperCase(), x + 16, y + 6, { f: `500 20px ${MONO}`, col: C.text, ls: '2px' });
  });
  ctx.restore();
  txt((p.title || '').toUpperCase(), cx, cy + 8, { f: `800 44px ${SANS}`, col: C.cream, align: 'center', ls: '4px' });
});
```

```json
{"scene": "orbit", "dur": 2.5, "name": "ORBIT", "slams": [1.0],
 "p": {"title": "launch80", "items": ["agents", "reels", "stats"], "seed": 7}}
```

## Limits (be honest with the user)

- New scenes inherit the **post layer** (glitch/flash/grain/vignette) — you
  don't add it, it's applied around cuts automatically.
- `audio.py` knows nothing about the *inside* of your scene — only the
  `slams` list and the timeline timing produce sound.
- If a scene needs a new *sound*, that's a pipeline change, not a scene
  change — stop and ask the user.
- Keep the whole thing under ~15 scenes and ~30s; per-frame draw cost is
  Python→PNG→ffmpeg at 60fps, so don't draw 10,000 particles.
