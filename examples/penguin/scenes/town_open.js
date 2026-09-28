/* @meta {"name": "town_open", "required": ["kicker"], "text": ["kicker"]} */
// Establishing shot: same world, camera settles from a wide sky tilt; the rider glides in.
defineScene('town_open', (lt, d, p) => {
  const T = T_ABS; const base = townCam(T);
  const tilt = kf(lt, [[0, -260], [2.2, 0]], eInOutSine), z = kf(lt, [[0, 0.86], [2.4, 1]], eInOutSine);
  const c = cam(base.x, tilt, z, { cy: base.cy });
  drawTown(c, T);
  layer(c, 1, () => penguinRide(riderX(T), ROAD_Y, T, { look: [1, 0] }));
  const e = M.in(prog(lt, 0.3, 1.2)) * (1 - prog(lt, d - 0.5, d));
  const f = F('serif', 64 * U, { i: true }); const tw_ = tw(p.kicker, f) + 70 * U;
  box(W / 2 - tw_ / 2, SAFE.t + 20 * U, tw_, 100 * U, { fill: 'rgba(255,255,255,0.92)', stroke: null, r: 50 * U, a: e, shadow: 12 });
  txt(p.kicker, W / 2, SAFE.t + 90 * U, { f, col: '#1f2a44', align: 'center', a: e });
});
