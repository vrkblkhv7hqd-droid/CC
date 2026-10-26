const { chromium } = require('playwright');
const path = require('path'); const fs = require('fs'); const http = require('http');
const file = path.resolve(process.argv[2]); const out = path.resolve(process.argv[3]); const shot = process.argv[4] ? path.resolve(process.argv[4]) : null;
const root = path.dirname(file);
const mime = { '.html': 'text/html; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
const server = http.createServer((req, res) => { const p = path.join(root, decodeURIComponent(req.url.split('?')[0])); if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); } res.writeHead(200, { 'Content-Type': mime[path.extname(p)] || 'application/octet-stream' }); fs.createReadStream(p).pipe(res); });
(async () => {
  await new Promise(r => server.listen(0, r));
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 900, height: 1300 } });
  await page.goto(`http://127.0.0.1:${server.address().port}/${path.basename(file)}`, { waitUntil: 'networkidle' });
  await page.waitForTimeout(800);
  const h = await page.evaluate(() => document.querySelector('.page').scrollHeight);
  console.log('page content height px:', h, '(A4 at 96dpi = 1123px)');
  if (shot) await page.screenshot({ path: shot, fullPage: true });
  await page.emulateMedia({ media: 'print' });
  await page.pdf({ path: out, format: 'A4', printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  await browser.close(); server.close();
})().catch(e => { console.error(e); process.exit(1); });
