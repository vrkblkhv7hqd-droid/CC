// ---------- canvases ----------
const cv = document.getElementById('c');
const g = cv.getContext('2d', { willReadFrequently: true, alpha: false });
const GS = 0.25;                                   // glow layer scale
const glowCv = new OffscreenCanvas(W * GS, H * GS);
const GL = glowCv.getContext('2d');
const b1Cv = new OffscreenCanvas(W * GS, H * GS), B1 = b1Cv.getContext('2d');
const b2Cv = new OffscreenCanvas(W * GS / 2, H * GS / 2), B2 = b2Cv.getContext('2d');
const b3Cv = new OffscreenCanvas(W * GS / 4, H * GS / 4), B3 = b3Cv.getContext('2d');

let CAM = { x: 0, y: 0, z: 1 };
function setWorld(cam = CAM, par = 1, ox = 0, oy = 0) {
  // par: parallax factor (1 = fully attached to the world)
  const z = cam.z, tx = W / 2 - (cam.x * par + ox) * z, ty = H / 2 - (cam.y * par + oy) * z;
  g.setTransform(z, 0, 0, z, tx, ty);
  GL.setTransform(z * GS, 0, 0, z * GS, tx * GS, ty * GS);
}
function setScreen() { g.setTransform(1, 0, 0, 1, 0, 0); GL.setTransform(GS, 0, 0, GS, 0, 0); }
// run the same drawing on main + glow layers
function both(fn, glowAlpha = 1) {
  fn(g);
  if (glowAlpha > 0) { GL.save(); GL.globalAlpha *= glowAlpha; fn(GL); GL.restore(); }
}
function applyBloom(strength = 1) {
  if (strength <= 0) return;
  B1.clearRect(0, 0, b1Cv.width, b1Cv.height); B1.filter = 'blur(2.5px)'; B1.drawImage(glowCv, 0, 0);
  B2.clearRect(0, 0, b2Cv.width, b2Cv.height); B2.filter = 'blur(4px)'; B2.drawImage(glowCv, 0, 0, b2Cv.width, b2Cv.height);
  B3.clearRect(0, 0, b3Cv.width, b3Cv.height); B3.filter = 'blur(5px)'; B3.drawImage(glowCv, 0, 0, b3Cv.width, b3Cv.height);
  g.save(); g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = 'lighter'; g.imageSmoothingEnabled = true; g.imageSmoothingQuality = 'high';
  g.globalAlpha = 0.55 * strength; g.drawImage(b1Cv, 0, 0, W, H);
  g.globalAlpha = 0.5 * strength; g.drawImage(b2Cv, 0, 0, W, H);
  g.globalAlpha = 0.45 * strength; g.drawImage(b3Cv, 0, 0, W, H);
  g.restore();
}

// ---------- frame assembly: motion blur + vignette + grain ----------
const NPX = W * H;
const acc = new Uint32Array(NPX * 3);
const outImg = new ImageData(W, H);
const out = outImg.data;
const NMASK = (1 << 21) - 1;
const noise = new Float32Array(NMASK + 1);
(() => { const r = rng(20261118); for (let i = 0; i <= NMASK; i++) { noise[i] = (r() + r() + r() + r() - 2) * 1.732; } })(); // ~unit sigma
const vig = new Float32Array(NPX);
(() => {
  for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
    const dx = (x - W / 2) / (W / 2), dy = (y - H / 2) / (H / 2);
    const r = Math.sqrt(dx * dx * 0.82 + dy * dy * 0.9);
    vig[y * W + x] = smooth(clamp((r - 0.35) / 0.95));
  }
})();
const SHUTTER = 0.5;       // 180 degrees
let QUALITY = 1;           // sample multiplier (preview can lower)

function sampleCount(t) {
  const a = cameraAt(t), b = cameraAt(t + SHUTTER / FPS);
  const d = Math.hypot(b.x - a.x, b.y - a.y) * a.z + Math.abs(b.z - a.z) * 900;
  const base = FRAME.baseSamples ? FRAME.baseSamples(t) : 4;
  return Math.max(1, Math.round(clamp(Math.ceil(d / 3.5), base, 40) * QUALITY));
}
function renderFrame(fi) {
  const t0 = fi / FPS;
  const N = sampleCount(t0);
  acc.fill(0);
  for (let k = 0; k < N; k++) {
    const t = t0 + ((k + 0.5) / N) * (SHUTTER / FPS);
    drawScene(t);
    const d = g.getImageData(0, 0, W, H).data;
    for (let p = 0, i = 0, j = 0; p < NPX; p++, i += 4, j += 3) { acc[j] += d[i]; acc[j + 1] += d[i + 1]; acc[j + 2] += d[i + 2]; }
  }
  const look = FRAME.look(t0);                   // {vig, grain}
  const inv = 1 / N, vs = look.vig, gs = look.grain;
  const off = (Math.imul(fi + 1, 2654435761) >>> 0) & NMASK;
  for (let p = 0, i = 0, j = 0; p < NPX; p++, i += 4, j += 3) {
    const v = (1 - vs * vig[p]) * inv, n = noise[(p + off) & NMASK] * gs + 0.5;
    out[i] = acc[j] * v + n; out[i + 1] = acc[j + 1] * v + n; out[i + 2] = acc[j + 2] * v + n; out[i + 3] = 255;
  }
  return N;
}

// ---------- driver API ----------
async function loadFonts() {
  const faces = [];
  for (const w of [400, 500, 700, 900]) {
    faces.push(new FontFace('NotoSC', `url(fonts/noto-sans-sc-chinese-simplified-${w}-normal.woff2)`, { weight: String(w) }));
    faces.push(new FontFace('NotoSC', `url(fonts/noto-sans-sc-latin-${w}-normal.woff2)`, { weight: String(w), unicodeRange: 'U+0000-00FF,U+2000-206F' }));
  }
  for (const w of [400, 500, 600, 700, 800]) faces.push(new FontFace('Manrope', `url(fonts/manrope-latin-${w}-normal.woff2)`, { weight: String(w) }));
  await Promise.all(faces.map((f) => f.load().then((ff) => document.fonts.add(ff))));
}
window.ready = (async () => { await loadFonts(); if (window.initFilm) await window.initFilm(); return true; })();

// preview: single composited frame as data URL
window.previewFrame = async (t, q = 1, type = 'image/png') => {
  await window.ready; QUALITY = q;
  renderFrame(Math.round(t * FPS));
  g.setTransform(1, 0, 0, 1, 0, 0); g.putImageData(outImg, 0, 0);
  return cv.toDataURL(type, 0.92);
};
// contact sheet of many frames
window.sheet = async (times, cols = 4, tw = 640, q = 0.5) => {
  await window.ready; QUALITY = q;
  const th = Math.round((tw * H) / W), rows = Math.ceil(times.length / cols);
  const sc = document.createElement('canvas'); sc.width = cols * tw; sc.height = rows * th;
  const s = sc.getContext('2d'); s.imageSmoothingQuality = 'high';
  const tmp = new OffscreenCanvas(W, H), tc = tmp.getContext('2d');
  for (let i = 0; i < times.length; i++) {
    renderFrame(Math.round(times[i] * FPS));
    tc.putImageData(outImg, 0, 0);
    const x = (i % cols) * tw, y = Math.floor(i / cols) * th;
    s.drawImage(tmp, x, y, tw, th);
    s.fillStyle = 'rgba(0,0,0,.6)'; s.fillRect(x, y, 74, 22);
    s.fillStyle = '#fff'; s.font = '14px monospace'; s.fillText(times[i].toFixed(2) + 's', x + 6, y + 16);
  }
  return sc.toDataURL('image/jpeg', 0.9);
};
// full render: POST raw RGBA frames to the server in order
window.renderRange = async (a, b, wid) => {
  await window.ready; QUALITY = 1;
  let tot = 0;
  for (let fi = a; fi < b; fi++) {
    tot += renderFrame(fi);
    const r = await fetch(`/frame?w=${wid}&i=${fi}`, { method: 'POST', body: out });
    if (!r.ok) throw new Error('post failed ' + fi);
  }
  return tot;
};
