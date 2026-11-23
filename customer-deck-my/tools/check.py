#!/usr/bin/env python3
"""口径自检：改完文字后跑一遍，确认没有把旧数字、旧说法或越界表述带进客户版。

用法（在 customer-deck-my 目录下）：
    python3 tools/build.py && python3 tools/check.py

检查三类问题：
  1. 禁用内容：旧门店数、旧定价、内部与市场数据、点名渠道、投资人叙事、错误缩写等（出现即不通过）。
  2. 需带否定或限定才能出现的说法：自动改价、自动发布、保证增收、200+ OTA、实时收益报表等。
  3. 必备内容：三档月费、每张截图的来源与验证范围、31/56 的写法、主体名称、联系方式等。
另外确认成品文件没有外部引用、没有注释。
"""
import html as htmllib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILT = ROOT / "HogentX-Malaysia-Hotel-Briefing.html"

problems = []
notes = []


def fail(msg):
    problems.append(msg)


def visible_text(doc: str) -> str:
    body = re.sub(r"<style\b.*?</style>", " ", doc, flags=re.S)
    body = re.sub(r"<script\b.*?</script>", " ", body, flags=re.S)
    attrs = re.findall(r'\b(?:alt|aria-label|title|placeholder|data-title|content)="([^"]*)"', body)
    body = re.sub(r'="data:[^"]*"', '=""', body)
    # .nb / .nowrap 只是断行用的词组标记，读文字时当作不存在
    body = re.sub(r'<(span|b) class="(?:nb|nowrap)">(.*?)</\1>', r"\2", body, flags=re.S)
    body = re.sub(r"<(br|/p|/li|/h[1-6]|/div|/tr|/td|/th|/dd|/dt|/section|/article|/figcaption|/span|/button|/label)\b[^>]*>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    text = htmllib.unescape(body + "\n" + "\n".join(attrs))
    text = re.sub(r"[ \t　]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text)


def ctx(text, m, span=18):
    a, b = max(0, m.start() - span), min(len(text), m.end() + span)
    return text[a:b].replace("\n", " ")


def main():
    if not BUILT.is_file():
        sys.exit("先运行 python3 tools/build.py")
    doc = BUILT.read_text(encoding="utf-8")
    text = visible_text(doc)
    flat = text.replace("\n", " ")

    # ---------- 1. 出现即不通过 ----------
    banned = {
        "旧门店数（应为 31 家已开业、合计 56 家）": r"(?<!\d)(29|30|54) ?家",
        "旧测试与内部数字": r"64 ?%|480 ?分钟|174 ?分钟|498 ?条|1,890|413 ?条|4,000 ?间|2\.4 ?万",
        "旧定价": r"RM ?199|免费|抽成|测试期|试用期|限时|折扣|优惠",
        "错误缩写（只能写 A2A、MCP）": r"H2A|A2E|MCT",
        "点名渠道（客户版不点名可接渠道）": r"Agoda|Booking|Trip\.com|Traveloka|Expedia|Airbnb|携程|美团|飞猪|抖音|去哪儿",
        "市场数据与同行": r"D-EDGE|Cloudbeds|SiteMinder|Lighthouse|Softinn|ZUZU|RoomPriceGenie|Phocuswright|83 ?%|17 ?[–-] ?20 ?%|RM ?60|2,900",
        "投资人叙事": r"投资人|融资|三关|送样|敲门砖|打样|做标杆|放量|第一站|试验场",
        "路线图与时间承诺": r"2027|年底|下旬|一季度|即将上线|很快上线|Beta|内测",
        "可识别的门店或个人信息": r"团结湖|六道口|WhatsApp|微信|\+?60 ?1\d[ -]?\d{3}",
        "越界的状态说法": r"已上线|已接通所有|全部平台都|全渠道覆盖|即开即订(?!)|已跑通|全链路",
        "国内叫法（客户版用“酒店团队/经理”）": r"店长|夜审|钉钉",
        "截图日期写错（截图是 2026-11-12）": r"2026-11-22",
        "外部客户或付费客户数量": r"\d+ ?家(酒店)?(客户|在用|已接入|合作酒店)|客户案例|付费客户 ?\d",
    }
    for name, pat in banned.items():
        for m in re.finditer(pat, flat):
            fail(f"禁用内容 · {name}：…{ctx(flat, m)}…")

    # ---------- 2. 必须带否定或限定 ----------
    NEG = r"(不|非|没有|不是|不等于|不做|不给|不说|不默认|不承诺|不谈|不代表|并非|不含|不证明|≠)"

    def need_negation(label, pat, window=14):
        for m in re.finditer(pat, flat):
            before = flat[max(0, m.start() - window):m.start()]
            if not re.search(NEG, before):
                fail(f"需带否定 · {label}：…{ctx(flat, m)}…")

    need_negation("自动执行类说法", r"自动(改价|调价|执行|发布|回复|生效)|一键(改价|发布)|无人值守|全自动")
    need_negation("保证类说法", r"保证|承诺|确保(增收|排名|订单)")
    need_negation("增收类说法", r"增收|多赚|提升 ?\d+ ?%|回本")
    need_negation("利润", r"利润")
    need_negation("接通类说法", r"已经?(为您的酒店)?(接通|连接|接入)|已经?(为您的酒店)?开通(?!权限)|已连接|已支持|已覆盖")

    for m in re.finditer(r"200\+", flat):
        around = flat[max(0, m.start() - 40):m.end() + 40]
        if not re.search(r"计划", around):
            fail(f"200+ OTA 只能作为计划出现：…{ctx(flat, m, 30)}…")
    for m in re.finditer(r"实时", flat):
        around = flat[max(0, m.start() - 30):m.end() + 60]
        if not re.search(r"未上线|需求|还没有|还没上线|不能使用|不验证", around):
            fail(f"“实时”只能出现在未上线的收益报表语境里：…{ctx(flat, m, 30)}…")
    for m in re.finditer(r"(?<!\d)56(?!\d)", flat):
        around = flat[m.start():m.end() + 26]
        if "包含已开业、已签约及筹建中" not in around:
            fail(f"56 必须紧跟“（包含已开业、已签约及筹建中）”：…{ctx(flat, m, 26)}…")
    for m in re.finditer(r"门店", flat):
        around = flat[max(0, m.start() - 24):m.end() + 24]
        if not re.search(r"不证明马来西亚门店|门店筛选", around):
            fail(f"客户的地方请写“酒店”，不要写“门店”：…{ctx(flat, m)}…")

    # 价格：静态文字里只允许三个月费数字
    amounts = set(re.findall(r"RM ?([\d,]+(?:\.\d+)?)", flat))
    extra = amounts - {"699", "2,499", "9,980"}
    if extra:
        fail("出现了三档月费以外的 RM 金额：" + ", ".join(sorted(extra)))

    # ---------- 3. 必备内容 ----------
    required = [
        "面向酒店的 AI 运营产品",
        "不是保证增收的工具",
        "31 家已开业",
        "合计 56 家（包含已开业、已签约及筹建中）",
        "INTENT COMPUTING PTE. LTD.",
        "hi@intent-computing.com",
        "hogentx.com",
        "每家酒店",
        "基础运营工具（如调价建议、点评回复草稿、质检整改、经营报表）",
        "酒店自行决策和执行",
        "专人协助配置和运营指导",
        "酒店团队负责日常运营与执行",
        "专人接管双方约定的线上 OTA 运营",
        "约定渠道、已开通权限及批准的操作范围",
        "面向符合条件的合作酒店",
        "不承诺排名、曝光或订单量",
        "A2A",
        "MCP",
        "200+ OTA 是渠道拓展计划",
        "独立、实时的收益报表",
        "按日看未来预计收益",
        "划线价（展示原价，不是成交价）",
        "建议不等于自动执行",
        "不是默认自动发布",
        "数据取自哪里",
        "谁能动价格、谁能发布内容",
        "出了问题谁来处理",
        "由双方另",
        "English",
        "Bahasa Melayu",
        "专人不代运营、不代改价",
        "从专人陪跑方案（RM 2,499）起包含",
        "三个方案都含",
        "不含 AI 浏览器",
    ]
    for r in required:
        if r not in flat:
            fail(f"缺少必备内容：{r}")
    for price in ("699", "2,499", "9,980"):
        if price not in amounts and not re.search(r"RM\s*" + re.escape(price), flat):
            fail(f"缺少月费 RM {price}")

    shots = {
        "出租率监测": ("原界面可配置预订进度偏高或偏低的提醒规则。", "第 4 页"),
        "小时级订房监测": ("原界面可配置小时级变化的监测规则。", "第 7 页"),
        "房态与开售核对": ("原界面展示房态差异巡检、数据来源及触发设置。", "第 10 页"),
        "调价安全边界": ("原界面展示房型调价范围设置；保护区间并非真实报价。", "第 19 页"),
        "质检工作台": ("原界面展示质检任务和整改管理入口。", "第 23 页"),
        "早安简报": ("原界面展示每日经营信号和待处理任务。", "第 25 页"),
    }
    scope = "用于理解产品界面，不证明马来西亚门店当前接入或实际运营结果。"
    figures = re.findall(r"<figure\b.*?</figure>", doc, flags=re.S)
    for title, (desc, page) in shots.items():
        hit = [f for f in figures if f"<b>{title}</b>" in f]
        if not hit:
            fail(f"截图缺失或标题不符：{title}")
            continue
        f = re.sub(r"<[^>]+>", "", hit[0])
        for need in (desc, "历史实拍，已脱敏。" + scope, "来源：2026-11-12 产品进展汇报，" + page):
            if need not in f:
                fail(f"截图「{title}」旁缺少标注：{need}")
    static = re.sub(r"<(style|script)\b.*?</\1>", "", doc, flags=re.S)
    if scope and len(re.findall(re.escape(scope), re.sub(r"<[^>]+>", "", static))) < 6:
        fail("六张截图应各自带一句验证范围")

    # ---------- 结构：标签成对，<main> 下只有幻灯片 ----------
    from html.parser import HTMLParser

    VOID = {"meta", "link", "img", "input", "br", "hr", "use", "circle", "path", "source"}

    class Tree(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.errors, self.main_children = [], [], []

        def handle_starttag(self, tag, attrs):
            if self.stack and self.stack[-1][0] == "main":
                self.main_children.append((tag, dict(attrs).get("class") or ""))
            if tag not in VOID:
                self.stack.append((tag, self.getpos()[0]))

        def handle_startendtag(self, tag, attrs):
            if self.stack and self.stack[-1][0] == "main":
                self.main_children.append((tag, dict(attrs).get("class") or ""))

        def handle_endtag(self, tag):
            if tag in VOID:
                return
            if not self.stack or self.stack[-1][0] != tag:
                self.errors.append(f"第 {self.getpos()[0]} 行 </{tag}> 与未闭合的 <{self.stack[-1][0] if self.stack else '无'}> 不匹配")
                names = [x[0] for x in self.stack]
                if tag in names:
                    while self.stack and self.stack[-1][0] != tag:
                        self.stack.pop()
                    self.stack.pop()
            else:
                self.stack.pop()

    tree = Tree()
    tree.feed(re.sub(r"<(style|script)\b.*?</\1>", "", doc, flags=re.S))
    for e in tree.errors[:5]:
        fail("标签不成对：" + e)
    if tree.stack:
        fail("有未闭合的标签：" + ", ".join(x[0] for x in tree.stack[:5]))
    stray = [c for c in tree.main_children if c[0] != "section" or "slide" not in c[1].split()]
    if stray:
        fail("<main> 下出现了幻灯片以外的内容：" + ", ".join(f"<{c[0]} class='{c[1]}'>" for c in stray[:5]))
    slide_n = len([c for c in tree.main_children if c[0] == "section"])
    notes.append(f"共 {slide_n} 页。")

    # ---------- 4. 成品文件本身 ----------
    # 结尾页的邮箱和网址是读者自己点的链接，不算外部引用
    probe = doc
    for ok in ("mailto:hi@intent-computing.com", "https://hogentx.com"):
        probe = probe.replace(ok, "")
    if re.search(r"https?://", probe):
        fail("成品文件里有外部网址")
    if "<!--" in doc:
        fail("成品文件里有注释")
    if re.search(r'(?:src|href)="(?!data:|#|")[^"]*"', probe):
        fail("成品文件里有未内嵌的引用")
    if 'lang="zh-CN"' not in doc:
        fail("缺少 lang=\"zh-CN\"")
    size_mb = BUILT.stat().st_size / 1024 / 1024
    notes.append(f"成品大小 {size_mb:.2f} MB；可见文字约 {len(re.sub(r'\\s', '', text))} 字；截图 {len(figures)} 张。")

    if problems:
        print(f"未通过：{len(problems)} 处")
        for p in problems:
            print("  ✗ " + p)
        for n in notes:
            print("  · " + n)
        sys.exit(1)
    print("通过：未发现禁用内容，必备内容齐全，成品文件无外部引用。")
    for n in notes:
        print("  · " + n)


if __name__ == "__main__":
    main()
