// code-reel engine · illustrate.js — the ILLUSTRATION toolkit.
// For briefs that need a picture, not a chart: characters, vehicles, places,
// camera moves through a world, and graphics anchored to things in it.
//   world + camera   cam(), layer(cam, depth, fn), toScreen(), kf() keyframes
//   rigging          ik2() two-bone IK, limb(), cycles (pedal/walk/bob/blink)
//   shape kit        blob, capsule, shape (smooth closed path), shadow, grad, eye
//   props            bicycle()
//   environments     sky, sun, clouds, hills, street, storefront, street row, tree, lamp
//   graphics         popout() anchored callout cards, bubble(), passing()
// Output is flat 2D vector illustration (explainer / motion-graphics cartoon),
// deterministic like everything else: seeds, never Math.random.
'use strict';

let IN_WORLD = false;             // txt() inside a world layer: audit skips off-canvas checks
const _auditBoxOrig = auditBox;
auditBox = function (s, x, y, w, asc, desc, align) {   // tag world text for the audit
  const n = AUDIT_LOG.length; _auditBoxOrig(s, x, y, w, asc, desc, align);
  if (AUDIT_LOG.length > n && IN_WORLD) AUDIT_LOG[AUDIT_LOG.length - 1].world = true;
};

// ------------------------------------------------------------------ keyframes
// kf(t, [[t0, v0], [t1, v1], ...], ease) — numbers or arrays; holds before/after
function kf(t, keys, ease = eInOutSine) {
  if (!keys.length) return 0; if (t <= keys[0][0]) return keys[0][1];
  for (let i = 1; i < keys.length; i++) {
    if (t <= keys[i][0]) {
      const [t0, a] = keys[i - 1], [t1, b] = keys[i]; const u = ease(prog(t, t0, t1));
      return Array.isArray(a) ? a.map((v, k) => lerp(v, b[k], u)) : lerp(a, b, u);
    }
  }
  return keys[keys.length - 1][1];
}

// ------------------------------------------------------------------ world + camera
// A camera looks at world point (x, y) with zoom z. Layers have a depth:
// 1 = the action plane, <1 = further away (moves slower), >1 = foreground.
function cam(x, y, z = 1, o = {}) { return { x, y, z, cx: o.cx ?? W / 2, cy: o.cy ?? H * 0.62 }; }
function layer(c, depth, fn) {
  ctx.save(); ctx.translate(c.cx, c.cy); const s = lerp(1, c.z, depth); ctx.scale(s, s);
  ctx.translate(-c.x * depth, -c.y * depth); const was = IN_WORLD; IN_WORLD = true;
  try { fn(); } finally { IN_WORLD = was; ctx.restore(); }
}
function toScreen(c, depth, x, y) { const s = lerp(1, c.z, depth); return [c.cx + (x - c.x * depth) * s, c.cy + (y - c.y * depth) * s]; }
// visible world x-range for a layer (for culling procedural rows)
function viewX(c, depth) { const s = lerp(1, c.z, depth); return [c.x * depth - c.cx / s, c.x * depth + (W - c.cx) / s]; }

// ------------------------------------------------------------------ shape kit
let INK = null, INKW = 0;         // optional outline for every shape (set per scene: INK = '#1f2a44'; INKW = 4)
function _paint(fill, stroke, sw, a = 1) {
  ctx.globalAlpha *= a;
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  const st = stroke === undefined ? INK : stroke; const w = sw ?? INKW;
  if (st && w) { ctx.strokeStyle = st; ctx.lineWidth = w; ctx.lineJoin = 'round'; ctx.lineCap = 'round'; ctx.stroke(); }
}
function blob(x, y, rx, ry, o = {}) { ctx.save(); ctx.beginPath(); ctx.ellipse(x, y, Math.max(0.1, rx), Math.max(0.1, ry), o.rot || 0, 0, Math.PI * 2); _paint(o.fill, o.stroke, o.sw, o.a); ctx.restore(); }
function capsule(x1, y1, x2, y2, w, o = {}) {
  ctx.save(); ctx.globalAlpha *= (o.a ?? 1);
  const st = o.stroke === undefined ? INK : o.stroke; const sw = o.sw ?? INKW;
  if (st && sw) { ctx.strokeStyle = st; ctx.lineWidth = w + sw * 2; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); }
  ctx.strokeStyle = o.fill || C.text; ctx.lineWidth = w; ctx.lineCap = 'round'; ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore();
}
// smooth closed (or open) path through points — Catmull-Rom -> Bezier
function smoothPath(pts, closed = true, k = 0.5) {
  const n = pts.length; if (n < 2) return; ctx.moveTo(pts[0][0], pts[0][1]);
  const P = i => pts[closed ? (i + n) % n : clamp(i, 0, n - 1)];
  for (let i = 0; i < (closed ? n : n - 1); i++) {
    const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
    ctx.bezierCurveTo(p1[0] + (p2[0] - p0[0]) * k / 3, p1[1] + (p2[1] - p0[1]) * k / 3, p2[0] - (p3[0] - p1[0]) * k / 3, p2[1] - (p3[1] - p1[1]) * k / 3, p2[0], p2[1]);
  }
  if (closed) ctx.closePath();
}
function shape(pts, o = {}) { ctx.save(); ctx.beginPath(); if (o.smooth === false) { pts.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); ctx.closePath(); } else smoothPath(pts, true, o.k ?? 0.5); _paint(o.fill, o.stroke, o.sw, o.a); ctx.restore(); }
function shadow(x, y, rx, ry, a = 0.18) { blob(x, y, rx, ry, { fill: `rgba(0,0,0,${a})`, stroke: null }); }
function grad(x0, y0, x1, y1, stops) { const g = ctx.createLinearGradient(x0, y0, x1, y1); stops.forEach(([o, c]) => g.addColorStop(o, c)); return g; }
function rgrad(x, y, r0, r1, stops) { const g = ctx.createRadialGradient(x, y, r0, x, y, r1); stops.forEach(([o, c]) => g.addColorStop(o, c)); return g; }
// eye with pupil look direction and blink (0 open .. 1 closed)
function eye(x, y, r, o = {}) {
  const { look = [0, 0], blink = 0, white = '#ffffff', pupil = '#111111' } = o;
  ctx.save(); ctx.beginPath(); ctx.ellipse(x, y, r, r * (1 - 0.92 * blink), 0, 0, Math.PI * 2); ctx.fillStyle = white; ctx.fill();
  if (INK && INKW) { ctx.strokeStyle = INK; ctx.lineWidth = INKW * 0.7; ctx.stroke(); }
  ctx.clip(); blob(x + look[0] * r * 0.4, y + look[1] * r * 0.4, r * 0.52, r * 0.52, { fill: pupil, stroke: null });
  blob(x + look[0] * r * 0.4 - r * 0.18, y + look[1] * r * 0.4 - r * 0.2, r * 0.16, r * 0.16, { fill: '#ffffff', stroke: null }); ctx.restore();
}

// ------------------------------------------------------------------ rigging
// two-bone IK: root (sx,sy) reaching target (tx,ty) with bone lengths l1,l2.
// bend = +1 / -1 picks the elbow/knee side. Returns {jx,jy, ex,ey, reach}
function ik2(sx, sy, tx, ty, l1, l2, bend = 1) {
  let dx = tx - sx, dy = ty - sy; let d = Math.hypot(dx, dy); const reach = d <= l1 + l2;
  d = clamp(d, Math.abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3);
  const a = Math.atan2(dy, dx); const cosA = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d); const A1 = a - bend * Math.acos(clamp(cosA, -1, 1));
  const jx = sx + Math.cos(A1) * l1, jy = sy + Math.sin(A1) * l1;
  const ang2 = Math.atan2(sy + Math.sin(a) * d - jy, sx + Math.cos(a) * d - jx);
  return { jx, jy, ex: jx + Math.cos(ang2) * l2, ey: jy + Math.sin(ang2) * l2, reach };
}
// forward-kinematic chain: angles are relative; returns joint list [[x,y],...]
function limb(x, y, angles, lens) { const pts = [[x, y]]; let a = 0; for (let i = 0; i < lens.length; i++) { a += angles[i]; x += Math.cos(a) * lens[i]; y += Math.sin(a) * lens[i]; pts.push([x, y]); } return pts; }
function limbDraw(pts, w, o = {}) { for (let i = 1; i < pts.length; i++) capsule(pts[i - 1][0], pts[i - 1][1], pts[i][0], pts[i][1], w * (o.taper ? lerp(1, o.taper, i / pts.length) : 1), o); }
// cycles
const cyc = {
  phase: (t, period, off = 0) => ((t / period + off) % 1 + 1) % 1,                  // 0..1 sawtooth
  osc: (t, period, amp = 1, off = 0) => Math.sin((t / period + off) * Math.PI * 2) * amp,
  bob: (t, period, amp = 1) => -Math.abs(Math.sin(t / period * Math.PI)) * amp,      // footfall bounce
  blink: (t, every = 3.2, seed = 1) => { const k = Math.floor(t / every); const st = k * every + hash1(k + seed) * every * 0.6; const u = (t - st) / 0.16; return u > 0 && u < 1 ? Math.sin(u * Math.PI) : 0; },
  crank: (t, rpm = 60) => t * rpm / 60 * Math.PI * 2,
};

// ------------------------------------------------------------------ props
// bicycle at (x, y) = rear-wheel contact point on the ground; returns rig points.
// o: {s (scale), rot (wheel angle, rad), crank (crank angle), frame, tire, dir (+1 faces right)}
function bikeRig(x, y, o = {}) {   // geometry only (plan limbs before drawing); bicycle() draws it
  const s = o.s || 1, R = 52 * s, dir = o.dir || 1;
  const rear = [x, y - R], front = [x + dir * 170 * s, y - R], crank = [x + dir * 72 * s, y - R + 6 * s];
  const seat = [x + dir * 52 * s, y - R - 96 * s], bar = [x + dir * 150 * s, y - R - 104 * s], head = [x + dir * 138 * s, y - R - 70 * s];
  const ca = o.crank || 0, cr = 20 * s; const p1 = [crank[0] + Math.cos(ca) * cr, crank[1] + Math.sin(ca) * cr], p2 = [crank[0] - Math.cos(ca) * cr, crank[1] - Math.sin(ca) * cr];
  return { rear, front, crank, seat, bar, head, pedals: [p1, p2], R, s, dir };
}
function bicycle(x, y, o = {}) {
  const { rear, front, crank, seat, bar, head, pedals: [p1, p2], R, s, dir } = bikeRig(x, y, o);
  const frame = o.frame || C.accent, tire = o.tire || '#1d1d1f';
  const wheel = (cx, cy) => { ctx.save(); circle(cx, cy, R, { stroke: tire, sw: 9 * s }); circle(cx, cy, R - 7 * s, { stroke: rgba('#888888', 0.6), sw: 1.5 * s });
    for (let k = 0; k < 8; k++) { const a = (o.rot || 0) + k * Math.PI / 4; line(cx, cy, cx + Math.cos(a) * (R - 6 * s), cy + Math.sin(a) * (R - 6 * s), { col: rgba('#9aa0a6', 0.8), sw: 1.4 * s }); }
    circle(cx, cy, 5 * s, { fill: '#888' }); ctx.restore(); };
  const tube = (a, b, w = 7) => capsule(a[0], a[1], b[0], b[1], w * s, { fill: frame, stroke: o.ink ?? INK, sw: INKW ? INKW * 0.6 : 0 });
  wheel(...rear); wheel(...front);
  // back pedal (behind frame)
  capsule(crank[0], crank[1], p2[0], p2[1], 4 * s, { fill: '#444', stroke: null }); rect(p2[0] - 9 * s, p2[1] - 2 * s, 18 * s, 5 * s, '#333');
  tube(rear, crank); tube(rear, seat); tube(crank, seat); tube(seat, head); tube(crank, head); tube(head, front, 6); tube(head, bar, 5);
  capsule(bar[0] - dir * 8 * s, bar[1], bar[0] + dir * 14 * s, bar[1] + 4 * s, 7 * s, { fill: '#2b2b2b', stroke: null });
  capsule(seat[0] - dir * 16 * s, seat[1] - 4 * s, seat[0] + dir * 10 * s, seat[1] - 4 * s, 9 * s, { fill: '#2b2b2b', stroke: null });
  circle(crank[0], crank[1], 12 * s, { fill: '#555', stroke: o.ink ?? INK, sw: INKW * 0.5 });
  capsule(crank[0], crank[1], p1[0], p1[1], 4 * s, { fill: '#666', stroke: null }); rect(p1[0] - 9 * s, p1[1] - 2 * s, 18 * s, 5 * s, '#444');
  return { rear, front, crank, seat, bar, head, pedals: [p1, p2], R };
}

// ------------------------------------------------------------------ environments
function sky(top, bottom, o = {}) { ctx.save(); ctx.fillStyle = grad(0, 0, 0, o.h || H, [[0, top], [1, bottom]]); ctx.fillRect(0, 0, W, o.h || H); ctx.restore(); }
function sun(x, y, r, col = '#ffd166', glowA = 0.35) { ctx.save(); ctx.fillStyle = rgrad(x, y, r * 0.8, r * 3, [[0, rgba(col, glowA)], [1, rgba(col, 0)]]); ctx.fillRect(x - r * 3, y - r * 3, r * 6, r * 6); ctx.restore(); blob(x, y, r, r, { fill: col, stroke: null }); }
function cloud(x, y, s = 1, o = {}) {
  const col = o.fill || 'rgba(255,255,255,0.92)'; ctx.save(); ctx.globalAlpha *= (o.a ?? 1);
  [[0, 0, 60], [55, -22, 52], [110, 0, 58], [55, 14, 62]].forEach(([dx, dy, r]) => blob(x + dx * s, y + dy * s, r * s, r * s * 0.78, { fill: col, stroke: null })); ctx.restore();
}
// clouds drifting across a parallax layer; world x range handled by the layer's culling
function clouds(c, depth, seed, o = {}) {
  const r = rng(seed); const n = o.n || 8, span = o.span || 6000, y0 = o.y ?? -H * 0.45; const drift = (o.drift ?? 12) * (o.t || 0);
  layer(c, depth, () => { for (let i = 0; i < n; i++) { const x = r() * span - span * 0.2 + drift, y = y0 + r() * 160; cloud(x, y, 0.6 + r() * 0.8, { a: 0.85 }); } });
}
function hills(c, depth, seed, o = {}) {
  const [x0, x1] = viewX(c, depth); const base = o.y ?? 0, amp = o.amp ?? 120, step = 40;
  layer(c, depth, () => { ctx.beginPath(); ctx.moveTo(x0 - step, base + 2000);
    for (let x = Math.floor(x0 / step) * step - step; x <= x1 + step; x += step) ctx.lineTo(x, base - noise2(x * 0.0022, 0, seed) * amp - noise2(x * 0.009, 3, seed) * amp * 0.25);
    ctx.lineTo(x1 + step, base + 2000); ctx.closePath(); _paint(o.fill || mix(C.bg, '#2f6b4f', 0.6), null, 0); });
}
// road/sidewalk along y (world), full width of the view
function street(c, o = {}) {
  const depth = o.depth ?? 1, y = o.y ?? 0; const [x0, x1] = viewX(c, depth);
  layer(c, depth, () => {
    rect(x0 - 10, y, x1 - x0 + 20, o.sidewalk ?? 60, o.walk || '#d9d4cc');
    rect(x0 - 10, y + (o.sidewalk ?? 60), x1 - x0 + 20, 14, o.curb || '#b9b2a6');
    rect(x0 - 10, y + (o.sidewalk ?? 60) + 14, x1 - x0 + 20, o.road ?? 420, o.asphalt || '#4a4e57');
    const dy = y + (o.sidewalk ?? 60) + 14 + (o.road ?? 420) * 0.45;
    for (let x = Math.floor(x0 / 160) * 160; x < x1 + 160; x += 160) rect(x, dy, 80, 10, o.dash || '#f2e8c9');
    for (let x = Math.floor(x0 / 90) * 90; x < x1 + 90; x += 90) line(x, y, x, y + (o.sidewalk ?? 60), { col: 'rgba(0,0,0,0.08)', sw: 2 });
  });
}
// one storefront at world x (left edge), ground y; returns anchors {sign:[x,y], door:[x,y], w, h}
function storefront(x, y, o = {}) {
  const w = o.w || 360, h = o.h || 300, wall = o.wall || '#f4e3c9', trim = o.trim || '#2b3a55';
  const aw = o.awning || [C.accent, '#ffffff'], name = o.name || '';
  rect(x, y - h, w, h, wall); if (INK && INKW) { ctx.save(); ctx.strokeStyle = INK; ctx.lineWidth = INKW; ctx.strokeRect(x, y - h, w, h); ctx.restore(); }
  rect(x - 6, y - h - 14, w + 12, 18, trim);                                 // cornice
  const sy = y - h + 26, sh = 58; box(x + 24, sy, w - 48, sh, { fill: o.signBg || trim, stroke: INK, sw: INKW, r: 6 });
  if (name) txt(name, x + w / 2, sy + sh * 0.68, { f: F(o.signFont || 'disp', Math.min(40, fitPx(name, o.signFont || 'disp', w - 80, 40, 14))), col: o.signCol || '#ffffff', align: 'center' });
  const ay = sy + sh + 10, stripes = 8, sw_ = (w + 20) / stripes;       // awning
  for (let i = 0; i < stripes; i++) { ctx.save(); ctx.beginPath(); const ax = x - 10 + i * sw_; ctx.moveTo(ax, ay); ctx.lineTo(ax + sw_, ay); ctx.lineTo(ax + sw_, ay + 44); ctx.quadraticCurveTo(ax + sw_ / 2, ay + 62, ax, ay + 44); ctx.closePath(); ctx.fillStyle = aw[i % 2]; ctx.fill(); if (INK && INKW) { ctx.strokeStyle = INK; ctx.lineWidth = INKW * 0.6; ctx.stroke(); } ctx.restore(); }
  const wy = ay + 70, wh = y - wy - 12, dw = 80;                           // window + door
  box(x + 20, wy, w - dw - 56, wh, { fill: o.glass || '#a9d6e5', stroke: INK || trim, sw: INKW || 3, r: 4 });
  line(x + 30, wy + 12, x + 70, wy + wh - 20, { col: 'rgba(255,255,255,0.6)', sw: 6, cap: 'round' });
  if (o.display) o.display(x + 20, wy, w - dw - 56, wh);                  // caller draws the window display
  box(x + w - dw - 22, wy - 10, dw, wh + 10, { fill: o.door || trim, stroke: INK, sw: INKW, r: 4 }); circle(x + w - 36, wy + wh * 0.55, 4, { fill: '#ffd166' });
  return { sign: [x + w / 2, sy], door: [x + w - dw / 2 - 22, y], mid: [x + w / 2, y - h / 2], x, w, h };
}
// a deterministic row of storefronts from world x0 with shop specs; returns anchors per shop
function storeRow(c, shops, o = {}) {
  const depth = o.depth ?? 1, y = o.y ?? 0, gap = o.gap ?? 40; let x = o.x0 ?? 0; const out = [];
  const [vx0, vx1] = viewX(c, depth);
  layer(c, depth, () => {
    shops.forEach((sh, i) => { const w = sh.w || 360; if (x + w > vx0 - 50 && x < vx1 + 50) out.push(Object.assign({ i, spec: sh }, storefront(x, y, sh)));
      else out.push({ i, spec: sh, sign: [x + w / 2, y - (sh.h || 300) + 26], door: [x + w - 62, y], mid: [x + w / 2, y - (sh.h || 300) / 2], x, w, h: sh.h || 300, culled: true });
      if (o.between) o.between(x + w + gap / 2, y, i); x += w + gap; });
  });
  return out;
}
function tree(x, y, s = 1, o = {}) {
  capsule(x, y, x, y - 90 * s, 16 * s, { fill: o.trunk || '#7a5134' });
  const leaf = o.leaf || '#3f8f5b'; [[0, -150, 70], [-45, -115, 55], [45, -115, 55], [0, -95, 60]].forEach(([dx, dy, r]) => blob(x + dx * s, y + dy * s, r * s, r * s, { fill: leaf }));
}
function lamp(x, y, h = 260, o = {}) { capsule(x, y, x, y - h, 8, { fill: o.col || '#2b3a55' }); capsule(x, y - h, x + 36, y - h, 8, { fill: o.col || '#2b3a55' }); blob(x + 40, y - h + 12, 16, 12, { fill: o.light || '#ffe08a' }); }

// ------------------------------------------------------------------ graphics anchored to the world
// progress 0..1 as a world object (at world x wx, layer depth) passes the camera focus
function passing(c, depth, wx, o = {}) {
  const [sx] = toScreen(c, depth, wx, 0); const focus = o.focus ?? W * 0.55, range = o.range ?? W * 0.45;
  return clamp(1 - Math.abs(sx - focus) / range);
}
// pop-out card anchored at screen point (ax, ay). p: 0..1 (spring it in/out yourself or via passing())
// o: {title, body, badge, w, h, side:'up'|'down'|'left'|'right', fill, col, accent, dist}
function popout(ax, ay, p, o = {}) {
  if (p <= 0.001) return null;
  const w = o.w || 360 * U, h = o.h || 150 * U, side = o.side || 'up', dist = o.dist ?? 90 * U;
  const e = spring(clamp(p * 1.25)); const sc = lerp(0.2, 1, e);
  let cx = ax, cy = ay; if (side === 'up') cy -= dist + h / 2; else if (side === 'down') cy += dist + h / 2; else if (side === 'left') cx -= dist + w / 2; else cx += dist + w / 2;
  cx = clamp(cx, SAFE.l + w / 2, W - SAFE.r - w / 2); cy = clamp(cy, SAFE.t * 0.6 + h / 2, H - SAFE.b * 0.6 - h / 2);
  ctx.save(); ctx.globalAlpha *= clamp(p * 3);
  ctx.translate(ax, ay); ctx.scale(sc, sc); ctx.translate(-ax, -ay);
  const bx = cx - w / 2, by = cy - h / 2;
  // tail
  ctx.save(); ctx.beginPath(); const tx = clamp(ax, bx + 24, bx + w - 24), ty = clamp(ay, by + 20, by + h - 20);
  if (side === 'up' || side === 'down') { const ey = side === 'up' ? by + h - 2 : by + 2; ctx.moveTo(tx - 18 * U, ey); ctx.lineTo(ax, ay); ctx.lineTo(tx + 18 * U, ey); }
  else { const ex = side === 'left' ? bx + w - 2 : bx + 2; ctx.moveTo(ex, ty - 16 * U); ctx.lineTo(ax, ay); ctx.lineTo(ex, ty + 16 * U); }
  ctx.closePath(); ctx.fillStyle = o.fill || '#ffffff'; ctx.fill(); if (INK && INKW) { ctx.strokeStyle = INK; ctx.lineWidth = INKW; ctx.stroke(); } ctx.restore();
  box(bx, by, w, h, { fill: o.fill || '#ffffff', stroke: INK || rgba('#000000', 0.12), sw: INKW || 1.5, r: 16 * U, shadow: 18 });
  circle(ax, ay, 7 * U, { fill: o.accent || ACC, stroke: '#ffffff', sw: 3 });
  const pad = 22 * U; let ty2 = by + pad + 30 * U;
  if (o.badge) { const bf = F('sans', 26 * U, { w: 'bold' }); const bw = tw(o.badge, bf) + 28 * U; box(bx + w - pad - bw, by + pad - 6 * U, bw, 44 * U, { fill: o.accent || ACC, stroke: null, r: 22 * U }); txt(o.badge, bx + w - pad - bw / 2, by + pad + 25 * U, { f: bf, col: '#ffffff', align: 'center' }); }
  if (o.title) { const tf = F('sans', fitPx(o.title, 'sans', w - 2 * pad - (o.badge ? tw(o.badge, F('sans', 26 * U, { w: 'bold' })) + 40 * U : 0), 34 * U, 16 * U, { w: 'bold' }), { w: 'bold' }); txt(o.title, bx + pad, ty2, { f: tf, col: o.col || '#1f2a44' }); ty2 += 44 * U; }
  if (o.body) para(o.body, bx + pad, ty2, w - 2 * pad, { f: F('sans', 22 * U), col: o.col ? rgba(o.col, 0.75) : '#5d6b86', lh: 1.25 });
  ctx.restore();
  return { x: bx, y: by, w, h };
}
function bubble(ax, ay, text, p, o = {}) { const f = F('sans', o.px || 30 * U, { w: 'bold' }); const w = tw(text, f) + 48 * U; return popout(ax, ay, p, Object.assign({ w, h: 74 * U, title: text, dist: 50 * U }, o)); }
