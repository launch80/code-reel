/* @meta {"name": "install_end", "required": ["cmd", "url"], "text": ["cmd", "url", "version", "tag"], "typing": [{"key": "cmd", "a": 0.15, "b": 1.0}]} */
// One tile becomes the cursor: the install command types out, then the address lands.
defineScene('install_end', (lt, d, p) => {
  const f = F('mono', fitPx('$ ' + p.cmd, 'mono', W - SAFE.l - SAFE.r, 44 * U, 18 * U)); const y = H * 0.44;
  const shrink = M.move(prog(lt, 0, 0.2)); const cw = lerp(120 * U, tw('m', f), shrink), chh = lerp(120 * U, 50 * U, shrink);
  const s = '$ ' + typed(p.cmd, lt, 0.15, 1.0);
  txt(s, SAFE.l, y, { f, col: C.cream });
  const cx = lt < 0.2 ? W / 2 - cw / 2 : SAFE.l + tw(s, f) + 6 * U;
  if (lt < 0.2 || Math.floor(lt * 2.6) % 2 === 0) rect(cx, y - chh * 0.8, cw, chh, ACC);
  const e = M.in(prog(lt, 1.0, 1.5));
  const uf = F('disp', fitPx(p.url, 'disp', W * 0.6, 170 * U, 60 * U));
  txt(p.url, SAFE.l, H * 0.72, { f: uf, col: C.cream, a: e });
  if (p.version) txt(p.version, W - SAFE.r, H * 0.72, { f: F('mono', 30 * U, { w: 'bold' }), col: HOTC, align: 'right', a: e });
  if (p.tag) txt(p.tag, SAFE.l, H * 0.72 + 70 * U, { f: F('mono', fitPx(p.tag, 'mono', W - SAFE.l - SAFE.r, 28 * U, 14 * U)), col: C.mute, a: M.in(prog(lt, 1.3, 1.8)) });
});
