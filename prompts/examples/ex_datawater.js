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
