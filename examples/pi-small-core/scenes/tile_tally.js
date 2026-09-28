/* @meta {"name": "tile_tally", "required": ["cells", "cells_label", "side"], "text": ["cells_label", "side", "source"], "ticks": [{"a": 0.2, "b": "0.62d"}]} */
// The parts bin: one tile per extension example rains into a grid; two side tallies stack their own tiles.
defineScene('tile_tally', (lt, d, p) => {
  const n = Math.round(+p.cells || 0); const cols = 17, rows = Math.ceil(n / cols);
  const gw = W * 0.58, cs = gw / cols, gx = SAFE.l, gy = H * 0.30;
  const fillEnd = 0.62 * d;
  let landed = 0;
  for (let k = 0; k < n; k++) {
    const t0 = 0.2 + (k / n) * (fillEnd - 0.4); const s = prog(lt, t0, t0 + 0.35); if (s <= 0) continue;
    const x = gx + (k % cols) * cs, yEnd = gy + Math.floor(k / cols) * cs, y = lerp(-cs, yEnd, eOutBack(s));
    if (s >= 1) landed++;
    box(x + 3 * U, y + 3 * U, cs - 6 * U, cs - 6 * U, { fill: k === n - 1 && s >= 1 ? HOTC : ACC, stroke: null, r: 0, a: 0.35 + 0.65 * s });
  }
  // counter follows the tiles that have actually landed
  const words = String(p.cells_label).replace(/^\s*\d[\d,]*\s*/, '');
  const nf = F('disp', 150 * U), yb = gy + rows * cs + 170 * U;
  txt(String(landed), gx, yb, { f: nf, col: C.cream });
  txt(words, gx + tw(String(n), nf) + 30 * U, yb, { f: F('sans', 44 * U, { w: 'bold' }), col: C.cream, a: prog(lt, 0.4, 0.9) });
  // side tallies: stacked tile columns
  const side = p.side || []; const sx0 = W * 0.70, colW = (W - SAFE.r - sx0) / Math.max(1, side.length);
  side.forEach((s_, i) => {
    const v = +s_.value || 0; const e = eOutCubic(prog(lt, 0.6 + i * 0.25, fillEnd + 0.4)); const shown = Math.round(v * e);
    const x = sx0 + i * colW, baseY = gy + rows * cs; const per = 10, tsz = Math.min(18 * U, colW / per - 2 * U);
    for (let k = 0; k < shown; k++) rect(x + (k % per) * (tsz + 2 * U), baseY - Math.floor(k / per) * (tsz + 2 * U) - tsz, tsz, tsz, rgba(C.text, 0.75));
    txt(String(shown), x, baseY + 70 * U, { f: F('disp', 64 * U), col: C.cream, a: e > 0 ? 1 : 0 });
    txt(s_.label, x, baseY + 110 * U, { f: F('mono', 24 * U), col: C.mute, a: e > 0 ? 1 : 0 });
  });
  if (p.source) txt(p.source, SAFE.l, H - SAFE.b + 20 * U, { f: F('mono', 20 * U), col: C.mute, a: prog(lt, 1.0, 1.6) });
});
