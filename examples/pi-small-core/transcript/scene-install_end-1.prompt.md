<!-- system -->
You are the director of a motion-graphics studio whose every frame is drawn in code
(HTML canvas, deterministic, rendered to 1080p60 video). You design videos that belong
to ONE brief and could not be mistaken for any other video. You never invent facts:
every number that appears on screen comes from the brief's claims (or is marked as
fictional ad copy by the brief). You answer in exactly the format requested — no prose
around it.


<!-- user -->
# Task: write the scene file scenes/install_end.js

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
 "name": "install_end",
 "beats": 4,
 "kind": "custom",
 "idea": "One tile becomes a blinking cursor; the npm command types out; pi.dev and the version.",
 "on_screen": [
  "npm i -g @earendil-works/pi-coding-agent",
  "pi.dev",
  "v0.87.1"
 ],
 "claims": [
  "version"
 ]
}
It runs 2.0 s (4 beats at 120.0 bpm) between: adapt_line → [this] → end.
Its params (p) from timeline.json:
```json
{
 "cmd": "npm i -g @earendil-works/pi-coding-agent",
 "url": "pi.dev",
 "version": "v{{version}}",
 "tag": "a minimal, extensible AI agent for the terminal"
}
```

## Already written for this video (shared helpers / other scenes — reuse, don't duplicate)
- scenes/adapt_line.js: adapt_line
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
/* @meta {"name": "courier_run", "required": ["stops"], "text": ["stops"]} */
// A character journey: a round bird courier scoots past houses; a speech bubble greets each stop.
function courier_run_bird(x, y, t, s) {
  const bob = cyc.bob(t, 0.25, 5 * s);
  capsule(x - 60 * s, y, x + 70 * s, y, 10 * s, { fill: '#3a3a3a' });                    // deck
  circle(x - 50 * s, y + 14 * s, 16 * s, { fill: '#222' }); circle(x + 60 * s, y + 14 * s, 16 * s, { fill: '#222' });
  capsule(x + 62 * s, y, x + 70 * s, y - 110 * s, 8 * s, { fill: '#3a3a3a' }); capsule(x + 50 * s, y - 110 * s, x + 90 * s, y - 110 * s, 8 * s, { fill: '#3a3a3a' });
  blob(x, y - 70 * s + bob, 48 * s, 52 * s, { fill: C.accent });                         // body
  blob(x + 12 * s, y - 60 * s + bob, 26 * s, 30 * s, { fill: '#fff4e0', stroke: null });  // belly
  eye(x + 22 * s, y - 92 * s + bob, 9 * s, { look: [1, 0], blink: cyc.blink(t, 2.3, 2) });
  shape([[x + 42 * s, y - 86 * s + bob], [x + 64 * s, y - 80 * s + bob], [x + 42 * s, y - 74 * s + bob]], { fill: '#f4a03a', smooth: false });
  box(x - 72 * s, y - 100 * s + bob, 44 * s, 40 * s, { fill: '#c49a6c', stroke: '#7a5a3a', sw: 2, r: 4 });   // parcel
  const w = ik2(x + 10 * s, y - 60 * s + bob, x + 58 * s, y - 108 * s, 30 * s, 30 * s, -1);
  capsule(x + 10 * s, y - 60 * s + bob, w.jx, w.jy, 10 * s, { fill: C.accent }); capsule(w.jx, w.jy, w.ex, w.ey, 9 * s, { fill: C.accent });
}
defineScene('courier_run', (lt, d, p) => {
  const stops = p.stops || []; const speed = 420, c = cam(lt * speed + 300, 0, 1, { cy: H * 0.68 });
  sky(mix(C.bg, '#9fd6f2', 0.6), C.bg);
  hills(c, 0.35, 4, { y: -20, amp: 140, fill: mix(C.bg, '#6aa37a', 0.5) });
  street(c, { y: 0, sidewalk: 40, road: 300, walk: mix(C.bg, '#d8d2c8', 0.6), asphalt: mix(C.bg, '#444a55', 0.7) });
  const houses = stops.map((st, i) => ({ x: 700 + i * 900, name: st.name, hi: st.hello }));
  layer(c, 1, () => houses.forEach((h, i) => { const col = ['#f2c6a0', '#b8d8c8', '#c9c2e8', '#f6d88a'][i % 4];
    rect(h.x, -300, 380, 300, col); shape([[h.x - 30, -300], [h.x + 190, -440], [h.x + 410, -300]], { fill: '#b5543c', smooth: false });
    box(h.x + 150, -150, 80, 150, { fill: '#6b4a3a', stroke: null, r: 4 });
    box(h.x + 40, -240, 90, 80, { fill: '#cde8f0', stroke: '#5a4a40', sw: 3, r: 4 }); box(h.x + 250, -240, 90, 80, { fill: '#cde8f0', stroke: '#5a4a40', sw: 3, r: 4 });
    txt(h.name, h.x + 190, -320, { f: F('sans', 34, { w: 'bold' }), col: '#3a2a20', align: 'center' }); }));
  const bx = lt * speed + 300 - 150;
  layer(c, 1, () => courier_run_bird(bx, 150, lt, 1.1));
  houses.forEach(h => { const k = clamp((passing(c, 1, h.x + 190, { focus: W * 0.42, range: W * 0.3 }) - 0.2) / 0.3);
    const [ax, ay] = toScreen(c, 1, h.x + 190, -150); bubble(ax, ay, h.hi, k, { side: 'up', accent: C.accent }); });
});

```

## Requirements
- One file: a `/* @meta {...} */` block, then `defineScene('install_end', (lt, d, p) => { ... })`. Helper functions allowed above it (prefix them with `install_end_`).
- Draw the treatment's metaphor for THIS scene — a picture, not a slide. One hero element, 2–4 supporting details, motion for the full duration.
- Every visible string comes from p. Text never overlaps text; everything readable stays inside SAFE.
- Deterministic. No Math.random, no Date.
Return ONLY the JavaScript file.

