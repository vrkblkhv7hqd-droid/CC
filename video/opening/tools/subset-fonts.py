"""Subset the Noto CJK source fonts to the characters the film uses.

Usage: python3 tools/subset-fonts.py <dir with NotoSerifCJKsc-Black.otf, NotoSerifCJKsc-Bold.otf,
       NotoSansCJKsc-Regular.otf, NotoSansCJKsc-Medium.otf, NotoSansCJKsc-Bold.otf>

The source OTFs come from https://github.com/notofonts/noto-cjk (Serif/OTF/SimplifiedChinese and
Sans/OTF/SimplifiedChinese). Characters are collected from script.json (every subtitle) and from the
on-screen strings in tools/build.py, plus digits, Latin and the symbols the layouts use, so a wording
change never falls back to a system font. build.py calls this automatically when the directory exists.
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOBS = [
    ('NotoSerifCJKsc-Black.otf', 'NotoSerifSC-Black.woff2'),
    ('NotoSerifCJKsc-Bold.otf', 'NotoSerifSC-Bold.woff2'),
    ('NotoSansCJKsc-Regular.otf', 'NotoSansSC-Regular.woff2'),
    ('NotoSansCJKsc-Medium.otf', 'NotoSansSC-Medium.woff2'),
    ('NotoSansCJKsc-Bold.otf', 'NotoSansSC-Bold.woff2'),
]


def used_characters():
    chars = set()
    s = json.load(open(os.path.join(ROOT, 'script.json')))
    for seg in s['segments']:
        for g in seg['zh']:
            chars |= set(g)
    src = open(os.path.join(ROOT, 'tools', 'build.py'), encoding='utf-8').read()
    chars |= set(re.findall(r'[⺀-鿿豈-﫿＀-￯　-〿]', src))
    chars |= set('0123456789%×−→·：，。、；！？（）「」“”…✓–-+&/.,:;\'"() ')
    chars |= set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
    return {c for c in chars if not c.isspace() or c == ' '}


def subset(src_dir):
    chars = used_characters()
    uni = ','.join(f'U+{ord(c):04X}' for c in sorted(chars))
    out_dir = os.path.join(ROOT, 'assets', 'fonts')
    os.makedirs(out_dir, exist_ok=True)
    for src, dst in JOBS:
        path = os.path.join(src_dir, src)
        if not os.path.exists(path):
            raise SystemExit(f'missing source font {path}')
        subprocess.run(['pyftsubset', path, '--unicodes=' + uni, '--flavor=woff2',
                        '--output-file=' + os.path.join(out_dir, dst), '--layout-features=*',
                        '--no-hinting', '--desubroutinize'], check=True)
    print(f'fonts: {len(chars)} characters, {len(JOBS)} files written to assets/fonts/')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    subset(sys.argv[1])
