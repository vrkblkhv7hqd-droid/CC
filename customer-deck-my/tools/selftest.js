// 功能自测：node tools/selftest.js
// 在无网络的条件下打开成品文件，检查翻页、目录、放大截图、现场填写、手机阅读、无脚本阅读和打印排版。
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const FILE = path.resolve(__dirname, '..', 'HogentX-Malaysia-Hotel-Briefing.html');
const URL = 'file://' + FILE;
const results = [];
const ok = (name, pass, detail) => { results.push({ name, pass: !!pass, detail: detail || '' }); };

async function newPage(browser, viewport, extra) {
  const ctx = await browser.newContext(Object.assign({ viewport }, extra || {}));
  const page = await ctx.newPage();
  page._external = []; page._errors = [];
  await page.route('**/*', (route) => {
    const u = route.request().url();
    if (/^(file|data|blob|about):/.test(u)) return route.continue();
    page._external.push(u); return route.abort();
  });
  page.on('pageerror', (e) => page._errors.push(e.message));
  page.on('console', (m) => { if (m.type() === 'error') page._errors.push(m.text()); });
  return page;
}

(async () => {
  if (!fs.existsSync(FILE)) { console.error('先运行 python3 tools/build.py'); process.exit(1); }
  const browser = await chromium.launch();

  // ---------- 投屏模式 ----------
  let page = await newPage(browser, { width: 1920, height: 1080 });
  await page.goto(URL, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
  ok('宽屏自动进入投屏模式', await page.evaluate(() => document.documentElement.classList.contains('present')));
  ok('第一页可见，其余隐藏', await page.evaluate(() => document.querySelectorAll('.slide.is-current').length === 1 && document.querySelector('.slide').classList.contains('is-current')));
  const cur = () => page.evaluate(() => Array.prototype.indexOf.call(document.querySelectorAll('.slide'), document.querySelector('.slide.is-current')) + 1);
  await page.keyboard.press('ArrowRight'); await page.keyboard.press('PageDown'); await page.keyboard.press('Space');
  ok('方向键、PageDown、空格向后翻页', (await cur()) === 4, '当前页 ' + (await cur()));
  await page.keyboard.press('ArrowLeft');
  ok('左方向键向前翻页', (await cur()) === 3);
  await page.keyboard.press('End');
  ok('End 跳到最后一页', (await cur()) === total);
  await page.keyboard.press('ArrowRight');
  ok('最后一页再往后不越界', (await cur()) === total);
  await page.keyboard.press('Home');
  ok('Home 回到第一页', (await cur()) === 1);
  await page.evaluate(() => { location.hash = '#14'; });
  await page.waitForTimeout(200);
  ok('网址加 #14 直达第 14 页', (await cur()) === 14);

  // 每页都不溢出、字号不小于 20px
  const layout = await page.evaluate(async () => {
    const out = [];
    const slides = Array.from(document.querySelectorAll('.slide'));
    for (let i = 0; i < slides.length; i++) {
      location.hash = '#' + (i + 1);
      await new Promise((r) => setTimeout(r, 60));
      const s = slides[i]; const sr = s.getBoundingClientRect();
      const scale = sr.width / 1920;
      const foot = s.querySelector('.slide-foot');
      const footTop = foot ? (foot.getBoundingClientRect().top - sr.top) / scale : 1080;
      let bottom = 0, right = 0, minFont = 99;
      s.querySelectorAll('.card, .note, .term, .status-col, .sheet, .shot-frame, .shot-label, .table-wrap, .money, p, li, h2, h3, td, th, dd, dt, span, b, label, input, button').forEach((el) => {
        if (el.closest('.slide-foot')) return;
        const r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
        bottom = Math.max(bottom, (r.bottom - sr.top) / scale); right = Math.max(right, (r.right - sr.left) / scale);
        const hasText = Array.from(el.childNodes).some((c) => c.nodeType === 3 && c.textContent.trim());
        if (hasText) minFont = Math.min(minFont, parseFloat(getComputedStyle(el).fontSize));
      });
      out.push({ id: s.id, over: Math.round(bottom - footTop), right: Math.round(right), minFont });
    }
    return out;
  });
  const overflow = layout.filter((l) => l.over > 0 || l.right > 1920);
  ok('投屏每页内容都在页脚之上、不出右边界', overflow.length === 0, overflow.map((l) => l.id + ':' + l.over).join(' '));
  const small = layout.filter((l) => l.minFont < 20);
  ok('投屏文字不小于 20px', small.length === 0, small.map((l) => l.id + ':' + l.minFont).join(' '));

  // 目录
  await page.evaluate(() => { location.hash = '#1'; });
  await page.keyboard.press('m');
  ok('按 M 打开目录', await page.evaluate(() => document.getElementById('toc').classList.contains('is-open')));
  ok('目录条数等于页数', (await page.evaluate(() => document.querySelectorAll('#tocList button').length)) === total);
  await page.click('#tocList li:nth-child(5) button');
  ok('点目录第 5 条跳到第 5 页并关闭目录', (await cur()) === 5 && !(await page.evaluate(() => document.getElementById('toc').classList.contains('is-open'))));

  // 放大截图：标注跟着一起出现
  const firstShot = await page.evaluate(() => {
    const slides = Array.from(document.querySelectorAll('.slide'));
    const i = slides.findIndex((s) => s.querySelector('.shot-frame img[src^="data:image/png"]'));
    location.hash = '#' + (i + 1); return i + 1;
  });
  await page.waitForTimeout(250);
  await page.click('.slide.is-current .shot-frame');
  const lb = await page.evaluate(() => ({ open: document.getElementById('lightbox').classList.contains('is-open'), cap: document.getElementById('lightboxCap').textContent }));
  ok('点击截图可放大（第 ' + firstShot + ' 页）', lb.open);
  ok('放大后仍带来源与验证范围', /来源：2026-11-12/.test(lb.cap) && /不证明马来西亚门店当前接入或实际运营结果/.test(lb.cap));
  await page.keyboard.press('Escape');
  ok('Esc 关闭放大图', !(await page.evaluate(() => document.getElementById('lightbox').classList.contains('is-open'))));

  // 现场可填：输入时方向键不翻页；换算正确
  await page.evaluate(() => { const s = document.getElementById('measure'); location.hash = '#' + (Array.prototype.indexOf.call(document.querySelectorAll('.slide'), s) + 1); });
  await page.waitForTimeout(200);
  const before = await cur();
  await page.fill('#calcNights', '1000'); await page.fill('#calcNet', '100');
  await page.focus('#calcNights'); await page.keyboard.press('ArrowRight');
  ok('在输入框里按方向键不会翻页', (await cur()) === before);
  const calc = await page.evaluate(() => Array.from(document.querySelectorAll('[data-fee]')).map((r) => [r.getAttribute('data-fee'), r.querySelector('[data-out="per"]').textContent, r.querySelector('[data-out="eq"]').textContent]));
  ok('换算：699÷1000=0.70、699÷100=7.0', calc[0][1] === 'RM 0.70' && calc[0][2].indexOf('7.0') === 0, JSON.stringify(calc));
  ok('换算：9,980÷1000=9.98、9,980÷100=99.8', calc[2][1] === 'RM 9.98' && calc[2][2].indexOf('99.8') === 0);
  await page.fill('#calcNights', ''); await page.fill('#calcNet', 'abc');
  const blank = await page.evaluate(() => document.querySelector('[data-fee] [data-out="per"]').textContent + document.querySelector('[data-fee] [data-out="eq"]').textContent);
  ok('没填或填错时显示“—”，不显示错误数字', blank === '——');

  // 三个问题 → 试点里的对应事项
  await page.evaluate(() => { location.hash = '#2'; });
  await page.waitForTimeout(150);
  await page.click('.choice[data-q="avail"] button[data-v="no"]');
  ok('“答不上”会在试点页标出对应的事', await page.evaluate(() => document.querySelector('.job[data-q="avail"]').classList.contains('is-picked') && !document.querySelector('.job[data-q="price"]').classList.contains('is-picked')));

  ok('投屏模式没有外部请求', page._external.length === 0, page._external.join(' '));
  ok('投屏模式没有脚本错误', page._errors.length === 0, page._errors.join(' | '));
  await page.context().close();

  // ---------- 手机阅读 ----------
  page = await newPage(browser, { width: 390, height: 844 }, { deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  await page.goto(URL, { waitUntil: 'load' });
  const m = await page.evaluate(() => {
    let minBody = 99;
    document.querySelectorAll('.slide p, .slide li, .slide dd').forEach((el) => { const f = parseFloat(getComputedStyle(el).fontSize); if (el.textContent.trim() && !el.classList.contains('small') && !el.classList.contains('tiny') && !el.classList.contains('kicker') && !el.closest('.shot-cap') && f < minBody) minBody = f; });
    return { present: document.documentElement.classList.contains('present'), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, allVisible: Array.from(document.querySelectorAll('.slide')).every((s) => s.getBoundingClientRect().height > 100), minBody };
  });
  ok('手机上是竖向阅读模式', !m.present && m.allVisible);
  ok('手机上没有横向滚动', m.sw <= m.cw, m.sw + ' > ' + m.cw);
  ok('手机正文不小于 14px', m.minBody >= 14, String(m.minBody));
  ok('手机阅读没有外部请求和脚本错误', page._external.length === 0 && page._errors.length === 0, page._errors.join(' | '));
  await page.context().close();

  // ---------- 关闭脚本也能读 ----------
  page = await newPage(browser, { width: 390, height: 844 }, { javaScriptEnabled: false });
  await page.goto(URL, { waitUntil: 'load' });
  const nojs = await page.evaluate(() => ({ slides: document.querySelectorAll('.slide').length, visible: Array.from(document.querySelectorAll('.slide')).every((s) => s.getBoundingClientRect().height > 100), imgs: Array.from(document.images).filter((i) => i.getAttribute('src')).every((i) => i.naturalWidth > 0), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth }));
  ok('关闭脚本时所有页面和图片仍可阅读', nojs.visible && nojs.imgs && nojs.sw <= nojs.cw, JSON.stringify(nojs));
  await page.context().close();

  // ---------- 打印排版 ----------
  page = await newPage(browser, { width: 1920, height: 1080 });
  await page.goto(URL + '?print=1', { waitUntil: 'load' });
  const pr = await page.evaluate(() => Array.from(document.querySelectorAll('.slide')).map((s) => { const r = s.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }));
  ok('打印排版：每页 1920×1080', pr.every((x) => x[0] === 1920 && x[1] === 1080), JSON.stringify(pr.slice(0, 3)));
  await page.context().close();

  await browser.close();
  const failed = results.filter((r) => !r.pass);
  results.forEach((r) => console.log((r.pass ? '  ✓ ' : '  ✗ ') + r.name + (r.pass || !r.detail ? '' : '  →  ' + r.detail)));
  console.log(failed.length ? `未通过 ${failed.length} 项（共 ${results.length} 项）` : `全部通过（${results.length} 项，${total} 页）`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
