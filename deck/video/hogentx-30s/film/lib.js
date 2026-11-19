// ---------- constants ----------
const W = 1920, H = 1080, FPS = 60, DUR = 30;
const BPM = 96, BEAT = 60 / BPM, BAR = BEAT * 4;      // bar = 2.5 s, 12 bars = 30 s
const TAU = Math.PI * 2;

// ---------- math ----------
const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
const lerp = (a, b, t) => a + (b - a) * t;
const pr = (t, a, b) => clamp((t - a) / (b - a));
const smooth = (x) => x * x * (3 - 2 * x);
const E = {
  lin: (t) => t,
  inQuad: (t) => t * t,
  outQuad: (t) => 1 - (1 - t) * (1 - t),
  inCubic: (t) => t * t * t,
  outCubic: (t) => 1 - Math.pow(1 - t, 3),
  inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  inQuart: (t) => t * t * t * t,
  outQuart: (t) => 1 - Math.pow(1 - t, 4),
  inOutQuart: (t) => (t < 0.5 ? 8 * t * t * t * t : 1 - Math.pow(-2 * t + 2, 4) / 2),
  outQuint: (t) => 1 - Math.pow(1 - t, 5),
  inOutQuint: (t) => (t < 0.5 ? 16 * t ** 5 : 1 - Math.pow(-2 * t + 2, 5) / 2),
  inExpo: (t) => (t <= 0 ? 0 : Math.pow(2, 10 * t - 10)),
  outExpo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutExpo: (t) => (t <= 0 ? 0 : t >= 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  outBack: (t, s = 1.70158) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2),
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  outSine: (t) => Math.sin((t * Math.PI) / 2),
};
// animate: eased 0..1 from start over dur
const an = (t, start, dur, ease = E.outExpo) => ease(pr(t, start, start + dur));
// damped spring step response (t seconds since release)
function spring(t, f = 3, z = 0.5) {
  if (t <= 0) return 0;
  const w = TAU * f, wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + ((z * w) / wd) * Math.sin(wd * t));
}
// camera whip ease: sharp attack, long settle. value h at x=c.
function whip(x, c = 0.4, n = 4, m = 5) {
  const h = (m / (1 - c)) / (n / c + m / (1 - c));
  if (x <= 0) return 0; if (x >= 1) return 1;
  if (x < c) return h * Math.pow(x / c, n);
  return h + (1 - h) * (1 - Math.pow(1 - (x - c) / (1 - c), m));
}
function rng(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// ---------- colour ----------
const hex = (h) => { const n = parseInt(h.slice(1), 16); return [(n >> 16) & 255, (n >> 8) & 255, n & 255]; };
const _hc = {};
const hx = (h) => _hc[h] || (_hc[h] = hex(h));
const rgba = (h, a = 1) => { const c = typeof h === 'string' ? hx(h) : h; return `rgba(${c[0] | 0},${c[1] | 0},${c[2] | 0},${a})`; };
const mixc = (h1, h2, t, a = 1) => {
  const a1 = typeof h1 === 'string' ? hx(h1) : h1, a2 = typeof h2 === 'string' ? hx(h2) : h2;
  return `rgba(${lerp(a1[0], a2[0], t) | 0},${lerp(a1[1], a2[1], t) | 0},${lerp(a1[2], a2[2], t) | 0},${a})`;
};
const C = {
  night0: '#050A17', night1: '#0A1630', night2: '#132A55',
  navy: '#10213A', ink: '#0E1B33', mute: '#5B6780', soft: '#3B4864',
  blue: '#2D60FF', blueDeep: '#1A3FD1', blueLight: '#7FA2FF', sky: '#A9C1FF',
  paper: '#F3F6FC', paper2: '#E6ECF8', card: '#FFFFFF', hair: '#D6E0FF',
  amber: '#FFC46B', amberHot: '#FFE2A8', amberDeep: '#F59E2D',
  white: '#F6F8FF',
};

// ---------- brand geometry (symbol, local units 1077 x 1252) ----------
const ROOF = 0.6545;     // roof slope (down to the right)
const LINK = -0.5056;    // link slope (up to the right)
const SYM = {
  L: [[4, 0], [231, 148.3], [231, 1247], [4, 1247]],
  M: [[618, -0.5], [845.5, 148.4], [845.5, 631.7], [618, 746.9]],
  R: [[845.5, 622.5], [1073, 771.4], [1073, 1247], [845.5, 1247]],
  link: [[231, 925.5], [845.5, 614.9], [845.5, 631.7], [231, 942.8]],
  w: 1077, h: 1252,
};
const U = (() => { const l = Math.hypot(1, LINK); return [1 / l, LINK / l]; })();   // unit vector along the link (up-right)
const RV = (() => { const l = Math.hypot(1, ROOF); return [1 / l, ROOF / l]; })();   // unit vector along the roof (down-right)

// ---------- drawing helpers ----------
function poly(ctx, pts) {
  ctx.beginPath();
  ctx.moveTo(pts[0][0], pts[0][1]);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1]);
  ctx.closePath();
}
function fillPoly(ctx, pts, style) { poly(ctx, pts); ctx.fillStyle = style; ctx.fill(); }
// tower: vertical sides, slanted roof. (x, base) = bottom-left, h = height of the tall (left) side
function towerPts(x, base, w, h, slope = ROOF) {
  return [[x, base - h], [x + w, base - h + w * slope], [x + w, base], [x, base]];
}
function rr(ctx, x, y, w, h, r) { ctx.beginPath(); ctx.roundRect(x, y, w, h, r); }
function seg(ctx, x1, y1, x2, y2, style, lw, cap = 'round') {
  ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2);
  ctx.strokeStyle = style; ctx.lineWidth = lw; ctx.lineCap = cap; ctx.stroke();
}
function circle(ctx, x, y, r, style) { ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), 0, TAU); ctx.fillStyle = style; ctx.fill(); }
function ring(ctx, x, y, r, style, lw, a0 = 0, a1 = TAU) {
  ctx.beginPath(); ctx.arc(x, y, Math.max(0, r), a0, a1); ctx.strokeStyle = style; ctx.lineWidth = lw; ctx.stroke();
}

// ---------- type ----------
const FAM = '"Manrope","NotoSC","Noto Sans SC",sans-serif';
const fnt = (weight, size) => `${weight} ${size}px ${FAM}`;
const _mc = new Map();
let _mctx = null;
function layoutText(s, font, ls = 0) {
  const key = font + '|' + ls + '|' + s;
  let L = _mc.get(key);
  if (L) return L;
  if (!_mctx) _mctx = document.createElement('canvas').getContext('2d');
  const c = _mctx; c.font = font; c.letterSpacing = ls + 'px';
  const chars = Array.from(s), xs = [0], wi = [];
  let acc = '', wn = 0;
  for (let i = 0; i < chars.length; i++) { acc += chars[i]; xs.push(c.measureText(acc).width); wi.push(wn); if (chars[i] === ' ') wn++; }
  L = { chars, xs, wi, w: xs[xs.length - 1] - ls };
  _mc.set(key, L);
  return L;
}
const textW = (s, font, ls = 0) => layoutText(s, font, ls).w;
/* Animated line of text. Characters rise out of a baseline mask, staggered.
   o: {w(weight), size, color, ls, align, t, st, d, out, sto, rise, alpha, clip, ease, by} */
function txt(ctx, s, x, y, o = {}) {
  const size = o.size || 40, font = fnt(o.w || 700, size), ls = o.ls || 0;
  const L = layoutText(s, font, ls);
  const t = o.t === undefined ? 99 : o.t, st = o.st === undefined ? 0.028 : o.st, d = o.d || 0.7;
  const out = o.out === undefined ? null : o.out, sto = o.sto === undefined ? 0.012 : o.sto;
  const rise = o.rise === undefined ? 1.1 : o.rise, ease = o.ease || E.outExpo;
  let x0 = x;
  if (o.align === 'c') x0 = x - L.w / 2; else if (o.align === 'r') x0 = x - L.w;
  if (t <= 0) return L.w;
  if (out !== null && t > out + sto * L.chars.length + 0.4) return L.w;
  ctx.save();
  if (o.clip !== false) { ctx.beginPath(); ctx.rect(x0 - size * 0.3, y - size * 1.08, L.w + size * 0.6, size * 1.42); ctx.clip(); }
  ctx.font = font; ctx.letterSpacing = '0px'; ctx.textBaseline = 'alphabetic'; ctx.textAlign = 'left';
  ctx.fillStyle = o.color || '#fff';
  const A = o.alpha === undefined ? 1 : o.alpha;
  const n = L.chars.length;
  for (let i = 0; i < n; i++) {
    const k = o.by === 'line' ? 0 : o.by === 'word' ? L.wi[i] : i;
    const p = ease(pr(t, k * st, k * st + d));
    if (p <= 0) continue;
    const q = out === null ? 0 : E.inQuart(pr(t, out + k * sto, out + k * sto + 0.32));
    if (q >= 1) continue;
    const dy = (1 - p) * size * rise - q * size * 1.15;
    ctx.globalAlpha = A * clamp(p * 4) * (1 - q * q);
    ctx.fillText(L.chars[i], x0 + L.xs[i], y + dy);
  }
  ctx.restore();
  return L.w;
}
// simple static text
function label(ctx, s, x, y, o = {}) {
  ctx.save();
  ctx.font = fnt(o.w || 600, o.size || 24); ctx.letterSpacing = (o.ls || 0) + 'px';
  ctx.textBaseline = o.base || 'alphabetic'; ctx.textAlign = o.align === 'c' ? 'center' : o.align === 'r' ? 'right' : 'left';
  ctx.fillStyle = o.color || '#fff'; ctx.globalAlpha *= o.alpha === undefined ? 1 : o.alpha;
  ctx.fillText(s, x, y);
  ctx.restore();
}
// pointer cursor (tip at x,y)
function cursor(ctx, x, y, s = 1, press = 0) {
  ctx.save(); ctx.translate(x, y); ctx.scale(s * (1 - 0.12 * press), s * (1 - 0.12 * press));
  ctx.beginPath();
  ctx.moveTo(0, 0); ctx.lineTo(0, 34); ctx.lineTo(8.6, 26.4); ctx.lineTo(14.6, 39.6); ctx.lineTo(20.4, 37);
  ctx.lineTo(14.6, 24.2); ctx.lineTo(25.4, 24.2); ctx.closePath();
  ctx.shadowColor = 'rgba(8,16,40,.35)'; ctx.shadowBlur = 14; ctx.shadowOffsetY = 6;
  ctx.fillStyle = '#0E1B33'; ctx.fill();
  ctx.shadowColor = 'transparent';
  ctx.lineJoin = 'round'; ctx.lineWidth = 3.2; ctx.strokeStyle = '#fff'; ctx.stroke();
  ctx.restore();
}
// check mark (elbow at x,y): short arm up-left, long arm up-right
function checkPath(ctx, x, y, s, p = 1) {
  const a = 0.44 * s, b = 1.0 * s, ax = -0.7071, ay = -0.7071, bx = 0.6157, by = -0.788;
  const p1 = clamp(p / 0.3), p2 = clamp((p - 0.3) / 0.7);
  ctx.beginPath();
  ctx.moveTo(x + ax * a, y + ay * a);
  ctx.lineTo(x + ax * a * (1 - p1), y + ay * a * (1 - p1));
  if (p2 > 0) ctx.lineTo(x + bx * b * p2, y + by * b * p2);
}
