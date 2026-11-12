// 逐页截图并检查溢出。用法： node tools/check.js <输出目录> [宽 高]
// 依赖预装的 Playwright；通过 file:// 打开单文件演示稿。
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const deck = path.resolve(__dirname, '..');
const file = path.join(deck, 'HogentX-Investor-Update-202611.html');
const outDir = path.resolve(process.argv[2] || path.join(deck, '.check'));
const W = parseInt(process.argv[3] || '1920', 10), H = parseInt(process.argv[4] || '1080', 10);
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('pageerror', e => errors.push('pageerror: ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push('console: ' + m.text()); });
  await page.goto('file://' + file, { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);
  const n = await page.evaluate(() => document.querySelectorAll('.slide').length);
  const report = [];
  for (let i = 0; i < n; i++) {
    await page.evaluate(k => window.__deck.go(k), i);
    await page.waitForTimeout(1500);
    const issues = await page.evaluate(() => {
      const slide = document.querySelector('.slide.active');
      const stage = document.getElementById('deckStage').getBoundingClientRect();
      const scale = stage.width / 1920;
      const toStage = r => ({ l: (r.left - stage.left) / scale, t: (r.top - stage.top) / scale, r: (r.right - stage.left) / scale, b: (r.bottom - stage.top) / scale });
      const out = [];
      const inner = slide.querySelector('.slide-inner');
      const foot = slide.querySelector('.foot');
      const body = slide.querySelector('.slide-body');
      const footTop = foot ? toStage(foot.getBoundingClientRect()).t : 1080 - 66;
      // 1. 正文区内容是否压到脚注或超出画面
      if (body) {
        const b = toStage(body.getBoundingClientRect());
        if (body.scrollHeight > body.clientHeight + 2) out.push(`body scroll overflow ${body.scrollHeight - body.clientHeight}px`);
        if (b.b > footTop + 1) out.push(`body bottom ${b.b.toFixed(0)} > foot top ${footTop.toFixed(0)}`);
      }
      // 2. 任意可见元素超出 1920×1080 或越过左右内边距
      const all = slide.querySelectorAll('.slide-inner *');
      let worst = null;
      all.forEach(el => {
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const r = el.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return;
        const s = toStage(r);
        const over = Math.max(s.r - 1920 + 110, 110 - s.l, s.b - 1080 + 20, 0);
        const pastFoot = (el !== foot && !foot?.contains(el) && el.closest('.slide-body')) ? s.b - footTop : 0;
        const amount = Math.max(over, pastFoot);
        if (amount > 2 && (!worst || amount > worst.amount)) worst = { amount, tag: el.tagName.toLowerCase() + (el.className ? '.' + String(el.className).split(' ').join('.') : ''), text: (el.textContent || '').trim().slice(0, 24), box: s };
      });
      if (worst) out.push(`element overflow ${worst.amount.toFixed(0)}px: ${worst.tag} "${worst.text}" [l${worst.box.l.toFixed(0)} t${worst.box.t.toFixed(0)} r${worst.box.r.toFixed(0)} b${worst.box.b.toFixed(0)}]`);
      // 3. 标题行数
      const h2 = slide.querySelector('.title-block h2');
      if (h2) { const lh = parseFloat(getComputedStyle(h2).lineHeight); const linesN = Math.round(h2.getBoundingClientRect().height / scale / lh); if (linesN > 1) out.push(`title wraps to ${linesN} lines`); }
      // 4. 图片是否加载
      slide.querySelectorAll('img').forEach(img => { if (!img.complete || img.naturalWidth === 0) out.push('image not loaded: ' + (img.alt || img.src.slice(0, 40))); });
      const free = body && foot ? (footTop - toStage(body.getBoundingClientRect()).b) : null;
      return { issues: out, label: slide.dataset.label, free };
    });
    const name = String(i + 1).padStart(2, '0') + '.png';
    await page.screenshot({ path: path.join(outDir, name) });
    report.push({ i: i + 1, ...issues });
  }
  await browser.close();
  for (const r of report) console.log(String(r.i).padStart(2, '0'), r.label.padEnd(14, '　'), r.issues.length ? 'ISSUES: ' + r.issues.join(' | ') : 'ok');
  if (errors.length) console.log('JS errors:', errors.slice(0, 5));
  console.log('screenshots in', outDir);
})();
