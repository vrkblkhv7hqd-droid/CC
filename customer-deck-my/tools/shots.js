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
  await page.addStyleTag({ content: '.hud{display:none !important}' });
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
        // 带边框或底色的容器也不能压到页脚，或超出右边界
        let boxBottom = 0, boxWho = '';
        s.querySelectorAll('.card, .note, .term, .status-col, .sheet, .shot-frame, .shot-label, .table-wrap, .flow > li, .money').forEach((el) => {
          const r = el.getBoundingClientRect();
          if (r.width === 0 || r.height === 0) return;
          const bb = (r.bottom - sr.top) / scale;
          if (bb > boxBottom) { boxBottom = bb; boxWho = el.className; }
        });
        // 容器内文字是否溢出容器
        const clipped = [];
        s.querySelectorAll('.card, .note, .term, .status-col, .sheet').forEach((el) => {
          if (el.scrollHeight - el.clientHeight > 2 || el.scrollWidth - el.clientWidth > 2) clipped.push(el.className + ':' + (el.scrollHeight - el.clientHeight));
          const er = el.getBoundingClientRect();
          el.querySelectorAll('*').forEach((c) => {
            const cr = c.getBoundingClientRect();
            if (cr.width && cr.height && (cr.bottom - er.bottom > 2 * scale)) { const t = (c.textContent || '').trim().slice(0, 10); if (t && clipped.length < 6) clipped.push('out-of-' + el.className.split(' ')[0] + ':' + t); }
          });
        });
        if (boxBottom > maxBottom) { maxBottom = boxBottom; lowest = 'box ' + boxWho; }
        // 任何被裁掉、需要滚动才能看到的内容都算问题
        s.querySelectorAll('*').forEach((el) => {
          const cs2 = getComputedStyle(el);
          if (cs2.overflowY !== 'visible' || cs2.overflowX !== 'visible') {
            if (el.scrollHeight - el.clientHeight > 2 && clipped.length < 8) clipped.push('scroll-clipped ' + (el.className || el.tagName) + ' by ' + (el.scrollHeight - el.clientHeight) + 'px');
            if (el.scrollWidth - el.clientWidth > 2 && el !== s && clipped.length < 8) clipped.push('scroll-clipped-x ' + (el.className || el.tagName) + ' by ' + (el.scrollWidth - el.clientWidth) + 'px');
          }
        });
        // 互不包含的块之间不能重叠
        const boxes = Array.from(s.querySelectorAll('.card, .note, .term, .status-col, .sheet, .shot, .slide-head, .table-wrap, .flow > li, .money, .slide-lead, .slide-title')).filter((el) => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; });
        for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
          const A = boxes[i], B = boxes[j];
          if (A.contains(B) || B.contains(A)) continue;
          const ra = A.getBoundingClientRect(), rb = B.getBoundingClientRect();
          const ox = Math.min(ra.right, rb.right) - Math.max(ra.left, rb.left);
          const oy = Math.min(ra.bottom, rb.bottom) - Math.max(ra.top, rb.top);
          if (ox > 3 * scale && oy > 3 * scale && clipped.length < 8) clipped.push('overlap ' + A.className.split(' ').slice(0, 2).join('.') + ' x ' + B.className.split(' ').slice(0, 2).join('.') + ' by ' + Math.round(oy / scale) + 'px');
        }
        return { id: s.id, clipped: Array.from(new Set(clipped)).slice(0, 6), contentBottom: Math.round(maxBottom), footTop: Math.round(footTop), slack: Math.round(footTop - maxBottom), maxRight: Math.round(maxRight), minFont, small: small.slice(0, 6), lowest };
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
