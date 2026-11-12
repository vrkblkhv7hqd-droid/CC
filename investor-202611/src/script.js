/* 行内编辑的草稿只在同一版文件里生效：每次重新生成，草稿键随版本号变化，旧草稿不会盖住新稿 */
const DRAFT_KEY = "hogentx-investor-202611-__BUILD_ID__";

/* ===========================================
   幻灯片控制器：缩放舞台、翻页、备注、编辑
   =========================================== */
class SlidePresentation {
    constructor() {
        this.slides = Array.from(document.querySelectorAll('.slide'));
        this.stage = document.getElementById('deckStage');
        this.current = 0;
        this.setupStageScale();
        this.setupKeyboardNav();
        this.setupTouchNav();
        this.setupWheelNav();
        this.setupNotes();
        this.setupEditing();
        const fromHash = parseInt(location.hash.replace('#', ''), 10);
        this.go(isNaN(fromHash) ? 0 : fromHash - 1);
        window.addEventListener('hashchange', () => {
            const n = parseInt(location.hash.replace('#', ''), 10);
            if (!isNaN(n) && n - 1 !== this.current) this.go(n - 1);
        });
    }

    /* 舞台按窗口等比缩放，留黑边，不重排内容 */
    setupStageScale() {
        const scale = () => {
            const factor = Math.min(window.innerWidth / 1920, window.innerHeight / 1080);
            const x = (window.innerWidth - 1920 * factor) / 2;
            const y = (window.innerHeight - 1080 * factor) / 2;
            this.stage.style.transform = `translate(${x}px, ${y}px) scale(${factor})`;
        };
        scale();
        window.addEventListener('resize', scale);
    }

    setupKeyboardNav() {
        document.addEventListener('keydown', (e) => {
            if (e.target.getAttribute && e.target.getAttribute('contenteditable') === 'true') return;
            switch (e.key) {
                case 'ArrowRight': case 'ArrowDown': case ' ': case 'PageDown': e.preventDefault(); this.next(); break;
                case 'ArrowLeft': case 'ArrowUp': case 'PageUp': e.preventDefault(); this.prev(); break;
                case 'Home': e.preventDefault(); this.go(0); break;
                case 'End': e.preventDefault(); this.go(this.slides.length - 1); break;
                case 'n': case 'N': this.toggleNotes(); break;
                case 'f': case 'F': this.toggleFullscreen(); break;
            }
        });
    }

    setupTouchNav() {
        let x0 = null, y0 = null;
        document.addEventListener('touchstart', (e) => { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; }, { passive: true });
        document.addEventListener('touchend', (e) => {
            if (x0 === null) return;
            const dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0;
            if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy)) { dx < 0 ? this.next() : this.prev(); }
            x0 = y0 = null;
        }, { passive: true });
    }

    setupWheelNav() {
        let lock = false;
        document.addEventListener('wheel', (e) => {
            if (document.body.classList.contains('editing')) return;
            if (lock || Math.abs(e.deltaY) < 20) return;
            lock = true; setTimeout(() => lock = false, 900);
            e.deltaY > 0 ? this.next() : this.prev();
        }, { passive: true });
    }

    /* 备注面板：读取当前页 <aside class="notes"> */
    setupNotes() {
        this.panel = document.getElementById('notesPanel');
        this.notesBody = document.getElementById('notesBody');
    }
    toggleNotes() { this.panel.classList.toggle('show'); this.renderNotes(); }
    renderNotes() {
        const n = this.slides[this.current].querySelector('.notes');
        this.notesBody.textContent = n ? n.textContent.trim() : '（本页无备注）';
    }
    toggleFullscreen() {
        if (!document.fullscreenElement) document.documentElement.requestFullscreen && document.documentElement.requestFullscreen();
        else document.exitFullscreen && document.exitFullscreen();
    }

    /* 行内编辑：E 键或左上角热区，Ctrl+S 保存为新 HTML 文件，草稿自动存 localStorage */
    setupEditing() {
        const hotzone = document.getElementById('editHotzone');
        const toggle = document.getElementById('editToggle');
        let hideTimeout = null;
        this.isEditing = false;
        const show = () => { clearTimeout(hideTimeout); toggle.classList.add('show'); };
        const hide = () => { hideTimeout = setTimeout(() => { if (!this.isEditing) toggle.classList.remove('show'); }, 400); };
        hotzone.addEventListener('mouseenter', show);
        hotzone.addEventListener('mouseleave', hide);
        toggle.addEventListener('mouseenter', show);
        toggle.addEventListener('mouseleave', hide);
        hotzone.addEventListener('click', () => this.toggleEditMode());
        toggle.addEventListener('click', () => this.toggleEditMode());
        document.addEventListener('keydown', (e) => {
            if ((e.key === 'e' || e.key === 'E') && !(e.target.getAttribute && e.target.getAttribute('contenteditable') === 'true')) this.toggleEditMode();
            if ((e.ctrlKey || e.metaKey) && e.key === 's' && this.isEditing) { e.preventDefault(); this.saveFile(); }
        });
        try {
            const saved = localStorage.getItem(DRAFT_KEY);
            if (saved) { const stage = document.getElementById('deckStage'); stage.innerHTML = saved; this.slides = Array.from(document.querySelectorAll('.slide')); }
        } catch (err) { /* 浏览器禁用存储时忽略 */ }
    }
    toggleEditMode() {
        this.isEditing = !this.isEditing;
        document.body.classList.toggle('editing', this.isEditing);
        document.getElementById('editToggle').classList.toggle('active', this.isEditing);
        document.querySelectorAll('.slide h1, .slide h2, .slide h3, .slide p, .slide li, .slide td, .slide th, .slide .cap, .slide .big, .slide .src, .slide .eyebrow, .slide .notes, .slide .label, .slide .caption, .slide .role b, .slide .role span')
            .forEach(el => el.setAttribute('contenteditable', this.isEditing ? 'true' : 'false'));
        if (!this.isEditing) {
            try { localStorage.setItem(DRAFT_KEY, document.getElementById('deckStage').innerHTML); } catch (err) { /* ignore */ }
        }
    }
    saveFile() {
        document.querySelectorAll('[contenteditable]').forEach(el => el.removeAttribute('contenteditable'));
        const html = '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
        const blob = new Blob([html], { type: 'text/html' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob); a.download = 'HogentX-Investor-Update-202611-edited.html'; a.click();
        this.toggleEditMode(); this.toggleEditMode();
    }

    next() { this.go(this.current + 1); }
    prev() { this.go(this.current - 1); }
    go(i) {
        this.current = Math.max(0, Math.min(i, this.slides.length - 1));
        this.slides.forEach((s, k) => { s.classList.toggle('active', k === this.current); s.classList.toggle('visible', k === this.current); });
        document.getElementById('counter').textContent = `${this.current + 1} / ${this.slides.length}`;
        document.getElementById('progress').style.width = `${((this.current + 1) / this.slides.length) * 100}%`;
        if (history.replaceState) history.replaceState(null, '', `#${this.current + 1}`);
        if (this.panel && this.panel.classList.contains('show')) this.renderNotes();
    }
}
window.__deck = new SlidePresentation();
