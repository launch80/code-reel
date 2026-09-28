/* @meta {"name": "courier_run", "required": ["stops"], "text": ["stops"]} */
// A character journey: a round bird courier scoots past houses; a speech bubble greets each stop.
function courier_run_bird(x, y, t, s) {
  const bob = cyc.bob(t, 0.25, 5 * s);
  capsule(x - 60 * s, y, x + 70 * s, y, 10 * s, { fill: '#3a3a3a' });                    // deck
  circle(x - 50 * s, y + 14 * s, 16 * s, { fill: '#222' }); circle(x + 60 * s, y + 14 * s, 16 * s, { fill: '#222' });
  capsule(x + 62 * s, y, x + 70 * s, y - 110 * s, 8 * s, { fill: '#3a3a3a' }); capsule(x + 50 * s, y - 110 * s, x + 90 * s, y - 110 * s, 8 * s, { fill: '#3a3a3a' });
  blob(x, y - 70 * s + bob, 48 * s, 52 * s, { fill: C.accent });                         // body
  blob(x + 12 * s, y - 60 * s + bob, 26 * s, 30 * s, { fill: '#fff4e0', stroke: null });  // belly
  eye(x + 22 * s, y - 92 * s + bob, 9 * s, { look: [1, 0], blink: cyc.blink(t, 2.3, 2) });
  shape([[x + 42 * s, y - 86 * s + bob], [x + 64 * s, y - 80 * s + bob], [x + 42 * s, y - 74 * s + bob]], { fill: '#f4a03a', smooth: false });
  box(x - 72 * s, y - 100 * s + bob, 44 * s, 40 * s, { fill: '#c49a6c', stroke: '#7a5a3a', sw: 2, r: 4 });   // parcel
  const w = ik2(x + 10 * s, y - 60 * s + bob, x + 58 * s, y - 108 * s, 30 * s, 30 * s, -1);
  capsule(x + 10 * s, y - 60 * s + bob, w.jx, w.jy, 10 * s, { fill: C.accent }); capsule(w.jx, w.jy, w.ex, w.ey, 9 * s, { fill: C.accent });
}
defineScene('courier_run', (lt, d, p) => {
  const stops = p.stops || []; const speed = 420, c = cam(lt * speed + 300, 0, 1, { cy: H * 0.68 });
  sky(mix(C.bg, '#9fd6f2', 0.6), C.bg);
  hills(c, 0.35, 4, { y: -20, amp: 140, fill: mix(C.bg, '#6aa37a', 0.5) });
  street(c, { y: 0, sidewalk: 40, road: 300, walk: mix(C.bg, '#d8d2c8', 0.6), asphalt: mix(C.bg, '#444a55', 0.7) });
  const houses = stops.map((st, i) => ({ x: 700 + i * 900, name: st.name, hi: st.hello }));
  layer(c, 1, () => houses.forEach((h, i) => { const col = ['#f2c6a0', '#b8d8c8', '#c9c2e8', '#f6d88a'][i % 4];
    rect(h.x, -300, 380, 300, col); shape([[h.x - 30, -300], [h.x + 190, -440], [h.x + 410, -300]], { fill: '#b5543c', smooth: false });
    box(h.x + 150, -150, 80, 150, { fill: '#6b4a3a', stroke: null, r: 4 });
    box(h.x + 40, -240, 90, 80, { fill: '#cde8f0', stroke: '#5a4a40', sw: 3, r: 4 }); box(h.x + 250, -240, 90, 80, { fill: '#cde8f0', stroke: '#5a4a40', sw: 3, r: 4 });
    txt(h.name, h.x + 190, -320, { f: F('sans', 34, { w: 'bold' }), col: '#3a2a20', align: 'center' }); }));
  const bx = lt * speed + 300 - 150;
  layer(c, 1, () => courier_run_bird(bx, 150, lt, 1.1));
  houses.forEach(h => { const k = clamp((passing(c, 1, h.x + 190, { focus: W * 0.42, range: W * 0.3 }) - 0.2) / 0.3);
    const [ax, ay] = toScreen(c, 1, h.x + 190, -150); bubble(ax, ay, h.hi, k, { side: 'up', accent: C.accent }); });
});
