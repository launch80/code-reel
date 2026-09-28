// code-reel engine · scenes.js — BLUEPRINT scene library.
// These are reference implementations and reusable building blocks, not the
// default output: a final reel is mostly scenes written for THAT video
// (project scenes/*.js via defineScene). Every blueprint here:
//   · is responsive (lays out from W/H/SAFE/U, works at 16:9, 9:16, 1:1)
//   · takes fonts/colors/motion from the style pack (F(), C, M, GLOW)
//   · has no brand defaults — every visible string comes from params
'use strict';

const wide = () => W / H > 1.2;
const L0 = () => SAFE.l;                       // left margin
const CW = () => W - SAFE.l - SAFE.r;          // content width

// ---- terminal: {prompt, cmd, title, rows:[[label,value]], progress:{label,pct}, ok}
builtin('terminal', (lt, d, p) => {
  const ap = M.in(prog(lt, 0, 0.23 * d)), ex = exitP(lt, d, 0.86, 1.0);
  const rows = p.rows || []; const fs = 34 * U, rs = 30 * U, rh = 54 * U;
  const pw = Math.min(1180 * U, CW()), ph = 170 * U + rows.length * rh + (p.progress ? 90 * U : 20 * U);
  const px = (W - pw) / 2, py = (H - ph) / 2 - 10;
  const prompt = p.prompt || '$';
  ctx.save(); ctx.translate(W / 2, H / 2); const s = lerp(0.94, 1, ap) + ex * 0.35; ctx.scale(s, s); ctx.translate(-W / 2, -H / 2); ctx.globalAlpha = ap * (1 - ex);
  ctx.save(); if (GLOW) { ctx.shadowColor = A(0.55); ctx.shadowBlur = 40 * DPR * GLOW; }
  rrect(px, py, pw, ph, STYLE.radius + 2); ctx.fillStyle = rgba(C.surf, 0.96); ctx.fill(); ctx.restore();
  rrect(px, py, pw, ph, STYLE.radius + 2); ctx.strokeStyle = A(0.8); ctx.lineWidth = 2; ctx.stroke();
  rect(px, py + 62 * U, pw, 1, C.line);
  ['#ff5f56', C.line, C.line].forEach((c, i) => circle(px + 36 * U + i * 30 * U, py + 31 * U, 9 * U, { fill: c }));
  txt(prompt, px + 150 * U, py + 40 * U, { f: F('mono', 24 * U, { w: 'bold' }), col: C.text });
  if (p.title) txt(p.title, px + pw - 30 * U, py + 40 * U, { f: F('mono', 20 * U), col: C.mute, align: 'right' });
  const Lx = px + 50 * U; const y = py + 140 * U; const Fm = F('mono', fs);
  txt(prompt, Lx, y, { f: Fm, col: ACC });
  const cmd = typed(p.cmd || '', lt, 0.12 * d, 0.48 * d);
  txt(cmd, Lx + tw(prompt + ' ', Fm), y, { f: Fm, col: C.cream });
  if (lt < 0.53 * d) cursor(Lx + tw(prompt + ' ' + cmd, Fm) + 4, y + 4, lt, 36 * U, 18 * U);
  const ok = p.ok || '[ok]'; const okw = tw(ok + ' ', F('mono', rs, { w: 'bold' }));
  const labW = Math.max(...rows.map(r => tw(r[0], F('mono', rs))), 0);
  rows.forEach((r, i) => { const a = prog(lt, 0.52 * d + i * 0.053 * d, 0.56 * d + i * 0.053 * d); if (!a) return; const yy = y + 66 * U + i * rh;
    txt(ok, Lx, yy, { f: F('mono', rs, { w: 'bold' }), col: ACC, a }); txt(r[0], Lx + okw, yy, { f: F('mono', rs), col: C.text, a });
    txt(r[1], Lx + okw + labW + 40 * U, yy, { f: F('mono', rs), col: C.mute, a }); });
  if (p.progress) { const bp = prog(lt, 0.72 * d, 0.90 * d); const yy = y + 66 * U + rows.length * rh + 18 * U;
    const lab = p.progress.label || ''; const lw = tw(lab + '  ', F('mono', rs));
    txt(lab, Lx, yy, { f: F('mono', rs), col: C.text });
    const bx = Lx + lw, bw = pw - 100 * U - lw - 120 * U; rect(bx, yy - 22 * U, bw, 24 * U, C.line); rect(bx, yy - 22 * U, bw * eOutCubic(bp), 24 * U, ACC);
    txt(Math.round(bp * (p.progress.pct ?? 100)) + '%', bx + bw + 24 * U, yy, { f: F('mono', rs, { w: 'bold' }), col: C.cream }); }
  ctx.restore();
}, { exit: 0.86 });

// ---- kinetic: {intro, words:[[text, offset, color?, note?, val?]]}  (offset = seconds into scene)
builtin('kinetic', (lt, d, p) => {
  const out = exitP(lt, d);
  ctx.save(); ctx.translate(-out * 260 * U, 0); ctx.globalAlpha = 1 - out;
  const words = (p.words || []).map(w => (w.length === 4 && typeof w[2] === 'string' && w[2] !== 'ACCENT' && w[2] !== '' && !w[2].startsWith('#') && !w[2].startsWith('rgb')) ? [w[0], w[1], '', w[2], w[3]] : w);
  const hasNotes = words.some(w => w[3] || w[4]);
  const colX = wide() && hasNotes ? W * 0.69 : null;
  const maxW = (colX ? colX - 80 * U : W - SAFE.r) - L0();
  const px = Math.min(...words.map(w => fitPx(w[0], 'disp', maxW, 190 * U, 60 * U)));
  const Fw = F('disp', px); const noteBelow = !colX && hasNotes;
  const rowH = px * 1.12 + (noteBelow ? 100 * U : 0);
  const introH = p.intro ? 140 * U : 0;
  const blockH = introH + rowH * words.length;
  let y0 = Math.max(SAFE.t + introH, (H - blockH) / 2 + introH) + px * 0.85;
  if (p.intro) {
    const ip = M.in(prog(lt, 0.008 * d, 0.18 * d)); const ipx = fitPx(p.intro, 'serif', CW(), 76 * U, 30 * U, { i: true });
    wipeLine(p.intro, L0(), y0 - px * 0.85 - 60 * U, CW(), ip, { f: F('serif', ipx, { i: true }), col: C.mute });
    rect(L0(), y0 - px * 0.85 - 30 * U, 420 * U * ip, 3, ACC);
  }
  words.forEach(([w, off, col, note, val], i) => {
    const st = off != null ? off : 0.2 * d + i * 0.2 * d;
    const colr = col === 'ACCENT' ? ACC : (col || C.cream);
    const pr = prog(lt, st - 0.02, st + 0.22); if (pr <= 0) return;
    const e = M.in(pr); const sc = lerp(1.9, 1, e); const y = y0 + i * rowH; const x = L0();
    ctx.save(); ctx.translate(x, y); ctx.scale(sc, sc);
    const g = (1 - e) * 40;
    if (GLOW) txt(w, -g, 0, { f: Fw, col: A(0.55), a: clamp(pr * 3) * (1 - e) });
    txt(w, 0, 0, { f: Fw, col: colr, a: clamp(pr * 3), glow: i === words.length - 1 ? 50 : 0 });
    ctx.restore();
    const ap = M.in(prog(lt, st + 0.12, st + 0.45));
    const nf = F('mono', 24 * U), vf = F('mono', 52 * U, { w: 'bold' }); const vcol = i === words.length - 1 ? HOTC : C.cream;
    if (colX) {
      const wEnd = x + tw(w, Fw);
      if (note || val) dashed(wEnd + 30 * U, y - px * 0.38, colX - 30 * U, y - px * 0.38, ap);
      txt(cap(note || ''), colX, y - px * 0.52, { f: nf, col: C.mute, a: ap, ls: '3px' });
      txt(val || '', colX, y - px * 0.52 + 60 * U, { f: vf, col: vcol, a: ap });
    } else if (note || val) {
      txt(cap(note || ''), x, y + 40 * U, { f: nf, col: C.mute, a: ap, ls: '3px' });
      txt(val || '', x + tw(cap(note || '') + '   ', nf, '3px'), y + 40 * U, { f: F('mono', 30 * U, { w: 'bold' }), col: vcol, a: ap });
    }
  });
  ctx.restore();
}, { exit: 0.88 });

// ---- cards: {header, kicker, cards:[{tag, big:{from,to,fmt}, unit, sub, label, viz, vizFrom, vizTo}], ticker:{label, items}}
builtin('cards', (lt, d, p) => {
  const hp = M.in(prog(lt, 0, 0.17 * d)); const fade = 1 - exitP(lt, d, 0.9, 0.98);
  const top = SAFE.t + 70 * U;
  txt(cap(p.header || ''), L0(), top, { f: F('mono', 24 * U, { w: 'bold' }), col: ACC, a: hp * fade, ls: '3px' });
  const kpx = fitPx(p.kicker || '', 'serif', CW(), 88 * U, 36 * U);
  clipRect(L0() - 10, top + 10, CW() + 20, kpx * 1.3, () =>
    txt(p.kicker || '', L0(), lerp(top + kpx * 2.2, top + kpx * 1.05, hp), { f: F('serif', kpx), col: C.cream, a: fade }));
  const cards = p.cards || []; const n = Math.max(1, cards.length); const gap = 30 * U;
  const hasTicker = p.ticker && (p.ticker.items || []).length;
  const areaT = top + kpx * 1.6, areaB = H - SAFE.b - (hasTicker ? 70 * U : 0);
  const horiz = wide();
  const cw = horiz ? (CW() - (n - 1) * gap) / n : CW();
  const ch = horiz ? Math.min(520 * U, areaB - areaT) : Math.min(420 * U, (areaB - areaT - (n - 1) * gap) / n);
  cards.forEach((c, i) => {
    const st = 0.05 * d + i * 0.047 * d; const pr = M.in(prog(lt, st, st + 0.6)); const o = SELF_EXIT ? M.out(prog(lt, 0.88 * d + i * 0.02 * d, 0.98 * d)) : 0;
    if (pr <= 0) return;
    const x = horiz ? L0() + i * (cw + gap) : L0(), yb = horiz ? areaT : areaT + i * (ch + gap);
    const y = yb + lerp(120 * U, 0, pr) + o * 140 * U;
    ctx.save(); ctx.globalAlpha = pr * (1 - o);
    box(x, y, cw, ch, { fill: rgba(C.surf, 0.94), stroke: C.line });
    rect(x, y, cw * M.in(prog(lt, st + 0.2, st + 0.9)), 4, ACC);
    const pad = 32 * U; const k = ch / 520;
    txt(cap(c.tag || ''), x + pad, y + 62 * k, { f: F('mono', 22 * U, { w: 'bold' }), col: ACC, ls: '2px' });
    const v = eOutCubic(prog(lt, st + 0.25, st + 1.5));
    const bf = c.big || { from: 0, to: 0, fmt: 'int' };
    const UF = F('mono', 30 * U, { w: 'bold' }); const fin = bigFmt(+bf.to, bf.fmt);
    const bs = Math.min(136 * U, ch * 0.26, fitPx(fin, 'disp', cw - 2 * pad - tw(c.unit || '', UF) - 16 * U, 136 * U, 40 * U));
    const bigS = countTo(bf, v);
    txt(bigS, x + pad, y + 215 * k, { f: F('disp', bs), col: C.cream, glow: v >= 1 ? 18 : 0, gcol: A(0.8) });
    txt(c.unit || '', x + pad + 8 * U + tw(bigS, F('disp', bs)), y + 215 * k, { f: UF, col: C.mute });
    const sf = F('mono', Math.min(22 * U, fitPx(c.sub || '', 'mono', cw - 2 * pad, 22 * U, 14 * U)));
    txt(c.sub || '', x + pad, y + 262 * k, { f: sf, col: C.mute });
    const vx = x + pad, vy = y + 300 * k, vw = cw - 2 * pad, vh = 70 * k;
    const grow = eOutCubic(prog(lt, st + 0.2, st + 0.7));
    if (c.viz === 'bars') {
      const mx = Math.max(Math.abs(bf.from), Math.abs(bf.to), 1); const r0 = bf.from / mx, r1 = bf.to / mx; const lf = F('mono', 18 * U);
      txt(c.vizFrom || 'before', vx, vy + 22 * k, { f: lf, col: C.mute }); rect(vx + 100 * U, vy + 6 * k, (vw - 100 * U) * r0 * grow, 20 * k, C.line);
      txt(c.vizTo || 'after', vx, vy + 66 * k, { f: lf, col: C.cream }); rect(vx + 100 * U, vy + 50 * k, (vw - 100 * U) * lerp(r0, r1, v) * grow, 20 * k, ACC);
    } else if (c.viz === 'kv') {
      box(vx, vy, vw, vh, { fill: C.bg, stroke: C.line, r: 4 });
      const ratio = bf.to ? bf.from / bf.to : 1; const cur = vw / lerp(1, ratio > 0 ? 1 / ratio : 1, v);
      for (let q = 0; q < Math.floor(cur / 14); q++) rect(vx + q * 14 + 2, vy + 6, 10, vh - 12, ACC, 0.9);
      txt(c.vizTo || '', vx + vw - 8, vy + vh + 30 * k, { f: F('mono', 18 * U), col: C.mute, align: 'right' }); txt(c.vizFrom || '', vx, vy + vh + 30 * k, { f: F('mono', 18 * U), col: HOTC });
    } else if (c.viz === 'ctx') {
      const nn = 48; for (let q = 0; q < nn; q++) { const on = q / nn < v; rect(vx + q * (vw / nn), vy + 10, vw / nn - 3, vh - 20, on ? ACC : C.line, on ? lerp(0.35, 1, q / nn) : 1); }
      txt('0', vx, vy + vh + 30 * k, { f: F('mono', 18 * U), col: C.mute }); txt(c.vizTo || fin, vx + vw, vy + vh + 30 * k, { f: F('mono', 18 * U), col: HOTC, align: 'right' });
    }
    txt(c.label || '', x + pad, y + ch - 40 * k, { f: F('sans', Math.min(26 * U, fitPx(c.label || '', 'sans', cw - 2 * pad, 26 * U, 14 * U))), col: C.text });
    ctx.restore();
  });
  if (hasTicker) {
    const tk = p.ticker.items.join('    ') + '    '; const ty = H - SAFE.b - 20 * U;
    const ta = prog(lt, 0.1 * d, 0.23 * d) * fade; const Ft = F('mono', 22 * U); const w = tw(tk, Ft); const off = (lt * 260) % w;
    ctx.save(); ctx.globalAlpha = ta; rect(0, ty - 31 * U, W, 1, C.line); rect(0, ty + 15 * U, W, 1, C.line);
    const lab = cap(p.ticker.label || ''); const lw = lab ? tw(lab, F('mono', 20 * U, { w: 'bold' }), '2px') + 40 * U : 0;
    clipRect(L0() + lw, ty - 40 * U, CW() - lw, 60 * U, () => { for (let q = -1; q < 3; q++) txt(tk, L0() + lw - off + q * w, ty, { f: Ft, col: C.mute }); });
    if (lab) txt(lab, L0(), ty, { f: F('mono', 20 * U, { w: 'bold' }), col: ACC, ls: '2px' });
    ctx.restore();
  }
}, { exit: 0.88 });

// ---- counter: {prompt, promptArg, kicker, big:{from,to,fmt}, unit, sub, tagline, typing, scope:[0..1 values]}
builtin('counter', (lt, d, p) => {
  const out = exitP(lt, d, 0.9, 1.0);
  ctx.save(); ctx.globalAlpha = 1 - out;
  const scope = p.scope || []; const dp = eOutCubic(prog(lt, 0.1, 0.53 * d));
  if (scope.length > 1) {
    const gy = H * 0.83, gh = H * 0.48; const pts = [];
    scope.forEach((yy, i) => { const fr = i / (scope.length - 1); if (fr <= dp) pts.push([fr * W, gy - clamp(yy) * gh]); });
    ctx.save(); if (GLOW) { ctx.shadowColor = ACC; ctx.shadowBlur = 20 * DPR * GLOW; } poly(pts, 1, { col: A(0.45), sw: 3 }); ctx.restore();
    const e = pts[pts.length - 1]; if (e) circle(e[0], e[1], 7, { fill: HOTC });
  }
  let y = SAFE.t + 80 * U;
  if (p.prompt || p.promptArg) { const Fp = F('mono', 30 * U); txt(p.prompt || '$', L0(), y, { f: Fp, col: ACC });
    txt(typed(p.promptArg || '', lt, 0.05, 0.4), L0() + tw((p.prompt || '$') + ' ', Fp), y, { f: Fp, col: C.mute }); y += 90 * U; }
  const hp = M.in(prog(lt, 0.15, 0.5));
  if (p.kicker) txt(p.kicker, L0(), y, { f: F('serif', fitPx(p.kicker, 'serif', CW(), 64 * U, 28 * U, { i: true }), { i: true }), col: C.cream, a: hp });
  const bf = p.big || { from: 0, to: 0, fmt: 'int' };
  const v = eOutExpo(prog(lt, 0.3, 1.5)); const nS = countTo(bf, v); const fin = bigFmt(+bf.to, bf.fmt);   // counters never use springy easing: they must land exactly const fin = bigFmt(+bf.to, bf.fmt);
  const UF = F('mono', 84 * U, { w: 'bold' }); const unitW = Math.max(tw(p.unit || '', UF), tw(cap(p.sub || ''), F('mono', 34 * U, { w: 'bold' }), '6px'));
  const side = wide() && unitW + 60 * U < CW() * 0.45;
  const bpx = fitPx(fin, 'disp', side ? CW() - unitW - 60 * U : CW(), 440 * U, 80 * U); const BF = F('disp', bpx);
  const by = side ? H * 0.667 : H * 0.55; const sp = M.in(prog(lt, 0.25, 0.55));
  ctx.save(); ctx.translate(L0(), by); ctx.scale(lerp(1.25, 1, sp), lerp(1.25, 1, sp));
  const gr = ctx.createLinearGradient(0, -bpx * 0.75, 0, 0); gr.addColorStop(0, HOTC); gr.addColorStop(1, rgba(ACC, 0.9));
  txt(nS, 0, 0, { f: BF, col: gr, a: sp, glow: 60, gcol: A(0.7) }); ctx.restore();
  const up = M.in(prog(lt, 0.6, 1.0));
  const ux = side ? L0() + tw(fin, BF) + 40 * U : L0(), uy = side ? by - bpx * 0.36 : by + 110 * U;
  txt(p.unit || '', ux, uy, { f: UF, col: C.cream, a: up });
  txt(cap(p.sub || ''), ux, uy + 70 * U, { f: F('mono', 34 * U, { w: 'bold' }), col: C.mute, a: up, ls: '6px' });
  const wp = M.in(prog(lt, 1.0, 1.5)); const tgy = side ? H * 0.78 : uy + 190 * U;
  if (p.tagline) { const tf = F('mono', fitPx(cap(p.tagline), 'mono', CW(), 44 * U, 20 * U, { w: 'bold' }, '4px'), { w: 'bold' });
    wipeLine(cap(p.tagline), L0(), tgy, CW(), wp, { f: tf, col: C.cream, ls: '4px' }); rect(L0(), tgy + 22 * U, Math.min(900 * U, CW()) * wp, 3, ACC); }
  if (p.typing) { const Ft = F('mono', fitPx(p.typing, 'mono', CW() - 30, 28 * U, 16 * U)); const ms = typed(p.typing, lt, 0.53 * d, 0.78 * d);
    const ty = Math.min(H - SAFE.b - 10, tgy + 100 * U); txt(ms, L0(), ty, { f: Ft, col: C.mute });
    if (lt > 0.51 * d && lt < 0.9 * d) cursor(L0() + 4 + tw(ms, Ft), ty + 4, lt, 30 * U, 14 * U); }
  ctx.restore();
}, { exit: 0.9 });

// ---- chart: {line, grow:[values], months:[labels], label, sub, max, impact, seed, fmt}
builtin('chart', (lt, d, p) => {
  const grow = p.grow || [0, 1], months = p.months || []; const max = p.max || Math.max(...grow) || 1;
  const impact = p.impact != null ? p.impact : 0.72 * d;
  const growth = x => { const n = grow.length - 1; const i = Math.min(n - 1, Math.floor(x * n)); const f = x * n - i; return lerp(grow[i], grow[i + 1], f); };
  const out = exitP(lt, d); ctx.save(); ctx.globalAlpha = 1 - out; ctx.translate(0, -out * 60 * U);
  const hp = M.in(prog(lt, 0, 0.45)); const top = SAFE.t + 90 * U;
  const lpx = fitPx(p.line || '', 'serif', CW(), 76 * U, 30 * U, { i: true });
  if (p.line) wipeLine(p.line, L0(), top, CW(), hp, { f: F('serif', lpx, { i: true }), col: C.cream });
  const v = eOutCubic(prog(lt, 0.2, impact)); const val = growth(v);
  const hit = prog(lt, impact, impact + 0.3); const pop = 1 + 0.12 * Math.sin(Math.PI * clamp(hit)) * (1 - hit);
  const horiz = wide();
  const leftW = horiz ? CW() * 0.52 : CW();
  const fin = bigFmt(Math.max(...grow), p.fmt || 'comma');
  const npx = fitPx(fin, 'disp', leftW, 250 * U, 60 * U);
  const ny = horiz ? H * 0.52 : top + npx * 1.2;
  ctx.save(); ctx.translate(L0(), ny); ctx.scale(pop, pop);
  txt(bigFmt(val, p.fmt || 'comma'), 0, 0, { f: F('disp', npx), col: ACC, glow: lt > impact ? 70 : 25, gcol: A(0.8) }); ctx.restore();
  const lbpx = fitPx(p.label || '', 'disp', leftW, 150 * U, 40 * U);
  txt(p.label || '', L0(), ny + lbpx * 1.07, { f: F('disp', lbpx), col: C.cream, a: M.in(prog(lt, 0.25, 0.6)) });
  txt(cap(p.sub || ''), L0() + 4, ny + lbpx * 1.07 + 80 * U, { f: F('mono', fitPx(cap(p.sub || ''), 'mono', leftW, 30 * U, 14 * U, { w: 'bold' }, '8px'), { w: 'bold' }), col: C.mute, a: M.in(prog(lt, 0.45, 0.8)), ls: '8px' });
  // chart box
  const cx = horiz ? L0() + CW() * 0.6 : L0(), cw = horiz ? CW() * 0.36 : CW() - 80 * U;
  const cyb = horiz ? H * 0.74 : H - SAFE.b - 80 * U, chh = horiz ? H * 0.43 : Math.min(H * 0.3, cyb - (ny + lbpx + 200 * U));
  const ca = M.in(prog(lt, 0.1, 0.5));
  ctx.save(); ctx.globalAlpha *= ca;
  for (let k = 0; k <= 4; k++) { rect(cx, cyb - k * chh / 4, cw, 1, C.line); txt(fmt(k * max / 4), cx + cw + 16 * U, cyb - k * chh / 4 + 6, { f: F('mono', 18 * U), col: C.mute }); }
  months.forEach((m, i) => txt(m, cx + i * cw / Math.max(1, months.length - 1), cyb + 36 * U, { f: F('mono', 18 * U), col: i === months.length - 1 ? HOTC : C.mute, align: 'center' }));
  const pts = []; const N = 100; for (let i = 0; i <= N; i++) { const xx = i / N * v; pts.push([cx + xx * cw, cyb - growth(xx) / max * chh]); }
  const e = pts[pts.length - 1];
  ctx.save(); ctx.beginPath(); pts.forEach(([X, Y], i) => i ? ctx.lineTo(X, Y) : ctx.moveTo(X, Y)); ctx.lineTo(e[0], cyb); ctx.lineTo(cx, cyb); ctx.closePath();
  const ag = ctx.createLinearGradient(0, cyb - chh, 0, cyb); ag.addColorStop(0, A(0.35)); ag.addColorStop(1, A(0)); ctx.fillStyle = ag; ctx.fill(); ctx.restore();
  ctx.save(); if (GLOW) { ctx.shadowColor = ACC; ctx.shadowBlur = 18 * DPR * GLOW; } poly(pts, 1, { col: ACC, sw: 4 }); ctx.restore();
  const pr = (lt * 2) % 1; circle(e[0], e[1], 8 + pr * 28, { stroke: Hh(1 - pr), sw: 2 }); circle(e[0], e[1], 8, { fill: C.cream });
  ctx.restore();
  if (lt > impact) {   // burst — seeded from p.seed so it's stable and varies per reel
    const r = rng(p.seed || 1); const pt = lt - impact; const al = 1 - clamp(pt / 0.6);
    if (al > 0) for (let i = 0; i < 140; i++) { const a = r() * Math.PI * 2, s = (300 + r() * 1100) * U, z = r() * 3 + 1, ox = L0() + r() * leftW * 0.8;
      const dd = s * eOutCubic(clamp(pt / 0.7)); rect(ox + Math.cos(a) * dd, ny - npx * 0.36 + Math.sin(a) * dd * 0.6, z * 2, z * 2, HOTC, al); }
  }
  ctx.restore();
}, { exit: 0.88 });

// ---- quote: {tag, text, author, handle, slam}
builtin('quote', (lt, d, p) => {
  const slam = p.slam != null ? p.slam : 0.4 * d; const out = exitP(lt, d);
  ctx.save(); ctx.translate(0, out * 120 * U); ctx.globalAlpha = 1 - out;
  const hp = M.in(prog(lt, 0.05 * d, 0.25 * d)); const top = SAFE.t + 70 * U;
  if (p.tag) txt(cap(p.tag), L0(), top, { f: F('mono', 24 * U, { w: 'bold' }), col: ACC, a: hp, ls: '3px' });
  const hit = prog(lt, slam, slam + 0.25); const pop = 1 + 0.06 * Math.sin(Math.PI * clamp(hit)) * (1 - hit);
  let qpx = 96 * U, lines; do { lines = wrap(p.text || '', F('serif', qpx, { i: true }), CW()); if (lines.length <= 4) break; qpx *= 0.9; } while (qpx > 30 * U);
  const QF = F('serif', qpx, { i: true }); const lh = qpx * 1.22;
  const blockH = lines.length * lh; let qy = Math.max(top + qpx * 1.5, (H - blockH) / 2);
  const words = []; lines.forEach((ln, li) => { let x = L0(); ln.split(' ').forEach(w => { words.push([w, x, qy + li * lh]); x += tw(w + ' ', QF); }); });
  ctx.save(); ctx.translate(L0(), qy); ctx.scale(pop, pop); ctx.translate(-L0(), -qy);
  words.forEach(([w, x, y], i) => { const a = prog(lt, 0.15 * d + i * (0.4 * d / words.length), 0.2 * d + i * (0.4 * d / words.length) + 0.1); txt(w, x, y, { f: QF, col: C.cream, a }); });
  ctx.restore();
  const ay = qy + blockH + 40 * U; const ap = M.in(prog(lt, slam + 0.1, slam + 0.5));
  rect(L0(), ay, Math.min(1100 * U, CW()) * ap, 2, ACC);
  txt(p.author || '', L0(), ay + 80 * U, { f: F('mono', 40 * U, { w: 'bold' }), col: C.cream, a: ap });
  txt(p.handle || '', L0() + tw(p.author || '', F('mono', 40 * U, { w: 'bold' })) + 24 * U, ay + 80 * U, { f: F('mono', 32 * U), col: C.mute, a: ap });
  ctx.restore();
}, { exit: 0.88, slams: ['slam'] });

// ---- split: {title, left:{label, badge, items:[[label,value]], winner}, right:{...}}
builtin('split', (lt, d, p) => {
  const Lc = p.left || {}, Rc = p.right || {}; const out = exitP(lt, d);
  ctx.save(); ctx.globalAlpha = 1 - out;
  const hp = M.in(prog(lt, 0.05 * d, 0.3 * d)); const top = SAFE.t + 80 * U; const horiz = wide();
  txt(cap(p.title || ''), W / 2, top, { f: F('mono', fitPx(cap(p.title || ''), 'mono', CW(), 30 * U, 16 * U, { w: 'bold' }, '6px'), { w: 'bold' }), col: ACC, a: hp, align: 'center', ls: '6px' });
  const dv = M.in(prog(lt, 0.2 * d, 0.45 * d));
  if (horiz) { line(W / 2, top + 100 * U, W / 2, lerp(top + 100 * U, H - SAFE.b - 40 * U, dv), { col: A(0.6), sw: 2, dash: [8, 10] });
    txt(p.vs ?? 'VS', W / 2, top + 140 * U, { f: F('mono', 28 * U, { w: 'bold' }), col: C.mute, a: dv, align: 'center', ls: '4px' }); }
  const colW = horiz ? (CW() - 120 * U) / 2 : CW();
  const colFn = (c, side) => {
    const win = c.winner; const e = M.in(prog(lt, 0.15 * d, 0.45 * d)); const items = c.items || [];
    const x = horiz ? (side === 'L' ? L0() : W / 2 + 60 * U) : L0();
    const colH = 110 * U + items.length * 74 * U; const y0 = horiz ? top + 190 * U : (side === 'L' ? top + 80 * U : top + 120 * U + colH);
    ctx.save(); ctx.translate((side === 'L' ? -1 : 1) * (1 - e) * 160 * U, 0); ctx.globalAlpha *= e;
    box(x, y0, colW, 86 * U, { fill: win ? A(0.12) : rgba(C.surf, 0.94), stroke: win ? A(0.7) : C.line, r: STYLE.radius });
    txt(cap(c.label || ''), x + 28 * U, y0 + 56 * U, { f: F('mono', fitPx(cap(c.label || ''), 'mono', colW * 0.62, 34 * U, 16 * U, { w: 'bold' }, '3px'), { w: 'bold' }), col: win ? ACC : C.cream, ls: '3px' });
    if (c.badge) txt(cap(c.badge), x + colW - 28 * U, y0 + 56 * U, { f: F('mono', 22 * U), col: C.mute, align: 'right', ls: '2px' });
    items.forEach((it, i) => { const ia = prog(lt, 0.35 * d + i * 0.07 * d, 0.45 * d + i * 0.07 * d); if (!ia) return; const y = y0 + 150 * U + i * 74 * U;
      ctx.save(); ctx.globalAlpha *= ia;
      if (win) poly([[x + 6, y - 12 * U], [x + 16 * U, y - 2 * U], [x + 34 * U, y - 22 * U]], 1, { col: ACC, sw: 3 });
      else { line(x + 8 * U, y - 22 * U, x + 30 * U, y - 2 * U, { col: C.mute, sw: 3 }); line(x + 30 * U, y - 22 * U, x + 8 * U, y - 2 * U, { col: C.mute, sw: 3 }); }
      const vf = F('mono', 28 * U, { w: 'bold' }); const vw = tw(it[1] || '', vf);
      txt(it[0], x + 58 * U, y, { f: F('sans', fitPx(it[0], 'sans', colW - 90 * U - vw - 40 * U, 28 * U, 14 * U)), col: C.text });
      txt(it[1] || '', x + colW - 28 * U, y, { f: vf, col: win ? HOTC : C.mute, align: 'right' }); ctx.restore(); });
    ctx.restore();
  };
  colFn(Lc, 'L'); colFn(Rc, 'R'); ctx.restore();
}, { exit: 0.88 });

// ---- endcard: {tag, word1, word2, serif, url, footer}
builtin('endcard', (lt, d, p) => {
  const hp = M.in(prog(lt, 0.14 * d, 0.32 * d));
  const w1 = p.word1 || '', w2 = p.word2 || '';
  const wpx = fitPx(w1 + w2, 'sans', CW(), 250 * U, 60 * U, { w: 'bold' }, '-8px'); const WF = F('sans', wpx, { w: 'bold' });
  const w1w = tw(w1, WF, '-8px'), w2w = tw(w2, WF, '-8px'); const tot = w1w + w2w; const x0 = W / 2 - tot / 2, y0 = H * 0.555;
  if (p.tag) txt(cap(p.tag), W / 2, y0 - wpx * 0.88, { f: F('mono', fitPx(cap(p.tag), 'mono', CW(), 24 * U, 12 * U, {}, '5px')), col: C.mute, align: 'center', ls: '5px', a: hp });
  const wp = eInOut(prog(lt, 0, 0.55));
  if (wp > 0) clipRect(x0 - 20, y0 - wpx * 1.05, (tot + 40) * wp, wpx * 1.3, () => {
    txt(w1, x0, y0, { f: WF, col: C.cream, ls: '-8px' }); txt(w2, x0 + w1w, y0, { f: WF, col: ACC, ls: '-8px', glow: lt > 0.5 ? 50 : 0, gcol: A(0.9) }); });
  if (wp > 0 && wp < 1) { const sx = x0 - 20 + (tot + 40) * wp; ctx.save(); if (GLOW) { ctx.shadowColor = HOTC; ctx.shadowBlur = 40 * DPR * GLOW; } rect(sx - 3, y0 - wpx, 6, wpx * 1.2, HOTC); ctx.restore(); }
  const sa = M.in(prog(lt, 0.55, 1.0));
  if (p.serif) txt(p.serif, W / 2, lerp(y0 + wpx * 0.56, y0 + wpx * 0.45, sa), { f: F('serif', fitPx(p.serif, 'serif', CW(), 84 * U, 30 * U, { i: true }), { i: true }), col: C.cream, align: 'center', a: sa });
  if (p.url) { const ua = M.in(prog(lt, 0.85, 1.2)); const UF = F('mono', fitPx('→ ' + p.url, 'mono', CW(), 36 * U, 16 * U, { w: 'bold' }), { w: 'bold' });
    const us = '→ ' + typed(p.url, lt, 0.9, 1.35); const ux = W / 2 - tw('→ ' + p.url, UF) / 2; const uy = y0 + wpx * 0.92;
    txt(us, ux, uy, { f: UF, col: ACC, a: ua }); if (lt > 0.85) cursor(ux + tw(us, UF) + 6, uy + 4, lt, 36 * U, 16 * U); }
  rect(W / 2 - 300 * U * hp, y0 + wpx * 1.08, 600 * U * hp, 1, C.line);
  if (p.footer) txt(cap(p.footer), W / 2, y0 + wpx * 1.25, { f: F('mono', fitPx(cap(p.footer), 'mono', CW(), 20 * U, 11 * U, {}, '6px')), col: C.mute, align: 'center', ls: '6px', a: M.in(prog(lt, 1.2, 1.6)) });
}, { exit: 1 });
