// ---------- HogentX logo film: nothing but the logo's own parts ----------
// 0-5   the mark comes apart: towers -> line -> point -> line (26.8 deg)
// 5-10  the line raises three towers (33.2 deg roofs; 26.8 + 33.2 = 60)
// 10-15 one becomes many (pattern)
// 15-20 rhythm: towers as an equaliser driven by the soundtrack, then they find the line
// 20-25 light: a day turns into night, every room lights up
// 25-30 lockup
const HK = 0.52, HCX = 960, HCY = 520;                         // hero symbol: scale + bbox centre on screen
const hp = (p) => [HCX + (p[0] - 538.5) * HK, HCY + (p[1] - 623.5) * HK];
const LKC = [(231 + 845.5) / 2, (934.15 + 623.3) / 2];         // link centre (symbol units)
const PC = hp(LKC);                                            // the point everything starts from
const HP = { L: SYM.L.map(hp), M: SYM.M.map(hp), R: SYM.R.map(hp), link: SYM.link.map(hp) };
const GROUNDY = hp([0, 1247])[1];
const MONO = '"JetBrains Mono","DejaVu Sans Mono",monospace';
const lineYs = (x) => PC[1] + (x - PC[0]) * LINK;              // the link line on screen (z = 1)
const DEG = Math.PI / 180, A_LINK = Math.atan(-LINK), A_ROOF = Math.atan(ROOF);

// ---------- camera ----------
const ZT = { out0: 9.62, out1: 10.55, in0: 14.5, in1: 14.93 };
const ZP = 0.36, ZPE = ZP * 0.86;                               // pattern zoom: after the pull-back, and just before the dive
const LTW = hp([117.5, 623.5]);                                 // centre of the hero's left tower (zoom-in target)
function cameraAt(t) {
  let z = 1, x = 960, y = 540;
  if (t < ZT.out0) z = 1 + 0.03 * (t / 5) + 0.035 * E.inOutSine(pr(t, 5, 9.6));
  else if (t < ZT.in0) {
    const z0 = 1.03 + 0.035, p = whip(pr(t, ZT.out0, ZT.out1), 0.4);
    z = z0 * Math.pow(ZP / z0, p) * (1 - 0.14 * pr(t, ZT.out1, ZT.in0));
    const d = 60 * pr(t, 10, ZT.in0);
    x += U[0] * d * 5; y += U[1] * d * 5;
  } else if (t < ZT.in1) {
    const zs = ZPE, p = pr(t, ZT.in0, ZT.in1), e = E.inCubic(p);
    z = zs * Math.pow(40 / zs, e);
    const m = 1 - Math.pow(1 - p, 3);                           // centre moves early so the tower is centred before it fills
    x = lerp(960 + U[0] * 300, LTW[0], m); y = lerp(540 + U[1] * 300, LTW[1], m);
  } else if (t < 15.0) { z = 40; x = LTW[0]; y = LTW[1]; }
  else if (t >= 26) z = 1 + 0.03 * E.inOutSine(pr(t, 26, 30));
  // impacts
  const sh = (t0, amp, f = 62) => { const d = t - t0; if (d < 0 || d > 0.6) return; const e = amp * Math.exp(-d * 9); x += e * Math.sin(d * f); y += e * Math.cos(d * f * 1.31); };
  sh(5.0, 7); sh(25.0, 6);
  return { x, y, z };
}
function setCam(c) {
  const tx = W / 2 - c.x * c.z, ty = H / 2 - c.y * c.z;
  g.setTransform(c.z, 0, 0, c.z, tx, ty); GL.setTransform(c.z * GS, 0, 0, c.z * GS, tx * GS, ty * GS);
}
const FRAME = {
  look(t) {
    const L = (a, b, p) => ({ vig: lerp(a.vig, b.vig, p), grain: lerp(a.grain, b.grain, p) });
    const N = { vig: 0.4, grain: 2.0 }, B = { vig: 0.22, grain: 1.5 }, P = { vig: 0.08, grain: 1.2 };
    if (t < 9.8) return N;
    if (t < 10.3) return L(N, B, pr(t, 9.8, 10.3));
    if (t < 14.8) return B;
    if (t < 15.1) return L(B, P, pr(t, 14.8, 15.1));
    if (t < 21.6) return P;
    if (t < 23.0) return L(P, N, pr(t, 21.6, 23.0));
    return N;
  },
  baseSamples(t) { return 5; },
};

// ---------- small helpers ----------
function dashed(ctx, x1, y1, x2, y2, col, lw = 1.5, dash = [8, 8]) {
  ctx.save(); ctx.setLineDash(dash); ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
  ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'butt'; ctx.stroke(); ctx.restore();
}
// trace a closed polygon's outline up to fraction p of its perimeter
function tracePoly(ctx, pts, p) {
  const n = pts.length, len = [];
  let tot = 0;
  for (let i = 0; i < n; i++) { const a = pts[i], b = pts[(i + 1) % n]; const l = Math.hypot(b[0] - a[0], b[1] - a[1]); len.push(l); tot += l; }
  let rem = tot * clamp(p);
  ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 0; i < n && rem > 0; i++) {
    const a = pts[i], b = pts[(i + 1) % n], k = Math.min(1, rem / len[i]);
    ctx.lineTo(a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k); rem -= len[i];
  }
}
// growth band for one tower (symbol units), edges parallel to the roof
function bandClip(ctx, key, p) {
  let x0, lo, hi;
  if (key === 'L') { x0 = 4; lo = 785 - p * 800; hi = 785 + p * 480; }
  else if (key === 'M') { x0 = 618; lo = 760 - p * 790; hi = 770; }
  else { x0 = 845.5; lo = 600; hi = 622 + p * 650; }
  const a = hp([x0 - 20, lo - 20 * ROOF]), b = hp([x0 + 260, lo + 260 * ROOF]), c = hp([x0 + 260, hi + 260 * ROOF]), d = hp([x0 - 20, hi - 20 * ROOF]);
  ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.lineTo(c[0], c[1]); ctx.lineTo(d[0], d[1]); ctx.closePath();
}
function towerFill(key, p, col, glowCol, glowA = 0.5) {
  if (p <= 0) return;
  for (const c of [g, GL]) {
    if (c === GL && !glowCol) continue;
    c.save(); if (p < 1) { bandClip(c, key, p); c.clip(); }
    if (c === GL) c.globalAlpha *= glowA;
    fillPoly(c, HP[key], c === GL ? glowCol : col); c.restore();
  }
}
function angleArc(ctx, cx, cy, r, a0, a1, p, col, lw = 2) {      // canvas angles (clockwise positive)
  if (p <= 0) return;
  const a = lerp(a0, a1, p);
  ctx.beginPath(); ctx.arc(cx, cy, r, Math.min(a0, a), Math.max(a0, a)); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.lineCap = 'round'; ctx.stroke();
}
function mono(ctx, s, x, y, size, col, a = 1, align = 'left') {
  ctx.save(); ctx.font = `500 ${size}px ${MONO}`; ctx.fillStyle = col; ctx.globalAlpha *= a; ctx.textAlign = align; ctx.textBaseline = 'middle'; ctx.fillText(s, x, y); ctx.restore();
}
// caption: index + sentence, bottom left (screen space)
function caption(t, t0, t1, idx, text, col, colIdx = C.amber) {
  if (t < t0 || t > t1 + 0.7) return;
  const s = t - t0, o = t1 - t0;
  // centred group: index, rule, sentence
  const tw = textW(text, fnt(700, 58), -1.4), x0 = 960 - (132 + tw) / 2;
  txt(g, '0' + idx, x0, 964, { w: 800, size: 30, ls: 2, color: colIdx, t: s, st: 0.04, out: o });
  g.save(); g.globalAlpha = an(s, 0.05, 0.5) * (1 - pr(t, t1, t1 + 0.3)) * 0.55; seg(g, x0 + 60, 953, x0 + 60 + 48 * an(s, 0.05, 0.6), 953, col, 2.5, 'butt'); g.restore();
  txt(g, text, x0 + 132, 968, { w: 700, size: 58, ls: -1.4, by: 'word', color: col, t: s - 0.08, st: 0.075, d: 0.8, out: o + 0.04, sto: 0.03 });
}
function bgNavy() {
  g.fillStyle = '#050A17'; g.fillRect(-80, -80, W + 160, H + 160);
  const rg = g.createRadialGradient(960, 500, 0, 960, 500, 1250);
  rg.addColorStop(0, '#16306A'); rg.addColorStop(0.55, '#0A1733'); rg.addColorStop(1, 'rgba(5,10,23,0)');
  g.fillStyle = rg; g.fillRect(-80, -80, W + 160, H + 160);
}
function bgBlue(a) {
  g.save(); g.globalAlpha = a; g.fillStyle = '#2A5BF7'; g.fillRect(0, 0, W, H);
  const rg = g.createRadialGradient(960, 480, 0, 960, 480, 1400);
  rg.addColorStop(0, 'rgba(92,134,255,.75)'); rg.addColorStop(1, 'rgba(26,63,209,0)');
  g.fillStyle = rg; g.fillRect(0, 0, W, H); g.restore();
}
function bgPaper() {
  g.fillStyle = C.paper; g.fillRect(-80, -80, W + 160, H + 160);
  const rg = g.createRadialGradient(700, 300, 0, 700, 300, 1300);
  rg.addColorStop(0, 'rgba(255,255,255,.9)'); rg.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = rg; g.fillRect(-80, -80, W + 160, H + 160);
}
// faint construction lattice in the two logo directions, through the point
function latticeScreen(aLink, aRoof, col) {
  const sp = 150;
  g.save(); g.lineWidth = 1.2; g.lineCap = 'butt';
  if (aLink > 0) {
    g.strokeStyle = rgba(col, aLink); g.beginPath();
    for (let k = -14; k <= 14; k++) { if (k === 0) continue; const ox = PC[0] - U[1] * k * sp, oy = PC[1] + U[0] * k * sp; g.moveTo(ox - U[0] * 2600, oy - U[1] * 2600); g.lineTo(ox + U[0] * 2600, oy + U[1] * 2600); }
    g.stroke();
  }
  if (aRoof > 0) {
    g.strokeStyle = rgba(col, aRoof); g.beginPath();
    for (let k = -14; k <= 14; k++) { const ox = PC[0] + NV0[0] * k * sp, oy = PC[1] + NV0[1] * k * sp; g.moveTo(ox - RV[0] * 2600, oy - RV[1] * 2600); g.lineTo(ox + RV[0] * 2600, oy + RV[1] * 2600); }
    g.stroke();
  }
  g.restore();
}
const NV0 = [RV[1], -RV[0]];

// ================= ACT 1 + 2: apart, then built again =================
function actBuild(t) {
  const sky = '#A9C1FF';
  const lf = 1 - pr(t, 8.9, 9.5);
  latticeScreen(0.05 * an(t, 2.6, 0.9, E.outCubic) * lf, 0.045 * an(t, 5.0, 0.9, E.outCubic) * lf, '#8FB0FF');
  // ---- the line ----
  const A = hp([231, 934.15]), B = hp([845.5, 623.3]);
  const con = E.inOutQuart(pr(t, 1.3, 1.875));                          // link contracts to the point
  const shoot = E.outExpo(pr(t, 2.5, 3.15));                             // then the line shoots out
  if (t < 2.5) {
    const a = [lerp(A[0], PC[0], con), lerp(A[1], PC[1], con)], b = [lerp(B[0], PC[0], con), lerp(B[1], PC[1], con)];
    both((c) => seg(c, a[0], a[1], b[0], b[1], c === GL ? '#6F96FF' : C.white, c === GL ? 16 : 8, 'butt'), 0.8);
  } else {
    const Ls = lerp(2600 * shoot, 179, E.inOutQuart(pr(t, 8.75, 9.4)));
    both((c) => seg(c, PC[0] - U[0] * Ls, PC[1] - U[1] * Ls, PC[0] + U[0] * Ls, PC[1] + U[1] * Ls, c === GL ? rgba('#5E8BFF', 0.9) : rgba('#DCE7FF', 0.85), c === GL ? 9 : 2.6, 'butt'));
    // ruler ticks
    const ta = (1 - pr(t, 5.0, 5.5)) * 0.55;
    if (ta > 0) {
      g.save(); g.strokeStyle = rgba('#DCE7FF', ta); g.lineWidth = 1.5; g.beginPath();
      for (let n = -22; n <= 22; n++) {
        if (n === 0) continue; const s = n * 80; if (Math.abs(s) > Ls) continue;
        const k = clamp(spring(t - 2.5 - Math.abs(n) * 0.022, 4, 0.5), 0, 1.3), l = (n % 5 === 0 ? 16 : 9) * k;
        const x = PC[0] + U[0] * s, y = PC[1] + U[1] * s;
        g.moveTo(x + U[1] * l, y - U[0] * l); g.lineTo(x - U[1] * l, y + U[0] * l);
      }
      g.stroke(); g.restore();
    }
    // link at logo weight once the towers are filled
    if (t > 6.6) { const lk = pr(t, 6.6, 7.2); g.save(); g.globalAlpha = lk; fillPoly(g, HP.link, C.white); g.restore(); GL.save(); GL.globalAlpha = lk * 0.7; fillPoly(GL, HP.link, '#8FB0FF'); GL.restore(); }
  }
  // ---- the point ----
  if (t > 1.6 && t < 6.8) {
    const k = 1 + 0.9 * Math.exp(-Math.max(0, t - 1.875) * 7) * (t > 1.875 ? 1 : 0) + 0.7 * Math.exp(-Math.max(0, t - 2.5) * 7) * (t > 2.5 ? 1 : 0);
    const a = pr(t, 1.6, 1.875) * (1 - pr(t, 6.3, 6.8));
    both((c) => { c.save(); c.globalAlpha *= a; circle(c, PC[0], PC[1], (c === GL ? 26 : 7) * k, c === GL ? '#8FB0FF' : '#fff'); c.restore(); });
    for (const t0 of [1.875, 2.5]) { const rp = pr(t, t0, t0 + 0.8); if (rp > 0 && rp < 1) { g.save(); g.globalAlpha = (1 - rp) * 0.6; ring(g, PC[0], PC[1], 12 + 120 * E.outCubic(rp), '#DCE7FF', 2); g.restore(); } }
  }
  // ---- angle of the line: 26.8 ----
  const fa = 1 - pr(t, 5.0, 5.45);
  if (t > 2.9 && fa > 0) {
    g.save(); g.globalAlpha = fa;
    const bl = 520 * an(t, 2.9, 0.6);
    dashed(g, PC[0], PC[1], PC[0] + bl, PC[1], rgba(sky, 0.7));
    angleArc(g, PC[0], PC[1], 330, 0, -A_LINK, an(t, 3.15, 0.7, E.inOutCubic), sky, 2.2);
    const la = an(t, 3.6, 0.5, E.outCubic);
    mono(g, '26.8°', PC[0] + 366 * Math.cos(-A_LINK / 2), PC[1] + 366 * Math.sin(-A_LINK / 2) + (1 - la) * 10, 34, sky, la);
    g.restore();
  }
  // ---- deconstruction (0 - 1.35) ----
  if (t < 1.4) {
    towerFill('R', 1 - E.inOutCubic(pr(t, 0.5, 1.05)), C.white, '#6F96FF', 0.42);
    towerFill('M', 1 - E.inOutCubic(pr(t, 0.65, 1.2)), C.white, '#6F96FF', 0.42);
    towerFill('L', 1 - E.inOutCubic(pr(t, 0.8, 1.35)), C.white, '#6F96FF', 0.42);
  }
  // ---- construction (5.0 - 7.4) ----
  if (t >= 5.0) {
    const gfade = 1 - pr(t, 7.7, 8.5);
    // vertical guides shoot out of the line
    if (gfade > 0) {
      const xs = [4, 231, 618, 845.5, 1073];
      xs.forEach((sx, i) => {
        const p = E.outExpo(pr(t, 5.0 + i * 0.035, 5.5 + i * 0.035)); if (p <= 0) return;
        const x = hp([sx, 0])[0], y = lineYs(x);
        dashed(g, x, y - 1200 * p, x, y + 1200 * p, rgba(sky, 0.26 * gfade), 1.3, [6, 9]);
      });
      // roof guides
      for (const k of ['L', 'M', 'R']) {
        const p = E.outExpo(pr(t, 5.65, 6.3)); if (p <= 0) break;
        const v = HP[k][0];
        dashed(g, v[0] - RV[0] * 1500 * p, v[1] - RV[1] * 1500 * p, v[0] + RV[0] * 1500 * p, v[1] + RV[1] * 1500 * p, rgba(sky, 0.2 * gfade), 1.3, [6, 9]);
      }
    }
    // outlines traced from where each tower meets the line
    const tr = [['L', 0, 5.3], ['M', 0, 5.45], ['R', 0, 5.6]];
    const ord = { L: [HP.L[2], HP.L[1], HP.L[0], HP.L[3]], M: [HP.M[3], HP.M[0], HP.M[1], HP.M[2]], R: [HP.R[0], HP.R[1], HP.R[2], HP.R[3]] };
    const oa = 1 - pr(t, 6.9, 7.5);
    if (oa > 0) for (const [k, , t0] of tr) {
      const p = E.inOutCubic(pr(t, t0, t0 + 0.85)); if (p <= 0) continue;
      both((c) => { c.save(); c.globalAlpha *= oa; tracePoly(c, ord[k], p); c.strokeStyle = c === GL ? '#6F96FF' : '#fff'; c.lineWidth = c === GL ? 7 : 2.6; c.lineJoin = 'miter'; c.lineCap = 'butt'; c.stroke(); c.restore(); }, 0.8);
    }
    // 33.2 + 26.8 = 60, read off the corner where line and roof meet
    const Q = HP.R[0], af = an(t, 6.0, 0.4) * (1 - pr(t, 8.0, 8.6));
    if (af > 0) {
      g.save(); g.globalAlpha = af;
      dashed(g, Q[0], Q[1], Q[0] + 330 * an(t, 6.0, 0.6), Q[1], rgba(sky, 0.7));
      dashed(g, Q[0], Q[1], Q[0] + U[0] * 330 * an(t, 6.0, 0.6), Q[1] + U[1] * 330 * an(t, 6.0, 0.6), rgba(sky, 0.7));
      angleArc(g, Q[0], Q[1], 150, 0, A_ROOF, an(t, 6.15, 0.6, E.inOutCubic), sky, 2.2);
      angleArc(g, Q[0], Q[1], 150, 0, -A_LINK, an(t, 6.3, 0.6, E.inOutCubic), sky, 2.2);
      const l1 = an(t, 6.5, 0.45, E.outCubic), l2 = an(t, 6.65, 0.45, E.outCubic), l3 = an(t, 7.0, 0.5, E.outCubic);
      mono(g, '33.2°', Q[0] + 180 * Math.cos(A_ROOF / 2) - 2, Q[1] + 180 * Math.sin(A_ROOF / 2) + 2, 28, sky, l1);
      mono(g, '26.8°', Q[0] + 180 * Math.cos(-A_LINK / 2) - 2, Q[1] + 180 * Math.sin(-A_LINK / 2) - 2, 28, sky, l2);
      angleArc(g, Q[0], Q[1], 310, -A_LINK, A_ROOF, an(t, 6.85, 0.7, E.inOutCubic), C.amber, 3);
      mono(g, '60°', Q[0] + 340, Q[1] + 4, 40, C.amber, l3);
      g.restore();
    }
    // fills grow away from the line
    const ga = 0.5 + (t > 7.5 ? 0.5 * Math.exp(-(t - 7.5) * 4) : 0);            // the finished mark flares once, on the beat
    towerFill('L', E.outQuart(pr(t, 6.5, 7.25)), C.white, '#6F96FF', ga);
    towerFill('M', E.outQuart(pr(t, 6.6, 7.35)), C.white, '#6F96FF', ga);
    towerFill('R', E.outQuart(pr(t, 6.7, 7.45)), C.white, '#6F96FF', ga);
  }
}

// ================= ACT 3: one becomes many =================
const DX = 1077 * HK * 1.6, DY = 1252 * HK * 1.34;
const CELLS = (() => { const a = []; for (let j = -6; j <= 6; j++) for (let i = -9; i <= 9; i++) { if (i === 0 && j === 0) continue; const x = HCX + i * DX + (j & 1 ? DX / 2 : 0), y = HCY + j * DY; a.push({ x, y, d: Math.hypot(x - HCX, y - HCY), pj: (x - HCX) * U[0] + (y - HCY) * U[1] }); } return a.sort((p, q) => p.d - q.d); })();
function symAt(ctx, x, y, s, col) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s, s); ctx.translate(-HCX, -HCY);
  ctx.fillStyle = col; ctx.beginPath();
  for (const k of ['L', 'M', 'R', 'link']) { const p = HP[k]; ctx.moveTo(p[0][0], p[0][1]); for (let i = 1; i < 4; i++) ctx.lineTo(p[i][0], p[i][1]); ctx.closePath(); }
  ctx.fill(); ctx.restore();
}
const WAVES = [10.625, 11.875, 13.125];
function waveAmt(pj, t) {
  let a = 0;
  for (const tw of WAVES) { const f = -4400 + 8800 * pr(t, tw, tw + 1.35); const d = (pj - f) / 520; a = Math.max(a, Math.exp(-d * d)); }
  return a;
}
function actMany(t, cam) {
  const vis = 1100 / cam.z + 800;
  for (const c of CELLS) {
    if (Math.abs(c.x - cam.x) > vis * 1.05 || Math.abs(c.y - cam.y) > vis * 0.62) continue;
    const s0 = clamp(spring(t - 9.74 - c.d / 16000, 2.2, 0.7), 0, 1.15); if (s0 <= 0) continue;
    const s = lerp(0.74, 1, s0), a = waveAmt(c.pj, t);
    g.globalAlpha = clamp(s0 * 3);
    symAt(g, c.x, c.y - a * 70, s * (1 + 0.14 * a), a > 0.02 ? mixc(C.white, C.amber, clamp(a * 1.2)) : C.white);
    g.globalAlpha = 1;
  }
  // the original
  const a0 = waveAmt(0, t);
  symAt(g, HCX, HCY - a0 * 70, 1 + 0.14 * a0, a0 > 0.02 ? mixc(C.white, C.amber, clamp(a0 * 1.2)) : C.white);
  if (t < 10.4) { GL.save(); GL.globalAlpha = 0.5 * (1 - pr(t, 9.7, 10.4)); for (const k of ['L', 'M', 'R']) fillPoly(GL, HP[k], '#6F96FF'); GL.restore(); }
}

// ================= ACT 4: rhythm =================
const NB = 13, BW = 76, BP = 104, BX0 = 298, BASE4 = 880;
const bx = (i) => BX0 + i * BP;
function barPts(x, base, w, h) {
  if (h >= w * ROOF) return towerPts(x, base, w, h);
  const hh = Math.max(0, h); return [[x, base - hh], [x + hh / ROOF, base], [x + hh / ROOF, base], [x, base]];
}
const lineTop = (i) => 800 - (-LINK) * (bx(i) - BX0);              // tops when every bar meets the line
const HSEL = { 4: 'L', 7: 'M', 8: 'R' };
function bandAmp(i, t) {
  if (typeof BANDS === 'undefined') return 0.45 + 0.4 * Math.sin(t * (5 + i * 0.7) + i);
  // one value per video frame: the bars step crisply like a real equaliser instead of smearing
  const f0 = clamp(Math.floor(t * 60 + 1e-6) - BANDS_F0, 0, BANDS.length - 1);
  return BANDS[f0][i];
}
function actRhythm(t) {
  const settle = (i) => E.inOutCubic(pr(t, 18.55 + i * 0.022, 19.2 + i * 0.022));
  const morph = E.inOutCubic(pr(t, 19.38, 20.0));
  const tops = [];
  // baseline -> ground of the mark
  const by = lerp(BASE4, GROUNDY, morph);
  g.save(); g.globalAlpha = an(t, 15.05, 0.5); seg(g, 960 - 900 * an(t, 15.05, 0.9), by + 1, 960 + 900 * an(t, 15.05, 0.9), by + 1, rgba(C.navy, 0.2), 2, 'butt'); g.restore();
  for (let i = 0; i < NB; i++) {
    const rise = clamp(spring(t - 15.02 - Math.abs(i - 6) * 0.035, 2.3, 0.7), 0, 1.2);
    const live = 130 + 620 * bandAmp(i, t), tgt = BASE4 - lineTop(i);
    let h = lerp(live, tgt, settle(i)) * rise;
    const x = bx(i);
    let pts = barPts(x, BASE4, BW, h);
    tops.push([x, BASE4 - h]);
    if (morph > 0) {
      if (HSEL[i]) { const T = HP[HSEL[i]]; pts = pts.map((p, k) => [lerp(p[0], T[k][0], morph), lerp(p[1], T[k][1], morph)]); }
      else { const dy = 900 * E.inCubic(pr(t, 19.38 + Math.abs(i - 6) * 0.012, 19.95)), lift = by - BASE4; pts = pts.map((p) => [p[0], Math.min(by + 1, p[1] + dy + lift)]); if (dy > h + 4) continue; }   // sink into the moving ground line
    }
    fillPoly(g, pts, C.navy);
  }
  // the line through every roof corner
  const lp = an(t, 15.3, 0.6);
  if (lp > 0 && morph < 1) {
    const s = pr(t, 18.55, 19.45), ext = 1500 * E.outExpo(pr(t, 19.0, 19.5));
    g.save(); g.globalAlpha = lp;
    // as the bars become the mark, the line slides onto the link
    const off = [lerp(0, hp([231, 934.15])[0] - (BX0 + (hp([231, 934.15])[1] - 800) / LINK), morph), 0];
    g.beginPath();
    const p0 = tops[0], pn = tops[NB - 1];
    g.moveTo(p0[0] - U[0] * ext + off[0], p0[1] - U[1] * ext);
    for (const p of tops) g.lineTo(p[0] + off[0], p[1]);
    g.lineTo(pn[0] + U[0] * ext + off[0], pn[1] + U[1] * ext);
    g.strokeStyle = C.blue; g.lineWidth = 5; g.lineJoin = 'round'; g.lineCap = 'butt'; g.stroke();
    const da = 1 - pr(t, 19.3, 19.6);
    if (da > 0) for (const p of tops) { g.globalAlpha = lp * da; circle(g, p[0], p[1], 8, '#fff'); ring(g, p[0], p[1], 8, C.blue, 4); }
    g.restore();
  }
}

// ================= ACT 5: light =================
const WINS = (() => {
  const r = rng(77), out = [];
  const cw = 28, ch = 34, gx = 18, gy = 24, m = 27, top = 48;
  for (const k of ['L', 'M', 'R']) {
    const P = SYM[k], x0 = P[0][0], w = P[1][0] - P[0][0], yTop = P[0][1];
    const cols = Math.floor((w - 2 * m + gx) / (cw + gx)), tot = cols * cw + (cols - 1) * gx, xo = (w - tot) / 2;
    for (let row = 0; ; row++) {
      const yr = top + row * (ch + gy);
      const bottomAt = (wx) => (k === 'M' ? 746.9 + (wx / w) * (631.7 - 746.9) - yTop : 1247 - yTop);
      if (yr + ROOF * w + ch > bottomAt(w) - 24 && k !== 'M') break;
      if (k === 'M' && yr > 760) break;
      for (let c = 0; c < cols; c++) {
        const wx = xo + c * (cw + gx), y = yr + ROOF * wx;
        if (y + ch > bottomAt(wx + cw) - 20) continue;
        out.push({ p: [[x0 + wx, yTop + y], [x0 + wx + cw, yTop + y + cw * ROOF], [x0 + wx + cw, yTop + y + cw * ROOF + ch], [x0 + wx, yTop + y + ch]].map(hp), rank: r(), tone: Math.floor(r() * 3), keep: r() });
      }
    }
  }
  out.sort((a, b) => a.rank - b.rank); out.forEach((w, i) => { w.on = 22.45 + 1.85 * Math.pow(i / out.length, 0.72); });
  return out;
})();
const STARS5 = (() => { const r = rng(5), a = []; for (let i = 0; i < 120; i++) a.push({ x: r() * W, y: r() * 760, s: 0.6 + r() * 1.3, ph: r() * 6.28, f: 0.6 + r() * 1.8 }); return a; })();
const AMB5 = ['#FFC46B', '#FFD489', '#FFB24A'];
const SKY = [
  [0.0, '#F3F6FC', '#F3F6FC', '#F3F6FC'],
  [0.4, '#E4ECFF', '#F6F1EA', '#FFE9C9'],
  [0.68, '#8C9BE0', '#F3B88E', '#FFC27A'],
  [0.86, '#1E2C66', '#7A4E79', '#E98A5E'],
  [1.0, '#040915', '#081530', '#0E2250'],
];
function skyCols(p) {
  let i = 0; while (i < SKY.length - 2 && p > SKY[i + 1][0]) i++;
  const a = SKY[i], b = SKY[i + 1], u = clamp((p - a[0]) / (b[0] - a[0]));
  return [1, 2, 3].map((k) => mixc(a[k], b[k], u));
}
const GND = [[0.0, '#E7ECF6', '#F3F6FC'], [0.4, '#E6E0D8', '#EEE8E0'], [0.68, '#C99B7A', '#B58A72'], [0.86, '#4B3857', '#2A2140'], [1.0, '#081329', '#040915']];
function gndCols(p) {
  let i = 0; while (i < GND.length - 2 && p > GND[i + 1][0]) i++;
  const a = GND[i], b = GND[i + 1], u = clamp((p - a[0]) / (b[0] - a[0]));
  return [mixc(a[1], b[1], u), mixc(a[2], b[2], u)];
}
function actLight(t) {
  const night = pr(t, 20.35, 22.95);                    // 0 day .. 1 night
  const charge = [E.outQuart(pr(t, 25.0, 25.55)), E.outQuart(pr(t, 25.06, 25.6)), E.outQuart(pr(t, 25.12, 25.66))];
  // sky
  const sc = skyCols(night), sg = g.createLinearGradient(0, 0, 0, GROUNDY);
  sg.addColorStop(0, sc[0]); sg.addColorStop(0.62, sc[1]); sg.addColorStop(1, sc[2]);
  bgPaper();
  g.save(); g.globalAlpha = clamp(night * 7); g.fillStyle = sg; g.fillRect(-80, -80, W + 160, GROUNDY + 80); g.restore();
  if (t >= 25) { g.save(); g.globalAlpha = E.outCubic(pr(t, 25.0, 26.2)); bgNavy(); g.restore(); }
  // stars
  const sa = pr(night, 0.82, 1);
  if (sa > 0) for (const s of STARS5) circle(g, s.x, s.y, s.s, rgba('#CFE0FF', sa * (0.25 + 0.3 * (0.5 + 0.5 * Math.sin(t * s.f + s.ph)))));
  // sun: an arc from upper left, down behind the towers, to the horizon on the right
  const sp = pr(t, 20.2, 22.75), th = lerp(152, -14, sp * sp * (3 - 2 * sp) * 0.5 + sp * 0.5) * DEG;
  const sx = 960 + 820 * Math.cos(th), sy = GROUNDY - 650 * Math.sin(th), sr = 74;
  const sv = an(t, 20.15, 0.6);
  if (sv > 0 && sy - sr < GROUNDY + 300) {
    g.save(); g.beginPath(); g.rect(-80, -80, W + 160, GROUNDY + 80); g.clip(); g.globalAlpha = sv * (1 - pr(t, 22.9, 24.3));
    const warm = pr(night, 0.2, 0.8);
    const gl = g.createRadialGradient(sx, sy, sr * 0.5, sx, sy, lerp(380, 760, warm));
    gl.addColorStop(0, rgba(mixc('#FFD27A', '#FF9A4A', warm).match(/\d+/g).slice(0, 3).map(Number), lerp(0.5, 0.75, warm))); gl.addColorStop(1, rgba('#FFB24A', 0));
    g.fillStyle = gl; g.fillRect(-80, -80, W + 160, GROUNDY + 80);
    const dg = g.createLinearGradient(0, sy - sr, 0, sy + sr); dg.addColorStop(0, mixc('#FFD98A', '#FFB45C', warm)); dg.addColorStop(1, mixc('#FFB03B', '#FF7A3D', warm));
    circle(g, sx, sy, sr, dg);
    g.restore();
  }
  // ground + horizon
  const gcs = gndCols(night);
  const gg = g.createLinearGradient(0, GROUNDY, 0, H); gg.addColorStop(0, gcs[0]); gg.addColorStop(1, gcs[1]);
  const hl = an(t, 20.0, 0.9), gf = 1 - E.outCubic(pr(t, 25.25, 26.0));
  g.save(); g.globalAlpha = hl * gf; g.fillStyle = gg; g.fillRect(-80, GROUNDY, W + 160, H - GROUNDY + 80);
  g.globalAlpha = gf;
  seg(g, -80, GROUNDY, W + 80, GROUNDY, mixc('#10213A', '#8FB0FF', night, lerp(0.22, 0.3, night)), 1.6, 'butt');
  g.restore();
  // the line retracts into the link (20.0 - 20.55)
  const ret = E.inOutQuart(pr(t, 20.0, 20.55));
  if (ret < 1) {
    const A = hp([231, 934.15]), B = hp([845.5, 623.3]), ext = 1500 * (1 - ret);
    g.save(); g.globalAlpha = 1 - pr(t, 20.4, 20.55); seg(g, A[0] - U[0] * ext, A[1] - U[1] * ext, B[0] + U[0] * ext, B[1] + U[1] * ext, C.blue, 5, 'butt'); g.restore();
  }
  // towers
  const keys = ['L', 'M', 'R'];
  for (let i = 0; i < 3; i++) {
    const P = HP[keys[i]];
    const fg = g.createLinearGradient(0, P[0][1], 0, P[2][1]);
    fg.addColorStop(0, mixc('#10213A', '#1B3570', night)); fg.addColorStop(1, mixc('#10213A', '#0F2148', night));
    fillPoly(g, P, fg);
    if (night > 0.3) { g.save(); g.globalAlpha = pr(night, 0.3, 1) * 0.55; g.beginPath(); g.moveTo(P[3][0] + 0.7, P[3][1]); g.lineTo(P[0][0] + 0.7, P[0][1] + 0.7); g.lineTo(P[1][0], P[1][1] + 0.7); g.strokeStyle = '#8FB0FF'; g.lineWidth = 1.6; g.stroke(); g.restore(); }
  }
  // link
  fillPoly(g, HP.link, mixc('#10213A', '#DCE7FF', pr(night, 0.4, 1)));
  if (night > 0.6) { GL.save(); GL.globalAlpha = pr(night, 0.6, 1) * 0.6; fillPoly(GL, HP.link, '#6F96FF'); GL.restore(); }
  // windows
  const wa = pr(night, 0.45, 0.8);
  if (wa > 0 && charge[2] < 1) {
    const dark = new Path2D(), lit = [new Path2D(), new Path2D(), new Path2D()];
    for (const w of WINS) {
      const f = t - w.on, P = w.p;
      const add = (pa) => { pa.moveTo(P[0][0], P[0][1]); pa.lineTo(P[1][0], P[1][1]); pa.lineTo(P[2][0], P[2][1]); pa.lineTo(P[3][0], P[3][1]); pa.closePath(); };
      if (f < 0) add(dark);
      else if (f < 0.3) { const b = f < 0.04 ? 0.75 : f < 0.09 ? 0.25 : lerp(0.5, 1, pr(f, 0.09, 0.3)); add(dark); both((c) => { c.save(); c.globalAlpha *= b; c.beginPath(); add(c); c.fillStyle = AMB5[w.tone]; c.fill(); c.restore(); }, 0.8); }
      else add(lit[w.tone]);
    }
    g.save(); g.globalAlpha = wa; g.fillStyle = rgba('#9DB8FF', 0.09); g.fill(dark);
    for (let i = 0; i < 3; i++) { g.fillStyle = AMB5[i]; g.fill(lit[i]); }
    g.restore();
    GL.save(); GL.globalAlpha = wa * (0.8 + 0.35 * pr(t, 24.3, 25.0)); for (let i = 0; i < 3; i++) { GL.fillStyle = AMB5[i]; GL.fill(lit[i]); } GL.restore();
  }
  // 25.0: the mark charges white
  if (t >= 25) {
    towerFill('L', charge[0], C.white, '#6F96FF', 0.6); towerFill('M', charge[1], C.white, '#6F96FF', 0.6); towerFill('R', charge[2], C.white, '#6F96FF', 0.6);
    fillPoly(g, HP.link, C.white);
  }
}

// ================= ACT 6: lockup =================
let WMP = null;
function symbolAt(ctx, cx, cy, k, col) {            // link centre at (cx,cy), symbol scale k
  ctx.save(); ctx.translate(cx, cy); ctx.scale(k, k); ctx.translate(-LKC[0], -LKC[1]);
  for (const key of ['L', 'M', 'R', 'link']) fillPoly(ctx, SYM[key], col);
  ctx.restore();
}
function actLockup(t) {
  if (!WMP) { WMP = {}; for (const k in WM_GLYPHS) WMP[k] = new Path2D(WM_GLYPHS[k].d); }
  const τ = t - 25, K2 = 0.2396;
  const mv = E.inOutCubic(pr(τ, 1.0, 1.72));
  const k = lerp(HK, K2, mv), cx = lerp(PC[0], 960 - 442 + (LKC[0] - 538.5) * K2, mv), cy = lerp(PC[1], 440 + (LKC[1] - 626) * K2, mv);
  symbolAt(g, cx, cy, k, C.white);
  GL.save(); GL.globalAlpha = lerp(0.7, 0.42, pr(τ, 0.3, 1.6)); symbolAt(GL, cx, cy, k, '#6F96FF'); GL.restore();
  // wordmark
  const WS = 0.27, wx = 960 - 243, wy = 440 - 289 * WS;
  const order = ['H', 'o', 'g', 'e', 'n', 't', 'X'];
  for (const c of [g, GL]) {
    c.save(); c.translate(wx, wy); c.scale(WS, WS);
    c.save(); c.beginPath(); c.rect(-40, -60, WM_W + 80, 60 + 592); c.clip();
    for (let i = 0; i < order.length; i++) {
      const q = E.outExpo(pr(τ, 1.48 + i * 0.065, 2.28 + i * 0.065)); if (q <= 0) continue;
      c.save(); c.translate(0, (1 - q) * 640); c.globalAlpha = (c === GL ? 0.3 : 1) * clamp(q * 3);
      c.fillStyle = c === GL ? '#6F96FF' : C.white; c.fill(WMP[order[i]], 'evenodd'); c.restore();
    }
    c.restore();
    const sm = E.outCubic(pr(τ, 2.12, 2.6));
    if (sm > 0) {
      const bb = WM_GLYPHS.smile.bb, bounce = 1 + 0.12 * Math.sin(Math.PI * pr(τ, 2.3, 2.9));
      c.save(); c.beginPath(); c.rect(bb[0] - 10, bb[1] - 40, (bb[2] - bb[0] + 20) * sm, 220); c.clip();
      c.translate((bb[0] + bb[2]) / 2, bb[1]); c.scale(1, bounce); c.translate(-(bb[0] + bb[2]) / 2, -bb[1]);
      c.globalAlpha = c === GL ? 0.6 : 1; c.fillStyle = mixc(C.amber, C.white, E.inOutCubic(pr(τ, 2.9, 3.5))); c.fill(WMP.smile, 'evenodd'); c.restore();
    }
    c.restore();
  }
  // glint
  const gp = pr(τ, 3.35, 4.25);
  if (gp > 0 && gp < 1) {
    const gx = 960 + lerp(-900, 900, E.inOutCubic(gp));
    GL.save(); GL.beginPath(); GL.moveTo(gx - 60, 0); GL.lineTo(gx + 60, 0); GL.lineTo(gx + 60 + 500, 800); GL.lineTo(gx - 60 + 500, 800); GL.closePath(); GL.clip();
    GL.globalAlpha = Math.sin(Math.PI * gp);
    symbolAt(GL, cx, cy, k, '#fff');
    GL.translate(wx, wy); GL.scale(WS, WS); GL.fillStyle = '#fff'; for (const o of order) GL.fill(WMP[o], 'evenodd');
    GL.restore();
  }
  txt(g, 'Every room, sold at the price it deserves.', 960, 740, { w: 700, size: 64, ls: -1, by: 'word', color: C.white, align: 'c', t: τ - 2.47, st: 0.075, d: 0.9 });
  const s1 = 'AI digital employees for hotels', s2 = 'hogentx.com', w1 = textW(s1, fnt(500, 28), 0.6), w2 = textW(s2, fnt(700, 28), 2.5), x0 = 960 - (w1 + 64 + w2) / 2;
  txt(g, s1, x0, 822, { w: 500, size: 28, ls: 0.6, by: 'word', color: 'rgba(214,224,255,.78)', t: τ - 3.0, st: 0.05, d: 0.7 });
  g.save(); g.globalAlpha = an(τ, 3.2, 0.5); fillPoly(g, towerPts(x0 + w1 + 28, 824, 7, 26), C.amber); g.restore();
  txt(g, s2, x0 + w1 + 64, 822, { w: 700, size: 28, ls: 2.5, color: C.white, t: τ - 3.22, st: 0.02, d: 0.7 });
}

// ================= master =================
function drawScene(t) {
  const cam = (CAM = cameraAt(t));
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  GL.setTransform(1, 0, 0, 1, 0, 0); GL.globalAlpha = 1; GL.clearRect(0, 0, glowCv.width, glowCv.height);
  if (t < 15.0) {
    bgNavy();
    const bl = pr(t, 9.78, 10.3); if (bl > 0) bgBlue(E.inOutCubic(bl));
    setCam(cam);
    if (t < 9.7) actBuild(t); else actMany(t, cam);
  } else if (t < 20.0) {
    bgPaper();
    const wf = 1 - pr(t, 15.0, 15.35); if (wf > 0) { g.save(); g.globalAlpha = wf; g.fillStyle = C.white; g.fillRect(0, 0, W, H); g.restore(); }
    setScreen(); actRhythm(t);
  } else {
    setCam(cam);
    if (t < 26.02) actLight(t); else bgNavyStars(t);
    if (t >= 26.0) actLockup(t);
  }
  applyBloom(1);
  setScreen();
  // captions
  const sca = an(t, 10.45, 0.5, E.outCubic) * (1 - pr(t, 14.1, 14.45));
  if (sca > 0) { const sg2 = g.createLinearGradient(0, 800, 0, 1010); sg2.addColorStop(0, 'rgba(26,63,209,0)'); sg2.addColorStop(1, 'rgba(26,63,209,.96)'); g.save(); g.globalAlpha = sca; g.fillStyle = sg2; g.fillRect(0, 800, W, 280); g.restore(); }
  caption(t, 2.75, 4.7, 1, 'It starts with a line.', C.white);
  caption(t, 5.75, 9.0, 2, 'Three towers rise from it.', C.white);
  caption(t, 10.65, 13.9, 3, 'One hotel becomes many.', C.white);
  caption(t, 15.65, 18.85, 4, 'Each one keeps its own rhythm.', C.navy, C.blue);
  const n5 = smooth(pr(t, 22.25, 22.65));
  caption(t, 20.7, 24.15, 5, 'And in every room, a light.', mixc(C.navy, C.white, n5), mixc(C.blue, C.amber, n5));
  // hits
  const fl = (t0, a, d = 0.35) => { const f = t - t0; if (f < 0 || f > d) return; g.globalAlpha = a * Math.pow(1 - f / d, 2.2); g.globalCompositeOperation = 'lighter'; g.fillStyle = '#BFD2FF'; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; };
  fl(5.0, 0.16); fl(25.0, 0.26);
}
function bgNavyStars(t) {
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0); bgNavy();
  for (const s of STARS5) circle(g, s.x, s.y, s.s, rgba('#CFE0FF', 0.25 + 0.3 * (0.5 + 0.5 * Math.sin(t * s.f + s.ph))));
  g.restore();
}
window.initFilm = async () => { await document.fonts.load(`500 24px ${MONO}`).catch(() => {}); };
