// ---------- ACT I: night. hotels as towers, rooms as windows ----------
const LAY = [
  { par: 0.55, ground: 597.9, lit: 0.0 },
  { par: 0.75, ground: 610.2, cw: 9, ch: 11, gx: 7, gy: 9, m: 10, top: 18, lit: 0.34, poff: 0.5 },
  { par: 1.0, ground: GROUND, cw: 14, ch: 17, gx: 9, gy: 12, m: 13, top: 24, lit: 0.6, poff: 0.62 },
];
const HERO = {
  L: { x: 4 * KH, w: 227 * KH, top: 0 },
  M: { x: 618 * KH, w: 227.5 * KH, top: -0.25 },
  R: { x: 845.5 * KH, w: 227.5 * KH, top: 622.5 * KH },
};
const CITY = (() => {
  const r = rng(4242);
  const T = [], drops = [];
  function mk(layer, x, w, h, hero) {
    const Ld = LAY[layer], t = { layer, x, w, h, hero: hero || null, wins: [], base: Ld.ground };
    t.dist = Math.abs(x + w / 2 - 269);
    if (Ld.cw) {
      const cols = Math.max(1, Math.floor((w - 2 * Ld.m + Ld.gx) / (Ld.cw + Ld.gx)));
      const tot = cols * Ld.cw + (cols - 1) * Ld.gx, x0 = (w - tot) / 2;
      const litP = hero ? 0.78 : Ld.lit * (0.7 + r() * 0.6), poff = hero ? 0.5 : Ld.poff;
      for (let row = 0; ; row++) {
        const yr = Ld.top + row * (Ld.ch + Ld.gy);
        if (yr + ROOF * w + Ld.ch > h - 12) break;
        for (let c = 0; c < cols; c++) {
          const wx = x0 + c * (Ld.cw + Ld.gx);
          const lit = r() < litP;
          const off = lit && r() < poff ? 0.85 + 3.75 * Math.pow(r(), 0.8) : Infinity;
          const win = { x: wx, y: yr + ROOF * wx, lit, off, tone: Math.floor(r() * 3), re: lit || r() < 0.5 ? 5.4 + Math.min(1, t.dist / 1500) * 2.4 + r() * 0.7 : Infinity };
          t.wins.push(win);
          if (layer === 2 && lit && off < 9 && r() < 0.55) drops.push({ x: x + wx + Ld.cw / 2, y: Ld.ground - h + win.y + Ld.ch, t0: off, v: 0.7 + r() * 0.6 });
        }
      }
    }
    T.push(t);
    return t;
  }
  // far silhouettes
  let x = -1750;
  while (x < 1500) { const w = 110 + r() * 120; const lim = x < -300 ? 600 : 800; mk(0, x, w, 380 + r() * (lim - 380)); x += w + r() * 26; }
  // mid layer
  x = -1640;
  while (x < 1250) { const w = 78 + r() * 74; const lim = x < -350 ? 530 : 680; mk(1, x, w, 300 + r() * (lim - 300)); x += w + 6 + r() * 30; }
  // near layer, left of the H
  x = -1700;
  while (x < -90) { const w = 86 + r() * 62; const cap = Math.min(520, 300 + (x + 1700) * 0.2); mk(2, Math.round(x), Math.round(w), 210 + r() * (cap - 210)); x += w + 10 + r() * 36; }
  // near layer, right of the H
  x = 600;
  while (x < 1150) { const w = 86 + r() * 62; mk(2, Math.round(x), Math.round(w), 220 + r() * 300); x += w + 10 + r() * 36; }
  // the three hero towers (full buildings until the line arrives)
  const hL = mk(2, HERO.L.x, HERO.L.w, GROUND - HERO.L.top, 'L');
  const hM = mk(2, HERO.M.x, HERO.M.w, GROUND - HERO.M.top, 'M');
  const hR = mk(2, HERO.R.x, HERO.R.w, GROUND - HERO.R.top, 'R');
  const stars = [];
  for (let i = 0; i < 110; i++) stars.push({ x: -1400 + r() * 2800, y: -900 + r() * 1150, s: 0.6 + r() * 1.3, ph: r() * TAU, f: 0.6 + r() * 1.8 });
  return { T, drops, stars, hero: { L: hL, M: hM, R: hR } };
})();
// leak labels (deck: where the revenue leaks)
const LEAKS = (() => {
  const near = CITY.T.filter((t) => t.layer === 2 && !t.hero && t.x > -1250 && t.x < -150).sort((a, b) => a.x - b.x);
  const pick = [near[Math.floor(near.length * 0.12)], near[Math.floor(near.length * 0.42)], near[Math.floor(near.length * 0.68)], near[near.length - 1]];
  const txts = S.night.leaks;
  return pick.map((t, i) => ({ t, s: txts[i], at: 1.5625 + i * 0.625, lift: (EN ? [92, 132, 60, 150] : [92, 132, 84, 120])[i], flip: EN && i === 3 }));
})();

const AMB = ['#FFC46B', '#FFD489', '#FFB24A'];
function winPoly(ctx, x, y, cw, ch) {
  ctx.moveTo(x, y); ctx.lineTo(x + cw, y + cw * ROOF); ctx.lineTo(x + cw, y + cw * ROOF + ch); ctx.lineTo(x, y + ch); ctx.closePath();
}
function drawTower(tw, t, opt = {}) {
  const Ld = LAY[tw.layer], x = tw.x, base = tw.base, top = base - tw.h;
  const pts = towerPts(x, base, tw.w, tw.h);
  // face
  const gr = g.createLinearGradient(0, top, 0, base);
  if (tw.layer === 0) { gr.addColorStop(0, '#0B1936'); gr.addColorStop(1, '#081329'); }
  else if (tw.layer === 1) { gr.addColorStop(0, '#0F2148'); gr.addColorStop(1, '#0A1731'); }
  else if (tw.hero) { gr.addColorStop(0, '#1B3570'); gr.addColorStop(1, '#10224A'); }
  else { gr.addColorStop(0, '#152B5C'); gr.addColorStop(1, '#0C1B3B'); }
  fillPoly(g, pts, gr);
  // rim light on roof + left edge
  if (tw.layer > 0) {
    g.beginPath(); g.moveTo(x + 0.6, base); g.lineTo(x + 0.6, top + 0.6); g.lineTo(x + tw.w, top + tw.w * ROOF + 0.6);
    g.strokeStyle = rgba('#8FB0FF', tw.hero ? 0.55 : tw.layer === 2 ? 0.34 : 0.16); g.lineWidth = tw.layer === 2 ? 1.6 : 1.1; g.lineJoin = 'miter'; g.stroke();
  }
  if (!Ld.cw) return;
  const cw = Ld.cw, ch = Ld.ch;
  const heroOn = opt.heroOn;   // time when hero windows are switched on by the line
  const P = [new Path2D(), new Path2D(), new Path2D()], dark = new Path2D();
  g.save(); g.translate(x, top); GL.save(); GL.translate(x, top);
  const dim = tw.layer === 1 ? 0.6 : 1;
  for (const w of tw.wins) {
    let b = 0;
    if (heroOn !== undefined && t > heroOn + w.y * 0.0004) b = 1;
    else if (w.lit) {
      const f = t - w.off;
      b = f < 0 ? 1 : f < 0.04 ? 0.2 : f < 0.09 ? 0.85 : lerp(0.85, 0, pr(f, 0.09, 0.32));
    }
    if (heroOn === undefined && t > w.re) { const f = t - w.re; b = Math.max(b, f < 0.04 ? 0.7 : f < 0.09 ? 0.2 : lerp(0.5, 1, pr(f, 0.09, 0.3))); }
    if (b >= 1) winPoly(P[w.tone], w.x, w.y, cw, ch);
    else {
      winPoly(dark, w.x, w.y, cw, ch);
      if (b > 0) {
        g.globalAlpha = b * dim; g.beginPath(); winPoly(g, w.x, w.y, cw, ch); g.fillStyle = AMB[w.tone]; g.fill(); g.globalAlpha = 1;
        GL.globalAlpha = b * dim * 0.8; GL.beginPath(); winPoly(GL, w.x, w.y, cw, ch); GL.fillStyle = AMB[w.tone]; GL.fill(); GL.globalAlpha = 1;
      }
    }
  }
  g.fillStyle = rgba('#9DB8FF', tw.layer === 2 ? 0.075 : 0.05); g.fill(dark);
  g.globalAlpha = dim; GL.globalAlpha = dim * (tw.layer === 2 ? 0.8 : 0.5);
  for (let i = 0; i < 3; i++) { g.fillStyle = AMB[i]; g.fill(P[i]); GL.fillStyle = AMB[i]; GL.fill(P[i]); }
  g.restore(); GL.restore();
}
// white "charge" of a hero tower: grows away from where the line touches it, edges follow the roof angle
function heroCharge(key, t) {
  const pts = SYM[key].map((p) => [p[0] * KH, p[1] * KH]);
  const x0 = pts[0][0];
  let lo, hi;                                    // bounds on (y - ROOF*(x-x0))
  if (key === 'L') { const p = an(t, 5.05, 1.0, E.outQuart); const c = 467 - ROOF * 113.5; lo = c - p * 480; hi = c + p * 250; if (p <= 0) return; }
  else if (key === 'M') { const p = an(t, 5.1, 0.95, E.outQuart); lo = 380 - p * 400; hi = 400; if (p <= 0) return; }
  else { const p = an(t, 5.14, 0.9, E.outQuart); lo = 300; hi = 311 + p * 330; if (p <= 0) return; }
  const band = (ctx) => {
    ctx.beginPath();
    ctx.moveTo(x0 - 10, lo - 10 * ROOF); ctx.lineTo(x0 + 140, lo + 140 * ROOF); ctx.lineTo(x0 + 140, hi + 140 * ROOF); ctx.lineTo(x0 - 10, hi - 10 * ROOF); ctx.closePath();
  };
  g.save(); band(g); g.clip(); fillPoly(g, pts, C.white); g.restore();
  GL.save(); band(GL); GL.clip(); fillPoly(GL, pts, rgba('#6F96FF', 0.5)); GL.restore();
}

function drawNightBg(t, cam) {
  // sky
  const sk = g.createLinearGradient(0, 0, 0, H);
  sk.addColorStop(0, '#040915'); sk.addColorStop(0.55, '#081530'); sk.addColorStop(1, '#0E2250');
  g.fillStyle = sk; g.fill();
}
const KEEP = [0.62, 0.6, 0.66];      // how far each layer sinks when the line arrives
function drawNight(t, cam) {
  const collapse = (tw) => { const del = 5.06 + Math.min(1, tw.dist / 1500) * 0.42 + (2 - tw.layer) * 0.08; return E.inOutCubic(pr(t, del, del + 0.62)); };
  // glow behind the skyline / the H
  setScreen();
  const hp = [W / 2 + (269 - cam.x) * cam.z, H / 2 + (GROUND - 180 - cam.y) * cam.z];
  const k = an(t, 5.0, 1.6, E.outCubic);
  const rg = g.createRadialGradient(hp[0], hp[1], 0, hp[0], hp[1], lerp(900, 760, k));
  rg.addColorStop(0, rgba('#2D60FF', lerp(0.2, 0.3, k))); rg.addColorStop(0.5, rgba('#2D60FF', 0.07)); rg.addColorStop(1, rgba('#2D60FF', 0));
  g.fillStyle = rg; g.fillRect(0, 0, W, H);
  // stars
  setWorld(cam, 0.18);
  for (const s of CITY.stars) {
    const a = 0.25 + 0.3 * (0.5 + 0.5 * Math.sin(t * s.f + s.ph));
    circle(g, s.x, s.y, s.s, rgba('#CFE0FF', a));
  }
  // layers
  for (let layer = 0; layer < 3; layer++) {
    const Ld = LAY[layer];
    setWorld(cam, Ld.par);
    g.save(); g.beginPath(); g.rect(-6000, -4000, 12000, 4000 + Ld.ground); g.clip();
    GL.save(); GL.beginPath(); GL.rect(-6000, -4000, 12000, 4000 + Ld.ground); GL.clip();
    for (const tw of CITY.T) {
      if (tw.layer !== layer || tw.hero) continue;
      const c = collapse(tw) * KEEP[layer];
      if (c > 0) { g.save(); GL.save(); g.translate(0, tw.h * c); GL.translate(0, tw.h * c); drawTower(tw, t); g.restore(); GL.restore(); }
      else drawTower(tw, t);
    }
    // haze at the foot of each layer
    {
      const hz = g.createLinearGradient(0, Ld.ground - 220, 0, Ld.ground);
      hz.addColorStop(0, rgba('#1B3F9A', 0)); hz.addColorStop(1, rgba('#1B3F9A', 0.2));
      g.fillStyle = hz; g.fillRect(-6000, Ld.ground - 220, 12000, 220);
    }
    g.restore(); GL.restore();
  }
  // hero towers
  setWorld(cam, 1);
  const Hh = CITY.hero;
  if (t < 6.2) {
    drawTower(Hh.L, t, t >= 5.03 ? { heroOn: 5.03 } : {});
    drawTower(Hh.R, t, t >= 5.1 ? { heroOn: 5.1 } : {});
    // M: upper part stays, lower part (under the line) falls away
    const mUp = SYM.M.map((p) => [p[0] * KH, p[1] * KH]);
    if (t < 5.02) drawTower(Hh.M, t);
    else {
      g.save(); GL.save(); poly(g, mUp); g.clip(); poly(GL, mUp); GL.clip(); drawTower(Hh.M, t, { heroOn: 5.06 }); g.restore(); GL.restore();
      const p = pr(t, 5.02, 5.42);
      if (p < 1) {
        const lowPts = [[mUp[3][0], mUp[3][1] + 6], [mUp[2][0], mUp[2][1] + 6], [mUp[2][0], GROUND], [mUp[3][0], GROUND]];
        const dy = 340 * E.inCubic(p);
        g.save(); GL.save(); g.globalAlpha = 1 - E.inQuad(p); GL.globalAlpha = 1 - p;
        g.translate(0, dy); GL.translate(0, dy);
        poly(g, lowPts); g.clip(); poly(GL, lowPts); GL.clip();
        g.beginPath(); g.rect(-9999, -9999, 19998, 9999 + GROUND - dy); g.clip();
        drawTower(Hh.M, t);
        g.restore(); GL.restore();
      }
    }
  }
  if (t >= 5.03) { heroCharge('L', t); heroCharge('M', t); heroCharge('R', t); }
  // ground band
  const ga = 1;
  {
    g.globalAlpha = ga;
    const gg = g.createLinearGradient(0, GROUND, 0, GROUND + 260);
    gg.addColorStop(0, '#081329'); gg.addColorStop(1, '#040915');
    g.fillStyle = gg; g.fillRect(-6000, GROUND, 12000, 1200);
    seg(g, -6000, GROUND, 6000, GROUND, rgba('#8FB0FF', 0.28), 1.5, 'butt');
    g.globalAlpha = 1;
    // the H mirrored on the ground
    const ra = an(t, 5.3, 1.2, E.outCubic);
    if (ra > 0) {
      const rg2 = g.createLinearGradient(0, GROUND, 0, GROUND + 190);
      rg2.addColorStop(0, rgba('#BFD2FF', 0.26 * ra)); rg2.addColorStop(1, rgba('#BFD2FF', 0));
      g.fillStyle = rg2;
      for (const k of ['L', 'R']) { const hx0 = HERO[k].x, hw = HERO[k].w; g.fillRect(hx0, GROUND + 1, hw, 190); }
    }
  }
  // leak drops
  if (t < 5.6) {
    for (const d of CITY.drops) {
      const f = t - d.t0; if (f < 0 || f > 0.95) continue;
      const y = d.y + 520 * d.v * f * f + 30 * f, a = (1 - pr(f, 0.45, 0.95)) * clamp(f * 20);
      if (y > GROUND) continue;
      const len = 6 + 46 * f;
      both((c) => { c.globalAlpha = a * (c === g ? 0.95 : 1); seg(c, d.x, y - len, d.x, y, '#FFD489', 2.4); c.globalAlpha = 1; });
    }
  }
  // leak labels
  for (const L of LEAKS) {
    const p = spring(t - L.at, 2.6, 0.62), o = 1 - pr(t, 4.3 + (L.at - 1.56) * 0.06, 4.62 + (L.at - 1.56) * 0.06);
    if (t < L.at || o <= 0) continue;
    const tw = L.t, ax = tw.x + tw.w * 0.3, ay = tw.base - tw.h + tw.w * 0.3 * ROOF;
    const lsz = S.night.leakSize, lw = EN ? 600 : 500, lls = EN ? 0.2 : 1;
    const f = fnt(lw, lsz), wT = textW(L.s, f, lls);
    const pw = wT + 78, ph = 54, px = L.flip ? ax - pw + 26 : ax - 26, py = ay - L.lift - ph;       // long English label opens to the left, clear of the hero tower
    g.save(); g.globalAlpha = clamp(p * 1.4) * o;
    seg(g, ax, ay - 4, ax, py + ph + 2, rgba('#FFC46B', 0.7), 1.6, 'butt');
    circle(g, ax, ay - 4, 4.5, '#FFC46B');
    g.translate(px + pw / 2, py + ph); g.scale(lerp(0.7, 1, p), lerp(0.7, 1, p)); g.translate(-(px + pw / 2), -(py + ph));
    rr(g, px, py, pw, ph, 27); g.fillStyle = rgba('#07112A', 0.86); g.fill();
    g.strokeStyle = rgba('#FFC46B', 0.55); g.lineWidth = 1.5; g.stroke();
    circle(g, px + 28, py + ph / 2, 11, '#FFC46B');
    seg(g, px + 22, py + ph / 2, px + 34, py + ph / 2, '#07112A', 3, 'round');
    label(g, L.s, px + 50, py + ph / 2 + 1, { w: lw, size: lsz, ls: lls, color: '#F6F8FF', base: 'middle' });
    g.restore();
  }
}
// the line inside the night zone (+ link of the H)
function drawNightLine(t, cam) {
  const R = lineRange(t); if (!R) return;
  setWorld(cam, 1);
  const sb = Math.min(R[1], BOUND[0] + 40), a = onLine(-4000), b = onLine(sb);
  const settle = pr(t, 5.0, 6.0);
  both((c) => {
    const isG = c === GL;
    seg(c, a[0], a[1], b[0], b[1], isG ? rgba('#5E8BFF', 0.95) : rgba('#DCE7FF', lerp(1, 0.78, settle)), isG ? lerp(16, 7, settle) : lerp(4.2, 2.4, settle), 'butt');
  });
  // link of the H (logo thickness)
  if (R[1] > 200) {
    const lk = SYM.link.map((p) => [p[0] * KH, p[1] * KH]);
    fillPoly(g, lk, C.white); fillPoly(GL, lk, rgba('#8FB0FF', 0.8));
  }
  // head flare
  if (R[1] < 1e5) {
    const hd = onLine(R[1]);
    both((c) => { circle(c, hd[0], hd[1], c === GL ? 46 : 8, '#fff'); });
  }
  // working pulses along the line
  for (const t0 of [6.25, 7.5, 8.75]) {
    const p = pr(t, t0, t0 + 1.05); if (p <= 0 || p >= 1) continue;
    const s = lerp(-1500, 1700, E.inOutCubic(p)), a1 = onLine(s - 70), b1 = onLine(s + 70), al = Math.sin(Math.PI * p);
    both((c) => { c.globalAlpha = al; seg(c, a1[0], a1[1], b1[0], b1[1], '#fff', c === GL ? 12 : 4.5, 'round'); c.globalAlpha = 1; });
  }
}
// ---------- type for act I ----------
function drawNightText(t, cam) {
  // scene 1 (screen space)
  if (t < 5.2) {
    setScreen();
    const o = 4.18;
    const kp = an(t, 0.12, 0.6);
    if (kp > 0) {
      g.save(); g.globalAlpha = kp * (1 - pr(t, 4.2, 4.5));
      fillPoly(g, [[140, 132], [140 + 34 * kp, 132 + 34 * kp * ROOF * 0.0], [140 + 34 * kp, 142], [140, 142]], C.amber);
      g.restore();
    }
    const N1 = S.night, y1 = EN ? 262 : 268;
    txt(g, N1.kicker, 190, 149, { w: 700, size: N1.ksize, ls: N1.kls, color: C.amber, t: t - 0.15, st: 0.03, out: 4.2 - 0.15 });
    N1.h.forEach((ln, i) => { const d0 = 0.22 + i * 0.28; txt(g, ln, 134, y1 + i * HL.lead, { w: HL.w, size: HL.size, ls: HL.ls, by: HL.by, color: C.white, t: t - d0, st: HL.st, d: 0.8, out: 4.24 + i * 0.06 - d0, sto: EN ? 0.035 : 0.012 }); });
    txt(g, N1.sub, 140, y1 + (N1.h.length - 1) * HL.lead + (EN ? 66 : 70), { w: 500, size: 28, ls: 0.3, by: 'word', color: rgba('#C9D6F5', 0.76), t: t - 1.0, st: 0.045, d: 0.7, out: 4.36 - 1.0, sto: 0.012 });
  }
  // scene 2 (attached to the world at stop 0)
  if (t > 5.8) {
    setWorld(cam, 1);
    const ox = STOPS[0].x - 960, oy = STOPS[0].y - 540;      // screen -> world for stop 0
    const kp = an(t, 6.0, 0.6);
    g.save(); g.globalAlpha = kp;
    fillPoly(g, towerPts(ox + 140, oy + 154, 14, 30), C.amber);
    g.restore();
    txt(g, 'HogentX', ox + 170, oy + 152, { w: 800, size: 34, ls: 1.5, color: C.white, t: t - 6.02, st: 0.03 });
    const I2 = S.intro, y2 = oy + (EN ? 262 : 268), yt = y2 + (I2.h.length - 1) * HL.lead + (EN ? 82 : 76);
    I2.h.forEach((ln, i) => txt(g, ln, ox + 134, y2 + i * HL.lead, { w: HL.w, size: HL.size, ls: HL.ls, by: HL.by, color: C.white, t: t - 6.1 - i * 0.2, st: HL.st, d: 0.8 }));
    const parts = I2.tags;
    let x = ox + 140;
    for (let i = 0; i < 4; i++) {
      const tt = t - 6.9 - i * 0.16;
      const w = txt(g, parts[i], x, yt, { w: 700, size: I2.tagSize, ls: EN ? 0.3 : 2, color: C.amber, t: tt, st: EN ? 0.018 : 0.03, d: 0.6 });
      x += w + 22;
      if (i < 3) { g.save(); g.globalAlpha = an(tt, 0.15, 0.4) * 0.6; fillPoly(g, towerPts(x, yt - 6, 5, 22), '#C9D6F5'); g.restore(); x += 27; }
    }
    txt(g, I2.sub, ox + 141, yt + 56, { w: 500, size: 27, ls: 0.3, by: 'word', color: rgba('#C9D6F5', 0.74), t: t - 7.4, st: 0.045, d: 0.7 });
  }
}
