// 导出 PDF 备用稿：node tools/export-pdf.js
// 三种语言各一份，每页 1920×1080，矢量文字。需要本机装有 Playwright（Chromium）和中文字体。
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const root = path.resolve(__dirname, '..');
const BASE = 'HogentX-Malaysia-Hotel-Briefing';
const SETS = [['', '中文'], ['-EN', 'English'], ['-BM', 'Bahasa Melayu']];

(async () => {
  const browser = await chromium.launch();
  for (const [suffix, label] of SETS) {
    const src = path.join(root, BASE + suffix + '.html');
    const out = path.join(root, BASE + suffix + '.pdf');
    if (!fs.existsSync(src)) { console.error('先运行 python3 tools/build.py'); process.exit(1); }
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
    const external = [];
    await page.route('**/*', (route) => {
      const u = route.request().url();
      if (/^(file|data|blob|about):/.test(u)) return route.continue();
      external.push(u); return route.abort();
    });
    await page.goto('file://' + src + '?print=1', { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    await page.waitForTimeout(300);
    await page.pdf({ path: out, width: '1920px', height: '1080px', printBackground: true, preferCSSPageSize: true, margin: { top: 0, right: 0, bottom: 0, left: 0 } });
    const slides = await page.evaluate(() => document.querySelectorAll('.slide').length);
    await page.close();
    if (external.length) { console.error('发现外部请求：', external); process.exit(1); }
    console.log(`已导出 ${path.basename(out)}（${label}）：${slides} 页，${(fs.statSync(out).size / 1024 / 1024).toFixed(2)} MB`);
  }
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
