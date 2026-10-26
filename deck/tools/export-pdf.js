// Export the deck to a vector PDF (one 1920x1080 page per slide).
// Usage (from the deck folder): node tools/export-pdf.js [output.pdf]
// Needs Playwright with Chromium; serves the folder over HTTP so fonts and images load.
const { chromium } = require('playwright');
const http = require('http');
const fs = require('fs');
const path = require('path');

const deckDir = path.resolve(__dirname, '..');
const out = path.resolve(process.argv[2] || path.join(deckDir, 'HogentX-新马合作交流.pdf'));
const types = { '.html': 'text/html; charset=utf-8', '.png': 'image/png', '.svg': 'image/svg+xml', '.jpg': 'image/jpeg' };

const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split('?')[0].split('#')[0]);
  const file = path.join(deckDir, rel === '/' ? 'index.html' : rel);
  fs.readFile(file, (err, data) => {
    if (err) { res.writeHead(404); res.end(); return; }
    res.writeHead(200, { 'Content-Type': types[path.extname(file)] || 'application/octet-stream' });
    res.end(data);
  });
}).listen(0, async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto(`http://127.0.0.1:${server.address().port}/index.html?static`, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  // Show every slide in its final (post-animation) state for print.
  await page.evaluate(() => document.querySelectorAll('.slide').forEach(s => s.classList.add('visible')));
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: out, width: '1920px', height: '1080px', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await browser.close();
  server.close();
  console.log('wrote', out, (fs.statSync(out).size / 1e6).toFixed(1) + ' MB');
});
