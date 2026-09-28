<!-- system -->
You are the director of a motion-graphics studio whose every frame is drawn in code
(HTML canvas, deterministic, rendered to 1080p60 video). You design videos that belong
to ONE brief and could not be mistaken for any other video. You never invent facts:
every number that appears on screen comes from the brief's claims (or is marked as
fictional ad copy by the brief). You answer in exactly the format requested — no prose
around it.


<!-- user -->
# Task: write the scene file scenes/adapt_line.js

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
 "name": "adapt_line",
 "beats": 4,
 "kind": "custom",
 "idea": "The tiles rearrange into the shape of the viewer's own workflow as the README line lands.",
 "on_screen": [
  "Adapt Pi to your workflow, not the other way around."
 ],
 "claims": []
}
It runs 2.0 s (4 beats at 120.0 bpm) between: tile_tally → [this] → install_end.
Its params (p) from timeline.json:
```json
{
 "line": "Adapt Pi to your workflow, not the other way around.",
 "emphasis": [
  "your",
  "workflow"
 ]
}
```

## Already written for this video (shared helpers / other scenes — reuse, don't duplicate)
- scenes/core_split.js: core_split, core_split_orbit
- scenes/monolith.js: monolith, monolith_geom
- scenes/tile_tally.js: tile_tally

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
/* @meta {"name": "gpu_fill", "required": ["big", "unit"], "text": ["label", "big", "unit", "caption"], "ticks": [{"a": 0.4, "b": "0.7d"}]} */
// Data as a physical picture: throughput is liquid rising inside a graphics card.
function gpu_fill_card(x, y, w, h, level, lt) {
  box(x, y, w, h, { fill: C.surf, stroke: C.line, sw: 3, r: 18 * U, shadow: 30 });
  const fy = y + h * (1 - level);                                  // liquid surface
  withClip(() => rrect(x + 6, y + 6, w - 12, h - 12, 14 * U), () => {
    ctx.beginPath(); ctx.moveTo(x, y + h);
    for (let k = 0; k <= 60; k++) { const px = x + w * k / 60; ctx.lineTo(px, fy + Math.sin(k * 0.45 + lt * 5) * 7 * U * (1 - level * 0.5)); }
    ctx.lineTo(x + w, y + h); ctx.closePath(); ctx.fillStyle = grad(0, fy, 0, y + h, [[0, A(0.85)], [1, Hh(0.6)]]); ctx.fill();
    const r = rng(9); for (let b = 0; b < 26; b++) { const bx = x + r() * w, sp = 0.25 + r() * 0.5, by = y + h - ((lt * sp * h + r() * h) % (h * level + 1)); circle(bx, by, (2 + r() * 5) * U, { stroke: rgba('#ffffff', 0.5), sw: 1.5 }); }
  }, { x, y, w, h });
  [0.3, 0.7].forEach(f => { const cx = x + w * f, cy = y + h * 0.42, R = h * 0.26;
    circle(cx, cy, R, { stroke: rgba(C.text, 0.35), sw: 3 });
    for (let k = 0; k < 7; k++) { const a = lt * 6 + k * Math.PI * 2 / 7; line(cx, cy, cx + Math.cos(a) * R * 0.9, cy + Math.sin(a) * R * 0.9, { col: rgba(C.text, 0.25), sw: 5 * U, cap: 'round' }); } });
  for (let k = 0; k < 14; k++) rect(x + 40 * U + k * (w - 80 * U) / 14, y + h, (w - 80 * U) / 14 - 8 * U, 22 * U, '#c9a227');   // gold contacts
}
defineScene('gpu_fill', (lt, d, p) => {
  const e = M.in(prog(lt, 0, 0.5)), fill = eOutCubic(prog(lt, 0.4, 0.7 * d));
  const w = Math.min(1100 * U, W - SAFE.l - SAFE.r), h = w * 0.42, x = (W - w) / 2, y = H * 0.24 + (1 - e) * 80 * U;
  ctx.save(); ctx.globalAlpha = e; gpu_fill_card(x, y, w, h, 0.08 + 0.84 * fill, lt); ctx.restore();
  const v = countTo(p.big, fill), f = F('disp', fitPx(bigFmt(p.big.to, p.big.fmt), 'disp', w * 0.5, 200 * U, 60 * U));
  txt(v, W / 2, y + h * 0.62, { f, col: C.cream, align: 'center', a: e, stroke: rgba(C.bg, 0.6), sw: 8 });
  txt(p.unit, W / 2, y + h * 0.62 + 70 * U, { f: F('mono', 34 * U, { w: 'bold' }), col: C.cream, align: 'center', a: e });
  if (p.label) txt(cap(p.label), x, y - 30 * U, { f: F('mono', 24 * U, { w: 'bold' }), col: ACC, ls: '3px', a: e });
  if (p.caption) wipeLine(p.caption, W / 2, y + h + 110 * U, W - SAFE.l - SAFE.r, M.in(prog(lt, 0.6 * d, 0.85 * d)), { f: F('serif', fitPx(p.caption, 'serif', W - SAFE.l - SAFE.r, 56 * U, 24 * U, { i: true }), { i: true }), col: C.text, align: 'center' });
});

```

## Requirements
- One file: a `/* @meta {...} */` block, then `defineScene('adapt_line', (lt, d, p) => { ... })`. Helper functions allowed above it (prefix them with `adapt_line_`).
- Draw the treatment's metaphor for THIS scene — a picture, not a slide. One hero element, 2–4 supporting details, motion for the full duration.
- Every visible string comes from p. Text never overlaps text; everything readable stays inside SAFE.
- Deterministic. No Math.random, no Date.
Return ONLY the JavaScript file.

