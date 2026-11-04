# -*- coding: utf-8 -*-
"""用模型输出的表格替换模板占位符，生成最终 Markdown，并用 pandoc 导出 Word。"""
import json, re, subprocess, sys, os
BASE = "/home/user/CC/douyin-live/report"
TEMPLATE = f"{BASE}/住小叮抖音直播组织方案_股东决策文档.template.md"
OUT_MD = f"{BASE}/住小叮抖音直播组织方案_股东决策文档.md"
OUT_DOCX = f"{BASE}/住小叮抖音直播组织方案_股东决策文档.docx"
T = json.load(open(f"{BASE}/build/tables.json", encoding="utf-8"))
T["SOURCES"] = open(f"{BASE}/build/sources.md", encoding="utf-8").read().strip()
tpl = open(TEMPLATE, encoding="utf-8").read()
missing = sorted(set(re.findall(r"\{\{([A-Za-z0-9_一-鿿+]+)\}\}", tpl)) - set(T))
if missing:
    print("MISSING placeholders:", missing); sys.exit(1)
out = re.sub(r"\{\{([A-Za-z0-9_一-鿿+]+)\}\}", lambda m: str(T[m.group(1)]), tpl)

# 按内容宽度重写管道表的分隔行，让 pandoc 按比例分配列宽（中文按 2 个字符宽计）
def dwidth(text):
    return sum(2 if ord(ch) > 0x2E80 else 1 for ch in text)
def split_row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]
def fix_tables(md):
    lines = md.split("\n"); i = 0; outl = []
    while i < len(lines):
        if i + 1 < len(lines) and lines[i].lstrip().startswith("|") and re.match(r"^\s*\|?\s*:?-{3,}", lines[i + 1]):
            hdr = split_row(lines[i]); sep = split_row(lines[i + 1])
            body = []; j = i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                body.append(split_row(lines[j])); j += 1
            ncol = len(hdr)
            widths = []
            for c in range(ncol):
                cells = [hdr[c]] + [r[c] for r in body if c < len(r)]
                w = max(dwidth(x) for x in cells)
                widths.append(max(6, min(w, 36)))
            newsep = []
            for c in range(ncol):
                right = sep[c].endswith(":") if c < len(sep) else False
                newsep.append("-" * widths[c] + (":" if right else ""))
            outl.append(lines[i]); outl.append("|" + "|".join(newsep) + "|")
            for r in body: outl.append("| " + " | ".join(r) + " |")
            i = j
        else:
            outl.append(lines[i]); i += 1
    return "\n".join(outl)
out = fix_tables(out)
open(OUT_MD, "w", encoding="utf-8").write(out)
print("md written:", OUT_MD, len(out), "chars")
cmd = ["pandoc", OUT_MD, "-o", OUT_DOCX, "--reference-doc", f"{BASE}/build/reference.docx", "--resource-path", BASE]
subprocess.run(cmd, check=True)
print("docx written:", OUT_DOCX)
