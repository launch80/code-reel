// Shared world for this video: the street, the stores, the rider.
// Every town_* scene draws the SAME world at the same world clock (T_ABS),
// so cuts between scenes are continuous.
'use strict';

const SHOPS = [
  { name: 'BAKERY', w: 400, h: 300, wall: '#f6d7b0', trim: '#8a4b2a', awning: ['#e76f51', '#fff4e6'], glass: '#cde8f0', item: 'bread' },
  { name: 'SPOKES', w: 440, h: 330, wall: '#cfe3d6', trim: '#2f5d50', awning: ['#2a9d8f', '#f1faee'], glass: '#d7eef7', item: 'wheel' },
  { name: 'PAGES', w: 380, h: 290, wall: '#e9dcf5', trim: '#5a3e85', awning: ['#7b5ea7', '#fbf8ff'], glass: '#e3f1f8', item: 'books' },
  { name: 'SCOOPS', w: 420, h: 310, wall: '#ffe1ea', trim: '#c9184a', awning: ['#ff4d6d', '#fff0f3'], glass: '#dff3fb', item: 'cone' },
];
const SHOP_GAP = 150, ROAD_Y = 210;
// world x of each shop's left edge
const SHOP_X = (() => { let x = 260; return SHOPS.map(s => { const v = x; x += s.w + SHOP_GAP; return v; }); })();

// the rider's world x at absolute time T: glides in, cruises, brakes at SCOOPS
function riderX(T) {
  const stop = SHOP_X[3] + 120;
  return kf(T, [[0, -380], [1.2, -80], [12.0, stop - 60], [13.2, stop]], x => x);   // piecewise-linear cruise
}
function riderV(T) { return (riderX(T + 0.02) - riderX(T - 0.02)) / 0.04; }
function townCam(T) {
  const x = riderX(T);
  return cam(Math.max(x + 230, W * 0.2), 0, 1.22, { cy: H * 0.6 });
}

function window_item(kind, x, y, w, h) {
  const cx = x + w / 2, by = y + h - 12;
  if (kind === 'bread') { [[-50, 0], [0, -6], [50, 0]].forEach(([dx, dy]) => { blob(cx + dx, by - 26 + dy, 38, 20, { fill: '#d4a373' }); line(cx + dx - 18, by - 32 + dy, cx + dx - 6, by - 20 + dy, { col: '#a26f45', sw: 3 }); line(cx + dx + 2, by - 34 + dy, cx + dx + 14, by - 22 + dy, { col: '#a26f45', sw: 3 }); }); }
  if (kind === 'wheel') { circle(cx, by - 60, 52, { stroke: '#2b2b2b', sw: 8 }); for (let k = 0; k < 6; k++) { const a = k * Math.PI / 3; line(cx, by - 60, cx + Math.cos(a) * 48, by - 60 + Math.sin(a) * 48, { col: '#888', sw: 2 }); } }
  if (kind === 'books') { const cols = ['#e63946', '#457b9d', '#f4a261', '#2a9d8f', '#6d597a']; cols.forEach((c, i) => rect(x + 30 + i * 30, by - 90 + (i % 2) * 10, 24, 90 - (i % 2) * 10, c)); }
  if (kind === 'cone') { shape([[cx - 26, by - 70], [cx + 26, by - 70], [cx, by]], { fill: '#e9c46a', smooth: false }); blob(cx, by - 84, 32, 28, { fill: '#ffafcc' }); blob(cx + 10, by - 104, 20, 18, { fill: '#bde0fe' }); }
}

function drawTown(c, T) {
  sky('#8fd3f4', '#e8f7fd');
  sun(W * 0.82, H * 0.17, 60 * U, '#ffd166', 0.45);
  clouds(c, 0.12, 5, { n: 9, span: 5200, y: -H * 0.42, t: T, drift: 18 });
  hills(c, 0.3, 11, { y: -30, amp: 170, fill: '#a8d5ba' });
  hills(c, 0.45, 23, { y: -10, amp: 110, fill: '#86c29c' });
  // distant rooftops
  const [bx0, bx1] = viewX(c, 0.65);
  layer(c, 0.65, () => {
    for (let k = Math.floor(bx0 / 170) - 1; k < bx1 / 170 + 1; k++) {
      const h = 180 + hash1(k * 3.3) * 220, w = 150; const x = k * 170, col = ['#c6d8e4', '#b9cfdd', '#d3e1ea'][Math.abs(k) % 3];
      rect(x, -h, w, h + 5, col);
      for (let wy = -h + 30; wy < -30; wy += 48) for (let wx = x + 20; wx < x + w - 30; wx += 40) rect(wx, wy, 18, 24, 'rgba(255,255,255,0.55)');
    }
  });
  street(c, { y: 0, sidewalk: 70, road: 460, walk: '#e9e2d6', curb: '#c9bfae', asphalt: '#59606b', dash: '#f7ecc9' });
  INK = '#2b3a55'; INKW = 3;
  const row = storeRow(c, SHOPS.map((s, i) => Object.assign({ display: (x, y, w, h) => window_item(s.item, x, y, w, h), signFont: 'disp' }, s)),
    { y: 0, x0: SHOP_X[0], gap: SHOP_GAP, between: (x, y, i) => (i % 2 ? tree(x, y + 4, 1.05, {}) : lamp(x, y + 4, 280)) });
  INK = null; INKW = 0;
  return row;
}

// ---- the penguin on the bicycle (world coords: x = rear-wheel contact, y = road)
function penguinRide(x, y, T, o = {}) {
  const s = o.s || 1.05; const v = riderV(T);
  const crankA = o.crank ?? (riderX(T) / (2 * Math.PI * 52 * s) * Math.PI * 2 * 0.9);   // pedal with the wheels
  const rig = bikeRig(x, y, { s, crank: crankA });
  const bob = cyc.osc(T, 0.5, 2.5 * clamp(Math.abs(v) / 200));
  const hip = [rig.seat[0] - 4 * s, rig.seat[1] - 16 * s + bob];
  const INKC = '#1f2a44';
  const leg = (ped, far) => {
    const k = ik2(hip[0], hip[1], ped[0], ped[1] - 6 * s, 60 * s, 56 * s, -1);
    const col = far ? '#15181f' : '#232834';
    capsule(hip[0], hip[1], k.jx, k.jy, 26 * s, { fill: col, stroke: INKC, sw: 2.5 });
    capsule(k.jx, k.jy, k.ex, k.ey, 20 * s, { fill: col, stroke: INKC, sw: 2.5 });
    blob(ped[0] + 10 * s, ped[1] - 4 * s, 26 * s, 10 * s, { fill: far ? '#e07a1f' : '#f4a03a', stroke: INKC, sw: 2.5 });
  };
  shadow(x + 85 * s, y + 4, 150 * s, 12 * s, 0.22);
  leg(rig.pedals[1], true);                           // far leg behind the frame
  INK = INKC; INKW = 2.5;
  bicycle(x, y, { s, crank: crankA, rot: riderX(T) / (52 * s), frame: o.frame || '#e76f51' });
  // body: leaning forward over the bars
  const lean = -0.35; const bx = hip[0] + 34 * s, by = hip[1] - 58 * s + bob;
  ctx.save(); ctx.translate(bx, by); ctx.rotate(lean);
  blob(0, 0, 50 * s, 74 * s, { fill: '#1d2230' });                         // back / body
  blob(14 * s, 8 * s, 34 * s, 58 * s, { fill: '#fbfbf7', stroke: null });   // belly
  ctx.restore();
  // scarf trailing behind in the wind
  const neck = [bx + 10 * s, by - 58 * s + bob]; const pts = [];
  for (let k = 0; k < 7; k++) pts.push([neck[0] - k * 22 * s, neck[1] + k * 5 * s + cyc.osc(T + k * 0.07, 0.35, (2 + k * 3) * s)]);
  poly(pts, 1, { col: '#e63946', sw: 14 * s }); capsule(neck[0] - 6 * s, neck[1], neck[0] + 22 * s, neck[1] + 6 * s, 16 * s, { fill: '#e63946' });
  // head
  const hx = bx + 44 * s, hy = by - 88 * s + bob; const look = o.look || [1, 0];
  blob(hx, hy, 40 * s, 38 * s, { fill: '#1d2230' });
  blob(hx + 16 * s, hy + 6 * s, 24 * s, 24 * s, { fill: '#fbfbf7', stroke: null });
  shape([[hx + 32 * s, hy - 2 * s], [hx + 70 * s + look[0] * 4 * s, hy + 8 * s + look[1] * 6 * s], [hx + 32 * s, hy + 16 * s]], { fill: '#f4a03a', smooth: false });
  eye(hx + 20 * s, hy - 6 * s, 9 * s, { look, blink: cyc.blink(T, 2.7, 4) });
  blob(hx + 26 * s, hy + 14 * s, 6 * s, 3 * s, { fill: 'rgba(255,120,120,0.45)', stroke: null });   // cheek
  // flipper reaching the handlebar
  const sh = [bx + 22 * s, by - 34 * s + bob]; const f = ik2(sh[0], sh[1], rig.bar[0] - 4 * s, rig.bar[1] + 4 * s, 46 * s, 40 * s, 1);
  capsule(sh[0], sh[1], f.jx, f.jy, 18 * s, { fill: '#1d2230' }); capsule(f.jx, f.jy, f.ex, f.ey, 14 * s, { fill: '#1d2230' });
  INK = null; INKW = 0;
  leg(rig.pedals[0], false);                          // near leg in front
  return { head: [hx, hy], rig };
}
