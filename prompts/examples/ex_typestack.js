/* @meta {"name": "crane_words", "required": ["words"], "text": ["words", "caption"], "slams": []} */
// Kinetic type with a physical metaphor: a crane lowers each word as a crate onto a stack.
defineScene('crane_words', (lt, d, p) => {
  const words = p.words || []; const n = words.length; const per = 0.7 * d / Math.max(1, n);
  const baseY = H - SAFE.b - 40 * U, colX = W * 0.56, crH = 118 * U;
  const craneX = SAFE.l + 80 * U, top = SAFE.t + 30 * U;
  // crane: mast + jib + counterweight
  rect(craneX - 14 * U, top, 28 * U, baseY - top, C.line); rect(craneX - 160 * U, top, W - craneX - SAFE.r + 160 * U, 16 * U, C.line);
  for (let x = craneX; x < W - SAFE.r; x += 60 * U) line(x, top, x + 30 * U, top + 16 * U, { col: C.bg, sw: 2 });
  rect(craneX - 160 * U, top + 16 * U, 90 * U, 70 * U, C.mute);
  line(SAFE.l, baseY, W - SAFE.r, baseY, { col: C.line, sw: 4 });
  let hookX = colX, hookY = top + 120 * U, stackTop = baseY;
  words.forEach((w, i) => {
    const t0 = 0.08 * d + i * per, k = prog(lt, t0, t0 + per * 0.85);
    const f = F('disp', fitPx(w, 'disp', W * 0.5, 84 * U, 30 * U)); const bw = tw(w, f) + 80 * U;
    const landY = stackTop - crH; const x = colX - bw / 2 + (i % 2 ? 26 : -26) * U;
    if (k <= 0) return;
    const drop = eOutBack(clamp(k * 1.15)); const y = lerp(top + 140 * U, landY, drop);
    if (k < 1) { hookX = x + bw / 2; hookY = y; }
    box(x, y, bw, crH - 10 * U, { fill: i === n - 1 ? A(1) : C.surf, stroke: C.cream, sw: 3, r: 6 * U });
    for (let s = 1; s < 4; s++) line(x + bw * s / 4, y + 10 * U, x + bw * s / 4, y + crH - 20 * U, { col: rgba(C.cream, 0.15), sw: 2 });
    txt(w, x + bw / 2, y + crH * 0.62, { f, col: i === n - 1 ? C.bg : C.cream, align: 'center' });
    stackTop = landY + (k >= 1 ? 0 : crH);
    if (k >= 1) stackTop = landY;
  });
  line(hookX, top + 16 * U, hookX, hookY, { col: C.cream, sw: 3 }); circle(hookX, hookY, 9 * U, { stroke: C.cream, sw: 3 });
  if (p.caption) txt(p.caption, W - SAFE.r, top + 90 * U, { f: F('serif', fitPx(p.caption, 'serif', W * 0.36, 48 * U, 22 * U, { i: true }), { i: true }), col: C.mute, align: 'right', a: M.in(prog(lt, 0.75 * d, 0.95 * d)) });
});
