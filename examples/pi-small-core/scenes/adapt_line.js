/* @meta {"name": "adapt_line", "required": ["line"], "text": ["line"]} */
// The grid rearranges itself into a staircase — a workflow shape — as the README line lands.
defineScene('adapt_line', (lt, d, p) => {
  const cs = 58 * U; const k = M.move(prog(lt, 0.0, 0.9));
  const stairs = []; for (let c = 0; c < 6; c++) for (let r = 0; r <= c; r++) stairs.push([c, r]);   // 21 tiles: a staircase
  const n = stairs.length;
  for (let i = 0; i < n; i++) {
    const gx = W * 0.64 + (i % 5) * cs, gy = H * 0.28 + Math.floor(i / 5) * cs;                  // the old square block
    const [c, r] = stairs[i]; const sx = W * 0.58 + c * cs, sy = H * 0.78 - (r + 1) * cs;         // a workflow that climbs
    const e = M.move(prog(lt, i * 0.02, 0.7 + i * 0.02)); const x = lerp(gx, sx, e), y = lerp(gy, sy, e);
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
