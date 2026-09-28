/* @meta {"name": "town_ride", "required": ["ads"], "text": ["ads"]} */
// The tracking shot: camera follows the rider; each store's ad pops out of its sign as he passes.
defineScene('town_ride', (lt, d, p) => {
  const T = T_ABS; const c = townCam(T);
  const row = drawTown(c, T);
  let look = [1, -0.1];
  const ads = [];
  const [px] = toScreen(c, 1, riderX(T) + 90, 0);          // the rider's screen x: ads pop as HE passes
  row.forEach((shop, i) => {
    const pass = passing(c, 1, shop.x + shop.w / 2, { focus: px + 60 * U, range: W * 0.26 });
    const k = clamp((pass - 0.2) / 0.3);
    if (k > 0.05) { const [ax, ay] = toScreen(c, 1, shop.x + shop.w / 2, -shop.h + 20); ads.push([ax, ay, k, (p.ads || [])[i] || {}, SHOPS[i].trim]); if (k > 0.5) look = [0.6, -0.8]; }
  });
  layer(c, 1, () => penguinRide(riderX(T), ROAD_Y, T, { look }));
  ads.forEach(([ax, ay, k, ad, col]) => popout(ax, ay, k, { title: ad.title, body: ad.body, badge: ad.badge, side: ad.side || 'up', w: 400 * U, h: 150 * U, accent: col, col: '#1f2a44' }));
  // foreground: passing bollards at depth 1.3 add speed
  const [fx0, fx1] = viewX(c, 1.3);
  layer(c, 1.3, () => { for (let x = Math.floor(fx0 / 520) * 520; x < fx1 + 520; x += 520) { capsule(x, 560, x, 470, 26, { fill: '#2b3a55' }); rect(x - 13, 492, 26, 8, '#f4a03a'); } });
});
