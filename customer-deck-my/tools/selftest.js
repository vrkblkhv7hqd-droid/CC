// 功能自测：node tools/selftest.js
// 在无网络的条件下打开三份成品文件，检查翻页、目录、三语切换、放大截图、现场填写、
// 手机阅读、无脚本阅读和打印排版。需要 Playwright（Chromium）。
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
// 投屏时文字的最小字号（已折算缩放）：中文 20px；英文、马来文句子更长，不小于 18px
const MIN_STAGE = { zh: 20, en: 18, ms: 18 };
// 英文、马来文里允许保留的中文：品牌名，以及引用截图里出现的界面用词
const CJK_OK = /住小叮|出租率|间夜|评价回复|元|中文/g;

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

// 逐页量版面：内容是否压到页脚、是否出右边界、最小字号（折算缩放后）
function measureLayout() {
  return (async () => {
    const out = [];
    const slides = Array.from(document.querySelectorAll('.slide'));
    const zoomOf = (el) => { let z = 1; for (let n = el; n && n.nodeType === 1; n = n.parentElement) { const v = parseFloat(getComputedStyle(n).zoom); if (v && v !== 1) z *= v; } return z; };
    for (let i = 0; i < slides.length; i++) {
      location.hash = '#' + (i + 1);
      await new Promise((r) => setTimeout(r, 60));
      const s = slides[i]; const sr = s.getBoundingClientRect();
      const scale = sr.width / 1920;
      const foot = s.querySelector('.slide-foot');
      const footTop = foot ? (foot.getBoundingClientRect().top - sr.top) / scale : 1080;
      const headBottom = (() => { const h = s.querySelector('.slide-head'); return h ? (h.getBoundingClientRect().bottom - sr.top) / scale : 0; })();
      const body = s.querySelector('.slide-body');
      const bodyTop = body && body.firstElementChild ? (body.firstElementChild.getBoundingClientRect().top - sr.top) / scale : 9999;
      let bottom = 0, right = 0, minFont = 99;
      s.querySelectorAll('.card, .note, .sheet, .shot-frame, .shot-label, .table-wrap, .money, p, li, h2, h3, td, th, dd, dt, span, b, label, input, button').forEach((el) => {
        if (el.closest('.slide-foot')) return;
        const r = el.getBoundingClientRect(); if (!r.width || !r.height) return;
        bottom = Math.max(bottom, (r.bottom - sr.top) / scale); right = Math.max(right, (r.right - sr.left) / scale);
        const hasText = Array.from(el.childNodes).some((c) => c.nodeType === 3 && c.textContent.trim());
        if (hasText) minFont = Math.min(minFont, parseFloat(getComputedStyle(el).fontSize) * zoomOf(el));
      });
      const footNote = foot ? foot.querySelector('.foot-note') : null;
      const footLines = footNote ? Math.round(footNote.getBoundingClientRect().height / scale / parseFloat(getComputedStyle(footNote).lineHeight)) : 1;
      out.push({ id: s.id, over: Math.round(bottom - footTop), right: Math.round(right), minFont: Math.round(minFont * 10) / 10, headOverlap: Math.round(headBottom - bodyTop), footLines });
    }
    return out;
  })();
}

(async () => {
  for (const f of Object.values(FILES)) if (!fs.existsSync(f)) { console.error('先运行 python3 tools/build.py'); process.exit(1); }
  const browser = await chromium.launch();

  // ---------- 投屏模式（中文文件） ----------
  let page = await newPage(browser, { width: 1920, height: 1080 });
  await page.goto(URLS.zh, { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  const total = await page.evaluate(() => document.querySelectorAll('.slide').length);
  ok('宽屏自动进入投屏模式', await page.evaluate(() => document.documentElement.classList.contains('present')));
  ok('舞台里只有幻灯片，没有游离内容', await page.evaluate(() => Array.from(document.getElementById('deck').children).every((c) => c.classList.contains('slide'))));
  ok('第一页可见，其余隐藏', await page.evaluate(() => document.querySelectorAll('.slide.is-current').length === 1 && document.querySelector('.slide').classList.contains('is-current')));
  const cur = () => page.evaluate(() => Array.prototype.indexOf.call(document.querySelectorAll('.slide'), document.querySelector('.slide.is-current')) + 1);
  const gotoId = async (id) => { await page.evaluate((x) => { const s = document.getElementById(x); location.hash = '#' + (Array.prototype.indexOf.call(document.querySelectorAll('.slide'), s) + 1); }, id); await page.waitForTimeout(150); };
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
  await page.evaluate(() => { location.hash = '#10'; });
  await page.waitForTimeout(200);
  ok('网址加 #10 直达第 10 页（三个方案）', (await cur()) === 10 && (await page.evaluate(() => document.querySelector('.slide.is-current').id)) === 'plans');

  // 目录
  await page.evaluate(() => { location.hash = '#1'; });
  await page.keyboard.press('m');
  ok('按 M 打开目录', await page.evaluate(() => document.getElementById('toc').classList.contains('is-open')));
  ok('目录条数等于页数', (await page.evaluate(() => document.querySelectorAll('#tocList button').length)) === total);
  await page.click('#tocList li:nth-child(5) button');
  ok('点目录第 5 条跳到第 5 页并关闭目录', (await cur()) === 5 && !(await page.evaluate(() => document.getElementById('toc').classList.contains('is-open'))));

  // 放大截图：标注跟着一起出现，字号跟着舞台缩放
  await gotoId('pace');
  await page.click('.slide.is-current .shot-frame');
  const lb = await page.evaluate(() => ({ open: document.getElementById('lightbox').classList.contains('is-open'), cap: document.getElementById('lightboxCap').textContent, label: parseFloat(getComputedStyle(document.querySelector('#lightboxCap .shot-label')).fontSize) }));
  ok('点击截图可放大', lb.open);
  ok('放大后仍带来源与验证范围', /来源：2026-11-12/.test(lb.cap) && /不证明马来西亚门店当前接入或实际运营结果/.test(lb.cap));
  ok('放大后的标注字号不小于 20px', lb.label >= 20, String(lb.label));
  await page.keyboard.press('Escape');
  ok('Esc 关闭放大图', !(await page.evaluate(() => document.getElementById('lightbox').classList.contains('is-open'))));

  // 现场可填
  await gotoId('measure');
  const before = await cur();
  await page.fill('#calcNights', '1000');
  await page.focus('#calcNights'); await page.keyboard.press('ArrowRight');
  ok('在输入框里按方向键不会翻页', (await cur()) === before);
  const calc = () => page.evaluate(() => Array.from(document.querySelectorAll('[data-fee]')).map((r) => r.querySelector('[data-out="per"]').textContent));
  let c = await calc();
  ok('换算：699÷1000=0.70、2,499÷1000=2.50、9,980÷1000=9.98', c[0] === 'RM 0.70' && c[1] === 'RM 2.50' && c[2] === 'RM 9.98', JSON.stringify(c));
  await page.fill('#calcNights', '1,500 晚'); c = await calc();
  ok('带逗号或单位的数字也能算（1,500）', c[0] === 'RM 0.47', JSON.stringify(c));
  await page.fill('#calcNights', 'abc'); c = await calc();
  ok('没填或填错时显示“—”，不显示错误数字', c.every((x) => x === '—'));
  ok('换算表只有“摊到每个卖出的房晚”，没有回本类数字', await page.evaluate(() => document.querySelectorAll('.calc-table thead th').length === 2 && !document.getElementById('calcNet')));
  await page.focus('#calcNights'); await page.keyboard.press('PageDown');
  ok('填写时按翻页笔（PageDown）可以直接翻到下一页', (await cur()) === before + 1);

  // 三个问题 → 后面先验证哪件事
  await page.evaluate(() => { location.hash = '#2'; });
  await page.waitForTimeout(150);
  await page.click('.choice[data-q="avail"] button[data-v="exp"]');
  ok('选“凭经验”也会在后面标出对应的事', await page.evaluate(() => document.querySelector('#pilot .job[data-q="avail"]').classList.contains('is-picked') && !document.querySelector('#pilot .job[data-q="price"]').classList.contains('is-picked')));
  await page.keyboard.press('Space');
  ok('点完选项按空格直接翻页，选项不被取消', (await cur()) === 3 && (await page.evaluate(() => document.querySelector('.choice[data-q="avail"] button[data-v="exp"]').getAttribute('aria-pressed') === 'true')));
  await page.evaluate(() => { location.hash = '#2'; });
  await page.waitForTimeout(150);
  await page.click('.choice[data-q="cost"] button[data-v="no"]');
  ok('问题 3 选“说不准”，试点页和对照表都标出', await page.evaluate(() => document.querySelector('#pilot .job[data-q="cost"]').classList.contains('is-picked') && document.querySelector('#measure .job[data-q="cost"]').classList.contains('is-picked')));

  // 渠道核对表 → 试点单；点事项卡片 → 试点单
  await gotoId('multi-ota');
  await page.fill('#multi-ota input.fill >> nth=0', '平台甲'); await page.fill('#multi-ota input.fill >> nth=1', '平台乙');
  await gotoId('pilot');
  ok('渠道核对表里填的 OTA 自动带到试点约定单', (await page.inputValue('#p2')) === '平台甲、平台乙', await page.inputValue('#p2'));
  await page.click('#pilot .job[data-q="avail"]');
  ok('点一下事项卡片，填进“验证哪件事”', (await page.inputValue('#p3')) === '房态与开售核对');

  // 三语切换
  await page.evaluate(() => { location.hash = '#3'; });
  await page.waitForTimeout(120);
  await page.keyboard.press('l');
  let st = await page.evaluate(() => ({ lang: document.documentElement.lang, title: document.querySelector('#what .slide-title').textContent, rail: document.querySelector('#what .rail').textContent, toc: document.querySelector('#tocList li:nth-child(3)').textContent }));
  ok('按 L 切到 English：标题、公式条、目录一起换', st.lang === 'en' && /What HogentX does/.test(st.title) && /Occupancy/.test(st.rail) && /What HogentX does/.test(st.toc), JSON.stringify(st));
  ok('切换语言后已填内容和所在页不变', (await cur()) === 3 && (await page.inputValue('#p3')) === '房态与开售核对');
  await page.keyboard.press('l');
  st = await page.evaluate(() => ({ lang: document.documentElement.lang, title: document.querySelector('#what .slide-title').textContent, ph: document.getElementById('p1').getAttribute('placeholder') }));
  ok('再按 L 切到 Bahasa Melayu（含输入框提示字）', st.lang === 'ms' && /Apa yang HogentX buat/.test(st.title) && /hotel/i.test(st.ph) && !/[一-鿿]/.test(st.ph), JSON.stringify(st));
  await page.keyboard.press('l');
  st = await page.evaluate(() => ({ lang: document.documentElement.lang, title: document.querySelector('#what .slide-title').textContent }));
  ok('第三次按 L 回到中文', st.lang === 'zh-CN' && /HogentX 做什么/.test(st.title), JSON.stringify(st));
  ok('中文文件投屏没有外部请求和脚本错误', page._external.length === 0 && page._errors.length === 0, page._external.concat(page._errors).join(' | '));
  await page.context().close();

  // ---------- 三种语言逐页量版面 ----------
  for (const lang of ['zh', 'en', 'ms']) {
    page = await newPage(browser, { width: 1920, height: 1080 });
    await page.goto(URLS[lang], { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    ok(`${NAMES[lang]} 文件打开即为 ${NAMES[lang]}`, (await page.evaluate(() => document.documentElement.getAttribute('data-lang'))) === lang);
    const layout = await page.evaluate(measureLayout);
    const overflow = layout.filter((l) => l.over > 0 || l.right > 1920 || l.headOverlap > 0);
    ok(`${NAMES[lang]}：每页内容都在标题之下、页脚之上，不出右边界`, overflow.length === 0, overflow.map((l) => `${l.id}:${l.over}/${l.headOverlap}`).join(' '));
    const small = layout.filter((l) => l.minFont < MIN_STAGE[lang] - 0.05);
    ok(`${NAMES[lang]}：投屏文字不小于 ${MIN_STAGE[lang]}px`, small.length === 0, small.map((l) => l.id + ':' + l.minFont).join(' '));
    const twoLine = layout.filter((l) => l.footLines > 1);
    ok(`${NAMES[lang]}：页脚说明都在一行内`, twoLine.length === 0, twoLine.map((l) => l.id).join(' '));
    if (lang !== 'zh') {
      const stray = await page.evaluate((okSrc) => {
        const re = new RegExp(okSrc, 'g'); const bad = [];
        document.querySelectorAll('.slide, .topbar, .hud, .overlay').forEach((root) => {
          if (root.closest('[data-noi18n]')) return;
          const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
          while (walker.nextNode()) {
            const n = walker.currentNode; if (n.parentElement.closest('[data-noi18n], script, style')) continue;
            const t = n.textContent.replace(re, '');
            if (/[㐀-鿿]/.test(t)) bad.push(t.trim().slice(0, 24));
          }
          root.querySelectorAll('[placeholder], [aria-label], [alt], [data-title], [data-label], [data-fill]').forEach((el) => {
            if (el.closest('[data-noi18n]')) return;
            ['placeholder', 'aria-label', 'alt', 'data-title', 'data-label', 'data-fill'].forEach((a) => { const v = (el.getAttribute(a) || '').replace(re, ''); if (/[㐀-鿿]/.test(v)) bad.push(a + '=' + v.slice(0, 20)); });
          });
        });
        return bad;
      }, CJK_OK.source);
      ok(`${NAMES[lang]}：页面上没有漏翻的中文`, stray.length === 0, stray.slice(0, 5).join(' | '));
    }
    ok(`${NAMES[lang]}：没有外部请求和脚本错误`, page._external.length === 0 && page._errors.length === 0, page._external.concat(page._errors).join(' | '));
    await page.context().close();
  }

  // 网址参数切换语言
  page = await newPage(browser, { width: 1920, height: 1080 });
  await page.goto(URLS.zh + '?lang=ms#10', { waitUntil: 'load' });
  ok('网址加 ?lang=ms 直接以马来文打开', await page.evaluate(() => document.documentElement.lang === 'ms' && /Tiga pelan/.test(document.querySelector('#plans .slide-title').textContent)));
  await page.context().close();

  // ---------- 手机阅读（三种语言） ----------
  for (const lang of ['zh', 'en', 'ms']) {
    for (const width of [390, 320]) {
      page = await newPage(browser, { width, height: 844 }, { deviceScaleFactor: 2, isMobile: true, hasTouch: true });
      await page.goto(URLS[lang], { waitUntil: 'load' });
      const m = await page.evaluate(() => {
        let minBody = 99, minAny = 99;
        document.querySelectorAll('.slide p, .slide li, .slide dd, .slide td').forEach((el) => {
          const cs = getComputedStyle(el); if (cs.display === 'none' || !el.textContent.trim() || !el.getClientRects().length) return;
          const f = parseFloat(cs.fontSize); minAny = Math.min(minAny, f);
          if (!el.closest('.tiny, .kicker, .shot-cap, .formula-line, thead') && !el.classList.contains('tiny')) minBody = Math.min(minBody, f);
        });
        return { present: document.documentElement.classList.contains('present'), sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth, allVisible: Array.from(document.querySelectorAll('.slide')).every((s) => s.getBoundingClientRect().height > 100), minBody, minAny, footNotes: Array.from(document.querySelectorAll('.slide-foot .foot-note:not(.foot-legend)')).filter((n) => n.getClientRects().length).length };
      });
      ok(`${NAMES[lang]} · 手机 ${width}px：竖向阅读，没有横向滚动`, !m.present && m.allVisible && m.sw <= m.cw, m.sw + ' > ' + m.cw);
      if (width === 390) {
        ok(`${NAMES[lang]} · 手机：正文不小于 16px，标注不小于 14px`, m.minBody >= 16 && m.minAny >= 14, m.minBody + ' / ' + m.minAny);
        ok(`${NAMES[lang]} · 手机：各页页脚里的说明文字都显示`, m.footNotes >= 14, String(m.footNotes));
      }
      if (lang === 'zh' && width === 390) {
        await page.tap('.lang-switch button[data-lang="en"]');
        ok('手机顶栏点 EN 切到英文', await page.evaluate(() => document.documentElement.lang === 'en' && /three sums/i.test(document.querySelector('.cover-title').textContent)));
        await page.tap('.lang-switch button[data-lang="zh"]');
        const img = page.locator('#pace .shot-frame').first();
        await img.scrollIntoViewIfNeeded(); await img.tap();
        const z0 = await page.evaluate(() => document.getElementById('lightboxImg').getBoundingClientRect().width);
        await page.tap('#lightboxImg');
        const z1 = await page.evaluate(() => document.getElementById('lightboxImg').getBoundingClientRect().width);
        ok('手机上点截图再点一下，放大到原始大小', z1 > z0 * 2, z0 + ' → ' + z1);
        await page.goBack();
        ok('手机“返回”键只关掉放大图，不离开页面', await page.evaluate(() => !document.getElementById('lightbox').classList.contains('is-open') && document.querySelectorAll('.slide').length > 0));
      }
      ok(`${NAMES[lang]} · 手机 ${width}px：没有外部请求和脚本错误`, page._external.length === 0 && page._errors.length === 0, page._errors.join(' | '));
      await page.context().close();
    }
  }

  // 触屏平板横放：默认竖向阅读，不进投屏
  page = await newPage(browser, { width: 1180, height: 820 }, { isMobile: true, hasTouch: true });
  await page.goto(URLS.zh, { waitUntil: 'load' });
  ok('平板横放默认是阅读模式（可手动切投屏）', await page.evaluate(() => !document.documentElement.classList.contains('present')));
  await page.context().close();

  // ---------- 关闭脚本也能读（三份文件各显示自己的语言） ----------
  for (const lang of ['zh', 'en', 'ms']) {
    page = await newPage(browser, { width: 390, height: 844 }, { javaScriptEnabled: false });
    await page.goto(URLS[lang], { waitUntil: 'load' });
    const nojs = await page.evaluate(() => ({
      visible: Array.from(document.querySelectorAll('.slide')).every((s) => s.getBoundingClientRect().height > 100),
      imgs: Array.from(document.images).filter((i) => i.getAttribute('src')).every((i) => i.naturalWidth > 0),
      sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
      dead: Array.from(document.querySelectorAll('.choice button, .topbar-actions button, .shot-zoom, #calcNights')).filter((el) => el.getClientRects().length).length,
      title: document.querySelector('#plans .slide-title').textContent, lang: document.documentElement.lang,
    }));
    const want = { zh: /三个方案/, en: /Three plans/, ms: /Tiga pelan/ }[lang];
    ok(`${NAMES[lang]} · 关闭脚本：所有页面和图片可读，显示 ${NAMES[lang]}，不留点不动的按钮`, nojs.visible && nojs.imgs && nojs.sw <= nojs.cw && nojs.dead === 0 && want.test(nojs.title), JSON.stringify(nojs));
    await page.context().close();
  }

  // ---------- 打印排版 ----------
  page = await newPage(browser, { width: 1920, height: 1080 });
  await page.goto(URLS.zh + '?print=1', { waitUntil: 'load' });
  const pr = await page.evaluate(() => Array.from(document.querySelectorAll('.slide')).map((s) => { const r = s.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; }));
  ok('打印排版：每页 1920×1080', pr.every((x) => x[0] === 1920 && x[1] === 1080), JSON.stringify(pr.slice(0, 3)));
  await page.context().close();

  await browser.close();
  const failed = results.filter((r) => !r.pass);
  results.forEach((r) => console.log((r.pass ? '  ✓ ' : '  ✗ ') + r.name + (r.pass || !r.detail ? '' : '  →  ' + r.detail)));
  console.log(failed.length ? `未通过 ${failed.length} 项（共 ${results.length} 项）` : `全部通过（${results.length} 项，${total} 页 × 3 种语言）`);
  process.exit(failed.length ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(1); });
