<!-- system -->
You are the director of a motion-graphics studio whose every frame is drawn in code
(HTML canvas, deterministic, rendered to 1080p60 video). You design videos that belong
to ONE brief and could not be mistaken for any other video. You never invent facts:
every number that appears on screen comes from the brief's claims (or is marked as
fictional ad copy by the brief). You answer in exactly the format requested — no prose
around it.


<!-- user -->
# Task: write the scene file scenes/tile_tally.js

## Brief (short)
# Brief — pi, the minimal extensible terminal agent

**What is this video for?** Market `pi` (@earendil-works/pi-coding-agent) to developers who live in a
terminal. After watching they should go to pi.dev and install it. The one idea: pi is small at the core
and everything else is a plugin — "Adapt Pi to your workflow, not the other way around."

**Format:** 16:9 · 15 s

**Claims on screen** (measured from the installed package v0.87.1 on 2026-09-28):

| id | value | source |
|---|---|---|
| version | 0.87.1 | package.json version |
| ext_examples | 68 | `ls examples/extensions/*.ts \| wc -l` |
| example_files | 102 | `find examples -name '*.ts' \| wc -l` |
| docs_pages | 37 | `ls docs/*.md \| wc -l` |
| keybindings | 90 | key rows in docs/keybindings.md |
| modes | 5 | docs/how-pi-works.md — interactive, print, JSON, RPC, SDK |
| releases | 278 | CHANGELOG.md '## [x.y.z]' headers, Nov 2025 → Sep 2026 |
| node_min | 22.19 | package.json engines.node >= 22.19.0 |

(Provider and slash-command counts are excluded: the earlier brief and timeline disagreed — 24 vs 32
providers, 17 vs 25 commands — so they stay off screen until re-measured.)

Copy from README.md: "A minimal, extensible AI agent for the terminal", "Adapt Pi to your workflow,
not the other way around.", extensibility list: prompt templates, skills, extensions, themes, packages,
TypeScript SDK. Install: `npm i -g @earendil-works/pi-coding-agent`.

**Look:** pi.dev palette — bg #0d1116, panel #161d27, text #ebe7e4, muted #9fa4ab, accent thread blue
#6a9fcc, terracotta #8f3222; logo accents #F1BE58 #F09082 #4D9ABF. Monospace-forward.

**Must avoid:** looking like the Launch80 showreel (terminal box → FASTER/LEANER → stat cards → big counter → chart → endcard).


## Treatment
Title: Small Core — metaphor: a heavy monolith slab that cracks into modular tiles orbiting a tiny core — motif: square tiles on a strict grid — the same tile becomes plugin, counter cell and cursor — style: swiss

## This scene
{
 "name": "tile_tally",
 "beats": 8,
 "kind": "custom",
 "idea": "Tiles rain into a 68-cell grid (one per extension example) while two side tallies count docs pages and keybindings.",
 "on_screen": [
  "68 extension examples",
  "37 docs pages",
  "90 keybindings"
 ],
 "claims": [
  "ext_examples",
  "docs_pages",
  "keybindings"
 ]
}
It runs 4.0 s (8 beats at 120.0 bpm) between: core_split → [this] → adapt_line.
Its params (p) from timeline.json:
```json
{
 "cells": "@ext_examples",
 "cells_label": "{{ext_examples}} extension examples",
 "side": [
  {
   "value": "@docs_pages",
   "label": "docs pages"
  },
  {
   "value": "@keybindings",
   "label": "keybindings"
  }
 ],
 "source": "measured from @earendil-works/pi-coding-agent {{version}}"
}
```

## Already written for this video (shared helpers / other scenes — reuse, don't duplicate)
- scenes/core_split.js: core_split, core_split_orbit
- scenes/monolith.js: monolith, monolith_geom

## Scene API
# Scene API — everything a scene file can use

A project scene lives in `scenes/<name>.js`. Shared helpers for several scenes
(a world, a character, a palette) go in `scenes/_<anything>.js` — loaded first.

```js
/* @meta {"name": "orbit", "required": ["items"], "text": ["title", "items"], "slams": ["hit"]} */
defineScene('orbit', (lt, d, p) => {
  // lt = seconds since this scene started (0..d), d = duration, p = params from timeline.json
});
```

`@meta` (JSON, optional but recommended): `required` params (compile checks them),
`text` = which params are on-screen text (claims check reads them), `slams` = param
keys holding seconds-into-scene where an audio hit should land, `typing` =
`[{"key": "line", "a": "0.1d", "b": "0.5d"}]` for typing clicks.

## Rules (the audit enforces most of them)
- Deterministic: never `Math.random`/`Date.now`; use `rng(seed)`, `noise2`, `hash1`, `lt`, `T_ABS`.
- All on-screen strings with numbers come from params (compile rejects hard-coded ones in `--final`).
- Draw in CSS px on a `W x H` canvas; `U = min(W,H)/1080` scales sizes; keep text inside `SAFE` (l,r,t,b margins).
- Measure before placing: `fitPx`, `wrap`, `tw`. Never let text overlap other text (the audit fails it).
- Clip with `clipRect` / `withClip(shape, draw, bounds)` so the audit knows text is intentionally cut.
- Motion relative to `d`: entrance `M.in(prog(lt, 0, 0.3*d))`, exits via `exitP(lt, d)` (0 when the transition does the exit).
- Colors from the style: `C.bg C.surf C.line C.text C.mute C.accent C.hot C.cream` (cream = strongest text), `A(a)`/`Hh(a)` accent/hot with alpha, `rgba(hex,a)`, `mix(h1,h2,t)`, `isLight()`.
- Fonts from the style: `F(role, px, {w:'bold', i:true})`, roles `sans mono serif disp`. `cap(s)` uppercases if the style wants caps. `GLOW` scales glows (0 on print looks).

## Time + easing
`prog(t,a,b)` 0→1 ramp · `M.in/M.out/M.move` style easings · `eOutExpo eOutCubic eOutQuart eInOut eInOutSine eOutBack eIn smooth spring(x)` ·
`stagger(i,n,t,a,b,each)` · `kf(t, [[t0,v0],[t1,v1],...], ease)` keyframes (numbers or arrays) · `clamp lerp` ·
`T_ABS` absolute reel time, `SCENE_T0` this scene's start (continuity across cuts) · `cyc.phase/osc/bob/blink/crank`.

## Text
`txt(s, x, y, {f, col, a, align, ls, glow, gcol, base, stroke, sw})` · `tw(s, f, ls)` width ·
`fitPx(s, role, maxW, maxPx, minPx, {w,i}, ls)` → px · `wrap(s, f, maxW)` → lines · `para(s, x, y, maxW, {f, lh, align, col})` ·
`wipeLine(s, x, y, width, p, o)` · `typed(s, t, a, b)` · `chars(s, x, y, o, (i,n,ch)=>({dx,dy,a,sc,rot,col}))` per-letter ·
`scramble(s, p, seed)` decode · `cursor(x, y, t, h, w, col)` · numbers: `fmt(n)`, `bigFmt(v, fmt)`, `countTo({from,to,fmt}, p)` (fmt: int comma x k d pct dec1 dec2).

## Shapes
`rect(x,y,w,h,col,a)` · `box(x,y,w,h,{r,fill,stroke,sw,a,shadow})` (opaque boxes occlude text below for the audit) · `rrect` path ·
`circle(x,y,r,{fill,stroke,sw,a})` · `line(x1,y1,x2,y2,{col,sw,a,dash,cap})` · `dashed(...)` · `poly(pts, p, {col,sw,fill,dash})` progressive polyline (returns head point) ·
`arrow(x1,y1,x2,y2,p,o)` · `arcP(x,y,r,p,o)` · `pathD(svgPathData, {x,y,s,p,col,sw,fill,fillP})` draw-on SVG paths ·
`drawImg(assetName, x,y,w,h,{fit,r,a})` (timeline `"assets": {"logo": "assets/logo.png"}`) · `proj(x,y,z,{f,cx,cy,rx,ry})` 3D → screen ·
`clipRect(x,y,w,h, fn)` · `withClip(shapeFn, drawFn, bounds)` · `noise2(x,y,seed)` · `rng(seed)` · `hash1(n)`.

## Illustration (worlds, characters, props, places)
World + camera: `cam(x, y, zoom, {cx, cy})` · `layer(c, depth, fn)` (depth 1 = action plane, <1 far, >1 foreground) ·
`toScreen(c, depth, x, y)` · `viewX(c, depth)` visible world range · `passing(c, depth, worldX, {focus, range})` 0..1 as an object passes a screen point.
Shape kit: `blob(x,y,rx,ry,{fill,stroke,sw,rot,a})` · `capsule(x1,y1,x2,y2,w,{fill,stroke})` · `shape(pts,{fill,smooth,k})` smooth closed path ·
`smoothPath(pts, closed)` · `shadow(x,y,rx,ry,a)` · `grad(x0,y0,x1,y1,[[0,c],[1,c]])` · `rgrad(...)` · `eye(x,y,r,{look:[dx,dy],blink})` ·
`INK`/`INKW` globals give every shape an outline (set, draw, reset to null/0).
Rigging: `ik2(sx,sy,tx,ty,l1,l2,bend)` → `{jx,jy,ex,ey}` two-bone IK (legs to pedals, arms to handles) · `limb(x,y,angles,lens)` FK · `limbDraw(pts,w,o)`.
Props/places: `bikeRig(x,y,{s,crank})` geometry · `bicycle(x,y,{s,crank,rot,frame,tire})` · `sky(top,bottom)` · `sun(x,y,r,col)` · `cloud(x,y,s)` ·
`clouds(c,depth,seed,{n,span,y,t,drift})` · `hills(c,depth,seed,{y,amp,fill})` · `street(c,{y,sidewalk,road,...})` ·
`storefront(x,y,{w,h,name,wall,trim,awning:[c1,c2],glass,display(x,y,w,h)})` → anchors · `storeRow(c, shops, {y,x0,gap,between})` · `tree(x,y,s)` · `lamp(x,y,h)`.
Graphics anchored to things: `popout(ax, ay, p, {title, body, badge, w, h, side, fill, col, accent})` spring-in callout card with a tail to (ax,ay) · `bubble(ax, ay, text, p)`.

## Blueprints (reference scenes you can also use directly)
terminal · kinetic · cards · counter · chart · quote · split · endcard · statement · code · ui · steps · milestones · logo · ranking · route
— params in `references/scenes.md`. Read `engine/scenes.js` / `engine/scenes_plus.js` to see how a scene is built; do not copy one and recolor it.


## Example of the house standard (a different video — learn the craft, don't copy the picture)
```js
/* @meta {"name": "crane_words", "required": ["words"], "text": ["words", "caption"], "slams": []} */
// Kinetic type with a physical metaphor: a crane lowers each word as a crate onto a stack.
defineScene('crane_words', (lt, d, p) => {
  const words = p.words || []; const n = words.length; const per = 0.7 * d / Math.max(1, n);
  const baseY = H - SAFE.b - 40 * U, colX = W * 0.56, crH = 118 * U;
  const craneX = SAFE.l + 80 * U, top = SAFE.t + 30 * U;
  // crane: mast + jib + counterweight
  rect(craneX - 14 * U, top, 28 * U, baseY - top, C.line); rect(craneX - 160 * U, top, W - craneX - SAFE.r + 160 * U, 16 * U, C.line);
  for (let x = craneX; x < W - SAFE.r; x += 60 * U) line(x, top, x + 30 * U, top + 16 * U, { col: C.bg, sw: 2 });
  rect(craneX - 160 * U, top + 16 * U, 90 * U, 70 * U, C.mute);
  line(SAFE.l, baseY, W - SAFE.r, baseY, { col: C.line, sw: 4 });
  let hookX = colX, hookY = top + 120 * U, stackTop = baseY;
  words.forEach((w, i) => {
    const t0 = 0.08 * d + i * per, k = prog(lt, t0, t0 + per * 0.85);
    const f = F('disp', fitPx(w, 'disp', W * 0.5, 84 * U, 30 * U)); const bw = tw(w, f) + 80 * U;
    const landY = stackTop - crH; const x = colX - bw / 2 + (i % 2 ? 26 : -26) * U;
    if (k <= 0) return;
    const drop = eOutBack(clamp(k * 1.15)); const y = lerp(top + 140 * U, landY, drop);
    if (k < 1) { hookX = x + bw / 2; hookY = y; }
    box(x, y, bw, crH - 10 * U, { fill: i === n - 1 ? A(1) : C.surf, stroke: C.cream, sw: 3, r: 6 * U });
    for (let s = 1; s < 4; s++) line(x + bw * s / 4, y + 10 * U, x + bw * s / 4, y + crH - 20 * U, { col: rgba(C.cream, 0.15), sw: 2 });
    txt(w, x + bw / 2, y + crH * 0.62, { f, col: i === n - 1 ? C.bg : C.cream, align: 'center' });
    stackTop = landY + (k >= 1 ? 0 : crH);
    if (k >= 1) stackTop = landY;
  });
  line(hookX, top + 16 * U, hookX, hookY, { col: C.cream, sw: 3 }); circle(hookX, hookY, 9 * U, { stroke: C.cream, sw: 3 });
  if (p.caption) txt(p.caption, W - SAFE.r, top + 90 * U, { f: F('serif', fitPx(p.caption, 'serif', W * 0.36, 48 * U, 22 * U, { i: true }), { i: true }), col: C.mute, align: 'right', a: M.in(prog(lt, 0.75 * d, 0.95 * d)) });
});

```

## Requirements
- One file: a `/* @meta {...} */` block, then `defineScene('tile_tally', (lt, d, p) => { ... })`. Helper functions allowed above it (prefix them with `tile_tally_`).
- Draw the treatment's metaphor for THIS scene — a picture, not a slide. One hero element, 2–4 supporting details, motion for the full duration.
- Every visible string comes from p. Text never overlaps text; everything readable stays inside SAFE.
- Deterministic. No Math.random, no Date.
Return ONLY the JavaScript file.

