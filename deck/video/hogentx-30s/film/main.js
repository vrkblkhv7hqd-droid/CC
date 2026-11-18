// ---------- scene dispatch ----------
const LOOKS = [{ vig: 0.36, grain: 2.0 }, { vig: 0.08, grain: 1.2 }, { vig: 0.22, grain: 1.5 }, { vig: 0.4, grain: 2.0 }];
function zoneWeights(cam) {
  const f = BOUND.map((_, k) => clamp(0.5 + boundDist(k, cam) / 1500));
  return [1 - f[0], f[0] - f[1], f[1] - f[2], f[2]];
}
const FRAME = {
  look(t) {
    const w = zoneWeights(cameraAt(t)); let v = 0, gr = 0;
    for (let i = 0; i < 4; i++) { v += w[i] * LOOKS[i].vig; gr += w[i] * LOOKS[i].grain; }
    return { vig: v, grain: gr };
  },
  baseSamples(t) { return 5; },
};
function drawScene(t) {
  const cam = (CAM = cameraAt(t));
  g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over';
  GL.setTransform(1, 0, 0, 1, 0, 0); GL.globalAlpha = 1; GL.clearRect(0, 0, glowCv.width, glowCv.height);
  g.fillStyle = '#040915'; g.fillRect(0, 0, W, H);
  const zones = [
    { bg: drawNightBg, draw: (t, cam) => { drawNight(t, cam); drawNightLine(t, cam); drawNightText(t, cam); } },
    { bg: drawPaperBg, draw: drawRoles },
    { bg: drawBlueBg, draw: drawProof },
    { bg: drawFinalBg, draw: drawFinal },
  ];
  for (let z = 0; z < 4; z++) {
    if (!zoneVisible(z, cam)) continue;
    g.save(); GL.save();
    setWorld(cam, 1); clipZone(z);
    // background: path in world space, paint in screen space
    setWorld(cam, 1);
    if (z > 0) halfPlane(g, z - 1); else { g.beginPath(); g.rect(-1e5, -1e5, 2e5, 2e5); }
    setScreen();
    zones[z].bg(t, cam);
    setWorld(cam, 1);
    drawDebrisZone(z, cam);
    zones[z].draw(t, cam);
    g.restore(); GL.restore();
  }
  applyBloom(1);
  setScreen();
  drawOverlay(t, cam);
}
function drawDebrisZone(z, cam) { drawDebris(cam); }
// full-frame flashes on the hits
function drawOverlay(t, cam) {
  const fl = (t0, a, d = 0.35) => { const f = t - t0; if (f < 0 || f > d) return; g.globalAlpha = a * Math.pow(1 - f / d, 2.2); g.globalCompositeOperation = 'lighter'; g.fillStyle = '#BFD2FF'; g.fillRect(0, 0, W, H); g.globalCompositeOperation = 'source-over'; g.globalAlpha = 1; };
  fl(T_STRIKE, 0.2); fl(25.0, 0.3);
}
window.initFilm = async () => {};
