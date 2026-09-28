// code-reel engine · scenes_plus.js — non-stat blueprint scenes.
// Same rules as scenes.js: responsive, style-driven, no brand defaults.
// These show vocabulary beyond numbers: statements, code, product UI, process,
// history, identity, rankings, networks. Still blueprints — a final reel's
// hero scenes are written for that video.
'use strict';

// ---- statement: {kicker, text, emphasis:[words], align:'left'|'center', reveal:'rise'|'wipe'|'scramble'|'type'}
builtin('statement', (lt, d, p) => {
  const out = exitP(lt, d); const center = p.align === 'center';
  ctx.save(); ctx.globalAlpha = 1 - out; ctx.translate(0, -out * 40 * U);
  const maxW = CW() * (center ? 1 : 0.9); let px = 120 * U, lines;
  do { lines = wrap(p.text || '', F('serif', px), maxW); if (lines.length <= 4) break; px *= 0.9; } while (px > 34 * U);
  const f = F('serif', px); const lh = px * 1.12; const blockH = lines.length * lh;
  const y0 = (H - blockH) / 2 + px * 0.8; const emph = new Set((p.emphasis || []).map(w => w.toLowerCase().replace(/[^\w]/g, '')));
  if (p.kicker) txt(cap(p.kicker), center ? W / 2 : L0(), y0 - px * 1.1, { f: F('mono', 22 * U, { w: 'bold' }), col: ACC, ls: '4px', align: center ? 'center' : 'left', a: M.in(prog(lt, 0, 0.3)) });
  let wi = 0; const total = (p.text || '').split(/\s+/).length; const mode = p.reveal || 'rise';
  lines.forEach((ln, li) => {
    const lw = tw(ln, f); let x = center ? W / 2 - lw / 2 : L0(); const y = y0 + li * lh;
    ln.split(' ').forEach(w => {
      const ww = tw(w + ' ', f); const st = 0.08 * d + (wi / Math.max(1, total)) * 0.45 * d; const e = M.in(prog(lt, st, st + 0.35 + 0.1 * d));
      const key = w.toLowerCase().replace(/[^\w]/g, '');
      if (emph.has(key) && e > 0) { const hp = eOutCubic(prog(lt, st + 0.2, st + 0.6)); rect(x - 4, y - px * 0.36, (tw(w, f) + 8) * hp, px * 0.34, ACC, isLight() ? 0.28 : 0.45); }
      const col = emph.has(key) ? (isLight() ? C.cream : C.cream) : C.text;
      if (mode === 'scramble') txt(scramble(w, e, wi + 3), x, y, { f, col, a: e > 0 ? 1 : 0 });
      else if (mode === 'type') txt(typed(w, e, 0, 1), x, y, { f, col });
      else if (mode === 'wipe') wipeLine(w, x, y, tw(w, f), e, { f, col });
      else txt(w, x, y + (1 - e) * px * 0.5, { f, col, a: e });
      x += ww; wi++;
    });
  });
  ctx.restore();
}, { exit: 0.88 });

// ---- code: {file, lines:[str], add:[idx], del:[idx], focus:idx, caption, lang}
const _KW = /\b(const|let|var|function|return|if|else|for|while|import|from|export|def|class|async|await|new|true|false|null|None|self|in|of|fn|pub|use|struct|impl|type)\b/g;
function _codeTokens(s) {
  const out = []; const re = /(\/\/.*|#.*$)|("[^"]*"|'[^']*'|`[^`]*`)|(\b\d+(?:\.\d+)?\b)|(\b[A-Za-z_]\w*\b)|(\s+)|(.)/g; let m;
  while ((m = re.exec(s))) {
    if (m[1]) out.push([m[1], 'com']); else if (m[2]) out.push([m[2], 'str']); else if (m[3]) out.push([m[3], 'num']);
    else if (m[4]) out.push([m[4], _KW.test(m[4]) ? 'kw' : (s[re.lastIndex] === '(' ? 'fn' : 'id')]); else out.push([m[0], 'p']);
    _KW.lastIndex = 0;
  }
  return out;
}
builtin('code', (lt, d, p) => {
  const lines = p.lines || []; const out = exitP(lt, d); const ap = M.in(prog(lt, 0, 0.2 * d));
  const pw = Math.min(1500 * U, CW()), fs = Math.min(30 * U, fitPx(lines.reduce((a, b) => a.length > b.length ? a : b, ''), 'mono', pw - 170 * U, 30 * U, 14 * U));
  const lh = fs * 1.55, ph = 90 * U + lines.length * lh + (p.caption ? 20 * U : 30 * U); const px = (W - pw) / 2, py = Math.max(SAFE.t, (H - ph) / 2 - (p.caption ? 40 * U : 0));
  ctx.save(); ctx.globalAlpha = ap * (1 - out); ctx.translate(0, (1 - ap) * 60 * U);
  box(px, py, pw, ph, { fill: isLight() ? '#1e1e24' : C.surf, stroke: C.line, r: STYLE.radius + 2, shadow: 30 });
  ['#ff5f56', '#ffbd2e', '#27c93f'].forEach((c, i) => circle(px + 30 * U + i * 24 * U, py + 28 * U, 7 * U, { fill: c }));
  if (p.file) txt(p.file, px + pw / 2, py + 35 * U, { f: F('mono', 20 * U), col: '#9aa0aa', align: 'center' });
  const PAL = { kw: HOTC, str: '#a5d6a7', num: '#ffcc80', com: '#6b7280', fn: '#82aaff', id: '#e6e6e6', p: '#c8c8c8' };
  const add = new Set(p.add || []), del = new Set(p.del || []); const Fm = F('mono', fs);
  const per = 0.55 * d / Math.max(1, lines.length);
  lines.forEach((ln, i) => {
    const st = 0.15 * d + i * per; const shown = typed(ln, lt, st, st + per * 0.9); if (lt < st) return;
    const y = py + 80 * U + i * lh; const x0 = px + 110 * U;
    if (add.has(i)) rect(px + 2, y - fs * 1.05, pw - 4, lh, '#2ea043', 0.18); if (del.has(i)) rect(px + 2, y - fs * 1.05, pw - 4, lh, '#f85149', 0.18);
    if (p.focus === i && lt > st + per) rect(px + 2, y - fs * 1.05, 6 * U, lh, ACC);
    txt(String(i + 1).padStart(2, ' '), px + 40 * U, y, { f: Fm, col: '#555b66' });
    if (add.has(i) || del.has(i)) txt(add.has(i) ? '+' : '−', px + 80 * U, y, { f: Fm, col: add.has(i) ? '#3fb950' : '#f85149' });
    let x = x0; for (const [tok, k] of _codeTokens(shown)) { txt(tok, x, y, { f: Fm, col: del.has(i) ? '#8b949e' : PAL[k] }); x += tw(tok, Fm); }
    if (lt < st + per && lt >= st) cursor(x + 2, y + 4, lt, fs * 1.1, fs * 0.55);
  });
  if (p.caption) txt(p.caption, W / 2, py + ph + 70 * U, { f: F('serif', fitPx(p.caption, 'serif', CW(), 48 * U, 22 * U, { i: true }), { i: true }), col: C.cream, align: 'center', a: M.in(prog(lt, 0.6 * d, 0.8 * d)) });
  ctx.restore();
}, { exit: 0.9 });

// ---- ui: {app, nav:[str], title, items:[{title, meta, badge}], clicks:[{item, at}], toast}
builtin('ui', (lt, d, p) => {
  const out = exitP(lt, d); const ap = M.in(prog(lt, 0, 0.18 * d));
  const aw = Math.min(1500 * U, CW()), ah = Math.min(820 * U, H - SAFE.t - SAFE.b), ax = (W - aw) / 2, ay = (H - ah) / 2;
  ctx.save(); ctx.globalAlpha = ap * (1 - out); const sc = lerp(0.94, 1, ap); ctx.translate(W / 2, H / 2); ctx.scale(sc, sc); ctx.translate(-W / 2, -H / 2);
  box(ax, ay, aw, ah, { fill: isLight() ? '#ffffff' : C.surf, stroke: C.line, r: STYLE.radius + 6, shadow: 40 });
  rect(ax, ay + 56 * U, aw, 1, C.line); txt(p.app || '', ax + 28 * U, ay + 36 * U, { f: F('sans', 22 * U, { w: 'bold' }), col: C.text });
  const nav = p.nav || []; const sw = aw * 0.22; rect(ax + sw, ay + 57 * U, 1, ah - 57 * U, C.line);
  nav.forEach((n, i) => txt(n, ax + 28 * U, ay + 110 * U + i * 48 * U, { f: F('sans', 22 * U), col: i === 0 ? ACC : C.mute }));
  const mx = ax + sw + 40 * U, mw = aw - sw - 80 * U; txt(p.title || '', mx, ay + 120 * U, { f: F('sans', 40 * U, { w: 'bold' }), col: C.cream });
  const items = p.items || []; const ih = 86 * U; const clicks = p.clicks || [];
  let sel = -1; clicks.forEach(c => { if (lt >= c.at) sel = c.item; });
  items.forEach((it, i) => {
    const e = stagger(i, items.length, lt, 0.12 * d, 0.45 * d, 0.3); if (e <= 0) return; const y = ay + 160 * U + i * (ih + 14 * U);
    ctx.save(); ctx.globalAlpha *= e; ctx.translate(0, (1 - M.in(e)) * 30 * U);
    box(mx, y, mw, ih, { fill: sel === i ? A(isLight() ? 0.1 : 0.16) : (isLight() ? '#f7f7f9' : rgba(C.bg, 0.6)), stroke: sel === i ? ACC : C.line, r: STYLE.radius });
    txt(it.title || '', mx + 24 * U, y + 38 * U, { f: F('sans', 26 * U, { w: 'bold' }), col: C.text });
    txt(it.meta || '', mx + 24 * U, y + 68 * U, { f: F('sans', 20 * U), col: C.mute });
    if (it.badge) { const bf = F('mono', 18 * U, { w: 'bold' }); const bw = tw(it.badge, bf) + 24 * U; box(mx + mw - bw - 20 * U, y + ih / 2 - 17 * U, bw, 34 * U, { fill: A(0.15), stroke: null, r: 17 * U }); txt(it.badge, mx + mw - bw / 2 - 20 * U, y + ih / 2 + 6 * U, { f: bf, col: ACC, align: 'center' }); }
    ctx.restore();
  });
  // cursor: glides to each click target, presses on `at`
  if (clicks.length) {
    let cx = W * 0.8, cy = H * 0.85; let prevT = 0, px_ = cx, py_ = cy;
    for (const c of clicks) { const ty = ay + 160 * U + c.item * (ih + 14 * U) + ih / 2, tx = mx + mw * 0.6; const u = M.move(prog(lt, Math.max(prevT, c.at - 0.6), c.at)); cx = lerp(px_, tx, u); cy = lerp(py_, ty, u); if (lt >= c.at) { px_ = tx; py_ = ty; } prevT = c.at; }
    const press = clicks.some(c => lt >= c.at && lt < c.at + 0.15); const s = press ? 0.85 : 1;
    if (clicks.some(c => lt >= c.at && lt < c.at + 0.5)) { const c = clicks.filter(c => lt >= c.at).pop(); const k = prog(lt, c.at, c.at + 0.5); circle(cx, cy, 10 * U + k * 40 * U, { stroke: A(1 - k), sw: 3 }); }
    ctx.save(); ctx.translate(cx, cy); ctx.scale(s * U, s * U); ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(0, 34); ctx.lineTo(9, 26); ctx.lineTo(16, 40); ctx.lineTo(22, 37); ctx.lineTo(15, 23); ctx.lineTo(27, 23); ctx.closePath();
    ctx.fillStyle = '#111'; ctx.fill(); ctx.strokeStyle = '#fff'; ctx.lineWidth = 2.5; ctx.stroke(); ctx.restore();
  }
  if (p.toast && sel >= 0) { const c = clicks[clicks.length - 1]; const k = M.in(prog(lt, c.at + 0.2, c.at + 0.6)); const tf = F('sans', 24 * U, { w: 'bold' }); const tw_ = tw(p.toast, tf) + 60 * U;
    box(W / 2 - tw_ / 2, ay + ah - 90 * U + (1 - k) * 40 * U, tw_, 60 * U, { fill: C.cream, stroke: null, r: 30 * U, a: k }); txt(p.toast, W / 2, ay + ah - 52 * U + (1 - k) * 40 * U, { f: tf, col: C.bg, align: 'center', a: k }); }
  ctx.restore();
}, { exit: 0.9 });

// ---- steps: {title, steps:[{label, sub}], active}
builtin('steps', (lt, d, p) => {
  const st = p.steps || []; const n = st.length; const out = exitP(lt, d); const horiz = wide() && n <= 5;
  ctx.save(); ctx.globalAlpha = 1 - out;
  if (p.title) txt(cap(p.title), W / 2, SAFE.t + 80 * U, { f: F('mono', 26 * U, { w: 'bold' }), col: ACC, align: 'center', ls: '5px', a: M.in(prog(lt, 0, 0.25)) });
  const half = Math.min(CW() / n / 2, Math.max(...st.map(s => Math.max(tw(s.label || '', F('sans', 34 * U, { w: 'bold' })), tw(s.sub || '', F('sans', 22 * U))))) / 2 + 10 * U);
  const pts = st.map((_, i) => horiz ? [L0() + half + (CW() - 2 * half) * (n > 1 ? i / (n - 1) : 0.5), H * 0.5] : [W / 2, SAFE.t + 220 * U + i * (H - SAFE.t - SAFE.b - 300 * U) / Math.max(1, n - 1)]);
  const lineP = eInOut(prog(lt, 0.1 * d, 0.7 * d));
  for (let i = 1; i < n; i++) { const k = clamp(lineP * (n - 1) - (i - 1)); if (k > 0) arrow(pts[i - 1][0] + (horiz ? 70 : 0) * U, pts[i - 1][1] + (horiz ? 0 : 70) * U, pts[i][0] - (horiz ? 70 : 0) * U, pts[i][1] - (horiz ? 0 : 70) * U, k, { col: A(0.8), sw: 3 }); }
  const active = p.active != null ? p.active : Math.min(n - 1, Math.floor(prog(lt, 0.1 * d, 0.75 * d) * n));
  st.forEach((s, i) => {
    const e = M.in(prog(lt, 0.1 * d + i * 0.6 * d / n, 0.1 * d + i * 0.6 * d / n + 0.35)); if (e <= 0) return; const [x, y] = pts[i];
    const on = i <= active; const r = 58 * U * e;
    circle(x, y, r, { fill: on ? ACC : C.surf, stroke: on ? ACC : C.line, sw: 3 });
    if (i === active) { const k = (lt * 1.4) % 1; circle(x, y, r + k * 30 * U, { stroke: A(1 - k), sw: 2 }); }
    txt(String(i + 1), x, y + 16 * U, { f: F('disp', 46 * U), col: on ? (isLight() ? '#ffffff' : C.bg) : C.mute, align: 'center', a: e });
    const lf = F('sans', fitPx(s.label || '', 'sans', horiz ? CW() / n - 20 * U : CW() * 0.4, 34 * U, 16 * U, { w: 'bold' }), { w: 'bold' });
    if (horiz) { txt(s.label || '', x, y + 120 * U, { f: lf, col: C.cream, align: 'center', a: e }); if (s.sub) para(s.sub, x, y + 162 * U, CW() / n - 20 * U, { f: F('sans', 22 * U), col: C.mute, a: e, align: 'center' }); }
    else { txt(s.label || '', x + 90 * U, y + 10 * U, { f: lf, col: C.cream, a: e }); if (s.sub) txt(s.sub, x + 90 * U, y + 46 * U, { f: F('sans', 22 * U), col: C.mute, a: e }); }
  });
  ctx.restore();
}, { exit: 0.9 });

// ---- milestones: {title, items:[{when, label}]}
builtin('milestones', (lt, d, p) => {
  const it = p.items || []; const n = it.length; const out = exitP(lt, d);
  ctx.save(); ctx.globalAlpha = 1 - out;
  if (p.title) txt(p.title, L0(), SAFE.t + 90 * U, { f: F('serif', fitPx(p.title, 'serif', CW(), 72 * U, 30 * U, { i: true }), { i: true }), col: C.cream, a: M.in(prog(lt, 0, 0.3)) });
  const lw_ = Math.max(...it.map(m => Math.max(tw(m.label || '', F('sans', 30 * U, { w: 'bold' })), tw(m.when || '', F('mono', 24 * U, { w: 'bold' }))))); const half = Math.min(lw_ / 2 + 10 * U, CW() / Math.max(2, n) / 2);
  const y = H * 0.56, x0 = L0() + half, x1 = W - SAFE.r - half; const lp = eInOut(prog(lt, 0.1 * d, 0.8 * d));
  line(x0, y, lerp(x0, x1, lp), y, { col: ACC, sw: 4 });
  const slot = (x1 - x0) / Math.max(1, n - 1);
  it.forEach((m, i) => {
    const x = n > 1 ? x0 + (x1 - x0) * i / (n - 1) : (x0 + x1) / 2; const k = prog(lt, 0.1 * d + (i / Math.max(1, n - 1)) * 0.7 * d, 0.1 * d + (i / Math.max(1, n - 1)) * 0.7 * d + 0.3); if (k <= 0) return;
    const up = i % 2 === 0; circle(x, y, 12 * U * spring(k), { fill: i === n - 1 ? HOTC : ACC, stroke: C.bg, sw: 4 });
    line(x, y + (up ? -20 : 20) * U, x, y + (up ? -70 : 70) * U, { col: C.line, sw: 2, a: k });
    const wf = F('mono', 24 * U, { w: 'bold' }); const lf = F('sans', fitPx(m.label || '', 'sans', Math.max(slot - 20 * U, 160 * U), 30 * U, 15 * U, { w: 'bold' }), { w: 'bold' });
    const ty = up ? y - 150 * U : y + 110 * U;
    txt(m.when || '', x, ty, { f: wf, col: ACC, align: 'center', a: k, ls: '2px' }); txt(m.label || '', x, ty + 42 * U, { f: lf, col: C.cream, align: 'center', a: k });
  });
  ctx.restore();
}, { exit: 0.9 });

// ---- logo: {path (SVG d), vb:[w,h], word, tagline, asset}
builtin('logo', (lt, d, p) => {
  const dp = eInOut(prog(lt, 0.05 * d, 0.55 * d)); const fp = M.in(prog(lt, 0.45 * d, 0.7 * d));
  const size = Math.min(W, H) * 0.34; const cx = W / 2, cy = H * (p.word ? 0.42 : 0.5);
  if (p.asset && IMG[p.asset]) drawImg(p.asset, cx - size / 2, cy - size / 2, size, size, { a: fp });
  else if (p.path) { const vb = p.vb || [100, 100]; const s = size / Math.max(vb[0], vb[1]); pathD(p.path, { x: cx - vb[0] * s / 2, y: cy - vb[1] * s / 2, s, p: dp, col: ACC, sw: 4, fill: C.cream, fillP: fp }); }
  if (p.word) { const wf = F('sans', fitPx(p.word, 'sans', CW(), 150 * U, 40 * U, { w: 'bold' }, '-4px'), { w: 'bold' }); const wy = cy + size * 0.62 + 60 * U;
    chars(p.word, W / 2, wy, { f: wf, col: C.cream, align: 'center', ls: '-4px' }, (i, n) => { const k = prog(lt, 0.5 * d + i * 0.03, 0.5 * d + i * 0.03 + 0.4); return { a: k, dy: (1 - M.in(k)) * 40 * U }; }); }
  if (p.tagline) txt(p.tagline, W / 2, cy + size * 0.62 + 150 * U, { f: F('serif', fitPx(p.tagline, 'serif', CW(), 48 * U, 20 * U, { i: true }), { i: true }), col: C.mute, align: 'center', a: M.in(prog(lt, 0.7 * d, 0.9 * d)) });
}, { exit: 1 });

// ---- ranking: {title, items:[[label, value]], fmt, highlight, unit}
builtin('ranking', (lt, d, p) => {
  const it = (p.items || []).slice().sort((a, b) => b[1] - a[1]); const n = it.length; const out = exitP(lt, d);
  ctx.save(); ctx.globalAlpha = 1 - out;
  if (p.title) txt(p.title, L0(), SAFE.t + 90 * U, { f: F('serif', fitPx(p.title, 'serif', CW(), 72 * U, 28 * U), { i: true }), col: C.cream, a: M.in(prog(lt, 0, 0.3)) });
  const top = SAFE.t + 160 * U, avail = H - top - SAFE.b - 20 * U; const bh = Math.min(76 * U, avail / n * 0.72), gap = Math.min(28 * U, avail / n * 0.28);
  const max = Math.max(...it.map(x => x[1]), 1); const lw = Math.min(CW() * 0.3, Math.max(...it.map(x => tw(x[0], F('sans', 30 * U, { w: 'bold' })))) + 30 * U);
  const bw = CW() - lw - 200 * U;
  it.forEach(([lab, val], i) => {
    const k = eOutCubic(prog(lt, 0.12 * d + i * 0.05 * d, 0.6 * d + i * 0.05 * d)); const y = top + i * (bh + gap);
    const hi = p.highlight != null ? lab === p.highlight : i === 0;
    txt(lab, L0() + lw - 20 * U, y + bh * 0.68, { f: F('sans', fitPx(lab, 'sans', lw - 30 * U, 30 * U, 14 * U, { w: 'bold' }), { w: 'bold' }), col: hi ? C.cream : C.text, align: 'right', a: prog(lt, 0.05 * d + i * 0.04 * d, 0.2 * d + i * 0.04 * d) });
    box(L0() + lw, y, Math.max(2, bw * val / max * k), bh, { fill: hi ? ACC : rgba(C.text, 0.18), stroke: null, r: Math.min(STYLE.radius, bh / 2) });
    txt(bigFmt(val * k, p.fmt || 'comma') + (p.unit ? ' ' + p.unit : ''), L0() + lw + bw * val / max * k + 16 * U, y + bh * 0.68, { f: F('mono', 28 * U, { w: 'bold' }), col: hi ? HOTC : C.mute, a: k > 0.02 ? 1 : 0 });
  });
  ctx.restore();
}, { exit: 0.9 });

// ---- route: {title, nodes:[{label, x, y}] (0..1), edges:[[a,b]], path:[i...], seed}
builtin('route', (lt, d, p) => {
  const nodes = p.nodes || []; const out = exitP(lt, d);
  ctx.save(); ctx.globalAlpha = 1 - out;
  if (p.title) txt(cap(p.title), L0(), SAFE.t + 70 * U, { f: F('mono', 24 * U, { w: 'bold' }), col: ACC, ls: '4px', a: M.in(prog(lt, 0, 0.3)) });
  const bx = L0() + 40 * U, by = SAFE.t + 130 * U, bw = CW() - 80 * U, bh = H - by - SAFE.b - 60 * U;
  const P = nd => [bx + nd.x * bw, by + nd.y * bh];
  (p.edges || []).forEach(([a, b], i) => { const k = eOutCubic(prog(lt, 0.05 * d + i * 0.02 * d, 0.35 * d + i * 0.02 * d)); const A_ = P(nodes[a]), B_ = P(nodes[b]); poly([A_, B_], k, { col: rgba(C.text, 0.25), sw: 2, dash: [6, 8] }); });
  const path = (p.path || []).map(i => P(nodes[i])); const pk = eInOut(prog(lt, 0.3 * d, 0.85 * d));
  let head = null; if (path.length > 1) { ctx.save(); if (GLOW) { ctx.shadowColor = ACC; ctx.shadowBlur = 16 * DPR * GLOW; } head = poly(path, pk, { col: ACC, sw: 5 }); ctx.restore(); }
  nodes.forEach((nd, i) => { const [x, y] = P(nd); const k = spring(prog(lt, 0.05 * d + i * 0.03 * d, 0.3 * d + i * 0.03 * d)); const onPath = (p.path || []).includes(i);
    circle(x, y, (onPath ? 13 : 9) * U * k, { fill: onPath ? ACC : C.surf, stroke: onPath ? C.cream : C.line, sw: 3 });
    txt(nd.label || '', x, y - 26 * U, { f: F('sans', 22 * U, { w: onPath ? 'bold' : undefined }), col: onPath ? C.cream : C.mute, align: 'center', a: k }); });
  if (head && pk < 1) circle(head[0], head[1], 12 * U, { fill: HOTC, stroke: '#ffffff', sw: 3 });
  ctx.restore();
}, { exit: 0.9 });
