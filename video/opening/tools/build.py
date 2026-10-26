"""Build the HyperFrames opening film from script.json + the narration timings.

Writes index.html, compositions/*.html and compositions/captions.html. Every timed element is
written statically into the HTML; this script only resolves the times from the voice files so
that visuals land on the words that say them.

Usage: python3 tools/build.py
"""
import json, re, html, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
S = json.load(open('script.json'))
T = {t['id']: t for t in json.load(open('assets/voice/timings.json'))}

LEAD = 1.6          # seconds before the first word
GAP = S['gap_s']    # pause between narration files
TAIL = 4.6          # hold after the last word
VIS_LEAD = 0.45     # a scene cuts in this long before its narration starts
FPS = 30

# ---------------------------------------------------------------- schedule
segs = S['segments']
t = LEAD
for seg in segs:
    seg['vo_start'] = round(t, 3)
    seg['vo_dur'] = T[seg['id']]['duration']
    t += seg['vo_dur'] + GAP
VO_END = segs[-1]['vo_start'] + segs[-1]['vo_dur']
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
    # sentence boundaries only: locate the sentence that holds the word
    sents = tm['sentences']
    for s_ in sents:
        if want in [x.lower() for x in tokens(s_['text'])]:
            return seg['vo_start'] + s_['start']
    raise SystemExit(f"word {word!r} not found in sentences of {seg['id']}")


def sentence_starts(seg):
    """Absolute start time of every English sentence in a segment."""
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
GROUP_MAP = {
    's01': [0, 1, 2], 's02': [0, 1, 3], 's03': [0, 1], 's04': [0, 1, 3],
    's05': [0, 1, 2, 3], 's06': [0, 1, 2, 3], 's07': [0, 1, 3], 's08': [0, 2],
}
captions = []
for i, seg in enumerate(segs):
    starts, ends = sentence_starts(seg)
    m = GROUP_MAP[seg['id']]
    assert len(m) == len(seg['zh']), seg['id']
    nxt_seg = segs[i + 1]['vo_start'] if i + 1 < len(segs) else TOTAL
    for g, text in enumerate(seg['zh']):
        s0 = starts[m[g]] - 0.12
        last_sent = (m[g + 1] - 1) if g + 1 < len(m) else len(starts) - 1
        e0 = ends[last_sent] + 0.9
        if g + 1 < len(m):
            e0 = min(e0, starts[m[g + 1]] - 0.12)
        e0 = min(e0, nxt_seg - 0.3)
        captions.append({'id': f"cap-{seg['id']}-{g + 1}", 'text': text, 'start': round(s0, 3), 'end': round(e0, 3)})

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
.serif { font-family: 'Noto Serif SC', serif; font-weight: 900; }
.num { font-family: 'Fraunces', 'Noto Serif SC', serif; font-weight: 700; font-variant-numeric: lining-nums tabular-nums; }
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


def scene_file(sid, css, markup, script, extra_root_attrs=''):
    return f"""<template>
  <style>
{BASE_CSS}
{css}
  </style>
  <div id="root" data-composition-id="{sid}" data-width="1920" data-height="1080" {extra_root_attrs}>
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


# helper JS for a blur-in reveal at a local time
def reveal(sel, at, dur=0.4, blur=8, delay=0):
    return f"      tl.fromTo('{sel}', {{ opacity: 0, filter: 'blur({blur}px)' }}, {{ opacity: 1, filter: 'blur(0px)', duration: {dur}, ease: EASE_IN }}, {r3(at + delay)});\n"


def rise(sel, at, dur=0.6, y=28, delay=0):
    return f"      tl.fromTo('{sel}', {{ opacity: 0, y: {y} }}, {{ opacity: 1, y: 0, duration: {dur}, ease: EASE_IN }}, {r3(at + delay)});\n"


def fade_out(sel, at, dur=0.25):
    return f"      tl.to('{sel}', {{ opacity: 0, filter: 'blur(6px)', duration: {dur}, ease: 'power3.in' }}, {r3(at)});\n"


files = {}

# ================================================================ scene 1: formula
seg = segs[0]
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = """
#f-wrap { position: absolute; left: 160px; right: 160px; top: 0; bottom: 0; }
#f-eyebrow { position: absolute; top: 300px; left: 0; }
#f-line { position: absolute; top: 420px; left: 0; right: 0; display: flex; align-items: flex-start; gap: 36px; }
.term { display: flex; flex-direction: column; gap: 14px; }
.term .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 92px; line-height: 1; white-space: nowrap; }
.term .en { font-size: 28px; letter-spacing: 0.04em; white-space: nowrap; }
.op { font-family: 'Fraunces', serif; font-weight: 700; font-size: 84px; line-height: 1.1; color: #8fb0ff; padding: 0 4px; }
.op.minus { color: #ffb02e; }
#f-line2 { position: absolute; top: 620px; left: 0; display: flex; align-items: flex-start; gap: 36px; }
#f-mark { position: absolute; left: 0; right: 0; top: 0; bottom: 0; display: flex; align-items: center; justify-content: center; }
#f-mark img { width: 180px; height: auto; }
"""
markup = f"""
    <div id="f-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="f-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="f-mark" class="clip" data-start="0" data-duration="{r3(seg['vo_start'] + 0.2)}"><img id="f-mark-img" src="assets/logo-mark-white.png" alt="HogentX" /></div>
    <div id="f-wrap" class="clip" data-start="{r3(seg['vo_start'] - 0.3)}" data-duration="{r3(d - seg['vo_start'] + 0.3)}">
      <div id="f-eyebrow" class="eyebrow">每一家酒店的公式 · The hotel formula</div>
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
    </div>
"""
script = ""
script += "      tl.fromTo('#f-mark-img', { opacity: 1, scale: 0.96 }, { opacity: 1, scale: 1, duration: 1.0, ease: EASE_IN }, 0);\n"
script += f"      tl.to('#f-mark-img', {{ opacity: 0, scale: 1.06, duration: 0.35, ease: 'power3.in' }}, {r3(seg['vo_start'] - 0.25)});\n"
script += reveal('#f-eyebrow', L('Every'))
ghost_at = L('formula')
for i, sel in enumerate(['#t-rooms', '#o1', '#t-occ', '#o2', '#t-rate', '#o3', '#t-channel', '#o4', '#t-labour']):
    script += f"      tl.fromTo('{sel}', {{ opacity: 0 }}, {{ opacity: 0.2, duration: 0.5, ease: 'power2.out' }}, {r3(ghost_at + i * 0.06)});\n"
for sel, at in [('#t-rooms', L('Available')), ('#o1', L('occupancy') - 0.15), ('#t-occ', L('occupancy')), ('#o2', L('rate') - 0.15), ('#t-rate', L('rate')),
                ('#o3', L('Minus', 0)), ('#t-channel', L('channel')), ('#o4', L('Minus', 1)), ('#t-labour', L('labour'))]:
    script += f"      tl.to('{sel}', {{ opacity: 1, duration: 0.35, ease: 'power2.out' }}, {r3(at)});\n"
script += fade_out('#f-wrap > *', d - 0.3)
files['compositions/formula.html'] = scene_file('formula', css, markup, script)

# ================================================================ scene 2: leaks
seg = segs[1]
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

# ================================================================ scene 3: watch
seg = segs[2]
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
shots = ['workbench-home.jpg', 'screen-pricing.jpg', 'screen-reviews.jpg', 'screen-inspection.jpg', 'shot-occupancy.jpg']
pos = [(120, 150, 620), (780, 110, 560), (1380, 170, 440), (330, 560, 520), (980, 520, 640)]
css = """
#w-title { position: absolute; left: 160px; top: 150px; font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 64px; line-height: 1.2; }
.shot { position: absolute; border-radius: 12px; overflow: hidden; border: 1px solid rgba(255,255,255,0.14); box-shadow: 0 30px 60px rgba(0,0,0,0.45); background: #0b1730; }
.shot img { display: block; width: 100%; height: auto; }
#w-dim { position: absolute; inset: 0; background: rgba(16,33,58,0.78); }
#w-big { position: absolute; left: 0; right: 0; top: 400px; text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 128px; line-height: 1.1; letter-spacing: 0.04em; }
#w-sub { position: absolute; left: 0; right: 0; top: 580px; text-align: center; font-size: 32px; color: #b8c4d9; letter-spacing: 0.1em; }
"""
shot_markup = ''.join(
    f"""
      <div class="shot" id="sh{i + 1}" style="left:{x}px; top:{y}px; width:{w}px;"><img src="assets/{f}" alt="" /></div>"""
    for i, (f, (x, y, w)) in enumerate(zip(shots, pos)))
markup = f"""
    <div id="w-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="w-title" class="clip at" data-start="0" data-duration="{d}">不是店长不上心<br/>是没有人能盯住五个后台</div>
    <div id="w-shots" class="clip" data-start="0" data-duration="{d}" data-layout-allow-overlap>{shot_markup}
    </div>
    <div id="w-over" class="clip" data-start="{r3(L('every') - 0.1)}" data-duration="{r3(d - L('every') + 0.1)}">
      <div id="w-dim"></div>
      <div id="w-big">每小时 · 每天</div>
      <div id="w-sub">EVERY HOUR · EVERY DAY</div>
    </div>
"""
script = ""
script += reveal('#w-title', L('Not'), dur=0.5)
script += fade_out('#w-title', L('five') - 0.2, dur=0.3)
for i in range(5):
    script += rise(f'#sh{i + 1}', L('five') + i * 0.12, dur=0.6, y=60)
script += f"      tl.fromTo('#w-dim', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.4, ease: 'power2.inOut' }}, {L('every')});\n"
script += reveal('#w-big', L('every') + 0.05, dur=0.45)
script += reveal('#w-sub', L('hour'), dur=0.4)
script += fade_out('#w-title, #w-shots > *, #w-big, #w-sub', d - 0.3)
files['compositions/watch.html'] = scene_file('watch', css, markup, script)

# ================================================================ scene 4: team
seg = segs[3]
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
roles = [
    ('r1', '收益经理', 'Revenue manager', 'revenue',
     '<path d="M6 40h40M10 32l10-10 8 8 14-16" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
    ('r2', '宾客关系专员', 'Guest relations', 'guest',
     '<path d="M8 10h36v22H22l-10 8v-8H8z" stroke="currentColor" stroke-width="3" fill="none" stroke-linejoin="round"/>'),
    ('r3', '质检主管', 'Quality inspector', 'quality',
     '<path d="M10 8h32v36H10zM17 20l5 5 10-10M17 34h18" stroke="currentColor" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
    ('r4', '总经理助理', "General manager's assistant", 'general',
     '<path d="M6 16h40v26H6zM18 16v-6h16v6M6 28h40" stroke="currentColor" stroke-width="3" fill="none" stroke-linejoin="round"/>'),
]
css = """
#m-left { position: absolute; left: 160px; top: 300px; width: 640px; }
#m-logo { width: 96px; height: auto; margin-bottom: 36px; }
#m-title { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 72px; line-height: 1.2; }
#m-sub { margin-top: 22px; font-size: 28px; color: #b8c4d9; line-height: 1.5; }
#m-cards { position: absolute; left: 900px; top: 230px; width: 860px; display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
.role { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 18px; padding: 34px 32px; min-height: 270px; display: flex; flex-direction: column; gap: 14px; }
.role svg { width: 52px; height: 52px; color: #8fb0ff; }
.role .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 42px; line-height: 1.2; margin-top: 12px; white-space: nowrap; }
.role .en { font-size: 28px; }
"""
cards = ''.join(
    f"""
        <div class="role" id="{cid}"><svg viewBox="0 0 52 52">{svg}</svg><div class="zh">{zh}</div><div class="en">{en}</div></div>"""
    for cid, zh, en, _, svg in roles)
markup = f"""
    <div id="m-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="m-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="m-left" class="clip at" data-start="0" data-duration="{d}">
      <img id="m-logo" src="assets/logo-mark-white.png" alt="HogentX" />
      <div id="m-title">给每一家酒店<br/>一支数字员工队伍</div>
      <div id="m-sub">A team of digital employees<br/>for every hotel</div>
    </div>
    <div id="m-cards" class="clip at" data-start="0" data-duration="{d}">{cards}
    </div>
"""
script = ""
script += reveal('#m-logo', L('Hogent'), dur=0.5)
script += reveal('#m-title', L('gives'), dur=0.5)
script += reveal('#m-sub', L('team'), dur=0.5)
for cid, _, _, w, _ in roles:
    script += rise('#' + cid, L(w) - 0.05, dur=0.55, y=30)
script += fade_out('#m-left > *, #m-cards > *', d - 0.3)
files['compositions/team.html'] = scene_file('team', css, markup, script)

# ================================================================ scene 5: rule
seg = segs[4]
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
steps = [('p1', '读取', 'Read', 'read'), ('p2', '发现变化', 'Spot', 'spot'), ('p3', '核查', 'Check', 'check'),
         ('p4', '准备方案', 'Prepare', 'prepare')]
css = """
#u-eyebrow { position: absolute; left: 160px; top: 200px; }
#u-flow { position: absolute; left: 160px; right: 160px; top: 300px; display: flex; align-items: center; gap: 0; }
.node { flex: 1 1 0; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 26px 18px; text-align: center; min-height: 150px; }
#u-flow { align-items: stretch; }
.node .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 38px; line-height: 1.1; white-space: nowrap; }
.node .en { font-size: 28px; margin-top: 10px; line-height: 1.25; }
.node.src { border-color: rgba(143,176,255,0.6); }
.node.human { border-color: #3ddc97; background: rgba(61,220,151,0.08); }
.node.human .en { color: #3ddc97; }
.arrow { width: 40px; height: 3px; background: rgba(255,255,255,0.3); flex: 0 0 40px; position: relative; align-self: center; }
.arrow::after { content: ''; position: absolute; right: -2px; top: -6px; border: 7px solid transparent; border-left: 10px solid rgba(255,255,255,0.3); }
#u-rule { position: absolute; left: 160px; right: 160px; top: 560px; display: flex; align-items: center; gap: 40px; }
#u-lock { width: 120px; height: 120px; flex: 0 0 120px; color: #3ddc97; }
#u-rule-text .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 84px; line-height: 1.15; }
#u-rule-text .en { font-size: 30px; margin-top: 16px; letter-spacing: 0.04em; }
"""
flow = ''
flow += '<div class="node src" id="p0"><div class="zh">订房平台</div><div class="en">Platforms</div></div>'
for sid_, zh, en, _ in steps:
    flow += f'<div class="arrow" id="a-{sid_}"></div><div class="node" id="{sid_}"><div class="zh">{zh}</div><div class="en">{en}</div></div>'
flow += '<div class="arrow" id="a-p5"></div><div class="node human" id="p5"><div class="zh">人工确认</div><div class="en">Human confirms</div></div>'
markup = f"""
    <div id="u-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="u-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="u-eyebrow" class="clip at eyebrow" data-start="0" data-duration="{d}">全天候 · Around the clock</div>
    <div id="u-flow" class="clip at" data-start="0" data-duration="{d}">{flow}</div>
    <div id="u-rule" class="clip at" data-start="{r3(L('rule') - 0.3)}" data-duration="{r3(d - L('rule') + 0.3)}">
      <svg id="u-lock" viewBox="0 0 64 64"><rect x="12" y="28" width="40" height="30" rx="6" stroke="currentColor" stroke-width="3.5" fill="none"/><path d="M20 28v-8a12 12 0 0 1 24 0v8" stroke="currentColor" stroke-width="3.5" fill="none" stroke-linecap="round"/><circle cx="32" cy="43" r="4" fill="currentColor"/></svg>
      <div id="u-rule-text"><div class="zh">AI 只读取，人来确认</div><div class="en">The AI only reads. Every change is confirmed by a person.</div></div>
    </div>
"""
script = ""
script += reveal('#u-eyebrow', L('They'), dur=0.4)
script += rise('#p0', L('booking') - 0.1, dur=0.5, y=24)
for sid_, _, _, w in steps:
    script += reveal(f'#a-{sid_}', L(w) - 0.12, dur=0.25, blur=2)
    script += rise('#' + sid_, L(w) - 0.05, dur=0.5, y=24)
script += reveal('#a-p5', L('rule') - 0.2, dur=0.25, blur=2)
script += rise('#p5', L('rule') - 0.1, dur=0.5, y=24)
script += f"      tl.fromTo('#u-lock', {{ opacity: 0, scale: 0.8 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: 'back.out(1.4)' }}, {L('rule')});\n"
script += reveal('#u-rule-text .zh', L('only'), dur=0.5)
script += reveal('#u-rule-text .en', L('Every'), dur=0.5)
script += f"      tl.fromTo('#p5', {{ boxShadow: '0 0 0 rgba(61,220,151,0)' }}, {{ boxShadow: '0 0 48px rgba(61,220,151,0.45)', duration: 0.6, ease: 'power2.out' }}, {L('confirmed')});\n"
script += fade_out('#u-eyebrow, #u-flow > *, #u-rule > *', d - 0.3)
files['compositions/rule.html'] = scene_file('rule', css, markup, script)

# ================================================================ scene 6: proof
seg = segs[5]
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = """
#v-photo { position: absolute; inset: 0; overflow: hidden; }
#v-photo img { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }
#v-tint { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(16,33,58,0.96) 0%, rgba(16,33,58,0.9) 45%, rgba(16,33,58,0.45) 100%); }
#v-eyebrow { position: absolute; left: 160px; top: 200px; }
#v-stores { position: absolute; left: 160px; top: 280px; display: flex; align-items: baseline; gap: 22px; }
#v-stores .n { font-family: 'Fraunces', serif; font-weight: 700; font-size: 150px; line-height: 1; }
#v-stores .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 48px; }
#v-stores .en { font-size: 28px; color: #b8c4d9; margin-left: 10px; }
#v-task { position: absolute; left: 160px; top: 500px; font-size: 30px; color: #b8c4d9; }
#v-mins { position: absolute; left: 160px; top: 548px; display: flex; align-items: baseline; gap: 26px; }
#v-mins .n { font-family: 'Fraunces', serif; font-weight: 700; font-size: 150px; line-height: 1; min-width: 290px; }
#v-mins .arrow { font-family: 'Fraunces', serif; font-weight: 700; font-size: 80px; color: #8fb0ff; }
#v-mins .unit { font-size: 32px; color: #b8c4d9; }
#v-pct { position: absolute; left: 1180px; top: 420px; width: 600px; }
#v-pct .n { font-family: 'Fraunces', serif; font-weight: 700; font-size: 220px; line-height: 1.1; color: #3ddc97; }
#v-pct .zh { font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 44px; margin-top: 10px; }
#v-pct .tag { display: inline-block; margin-top: 18px; padding: 8px 18px; border: 1px solid rgba(255,255,255,0.3); border-radius: 999px; font-size: 28px; color: #b8c4d9; letter-spacing: 0.06em; }
"""
markup = f"""
    <div id="v-photo" class="clip" data-start="0" data-duration="{d}"><img id="v-img" src="assets/zhuxiaoding-store.jpg" alt="" /><div id="v-tint"></div></div>
    <div id="v-eyebrow" class="clip at eyebrow" data-start="0" data-duration="{d}">先在自家酒店验证 · 住小叮 · Tested in our own hotels</div>
    <div id="v-stores" class="clip at" data-start="0" data-duration="{d}"><div class="n">29</div><div class="zh">家门店</div><div class="en">properties, thin-margin segment</div></div>
    <div id="v-task" class="clip at" data-start="0" data-duration="{d}">六项日常任务 · 每天 · Six daily tasks, minutes a day</div>
    <div id="v-mins" class="clip at" data-start="0" data-duration="{d}"><div class="n" id="v-count">480</div><div class="arrow">→</div><div class="n" id="v-174">174</div><div class="unit">分钟 / 天</div></div>
    <div id="v-pct" class="clip at" data-start="0" data-duration="{d}"><div class="n" id="v-pct-n">−64%</div><div class="zh">时间减少约 64%</div><div class="tag">内部口径 · measured in-house</div></div>
"""
script = ""
script += f"      tl.fromTo('#v-img', {{ scale: 1.04 }}, {{ scale: 1.14, duration: {d}, ease: 'none' }}, 0);\n"
script += reveal('#v-eyebrow', L('tested'), dur=0.5)
script += rise('#v-stores', L('Twenty-nine') - 0.05, dur=0.6, y=30)
script += reveal('#v-task', L('Six'), dur=0.4)
script += rise('#v-count', L('four') - 0.05, dur=0.5, y=30)
script += (f"      const cnt = {{ v: 480 }};\n"
           f"      const paint = () => {{ document.getElementById('v-count').textContent = Math.round(cnt.v); }};\n"
           f"      tl.fromTo(cnt, {{ v: 480 }}, {{ v: 174, duration: {r3(L('seventy-four') - L('four') + 0.4)}, ease: 'power2.inOut', immediateRender: false, onUpdate: paint }}, {L('four')});\n"
           f"      tl.eventCallback('onUpdate', paint);\n")
script += reveal('#v-mins .arrow', L('to'), dur=0.3)
script += rise('#v-174', L('seventy-four') - 0.1, dur=0.5, y=30)
script += reveal('#v-mins .unit', L('seventy-four') + 0.2, dur=0.4)
script += f"      tl.fromTo('#v-pct-n', {{ opacity: 0, scale: 0.85 }}, {{ opacity: 1, scale: 1, duration: 0.6, ease: 'back.out(1.2)' }}, {L('About')});\n"
script += reveal('#v-pct .zh', L('percent'), dur=0.4)
script += reveal('#v-pct .tag', L('measured'), dur=0.4)
script += fade_out('#v-eyebrow, #v-stores, #v-task, #v-mins, #v-pct', d - 0.3)
files['compositions/proof.html'] = scene_file('proof', css, markup, script)

# ================================================================ scene 7: sgmy
seg = segs[6]
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = """
#g-eyebrow { position: absolute; left: 160px; top: 200px; }
#g-title { position: absolute; left: 160px; top: 270px; font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 110px; line-height: 1.1; }
#g-title .en { display: block; font-family: 'Noto Sans SC', sans-serif; font-weight: 400; font-size: 32px; color: #b8c4d9; margin-top: 14px; letter-spacing: 0.08em; }
#g-rows { position: absolute; left: 160px; right: 160px; top: 560px; display: flex; flex-direction: column; gap: 26px; }
.g-row { display: flex; align-items: center; gap: 18px; }
.g-row .lab { width: 340px; font-size: 28px; color: #b8c4d9; white-space: nowrap; }
.chip { padding: 14px 26px; border-radius: 999px; border: 1px solid rgba(255,255,255,0.22); font-size: 30px; font-weight: 500; white-space: nowrap; }
.chip.ok { border-color: rgba(61,220,151,0.7); }
.chip.ok::before { content: '✓ '; color: #3ddc97; }
.chip.plan { border-style: dashed; color: #d9e2f5; }
"""
langs = ['English', '中文', 'Bahasa Melayu', '日本語', '한국어']
markup = f"""
    <div id="g-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="g-grid" class="clip grid" data-start="0" data-duration="{d}" data-layout-ignore></div>
    <div id="g-eyebrow" class="clip at eyebrow" data-start="0" data-duration="{d}">现在 · Now</div>
    <div id="g-title" class="clip at" data-start="0" data-duration="{d}">新加坡 · 马来西亚<span class="en">SINGAPORE &amp; MALAYSIA</span></div>
    <div id="g-rows" class="clip at" data-start="0" data-duration="{d}">
      <div class="g-row" id="g-lang"><div class="lab">五种语言 · Languages</div>{''.join(f'<div class="chip" id="lg{i + 1}">{x}</div>' for i, x in enumerate(langs))}</div>
      <div class="g-row" id="g-ota"><div class="lab">已接入 · Connected</div><div class="chip ok" id="ota1">Agoda</div><div class="chip ok" id="ota2">Booking.com</div></div>
      <div class="g-row" id="g-data"><div class="lab">数据托管 · Hosting</div><div class="chip plan" id="data1">拟托管于新加坡 · Planned in Singapore</div></div>
    </div>
"""
script = ""
script += reveal('#g-eyebrow', L('Now'), dur=0.4)
script += reveal('#g-title', L('Singapore'), dur=0.55)
script += reveal('#g-lang .lab', L('Five'), dur=0.3)
for i in range(5):
    script += rise(f'#lg{i + 1}', L('Five') + 0.1 + i * 0.08, dur=0.45, y=18)
script += reveal('#g-ota .lab', L('Agoda') - 0.1, dur=0.3)
script += rise('#ota1', L('Agoda'), dur=0.45, y=18)
script += rise('#ota2', L('Agoda') + 0.35, dur=0.45, y=18)
script += reveal('#g-data .lab', L('plan') - 0.1, dur=0.3)
script += rise('#data1', L('plan'), dur=0.45, y=18)
script += fade_out('#g-eyebrow, #g-title, #g-rows > *', d - 0.3)
files['compositions/sgmy.html'] = scene_file('sgmy', css, markup, script)

# ================================================================ scene 8: close
seg = segs[7]
L = lambda w, n=0: r3(word_time(seg, w, n) - seg['scene_start'])
d = seg['scene_dur']
css = """
#c-line { position: absolute; left: 0; right: 0; top: 400px; text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 900; font-size: 84px; line-height: 1.2; }
#c-line .en { display: block; font-family: 'Noto Sans SC', sans-serif; font-weight: 400; font-size: 30px; color: #b8c4d9; margin-top: 18px; letter-spacing: 0.06em; }
#c-brand { position: absolute; left: 0; right: 0; top: 330px; display: flex; flex-direction: column; align-items: center; gap: 34px; }
#c-mark { width: 150px; height: auto; }
#c-word { width: 520px; height: auto; }
#c-tag { position: absolute; left: 0; right: 0; top: 760px; text-align: center; font-family: 'Noto Serif SC', serif; font-weight: 700; font-size: 44px; letter-spacing: 0.12em; color: #d9e2f5; }
#c-tag .en { display: block; font-family: 'Noto Sans SC', sans-serif; font-weight: 400; font-size: 28px; letter-spacing: 0.1em; color: #8fb0ff; margin-top: 14px; }
#c-black { position: absolute; inset: 0; background: #06101f; }
"""
brand_at = r3(L('Hogent') - 0.35)
markup = f"""
    <div id="c-ground" class="clip ground" data-start="0" data-duration="{d}"></div>
    <div id="c-line" class="clip at" data-hold data-start="0" data-duration="{brand_at}">用更少的人，提前看到收入风险<span class="en">Fewer people, watching more. Revenue risks, seen in time.</span></div>
    <div id="c-brand" class="clip at" data-hold data-start="{brand_at}" data-duration="{r3(d - brand_at)}"><img id="c-mark" src="assets/logo-mark-white.png" alt="HogentX" /><img id="c-word" src="assets/logo-word-white.png" alt="HogentX" /></div>
    <div id="c-tag" class="clip at" data-hold data-start="{brand_at}" data-duration="{r3(d - brand_at)}">懂经营的酒店数字员工<span class="en">THE HOTEL DIGITAL EMPLOYEE THAT UNDERSTANDS THE BUSINESS</span></div>
    <div id="c-black" class="clip" data-start="{r3(d - 1.2)}" data-duration="1.2"></div>
"""
script = ""
script += reveal('#c-line', L('Fewer'), dur=0.55)
script += fade_out('#c-line', brand_at - 0.3, dur=0.28)
script += f"      tl.fromTo('#c-mark', {{ opacity: 0, scale: 0.9 }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: EASE_IN }}, {brand_at});\n"
script += f"      tl.fromTo('#c-word', {{ opacity: 0, filter: 'blur(10px)' }}, {{ opacity: 1, filter: 'blur(0px)', duration: 0.6, ease: EASE_IN }}, {r3(brand_at + 0.25)});\n"
script += reveal('#c-tag', L('The'), dur=0.6)
script += f"      tl.fromTo('#c-black', {{ opacity: 0 }}, {{ opacity: 1, duration: 1.1, ease: 'power2.inOut' }}, {r3(d - 1.15)});\n"
files['compositions/close.html'] = scene_file('close', css, markup, script)

# ================================================================ brand corner mark
BRAND_END = segs[7]['scene_start']
css = """
#b-wrap { position: absolute; left: 72px; top: 52px; display: flex; align-items: center; gap: 18px; }
#b-mark { width: 44px; height: auto; }
#b-word { width: 130px; height: auto; opacity: 0.9; }
"""
markup = f"""
    <div id="b-wrap" class="clip at" data-start="0" data-duration="{r3(BRAND_END)}" data-layout-ignore><img id="b-mark" src="assets/logo-mark-white.png" alt="" /><img id="b-word" src="assets/logo-word-white.png" alt="HogentX" /></div>
"""
script = f"      tl.fromTo('#b-wrap', {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: 'power2.out' }}, {r3(segs[0]['vo_start'] - 0.2)});\n"
script += f"      tl.to('#b-wrap', {{ opacity: 0, duration: 0.3, ease: 'power2.in' }}, {r3(BRAND_END - 0.35)});\n"
files['compositions/brand.html'] = scene_file('brand', css.replace('#root {', '#root-unused {'), markup, script).replace(
    "#root { position: absolute; inset: 0; overflow: hidden; background: #10213a;", "#root { position: absolute; inset: 0; overflow: hidden; background: transparent;")

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
for i, seg in enumerate(segs):
    hosts += f"""
      <div id="{seg['scene']}" data-composition-id="{seg['scene']}" data-composition-src="compositions/{seg['scene']}.html"
        data-start="{seg['scene_start']}" data-duration="{seg['scene_dur']}" data-track-index="1" data-track-kind="graphics"
        data-width="1920" data-height="1080"></div>"""
voices = ''
for i, seg in enumerate(segs):
    voices += f"""
      <audio id="vo-{seg['id']}" class="clip" src="assets/voice/{seg['id']}.mp3" data-start="{seg['vo_start']}" data-duration="{r3(seg['vo_dur'])}" data-volume="1" data-track-index="4"></audio>"""
music_lane = json.dumps({"version": 1, "lanes": [{"target": "volume", "points": [
    {"t": 0, "v": 0.45}, {"t": r3(LEAD - 0.4), "v": 0.45}, {"t": r3(LEAD + 0.3), "v": 0.2},
    {"t": r3(VO_END + 0.2), "v": 0.2}, {"t": r3(VO_END + 1.4), "v": 0.45}, {"t": TOTAL, "v": 0.45}]}]})
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
for path, content in files.items():
    with open(path, 'w') as f:
        f.write(content)
json.dump({'total': TOTAL, 'vo_end': VO_END, 'segments': [{k: seg[k] for k in ('id', 'scene', 'vo_start', 'vo_dur', 'scene_start', 'scene_end')} for seg in segs],
           'captions': captions}, open('assets/voice/schedule.json', 'w'), indent=1, ensure_ascii=False)
print('total', TOTAL, 's; vo ends', round(VO_END, 2))
for seg in segs:
    print(f"  {seg['scene']:8s} scene {seg['scene_start']:7.2f}-{seg['scene_end']:7.2f}  vo {seg['vo_start']:7.2f}")
print(len(captions), 'caption groups')
