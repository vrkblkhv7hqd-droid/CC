"""Build the HyperFrames opening film from script.json + the narration timings.

Writes index.html, compositions/*.html and compositions/captions.html. Every timed element is
written statically into the HTML; this script only resolves the times from the voice files so
that visuals land on the words that say them.

Usage: python3 tools/build.py            (re-subsets the fonts first when the Noto CJK OTFs are
                                           found: $NOTO_CJK_DIR or the default directory below)
"""
import json, re, html, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))

S = json.load(open('script.json'))
T = {t['id']: t for t in json.load(open('assets/voice/timings.json'))}

LEAD = 1.6          # seconds before the first word
GAP = S['gap_s']    # pause between narration files
TAIL = 4.6          # hold after the last word
VIS_LEAD = 0.45     # a scene cuts in this long before its narration starts
BRAND = S.get('brand_token', 'Hojent')   # spelling of the brand in the English VO (word anchor)

# ---------------------------------------------------------------- fonts
FONT_SRC = os.environ.get('NOTO_CJK_DIR', '/tmp/claude-0/-home-user-CC/b11a4d30-e576-56e2-a445-b9838c59c1cd/scratchpad/cjk')
if os.path.isdir(FONT_SRC):
    import importlib
    importlib.import_module('subset-fonts').subset(FONT_SRC)
else:
    print('fonts: source OTFs not found, keeping the existing subset (run tools/subset-fonts.py after wording changes)')

# ---------------------------------------------------------------- schedule
segs = S['segments']
BY = {s_['id']: s_ for s_ in segs}
t = LEAD
for seg in segs:
    seg['vo_start'] = round(t, 3)
    seg['vo_dur'] = T[seg['id']]['duration']
    seg['vo_end'] = round(t + seg['vo_dur'], 3)
    t += seg['vo_dur'] + GAP + seg.get('hold_s', 0)
VO_END = segs[-1]['vo_end']
TOTAL = round(VO_END + TAIL, 1)

for i, seg in enumerate(segs):
    seg['scene_start'] = 0.0 if i == 0 else round(seg['vo_start'] - VIS_LEAD, 3)
for i, seg in enumerate(segs):
    seg['scene_end'] = TOTAL if i == len(segs) - 1 else segs[i + 1]['scene_start']
    seg['scene_dur'] = round(seg['scene_end'] - seg['scene_start'], 3)


def tokens(text):
    return [re.sub(r"[^\w'’-]", '', w) for w in text.split()]


def word_time(seg, word, nth=0):
    """Absolute start time of the nth occurrence of `word` in a segment's narration."""
    tm = T[seg['id']]
    want = re.sub(r"[^\w'’-]", '', word).lower()
    if tm['words']:
        hits = [w for w in tm['words'] if w['text'].lower() == want]
        if len(hits) <= nth:
            raise SystemExit(f"word {word!r} not found in {seg['id']}")
        return seg['vo_start'] + hits[nth]['start']
    for s_ in tm['sentences']:
        if want in [x.lower() for x in tokens(s_['text'])]:
            return seg['vo_start'] + s_['start']
    raise SystemExit(f"word {word!r} not found in sentences of {seg['id']}")


def sentence_starts(seg):
    """Absolute start and end time of every English sentence in a segment."""
    tm = T[seg['id']]
    if tm['sentences'] and not tm['words']:
        return [seg['vo_start'] + s_['start'] for s_ in tm['sentences']], [seg['vo_start'] + s_['end'] for s_ in tm['sentences']]
    sents = [x for x in re.split(r'(?<=[.!?])\s+', seg['en'].strip()) if x]
    words = tm['words']
    counts = [len(tokens(x)) for x in sents]
    if sum(counts) != len(words):
        raise SystemExit(f"word count mismatch in {seg['id']}: text {sum(counts)} vs tts {len(words)}")
    starts, ends, i = [], [], 0
    for c in counts:
        starts.append(seg['vo_start'] + words[i]['start'])
        ends.append(seg['vo_start'] + words[i + c - 1]['end'])
        i += c
    return starts, ends


# which English sentence each Chinese caption group starts on
GROUP_MAP = {'s01': [0, 1, 2], 's02': [0, 1, 3], 's03': [0, 1], 's04': [0], 's05': [0, 1], 's06': [0]}
captions = []
for i, seg in enumerate(segs):
    starts, ends = sentence_starts(seg)
    m = GROUP_MAP[seg['id']]
    assert len(m) == len(seg['zh']), seg['id']
    nxt_seg = segs[i + 1]['vo_start'] if i + 1 < len(segs) else TOTAL
    onscreen = set(seg.get('zh_onscreen', []))
    for g, text in enumerate(seg['zh']):
        if g in onscreen:
            continue   # the headline carries this sentence; no subtitle bar
        s0 = starts[m[g]] - 0.12
        last_sent = (m[g + 1] - 1) if g + 1 < len(m) else len(starts) - 1
        e0 = ends[last_sent] + 0.9
        if g + 1 < len(m):
            e0 = min(e0, starts[m[g + 1]] - 0.12)
        e0 = min(e0, nxt_seg - 0.3)
        captions.append({'id': f"cap-{seg['id']}-{g + 1}", 'text': text.rstrip('：，。'), 'start': round(s0, 3), 'end': round(e0, 3)})

for a, b in zip(captions, captions[1:]):
    assert a['end'] <= b['start'] + 1e-6, (a, b)

# ---------------------------------------------------------------- shared css
FONT_FACES = """
@font-face { font-family: 'Noto Serif SC'; font-weight: 900; font-style: normal; src: url('assets/fonts/NotoSerifSC-Black.woff2') format('woff2'); }
@font-face { font-family: 'Noto Serif SC'; font-weight: 700; font-style: normal; src: url('assets/fonts/NotoSerifSC-Bold.woff2') format('woff2'); }
@font-face { font-family: 'Noto Sans SC'; font-weight: 400; font-style: normal; src: url('assets/fonts/NotoSansSC-Regular.woff2') format('woff2'); }
@font-face { font-family: 'Noto Sans SC'; font-weight: 500; font-style: normal; src: url('assets/fonts/NotoSansSC-Medium.woff2') format('woff2'); }
@font-face { font-family: 'Noto Sans SC'; font-weight: 700; font-style: normal; src: url('assets/fonts/NotoSansSC-Bold.woff2') format('woff2'); }
@font-face { font-family: 'Fraunces'; font-weight: 700; font-style: normal; src: url('assets/fonts/Fraunces-Bold.woff2') format('woff2'); }
"""

BASE_CSS = FONT_FACES + """
#root { position: absolute; inset: 0; overflow: hidden; background: #10213a; color: #f4f6fa;
  font-family: 'Noto Sans SC', 'Noto Sans JP', sans-serif; }
#root * { box-sizing: border-box; margin: 0; }
.clip { position: absolute; inset: 0; }
.at { inset: auto; }
.eyebrow { font-size: 30px; font-weight: 500; letter-spacing: 0.22em; color: #8fb0ff; text-transform: uppercase; }
.en { font-family: 'Noto Sans SC', 'Noto Sans JP', sans-serif; font-weight: 400; color: #b8c4d9; }
.ground { position: absolute; inset: 0; background:
  radial-gradient(1200px 700px at 30% 20%, rgba(43,97,254,0.22), transparent 60%),
  radial-gradient(900px 600px at 85% 90%, rgba(43,97,254,0.14), transparent 60%), #10213a; }
.grid { position: absolute; inset: 0; background-image:
  linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
  linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px);
  background-size: 96px 96px; }
"""

FORMULA_CSS = """
#f-wrap { position: absolute; left: 160px; right: 160px; top: 0; bottom: 0; }
#f-eyebrow { position: absolute; top: 300px; left: 0; }
#f-line { position: absolute; top: 420px; left: 0; right: 0; display: flex; align-items: flex-start; gap: 36px; }
.term { display: flex; flex-direction: column; gap: 14px; }
.term .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 92px; line-height: 1; white-space: nowrap; }
.term .en { font-size: 28px; letter-spacing: 0.04em; white-space: nowrap; }
.op { font-family: 'Fraunces', serif; font-weight: 700; font-size: 84px; line-height: 1.1; color: #8fb0ff; padding: 0 4px; }
.op.minus { color: #ffb02e; }
#f-line2 { position: absolute; top: 620px; left: 0; display: flex; align-items: flex-start; gap: 36px; }
"""

FORMULA_MARKUP = """
      <div id="f-line">
        <div class="term" id="t-rooms"><div class="zh">可售房晚</div><div class="en">Available rooms</div></div>
        <div class="op" id="o1">×</div>
        <div class="term" id="t-occ"><div class="zh">入住率</div><div class="en">Occupancy</div></div>
        <div class="op" id="o2">×</div>
        <div class="term" id="t-rate"><div class="zh">房价</div><div class="en">Rate</div></div>
      </div>
      <div id="f-line2">
        <div class="op minus" id="o3">−</div>
        <div class="term" id="t-channel"><div class="zh">渠道成本</div><div class="en">Channel cost</div></div>
        <div class="op minus" id="o4">−</div>
        <div class="term" id="t-labour"><div class="zh">人力</div><div class="en">Labour</div></div>
      </div>
"""
FORMULA_ORDER = ['#t-rooms', '#o1', '#t-occ', '#o2', '#t-rate', '#o3', '#t-channel', '#o4', '#t-labour']
TERMS = ['#t-rooms', '#t-occ', '#t-rate', '#t-channel', '#t-labour']


def scene_file(sid, css, markup, script):
    return f"""<template>
  <style>
{BASE_CSS}
{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080">
{markup}
  </div>
  <script>
    (function () {{
      const tl = gsap.timeline({{ paused: true }});
      const EASE_IN = "expo.out";
{script}
      window.__timelines = window.__timelines || {{}};
      window.__timelines["{sid}"] = tl;
    }})();
  </script>
</template>
"""


def r3(x):
    return round(x, 3)


def reveal(sel, at, dur=0.4, blur=8):
    return f"      tl.fromTo('{sel}', {{ opacity: 0, filter: 'blur({blur}px)' }}, {{ opacity: 1, filter: 'blur(0px)', duration: {dur}, ease: EASE_IN }}, {r3(at)});\n"


def rise(sel, at, dur=0.6, y=28):
    return f"      tl.fromTo('{sel}', {{ opacity: 0, y: {y} }}, {{ opacity: 1, y: 0, duration: {dur}, ease: EASE_IN }}, {r3(at)});\n"


def fade_out(sel, at, dur=0.25):
    return f"      tl.to('{sel}', {{ opacity: 0, filter: 'blur(6px)', duration: {dur}, ease: 'power3.in' }}, {r3(at)});\n"


files = {}

# ================================================================ scene 1: formula
seg = BY['s01']
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = FORMULA_CSS + """
#f-mark { position: absolute; left: 0; right: 0; top: 0; bottom: 0; display: flex; align-items: center; justify-content: center; }
#f-mark img { width: 180px; height: auto; }
"""
markup = f"""
    <div id="f-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="f-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="f-mark" class="clip" data-start="0" data-duration="{r3(seg['vo_start'] + 0.2)}"><img id="f-mark-img" src="assets/logo-mark-white.png" alt="HogentX" /></div>
    <div id="f-wrap" class="clip" data-start="{r3(seg['vo_start'] - 0.3)}" data-duration="{r3(d - seg['vo_start'] + 0.3)}">
      <div id="f-eyebrow" class="eyebrow">每一家酒店的公式 · The hotel formula</div>{FORMULA_MARKUP}
    </div>
"""
script = ""
script += "      tl.fromTo('#f-mark-img', { opacity: 1, scale: 0.96 }, { opacity: 1, scale: 1, duration: 1.0, ease: EASE_IN }, 0);\n"
script += f"      tl.to('#f-mark-img', {{ opacity: 0, scale: 1.06, duration: 0.35, ease: 'power3.in' }}, {r3(seg['vo_start'] - 0.25)});\n"
script += reveal('#f-eyebrow', L('Every'))
ghost_at = L('formula')
for i, sel in enumerate(FORMULA_ORDER):
    script += f"      tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 0.2, duration: 0.5, ease: 'power2.out' }}, {r3(ghost_at + i * 0.06)});\n"
for sel, at in [('#t-rooms', L('Available')), ('#o1', L('occupancy') - 0.15), ('#t-occ', L('occupancy')), ('#o2', L('rate') - 0.15), ('#t-rate', L('rate')),
                ('#o3', L('Minus', 0)), ('#t-channel', L('channel')), ('#o4', L('Minus', 1)), ('#t-labour', L('labour'))]:
    script += f"      tl.to('{sel}', {{ opacity: 1, duration: 0.35, ease: 'power2.out' }}, {r3(at)});\n"
script += fade_out('#f-wrap > *', d - 0.3)
files['compositions/formula.html'] = scene_file('formula', css, markup, script)

# ================================================================ scene 2: leaks
seg = BY['s02']
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
leaks = [
    ('k1', '空房', 'Empty rooms nobody saw coming', 'Empty',
     '<path d="M6 30V14h40v16M6 30h40M6 30v6M46 30v6M12 14V8h10v6" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round"/>'),
    ('k2', '定错价', 'Prices set wrong', 'Prices',
     '<path d="M8 24 24 8h16v16L24 40 8 24z" stroke="currentColor" stroke-width="3" fill="none" stroke-linejoin="round"/><circle cx="32" cy="16" r="3" fill="currentColor"/>'),
    ('k3', '低价挂了一夜', 'A low rate left online overnight', 'low',
     '<path d="M34 8a16 16 0 1 0 12 26A14 14 0 0 1 34 8z" stroke="currentColor" stroke-width="3" fill="none" stroke-linejoin="round"/>'),
    ('k4', '差评', 'A bad review costs the next booking', 'bad',
     '<path d="M26 6l6 13 14 2-10 10 2 14-12-7-12 7 2-14L6 21l14-2z" stroke="currentColor" stroke-width="3" fill="none" stroke-linejoin="round"/><path d="M14 44l24-36" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>'),
]
css = """
#k-head { position: absolute; left: 160px; top: 230px; }
#k-title { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 72px; line-height: 1.15; margin-top: 18px; }
#k-row { position: absolute; left: 160px; right: 160px; top: 470px; display: flex; gap: 28px; }
.leak { flex: 1 1 0; min-height: 330px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 18px; padding: 34px 32px; display: flex; flex-direction: column; gap: 18px; position: relative; }
.leak .bar { position: absolute; left: 0; right: 0; top: 0; height: 4px; background: #ffb02e; border-radius: 18px 18px 0 0; }
.leak svg { width: 52px; height: 48px; color: #ffb02e; }
.leak .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 44px; line-height: 1.15; margin-top: 10px; }
.leak .en { font-size: 28px; line-height: 1.4; }
"""
cards = ''.join(
    f"""
        <div class="leak" id="{cid}"><div class="bar"></div>
          <svg viewBox="0 0 52 48">{svg}</svg>
          <div class="zh">{zh}</div><div class="en">{en}</div>
        </div>""" for cid, zh, en, _, svg in leaks)
markup = f"""
    <div id="k-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="k-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="k-head" class="clip at" data-start="0" data-duration="{d}">
      <div id="k-eyebrow" class="eyebrow">每一天 · Every day</div>
      <div id="k-title">收入在悄悄流失</div>
    </div>
    <div id="k-row" class="clip at" data-start="0" data-duration="{d}">{cards}
    </div>
"""
script = ""
script += reveal('#k-eyebrow', L('every'))
script += reveal('#k-title', L('leaks'), dur=0.5)
for cid, _, _, w, _ in leaks:
    script += rise('#' + cid, L(w) - 0.05, dur=0.55, y=34)
script += fade_out('#k-head, #k-row', d - 0.3)
files['compositions/leaks.html'] = scene_file('leaks', css, markup, script)

# ================================================================ scene 3: watch (typography only)
seg = BY['s03']
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = """
#w-stage { position: absolute; left: 160px; right: 160px; top: 0; bottom: 0; }
#w-title span { display: inline-block; }
#w-title, #w-big { position: absolute; left: 0; right: 0; top: 400px; text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 96px; line-height: 1.2; }
#w-big { letter-spacing: 0.04em; }
#w-sub { position: absolute; left: 0; right: 0; top: 530px; text-align: center; font-size: 32px; color: #b8c4d9; letter-spacing: 0.1em; }
"""
markup = f"""
    <div id="w-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="w-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="w-stage" class="clip" data-start="0" data-duration="{d}" data-layout-allow-overlap>
      <div id="w-title"><span id="w-l1">不是店长不用心</span><br/><span id="w-l2">而是没有人能每小时盯住五个后台</span></div>
      <div id="w-big">每小时 · 每天</div>
      <div id="w-sub">EVERY HOUR · EVERY DAY</div>
    </div>
"""
script = ""
script += reveal('#w-l1', L('Not'), dur=0.5)
script += reveal('#w-l2', L('Because', 1), dur=0.5)
script += fade_out('#w-title', L('every') - 0.25, dur=0.3)
script += reveal('#w-big', L('every'), dur=0.45)
script += reveal('#w-sub', L('hour'), dur=0.4)
script += fade_out('#w-big, #w-sub', d - 0.3)
files['compositions/watch.html'] = scene_file('watch', css, markup, script)

# ================================================================ scene 4: our own hotels
seg = BY['s04']
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = """
#o-photo { position: absolute; inset: 0; overflow: hidden; }
#o-photo img { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }
#o-tint { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(16,33,58,0.96) 0%, rgba(16,33,58,0.88) 45%, rgba(16,33,58,0.45) 100%); }
#o-eyebrow { position: absolute; left: 160px; top: 470px; }
#o-stores { position: absolute; left: 160px; top: 545px; display: flex; align-items: baseline; gap: 22px; }
#o-stores .n { font-family: 'Fraunces', serif; font-weight: 700; font-size: 170px; line-height: 1; }
#o-stores .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 52px; }
#o-stores .en { font-size: 28px; color: #b8c4d9; margin-left: 10px; }
"""
markup = f"""
    <div id="o-photo" class="clip" data-start="0" data-duration="{d}"><img id="o-img" src="assets/zhuxiaoding-store.jpg" alt="" /><div id="o-tint"></div></div>
    <div id="o-eyebrow" class="clip at eyebrow" data-start="0" data-duration="{d}">自家酒店 · 住小叮 · Our own hotels</div>
    <div id="o-stores" class="clip at" data-start="0" data-duration="{d}"><div class="n">29</div><div class="zh">家门店</div><div class="en">hotels we run ourselves</div></div>
"""
script = ""
script += f"      tl.fromTo('#o-img', {{ scale: 1.04 }}, {{ scale: 1.12, duration: {d}, ease: 'none' }}, 0);\n"
script += reveal('#o-eyebrow', L('We'), dur=0.5)
script += rise('#o-stores', L('twenty-nine') - 0.05, dur=0.6, y=30)
script += fade_out('#o-eyebrow, #o-stores', d - 0.3)
files['compositions/own.html'] = scene_file('own', css, markup, script)

# ================================================================ scene 5: back to the formula
seg = BY['s05']
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = FORMULA_CSS + """
#q-title { position: absolute; left: 0; top: 250px; font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 84px; line-height: 1.2; }
"""
markup = f"""
    <div id="q-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="q-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="f-wrap" class="clip" data-start="0" data-duration="{d}" data-hold>
      <div id="q-title">这些变量里，哪一个没人管？</div>{FORMULA_MARKUP}
    </div>
"""
script = ""
for i, sel in enumerate(FORMULA_ORDER):
    script += f"      tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: 'power2.out', immediateRender: false }}, {r3(i * 0.06)});\n"
script += reveal('#q-title', L('Which'), dur=0.5)
t0, t1 = L('variables'), L('watching')
for i, sel in enumerate(TERMS):
    script += f"      tl.to('{sel}', {{ opacity: 0.3, duration: 0.3, ease: 'power2.out' }}, {r3(t0 + i * (t1 - t0) / 4)});\n"
script += fade_out('#f-wrap > *', d - 0.3)
files['compositions/question.html'] = scene_file('question', css, markup, script)

# ================================================================ scene 6: close
seg = BY['s06']
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = """
#c-brand { position: absolute; left: 0; right: 0; top: 330px; display: flex; flex-direction: column; align-items: center; gap: 34px; }
#c-mark { width: 150px; height: auto; }
#c-word { width: 520px; height: auto; }
#c-tag { position: absolute; left: 0; right: 0; top: 760px; text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 44px; letter-spacing: 0.12em; color: #d9e2f5; }
#c-tag .en { display: block; font-family: 'Noto Sans SC', sans-serif; font-weight: 400; font-size: 28px; letter-spacing: 0.1em; color: #8fb0ff; margin-top: 14px; }
"""
brand_at = r3(L(BRAND) - 0.35)
markup = f"""
    <div id="c-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="c-brand" class="clip at" data-hold data-start="{brand_at}" data-duration="{r3(d - brand_at)}"><img id="c-mark" src="assets/logo-mark-white.png" alt="HogentX" /><img id="c-word" src="assets/logo-word-white.png" alt="HogentX" /></div>
    <div id="c-tag" class="clip at" data-hold data-start="{brand_at}" data-duration="{r3(d - brand_at)}">懂经营的酒店数字员工<span class="en">DIGITAL EMPLOYEES THAT UNDERSTAND THE HOTEL BUSINESS</span></div>
"""
script = ""
script += f"      tl.fromTo('#c-mark', {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: EASE_IN }}, {brand_at});\n"
script += f"      tl.fromTo('#c-word', {{ opacity: 0, filter: 'blur(10px)' }}, {{ opacity: 1, filter: 'blur(0px)', duration: 0.6, ease: EASE_IN }}, {r3(brand_at + 0.25)});\n"
script += reveal('#c-tag', L('Digital'), dur=0.6)
files['compositions/close.html'] = scene_file('close', css, markup, script)

# ================================================================ brand corner mark (until the close)
BRAND_END = BY['s06']['scene_start']
css = """
#root { background: transparent; }
#b-wrap { position: absolute; left: 72px; top: 52px; display: flex; align-items: center; gap: 18px; }
#b-mark { width: 44px; height: auto; }
#b-word { width: 130px; height: auto; opacity: 0.9; }
"""
markup = f"""
    <div id="b-wrap" class="clip at" data-start="0" data-duration="{r3(BRAND_END)}" data-layout-ignore><img id="b-mark" src="assets/logo-mark-white.png" alt="" /><img id="b-word" src="assets/logo-word-white.png" alt="HogentX" /></div>
"""
script = f"      tl.fromTo('#b-wrap', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: 'power2.out' }}, {r3(BY['s01']['vo_start'] - 0.2)});\n"
script += f"      tl.to('#b-wrap', {{ opacity: 0, duration: 0.3, ease: 'power2.in' }}, {r3(BRAND_END - 0.35)});\n"
files['compositions/brand.html'] = scene_file('brand', css, markup, script)

# ================================================================ captions
css = """
#root { background: transparent; }
.cap { position: absolute; left: 160px; right: 160px; bottom: 92px; text-align: center; }
.cap span { display: inline-block; padding: 12px 30px; border-radius: 12px; background: rgba(6,16,31,0.62);
  font-family: 'Noto Sans SC', 'Noto Sans JP', sans-serif; font-weight: 500; font-size: 42px; line-height: 1.35; color: #ffffff; letter-spacing: 0.02em; }
"""
markup = ''.join(
    f"""
    <div id="{c['id']}" class="clip at cap" data-start="{c['start']}" data-duration="{r3(c['end'] - c['start'])}"><span>{html.escape(c['text'])}</span></div>"""
    for c in captions)
script = ''
for c in captions:
    s0, e0 = c['start'], c['end']
    script += f"      tl.fromTo('#{c['id']} span', {{ opacity: 0, y: 10 }}, {{ opacity: 1, y: 0, duration: 0.18, ease: 'power2.out' }}, {s0});\n"
    script += f"      tl.to('#{c['id']} span', {{ opacity: 0, duration: 0.12, ease: 'power2.in' }}, {r3(e0 - 0.12)});\n"
    script += f"      tl.set('#{c['id']} span', {{ opacity: 0, visibility: 'hidden' }}, {e0});\n"
files['compositions/captions.html'] = scene_file('captions', css, markup, script)

# ================================================================ index.html
hosts = ''
for seg in segs:
    hosts += f"""
      <div id="{seg['scene']}" data-composition-id="{seg['scene']}" data-composition-src="compositions/{seg['scene']}.html"
        data-start="{seg['scene_start']}" data-duration="{seg['scene_dur']}" data-track-index="1" data-track-kind="graphics"
        data-width="1920" data-height="1080"></div>"""
voices = ''
for seg in segs:
    voices += f"""
      <audio id="vo-{seg['id']}" class="clip" src="assets/voice/{seg['id']}.mp3" data-start="{seg['vo_start']}" data-duration="{r3(seg['vo_dur'])}" data-volume="1" data-track-index="4"></audio>"""

# music bed: 0.45 alone, 0.2 under the voice, lifted to 0.32 inside the deliberate silences
BED, UNDER, HOLD = 0.45, 0.2, 0.32
points = [{"t": 0, "v": BED}, {"t": r3(LEAD - 0.4), "v": BED}, {"t": r3(LEAD + 0.3), "v": UNDER}]
for i, seg in enumerate(segs[:-1]):
    if seg.get('hold_s', 0) >= 0.8:
        nxt = segs[i + 1]['vo_start']
        points += [{"t": r3(seg['vo_end'] + 0.25), "v": UNDER}, {"t": r3(seg['vo_end'] + 0.75), "v": HOLD},
                   {"t": r3(nxt - 0.35), "v": HOLD}, {"t": r3(nxt - 0.05), "v": UNDER}]
points += [{"t": r3(VO_END + 0.2), "v": UNDER}, {"t": r3(VO_END + 1.4), "v": BED}, {"t": TOTAL, "v": BED}]
assert all(a['t'] < b['t'] for a, b in zip(points, points[1:])), points
music_lane = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": points}]})
index = f"""<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>HogentX 开场视频</title>
    <script src="assets/vendor/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #10213a; }}
      #root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; }}
      #bg {{ position: absolute; inset: 0; background: #10213a; }}
      #brand {{ z-index: 20; }}
      #captions {{ z-index: 30; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{TOTAL}" data-width="1920" data-height="1080">
      <div id="bg"></div>{hosts}
      <div id="brand" data-composition-id="brand" data-composition-src="compositions/brand.html"
        data-start="0" data-duration="{r3(BRAND_END)}" data-track-index="2" data-track-kind="graphics" data-width="1920" data-height="1080"></div>
      <div id="captions" data-composition-id="captions" data-composition-src="compositions/captions.html"
        data-start="0" data-duration="{TOTAL}" data-track-index="3" data-track-kind="captions" data-width="1920" data-height="1080"></div>{voices}
      <audio id="music" class="clip" src="assets/bgm/track.wav" data-start="0" data-duration="{TOTAL}" data-volume="1"
        data-fade-in="0.4" data-fade-out="2.6" data-track-index="5" data-automation='{music_lane}'></audio>
    </div>
    <script>
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = gsap.timeline({{ paused: true }});
    </script>
  </body>
</html>
"""
files['index.html'] = index

os.makedirs('compositions', exist_ok=True)
for stale in ('compositions/team.html', 'compositions/rule.html', 'compositions/proof.html', 'compositions/sgmy.html'):
    if os.path.exists(stale):
        os.remove(stale)
for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content)
json.dump({'total': TOTAL, 'vo_end': VO_END,
           'segments': [{k: seg[k] for k in ('id', 'scene', 'vo_start', 'vo_end', 'scene_start', 'scene_end')} for seg in segs],
           'captions': captions}, open('assets/voice/schedule.json', 'w'), indent=1, ensure_ascii=False)
print('total', TOTAL, 's; vo ends', round(VO_END, 2))
for seg in segs:
    print(f"  {seg['scene']:9s} scene {seg['scene_start']:6.2f}-{seg['scene_end']:6.2f}  vo {seg['vo_start']:6.2f}-{seg['vo_end']:6.2f}")
print(len(captions), 'caption groups shown')
