// ---------- world: one line, one take ----------
// The logo's link line runs through the whole world. Every scene sits on it; the camera travels along it.
const KH = 0.5;                                   // scale of the night "H"
const GROUND = 1247 * KH;
const L0 = [((231 + 845.5) / 2) * KH, ((934.15 + 623.3) / 2) * KH];   // centre of the link (world)
const D = 3000;                                   // distance between stops along the line
const onLine = (s) => [L0[0] + U[0] * s, L0[1] + U[1] * s];
const node = (i) => onLine(D * i);
const lineY = (x) => L0[1] + (x - L0[0]) * LINK;
const NV = [RV[1], -RV[0]];                       // normal of a roof-angle boundary, pointing "ahead"
const BOUND = [0.56 * D, 4.56 * D, 5.56 * D];     // zone boundaries (s on the line)
const T_STRIKE = 5.0;

// camera stops
const STOPS = [
  { x: -101, y: 262 },                            // 0: night H
  { x: node(1)[0], y: node(1)[1] },
  { x: node(2)[0], y: node(2)[1] },
  { x: node(3)[0], y: node(3)[1] },
  { x: node(4)[0], y: node(4)[1] },
  { x: node(5)[0], y: node(5)[1] },
  { x: node(6)[0], y: node(6)[1] - 70 },
];
const WHIPS = [10, 12.5, 15, 17.5, 20, 25];       // bar lines
const WT = 0.92, WC = 0.4;                        // whip duration, fraction before the bar line
const DRIFT = 13;                                 // px/s creep along the line while holding
function stopPos(i, t) {
  const t0 = i === 0 ? 6.6 : WHIPS[i - 1];
  const d = DRIFT * (t - t0 - 1.1);
  return [STOPS[i].x + U[0] * d, STOPS[i].y + U[1] * d];
}
function cameraAt(t) {
  let x, y, z = 1;
  if (t < T_STRIKE) {
    const p = t / T_STRIKE;
    x = lerp(-420, -262, p); y = lerp(70, 54, p); z = lerp(0.8, 0.84, p);
  } else {
    // which whip are we in / after
    let k = 0;
    while (k < WHIPS.length && t >= WHIPS[k] - WT * WC) k++;
    // k = number of whips started
    let a = stopPos(Math.max(0, k - 1), t), b = stopPos(k, t);
    if (k === 0) {
      // push in from the skyline to the H
      const p = E.outQuart(pr(t, T_STRIKE, 6.7));
      const s = stopPos(0, t);
      x = lerp(-262, s[0], p); y = lerp(54, s[1], p); z = lerp(0.84, 1, p);
    } else {
      const q = pr(t, WHIPS[k - 1] - WT * WC, WHIPS[k - 1] + WT * (1 - WC));
      const p = whip(q, WC);
      a = stopPos(k - 1, t); b = stopPos(k, t);
      x = lerp(a[0], b[0], p); y = lerp(a[1], b[1], p);
      z = 1 - 0.085 * Math.pow(Math.sin(Math.PI * Math.pow(q, 0.8)), 2);
    }
    // impacts
    const sh = (t0, amp, f = 62) => { const d = t - t0; if (d < 0 || d > 0.6) return; const e = amp * Math.exp(-d * 9); x += e * Math.sin(d * f); y += e * Math.cos(d * f * 1.31); };
    sh(T_STRIKE, 9); sh(22.5, 5); sh(25.0, 6);
  }
  // slow push on the H while the city relights
  z *= 1 + 0.045 * E.inOutSine(pr(t, 6.0, 9.6)) * (1 - smooth(pr(t, 9.63, 10.25)));
  // final slow push on the lockup
  if (t > 26) z *= 1 + 0.03 * E.inOutSine(pr(t, 26, 30));
  return { x, y, z };
}

// ---------- zones ----------
function halfPlane(ctx, k) {         // path: everything ahead of boundary k (world transform must be active)
  const B = onLine(BOUND[k]), R = 30000;
  ctx.beginPath();
  ctx.moveTo(B[0] - RV[0] * R, B[1] - RV[1] * R);
  ctx.lineTo(B[0] + RV[0] * R, B[1] + RV[1] * R);
  ctx.lineTo(B[0] + RV[0] * R + NV[0] * R, B[1] + RV[1] * R + NV[1] * R);
  ctx.lineTo(B[0] - RV[0] * R + NV[0] * R, B[1] - RV[1] * R + NV[1] * R);
  ctx.closePath();
}
function behindPlane(ctx, k) {       // path: everything behind boundary k
  const B = onLine(BOUND[k]), R = 30000;
  ctx.beginPath();
  ctx.moveTo(B[0] - RV[0] * R, B[1] - RV[1] * R);
  ctx.lineTo(B[0] + RV[0] * R, B[1] + RV[1] * R);
  ctx.lineTo(B[0] + RV[0] * R - NV[0] * R, B[1] + RV[1] * R - NV[1] * R);
  ctx.lineTo(B[0] - RV[0] * R - NV[0] * R, B[1] - RV[1] * R - NV[1] * R);
  ctx.closePath();
}
// signed distance of screen centre to boundary k (>0 = camera is ahead of it), in screen px
function boundDist(k, cam) {
  const B = onLine(BOUND[k]);
  return ((cam.x - B[0]) * NV[0] + (cam.y - B[1]) * NV[1]) * cam.z;
}
const REACH = 1250;                  // > half screen diagonal projected on NV
function zoneVisible(z, cam) {       // zone z lies between boundary z-1 and boundary z
  if (z > 0 && boundDist(z - 1, cam) < -REACH) return false;
  if (z < BOUND.length && boundDist(z, cam) > REACH) return false;
  return true;
}
// clip both layers to zone z
function clipZone(z) {
  for (const c of [g, GL]) {
    if (z > 0) { halfPlane(c, z - 1); c.clip(); }
    if (z < BOUND.length) { behindPlane(c, z); c.clip(); }
  }
}
// run fn in node-local coordinates (world transform must be active)
function atNode(i, fn) {
  const n = node(i);
  g.save(); GL.save(); g.translate(n[0], n[1]); GL.translate(n[0], n[1]);
  fn(); g.restore(); GL.restore();
}

// ---------- travelling debris between the stops (streaks into speed lines during a whip) ----------
const DEBRIS = (() => {
  const r = rng(99), a = [];
  for (let gap = 0; gap < 6; gap++) {
    for (let i = 0; i < 34; i++) {
      const s = (gap + 0.37 + r() * 0.25) * D, off = (r() * 2 - 1) * 900;
      const p = onLine(s);
      a.push({ x: p[0] - U[1] * off, y: p[1] + U[0] * off, w: 10 + r() * 46, h: 14 + r() * 90, s, k: r(), c: Math.floor(r() * 3) });
    }
  }
  return a;
})();
function drawDebris(cam) {
  const pal = [
    ['#FFC46B', '#7FA2FF', '#F6F8FF'],
    ['#2D60FF', '#10213A', '#FFC46B'],
    ['#FFFFFF', '#FFFFFF', '#10213A'],
    ['#FFFFFF', '#7FA2FF', '#FFC46B'],
  ];
  for (const d of DEBRIS) {
    if (Math.abs(d.x - cam.x) > 1500 / cam.z || Math.abs(d.y - cam.y) > 1100 / cam.z) continue;
    const zone = d.s < BOUND[0] ? 0 : d.s < BOUND[1] ? 1 : d.s < BOUND[2] ? 2 : 3;
    const col = pal[zone][d.c];
    g.globalAlpha = zone === 1 ? 0.1 + d.k * 0.22 : 0.08 + d.k * 0.2;
    fillPoly(g, towerPts(d.x, d.y, d.w, d.h), col);
  }
  g.globalAlpha = 1;
}

// ---------- the line ----------
// visible range of the line [sa, sb] at time t
function lineRange(t) {
  if (t < T_STRIKE) return null;
  let sb = -2700 + 10000 * E.outCubic(pr(t, T_STRIKE, T_STRIKE + 0.42));
  if (t > T_STRIKE + 0.42) sb = 1e6;
  let sa = -1e6;
  return [sa, sb];
}
