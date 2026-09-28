// code-reel engine · looks.js
// The swappable "look" of a reel: backgrounds, HUD overlays, post layers,
// cameras and transitions. A style pack (styles.json) picks one of each; a
// timeline can override any of them. Nothing here is scene-specific.
'use strict';

// ================================================================ BACKGROUNDS
// BG[name](t, o) — full-frame, CSS px, under every scene
const BG = {};
BG.solid = (t, o) => { rect(0, 0, W, H, C.bg); };
BG.grid = (t, o = {}) => {          // perspective floor + glows + dot matrix (the original house look)
  rect(0, 0, W, H, C.bg);
  const hor = H * 0.593, boost = o.boost || 1;
  ctx.save(); ctx.beginPath(); ctx.rect(0, hor, W, H - hor); ctx.clip();
  const vg = ctx.createLinearGradient(0, hor, 0, H); vg.addColorStop(0, A(0)); vg.addColorStop(1, A(1)); ctx.lineWidth = 1.2;
  const vp = W / 2;
  for (let i = -22; i <= 22; i++) { const xb = vp + i * W * 0.0885; ctx.strokeStyle = vg; ctx.globalAlpha = 0.12 * boost; ctx.beginPath(); ctx.moveTo(vp + i * 6, hor); ctx.lineTo(xb * 1.8 - vp * 0.8, H + 40); ctx.stroke(); }
  const sp = (t * 0.9) % 1;
  for (let k = 0; k < 14; k++) { const z = (k + 1 - sp); const y = hor + (H - hor) * Math.pow(z / 14, 2.2) * 1.05; ctx.strokeStyle = ACC; ctx.globalAlpha = 0.10 * boost * Math.pow(z / 14, 1.2); ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.restore();
  const gx = W * 0.78 + Math.sin(t * 0.6) * 120, gy = H * 0.85 + Math.cos(t * 0.5) * 60;
  let g = ctx.createRadialGradient(gx, gy, 0, gx, gy, 900 * U); g.addColorStop(0, A(0.20)); g.addColorStop(1, A(0)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  g = ctx.createRadialGradient(200, 120, 0, 200, 120, 700 * U); g.addColorStop(0, Hh(0.06)); g.addColorStop(1, Hh(0)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.fillStyle = rgba(C.text, 0.045); for (let x = 40; x < W; x += 48) for (let y = 40; y < hor - 60; y += 48) ctx.fillRect(x, y, 2, 2);
};
BG.paper = (t, o = {}) => {         // warm paper, fibre noise, folio rules
  rect(0, 0, W, H, C.bg);
  const r = rng(11); ctx.save(); ctx.globalAlpha = 0.05;
  for (let i = 0; i < 900; i++) { ctx.fillStyle = r() > 0.5 ? '#000' : '#fff'; ctx.fillRect(r() * W, r() * H, 1 + r() * 2, 1); }
  ctx.restore();
  line(SAFE.l, H - 64, W - SAFE.r, H - 64, { col: rgba(C.text, 0.18), sw: 1 });
  line(SAFE.l, 64, W - SAFE.r, 64, { col: rgba(C.text, 0.18), sw: 1 });
};
BG.swiss = (t, o = {}) => {         // 12-col grid, one accent block that drifts between columns
  rect(0, 0, W, H, C.bg);
  const cols = o.cols || 12, gw = (W - SAFE.l - SAFE.r) / cols;
  for (let i = 0; i <= cols; i++) line(SAFE.l + i * gw, 0, SAFE.l + i * gw, H, { col: rgba(C.text, 0.06), sw: 1 });
  const k = Math.floor(t / (60 / BPM * 4)) % cols;
  rect(SAFE.l + k * gw, 0, gw, 10, C.accent, 0.9);
};
BG.blueprint = (t, o = {}) => {     // fine + coarse grid, drafting crosshair
  rect(0, 0, W, H, C.bg);
  const fine = 24 * U, coarse = fine * 5;
  ctx.save(); ctx.lineWidth = 1;
  for (let x = 0; x < W; x += fine) { ctx.strokeStyle = rgba(C.text, x % coarse < 1 ? 0.14 : 0.05); ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 0; y < H; y += fine) { ctx.strokeStyle = rgba(C.text, y % coarse < 1 ? 0.14 : 0.05); ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  ctx.restore();
  const cx = W * (0.5 + 0.3 * Math.sin(t * 0.25)), cy = H * (0.5 + 0.2 * Math.cos(t * 0.19));
  line(cx - 40, cy, cx + 40, cy, { col: A(0.35), sw: 1 }); line(cx, cy - 40, cx, cy + 40, { col: A(0.35), sw: 1 });
  circle(cx, cy, 14, { stroke: A(0.35), sw: 1 });
};
BG.mesh = (t, o = {}) => {          // soft gradient blobs (pastel product look)
  rect(0, 0, W, H, C.bg);
  const cols = [C.accent, C.hot, o.third || mix(C.accent, C.bg, 0.4)];
  ctx.save(); ctx.globalCompositeOperation = isLight() ? 'multiply' : 'screen';
  cols.forEach((c, i) => {
    const x = W * (0.25 + 0.5 * noise2(t * 0.15 + i * 3.1, i)), y = H * (0.2 + 0.6 * noise2(i * 7.3, t * 0.12 + i));
    const g = ctx.createRadialGradient(x, y, 0, x, y, Math.max(W, H) * 0.55);
    g.addColorStop(0, rgba(c, o.strength || 0.35)); g.addColorStop(1, rgba(c, 0)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  });
  ctx.restore();
};
BG.crt = (t, o = {}) => {           // phosphor terminal
  rect(0, 0, W, H, C.bg);
  const g = ctx.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.max(W, H) * 0.7);
  g.addColorStop(0, A(0.10)); g.addColorStop(1, A(0)); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  const y = ((t * 0.35) % 1.2 - 0.1) * H; rect(0, y, W, 90 * U, A(0.04));
};
BG.dots = (t, o = {}) => {
  rect(0, 0, W, H, C.bg); const s = 36 * U;
  for (let x = s / 2; x < W; x += s) for (let y = s / 2; y < H; y += s) {
    const k = noise2(x * 0.004 + t * 0.2, y * 0.004); ctx.fillStyle = rgba(C.text, 0.03 + 0.08 * k); ctx.fillRect(x, y, 2.4 * U, 2.4 * U);
  }
};
BG.gradient = (t, o = {}) => {
  const g = ctx.createLinearGradient(0, 0, W * 0.3, H); g.addColorStop(0, o.top || C.bg); g.addColorStop(1, o.bottom || mix(C.bg, C.accent, 0.18));
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
};
BG.none = (t) => { ctx.clearRect(0, 0, W, H); rect(0, 0, W, H, C.bg); };

// ================================================================ HUD
// HUD[name](t, info) — overlay drawn above scenes, below post. info: {si, n, label, cuts}
const HUD = {};
HUD.none = () => { };
function _hudBrand(x, y, f) {
  const hd = (TL && TL.hud) || {}; const b1 = hd.brand || (TL && TL.name) || '', b2 = hd.brand2 || '';
  txt(b1, x, y, { f, col: C.text, ls: '3px' }); txt(b2, x + tw(b1, f, '3px'), y, { f, col: ACC, ls: '3px' });
  return tw(b1 + b2, f, '3px');
}
HUD.camera = (t, info) => {         // brackets, REC + timecode, scene label, frame counter, progress
  const hd = (TL && TL.hud) || {};
  ctx.save(); ctx.globalAlpha = 0.9; ctx.strokeStyle = rgba(C.text, 0.35); ctx.lineWidth = 2;
  const m = 48, L = 36; [[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]].forEach(([x, y, sx, sy]) => { ctx.beginPath(); ctx.moveTo(x, y + L * sy); ctx.lineTo(x, y); ctx.lineTo(x + L * sx, y); ctx.stroke(); });
  ctx.restore();
  const f = F('mono', 18), fb = F('mono', 18, { w: 'bold' });
  const bw = _hudBrand(100, 92, fb);
  const series = hd.series ? `  ·  ${hd.series}${hd.line ? '  ·  ' + hd.line : ''}` : '';
  if (W >= 1600) txt(series, 100 + bw, 92, { f, col: C.mute, ls: '3px' });
  const fr = Math.floor(t * FPS); const tc = `00:00:${String(Math.floor(t)).padStart(2, '0')}:${String(fr % FPS).padStart(2, '0')}`;
  const tcw = tw('TC ' + tc, f, '2px');
  if (Math.floor(t * 2) % 2 === 0) circle(W - 100 - tcw - 110, 86, 7, { fill: '#ff3b30' });
  txt('REC', W - 100 - tcw - 92, 92, { f: fb, col: C.text, ls: '3px' });
  txt('TC ' + tc, W - 100, 92, { f, col: C.mute, align: 'right', ls: '2px' });
  txt(`SCENE ${String(info.si + 1).padStart(2, '0')}/${String(info.n).padStart(2, '0')} — ${info.label}`, 100, H - 80, { f, col: C.mute, ls: '3px' });
  if (W >= 1600) txt(`${W}×${H} · ${FPS}FPS · F${String(fr).padStart(4, '0')}`, W - 100, H - 80, { f, col: C.mute, align: 'right', ls: '2px' });
  rect(0, H - 6, W, 6, mix(C.bg, C.text, 0.06)); rect(0, H - 6, W * t / DUR, 6, ACC);
  info.cuts.forEach(c => rect(W * c / DUR - 1, H - 10, 2, 10, C.mute));
};
HUD.minimal = (t, info) => {
  const f = F('mono', 16 * Math.max(1, U));
  _hudBrand(SAFE.l, 70, F('mono', 16 * Math.max(1, U), { w: 'bold' }));
  txt(`${String(info.si + 1).padStart(2, '0')} / ${String(info.n).padStart(2, '0')}`, W - SAFE.r, 70, { f, col: C.mute, align: 'right', ls: '2px' });
};
HUD.editorial = (t, info) => {      // magazine running head + folio
  const hd = (TL && TL.hud) || {}; const f = F('serif', 22, { i: true }), fm = F('mono', 14);
  txt((hd.brand || '') + (hd.brand2 || ''), SAFE.l, 50, { f: F('sans', 16, { w: 'bold' }), col: C.text, ls: '4px' });
  txt(hd.line || hd.series || '', W / 2, 50, { f, col: C.mute, align: 'center' });
  txt(`No. ${String(info.si + 1).padStart(2, '0')}`, W - SAFE.r, 50, { f: fm, col: C.mute, align: 'right', ls: '2px' });
  txt(info.label.toLowerCase(), SAFE.l, H - 34, { f, col: C.mute });
  txt(`${info.si + 1} — ${info.n}`, W - SAFE.r, H - 34, { f: fm, col: C.mute, align: 'right' });
};
HUD.blueprint = (t, info) => {      // drafting title block, bottom right
  const hd = (TL && TL.hud) || {}; const bw = 420, bh = 96, x = W - SAFE.r - bw + 40, y = H - bh - 30;
  ctx.save(); ctx.strokeStyle = rgba(C.text, 0.5); ctx.lineWidth = 1.2; ctx.strokeRect(x, y, bw, bh);
  ctx.beginPath(); ctx.moveTo(x, y + 40); ctx.lineTo(x + bw, y + 40); ctx.moveTo(x + 280, y + 40); ctx.lineTo(x + 280, y + bh); ctx.stroke(); ctx.restore();
  txt(((hd.brand || '') + (hd.brand2 || '')).toUpperCase(), x + 14, y + 28, { f: F('mono', 18, { w: 'bold' }), col: C.text, ls: '3px' });
  txt(info.label, x + 14, y + 76, { f: F('mono', 15), col: C.mute, ls: '2px' });
  txt(`SHT ${info.si + 1}/${info.n}`, x + 294, y + 76, { f: F('mono', 15), col: ACC, ls: '2px' });
  const m = 30; ctx.save(); ctx.strokeStyle = rgba(C.text, 0.35); ctx.strokeRect(m, m, W - 2 * m, H - 2 * m); ctx.restore();
};
HUD.terminal = (t, info) => {       // status bar
  const hd = (TL && TL.hud) || {}; rect(0, H - 44, W, 44, ACC, 0.9);
  const f = F('mono', 20, { w: 'bold' });
  txt(` ${((hd.brand || '') + (hd.brand2 || '')).toLowerCase()} `, 20, H - 14, { f, col: C.bg });
  txt(`[${info.si + 1}/${info.n}] ${info.label.toLowerCase()}`, 260, H - 14, { f, col: C.bg });
  txt(`${t.toFixed(2)}s`, W - 24, H - 14, { f, col: C.bg, align: 'right' });
};

// ================================================================ CAMERAS
// CAM[name](t, sp, imp, fi) -> {x, y, z, r}; sp = scene progress 0..1, imp = impact strength 0..1
const CAM = {};
CAM.static = () => ({ x: 0, y: 0, z: 1, r: 0 });
CAM.push = (t, sp, imp, fi) => { const r = rng(fi + 1); return { x: (r() - 0.5) * 22 * imp, y: (r() - 0.5) * 22 * imp, z: 1 + 0.03 * sp, r: 0 }; };
CAM.drift = (t, sp, imp) => ({ x: Math.sin(t * 0.4) * 14, y: Math.cos(t * 0.33) * 8, z: 1.01 + 0.01 * Math.sin(t * 0.2), r: 0 });
CAM.handheld = (t, sp, imp) => ({ x: (noise2(t * 1.3, 1) - 0.5) * 18 + imp * 6, y: (noise2(t * 1.1, 7) - 0.5) * 12, z: 1.02, r: (noise2(t * 0.8, 3) - 0.5) * 0.006 });
CAM.dolly = (t, sp, imp) => ({ x: 0, y: 0, z: 1.06 - 0.06 * eInOutSine(sp), r: 0 });
CAM.punch = (t, sp, imp) => ({ x: 0, y: 0, z: 1 + 0.05 * imp, r: 0 });

// ================================================================ POST
// POST[name](t, fi, fx) — runs on the MAIN canvas in DEVICE pixels (identity transform).
// fx = {glitch: 0..1, flash: 0..1} computed by the player from cuts/impacts.
const POST = {};
const _grains = []; function grains() {
  if (_grains.length) return _grains; const r = rng(7);
  for (let i = 0; i < 6; i++) { const g = document.createElement('canvas'); g.width = 480; g.height = 270; const gc = g.getContext('2d'); const id = gc.createImageData(480, 270); for (let p = 0; p < id.data.length; p += 4) { const v = r() * 255; id.data[p] = id.data[p + 1] = id.data[p + 2] = v; id.data[p + 3] = 255; } gc.putImageData(id, 0, 0); _grains.push(g); }
  return _grains;
}
function _flash(fx, col, k = 1) { if (fx.flash > 0) { ctx.save(); ctx.globalCompositeOperation = isLight() ? 'multiply' : 'screen'; ctx.fillStyle = rgba(col, fx.flash * k); ctx.fillRect(0, 0, cv.width, cv.height); ctx.restore(); } }
function _grain(fi, a, op = 'overlay') { ctx.save(); ctx.globalAlpha = a; ctx.globalCompositeOperation = op; ctx.imageSmoothingEnabled = false; ctx.drawImage(grains()[fi % 6], 0, 0, cv.width, cv.height); ctx.restore(); }
function _vignette(a) { const VW = cv.width, VH = cv.height; const g = ctx.createRadialGradient(VW / 2, VH / 2, VH * 0.45, VW / 2, VH / 2, VH * 1.05); g.addColorStop(0, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(0,0,0,${a})`); ctx.fillStyle = g; ctx.fillRect(0, 0, VW, VH); }
function _scan(a, step = 4) { ctx.fillStyle = `rgba(0,0,0,${a})`; for (let y = 0; y < cv.height; y += step * DPR) ctx.fillRect(0, y, cv.width, DPR); }
function _glitch(fx, fi) {
  if (!(fx.glitch > 0)) return; const VW = cv.width, VH = cv.height; const gl = fx.glitch;
  const b = _layer('glitch'); b.ctx.clearRect(0, 0, VW, VH); b.ctx.drawImage(cv, 0, 0); const r = rng(fi * 31 + 5);
  for (let i = 0; i < 10; i++) { const y = r() * VH, h = (10 + r() * 90) * DPR, dx = (r() - 0.5) * 260 * gl * DPR; ctx.drawImage(b.c, 0, y, VW, h, dx, y, VW, h); }
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = 0.35 * gl; ctx.drawImage(b.c, 18 * gl * DPR, 0); ctx.globalAlpha = 0.2 * gl; ctx.drawImage(b.c, -18 * gl * DPR, 0); ctx.restore();
}
POST.film = (t, fi, fx, o = {}) => { _glitch(fx, fi); _flash(fx, HOTC, o.flash ?? 1); _scan(0.10); _grain(fi, o.grain ?? 0.055); _vignette(o.vignette ?? 0.6); };
POST.clean = (t, fi, fx, o = {}) => { _glitch(fx, fi); _flash(fx, HOTC, o.flash ?? 0.5); };
POST.paper = (t, fi, fx, o = {}) => { _glitch(fx, fi); _flash(fx, C.accent, o.flash ?? 0.25); _grain(fi, o.grain ?? 0.07, 'multiply'); _vignette(o.vignette ?? 0.12); };
POST.crt = (t, fi, fx, o = {}) => {
  _glitch(fx, fi); _flash(fx, HOTC, o.flash ?? 1);
  // bloom: blurred copy of the frame, screened back on
  const b = _layer('bloom'); b.ctx.clearRect(0, 0, cv.width, cv.height); b.ctx.filter = `blur(${6 * DPR}px) brightness(1.2)`; b.ctx.drawImage(cv, 0, 0); b.ctx.filter = 'none';
  ctx.save(); ctx.globalCompositeOperation = 'screen'; ctx.globalAlpha = o.bloom ?? 0.45; ctx.drawImage(b.c, 0, 0); ctx.restore();
  _scan(o.scan ?? 0.22, 3); _grain(fi, 0.05); _vignette(0.75);
};
POST.print = (t, fi, fx, o = {}) => {   // slight ink misregistration + paper grain
  _flash(fx, C.accent, 0.2);
  const b = _layer('print'); b.ctx.clearRect(0, 0, cv.width, cv.height); b.ctx.drawImage(cv, 0, 0);
  ctx.save(); ctx.globalCompositeOperation = 'multiply'; ctx.globalAlpha = 0.18; ctx.drawImage(b.c, 2 * DPR, 1 * DPR); ctx.restore();
  _grain(fi, 0.06, 'multiply');
};

// offscreen layers (device px) shared by post + transitions
const _layers = {};
function _layer(name) {
  let L = _layers[name];
  if (!L || L.c.width !== cv.width || L.c.height !== cv.height) { const c = document.createElement('canvas'); c.width = cv.width; c.height = cv.height; L = _layers[name] = { c, ctx: c.getContext('2d') }; }
  return L;
}

// ================================================================ TRANSITIONS
// TRANS[name] = {self, dur, draw(q, A, B, o)}; A/B are layer canvases of the
// outgoing / incoming FRAME (device px, opaque: background + camera + scene).
// self:true  -> no overlap; outgoing scene plays its own exit (cut, glitch, flash)
// q = eased progress 0..1 across the transition window centred on the cut.
const TRANS = {};
function _dir(o) { return ({ left: [-1, 0], right: [1, 0], up: [0, -1], down: [0, 1] })[o.dir || 'left'] || [-1, 0]; }
TRANS.cut = { self: true, dur: 0 };
TRANS.glitch = { self: true, dur: 0, fx: 'glitch' };
TRANS.flash = { self: true, dur: 0, fx: 'flash' };
TRANS.dissolve = { self: false, dur: 0.5, draw(q, a, b) { ctx.globalAlpha = 1 - q; ctx.drawImage(a, 0, 0); ctx.globalAlpha = q; ctx.drawImage(b, 0, 0); ctx.globalAlpha = 1; } };
TRANS.push = { self: false, dur: 0.45, draw(q, a, b, o) {
  const [dx, dy] = _dir(o); const VW = cv.width, VH = cv.height;
  ctx.drawImage(a, dx * q * VW, dy * q * VH); ctx.drawImage(b, dx * (q - 1) * VW, dy * (q - 1) * VH);
} };
TRANS.whip = { self: false, dur: 0.35, draw(q, a, b, o) {
  const [dx, dy] = _dir(o); const VW = cv.width, VH = cv.height; const blur = Math.sin(Math.PI * q);
  for (let k = 0; k < 6; k++) { const s = (k / 5 - 0.5) * 0.12 * blur; ctx.globalAlpha = 1 / 6 * 1.6;
    ctx.drawImage(a, dx * (q + s) * VW, dy * (q + s) * VH); ctx.drawImage(b, dx * (q - 1 + s) * VW, dy * (q - 1 + s) * VH); }
  ctx.globalAlpha = 1;
} };
TRANS.wipe = { self: false, dur: 0.5, draw(q, a, b, o) {
  const VW = cv.width, VH = cv.height; const [dx, dy] = _dir(o);
  ctx.drawImage(a, 0, 0); ctx.save(); ctx.beginPath();
  let ex;
  if (dx) { const w = VW * q; const x = dx < 0 ? VW - w : 0; ctx.rect(x, 0, w, VH); ex = dx < 0 ? x : w; }
  else { const h = VH * q; const y = dy < 0 ? VH - h : 0; ctx.rect(0, y, VW, h); ex = dy < 0 ? y : h; }
  ctx.clip(); ctx.drawImage(b, 0, 0); ctx.restore();
  ctx.fillStyle = ACC; if (dx) ctx.fillRect(ex - 3 * DPR, 0, 6 * DPR, VH); else ctx.fillRect(0, ex - 3 * DPR, VW, 6 * DPR);
} };
TRANS.zoom = { self: false, dur: 0.5, draw(q, a, b) {
  const VW = cv.width, VH = cv.height;
  const s1 = 1 + q * 0.6; ctx.globalAlpha = clamp(1 - q * 2); ctx.drawImage(a, VW / 2 - VW * s1 / 2, VH / 2 - VH * s1 / 2, VW * s1, VH * s1);
  const s2 = lerp(0.82, 1, q); ctx.globalAlpha = clamp(q * 2 - 0.4); ctx.drawImage(b, VW / 2 - VW * s2 / 2, VH / 2 - VH * s2 / 2, VW * s2, VH * s2); ctx.globalAlpha = 1;
} };
TRANS.iris = { self: false, dur: 0.55, draw(q, a, b, o) {
  const VW = cv.width, VH = cv.height; ctx.drawImage(a, 0, 0);
  const cx = (o.x ?? 0.5) * VW, cy = (o.y ?? 0.5) * VH, R = Math.hypot(VW, VH) * q * 0.62;
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.clip(); ctx.drawImage(b, 0, 0); ctx.restore();
  ctx.save(); ctx.strokeStyle = ACC; ctx.lineWidth = 4 * DPR; ctx.beginPath(); ctx.arc(cx, cy, R, 0, 7); ctx.stroke(); ctx.restore();
} };
TRANS.shutter = { self: false, dur: 0.5, draw(q, a, b, o) {
  const VW = cv.width, VH = cv.height, n = o.n || 8, bh = VH / n; ctx.drawImage(a, 0, 0);
  for (let i = 0; i < n; i++) { const k = clamp((q - i / n * 0.5) / 0.5); if (k <= 0) continue;
    ctx.save(); ctx.beginPath(); const w = VW * eInOut(k); ctx.rect(i % 2 ? VW - w : 0, i * bh, w, bh + 1); ctx.clip(); ctx.drawImage(b, 0, 0); ctx.restore(); }
} };
TRANS.slide = { self: false, dur: 0.5, draw(q, a, b, o) {  // incoming covers the (dimmed) outgoing
  const [dx, dy] = _dir(o); const VW = cv.width, VH = cv.height;
  ctx.drawImage(a, 0, 0); ctx.fillStyle = `rgba(0,0,0,${0.5 * q})`; ctx.fillRect(0, 0, VW, VH);
  ctx.save(); ctx.translate(dx * (q - 1) * VW, dy * (q - 1) * VH); ctx.drawImage(b, 0, 0); ctx.restore();
} };
