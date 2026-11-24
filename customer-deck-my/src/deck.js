/* HogentX 客户汇报：投屏翻页（含分步出现）、手机阅读、三语切换、按您的数字算账、放大截图、打印。无任何外部请求。 */
(function () {
  'use strict';
  var root = document.documentElement;
  var deck = document.getElementById('deck');
  if (!deck) return;
  var slides = Array.prototype.slice.call(deck.querySelectorAll('.slide'));
  var total = slides.length;
  var current = 0;
  var STAGE_W = 1920, STAGE_H = 1080;
  var params = new URLSearchParams(location.search);
  var forced = params.get('mode'); // 'present' | 'read' | null
  var printFlat = params.get('print') === '1';
  /* 触屏设备（手机、平板）默认竖向阅读；有鼠标的宽屏默认投屏 */
  var wideQuery = window.matchMedia('(min-width: 1000px) and (min-aspect-ratio: 5/4) and (hover: hover) and (pointer: fine)');
  var calmMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  root.classList.add('js');

  /* ---------- 三语：中文 / English / Bahasa Melayu ---------- */
  var LANGS = ['zh', 'en', 'ms'];
  var HTML_LANG = { zh: 'zh-CN', en: 'en', ms: 'ms' };
  var UI = {
    zh: { present: '投屏模式', read: '阅读模式', timer: '已用时间 / 讲完这一页的计划时间。点击归零。' },
    en: { present: 'Present', read: 'Reading view', timer: 'Time used / planned time by the end of this slide. Click to reset.' },
    ms: { present: 'Mod pembentangan', read: 'Mod bacaan', timer: 'Masa digunakan / masa dirancang pada akhir slaid ini. Klik untuk set semula.' }
  };
  var I18N = null;
  try {
    var blob = document.getElementById('i18n');
    if (blob) I18N = JSON.parse(blob.textContent);
  } catch (e) { I18N = null; }
  var lang = root.getAttribute('data-lang') || 'zh';
  if (LANGS.indexOf(lang) < 0) lang = 'zh';
  if (I18N) root.classList.add('i18n');

  function applyStrings(l) {
    var table = I18N[l];
    each(document.querySelectorAll('[data-i]'), function (el) {
      var v = table[+el.getAttribute('data-i')];
      if (typeof v === 'string') el.innerHTML = v;
    });
    each(document.querySelectorAll('[data-ia]'), function (el) {
      el.getAttribute('data-ia').split(';').forEach(function (pair) {
        var kv = pair.split('=');
        var v = table[+kv[1]];
        if (typeof v === 'string') el.setAttribute(kv[0], v);
      });
    });
  }
  function markLang() {
    root.lang = HTML_LANG[lang];
    root.setAttribute('data-lang', lang);
    each(document.querySelectorAll('.lang-switch button'), function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-lang') === lang ? 'true' : 'false');
    });
  }
  function setLang(l) {
    if (!I18N || LANGS.indexOf(l) < 0 || l === lang) return;
    lang = l;
    applyStrings(l);
    markLang();
    buildToc();
    updateModeLabel();
    recalc();
    try {
      var u = new URL(location.href);
      u.searchParams.set('lang', l);
      history.replaceState(history.state, '', u.toString());
    } catch (e) { /* 本地文件个别环境不允许，忽略 */ }
  }
  function cycleLang() { setLang(LANGS[(LANGS.indexOf(lang) + 1) % LANGS.length]); }

  /* ---------- 页码 ---------- */
  slides.forEach(function (s, i) {
    var page = s.querySelector('.foot-page');
    if (page) page.textContent = (i + 1) + ' / ' + total;
    if (!s.id) s.id = 's' + (i + 1);
  });
  function titleOf(s) {
    return s.getAttribute('data-title') || (s.querySelector('.slide-title, .cover-title') || {}).textContent || '';
  }

  /* ---------- 模式 ---------- */
  function wantPresent() {
    if (printFlat) return true;
    if (forced === 'present') return true;
    if (forced === 'read') return false;
    return wideQuery.matches;
  }
  function isPresent() { return root.classList.contains('present'); }
  function isPrint() { return root.classList.contains('print-flat'); }

  function fit() {
    if (!isPresent() || isPrint()) return;
    var s = Math.min(window.innerWidth / STAGE_W, window.innerHeight / STAGE_H);
    root.style.setProperty('--scale', String(s));
  }
  function nearestSlideInView() {
    var best = 0, bestDist = Infinity;
    slides.forEach(function (s, i) {
      var d = Math.abs(s.getBoundingClientRect().top - 56);
      if (d < bestDist) { bestDist = d; best = i; }
    });
    return best;
  }
  function updateModeLabel() {
    var toggle = document.getElementById('modeToggle');
    if (toggle) toggle.textContent = isPresent() ? UI[lang].read : UI[lang].present;
  }
  function applyMode() {
    var present = wantPresent();
    if (present && !isPresent()) {
      current = nearestSlideInView();
      root.classList.add('present');
      show(current, { silent: true, steps: 'all' });
      keepAwake();
    } else if (!present && isPresent()) {
      root.classList.remove('present', 'hud-on', 'is-blackout', 'cursor-idle');
      letSleep();
      slides.forEach(function (s) { s.classList.remove('is-current'); });
      var target = slides[current];
      if (target && target.scrollIntoView) target.scrollIntoView();
    }
    fit();
    updateModeLabel();
  }

  /* ---------- 分步出现：同一页里一条一条讲 ---------- */
  var stepNow = 0;
  function stepsOf(s) {
    var seen = {}, list = [];
    each(s.querySelectorAll('[data-step]'), function (el) {
      var k = el.getAttribute('data-step');
      if (!seen[k]) { seen[k] = true; list.push(+k); }
    });
    return list.sort(function (a, b) { return a - b; });
  }
  function setSteps(s, n, animate) {
    var order = stepsOf(s);
    each(s.querySelectorAll('[data-step]'), function (el) {
      var on = order.indexOf(+el.getAttribute('data-step')) < n;
      var was = el.classList.contains('is-on');
      el.classList.toggle('is-on', on);
      if (animate && on && !was) countUp(el);
    });
    stepNow = Math.max(0, Math.min(order.length, n));
  }

  /* ---------- 数字跳动：进入页面时从 0 数到位（打印、阅读模式、减少动态时不做） ---------- */
  function fmtInt(v) { return Math.round(v).toLocaleString('en-MY'); }
  function countUp(scope) {
    if (!isPresent() || isPrint() || calmMotion.matches) return;
    each(scope.querySelectorAll('[data-count]'), function (el) {
      if (el.closest('[data-step]') && !el.closest('[data-step]').classList.contains('is-on')) return;
      var raw = el.getAttribute('data-count');
      var end = parseFloat(raw);
      if (!isFinite(end)) return;
      var finalText = el.getAttribute('data-final') || el.textContent;
      el.setAttribute('data-final', finalText);
      var decimals = (raw.split('.')[1] || '').length;
      var t0 = null, dur = 700;
      function mid(v) {
        var a = Math.abs(v);
        return (v < 0 ? '−' : '') + (decimals ? a.toFixed(decimals) : fmtInt(a));
      }
      function frame(t) {
        if (t0 === null) t0 = t;
        var p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3);
        el.textContent = p < 1 ? mid(end * e) : finalText;
        if (p < 1) requestAnimationFrame(frame);
      }
      requestAnimationFrame(frame);
    });
  }

  /* ---------- 翻页 ---------- */
  function show(i, opts) {
    opts = opts || {};
    var prev = current;
    current = Math.max(0, Math.min(total - 1, i));
    slides.forEach(function (s, k) { s.classList.toggle('is-current', k === current); });
    var s = slides[current];
    setSteps(s, opts.steps === 'none' ? 0 : stepsOf(s).length);
    if (prev !== current || opts.fresh) countUp(s);
    var count = document.getElementById('hudCount');
    if (count) count.textContent = (current + 1) + ' / ' + total;
    var bar = document.getElementById('progressBar');
    if (bar) bar.style.width = (((current + 1) / total) * 100).toFixed(2) + '%';
    if (root.classList.contains('timer-on')) paintTimer();
    if (!opts.silent) {
      try { history.replaceState(history.state, '', '#' + (current + 1)); } catch (e) { /* 本地文件个别环境不允许，忽略 */ }
    }
  }
  function go(delta) {
    if (!isPresent()) {
      var i = Math.max(0, Math.min(total - 1, nearestSlideInView() + delta));
      slides[i].scrollIntoView({ behavior: 'smooth' });
      return;
    }
    var s = slides[current], n = stepsOf(s).length;
    if (delta > 0) {
      if (stepNow < n) setSteps(s, stepNow + 1, true);
      else if (current < total - 1) show(current + 1, { steps: 'none' });
    } else {
      if (stepNow > 0) setSteps(s, stepNow - 1);
      else if (current > 0) show(current - 1, { steps: 'all' });
    }
  }
  function jump(i) {
    if (isPresent()) show(i, { steps: 'all' });
    else { current = i; slides[i].scrollIntoView(); }
  }
  function fromHash() {
    var h = (location.hash || '').replace('#', '');
    if (!h) return null;
    var n = parseInt(h, 10);
    if (!isNaN(n) && String(n) === h && n >= 1 && n <= total) return n - 1;
    var el = document.getElementById(h);
    var idx = el ? slides.indexOf(el.closest ? el.closest('.slide') : el) : -1;
    return idx >= 0 ? idx : null;
  }

  function isTyping(t) {
    if (!t) return false;
    var tag = (t.tagName || '').toLowerCase();
    return tag === 'input' || tag === 'textarea' || tag === 'select' || t.isContentEditable;
  }

  document.addEventListener('keydown', function (e) {
    if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.altKey) return;
    if (openOverlay) {
      if (e.key === 'Escape') { closeOverlay(); e.preventDefault(); }
      return;
    }
    if (isTyping(e.target)) {
      /* 正在用输入法时不打断；Enter / Esc 结束填写；翻页笔（PageDown / PageUp）照常翻页 */
      if (e.isComposing || e.keyCode === 229) return;
      if (e.key === 'Escape' || e.key === 'Enter') { e.target.blur(); e.preventDefault(); return; }
      if (e.key !== 'PageDown' && e.key !== 'PageUp') return;
      e.target.blur();
    }
    var k = e.key;
    if (k === 'm' || k === 'M') { openToc(); e.preventDefault(); return; }
    if (k === 'f' || k === 'F') { toggleFullscreen(); e.preventDefault(); return; }
    if (k === 'l' || k === 'L') { cycleLang(); e.preventDefault(); return; }
    if (k === 't' || k === 'T') { toggleTimer(); e.preventDefault(); return; }
    if (!isPresent()) return;
    /* 黑屏：想让大家看人、不看屏幕时按 B 或句号；再按任意键恢复 */
    if (root.classList.contains('is-blackout')) { root.classList.remove('is-blackout'); e.preventDefault(); return; }
    if (k === 'b' || k === 'B' || k === '.') { root.classList.add('is-blackout'); e.preventDefault(); return; }
    var onButton = e.target && (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.getAttribute('role') === 'button');
    if (k === 'ArrowRight' || k === 'ArrowDown' || k === 'PageDown' || ((k === ' ' || k === 'Enter') && !onButton && !e.shiftKey)) { go(1); e.preventDefault(); }
    else if (k === 'ArrowLeft' || k === 'ArrowUp' || k === 'PageUp' || (k === ' ' && !onButton && e.shiftKey) || k === 'Backspace') { go(-1); e.preventDefault(); }
    else if (k === 'Home') { show(0, { steps: 'all' }); e.preventDefault(); }
    else if (k === 'End') { show(total - 1, { steps: 'all' }); e.preventDefault(); }
  });

  /* 触屏左右滑动（仅投屏模式） */
  var touchX = null, touchY = null;
  deck.addEventListener('touchstart', function (e) {
    if (!isPresent() || e.touches.length !== 1) return;
    touchX = e.touches[0].clientX; touchY = e.touches[0].clientY;
  }, { passive: true });
  deck.addEventListener('touchend', function (e) {
    if (!isPresent() || touchX === null) return;
    var dx = e.changedTouches[0].clientX - touchX, dy = e.changedTouches[0].clientY - touchY;
    touchX = null;
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5 && !isTyping(e.target)) go(dx < 0 ? 1 : -1);
  }, { passive: true });

  /* 控制条：鼠标动一下才出现，免得挡住画面 */
  var hudTimer = null;
  function pokeHud() {
    if (!isPresent()) return;
    root.classList.add('hud-on');
    clearTimeout(hudTimer);
    hudTimer = setTimeout(function () { root.classList.remove('hud-on'); }, 2600);
  }
  var cursorTimer = null;
  function pokeCursor() {
    root.classList.remove('cursor-idle');
    clearTimeout(cursorTimer);
    if (isPresent()) cursorTimer = setTimeout(function () { root.classList.add('cursor-idle'); }, 3000);
  }
  document.addEventListener('mousemove', function () { pokeHud(); pokeCursor(); });
  document.addEventListener('touchstart', pokeHud, { passive: true });
  document.addEventListener('click', function () { if (root.classList.contains('is-blackout')) root.classList.remove('is-blackout'); });

  /* 投屏时请求屏幕常亮（浏览器不支持或不允许时忽略） */
  var wakeLock = null;
  function keepAwake() {
    if (!isPresent() || isPrint() || wakeLock || !navigator.wakeLock || document.visibilityState !== 'visible') return;
    try {
      navigator.wakeLock.request('screen').then(function (lock) {
        wakeLock = lock;
        lock.addEventListener('release', function () { wakeLock = null; });
      }).catch(function () { /* 忽略 */ });
    } catch (e) { /* 忽略 */ }
  }
  function letSleep() { if (wakeLock) { try { wakeLock.release(); } catch (e) { /* 忽略 */ } wakeLock = null; } }
  document.addEventListener('visibilitychange', keepAwake);

  function toggleFullscreen() {
    var el = document.documentElement;
    try {
      if (!document.fullscreenElement) { if (el.requestFullscreen) el.requestFullscreen(); }
      else if (document.exitFullscreen) document.exitFullscreen();
    } catch (e) { /* 忽略 */ }
  }

  /* ---------- 计时：按 T 显示讲了多久（默认不显示，免得客户看到） ---------- */
  var timerEl = document.getElementById('timer'), timerStart = null, timerTick = null;
  function clock(sec) {
    var m = Math.floor(sec / 60), s = sec % 60;
    return (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
  }
  /* 每页的计划用时写在 data-sec 上：讲到这一页结束时应该用了多久 */
  function plannedThrough(i) {
    var sum = 0;
    for (var k = 0; k <= i && k < total; k++) sum += parseInt(slides[k].getAttribute('data-sec'), 10) || 0;
    return sum;
  }
  function paintTimer() {
    if (!timerEl || timerStart === null) return;
    var sec = Math.floor((Date.now() - timerStart) / 1000);
    var plan = plannedThrough(current);
    timerEl.textContent = clock(sec) + (plan ? ' / ' + clock(plan) : '');
    timerEl.classList.toggle('is-late', plan > 0 && sec > plan + 30);
    timerEl.title = UI[lang].timer;
  }
  function toggleTimer() {
    if (!timerEl) return;
    var on = !root.classList.contains('timer-on');
    root.classList.toggle('timer-on', on);
    if (on) {
      if (timerStart === null) timerStart = Date.now();
      paintTimer();
      timerTick = setInterval(paintTimer, 1000);
    } else { clearInterval(timerTick); }
  }
  if (timerEl) timerEl.addEventListener('click', function () { timerStart = Date.now(); paintTimer(); });

  /* ---------- 浮层：目录与放大图 ---------- */
  var openOverlay = null, lastFocus = null;
  var pushed = false, pendingJump = null;
  function setRestore(v) { try { if ('scrollRestoration' in history) history.scrollRestoration = v; } catch (e) { /* 忽略 */ } }
  function open(el) {
    lastFocus = document.activeElement;
    openOverlay = el;
    el.classList.add('is-open');
    root.classList.add('has-overlay');
    var btn = el.querySelector('.overlay-close');
    if (btn) btn.focus();
    /* 阅读模式下，手机的“返回”键只关掉浮层，不离开页面 */
    if (!isPresent()) {
      try { setRestore('manual'); history.pushState({ overlay: 1 }, ''); pushed = true; } catch (e) { pushed = false; setRestore('auto'); }
    }
  }
  function hideOverlay() {
    if (!openOverlay) return;
    openOverlay.classList.remove('is-open');
    openOverlay = null;
    root.classList.remove('has-overlay');
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function closeOverlay() {
    if (!openOverlay) return;
    if (pushed) { try { history.back(); return; } catch (e) { pushed = false; } }
    hideOverlay();
  }
  window.addEventListener('popstate', function () {
    if (!pushed) return;
    pushed = false;
    hideOverlay();
    setRestore('auto');
    if (pendingJump !== null) { var to = pendingJump; pendingJump = null; setTimeout(function () { jump(to); }, 0); }
  });

  var toc = document.getElementById('toc');
  var tocList = document.getElementById('tocList');
  function buildToc() {
    if (!tocList) return;
    while (tocList.firstChild) tocList.removeChild(tocList.firstChild);
    slides.forEach(function (s, i) {
      var li = document.createElement('li');
      var b = document.createElement('button');
      b.type = 'button';
      var n = document.createElement('span'); n.className = 'n'; n.textContent = String(i + 1);
      var t = document.createElement('span'); t.textContent = titleOf(s).replace(/\s+/g, ' ').trim();
      b.appendChild(n); b.appendChild(t);
      b.addEventListener('click', function () {
        if (pushed) { pendingJump = i; closeOverlay(); } else { closeOverlay(); jump(i); }
      });
      li.appendChild(b); tocList.appendChild(li);
    });
  }
  function openToc() { if (toc) open(toc); }

  var lightbox = document.getElementById('lightbox');
  var lbImg = document.getElementById('lightboxImg');
  var lbCap = document.getElementById('lightboxCap');
  var lbScroll = document.getElementById('lightboxScroll');
  deck.addEventListener('click', function (e) {
    var frame = e.target.closest ? e.target.closest('.shot-frame') : null;
    if (!frame || !lightbox) return;
    var img = frame.querySelector('img');
    var fig = frame.closest('.shot') || frame.parentNode;
    var cap = fig.querySelector('.shot-cap');
    lbImg.src = img.currentSrc || img.src;
    lbImg.alt = img.alt;
    lbCap.innerHTML = cap ? cap.innerHTML : '';
    lightbox.classList.remove('is-zoomed');
    open(lightbox);
    if (lbScroll) { lbScroll.scrollTop = 0; lbScroll.scrollLeft = 0; }
  });
  if (lbImg) lbImg.addEventListener('click', function () {
    lightbox.classList.toggle('is-zoomed');
    if (lbScroll) { lbScroll.scrollTop = 0; lbScroll.scrollLeft = 0; }
  });
  each(document.querySelectorAll('.overlay'), function (ov) {
    ov.addEventListener('click', function (e) { if (e.target === ov) closeOverlay(); });
  });
  each(document.querySelectorAll('.overlay-close'), function (b) {
    b.addEventListener('click', closeOverlay);
  });

  /* ---------- 按钮 ---------- */
  function on(id, fn) { var el = document.getElementById(id); if (el) el.addEventListener('click', fn); }
  on('hudPrev', function () { go(-1); });
  on('hudNext', function () { go(1); });
  on('hudToc', openToc);
  on('hudFull', toggleFullscreen);
  on('hudLang', cycleLang);
  on('hudPrint', function () { window.print(); });
  on('hudRead', function () { forced = 'read'; applyMode(); });
  on('edgePrev', function () { go(-1); });
  on('edgeNext', function () { go(1); });
  on('tocBtn', openToc);
  on('modeToggle', function () { forced = isPresent() ? 'read' : 'present'; applyMode(); });
  each(document.querySelectorAll('.lang-switch button'), function (b) {
    b.addEventListener('click', function () { setLang(b.getAttribute('data-lang')); });
  });

  /* ---------- 按您的数字算一笔：三个数填一次，后面的方案页跟着算 ---------- */
  var inRooms = document.getElementById('cRooms'), inAdr = document.getElementById('cAdr'), inOcc = document.getElementById('cOcc');
  function num(el) {
    if (!el) return NaN;
    var v = parseFloat(String(el.value).replace(/[^0-9.]/g, ''));
    return isFinite(v) && v > 0 ? v : NaN;
  }
  function money(v) { return 'RM ' + Math.round(v).toLocaleString('en-MY'); }

  function put(key, text) {
    each(document.querySelectorAll('[data-out="' + key + '"]'), function (el) { el.textContent = text; });
  }
  function recalc() {
    var rooms = num(inRooms), adr = num(inAdr), occ = num(inOcc);
    if (occ > 100) occ = 100;
    var ok = !(isNaN(rooms) || isNaN(adr) || isNaN(occ));
    var nights = ok ? rooms * 365 * occ / 100 : NaN;      /* 一年卖出的房晚 */
    var rev = ok ? nights * adr : NaN;                    /* 一年房费收入 */
    var emptyPerNight = ok ? rooms * (1 - occ / 100) : NaN; /* 平均每晚空着的房 */
    put('nights', ok ? fmtInt(nights) : '—');
    put('rev', ok ? money(rev) : '—');
    put('empty', ok ? fmtInt(emptyPerNight) : '—');
    put('emptyMonth', ok ? fmtInt(emptyPerNight * 365 / 12) : '—'); /* 每月空着的房晚 */
    put('occ1', ok ? money(rooms * 365 * 0.01 * adr) : '—'); /* 入住率每多 1 个百分点 */
    put('adr5', ok ? money(nights * 5) : '—');            /* 每个房晚多卖 RM 5 */
    each(document.querySelectorAll('[data-fee]'), function (row) {
      var fee = parseFloat(row.getAttribute('data-fee'));
      var eq = row.querySelector('[data-eq]');
      if (eq) eq.textContent = ok ? fmtInt(Math.ceil(fee / adr)) : '—'; /* 月费折成几个房晚的房费 */
    });
    root.classList.toggle('calc-ready', ok);
  }
  [inRooms, inAdr, inOcc].forEach(function (el) { if (el) el.addEventListener('input', recalc); });
  recalc();

  /* ---------- 打印 / 导出 PDF ---------- */
  var beforePrintWasPresent = false;
  function enterPrint() {
    beforePrintWasPresent = isPresent();
    root.classList.add('present', 'print-flat');
    root.classList.remove('hud-on');
    root.style.setProperty('--scale', '1');
    slides.forEach(function (s) { each(s.querySelectorAll('[data-step]'), function (el) { el.classList.add('is-on'); }); });
  }
  function leavePrint() {
    if (printFlat) return;
    root.classList.remove('print-flat');
    if (!beforePrintWasPresent) root.classList.remove('present');
    applyMode();
    if (isPresent()) show(current, { silent: true, steps: 'all' });
  }
  window.addEventListener('beforeprint', enterPrint);
  window.addEventListener('afterprint', leavePrint);

  /* ---------- 启动 ---------- */
  var wantLang = params.get('lang');
  if (I18N && wantLang && LANGS.indexOf(wantLang) >= 0 && wantLang !== lang) { lang = wantLang; applyStrings(lang); }
  markLang();
  buildToc();
  var start = fromHash();
  if (start !== null) current = start;
  if (printFlat) {
    enterPrint();
  } else {
    if (wantPresent()) { root.classList.add('present'); show(current, { silent: true, steps: start === null ? 'none' : 'all', fresh: true }); keepAwake(); }
    else if (start !== null) { slides[current].scrollIntoView(); }
    applyMode();
  }
  window.addEventListener('resize', function () { if (!isPrint()) applyMode(); });
  if (wideQuery.addEventListener) wideQuery.addEventListener('change', function () { if (!isPrint()) applyMode(); });
  window.addEventListener('hashchange', function () {
    var i = fromHash();
    if (i !== null) jump(i);
  });
})();
