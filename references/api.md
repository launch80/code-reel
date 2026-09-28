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
