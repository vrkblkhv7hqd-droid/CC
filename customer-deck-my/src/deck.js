/* HogentX 客户汇报：投屏翻页、手机阅读、三语切换、放大截图、打印、现场填写。无任何外部请求。 */
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
  function each(list, fn) { Array.prototype.forEach.call(list, fn); }

  root.classList.add('js');

  /* ---------- 三语：中文 / English / Bahasa Melayu ---------- */
  var LANGS = ['zh', 'en', 'ms'];
  var HTML_LANG = { zh: 'zh-CN', en: 'en', ms: 'ms' };
  var UI = {
    zh: { rail: ['可售房晚', '入住率', '平均成交房价', '房费收入', '渠道佣金', '净实收'], present: '投屏模式', read: '阅读模式' },
    en: { rail: ['Available room nights', 'Occupancy', 'ADR', 'Room revenue', 'Channel commission', 'Net received'], present: 'Present', read: 'Reading view' },
    ms: { rail: ['Malam bilik tersedia', 'Kadar penghunian', 'ADR', 'Hasil bilik', 'Komisen saluran', 'Terimaan bersih'], present: 'Mod pembentangan', read: 'Mod bacaan' }
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
    each(document.querySelectorAll('[data-lang-btn], .lang-switch button'), function (b) {
      b.setAttribute('aria-pressed', b.getAttribute('data-lang') === lang ? 'true' : 'false');
    });
  }
  function setLang(l) {
    if (!I18N || LANGS.indexOf(l) < 0 || l === lang) return;
    lang = l;
    applyStrings(l);
    markLang();
    buildRails();
    buildToc();
    updateModeLabel();
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

  /* ---------- 公式导航条：同一把尺子，标出这一页说的是哪个数 ---------- */
  var RAIL_KEYS = ['avail', 'occ', 'adr', 'rev', 'comm', 'net'];
  var RAIL_OPS = ['×', '×', '=', '−', '='];
  function buildRails() {
    var names = UI[lang].rail;
    each(document.querySelectorAll('.rail'), function (rail) {
      while (rail.firstChild) rail.removeChild(rail.firstChild);
      var on = (rail.getAttribute('data-on') || '').split(' ').filter(Boolean);
      /* 这一页不对应公式里的某个数：不放公式条，只显示栏目名 */
      rail.classList.toggle('rail--off', on.length === 0);
      if (on.length === 0) return;
      RAIL_KEYS.forEach(function (key, k) {
        var sp = document.createElement('span');
        sp.textContent = names[k];
        if (on.indexOf(key) >= 0) sp.className = 'on';
        rail.appendChild(sp);
        if (k < RAIL_OPS.length) { var op = document.createElement('i'); op.textContent = RAIL_OPS[k]; rail.appendChild(op); }
      });
      var kicker = rail.parentNode.querySelector('.kicker');
      if (kicker) {
        var parts = Array.prototype.filter.call(kicker.querySelectorAll('span'), function (x) { return !x.classList.contains('sep') && x.textContent.trim(); }).map(function (x) { return x.textContent.trim(); });
        /* 英文、马来文的栏目名较长：三段时只留首尾两段 */
        if (lang !== 'zh' && parts.length === 3) parts = [parts[0], parts[2]];
        var sec = document.createElement('b'); sec.className = 'rail-sec'; sec.textContent = parts.join(' · ');
        rail.appendChild(sec);
      }
      rail.setAttribute('aria-hidden', 'true');
    });
  }

  /* ---------- 模式 ---------- */
  function wantPresent() {
    if (printFlat) return true;
    if (forced === 'present') return true;
    if (forced === 'read') return false;
    return wideQuery.matches;
  }
  function isPresent() { return root.classList.contains('present'); }

  function fit() {
    if (!isPresent() || root.classList.contains('print-flat')) return;
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
      show(current, true);
    } else if (!present && isPresent()) {
      root.classList.remove('present', 'hud-on');
      slides.forEach(function (s) { s.classList.remove('is-current'); });
      var target = slides[current];
      if (target && target.scrollIntoView) target.scrollIntoView();
    }
    fit();
    updateModeLabel();
  }

  /* ---------- 翻页 ---------- */
  function show(i, silent) {
    current = Math.max(0, Math.min(total - 1, i));
    slides.forEach(function (s, k) { s.classList.toggle('is-current', k === current); });
    var count = document.getElementById('hudCount');
    if (count) count.textContent = (current + 1) + ' / ' + total;
    if (!silent) {
      try { history.replaceState(history.state, '', '#' + (current + 1)); } catch (e) { /* 本地文件个别环境不允许，忽略 */ }
    }
  }
  function go(delta) {
    if (isPresent()) { show(current + delta); return; }
    var i = Math.max(0, Math.min(total - 1, nearestSlideInView() + delta));
    slides[i].scrollIntoView({ behavior: 'smooth' });
  }
  function jump(i) {
    if (isPresent()) show(i);
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
    if (!isPresent()) return;
    var onButton = e.target && (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.getAttribute('role') === 'button');
    if (k === 'ArrowRight' || k === 'ArrowDown' || k === 'PageDown' || ((k === ' ' || k === 'Enter') && !onButton && !e.shiftKey)) { go(1); e.preventDefault(); }
    else if (k === 'ArrowLeft' || k === 'ArrowUp' || k === 'PageUp' || (k === ' ' && !onButton && e.shiftKey) || k === 'Backspace') { go(-1); e.preventDefault(); }
    else if (k === 'Home') { show(0); e.preventDefault(); }
    else if (k === 'End') { show(total - 1); e.preventDefault(); }
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
  document.addEventListener('mousemove', pokeHud);
  document.addEventListener('touchstart', pokeHud, { passive: true });

  function toggleFullscreen() {
    var el = document.documentElement;
    try {
      if (!document.fullscreenElement) { if (el.requestFullscreen) el.requestFullscreen(); }
      else if (document.exitFullscreen) document.exitFullscreen();
    } catch (e) { /* 忽略 */ }
  }

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

  /* ---------- 现场可点：三个问题 → 后面先验证哪件事 ---------- */
  var picks = {};
  each(document.querySelectorAll('.choice'), function (group) {
    var key = group.getAttribute('data-q');
    group.addEventListener('click', function (e) {
      var b = e.target.closest ? e.target.closest('button') : null;
      if (!b) return;
      var was = b.getAttribute('aria-pressed') === 'true';
      each(group.querySelectorAll('button'), function (x) { x.setAttribute('aria-pressed', 'false'); });
      if (!was) b.setAttribute('aria-pressed', 'true');
      picks[key] = was ? null : b.getAttribute('data-v');
      /* 鼠标点完把焦点放开，接着按空格或翻页笔可以直接翻页 */
      if (e.detail > 0) b.blur();
      each(document.querySelectorAll('.job[data-q]'), function (job) {
        var keys = (job.getAttribute('data-q') || '').split(' ');
        var hit = keys.some(function (k2) { return picks[k2] === 'no' || picks[k2] === 'exp'; });
        job.classList.toggle('is-picked', hit);
      });
    });
  });

  /* 试点页：点一下事项卡片，填进“验证哪件事”；渠道核对表里填过的 OTA 带到试点单 */
  var p3 = document.getElementById('p3'), p2 = document.getElementById('p2');
  each(document.querySelectorAll('#pilot .job[data-fill]'), function (job) {
    job.setAttribute('role', 'button');
    job.setAttribute('tabindex', '0');
    function pick() {
      each(document.querySelectorAll('#pilot .job'), function (j) { j.classList.remove('is-chosen'); });
      job.classList.add('is-chosen');
      if (p3) p3.value = job.getAttribute('data-fill');
    }
    job.addEventListener('click', pick);
    job.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') { pick(); e.preventDefault(); e.stopPropagation(); }
    });
  });
  var otaInputs = document.querySelectorAll('#multi-ota input.fill'), p2Auto = '';
  each(otaInputs, function (inp) {
    inp.addEventListener('input', function () {
      var names = Array.prototype.map.call(otaInputs, function (x) { return x.value.trim(); }).filter(Boolean).join(lang === 'zh' ? '、' : ', ');
      if (p2 && (p2.value === '' || p2.value === p2Auto)) { p2.value = names; p2Auto = names; }
    });
  });

  /* ---------- 现场可填：把月费摊到每个卖出的房晚 ---------- */
  var nightsEl = document.getElementById('calcNights');
  function num(el) {
    if (!el) return NaN;
    var v = parseFloat(String(el.value).replace(/[^0-9.]/g, ''));
    return isFinite(v) && v > 0 ? v : NaN;
  }
  function fmt(v, digits) {
    return v.toLocaleString('en-MY', { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }
  function recalc() {
    var nights = num(nightsEl);
    each(document.querySelectorAll('[data-fee]'), function (row) {
      var fee = parseFloat(row.getAttribute('data-fee'));
      var per = row.querySelector('[data-out="per"]');
      if (per) per.textContent = isNaN(nights) ? '—' : 'RM ' + fmt(fee / nights, 2);
    });
  }
  if (nightsEl) nightsEl.addEventListener('input', recalc);
  recalc();

  /* ---------- 打印 / 导出 PDF ---------- */
  var beforePrintWasPresent = false;
  function enterPrint() {
    beforePrintWasPresent = isPresent();
    root.classList.add('present', 'print-flat');
    root.classList.remove('hud-on');
    root.style.setProperty('--scale', '1');
  }
  function leavePrint() {
    if (printFlat) return;
    root.classList.remove('print-flat');
    if (!beforePrintWasPresent) root.classList.remove('present');
    applyMode();
    if (isPresent()) show(current, true);
  }
  window.addEventListener('beforeprint', enterPrint);
  window.addEventListener('afterprint', leavePrint);

  /* ---------- 启动 ---------- */
  var wantLang = params.get('lang');
  if (I18N && wantLang && LANGS.indexOf(wantLang) >= 0 && wantLang !== lang) { lang = wantLang; applyStrings(lang); }
  markLang();
  buildRails();
  buildToc();
  var start = fromHash();
  if (start !== null) current = start;
  if (printFlat) {
    enterPrint();
  } else {
    if (wantPresent()) { root.classList.add('present'); show(current, true); }
    else if (start !== null) { slides[current].scrollIntoView(); }
    applyMode();
  }
  window.addEventListener('resize', function () { if (!root.classList.contains('print-flat')) applyMode(); });
  if (wideQuery.addEventListener) wideQuery.addEventListener('change', function () { if (!root.classList.contains('print-flat')) applyMode(); });
  window.addEventListener('hashchange', function () {
    var i = fromHash();
    if (i !== null) jump(i);
  });
})();
