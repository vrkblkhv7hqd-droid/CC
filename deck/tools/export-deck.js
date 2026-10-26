// QA: screenshot every slide of a frontend-slides deck at 1920x1080 and report overflow.
// Usage: node qa-screenshot.js <deck.html> <outdir> [--pdf out.pdf]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
const http = require('http');

const deck = path.resolve(process.argv[2]);
const outdir = path.resolve(process.argv[3] || 'shots');
const pdfIdx = process.argv.indexOf('--pdf');
const pdfOut = pdfIdx > -1 ? path.resolve(process.argv[pdfIdx + 1]) : null;
fs.mkdirSync(outdir, { recursive: true });

// tiny static server so relative assets + fonts resolve like a real file share
const root = path.dirname(deck);
const mime = { '.html': 'text/html; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.css': 'text/css', '.js': 'text/javascript', '.woff2': 'font/woff2', '.ttf': 'font/ttf' };
const server = http.createServer((req, res) => {
  const p = path.join(root, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(root) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': mime[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});

(async () => {
  await new Promise(r => server.listen(0, r));
  const url = `http://127.0.0.1:${server.address().port}/${path.basename(deck)}`;
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', e => consoleErrors.push('PAGEERROR ' + e.message));
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.mouse.move(960, 540); // keep the pointer off the edit hotzone
  await page.waitForTimeout(800);
  const n = await page.evaluate(() => document.querySelectorAll('.slide').length);
  const report = [];
  for (let i = 0; i < n; i++) {
    await page.evaluate(i => { window.__deck && window.__deck.go(i); }, i);
    await page.waitForTimeout(1500); // let staggered reveal animations finish
    const r = await page.evaluate(i => {
      const slide = document.querySelectorAll('.slide')[i];
      const sb = slide.getBoundingClientRect();
      const issues = [];
      const all = slide.querySelectorAll('*');
      all.forEach(el => {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const b = el.getBoundingClientRect();
        if (b.width === 0 || b.height === 0) return;
        // element pokes outside the slide stage (allow 1px slack)
        if (b.right > sb.right + 1 || b.bottom > sb.bottom + 1 || b.left < sb.left - 1 || b.top < sb.top - 1) {
          issues.push(`OUT-OF-STAGE <${el.tagName.toLowerCase()} class="${el.className}"> ${Math.round(b.left)},${Math.round(b.top)} ${Math.round(b.width)}x${Math.round(b.height)}`);
        }
        // text clipped inside its own box
        if ((cs.overflow === 'hidden' || cs.overflowY === 'hidden') && el.scrollHeight > el.clientHeight + 2 && el.textContent.trim()) {
          issues.push(`CLIPPED <${el.tagName.toLowerCase()} class="${el.className}"> scroll ${el.scrollHeight} > client ${el.clientHeight}`);
        }
        // tiny text
        const fs = parseFloat(cs.fontSize);
        if (fs && fs < 18 && el.children.length === 0 && el.textContent.trim().length > 0) {
          issues.push(`SMALL-TEXT ${fs}px <${el.tagName.toLowerCase()} class="${el.className}"> "${el.textContent.trim().slice(0, 30)}"`);
        }
      });
      // sibling overlap among direct children of common layout containers
      const containers = slide.querySelectorAll('.grid, .cols, .cards, .row, .slide-body');
      containers.forEach(c => {
        const kids = Array.from(c.children).filter(k => getComputedStyle(k).position !== 'absolute');
        for (let a = 0; a < kids.length; a++) for (let b = a + 1; b < kids.length; b++) {
          const A = kids[a].getBoundingClientRect(), B = kids[b].getBoundingClientRect();
          const ox = Math.min(A.right, B.right) - Math.max(A.left, B.left);
          const oy = Math.min(A.bottom, B.bottom) - Math.max(A.top, B.top);
          if (ox > 4 && oy > 4) issues.push(`OVERLAP in .${c.className.split(' ')[0]}: child ${a} and ${b} overlap ${Math.round(ox)}x${Math.round(oy)}`);
        }
      });
      return { title: (slide.querySelector('h1,h2') || {}).textContent || '', issues: Array.from(new Set(issues)) };
    }, i);
    const file = path.join(outdir, `slide-${String(i + 1).padStart(2, '0')}.png`);
    await page.screenshot({ path: file });
    report.push({ slide: i + 1, title: r.title.trim(), issues: r.issues });
  }
  if (pdfOut) {
    // print mode: viewport-base.css lays slides out one per page
    await page.emulateMedia({ media: 'print' });
    await page.pdf({ path: pdfOut, width: '1920px', height: '1080px', printBackground: true, preferCSSPageSize: false, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
  }
  await browser.close();
  server.close();
  const bad = report.filter(r => r.issues.length);
  console.log(JSON.stringify({ slides: n, consoleErrors, problems: bad }, null, 1));
})().catch(e => { console.error(e); process.exit(1); });
