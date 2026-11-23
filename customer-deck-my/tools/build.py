#!/usr/bin/env python3
"""把 src/ 下的源文件合成可离线打开的单文件 HTML，一共三份，各自默认一种语言。

用法（在 customer-deck-my 目录下）：
    python3 tools/build.py

输入：src/deck.html（中文，唯一的内容来源）、src/deck.css、src/deck.js、
      i18n/strings.json（英文、马来文）、assets/ 下的图片与字体
输出：
    HogentX-Malaysia-Hotel-Briefing.html      打开默认中文
    HogentX-Malaysia-Hotel-Briefing-EN.html   打开默认 English
    HogentX-Malaysia-Hotel-Briefing-BM.html   打开默认 Bahasa Melayu
三份文件内容相同，都能在页面里切换三种语言；区别只是打开时（以及不能运行脚本的预览里）先显示哪一种。
样式、脚本、图片、字体全部内嵌，零外部请求。
"""
import base64
import json
import mimetypes
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i18n  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
BASENAME = "HogentX-Malaysia-Hotel-Briefing"
OUTPUTS = {"zh": f"{BASENAME}.html", "en": f"{BASENAME}-EN.html", "ms": f"{BASENAME}-BM.html"}

# 结尾页的两个联系方式是读者自己点的链接，不是页面加载的资源
ALLOWED_LINKS = ['href="mailto:hi@intent-computing.com"', 'href="https://hogentx.com"']

MIME = {
    ".png": "image/png",
    ".webp": "image/webp",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".woff2": "font/woff2",
}


def data_uri(path: Path) -> str:
    if not path.is_file():
        sys.exit(f"缺少素材文件：{path}")
    mime = MIME.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0]
    if not mime:
        sys.exit(f"不认识的素材类型：{path}")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def inline_css(css: str) -> str:
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def repl(m: re.Match) -> str:
        return f'url("{data_uri((SRC / m.group(1)).resolve())}")'

    css = re.sub(r'url\("(\.\./assets/[^"]+)"\)', repl, css)
    css = re.sub(r"\n\s*\n+", "\n", css).strip()
    return css


def leftovers(html: str):
    probe = html
    for ok in ALLOWED_LINKS:
        probe = probe.replace(ok, "")
    found = re.findall(r'(?:src|href)="(?!data:|#)[^"]*"', probe)
    found += re.findall(r'url\((?!"data:)[^)]*\)', probe)
    found += re.findall(r"https?://[^\s\"'<>)]+", probe)
    return sorted(set(found))


def main() -> None:
    source = (SRC / "deck.html").read_text(encoding="utf-8")
    css = inline_css((SRC / "deck.css").read_text(encoding="utf-8"))
    js = (SRC / "deck.js").read_text(encoding="utf-8").strip()

    # 发给客户的文件里不留源文件注释
    source = re.sub(r"<!--.*?-->\n?", "", source, flags=re.S)
    if '<link rel="stylesheet" href="deck.css">' not in source or '<script src="deck.js"></script>' not in source:
        sys.exit("src/deck.html 里找不到 deck.css 或 deck.js 的引用")

    for lang, name in OUTPUTS.items():
        html, tables = i18n.localize(source, lang)
        html = html.replace('<link rel="stylesheet" href="deck.css">', "<style>\n" + css + "\n</style>")

        def img_repl(m: re.Match) -> str:
            return f'src="{data_uri((SRC / m.group(1)).resolve())}"'

        html, n_img = re.subn(r'src="(\.\./assets/[^"]+)"', img_repl, html)

        # 三语字典：切换语言时由脚本读取；"</" 转义，避免提前结束 script
        blob = json.dumps(tables, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
        for lg in ("en", "ms"):
            bad = [t for t in tables[lg] if re.search(r"https?://(?!hogentx\.com)", t)]
            if bad:
                sys.exit(f"译文里出现了外部网址：{bad[0][:80]}")
        html = html.replace(
            '<script src="deck.js"></script>',
            '<script type="application/json" id="i18n">' + blob + "</script>\n<script>\n" + js + "\n</script>",
        )

        # 自检：除了两个联系方式和字典本身，不允许残留任何外部或相对引用
        probe = re.sub(r'<script type="application/json" id="i18n">.*?</script>', "", html, flags=re.S)
        left = leftovers(probe)
        if left:
            sys.exit("仍有未内嵌的引用：" + ", ".join(left[:10]))

        out = ROOT / name
        out.write_text(html, encoding="utf-8")
        print(f"已生成 {name}：{out.stat().st_size / 1024 / 1024:.2f} MB，内嵌图片 {n_img} 张，文字 {len(tables['zh'])} 条 × 3 种语言，无外部引用。")


if __name__ == "__main__":
    main()
