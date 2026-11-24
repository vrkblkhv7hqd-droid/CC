#!/usr/bin/env python3
"""三语支持：从中文源文件里找出要翻译的文字，和 i18n/strings.json 里的英文、马来文对上。

中文源文件（src/deck.html）是唯一的内容来源。本工具把其中每一段文字当作一个“条目”：
  - 元素条目：直接含有文字的最外层元素，条目内容是它的内部 HTML（可以带 <b>、<span> 等行内标记）。
  - 属性条目：placeholder、aria-label、alt、data-title、data-label、data-fill、meta description 等属性里的文字。
只有含中文的条目需要翻译；纯数字、纯英文（如 RM、OTA、A2A）原样保留。

用法（在 customer-deck-my 目录下）：
    python3 tools/i18n.py list            # 列出全部条目和翻译状态
    python3 tools/i18n.py missing         # 只列出还没有翻译的条目
    python3 tools/i18n.py merge 文件       # 把草稿（#编号 / 英文 / 马来文，三行一组）并入 i18n/strings.json
build.py 会调用 localize()，缺翻译时直接报错，避免发出半中半英的文件。
"""
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_HTML = ROOT / "src" / "deck.html"
STRINGS = ROOT / "i18n" / "strings.json"
LANGS = ("zh", "en", "ms")
HTML_LANG = {"zh": "zh-CN", "en": "en", "ms": "ms"}

VOID = {"br", "img", "input", "meta", "link", "hr", "use", "path", "circle", "source", "wbr"}
SKIP_SUBTREE = {"script", "style"}  # 图表（svg）里的 <text>、<title>、<desc> 也要翻译
CONTAINER_ONLY = {"html", "head", "body", "main"}
ATTRS = ("placeholder", "aria-label", "alt", "data-title", "data-label", "data-fill", "title")
CJK = re.compile(r"[㐀-鿿豈-﫿]")


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class Node:
    __slots__ = ("tag", "attrs", "pos", "raw", "inner_start", "inner_end", "children", "has_text", "parent")

    def __init__(self, tag, attrs, pos, raw, parent):
        self.tag, self.attrs, self.pos, self.raw, self.parent = tag, dict(attrs), pos, raw, parent
        self.inner_start = pos + len(raw)
        self.inner_end = None
        self.children = []
        self.has_text = False


class Tree(HTMLParser):
    def __init__(self, source: str):
        super().__init__(convert_charrefs=False)
        self.source = source
        self.line_starts = [0]
        for m in re.finditer(r"\n", source):
            self.line_starts.append(m.end())
        self.root = Node("#root", [], 0, "", None)
        self.cur = self.root
        self.feed(source)
        self.close()

    def abspos(self):
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs, self.abspos(), self.get_starttag_text(), self.cur)
        self.cur.children.append(node)
        if tag in VOID:
            node.inner_end = node.inner_start
        else:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        node = Node(tag, attrs, self.abspos(), self.get_starttag_text(), self.cur)
        node.inner_end = node.inner_start
        self.cur.children.append(node)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        node = self.cur
        while node is not self.root and node.tag != tag:
            node = node.parent
        if node is self.root:
            return
        node.inner_end = self.abspos()
        self.cur = node.parent

    def handle_data(self, data):
        if data.strip():
            self.cur.has_text = True

    def handle_entityref(self, name):
        self.cur.has_text = True

    def handle_charref(self, name):
        self.cur.has_text = True


def scan(source: str):
    """返回 (元素条目, 属性条目)。元素条目：(node, msgid)；属性条目：(node, attr, msgid)。"""
    tree = Tree(source)
    units, attr_units = [], []

    def visit(node, inside_unit=False):
        if node.tag in SKIP_SUBTREE or "data-noi18n" in node.attrs:
            return
        if node.tag == "meta" and node.attrs.get("name") == "description":
            attr_units.append((node, "content", norm(node.attrs.get("content", ""))))
        for a in ATTRS:
            v = node.attrs.get(a)
            if v and CJK.search(v):
                if inside_unit:
                    sys.exit(f"条目内部的元素不能再带要翻译的属性：<{node.tag} {a}=\"{v}\">")
                attr_units.append((node, a, norm(v)))
        if inside_unit:
            for c in node.children:
                visit(c, True)
            return
        # .nb / .nowrap 只是中文断行用的词组标记：含有它们的元素整句算一个条目
        phrase_kids = any(
            c.tag in ("span", "b") and {"nb", "nowrap"} & set((c.attrs.get("class") or "").split())
            for c in node.children
        )
        if (node.has_text or phrase_kids) and node.tag not in CONTAINER_ONLY and node.tag != "#root":
            msgid = norm(source[node.inner_start:node.inner_end])
            if re.search(r"<(input|button|svg|table|img)\b", msgid):
                sys.exit(f"这一段文字里混有控件，请把文字单独包一层 <span>：{msgid[:80]}")
            if CJK.search(msgid):
                units.append((node, msgid))
            for c in node.children:
                visit(c, True)
            return
        for c in node.children:
            visit(c, False)

    visit(tree.root)
    return units, attr_units


def load_strings():
    if not STRINGS.is_file():
        return {}
    rows = json.loads(STRINGS.read_text(encoding="utf-8"))
    return {r["zh"]: r for r in rows}


def catalog(source: str):
    units, attr_units = scan(source)
    seen, order = set(), []
    for _, msgid in units:
        if msgid not in seen:
            seen.add(msgid)
            order.append(msgid)
    for _, _, msgid in attr_units:
        if msgid not in seen:
            seen.add(msgid)
            order.append(msgid)
    return order


def esc_attr(v: str) -> str:
    return v.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")


def localize(source: str, lang: str, strict: bool = True):
    """把中文源 HTML 变成：静态内容为 lang、每个条目带编号、并附三语字典的 HTML。返回 (html, 字典)。"""
    table = load_strings()
    units, attr_units = scan(source)
    order = catalog(source)
    index = {m: i for i, m in enumerate(order)}
    missing = []
    tables = {"zh": order[:]}
    for l in ("en", "ms"):
        out = []
        for m in order:
            row = table.get(m)
            if row and row.get(l):
                out.append(row[l])
            else:
                missing.append((l, m))
                out.append(m)
        tables[l] = out
    if missing and strict:
        lines = "\n".join(f"  [{l}] {m[:90]}" for l, m in missing[:40])
        sys.exit(f"还有 {len(missing)} 处没有翻译（python3 tools/i18n.py missing 查看全部）：\n{lines}")

    edits = []  # (start, end, replacement)
    by_node = {}
    for node, attr, msgid in attr_units:
        by_node.setdefault(id(node), [node, []])[1].append((attr, msgid))
    unit_nodes = {id(n): m for n, m in units}
    touched = {}
    for node, msgid in units:
        touched[id(node)] = node
    for key, (node, _) in by_node.items():
        touched[key] = node
    for key, node in touched.items():
        raw = node.raw
        extra = ""
        if key in unit_nodes:
            n = index[unit_nodes[key]]
            extra += f' data-i="{n}"'
            edits.append((node.inner_start, node.inner_end, tables[lang][n]))
        if key in by_node:
            pairs = []
            for attr, msgid in by_node[key][1]:
                n = index[msgid]
                pairs.append(f"{attr}={n}")
                if lang != "zh":
                    pat = re.compile(r'(\b' + re.escape(attr) + r'=")[^"]*(")')
                    raw, k = pat.subn(lambda mm: mm.group(1) + esc_attr(tables[lang][n]) + mm.group(2), raw, count=1)
                    if k != 1:
                        sys.exit(f"找不到属性 {attr}：{node.raw[:80]}")
            extra += ' data-ia="' + ";".join(pairs) + '"'
        close = "/>" if raw.rstrip().endswith("/>") else ">"
        raw = raw.rstrip()[: -len(close)].rstrip() + extra + close
        edits.append((node.pos, node.pos + len(node.raw), raw))
    out = source
    for start, end, text in sorted(edits, key=lambda e: e[0], reverse=True):
        out = out[:start] + text + out[end:]
    out = re.sub(r'<html lang="[^"]*"', f'<html lang="{HTML_LANG[lang]}" data-lang="{lang}"', out, count=1)
    return out, tables


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    source = SRC_HTML.read_text(encoding="utf-8")
    source = re.sub(r"<!--.*?-->\n?", "", source, flags=re.S)
    order = catalog(source)
    table = load_strings()
    if cmd in ("list", "missing"):
        n_missing = 0
        for i, m in enumerate(order):
            row = table.get(m, {})
            done = bool(row.get("en")) and bool(row.get("ms"))
            n_missing += 0 if done else 1
            if cmd == "list" or not done:
                print(f"#{i}\t{m}")
                if cmd == "list" and done:
                    print(f"\tEN  {row['en']}\n\tMS  {row['ms']}")
        unused = [z for z in table if z not in set(order)]
        print(f"共 {len(order)} 条，未翻译 {n_missing} 条，字典里已不再使用 {len(unused)} 条。", file=sys.stderr)
    elif cmd == "merge":
        text = Path(sys.argv[2]).read_text(encoding="utf-8")
        blocks = re.findall(r"^#(\d+)\n(.*)\n(.*)$", text, flags=re.M)
        for num, en, ms in blocks:
            i = int(num)
            if i >= len(order):
                sys.exit(f"编号超出范围：#{i}")
            if not en.strip() or not ms.strip():
                sys.exit(f"#{i} 缺英文或马来文")
            table[order[i]] = {"zh": order[i], "en": en.strip(), "ms": ms.strip()}
        rows = [table[m] for m in order if m in table]
        STRINGS.parent.mkdir(exist_ok=True)
        STRINGS.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        left = [m for m in order if m not in table]
        print(f"已并入 {len(blocks)} 条；字典共 {len(rows)} 条；还缺 {len(left)} 条。")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
