// code-reel engine · player.js
// Loads the COMPILED timeline (window.__TIMELINE__, written by `reel.py compile`
// into .reel/timeline.js), applies the style pack, and renders any time t
// deterministically: background → camera → scene(s) → transition composite →
// HUD → post. Also a live preview player when opened without ?render.
'use strict';

let SCN = [], CUTS = [], IMPACTS = [], TRANSITIONS = [];

function applyStyle(st) {
  STYLE = st;
  const P = st.palette;
  C = Object.assign({}, C, P); C.or = P.accent; C.accent = P.accent; C.ink = P.cream;
  ACC = P.accent; HOTC = P.hot;
  FONTS = Object.assign({}, FONTS, st.fonts); FW = Object.assign({}, FW, st.weights || {});
  SANS = `"${FONTS.sans}"`; MONO = `"${FONTS.mono}"`; SERIF = `"${FONTS.serif}"`; DISP = `"${FONTS.disp}"`;
  CAPS = st.caps !== false; GLOW = st.glow ?? 1;
  const mo = st.motion || {};
  M = { in: EASE[mo.in] || eOutExpo, out: EASE[mo.out] || eIn, move: EASE[mo.move] || eInOut, k: mo.k || 1 };
  document.documentElement.style.setProperty('--accent', ACC);
  document.body.style.background = C.bg;
}

function buildTimeline(tl) {
  TL = tl;
  W = tl.w || 1920; H = tl.h || 1080; FPS = tl.fps || 60; BPM = tl.bpm || 120;
  U = Math.min(W, H) / 1080;
  const sb = (tl.style && tl.style.safe) || {};
  SAFE = { l: (sb.l ?? 96) * (W / 1920 > 0.7 ? W / 1920 : 0.9), r: (sb.r ?? 96) * (W / 1920 > 0.7 ? W / 1920 : 0.9), t: (sb.t ?? 120) * U, b: (sb.b ?? 110) * U };
  if (W < H) { SAFE.l = SAFE.r = 72 * U; SAFE.t = 160 * U; SAFE.b = 160 * U; }
  applyStyle(tl.style);
  const ev = tl.events || {};
  SCN = (tl.scenes || []).map(s => Object.assign({}, s));
  for (const s of SCN) if (!REG[s.scene]) throw new Error('unknown scene type: ' + s.scene + ' (not built in and not defined in scenes/*.js)');
  CUTS = ev.cuts || []; IMPACTS = ev.impacts || []; TRANSITIONS = ev.transitions || [];
  DUR = tl.duration;
  cv.width = W * DPR; cv.height = H * DPR;
}

function sceneAt(t) { for (let i = 0; i < SCN.length; i++) if (t >= SCN[i].t0 && t < SCN[i].t1) return i; return SCN.length - 1; }

function drawFrame(target, t, i, lt, selfExit, fi, imp) {
  const s = SCN[i]; const d = s.t1 - s.t0; const look = Object.assign({}, STYLE, s.look || {});
  ctx = target; ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  const boost = (t < (CUTS[0] ?? DUR) || t > (CUTS[CUTS.length - 1] ?? 0)) ? 1.6 : 1;
  (BG[look.bg] || BG.solid)(t, Object.assign({ boost }, look.bgOpts || {}));
  const cam = (CAM[look.camera] || CAM.static)(t, clamp(lt / d), imp, fi);
  ctx.save(); ctx.translate(W / 2 + cam.x, H / 2 + cam.y); ctx.rotate(cam.r || 0); ctx.scale(cam.z, cam.z); ctx.translate(-W / 2, -H / 2);
  SELF_EXIT = selfExit; CUR_SCENE = (s.name || s.scene);
  REG[s.scene](Math.max(0, lt), d, s.p || {});
  ctx.restore();
}

function render(t) {
  if (!TL) return;
  const fi = Math.round(t * FPS);
  const main = cv.getContext('2d');
  // impact strength (camera) and post fx
  let imp = 0; IMPACTS.forEach(c => { const d = t - c; if (d >= 0 && d < 0.3) imp = Math.max(imp, 1 - d / 0.3); });
  const fx = { glitch: 0, flash: 0 };
  TRANSITIONS.forEach(tr => {
    const d = t - tr.t;
    if (tr.fx === 'glitch' && d > -0.07 && d < 0.16) fx.glitch = Math.max(fx.glitch, 1 - Math.abs(d) / 0.16);
    if ((tr.fx === 'glitch' || tr.fx === 'flash') && d >= 0 && d < 0.2) fx.flash = Math.max(fx.flash, Math.pow(1 - d / 0.2, 2) * (tr.fx === 'flash' ? 0.55 : 0.3));
  });
  IMPACTS.forEach(c => { const d = t - c; if (d >= 0 && d < 0.2 && !CUTS.includes(c)) fx.flash = Math.max(fx.flash, Math.pow(1 - d / 0.2, 2) * 0.14); });
  fx.flash *= (STYLE.flash ?? 1);
  // is t inside an overlapping transition window?
  let tr = null; for (const x of TRANSITIONS) if (!x.self && x.dur > 0 && t >= x.t - x.dur / 2 && t < x.t + x.dur / 2) { tr = x; break; }
  const si = sceneAt(t);
  const selfExitOf = i => { const nx = TRANSITIONS.find(x => Math.abs(x.t - SCN[i].t1) < 1e-6); return !nx || nx.self; };
  if (!tr) {
    drawFrame(main, t, si, t - SCN[si].t0, selfExitOf(si), fi, imp);
  } else {
    const nextI = SCN.findIndex(s => Math.abs(s.t0 - tr.t) < 1e-6); const prevI = nextI - 1;
    const La = _layer('trA'), Lb = _layer('trB');
    drawFrame(La.ctx, t, prevI, t - SCN[prevI].t0, false, fi, imp);
    drawFrame(Lb.ctx, t, nextI, t - SCN[nextI].t0, selfExitOf(nextI), fi, imp);
    ctx = main; ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.clearRect(0, 0, cv.width, cv.height);
    const q = M.move(clamp((t - (tr.t - tr.dur / 2)) / tr.dur));
    ctx.save(); (TRANS[tr.type] || TRANS.dissolve).draw(q, La.c, Lb.c, tr.opts || {}); ctx.restore();
  }
  ctx = main; ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  if (TL.hud !== false) { CUR_SCENE = '__hud__'; (HUD[STYLE.hud] || HUD.none)(t, { si, n: SCN.length, label: (SCN[si].name || SCN[si].scene).toUpperCase(), cuts: CUTS }); }
  ctx.save(); ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
  (POST[STYLE.post] || POST.clean)(t, fi, fx, STYLE.postOpts || {});
  const fo = Math.max(1 - prog(t, 0, STYLE.fadeIn ?? 0.12), prog(t, DUR - (STYLE.fadeOut ?? 0.25), DUR));
  if (fo > 0) { ctx.globalAlpha = fo; ctx.fillStyle = STYLE.fadeTo || '#000'; ctx.fillRect(0, 0, cv.width, cv.height); }
  ctx.restore();
}
window.render = render;
window.auditFrame = t => { AUDIT_LOG = []; render(t); return AUDIT_LOG; };

// ------------------------------------------------------------------ loading
function _err(msg) { const e = document.getElementById('err'); if (e) { e.style.display = 'grid'; e.textContent = msg; } console.error(msg); window.__REEL_ERROR__ = msg; }
async function loadAssets(tl) {
  const jobs = Object.entries(tl.assets || {}).map(([k, src]) => new Promise(res => { const im = new Image(); im.onload = () => { IMG[k] = im; res(); }; im.onerror = () => { _err('asset failed to load: ' + k + ' -> ' + src); res(); }; im.src = src; }));
  await Promise.all(jobs);
}
window.ready = (async () => {
  try {
    const tl = window.__TIMELINE__;
    if (!tl) { _err('No compiled timeline. Run:  python3 reel.py compile <project>  (it writes .reel/timeline.js)'); return false; }
    buildTimeline(tl);
    const st = tl.style; const want = new Set();
    for (const role of ['sans', 'mono', 'serif', 'disp']) for (const o of [{}, { w: 'bold' }, { i: true }]) want.add(F(role, 20, o));
    for (const f of want) { try { await document.fonts.load(f); } catch (e) { } }
    for (const role of ['sans', 'mono', 'serif', 'disp']) if (!document.fonts.check(F(role, 20))) _err('font not available: ' + st.fonts[role]);
    await loadAssets(tl);
    render(0); return !window.__REEL_ERROR__;
  } catch (e) { _err(String(e && e.stack || e)); return false; }
})();

// ------------------------------------------------------------------ preview
if (!new URLSearchParams(location.search).has('render')) {
  document.body.classList.add('preview');
  window.ready.then(ok => {
    if (!ok) return;
    const ui = document.createElement('div'); ui.id = 'ui';
    ui.innerHTML = '<button id=pp>play</button><input id=sc type=range min=0 max=1 step=0.001 value=0><span id=tc>0.00s</span><label><input id=mu type=checkbox checked> sound</label>';
    document.body.appendChild(ui);
    const au = new Audio('audio.wav'); let playing = false, t0 = 0, base = 0;
    const pp = document.getElementById('pp'), sc = document.getElementById('sc'), tcEl = document.getElementById('tc'), mu = document.getElementById('mu');
    sc.max = DUR;
    const now = () => playing ? Math.min(DUR, base + (performance.now() - t0) / 1000) : base;
    function draw(t) { render(t); sc.value = t; tcEl.textContent = t.toFixed(2) + 's / F' + Math.round(t * FPS); }
    function play() { if (base >= DUR) base = 0; playing = true; t0 = performance.now(); pp.textContent = 'pause'; if (mu.checked) { au.currentTime = base; au.play().catch(() => { }); } }
    function pause() { base = now(); playing = false; pp.textContent = 'play'; au.pause(); }
    pp.onclick = () => playing ? pause() : play();
    sc.oninput = () => { base = +sc.value; if (playing) { t0 = performance.now(); au.currentTime = base; } draw(base); };
    mu.onchange = () => { if (!mu.checked) au.pause(); else if (playing) { au.currentTime = now(); au.play().catch(() => { }); } };
    addEventListener('keydown', e => { if (e.code === 'Space') { e.preventDefault(); pp.click(); }
      if (e.code === 'ArrowRight') { base = Math.min(DUR, now() + 1 / FPS); if (playing) pause(); draw(base); }
      if (e.code === 'ArrowLeft') { base = Math.max(0, now() - 1 / FPS); if (playing) pause(); draw(base); } });
    (function loop() { const t = now(); if (playing) { draw(t); if (t >= DUR) { pause(); base = DUR; } } requestAnimationFrame(loop); })(); draw(0);
  });
}
