/* @meta {"name": "adapt_line", "required": ["line"], "text": ["line"]} */
// The grid rearranges itself into a staircase — a workflow shape — as the README line lands.
defineScene('adapt_line', (lt, d, p) => {
  const n = 24, cs = 46 * U; const k = M.move(prog(lt, 0.0, 0.9));
  for (let i = 0; i < n; i++) {
    const gx = W * 0.62 + (i % 6) * cs, gy = H * 0.30 + Math.floor(i / 6) * cs;                 // square block
    const step = Math.floor(i / 3), sx = W * 0.56 + step * cs * 1.05 + (i % 3) * cs * 0.34, sy = H * 0.74 - step * cs * 0.62 - (i % 3) * cs * 0.3; // stairs
    const x = lerp(gx, sx, k), y = lerp(gy, sy, k);
    box(x, y, cs - 6 * U, cs - 6 * U, { fill: i === n - 1 ? HOTC : ACC, stroke: null, r: 0, a: 0.9 });
  }
  const maxW = W * 0.46; let px = 84 * U, lines;
  do { lines = wrap(p.line, F('sans', px, { w: 'bold' }), maxW); if (lines.length <= 4) break; px *= 0.92; } while (px > 30 * U);
  const f = F('sans', px, { w: 'bold' }); const em = new Set((p.emphasis || []).map(w => w.toLowerCase()));
  lines.forEach((ln, li) => {
    let x = SAFE.l; const y = H * 0.36 + li * px * 1.12; const a = M.in(prog(lt, 0.15 + li * 0.12, 0.55 + li * 0.12));
    ln.split(' ').forEach(w => { const key = w.toLowerCase().replace(/[^\w]/g, '');
      if (em.has(key)) rect(x - 4 * U, y + 10 * U, (tw(w, f) + 8 * U) * a, 10 * U, ACC);
      txt(w, x, y + (1 - a) * 30 * U, { f, col: em.has(key) ? C.cream : C.text, a }); x += tw(w + ' ', f); });
  });
});
