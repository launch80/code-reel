// code-reel engine · core.js
// Globals, math, color, text, shapes, motion primitives and the audit hook.
// Every other engine file and every project scene file runs in this global
// lexical scope (classic <script> tags share top-level let/const bindings).
//
// CONTRACT FOR SCENE CODE
//   defineScene('name', (lt, d, p) => { ... })
//     lt = seconds since the scene started, d = scene duration, p = params
//   Draw in CSS pixels (W x H). The DPR transform is already applied.
//   Determinism: never Math.random / Date.now — use rng(seed) and lt.
'use strict';

// ---------------------------------------------------------------- globals
let W = 1920, H = 1080, FPS = 60, BPM = 120, DUR = 15, TL = null, STYLE = null;
let U = 1;                       // responsive unit: min(W,H)/1080
let SAFE = { l: 96, r: 96, t: 120, b: 110 };   // title-safe box, set per style/aspect
const DPR = Math.max(1, +(new URLSearchParams(location.search).get('dpr') || 1));
const AUDIT = new URLSearchParams(location.search).has('audit');
const cv = document.getElementById('c');
let ctx = cv.getContext('2d');   // NOTE: `let` — the player swaps it to render into transition layers
let C = { bg: '#0b0b0c', surf: '#151517', line: '#2a2a2d', text: '#ececec', mute: '#9b9b9b', or: '#e85d04', hot: '#ff8a3d', cream: '#faf9f7', accent: '#e85d04', ink: '#faf9f7' };
let ACC = C.or, HOTC = C.hot;
// font roles — families come from the style pack (see styles.json)
let FONTS = { sans: 'DM Sans', mono: 'DM Mono', serif: 'Instrument Serif', disp: 'Russo One' };
let FW = { sans: 400, sansBold: 800, mono: 400, monoBold: 500, serif: 400, disp: 400 };
let SANS = '"DM Sans"', MONO = '"DM Mono"', SERIF = '"Instrument Serif"', DISP = '"Russo One"';
let CAPS = true;                 // style: uppercase mono labels
let GLOW = 1;                    // style: glow multiplier (0 on light/print looks)
let SELF_EXIT = true;            // player sets false when the outgoing transition handles the exit
let CUR_SCENE = '';              // for audit attribution

// ---------------------------------------------------------------- math
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, t) => a + (b - a) * t;
const prog = (t, a, b) => (b === a ? (t >= b ? 1 : 0) : clamp((t - a) / (b - a)));
const smooth = x => x * x * (3 - 2 * x);
const eOutExpo = x => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
const eOutCubic = x => 1 - Math.pow(1 - x, 3);
const eOutQuart = x => 1 - Math.pow(1 - x, 4);
const eInOut = x => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
const eInOutSine = x => -(Math.cos(Math.PI * x) - 1) / 2;
const eOutBack = x => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2); };
const eIn = x => x * x * x;
const eStep = (x, n = 4) => Math.floor(clamp(x) * n) / n;
// damped spring from 0 -> 1 (overshoots); freq in Hz-ish, damp 0..1
function spring(x, freq = 2.2, damp = 0.35) {
  if (x <= 0) return 0; if (x >= 1) return 1;   // lands exactly on 1 (counters/positions must settle)
  const w = 2 * Math.PI * freq; return 1 - Math.exp(-damp * w * x) * Math.cos(w * Math.sqrt(1 - damp * damp) * x);
}
const EASE = { linear: x => x, smooth, outExpo: eOutExpo, outCubic: eOutCubic, outQuart: eOutQuart, inOut: eInOut,
  inOutSine: eInOutSine, outBack: eOutBack, in: eIn, step: x => eStep(x, 5), spring: x => spring(x) };
// motion preset (style pack): M.in(x) entrance easing, M.out(x) exit easing, M.k time scale
let M = { in: eOutExpo, out: eIn, move: eInOut, k: 1 };
function rng(seed) { let s = (seed >>> 0) || 1; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; }
function hash1(n) { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); }
// deterministic value noise in [0,1]
function noise2(x, y = 0, seed = 0) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const h = (a, b) => hash1(a * 57 + b * 131 + seed * 17.13);
  const u = smooth(xf), v = smooth(yf);
  return lerp(lerp(h(xi, yi), h(xi + 1, yi), u), lerp(h(xi, yi + 1), h(xi + 1, yi + 1), u), v);
}
// stagger: progress of item i of n whose entrances spread over [a, b]
function stagger(i, n, t, a, b, each = 0.35) {
  const span = Math.max(0, (b - a) - each); const st = a + (n > 1 ? span * i / (n - 1) : 0);
  return prog(t, st, st + each);
}
// exit progress for built-in/custom scenes; 0 when the transition handles the exit
function exitP(lt, d, a = 0.88, b = 0.98) { return SELF_EXIT ? M.out(prog(lt, a * d, b * d)) : 0; }

// ---------------------------------------------------------------- color
function hx(h) {
  if (!h || h[0] !== '#') return [255, 255, 255];
  if (h.length === 4) h = '#' + h[1] + h[1] + h[2] + h[2] + h[3] + h[3];
  const n = parseInt(h.slice(1, 7), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}
function rgba(h, a = 1) { const c = hx(h); return `rgba(${c[0]},${c[1]},${c[2]},${a})`; }
function A(a) { return rgba(ACC, a); }
function Hh(a) { return rgba(HOTC, a); }
function mix(h1, h2, t) {
  const a = hx(h1), b = hx(h2);
  const c = a.map((v, i) => Math.round(lerp(v, b[i], t)));
  return '#' + c.map(v => v.toString(16).padStart(2, '0')).join('');
}
function lum(h) { const c = hx(h).map(v => v / 255); return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]; }
const isLight = () => lum(C.bg) > 0.5;

// ---------------------------------------------------------------- fonts
// F('disp', 180) -> '400 180px "Russo One"'; roles: sans | mono | serif | disp
// opts: {w: weight | 'bold', i: italic}
function F(role, px, o = {}) {
  const fam = FONTS[role] || FONTS.sans;
  let w = o.w;
  if (w === 'bold' || w == null) w = w === 'bold' ? (FW[role + 'Bold'] || 700) : (FW[role] || 400);
  return `${o.i ? 'italic ' : ''}${w} ${Math.round(px)}px "${fam}"`;
}
const cap = s => (CAPS ? String(s).toUpperCase() : String(s));

// ---------------------------------------------------------------- audit
// With ?audit every txt() call records its on-canvas box (CSS px, after the
// current transform). render.py collects them to find text that overflows the
// safe area / canvas or collides with other text.
let AUDIT_LOG = [];
let CLIPS = [];                  // canvas-space rects of active clipRect()/withClip() regions
function _xfRect(x, y, w, h) {
  const m = ctx.getTransform();
  const pts = [[x, y], [x + w, y], [x, y + h], [x + w, y + h]].map(([px, py]) => [(m.a * px + m.c * py + m.e) / DPR, (m.b * px + m.d * py + m.f) / DPR]);
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
}
// clip drawing to a rect; audit knows about it (text outside the clip is not "visible")
function clipRect(x, y, w, h, draw) {
  ctx.save(); ctx.beginPath(); ctx.rect(x, y, w, h); ctx.clip(); CLIPS.push(_xfRect(x, y, w, h));
  try { draw(); } finally { CLIPS.pop(); ctx.restore(); }
}
function auditBox(s, x, y, w, asc, desc, align) {
  if (!AUDIT || !s) return;
  const m = ctx.getTransform();
  let x0 = align === 'center' ? x - w / 2 : align === 'right' ? x - w : x;
  const pts = [[x0, y - asc], [x0 + w, y - asc], [x0, y + desc], [x0 + w, y + desc]].map(([px, py]) =>
    [(m.a * px + m.c * py + m.e) / DPR, (m.b * px + m.d * py + m.f) / DPR]);
  const xs = pts.map(p => p[0]), ys = pts.map(p => p[1]);
  let b = { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
  for (const c of CLIPS) { b = { x0: Math.max(b.x0, c.x0), y0: Math.max(b.y0, c.y0), x1: Math.min(b.x1, c.x1), y1: Math.min(b.y1, c.y1) }; if (b.x1 <= b.x0 || b.y1 <= b.y0) return; }
  AUDIT_LOG.push(Object.assign({ s: String(s).slice(0, 80), scene: CUR_SCENE, a: +ctx.globalAlpha.toFixed(3) }, b));
}

// ---------------------------------------------------------------- text
// txt(s, x, y, {f, col, a, align, ls, glow, gcol, base, stroke, sw})
function txt(s, x, y, o = {}) {
  const { f, col = C.text, a = 1, align = 'left', ls = '0px', glow = 0, gcol = A(0.8), base = 'alphabetic', stroke = null, sw = 2 } = o;
  if (a <= 0 || s == null || s === '') return;
  s = String(s);
  ctx.save(); if (f) ctx.font = f; ctx.letterSpacing = ls; ctx.textAlign = align; ctx.textBaseline = base;
  ctx.globalAlpha *= a; ctx.fillStyle = col;
  const g = glow * GLOW;
  if (g > 0) { ctx.shadowColor = gcol; ctx.shadowBlur = g * DPR; }
  if (stroke) { ctx.lineWidth = sw; ctx.strokeStyle = stroke; ctx.strokeText(s, x, y); }
  ctx.fillText(s, x, y);
  if (g > 0) { ctx.shadowBlur = g * 0.4 * DPR; ctx.fillText(s, x, y); }
  if (AUDIT && ctx.globalAlpha > 0.05) {
    const mm = ctx.measureText(s);
    auditBox(s, x, y, mm.width, mm.actualBoundingBoxAscent, mm.actualBoundingBoxDescent, align);
  }
  ctx.restore();
}
function tw(s, f, ls = '0px') { ctx.save(); ctx.font = f; ctx.letterSpacing = ls; const w = ctx.measureText(String(s)).width; ctx.restore(); return w; }
function typed(s, t, a, b) { s = String(s || ''); return s.slice(0, Math.floor(s.length * prog(t, a, b))); }
// largest px (<= maxPx, >= minPx) at which s fits maxW with role/opts
function fitPx(s, role, maxW, maxPx, minPx = 12, o = {}, ls = '0px') {
  let px = maxPx; while (px > minPx && tw(s, F(role, px, o), ls) > maxW) px -= Math.max(1, px * 0.04);
  return Math.max(minPx, px);
}
// word-wrap into lines no wider than maxW
function wrap(s, f, maxW, ls = '0px') {
  const words = String(s || '').split(/\s+/).filter(Boolean); const lines = []; let cur = '';
  for (const w of words) { const t = cur ? cur + ' ' + w : w; if (tw(t, f, ls) > maxW && cur) { lines.push(cur); cur = w; } else cur = t; }
  if (cur) lines.push(cur); return lines;
}
// paragraph: wraps, draws, returns {lines, h}
function para(s, x, y, maxW, o = {}) {
  const lh = o.lh || 1.2; const px = +((o.f || '').match(/(\d+)px/) || [0, 40])[1];
  const lines = wrap(s, o.f, maxW, o.ls); lines.forEach((ln, i) => txt(ln, x, y + i * px * lh, o));
  return { lines, h: lines.length * px * lh };
}
// mask-wipe reveal left->right
function wipeLine(s, x, y, wd, p, o = {}) {
  if (p <= 0) return; const px = +((o.f || '').match(/(\d+)px/) || [0, 60])[1];
  clipRect(x - 10 - (o.align === 'center' ? wd / 2 : 0), y - px * 1.25, wd * p + 20, px * 1.7, () => txt(s, x, y, o));
}
// per-character layout: fn(i, n, ch) -> {dx, dy, a, sc, rot, col}
function chars(s, x, y, o, fn) {
  s = String(s); const f = o.f; const ls = o.ls || '0px'; const total = tw(s, f, ls);
  let cx = o.align === 'center' ? x - total / 2 : o.align === 'right' ? x - total : x;
  const n = s.length;
  for (let i = 0; i < n; i++) {
    const ch = s[i]; const w = tw(ch, f, ls); const t = fn ? fn(i, n, ch) || {} : {};
    if ((t.a ?? 1) > 0 && ch !== ' ') {
      ctx.save(); ctx.translate(cx + w / 2 + (t.dx || 0), y + (t.dy || 0));
      if (t.rot) ctx.rotate(t.rot); if (t.sc != null) ctx.scale(t.sc, t.sc);
      txt(ch, 0, 0, { ...o, align: 'center', a: (o.a ?? 1) * (t.a ?? 1), col: t.col || o.col });
      ctx.restore();
    }
    cx += w;
  }
  return total;
}
// decode/scramble reveal: glyphs resolve left->right as p goes 0->1
function scramble(s, p, seed = 1, set = 'ABCDEFGHJKLMNPQRSTUVWXYZ0123456789#%&*') {
  s = String(s); const r = rng(seed + Math.floor(p * 30)); let out = '';
  for (let i = 0; i < s.length; i++) {
    const k = i / Math.max(1, s.length);
    out += (s[i] === ' ' || p >= k + 0.15) ? s[i] : (p > k - 0.25 ? set[Math.floor(r() * set.length)] : ' ');
  }
  return out;
}

// ---------------------------------------------------------------- shapes
function rect(x, y, w, h, col, a = 1) { if (a <= 0) return; ctx.save(); ctx.globalAlpha *= a; ctx.fillStyle = col; ctx.fillRect(x, y, w, h); ctx.restore(); }
function rrect(x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, Math.max(0, w), Math.max(0, h), r); }
function box(x, y, w, h, o = {}) {
  const { r = STYLE ? STYLE.radius : 12, fill = C.surf, stroke = C.line, sw = 1.5, a = 1, shadow = 0 } = o;
  ctx.save(); ctx.globalAlpha *= a; rrect(x, y, w, h, r);
  if (AUDIT && fill && ctx.globalAlpha > 0.9 && !/rgba\([^)]*,\s*0?\.[0-8]\d*\)/.test(String(fill))) { const b = _xfRect(x, y, w, h); AUDIT_LOG.push(Object.assign({ occ: true, scene: CUR_SCENE, a: 1, s: '' }, b)); }
  if (shadow) { ctx.shadowColor = isLight() ? 'rgba(0,0,0,0.18)' : 'rgba(0,0,0,0.6)'; ctx.shadowBlur = shadow * DPR; ctx.shadowOffsetY = shadow * 0.3 * DPR; }
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  ctx.shadowColor = 'transparent';
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = sw; ctx.stroke(); }
  ctx.restore();
}
function circle(x, y, r, o = {}) {
  const { fill = null, stroke = null, sw = 2, a = 1 } = o; if (a <= 0 || r <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.beginPath(); ctx.arc(x, y, r, 0, Math.PI * 2);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); } if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = sw; ctx.stroke(); }
  ctx.restore();
}
function line(x1, y1, x2, y2, o = {}) {
  const { col = C.line, sw = 2, a = 1, dash = null, cap = 'butt' } = o; if (a <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = col; ctx.lineWidth = sw; ctx.lineCap = cap; if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore();
}
function dashed(x1, y1, x2, y2, p, a = 1) { if (p > 0) line(x1, y1, lerp(x1, x2, p), lerp(y1, y2, p), { col: ACC, sw: 2, a, dash: [6, 8] }); }
// progressive polyline: draws the first p (0..1) of the path length
function poly(pts, p = 1, o = {}) {
  if (pts.length < 2 || p <= 0) return;
  const seg = []; let L = 0; for (let i = 1; i < pts.length; i++) { const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); seg.push(d); L += d; }
  let rem = L * clamp(p); const { col = ACC, sw = 3, a = 1, join = 'round', fill = null, dash = null } = o;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = col; ctx.lineWidth = sw; ctx.lineJoin = join; ctx.lineCap = 'round'; if (dash) ctx.setLineDash(dash);
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]); let end = pts[0];
  for (let i = 1; i < pts.length && rem > 0; i++) {
    const d = seg[i - 1]; const k = Math.min(1, rem / d);
    end = [lerp(pts[i - 1][0], pts[i][0], k), lerp(pts[i - 1][1], pts[i][1], k)]; ctx.lineTo(end[0], end[1]); rem -= d;
  }
  if (fill && p >= 1) { ctx.fillStyle = fill; ctx.fill(); }
  ctx.stroke(); ctx.restore(); return end;
}
function arrow(x1, y1, x2, y2, p = 1, o = {}) {
  const e = poly([[x1, y1], [x2, y2]], p, o); if (!e || p < 0.98) return;
  const ang = Math.atan2(y2 - y1, x2 - x1), s = o.head || 14;
  ctx.save(); ctx.fillStyle = o.col || ACC; ctx.globalAlpha *= (o.a ?? 1); ctx.beginPath(); ctx.moveTo(x2, y2);
  ctx.lineTo(x2 - s * Math.cos(ang - 0.45), y2 - s * Math.sin(ang - 0.45)); ctx.lineTo(x2 - s * Math.cos(ang + 0.45), y2 - s * Math.sin(ang + 0.45)); ctx.fill(); ctx.restore();
}
function arcP(x, y, r, p, o = {}) {
  const { col = ACC, sw = 6, a = 1, start = -Math.PI / 2 } = o; if (p <= 0) return;
  ctx.save(); ctx.globalAlpha *= a; ctx.strokeStyle = col; ctx.lineWidth = sw; ctx.lineCap = 'round';
  ctx.beginPath(); ctx.arc(x, y, r, start, start + Math.PI * 2 * clamp(p)); ctx.stroke(); ctx.restore();
}
// SVG path data: pathD(d, {x, y, s, p, col, sw, fill, a}) — p draws the stroke on (0..1)
const _pathCache = new Map();
function pathLen(d) {
  if (_pathCache.has(d)) return _pathCache.get(d);
  const el = document.createElementNS('http://www.w3.org/2000/svg', 'path'); el.setAttribute('d', d);
  let L = 1000; try { L = el.getTotalLength(); } catch (e) { }
  _pathCache.set(d, L); return L;
}
function pathD(d, o = {}) {
  const { x = 0, y = 0, s = 1, p = 1, col = ACC, sw = 3, fill = null, a = 1, fillP = null } = o; if (a <= 0) return;
  const P = new Path2D(d); ctx.save(); ctx.globalAlpha *= a; ctx.translate(x, y); ctx.scale(s, s);
  const fp = fillP == null ? (p >= 1 ? 1 : 0) : fillP;
  if (fill && fp > 0) { ctx.save(); ctx.globalAlpha *= fp; ctx.fillStyle = fill; ctx.fill(P); ctx.restore(); }
  if (col && p > 0) {
    const L = pathLen(d); ctx.strokeStyle = col; ctx.lineWidth = sw / s; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    if (p < 1) { ctx.setLineDash([L, L]); ctx.lineDashOffset = L * (1 - p); }
    ctx.stroke(P);
  }
  ctx.restore();
}

// ---------------------------------------------------------------- images / assets
// timeline "assets": {"logo": "assets/logo.svg"} — preloaded by the player
const IMG = {};
function drawImg(name, x, y, w, h, o = {}) {
  const im = IMG[name]; if (!im) return false; const { a = 1, fit = 'contain', r = 0 } = o;
  let dw = w, dh = h; const ar = im.naturalWidth / im.naturalHeight || 1;
  if (fit === 'contain') { if (w / h > ar) dw = h * ar; else dh = w / ar; }
  const dx = x + (w - dw) / 2, dy = y + (h - dh) / 2;
  ctx.save(); ctx.globalAlpha *= a; if (r) { rrect(dx, dy, dw, dh, r); ctx.clip(); }
  if (fit === 'cover') { rrect(x, y, w, h, r); ctx.clip(); const s = Math.max(w / im.naturalWidth, h / im.naturalHeight); ctx.drawImage(im, x + (w - im.naturalWidth * s) / 2, y + (h - im.naturalHeight * s) / 2, im.naturalWidth * s, im.naturalHeight * s); }
  else ctx.drawImage(im, dx, dy, dw, dh);
  ctx.restore(); return true;
}

// ---------------------------------------------------------------- 3D / masks
// simple perspective projection: returns [sx, sy, scale]
function proj(x, y, z, cam = {}) {
  const { f = 1200, cx = W / 2, cy = H / 2, ry = 0, rx = 0, dz = 0 } = cam;
  let X = x * Math.cos(ry) + z * Math.sin(ry), Z = -x * Math.sin(ry) + z * Math.cos(ry);
  let Y = y * Math.cos(rx) - Z * Math.sin(rx); Z = y * Math.sin(rx) + Z * Math.cos(rx);
  const s = f / (f + Z + dz); return [cx + X * s, cy + Y * s, s];
}
// arbitrary clip path; pass bounds {x,y,w,h} so the audit can account for it
function withClip(shapeFn, drawFn, bounds) {
  ctx.save(); ctx.beginPath(); shapeFn(); ctx.clip(); if (bounds) CLIPS.push(_xfRect(bounds.x, bounds.y, bounds.w, bounds.h));
  try { drawFn(); } finally { if (bounds) CLIPS.pop(); ctx.restore(); }
}

// ---------------------------------------------------------------- numbers
function fmt(n) { return Math.round(n).toLocaleString('en-US'); }
// {from,to,fmt} counters; fmt: int | comma | x | k | d(ollar) | pct | dec1 | dec2 | raw
function bigFmt(v, f) {
  switch (f) {
    case 'x': return v.toFixed(1) + '×';
    case 'k': return Math.round(v) + 'K';
    case 'kfmt': case 'comma': return fmt(v);
    case 'd': return '$' + fmt(v);
    case 'pct': return Math.round(v) + '%';
    case 'dec1': return v.toFixed(1);
    case 'dec2': return v.toFixed(2);
    default: return String(Math.round(v));
  }
}
// counter value for {from,to,fmt} at progress p (eased by caller)
function countTo(bf, p) { bf = bf || { from: 0, to: 0 }; return bigFmt(lerp(+bf.from || 0, +bf.to || 0, clamp(p)), bf.fmt); }
function cursor(x, y, t, h = 34, w = 16, col = ACC) { if (Math.floor(t * 2.6) % 2 === 0) rect(x, y - h, w, h, col); }

// ---------------------------------------------------------------- scene registry
const REG = {};
const REG_META = {};             // built-ins register metadata; custom scenes may pass meta too
function defineScene(name, fn, meta = {}) {
  if (!/^[a-z][a-z0-9_]*$/.test(name)) throw new Error('defineScene: bad name ' + name);
  if (REG[name] && REG_META[name] && REG_META[name].builtin) throw new Error('defineScene: built-in type ' + name + ' cannot be overridden');
  REG[name] = fn; REG_META[name] = Object.assign({ builtin: false, exit: 1 }, meta);
}
function builtin(name, fn, meta = {}) { REG[name] = fn; REG_META[name] = Object.assign({ builtin: true, exit: 0.88 }, meta); }
window.defineScene = defineScene;
