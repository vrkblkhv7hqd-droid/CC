// 功能自测：node tools/selftest.js
// 在断网条件下打开三份成品文件，检查：翻页与分步出现、目录、三语切换、按酒店数字算账、计时与黑屏、
// 放大截图、手机阅读、无脚本阅读、打印排版，以及每一页在三种语言下都不溢出。需要 Playwright（Chromium）。
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const ROOT = path.resolve(__dirname, '..');
const FILES = {
  zh: path.join(ROOT, 'HogentX-Malaysia-Hotel-Briefing.html'),
  en: path.join(ROOT, 'HogentX-Malaysia-Hotel-Briefing-EN.html'),
  ms: path.join(ROOT, 'HogentX-Malaysia-Hotel-Briefing-BM.html'),
};
const URLS = Object.fromEntries(Object.entries(FILES).map(([k, f]) => [k, 'file://' + f]));
const NAMES = { zh: '中文', en: 'English', ms: 'Bahasa Melayu' };
const HTML_LANG = { zh: 'zh-CN', en: 'en', ms: 'ms' };
const TOTAL = 17;
const IDS = ['cover', 'shift', 'leaks', 'math', 'what', 'avail', 'price', 'net', 'daily', 'grow', 'us', 'plans', 'start', 'screens', 'who', 'measure', 'sources'];
const MIN_FONT = 20; // 投屏时任何文字不小于 20px（按 1920 宽计）

const results = [];
const ok = (name, pass, detail) => { results.push({ name, pass: !!pass, detail: detail || '' }); };

async function newPage(browser, viewport, extra) {
  const ctx = await browser.newContext(Object.assign({ viewport, reducedMotion: 'reduce' }, extra || {}));
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
const text = (page, sel) => page.evaluate((s) => { const el = document.querySelector(s); return el ? el.textContent.trim() : null; }, sel);
const currentId = (page) => page.evaluate(() => { const s = document.querySelector('.slide.is-current'); return s ? s.id : null; });
const stepsOn = (page) => page.evaluate(() => document.querySelectorAll('.slide.is-current [data-step].is-on').length);
const htmlLang = (page) => page.evaluate(() => document.documentElement.lang);

// 逐页量版面：内容不压页脚、不出右边界、不压标题，字号不小于下限
async function measure(page) {
  return page.evaluate(async (minFont) => {
    const out = [];
    const slides = Array.from(document.querySelectorAll('.slide'));
    for (let i = 0; i < slides.length; i++) {
      location.hash = '#' + (i + 1);
      await new Promise((r) => setTimeout(r, 50));
      const s = slides[i], sr = s.getBoundingClientRect(), scale = sr.width / 1920;
      const foot = s.querySelector('.slide-foot');
      const footTop = foot ? (foot.getBoundingClientRect().top - sr.top) / scale : 1080;
      const head = s.querySelector('.slide-head');
      const headBottom = head ? (head.getBoundingClientRect().bottom - sr.top) / scale : 0;
      const body = s.querySelector('.slide-body');
      const bodyTop = body && body.firstElementChild ? (body.firstElementChild.getBoundingClientRect().top - sr.top) / scale : 9999;
      let bottom = 0, right = 0, small = 99, who = '';
      s.querySelectorAll('*').forEach((el) => {
        if (el.closest('.slide-foot') || el.closest('svg')) return;
        const cs = getComputedStyle(el);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        const r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
        const hasText = Array.from(el.childNodes).some((c) => c.nodeType === 3 && c.textContent.trim());
        if (!hasText && !/^(IMG|INPUT|BUTTON)$/.test(el.tagName) && !el.matches('.card, .viz, .plan, .leak, .callout')) return;
        bottom = Math.max(bottom, (r.bottom - sr.top) / scale);
        right = Math.max(right, (r.right - sr.left) / scale);
        if (hasText) { const f = parseFloat(cs.fontSize); if (f < small) { small = f; who = (el.className || el.tagName) + ':' + el.textContent.trim().slice(0, 12); } }
      });
      // 图表里的文字：按图在舞台上的实际缩放折算
      s.querySelectorAll('svg text').forEach((t) => {
        const svg = t.ownerSVGElement, vb = svg.viewBox.baseVal;
        if (!vb || !vb.width) return;
        const f = parseFloat(getComputedStyle(t).fontSize) * (svg.getBoundingClientRect().width / scale) / vb.width;
        if (f < small) { small = f; who = 'svg:' + t.textContent.trim().slice(0, 12); }
      });
      out.push({ id: s.id, over: Math.round(bottom - footTop), right: Math.round(right), headClash: Math.round(headBottom - bodyTop), small: Math.round(small * 10) / 10, who, tooSmall: small < minFont });
    }
    location.hash = '#1';
    return out;
  }, MIN_FONT);
}

(async () => {
  for (const f of Object.values(FILES)) if (!fs.existsSync(f)) { console.error('先运行 python3 tools/build.py'); process.exit(1); }
  const browser = await chromium.launch();

  // ------------------------------------------------------------------ 三份文件：加载、默认语言、版面
  for (const lang of ['zh', 'en', 'ms']) {
    const page = await newPage(browser, { width: 1920, height: 1080 });
    await page.goto(URLS[lang] + '?mode=present', { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const n = await page.evaluate(() => document.querySelectorAll('.slide').length);
    ok(`[${NAMES[lang]}] 共 ${TOTAL} 页`, n === TOTAL, '实际 ' + n);
    const ids = await page.evaluate(() => Array.from(document.querySelectorAll('.slide')).map((s) => s.id));
    ok(`[${NAMES[lang]}] 页面顺序`, JSON.stringify(ids) === JSON.stringify(IDS), ids.join(','));
    ok(`[${NAMES[lang]}] 打开时的语言`, (await htmlLang(page)) === HTML_LANG[lang]);
    const layout = await measure(page);
    const bad = layout.filter((r) => r.over > 0 || r.right > 1920 - 100 || r.headClash > 0);
    ok(`[${NAMES[lang]}] 每页内容不压页脚、不出边界、不压标题`, bad.length === 0, bad.map((r) => `${r.id}: 超出 ${r.over}px, 右 ${r.right}, 压标题 ${r.headClash}`).join('; '));
    const tiny = layout.filter((r) => r.tooSmall);
    ok(`[${NAMES[lang]}] 投屏时文字不小于 ${MIN_FONT}px`, tiny.length === 0, tiny.map((r) => `${r.id}: ${r.small}px（${r.who}）`).join('; '));
    if (lang !== 'zh') {
      const cjk = await page.evaluate(() => {
        const left = [];
        document.querySelectorAll('.slide *').forEach((el) => {
          if (el.closest('[data-noi18n]')) return;
          Array.from(el.childNodes).forEach((c) => {
            if (c.nodeType !== 3) return;
            const t = c.textContent.replace(/住小叮/g, '');
            if (/[\u3400-\u9fff]/.test(t)) left.push(t.trim().slice(0, 14));
          });
        });
        return left;
      });
      ok(`[${NAMES[lang]}] 页面上除“住小叮”外没有中文`, cjk.length === 0, cjk.slice(0, 5).join(' | '));
    }
    ok(`[${NAMES[lang]}] 没有外部请求`, page._external.length === 0, page._external.join(', '));
    ok(`[${NAMES[lang]}] 没有脚本报错`, page._errors.length === 0, page._errors.join(' | '));
    await page.context().close();
  }

  // ------------------------------------------------------------------ 投屏：翻页与分步出现
  {
    const page = await newPage(browser, { width: 1920, height: 1080 });
    await page.goto(URLS.zh + '?mode=present', { waitUntil: 'load' });
    ok('投屏：从封面开始', (await currentId(page)) === 'cover');
    await page.keyboard.press('ArrowRight');
    ok('投屏：→ 到第 2 页，要点先不出现', (await currentId(page)) === 'shift' && (await stepsOn(page)) === 0);
    for (let k = 1; k <= 4; k++) { await page.keyboard.press('ArrowRight'); }
    ok('投屏：再按 4 次，4 条依次出现，仍在第 2 页', (await currentId(page)) === 'shift' && (await stepsOn(page)) === 4);
    await page.keyboard.press('PageDown');
    ok('投屏：翻页笔（PageDown）到第 3 页', (await currentId(page)) === 'leaks');
    await page.keyboard.press('ArrowLeft');
    ok('投屏：← 回到第 2 页，内容全部可见', (await currentId(page)) === 'shift' && (await stepsOn(page)) === 4);
    await page.keyboard.press('End');
    ok('投屏：End 到最后一页', (await currentId(page)) === 'sources');
    await page.keyboard.press('Home');
    ok('投屏：Home 回到封面', (await currentId(page)) === 'cover');
    await page.evaluate(() => { location.hash = '#plans'; });
    await page.waitForTimeout(80);
    ok('投屏：#plans 直达方案页', (await currentId(page)) === 'plans');
    await page.evaluate(() => { location.hash = '#13'; });
    await page.waitForTimeout(80);
    ok('投屏：#13 直达收尾页', (await currentId(page)) === 'start');
    const pageNo = await text(page, '.slide.is-current .foot-page');
    ok('投屏：页码显示 13 / 17', pageNo === '13 / 17', pageNo);
    const bar = await page.evaluate(() => document.getElementById('progressBar').style.width);
    ok('投屏：进度条跟着走', Math.abs(parseFloat(bar) - (13 / 17) * 100) < 0.5, bar);

    // 目录
    await page.keyboard.press('m');
    const tocN = await page.evaluate(() => document.querySelectorAll('#toc.is-open #tocList button').length);
    ok('目录：按 M 打开，列出全部页面', tocN === TOTAL, '实际 ' + tocN);
    await page.click('#tocList li:nth-child(4) button');
    ok('目录：点第 4 项跳到“算一笔”', (await currentId(page)) === 'math');

    // 按酒店数字算账
    const calc = async () => page.evaluate(() => {
      const g = (k) => { const el = document.querySelector('[data-out="' + k + '"]'); return el ? el.textContent : null; };
      return { rev: g('rev'), nights: g('nights'), empty: g('empty'), occ1: g('occ1'), adr5: g('adr5'), emptyMonth: g('emptyMonth'),
        eq: Array.from(document.querySelectorAll('[data-eq]')).map((e) => e.textContent) };
    });
    let c = await calc();
    ok('算一笔：默认是全马平均（65 间、RM 231.3、51.2%）', c.rev === 'RM 2,809,647' && c.nights === '12,147' && c.empty === '32' && c.occ1 === 'RM 54,876' && c.adr5 === 'RM 60,736', JSON.stringify(c));
    ok('算一笔：月费折成房晚 4 / 11 / 44，每月空着 965 个房晚', c.eq.join('/') === '4/11/44' && c.emptyMonth === '965', JSON.stringify(c));
    await page.fill('#cRooms', '100'); await page.fill('#cAdr', '200'); await page.fill('#cOcc', '70');
    c = await calc();
    ok('算一笔：改成 100 间、RM 200、70% 后跟着变', c.rev === 'RM 5,110,000' && c.nights === '25,550' && c.empty === '30' && c.occ1 === 'RM 73,000' && c.adr5 === 'RM 127,750' && c.eq.join('/') === '4/13/50' && c.emptyMonth === '913', JSON.stringify(c));
    await page.fill('#cOcc', '');
    c = await calc();
    ok('算一笔：没填全时显示“—”，不出现 NaN', c.rev === '—' && c.eq.every((x) => x === '—') && !JSON.stringify(c).includes('NaN'), JSON.stringify(c));
    await page.fill('#cOcc', '70');
    await page.focus('#cRooms');
    await page.keyboard.press('ArrowRight');
    ok('算一笔：在输入框里按方向键不翻页', (await currentId(page)) === 'math');
    await page.keyboard.press('PageDown');
    ok('算一笔：在输入框里用翻页笔可以翻页', (await currentId(page)) === 'what');

    // 计时与黑屏
    await page.keyboard.press('Home');
    await page.keyboard.press('t');
    let timer = await text(page, '#timer');
    ok('计时：按 T 显示“已用 / 计划”，封面计划 00:30', /^\d\d:\d\d \/ 00:30$/.test(timer || '') && await page.isVisible('#timer'), timer);
    await page.keyboard.press('ArrowRight');
    timer = await text(page, '#timer');
    ok('计时：到第 2 页，计划时间变成 02:00', /\/ 02:00$/.test(timer || ''), timer);
    await page.evaluate(() => { location.hash = '#13'; });
    await page.waitForTimeout(80);
    timer = await text(page, '#timer');
    ok('计时：讲到收尾页，计划时间 19:30', /\/ 19:30$/.test(timer || ''), timer);
    await page.keyboard.press('t');
    ok('计时：再按 T 隐藏', !(await page.isVisible('#timer')));
    await page.keyboard.press('b');
    ok('黑屏：按 B 画面全黑', await page.isVisible('.blackout'));
    await page.keyboard.press('ArrowRight');
    ok('黑屏：再按任意键恢复，页面不动', !(await page.isVisible('.blackout')) && (await currentId(page)) === 'start');

    // 放大截图
    await page.evaluate(() => { location.hash = '#us'; });
    await page.waitForTimeout(80);
    await page.click('#us .shot-frame');
    ok('截图：点一下放大', await page.isVisible('#lightbox.is-open #lightboxImg'));
    const cap = await text(page, '#lightboxCap');
    ok('截图：放大后带着图注', (cap || '').length > 4, cap);
    await page.keyboard.press('Escape');
    ok('截图：Esc 关闭', !(await page.isVisible('#lightbox.is-open')));

    // 三语切换
    await page.evaluate(() => { location.hash = '#2'; });
    await page.waitForTimeout(80);
    const tZh = await text(page, '#shift .slide-title');
    await page.keyboard.press('l');
    const tEn = await text(page, '#shift .slide-title');
    ok('三语：按 L 切到 English', (await htmlLang(page)) === 'en' && tEn !== tZh && /occupancy/i.test(tEn || ''), tEn);
    const svgEn = await page.evaluate(() => document.querySelector('#price svg .vz-direct').textContent);
    ok('三语：图表里的文字也跟着换', /booked/i.test(svgEn || ''), svgEn);
    c = await calc();
    ok('三语：切换后算出来的数字还在', c.rev === 'RM 5,110,000' && c.eq.join('/') === '4/13/50', JSON.stringify(c));
    await page.keyboard.press('l');
    ok('三语：再按 L 切到 Bahasa Melayu', (await htmlLang(page)) === 'ms' && /penghunian/i.test((await text(page, '#shift .slide-title')) || ''));
    await page.keyboard.press('l');
    ok('三语：第三次回到中文', (await htmlLang(page)) === 'zh-CN' && (await text(page, '#shift .slide-title')) === tZh);
    ok('投屏流程：没有外部请求、没有脚本报错', page._external.length === 0 && page._errors.length === 0, page._external.concat(page._errors).join(' | '));
    await page.context().close();
  }

  // ------------------------------------------------------------------ 数字跳动：动画结束后是准确数字
  {
    const ctx = await browser.newContext({ viewport: { width: 1920, height: 1080 } });
    const page = await ctx.newPage();
    await page.goto(URLS.zh + '?mode=present', { waitUntil: 'load' });
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(1100);
    const v1 = await text(page, '#shift .fact:nth-child(1) .num');
    await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(1100);
    const v3 = await text(page, '#shift .fact:nth-child(3) .num');
    ok('数字跳动：停下来是 51.2 和 −7.6', v1 === '51.2' && v3 === '\u22127.6', v1 + ' / ' + v3);
    await ctx.close();
  }

  // ------------------------------------------------------------------ 地址栏参数
  {
    const page = await newPage(browser, { width: 1920, height: 1080 });
    await page.goto(URLS.zh + '?mode=present&lang=ms#plans', { waitUntil: 'load' });
    ok('参数：?lang=ms#plans 直接以马来文打开方案页', (await htmlLang(page)) === 'ms' && (await currentId(page)) === 'plans');
    await page.context().close();
  }

  // ------------------------------------------------------------------ 手机阅读
  for (const lang of ['zh', 'en', 'ms']) {
    const page = await newPage(browser, { width: 390, height: 844 }, { isMobile: true, hasTouch: true, deviceScaleFactor: 2 });
    await page.goto(URLS[lang], { waitUntil: 'load' });
    const m = await page.evaluate(() => ({ present: document.documentElement.classList.contains('present'), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
      hiddenSteps: Array.from(document.querySelectorAll('[data-step]')).filter((e) => getComputedStyle(e).opacity !== '1').length,
      small: Array.from(document.querySelectorAll('.slide p, .slide li, .slide b, .slide span, .slide td, .slide th')).filter((e) => e.offsetParent && Array.from(e.childNodes).some((c) => c.nodeType === 3 && c.textContent.trim()) && parseFloat(getComputedStyle(e).fontSize) < 12).length }));
    ok(`[手机 · ${NAMES[lang]}] 默认是竖向阅读`, !m.present);
    ok(`[手机 · ${NAMES[lang]}] 没有横向滚动`, m.sw <= m.cw, `${m.sw} > ${m.cw}`);
    ok(`[手机 · ${NAMES[lang]}] 分步内容全部直接可见`, m.hiddenSteps === 0, '隐藏 ' + m.hiddenSteps);
    ok(`[手机 · ${NAMES[lang]}] 文字不小于 12px`, m.small === 0, '偏小 ' + m.small);
    if (lang === 'zh') {
      await page.fill('#cRooms', '80');
      ok('[手机] 算一笔可以直接填', (await text(page, '[data-out="rev"]')) === 'RM 3,458,028', await text(page, '[data-out="rev"]'));
      await page.click('.lang-switch button[data-lang="en"]');
      ok('[手机] 顶栏可以切换语言', (await htmlLang(page)) === 'en');
      await page.click('#tocBtn');
      ok('[手机] 目录可以打开', await page.isVisible('#toc.is-open'));
      await page.goBack();
      ok('[手机] 按返回键只关掉目录，不离开页面', !(await page.isVisible('#toc.is-open')) && page.url().startsWith('file://'));
      await page.evaluate(() => document.querySelector('#screens').scrollIntoView());
      await page.waitForTimeout(400);
      const loaded = await page.evaluate(() => Array.from(document.querySelectorAll('#screens img')).filter((i) => i.complete && i.naturalWidth > 0).length);
      ok('[手机] 滚到附页时截图能显示', loaded >= 2, '已加载 ' + loaded);
    }
    ok(`[手机 · ${NAMES[lang]}] 没有外部请求、没有脚本报错`, page._external.length === 0 && page._errors.length === 0, page._external.concat(page._errors).join(' | '));
    await page.context().close();
  }

  // ------------------------------------------------------------------ 无脚本（邮件、聊天工具里的预览）
  {
    const page = await newPage(browser, { width: 390, height: 844 }, { javaScriptEnabled: false });
    await page.goto(URLS.en, { waitUntil: 'load' });
    const title = await page.locator('.cover-title').textContent();
    const shown = await page.locator('.needs-js').evaluateAll((els) => els.filter((e) => e.offsetParent).length);
    const note = await page.locator('.no-js-note').evaluateAll((els) => els.some((e) => e.offsetParent));
    const widths = await page.locator('html').evaluate((el) => [el.scrollWidth, el.clientWidth]);
    ok('无脚本：英文版仍显示英文内容', /Every room/.test(title || ''), title);
    ok('无脚本：需要脚本的控件收起，换成文字说明', shown === 0 && note, `控件 ${shown}，说明 ${note}`);
    ok('无脚本：没有横向滚动', widths[0] <= widths[1], widths.join(' > '));
    await page.context().close();
  }

  // ------------------------------------------------------------------ 打印 / 导出 PDF
  {
    const page = await newPage(browser, { width: 1920, height: 1080 });
    await page.goto(URLS.zh + '?print=1', { waitUntil: 'load' });
    const m = await page.evaluate(() => {
      const slides = Array.from(document.querySelectorAll('.slide'));
      return { n: slides.length, sizes: slides.every((s) => Math.round(s.getBoundingClientRect().width) === 1920 && Math.round(s.getBoundingClientRect().height) === 1080),
        steps: Array.from(document.querySelectorAll('[data-step]')).every((e) => getComputedStyle(e).opacity === '1'),
        hud: ['.hud', '.progress', '.timer', '.blackout'].every((s) => { const e = document.querySelector(s); return !e || getComputedStyle(e).display === 'none'; }),
        nums: document.querySelector('#shift .num').textContent };
    });
    ok('打印：每页 1920×1080，共 17 页', m.n === TOTAL && m.sizes, JSON.stringify(m));
    ok('打印：分步内容全部印出，数字是最终值', m.steps && m.nums === '51.2', JSON.stringify(m));
    ok('打印：控制条、进度条、计时不印出', m.hud);
    await page.context().close();
  }

  await browser.close();
  const failed = results.filter((r) => !r.pass);
  for (const r of results) console.log((r.pass ? '  ✓ ' : '  ✗ ') + r.name + (r.pass || !r.detail ? '' : '  →  ' + r.detail));
  console.log(`\n${results.length - failed.length} / ${results.length} 项通过`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
