/* HogentX 客户汇报：投屏翻页、手机阅读、放大截图、打印、现场填写。无任何外部请求。 */
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
  var wideQuery = window.matchMedia('(min-width: 1000px) and (min-aspect-ratio: 5/4)');

  root.classList.add('js');

  /* ---------- 页码与目录 ---------- */
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
    var toggle = document.getElementById('modeToggle');
    if (toggle) toggle.textContent = isPresent() ? '阅读模式' : '投屏模式';
  }

  /* ---------- 翻页 ---------- */
  function show(i, silent) {
    current = Math.max(0, Math.min(total - 1, i));
    slides.forEach(function (s, k) { s.classList.toggle('is-current', k === current); });
    var count = document.getElementById('hudCount');
    if (count) count.textContent = (current + 1) + ' / ' + total;
    if (!silent) {
      try { history.replaceState(null, '', '#' + (current + 1)); } catch (e) { /* 本地文件个别环境不允许，忽略 */ }
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
    if (!isNaN(n) && n >= 1 && n <= total) return n - 1;
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
      if (e.key === 'Escape') e.target.blur();
      return;
    }
    var k = e.key;
    if (k === 'm' || k === 'M') { openToc(); e.preventDefault(); return; }
    if (k === 'f' || k === 'F') { toggleFullscreen(); e.preventDefault(); return; }
    if (!isPresent()) return;
    var onButton = e.target && e.target.tagName === 'BUTTON';
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
  function open(el) {
    lastFocus = document.activeElement;
    openOverlay = el;
    el.classList.add('is-open');
    var btn = el.querySelector('.overlay-close');
    if (btn) btn.focus();
  }
  function closeOverlay() {
    if (!openOverlay) return;
    openOverlay.classList.remove('is-open');
    openOverlay = null;
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  var toc = document.getElementById('toc');
  var tocList = document.getElementById('tocList');
  if (tocList) {
    slides.forEach(function (s, i) {
      var li = document.createElement('li');
      var b = document.createElement('button');
      b.type = 'button';
      var n = document.createElement('span'); n.className = 'n'; n.textContent = String(i + 1);
      var t = document.createElement('span'); t.textContent = titleOf(s).replace(/\s+/g, ' ').trim();
      b.appendChild(n); b.appendChild(t);
      b.addEventListener('click', function () { closeOverlay(); jump(i); });
      li.appendChild(b); tocList.appendChild(li);
    });
  }
  function openToc() { if (toc) open(toc); }

  var lightbox = document.getElementById('lightbox');
  var lbImg = document.getElementById('lightboxImg');
  var lbCap = document.getElementById('lightboxCap');
  deck.addEventListener('click', function (e) {
    var frame = e.target.closest ? e.target.closest('.shot-frame') : null;
    if (!frame || !lightbox) return;
    var img = frame.querySelector('img');
    var fig = frame.closest('.shot') || frame.parentNode;
    var cap = fig.querySelector('.shot-cap');
    lbImg.src = img.currentSrc || img.src;
    lbImg.alt = img.alt;
    lbCap.innerHTML = cap ? cap.innerHTML : '';
    open(lightbox);
  });
  Array.prototype.forEach.call(document.querySelectorAll('.overlay'), function (ov) {
    ov.addEventListener('click', function (e) { if (e.target === ov) closeOverlay(); });
  });
  Array.prototype.forEach.call(document.querySelectorAll('.overlay-close'), function (b) {
    b.addEventListener('click', closeOverlay);
  });

  /* ---------- 按钮 ---------- */
  function on(id, fn) { var el = document.getElementById(id); if (el) el.addEventListener('click', fn); }
  on('hudPrev', function () { go(-1); });
  on('hudNext', function () { go(1); });
  on('hudToc', openToc);
  on('hudFull', toggleFullscreen);
  on('hudRead', function () { forced = 'read'; applyMode(); });
  on('edgePrev', function () { go(-1); });
  on('edgeNext', function () { go(1); });
  on('tocBtn', openToc);
  on('modeToggle', function () { forced = isPresent() ? 'read' : 'present'; applyMode(); });

  /* ---------- 现场可点：三个问题 → 试点里先验证哪件事 ---------- */
  var picks = {};
  Array.prototype.forEach.call(document.querySelectorAll('.choice'), function (group) {
    var key = group.getAttribute('data-q');
    group.addEventListener('click', function (e) {
      var b = e.target.closest ? e.target.closest('button') : null;
      if (!b) return;
      var was = b.getAttribute('aria-pressed') === 'true';
      Array.prototype.forEach.call(group.querySelectorAll('button'), function (x) { x.setAttribute('aria-pressed', 'false'); });
      if (!was) b.setAttribute('aria-pressed', 'true');
      picks[key] = was ? null : b.getAttribute('data-v');
      Array.prototype.forEach.call(document.querySelectorAll('.job[data-q]'), function (job) {
        var keys = (job.getAttribute('data-q') || '').split(' ');
        var hit = keys.some(function (k2) { return picks[k2] === 'no'; });
        job.classList.toggle('is-picked', hit);
      });
    });
  });

  /* ---------- 现场可填：把月费换算成酒店自己的数 ---------- */
  var nightsEl = document.getElementById('calcNights');
  var netEl = document.getElementById('calcNet');
  function num(el) {
    if (!el) return NaN;
    var v = parseFloat(String(el.value).replace(/[, ]/g, ''));
    return isFinite(v) && v > 0 ? v : NaN;
  }
  function fmt(v, digits) {
    return v.toLocaleString('en-MY', { minimumFractionDigits: digits, maximumFractionDigits: digits });
  }
  function recalc() {
    var nights = num(nightsEl), net = num(netEl);
    Array.prototype.forEach.call(document.querySelectorAll('[data-fee]'), function (row) {
      var fee = parseFloat(row.getAttribute('data-fee'));
      var per = row.querySelector('[data-out="per"]');
      var eq = row.querySelector('[data-out="eq"]');
      if (per) per.textContent = isNaN(nights) ? '—' : 'RM ' + fmt(fee / nights, 2);
      if (eq) eq.textContent = isNaN(net) ? '—' : fmt(fee / net, 1) + ' 个房晚';
    });
  }
  if (nightsEl) nightsEl.addEventListener('input', recalc);
  if (netEl) netEl.addEventListener('input', recalc);
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
