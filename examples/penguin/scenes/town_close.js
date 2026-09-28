/* @meta {"name": "town_close", "required": ["title"], "text": ["title", "line", "url"]} */
// He stops at SCOOPS, the camera eases in, the title card lands on the awning's color.
defineScene('town_close', (lt, d, p) => {
  const T = T_ABS; const base = townCam(T); const z = kf(lt, [[0, base.z], [2.2, 1.7]], eInOutSine);
  const focusX = riderX(T) + 120, c = cam(lerp(base.x, focusX + 380, eInOutSine(prog(lt, 0, 2.2))), kf(lt, [[0, 0], [2.2, 60]], eInOutSine), z, { cy: base.cy });
  drawTown(c, T);
  const cone = prog(lt, 0.4, 0.9);
  layer(c, 1, () => { const r = penguinRide(riderX(T), ROAD_Y, T, { look: [0.4, -0.6], crank: 0.6 });
    if (cone > 0) { const hx = r.head[0] + 66, hy = r.head[1] + 30; shape([[hx - 14, hy - 30], [hx + 14, hy - 30], [hx, hy + 10]], { fill: '#e9c46a', smooth: false }); blob(hx, hy - 42, 20 * spring(cone), 18 * spring(cone), { fill: '#ffafcc' }); } });
  const e = M.in(prog(lt, 0.9, 1.8));
  const tf = F('disp', fitPx(p.title, 'disp', W * 0.4, 130 * U, 50 * U));
  const cardW = W * 0.46, cardH = 330 * U, cx = W - SAFE.r - cardW, cy = H * 0.12;
  box(cx, cy + (1 - e) * 40 * U, cardW, cardH, { fill: '#fff8f0', stroke: '#c9184a', sw: 5, r: 36 * U, a: e, shadow: 24 });
  txt(p.title, cx + cardW / 2, cy + 160 * U + (1 - e) * 40 * U, { f: tf, col: '#c9184a', align: 'center', a: e });
  if (p.line) txt(p.line, cx + cardW / 2, cy + 235 * U, { f: F('serif', 46 * U, { i: true }), col: '#1f2a44', align: 'center', a: M.in(prog(lt, 1.3, 2.0)) });
  if (p.url) txt('→ ' + typed(p.url, lt, 1.6, 2.4), cx + cardW / 2, cy + 295 * U, { f: F('mono', 30 * U), col: '#5d6b86', align: 'center', a: M.in(prog(lt, 1.5, 1.8)) });
}, {});
