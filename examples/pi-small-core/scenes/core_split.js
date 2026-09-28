/* @meta {"name": "core_split", "required": ["core", "plugins"], "text": ["core", "plugins", "caption"], "slams": []} */
// The monolith cracks along its grid: most tiles scatter off-frame, six settle in orbit
// around a tiny core square and become the plugin types.
function core_split_orbit(i, n, lt) {
  const a = -Math.PI / 2 + i * Math.PI * 2 / n + lt * 0.18;
  return [W / 2 + Math.cos(a) * W * 0.28, H * 0.52 + Math.sin(a) * H * 0.28];
}
defineScene('core_split', (lt, d, p) => {
  const g = monolith_geom(); const cols = 10, rows = 6; const tw_ = g.w / cols, th = g.h / rows;
  const plugins = p.plugins || []; const r = rng(42);
  const keep = new Set([3, 8, 14, 27, 44, 51].slice(0, plugins.length));
  const blast = eOutCubic(prog(lt, 0.0, 1.1));
  let pi = 0;
  for (let k = 0; k < cols * rows; k++) {
    const cx = g.x + (k % cols + 0.5) * tw_, cy = g.y + (Math.floor(k / cols) + 0.5) * th;
    const ang = Math.atan2(cy - H * 0.6, cx - W / 2) + (r() - 0.5) * 0.8, dist = (600 + r() * 900) * U;
    if (keep.has(k)) {
      const idx = pi++; const [ox, oy] = core_split_orbit(idx, plugins.length, lt);
      const s = M.move(prog(lt, 0.3 + idx * 0.08, 1.4 + idx * 0.08));
      const x = lerp(cx, ox, s), y = lerp(cy, oy, s), sz = lerp(tw_, 70 * U, s);
      box(x - sz / 2, y - sz / 2, sz, sz, { fill: s > 0.95 ? ACC : C.surf, stroke: C.text, sw: 2, r: 0 });
      const la = prog(lt, 1.3 + idx * 0.1, 1.7 + idx * 0.1);
      if (la > 0) { const lbl = plugins[idx]; const lf = F('mono', 26 * U, { w: 'bold' }); const right = x >= W / 2;
        txt(lbl, x + (right ? 1 : -1) * 56 * U, y + 9 * U, { f: lf, col: C.cream, align: right ? 'left' : 'right', a: la }); }
    } else {
      const x = cx + Math.cos(ang) * dist * blast, y = cy + Math.sin(ang) * dist * blast + 400 * U * blast * blast;
      ctx.save(); ctx.translate(x, y); ctx.rotate((r() - 0.5) * 2 * blast);
      box(-tw_ / 2, -th / 2, tw_, th, { fill: C.surf, stroke: rgba(C.text, 0.6), sw: 2, r: 0, a: 1 - prog(lt, 0.6, 1.2) });
      ctx.restore();
    }
  }
  // the core: small, solid, accent — the whole point
  const ce = spring(prog(lt, 0.5, 1.3)); const cs = 130 * U * ce;
  if (cs > 1) { box(W / 2 - cs / 2, H * 0.52 - cs / 2, cs, cs, { fill: C.cream, stroke: null, r: 0 });
    txt(p.core, W / 2, H * 0.52 + cs * 0.22, { f: F('disp', cs * 0.62), col: C.bg, align: 'center' }); }
  // orbit ring (dashed) once the plugins arrive
  const ra = prog(lt, 1.2, 2.0);
  if (ra > 0) { ctx.save(); ctx.globalAlpha = 0.5 * ra; ctx.strokeStyle = rgba(C.text, 0.4); ctx.setLineDash([6, 10]); ctx.lineWidth = 2;
    ctx.beginPath(); ctx.ellipse(W / 2, H * 0.52, W * 0.28, H * 0.28, 0, 0, Math.PI * 2); ctx.stroke(); ctx.restore(); }
  if (p.caption) txt(p.caption, SAFE.l, H - SAFE.b - 10 * U, { f: F('sans', fitPx(p.caption, 'sans', W * 0.5, 40 * U, 20 * U, { w: 'bold' }), { w: 'bold' }), col: C.cream, a: M.in(prog(lt, 2.2, 2.8)) });
});
