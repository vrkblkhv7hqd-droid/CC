// node render.js <startFrame> <endFrame> [workers] [segFrames]  -> chunks/seg_XXXX.mkv (lossless RGB)
const { chromium } = require('playwright'); const fs = require('fs'); const { spawn } = require('child_process'); const { start } = require('./server');
(async () => {
  const A = +process.argv[2], B = +process.argv[3], NW = +(process.argv[4] || 3), SEG = +(process.argv[5] || 60);
  fs.mkdirSync('chunks', { recursive: true });
  const segs = []; for (let a = A; a < B; a += SEG) segs.push({ id: Math.floor(a / SEG), a, b: Math.min(B, a + SEG) });
  const ff = {};
  const { srv, port } = await start(async (w, i, buf) => {
    const p = ff[w]; if (!p.stdin.write(buf)) await new Promise((r) => p.stdin.once('drain', r));
  });
  const t0 = Date.now(); let done = 0, samples = 0;
  async function worker(wi) {
    const br = await chromium.launch(); const pg = await br.newPage({ viewport: { width: 1920, height: 1080 } });
    pg.on('pageerror', (e) => console.log('[pageerror]', e.message));
    await pg.goto(`http://127.0.0.1:${port}/index.html`); await pg.evaluate(() => window.ready);
    for (;;) {
      const s = segs.shift(); if (!s) break;
      const f = `chunks/seg_${String(s.id).padStart(4, '0')}.mkv`;
      const p = spawn('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', '1920x1080', '-r', '60', '-i', '-', '-c:v', 'libx264rgb', '-qp', '0', '-preset', 'ultrafast', '-pix_fmt', 'rgb24', f], { stdio: ['pipe', 'inherit', 'inherit'] });
      ff[s.id] = p;
      const n = await pg.evaluate(([a, b, id]) => window.renderRange(a, b, id), [s.a, s.b, s.id]);
      p.stdin.end(); await new Promise((r) => p.on('close', r));
      done += s.b - s.a; samples += n;
      console.log(`seg ${s.id} [${s.a},${s.b}) by w${wi}  ${done}/${B - A} frames  ${((Date.now() - t0) / 1000).toFixed(0)}s  avgN=${(n / (s.b - s.a)).toFixed(1)}`);
    }
    await br.close();
  }
  await Promise.all(Array.from({ length: NW }, (_, i) => worker(i)));
  srv.close(); console.log('done', ((Date.now() - t0) / 1000).toFixed(0) + 's');
})();
