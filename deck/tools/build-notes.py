"""Generate speaker-notes.md from the <aside class="notes"> blocks in index.html.
Usage: python3 tools/build-notes.py   (run from the deck folder)"""
import html, re, pathlib

deck = pathlib.Path(__file__).resolve().parent.parent
src = (deck / 'index.html').read_text(encoding='utf-8')
slides = re.findall(r'<section class="slide[^"]*" data-label="([^"]+)"(?: data-appendix="([^"]+)")?>(.*?)</section>', src, re.S)

lines = ['# HogentX 新马合作交流 · 讲稿', '', '由 `index.html` 中的讲稿自动生成。演示时按 **N** 可在屏幕下方打开同样的内容。', '']
total = 0.0
for i, (label, appendix, body) in enumerate(slides, 1):
    title = re.search(r'<h[12][^>]*>(.*?)</h[12]>', body, re.S)
    title = re.sub(r'<[^>]+>', '', title.group(1)).strip() if title else ''
    note = re.search(r'<aside class="notes">(.*?)</aside>', body, re.S)
    note = html.unescape(note.group(1).strip()) if note else ''
    m = re.search(r'约 ([\d.]+) (分钟|秒)', note)
    if m and not appendix:
        total += float(m.group(1)) / (60 if m.group(2) == '秒' else 1)
    head = f'附录 {appendix}' if appendix else f'第 {i} 页'
    lines += [f'## {head} · {label}', '', f'**页面标题**：{title}' if title else '', '', note, '']
lines.insert(4, f'正文合计约 **{total:.0f} 分钟**，留出几分钟给开场寒暄和问答；附录只在被问到时使用。')
lines.insert(5, '')
(deck / 'speaker-notes.md').write_text('\n'.join(l for l in lines) + '\n', encoding='utf-8')
print('slides', len(slides), 'main minutes', round(total, 1))
