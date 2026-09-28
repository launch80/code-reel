/* @meta {"name": "monolith", "required": ["slab", "question"], "text": ["slab", "question"], "typing": [{"key": "question", "a": 0.5, "b": 1.7}]} */
// The question, pressed under a monolith: one heavy slab on a strict grid.
function monolith_geom() { const w = W * 0.62, h = H * 0.46; return { x: (W - w) / 2, y: H * 0.40, w, h }; }
defineScene('monolith', (lt, d, p) => {
  const g = monolith_geom();
  const drop = lt < 0.9 ? eIn(prog(lt, 0.05, 0.9)) : 1;                  // falls like a weight
  const thud = Math.max(0, 1 - Math.abs(lt - 0.9) / 0.18);                // impact squash at landing
  const press = prog(lt, 1.9, 2.1) * (1 - prog(lt, 2.1, 2.6));            // second slam: presses down
  const y = lerp(-g.h - 40, g.y, drop) + press * 18 * U;
  const sq = 1 - 0.04 * thud - 0.03 * press;
  // grid lines under everything (the Swiss grid is the world)
  for (let k = 1; k < 12; k++) line(SAFE.l + (W - SAFE.l - SAFE.r) * k / 12, 0, SAFE.l + (W - SAFE.l - SAFE.r) * k / 12, H, { col: rgba(C.text, 0.05), sw: 1 });
  ctx.save(); ctx.translate(W / 2, y + g.h); ctx.scale(1 + (1 - sq) * 0.6, sq); ctx.translate(-W / 2, -(y + g.h));
  rect(g.x + 14 * U, y + 18 * U, g.w, g.h, rgba('#000000', 0.45));        // cast shadow
  box(g.x, y, g.w, g.h, { fill: C.surf, stroke: C.text, sw: 4, r: 0 });
  const f = F('disp', fitPx(p.slab, 'disp', g.w * 0.86, g.h * 0.72, 60 * U));
  txt(p.slab, W / 2, y + g.h * 0.72, { f, col: rgba(C.text, 0.92), align: 'center' });
  // hairline cracks start along the grid just before the cut
  const cr = prog(lt, 2.3, d);
  if (cr > 0) for (let k = 1; k < 10; k++) { const x = g.x + g.w * k / 10; poly([[x, y], [x + (k % 2 ? 6 : -6) * U, y + g.h * 0.5], [x, y + g.h]], cr, { col: ACC, sw: 2 }); }
  ctx.restore();
  // dust at landing
  if (lt > 0.9 && lt < 1.6) { const r = rng(3); const k = prog(lt, 0.9, 1.6); for (let i = 0; i < 40; i++) { const side = r() < 0.5 ? -1 : 1; circle(W / 2 + side * (g.w / 2 + r() * 220 * U * k), g.y + g.h - r() * 30 * U * (1 - k), (2 + r() * 5) * U, { fill: rgba(C.mute, 0.6 * (1 - k)) }); } }
  // the question types above the slab
  const qf = F('sans', fitPx(p.question, 'sans', W - SAFE.l - SAFE.r, 76 * U, 30 * U, { w: 'bold' }), { w: 'bold' });
  const q = typed(p.question, lt, 0.5, 1.7);
  txt(q, SAFE.l, SAFE.t + 110 * U, { f: qf, col: C.cream });
  if (lt > 0.4) cursor(SAFE.l + tw(q, qf) + 8 * U, SAFE.t + 116 * U, lt, 64 * U, 30 * U, ACC);
  rect(SAFE.l, SAFE.t + 140 * U, 160 * U * M.in(prog(lt, 0.2, 0.8)), 8 * U, ACC);
});
