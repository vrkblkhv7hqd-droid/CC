// node preview.js sheet out.jpg "0,1,2" [cols] [tw] [q]   |   node preview.js frame out.png 5.2 [q]
const { chromium } = require('playwright'); const fs = require('fs'); const { start } = require('./server');
(async () => {
  const [mode, outF, arg, a4, a5, a6] = process.argv.slice(2);
  const { srv, port } = await start(async () => {});
  const br = await chromium.launch(); const pg = await br.newPage({ viewport: { width: 1920, height: 1080 } });
  pg.on('console', (m) => console.log('[page]', m.text())); pg.on('pageerror', (e) => console.log('[pageerror]', e.message, e.stack));
  await pg.goto(`http://127.0.0.1:${port}/index.html`);
  await pg.evaluate(() => window.ready);
  const t0 = Date.now(); let url;
  if (mode === 'sheet') {
    let times;
    if (arg.includes(':')) { const [a, b, n] = arg.split(':').map(Number); times = Array.from({ length: n }, (_, i) => +(a + ((b - a) * i) / (n - 1)).toFixed(3)); }
    else times = arg.split(',').map(Number);
    url = await pg.evaluate(([t, c, w, q]) => window.sheet(t, c, w, q), [times, +(a4 || 4), +(a5 || 640), +(a6 || 0.5)]);
  } else url = await pg.evaluate(([t, q]) => window.previewFrame(t, q), [+arg, +(a4 || 1)]);
  fs.writeFileSync(outF, Buffer.from(url.split(',')[1], 'base64'));
  console.log('wrote', outF, ((Date.now() - t0) / 1000).toFixed(1) + 's');
  await br.close(); srv.close();
})();
