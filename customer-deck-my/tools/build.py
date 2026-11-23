#!/usr/bin/env python3
"""把 src/ 下的源文件合成一个可离线打开的单文件 HTML。

用法（在 customer-deck-my 目录下）：
    python3 tools/build.py

输入：src/deck.html、src/deck.css、src/deck.js、assets/ 下的图片与字体
输出：HogentX-Malaysia-Hotel-Briefing.html（样式、脚本、图片、字体全部内嵌，零外部请求）
"""
import base64
import mimetypes
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
OUT = ROOT / "HogentX-Malaysia-Hotel-Briefing.html"

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


def main() -> None:
    html = (SRC / "deck.html").read_text(encoding="utf-8")
    css = inline_css((SRC / "deck.css").read_text(encoding="utf-8"))
    js = (SRC / "deck.js").read_text(encoding="utf-8").strip()

    # 发给客户的文件里不留源文件注释
    html = re.sub(r"<!--.*?-->\n?", "", html, flags=re.S)

    if '<link rel="stylesheet" href="deck.css">' not in html or '<script src="deck.js"></script>' not in html:
        sys.exit("src/deck.html 里找不到 deck.css 或 deck.js 的引用")
    html = html.replace('<link rel="stylesheet" href="deck.css">', "<style>\n" + css + "\n</style>")
    html = html.replace('<script src="deck.js"></script>', "<script>\n" + js + "\n</script>")

    def img_repl(m: re.Match) -> str:
        return f'src="{data_uri((SRC / m.group(1)).resolve())}"'

    html, n_img = re.subn(r'src="(\.\./assets/[^"]+)"', img_repl, html)

    # 自检：不允许残留任何外部或相对引用
    # 结尾页的两个联系方式是读者自己点的链接，不是页面加载的资源
    probe = html
    for ok in ALLOWED_LINKS:
        probe = probe.replace(ok, "")
    leftovers = re.findall(r'(?:src|href)="(?!data:|#)[^"]*"', probe)
    leftovers += re.findall(r'url\((?!"data:)[^)]*\)', probe)
    leftovers += [u for u in re.findall(r"https?://[^\s\"'<>)]+", probe)]
    if leftovers:
        sys.exit("仍有未内嵌的引用：" + ", ".join(sorted(set(leftovers))[:10]))

    OUT.write_text(html, encoding="utf-8")
    size = OUT.stat().st_size
    print(f"已生成 {OUT.name}：{size / 1024 / 1024:.2f} MB，内嵌图片 {n_img} 张，无外部引用。")


if __name__ == "__main__":
    main()
