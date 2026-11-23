// 逐页截图：node tools/shots.js <html> <outDir> [mode=present|read] [width] [height]
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');
(async () => {
  const [, , src, outDir, mode = 'present', w = '1920', h = '1080'] = process.argv;
  fs.mkdirSync(outDir, { recursive: true });
  const base = 'file://' + path.resolve(src);
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  const page = await ctx.newPage();
  const blocked = [], errors = [];
  await page.route('**/*', (r) => { const u = r.request().url(); if (/^(file|data|blob|about):/.test(u)) return r.continue(); blocked.push(u); return r.abort(); });
  page.on('pageerror', (e) => errors.push('pageerror: ' + e.message));
  page.on('console', (m) => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto(base + (mode === 'present' ? '?mode=present' : '?mode=read'), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const n = await page.evaluate(() => document.querySelectorAll('.slide').length);
  const report = [];
  if (mode === 'present') {
    for (let i = 0; i < n; i++) {
      await page.evaluate((k) => { location.hash = '#' + (k + 1); }, i);
      await page.waitForTimeout(260);
      const m = await page.evaluate((k) => {
        const s = document.querySelectorAll('.slide')[k];
        const foot = s.querySelector('.slide-foot');
        const scale = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--scale')) || 1;
        const sr = s.getBoundingClientRect();
        let maxBottom = 0, maxRight = 0, minFont = 999; const small = []; let lowest = '';
        s.querySelectorAll('*').forEach((el) => {
          if (el.closest('.slide-foot')) return;
          const cs = getComputedStyle(el);
          if (cs.visibility === 'hidden' || cs.display === 'none') return;
          const hasText = Array.from(el.childNodes).some((c) => c.nodeType === 3 && c.textContent.trim().length > 0);
          const isLeaf = hasText || el.tagName === 'IMG' || el.tagName === 'INPUT' || el.tagName === 'BUTTON';
          if (!isLeaf) return;
          const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) return;
          const b = (r.bottom - sr.top) / scale, rt = (r.right - sr.left) / scale;
          if (b > maxBottom) { maxBottom = b; lowest = (el.className || el.tagName) + ':' + (el.textContent || '').trim().slice(0, 16); }
          maxRight = Math.max(maxRight, rt);
          if (hasText) { const fs = parseFloat(cs.fontSize); if (fs < minFont) minFont = fs; if (fs < 20) small.push(el.className + ':' + fs + ':' + el.textContent.trim().slice(0, 14)); }
        });
        const footTop = foot ? (foot.getBoundingClientRect().top - sr.top) / scale : 1080;
        return { id: s.id, contentBottom: Math.round(maxBottom), footTop: Math.round(footTop), slack: Math.round(footTop - maxBottom), maxRight: Math.round(maxRight), minFont, small: small.slice(0, 6), lowest };
      }, i);
      const file = path.join(outDir, String(i + 1).padStart(2, '0') + '-' + m.id + '.png');
      await page.screenshot({ path: file });
      report.push(m);
    }
  } else {
    await page.waitForTimeout(300);
    const file = path.join(outDir, 'read-' + w + '.png');
    await page.screenshot({ path: file, fullPage: true });
    const info = await page.evaluate(() => ({ scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth, height: document.documentElement.scrollHeight }));
    report.push(info);
  }
  console.log(JSON.stringify({ mode, slides: n, blocked, errors, report }, null, 1));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
