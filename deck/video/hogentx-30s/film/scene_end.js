// ---------- ACT III: proof (blue) ----------
function drawBlueBg(t, cam) {
  g.fillStyle = '#2A5BF7'; g.fill();
  const rg = g.createRadialGradient(700, 380, 0, 700, 380, 1500);
  rg.addColorStop(0, 'rgba(92,134,255,.75)'); rg.addColorStop(1, 'rgba(26,63,209,.0)');
  g.fillStyle = rg; g.fill();
}
// fixed-width digits
function digits(ctx, str, x, y, o) {
  const font = fnt(o.w || 800, o.size), cw = textW('0', font) * (o.cell || 1.0);
  ctx.save(); ctx.font = font; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic'; ctx.fillStyle = o.color;
  ctx.beginPath(); ctx.rect(x - 20, y - o.size * 0.95, cw * str.length + 40, o.size * 1.1); ctx.clip();
  for (let i = 0; i < str.length; i++) {
    const p = o.t === undefined ? 1 : E.outExpo(pr(o.t, i * 0.06, i * 0.06 + 0.8));
    if (p <= 0) continue;
    ctx.globalAlpha = clamp(p * 4) * (o.alpha === undefined ? 1 : o.alpha);
    ctx.fillText(str[i], x + cw * (i + 0.5), y + (1 - p) * o.size);
  }
  ctx.restore();
  return cw * str.length;
}
function drawProof(t, cam) {
  setWorld(cam, 1);
  lattice(cam, 'rgba(255,255,255,.075)', 'rgba(255,255,255,.04)');
  const a = onLine(BOUND[1] - 60), b = onLine(BOUND[2] + 60);
  seg(g, a[0], a[1], b[0], b[1], '#fff', 5, 'butt');
  linePulse(t, 23.4375, 5 * D, C.amber, null);
  const n = node(5);
  if (Math.hypot(n[0] - cam.x, n[1] - cam.y) > 2600) return;
  const τ = t - 20;
  atNode(5, () => {
    const mx = U[0] * -300, my = U[1] * -300, k = spring(τ - 0.1, 3, 0.5);
    circle(g, mx, my, 15 * Math.min(k, 1.5), C.blue); ring(g, mx, my, 15 * Math.min(k, 1.5), '#fff', 6);
    // kicker
    const s = τ - 0.1;
    g.save(); g.globalAlpha = an(s, 0, 0.5); fillPoly(g, towerPts(-820, -330, 13, 28), C.amber); g.restore();
    const P = S.proof, kw = txt(g, P.kicker, -792, -334, { w: 700, size: EN ? 25 : 28, ls: 5, color: C.amber, t: s, st: 0.03 }), kx = -792 + kw + 22;
    g.save(); g.globalAlpha = an(s, 0.1, 0.5) * 0.5; seg(g, kx, -345, kx + 44 * an(s, 0.1, 0.6), -345, '#fff', 2, 'butt'); g.restore();
    txt(g, P.kicker2, kx + 62, -336, { w: 700, size: 21, ls: 4.5, color: 'rgba(255,255,255,.72)', t: s - 0.08, st: 0.008 });
    // number
    const cnt = E.inOutCubic(pr(τ, 1.25, 2.42)), tq = Math.floor(t * FPS + 1e-6) / FPS - 20, val = Math.round(lerp(480, 174, E.inOutCubic(pr(tq, 1.25, 2.42))));
    const wN = digits(g, String(val), -832, -62, { size: 262, color: '#fff', t: s - 0.12 });
    txt(g, P.unit, -832 + wN + 26, -124, { w: 700, size: 56, ls: EN ? -0.5 : 2, color: '#fff', t: s - 0.4, st: 0.05 });
    txt(g, P.per, -832 + wN + 28, -62, { w: 500, size: 38, ls: EN ? 0 : 2, color: 'rgba(255,255,255,.75)', t: s - 0.5, st: 0.05 });
    txt(g, P.label, -820, 6, { w: 500, size: 36, ls: EN ? 0.2 : 2, by: BODY.by, color: 'rgba(255,255,255,.92)', t: s - 0.35, st: EN ? 0.05 : 0.022 });
    // towers: before (ghost) / after (solid)
    const base = 430, tx = 640, tw = 180, hB = 636, hA = 636 * (174 / 480);
    const up = clamp(spring(τ - 0.38, 2.3, 0.75), 0, 1.15);
    if (up > 0) {
      const hNow = lerp(hB, hA, cnt) * up, hG = hB * up;
      const gp = towerPts(tx, base, tw, hG);
      g.save(); g.globalAlpha = an(τ, 1.2, 0.5); fillPoly(g, gp, 'rgba(255,255,255,.13)');
      g.setLineDash([9, 9]); poly(g, gp); g.strokeStyle = 'rgba(255,255,255,.6)'; g.lineWidth = 2; g.stroke(); g.setLineDash([]); g.restore();
      fillPoly(g, towerPts(tx, base, tw, hNow), '#fff');
      seg(g, 30, base + 1, tx + tw + 30, base + 1, 'rgba(255,255,255,.4)', 2, 'butt');
      // labels
      g.save(); g.globalAlpha = an(τ, 0.75, 0.5);
      label(g, P.before, tx - 22, base - hB + 30, { w: 500, size: 25, ls: EN ? 0.5 : 2, color: 'rgba(255,255,255,.75)', align: 'r' });
      label(g, '480', tx - 22, base - hB + 68, { w: 800, size: 34, color: 'rgba(255,255,255,.9)', align: 'r' });
      g.restore();
      g.save(); g.globalAlpha = an(τ, 2.45, 0.5);
      label(g, P.after, tx - 22, base - hA + 30, { w: 500, size: 25, ls: EN ? 0.5 : 2, color: '#fff', align: 'r' });
      label(g, '174', tx - 22, base - hA + 68, { w: 800, size: 34, color: C.amber, align: 'r' });
      g.restore();
    }
    // -64 %
    const hp = E.outExpo(pr(τ, 2.5, 3.2));
    if (hp > 0) {
      g.save(); const sc = lerp(1.5, 1, hp); g.translate(300, 350); g.scale(sc, sc); g.translate(-300, -350);
      g.globalAlpha = clamp(hp * 3);
      label(g, '−64%', 14, 420, { w: 800, size: 192, ls: -4, color: C.amber });
      g.restore();
      txt(g, P.less, 26, 236, { w: 700, size: EN ? 30 : 40, ls: EN ? 5 : 6, color: '#fff', t: τ - 2.62, st: EN ? 0.025 : 0.05 });
      const k2 = pr(τ, 2.5, 3.2); if (k2 < 1) { g.save(); g.globalAlpha = (1 - k2) * 0.5; rr(g, 0 - 60 * k2, 190 - 60 * k2, 520 + 120 * k2, 250 + 120 * k2, 40); g.strokeStyle = C.amber; g.lineWidth = 3; g.stroke(); g.restore(); }
    }
    // footnote
    g.save(); g.globalAlpha = an(τ, 0.7, 0.8, E.outCubic) * 0.72;
    label(g, P.note, -820, 486, { w: 400, size: P.noteSize, ls: EN ? 0.2 : 0.6, color: '#fff' });
    g.restore();
  });
}

// ---------- ACT IV: the line becomes the logo ----------
function drawFinalBg(t, cam) {
  g.fillStyle = '#050A17'; g.fill();
  const rg = g.createRadialGradient(960, 470, 0, 960, 470, 1250);
  rg.addColorStop(0, '#16306A'); rg.addColorStop(0.55, '#0A1733'); rg.addColorStop(1, 'rgba(5,10,23,0)');
  g.fillStyle = rg; g.fill();
}
const LK = [(231 + 845.5) / 2, (934.15 + 623.3) / 2];      // link centre, symbol units
// symbol with per-tower growth (0..1), drawn so the link centre sits at (cx,cy)
function drawSymbol(ctx, cx, cy, k, p, col) {
  ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k); ctx.translate(-LK[0], -LK[1]);
  const band = (x0, lo, hi) => { ctx.beginPath(); ctx.moveTo(x0 - 20, lo - 20 * ROOF); ctx.lineTo(x0 + 260, lo + 260 * ROOF); ctx.lineTo(x0 + 260, hi + 260 * ROOF); ctx.lineTo(x0 - 20, hi - 20 * ROOF); ctx.closePath(); };
  const tw = (key, x0, lo, hi, pp) => { if (pp <= 0) return; ctx.save(); if (pp < 1) { band(x0, lo, hi); ctx.clip(); } fillPoly(ctx, SYM[key], col); ctx.restore(); };
  tw('L', 4, 785 - p.L * 800, 785 + p.L * 480, p.L);
  tw('M', 618, 760 - p.M * 790, 770, p.M);
  tw('R', 845.5, 600, 622 + p.R * 650, p.R);
  if (p.link > 0) fillPoly(ctx, SYM.link, col);
  ctx.restore();
}
let WM_PATHS = null;
function drawFinal(t, cam) {
  if (!WM_PATHS) { WM_PATHS = {}; for (const k in WM_GLYPHS) WM_PATHS[k] = new Path2D(WM_GLYPHS[k].d); }
  setWorld(cam, 1);
  const τ = t - 25;
  const n = node(6);
  const K1 = 0.447, K2 = 0.2396;
  // the line: runs through, then retracts into the link of the symbol
  const half = (688.6 * K1) / 2, ret = E.inOutQuart(pr(τ, 0.62, 1.12));
  const sa = lerp(BOUND[2] - 60 - 6 * D, -half, ret), sb = lerp(3200, half, ret);
  const mv = E.inOutCubic(pr(τ, 1.0, 1.72));
  if (τ < 1.14) {
    const a = onLine(6 * D + sa), b = onLine(6 * D + sb);
    both((c) => seg(c, a[0], a[1], b[0], b[1], c === GL ? rgba('#5E8BFF', 0.9) : rgba('#E6EEFF', 0.95), c === GL ? 9 : lerp(3, 6.9, ret), 'butt'));
  }
  if (Math.hypot(n[0] - cam.x, n[1] - cam.y) > 2600) return;
  atNode(6, () => {
    // symbol
    const k = lerp(K1, K2, mv), cx = lerp(0, -442 + (LK[0] - 538.5) * K2, mv), cy = lerp(0, -240 + (LK[1] - 626) * K2 + 70, mv);
    const p = { L: an(τ, -0.04, 0.8, E.outExpo), M: an(τ, 0.05, 0.8, E.outExpo), R: an(τ, 0.14, 0.8, E.outExpo), link: τ > -0.1 ? 1 : 0 };
    drawSymbol(g, cx, cy, k, p, C.white);
    GL.save(); GL.globalAlpha = lerp(0.75, 0.42, pr(τ, 0.3, 1.6)); drawSymbol(GL, cx, cy, k, p, '#6F96FF'); GL.restore();
    // wordmark
    const WS = 0.27, wx = -243, wy = -240 - 289 * WS + 70;
    const order = ['H', 'o', 'g', 'e', 'n', 't', 'X'];
    for (const c of [g, GL]) {
      c.save(); c.translate(wx, wy); c.scale(WS, WS);
      c.save(); c.beginPath(); c.rect(-40, -60, WM_W + 80, 60 + 592); c.clip();
      for (let i = 0; i < order.length; i++) {
        const q = E.outExpo(pr(τ, 1.48 + i * 0.065, 2.28 + i * 0.065));
        if (q <= 0) continue;
        c.save(); c.translate(0, (1 - q) * 640); c.globalAlpha = (c === GL ? 0.3 : 1) * clamp(q * 3);
        c.fillStyle = c === GL ? '#6F96FF' : C.white; c.fill(WM_PATHS[order[i]], 'evenodd'); c.restore();
      }
      c.restore();
      // the smile draws itself, left to right
      const sm = E.outCubic(pr(τ, 2.12, 2.6));
      if (sm > 0) {
        const bb = WM_GLYPHS.smile.bb, bounce = 1 + 0.12 * Math.sin(Math.PI * pr(τ, 2.3, 2.9));
        c.save(); c.beginPath(); c.rect(bb[0] - 10, bb[1] - 40, (bb[2] - bb[0] + 20) * sm, 220); c.clip();
        c.translate((bb[0] + bb[2]) / 2, bb[1]); c.scale(1, bounce); c.translate(-(bb[0] + bb[2]) / 2, -bb[1]);
        c.globalAlpha = c === GL ? 0.6 : 1; c.fillStyle = mixc(C.amber, C.white, E.inOutCubic(pr(τ, 2.9, 3.5))); c.fill(WM_PATHS.smile, 'evenodd'); c.restore();
      }
      c.restore();
    }
    // glint across the lockup
    const gp = pr(τ, 3.35, 4.25);
    if (gp > 0 && gp < 1) {
      const gx = lerp(-900, 900, E.inOutCubic(gp));
      GL.save(); GL.beginPath(); GL.moveTo(gx - 60, -500); GL.lineTo(gx + 60, -500); GL.lineTo(gx + 60 + 500 * 0.6, 300); GL.lineTo(gx - 60 + 500 * 0.6, 300); GL.closePath(); GL.clip();
      GL.globalAlpha = Math.sin(Math.PI * gp);
      drawSymbol(GL, cx, cy, k, { L: 1, M: 1, R: 1, link: 1 }, '#fff');
      GL.translate(wx, wy); GL.scale(WS, WS); GL.fillStyle = '#fff'; for (const o of order) GL.fill(WM_PATHS[o], 'evenodd');
      GL.restore();
    }
    // tagline
    const Z = S.end;
    txt(g, Z.tag, 0, 130, { w: 700, size: Z.tagSize, ls: Z.tagLs, by: BODY.by, color: C.white, align: 'c', t: τ - 2.47, st: Z.tagSt, d: 0.9 });
    // descriptor + url
    const f1 = fnt(500, 28), s1 = Z.desc, s2 = Z.url, dls = EN ? 0.6 : 3;
    const w1 = textW(s1, f1, dls), w2 = textW(s2, fnt(700, 28), 2.5), tot = w1 + 64 + w2, x0 = -tot / 2;
    txt(g, s1, x0, 212, { w: 500, size: 28, ls: dls, by: BODY.by, color: 'rgba(214,224,255,.78)', t: τ - 3.0, st: EN ? 0.05 : 0.016, d: 0.7 });
    g.save(); g.globalAlpha = an(τ, 3.2, 0.5); fillPoly(g, towerPts(x0 + w1 + 28, 214, 7, 26), C.amber); g.restore();
    txt(g, s2, x0 + w1 + 64, 212, { w: 700, size: 28, ls: 2.5, color: C.white, t: τ - 3.22, st: 0.02, d: 0.7 });
  });
}
