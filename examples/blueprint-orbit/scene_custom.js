// orbit scene — 3 satellites around a brand mark (blueprint example)
defineScene('orbit', (lt, d, p) => {
  const cx = W / 2, cy = H / 2, r = 260;
  const grow = eOutExpo(prog(lt, 0, 1.0));
  ctx.save();
  ctx.strokeStyle = A(0.25 * grow); ctx.lineWidth = 2;
  ctx.beginPath(); ctx.arc(cx, cy, r * grow, 0, 7); ctx.stroke();
  const rnd = rng(p.seed || 7);
  const items = p.items || [];
  items.forEach((it, i) => {
    const a = -Math.PI / 2 + i * 2 * Math.PI / items.length + lt * 0.9 + rnd() * 0.1;
    const x = cx + Math.cos(a) * r * grow, y = cy + Math.sin(a) * r * grow * 0.55;
    ctx.save(); ctx.shadowBlur = 24 * DPR; ctx.shadowColor = A(0.9);
    ctx.fillStyle = i % 2 ? ACC : C.cream;
    ctx.beginPath(); ctx.arc(x, y, 10, 0, 7); ctx.fill(); ctx.restore();
    txt(it.toUpperCase(), x + 16, y + 6, { f: `500 20px ${MONO}`, col: C.text, ls: '2px' });
  });
  ctx.restore();
  ctx.save(); ctx.shadowBlur = 40 * DPR; ctx.shadowColor = A(0.7);
  txt((p.title || '').toUpperCase(), cx, cy + 8, { f: `800 44px ${SANS}`, col: C.cream, align: 'center', ls: '4px' });
  ctx.restore();
});
