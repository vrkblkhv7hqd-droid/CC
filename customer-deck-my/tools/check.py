#!/usr/bin/env python3
"""口径自检：改完文字后跑一遍，确认上页的数字都有出处、说法没有越界、三种语言没有走样。

用法（在 customer-deck-my 目录下）：
    python3 tools/build.py && python3 tools/check.py

这一版是给酒店老板看的成交稿，检查四件事：
  1. 不该出现的内容：占位符、旧数字、旧定价、保证类说法、把“即将上线”写成已有、
     “我们不承诺 / 不包含”这类防御性说法、可识别的门店或个人信息。
  2. 数字白名单：页面上每一个百分比和每一个 RM 金额都必须在名单里（名单对应 README 的“数据来源”）。
     新增数字要先核实出处，再加进名单。
  3. 必备内容：三档月费、31 / 56 的写法、住小叮实测的标注、数据来源、联系方式等。
  4. 英文、马来文：数字与中文一致、标记成对、没有残留中文、没有保证类说法。
另外确认三份成品文件没有外部引用、没有注释。
"""
import html as htmllib
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASENAME = "HogentX-Malaysia-Hotel-Briefing"
BUILT = {"zh": ROOT / f"{BASENAME}.html", "en": ROOT / f"{BASENAME}-EN.html", "ms": ROOT / f"{BASENAME}-BM.html"}

SLIDE_IDS = ["cover", "shift", "leaks", "math", "what", "avail", "price", "net", "daily", "grow", "us", "plans", "start",
             "screens", "who", "measure", "sources"]
TALK_SECONDS = 1170  # 正文 13 页的计划用时合计：19 分 30 秒

# 页面上允许出现的百分比（去掉 % 后的写法）和 RM 金额。每一个都能在 README「数据来源」里找到出处。
PERCENT_OK = {
    "51.2", "54.1", "7.6",            # Tourism Malaysia：入住率；每间可售房的房费收入（计算值）
    "40", "17–20", "10–18", "92", "89", "2–3",  # MyCC
    "3",                               # Abrate 等，Tourism Management 2019
    "11.8",                            # Chen 等，Journal of Operations Management 2023
    "11.2",                            # Anderson，Cornell Hospitality Report 2012
    "53", "33",                        # Agoda，2027 Asia Travel Pulse
    "14.1",                            # Tourism Malaysia：中国游客
    "64",                              # 住小叮实测
    "80", "55", "100", "50", "1",      # 示意图里的刻度与标注、算式里的 1%
}
RM_OK = {
    "699", "2,499", "9,980",           # 三档月费
    "231", "231.3", "236.8", "118", "128",  # Tourism Malaysia：平均房价；每间可售房的房费收入（计算值）
    "100", "80–83", "17–20",           # RM 100 的房费怎么分（MyCC 佣金区间）
    "5", "15", "120–180",              # 算一笔里的“多卖 RM 5”、示意的调价建议
}
# 译文里允许出现、中文里没有的数字：单位换算（352 万 = 3.52 million）
EXTRA_NUM_OK = {"3.52"}

problems, notes = [], []


def fail(msg):
    problems.append(msg)


def visible_text(doc: str) -> str:
    body = re.sub(r"<style\b.*?</style>", " ", doc, flags=re.S)
    body = re.sub(r"<script\b.*?</script>", " ", body, flags=re.S)
    attrs = re.findall(r'\b(?:alt|aria-label|title|placeholder|data-title|content)="([^"]*)"', body)
    body = re.sub(r'="data:[^"]*"', '=""', body)
    body = re.sub(r"<(br|/p|/li|/h[1-6]|/div|/tr|/td|/th|/dd|/dt|/section|/article|/figcaption|/span|/button|/label|/text|/title|/desc)\b[^>]*>", "\n", body)
    body = re.sub(r"<[^>]+>", "", body)
    text = htmllib.unescape(body + "\n" + "\n".join(attrs))
    text = re.sub(r"[ \t　]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n", text)


def ctx(text, m, span=18):
    a, b = max(0, m.start() - span), min(len(text), m.end() + span)
    return text[a:b].replace("\n", " ")


def slides_of(doc: str):
    """返回 {id: 该页 HTML}。"""
    out = {}
    for m in re.finditer(r'<section class="slide[^"]*" id="([^"]+)"[^>]*>.*?</section>', doc, flags=re.S):
        out[m.group(1)] = m.group(0)
    return out


def check_numbers(flat: str, where: str):
    for m in re.finditer(r"(\d[\d.,]*(?:–\d[\d.,]*)?) ?%", flat):
        v = m.group(1).rstrip(".,")
        if v not in PERCENT_OK:
            fail(f"{where} 出现了名单外的百分比 {v}%：…{ctx(flat, m)}…")
    for m in re.finditer(r"RM ?(\d[\d.,]*(?:–\d[\d.,]*)?)", flat):
        v = m.group(1).rstrip(".,")
        if v not in RM_OK:
            fail(f"{where} 出现了名单外的金额 RM {v}：…{ctx(flat, m)}…")


def check_structure(doc: str):
    void = {"meta", "link", "img", "input", "br", "hr", "use", "circle", "path", "source", "line", "rect"}

    class Tree(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.stack, self.errors, self.main_children = [], [], []

        def handle_starttag(self, tag, attrs):
            if self.stack and self.stack[-1][0] == "main":
                self.main_children.append((tag, dict(attrs).get("class") or ""))
            if tag not in void:
                self.stack.append((tag, self.getpos()[0]))

        def handle_startendtag(self, tag, attrs):
            if self.stack and self.stack[-1][0] == "main":
                self.main_children.append((tag, dict(attrs).get("class") or ""))

        def handle_endtag(self, tag):
            if tag in void:
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


def check_file_itself(lang: str, doc: str):
    probe = re.sub(r'<script type="application/json" id="i18n">.*?</script>', "", doc, flags=re.S)
    for ok in ("mailto:hi@intent-computing.com", "https://hogentx.com"):
        probe = probe.replace(ok, "")
    if re.search(r"https?://", probe):
        fail(f"[{lang}] 成品文件里有外部网址")
    if "<!--" in doc:
        fail(f"[{lang}] 成品文件里有注释")
    if re.search(r'(?:src|href)="(?!data:|#|")[^"]*"', probe):
        fail(f"[{lang}] 成品文件里有未内嵌的引用")
    want = {"zh": 'lang="zh-CN"', "en": 'lang="en"', "ms": 'lang="ms"'}[lang]
    if want not in doc[:300]:
        fail(f"[{lang}] 缺少 {want}")


def check_chinese(doc: str):
    text = visible_text(doc)
    flat = text.replace("\n", " ")
    pages = slides_of(doc)

    # ---------- 1. 不该出现的内容 ----------
    banned = {
        "占位符（还没核实的内容）": r"〔待核对〕|待核对|TODO|待定|XX+",
        "旧门店数（应为 31 家已开业、合计 56 家）": r"(?<!\d)(29|30|54) ?家",
        "旧定价与促销": r"RM ?199|免费|抽成|测试期|试用期|限时|折扣|优惠",
        "错误缩写": r"H2A|A2E|MCT",
        "投资人叙事": r"投资人|融资|三关|送样|敲门砖|打样|做标杆|放量|第一站|试验场",
        "可识别的门店或个人信息": r"团结湖|六道口|WhatsApp|微信|\+?60 ?1\d[ -]?\d{3}",
        "把功能说成自动执行": r"自动(改价|调价|执行|发布|回复|生效)|一键(改价|发布|调价)|无人值守|全自动|即开即订",
        "保证类说法（既不保证，也不写“不保证”）": r"保证|承诺|确保|包赚|稳赚|回本",
        "把“即将上线”写成已有": r"已上线|已经上线|已跑通|全链路|全渠道覆盖|已接通所有",
        "防御性的负面说法（老板稿不写）": r"不包含|不含|不代表|不证明|未上线|还没上线|尚未上线|不能使用|暂不|不验证|不等同",
        "国内叫法（写“酒店”“经理”）": r"门店|店长|夜审|钉钉",
        "不引用同行厂商": r"SiteMinder|Cloudbeds|D-EDGE|Lighthouse|Softinn|ZUZU|RoomPriceGenie|STAAH",
        "外部客户数量": r"\d+ ?家(酒店)?(客户|在用|已接入|合作酒店)|客户案例|付费客户 ?\d",
    }
    for name, pat in banned.items():
        for m in re.finditer(pat, flat):
            fail(f"不该出现 · {name}：…{ctx(flat, m)}…")

    # ---------- 2. 数字白名单 ----------
    check_numbers(flat, "[zh]")

    # ---------- 3. 说法的位置 ----------
    for name in ("实时收益报表", "按日看未来预计收益"):
        hits = [m for m in re.finditer(re.escape(name), flat)]
        if not hits:
            fail(f"缺少：{name}")
        for m in hits:
            if "即将上线" not in flat[max(0, m.start() - 12):m.start()]:
                fail(f"“{name}”前面要紧跟“即将上线”的标注：…{ctx(flat, m)}…")
    for m in re.finditer(r"200\+", flat):
        if "目标" not in flat[max(0, m.start() - 12):m.start()]:
            fail(f"200+ OTA 只能作为目标出现：…{ctx(flat, m)}…")
    for m in re.finditer(r"(?<![\d,.])56(?![\d,.%])", flat):
        if "包含已开业、已签约及筹建中" not in flat[m.start():m.end() + 22]:
            fail(f"56 后面要紧跟“（包含已开业、已签约及筹建中）”：…{ctx(flat, m, 26)}…")
    for m in re.finditer(r"498|1,890|480 分钟|174 分钟|−64%", flat):
        if "住小叮" not in flat[max(0, m.start() - 160):m.end() + 160] and "每周" not in flat[max(0, m.start() - 30):m.end() + 30]:
            fail(f"住小叮的数字旁边要有“住小叮实测”：…{ctx(flat, m)}…")

    # ---------- 4. 必备内容 ----------
    required = [
        "面向酒店的 AI 运营产品", "每家酒店", "家已开业", "合计 56 家（包含已开业、已签约及筹建中）",
        "INTENT COMPUTING PTE. LTD.", "hi@intent-computing.com", "hogentx.com",
        "工具授权", "专人陪跑", "OTA 全托管", "推荐", "即将上线", "住小叮实测", "行业研究", "示意",
        "Agoda", "Booking.com", "携程", "美团", "飞猪",
        "早安简报", "四位数字员工", "数字收益、数字宾客关系、数字质检、数字总经理",
        "ChatGPT 预订", "生成酒店官网", "GEO 优化", "AI 浏览器",
        "确认后才执行", "您说了算",
        "1,890", "498", "480 分钟", "174 分钟",
        "English", "Bahasa Melayu",
    ]
    for r in required:
        if r not in flat:
            fail(f"缺少必备内容：{r}")
    for price in ("699", "2,499", "9,980"):
        if not re.search(r"RM\s*" + re.escape(price), flat):
            fail(f"缺少月费 RM {price}")
    if not re.search(r'<span class="num"[^>]*>31</span>', doc):
        fail("缺少“31 家已开业”的大数字")

    # 数据来源页：每个出处都在
    src = visible_text(pages.get("sources", ""))
    for name in ("Tourism Malaysia", "MyCC", "Tourism Management", "Journal of Operations Management", "Marketing Science",
                 "Cornell Hospitality Report", "Agoda", "住小叮内部"):
        if name not in src:
            fail(f"“数据来源”页缺少：{name}")
    # 用了行业数字的页，页脚要写来源；用了住小叮数字的页，页脚要写实测口径
    for sid, need in {"shift": "来源", "leaks": "来源", "what": "来源", "net": "来源", "grow": "来源", "price": "行业研究",
                      "avail": "住小叮实测", "daily": "住小叮实测"}.items():
        foot = re.search(r'<span class="foot-note"[^>]*>(.*?)</span>', pages.get(sid, ""), flags=re.S)
        if not foot or need not in foot.group(1):
            fail(f"第「{sid}」页的页脚缺少“{need}”说明")
    # 示意图都带“示意”标
    for sid in ("avail", "price", "daily"):
        if "tag--demo" not in pages.get(sid, ""):
            fail(f"第「{sid}」页的示意图缺少“示意”标")
    if 'class="plan plan--hero"' not in doc or "tag--hero" not in pages.get("plans", ""):
        fail("方案页缺少“推荐”的专人陪跑")

    # ---------- 5. 结构 ----------
    check_structure(doc)
    ids = list(pages)
    if ids != SLIDE_IDS:
        fail(f"页面顺序与预期不符：{ids}")
    secs = sum(int(x) for x in re.findall(r'<section class="slide[^>]*data-sec="(\d+)"', doc))
    if secs != TALK_SECONDS:
        fail(f"各页计划用时合计应为 {TALK_SECONDS} 秒，现在是 {secs} 秒")
    notes.append(f"共 {len(ids)} 页；正文 13 页计划用时 {secs // 60} 分 {secs % 60:02d} 秒；可见文字约 {len(re.sub(r'\\s', '', text))} 字。")


LANG_RULES = {
    "en": {
        "banned": {
            "old pricing or offers": r"RM ?199|\bfree\b|discount|revenue share|limited[- ]time|trial",
            "wrong abbreviations": r"H2A|A2E|MCT",
            "guarantee wording": r"guarantee|promis|ensure|payback",
            "overclaim": r"already (live|launched)|fully automatic|one[- ]click|automatically (change|publish|adjust)",
            "defensive wording": r"does not include|not included|not launched|not yet|we do not|cannot be used",
        },
        "soon": "Coming soon",
        "soon_items": ["Real-time revenue report", "Expected revenue, day by day"],
        "after_56": "including open, signed and in preparation",
        "target": "Target",
        "required": ["Tool Licence", "Specialist Coaching", "Full OTA Management", "Recommended", "Morning Brief", "Four digital staff",
                     "AI Browser", "AI Guest Acquisition", "Measured at 住小叮", "Industry research", "Illustration",
                     "INTENT COMPUTING PTE. LTD.", "hi@intent-computing.com", "hogentx.com", "only after you confirm"],
    },
    "ms": {
        "banned": {
            "harga lama atau tawaran": r"RM ?199|percuma|diskaun|masa terhad|percubaan",
            "singkatan salah": r"H2A|A2E|MCT",
            "kata jaminan": r"jamin|janji|pasti untung|pulang modal",
            "dakwaan berlebihan": r"sudah dilancarkan|automatik sepenuhnya|satu klik|secara automatik",
            "kata defensif": r"tidak termasuk|belum dilancarkan|kami tidak|tidak boleh digunakan",
        },
        "soon": "Akan datang",
        "soon_items": ["Laporan hasil masa nyata", "Hasil dijangka, hari demi hari"],
        "after_56": "termasuk yang telah dibuka, ditandatangani dan dalam persiapan",
        "target": "Sasaran",
        "required": ["Lesen Alat", "Bimbingan Pakar", "Pengurusan Penuh OTA", "Disyorkan", "Taklimat Pagi", "Empat pekerja digital",
                     "Pelayar AI", "Pemerolehan Tetamu AI", "Diukur di 住小叮", "Kajian industri", "Ilustrasi",
                     "INTENT COMPUTING PTE. LTD.", "hi@intent-computing.com", "hogentx.com", "selepas anda sahkan"],
    },
}
CJK = re.compile(r"[㐀-鿿豈-﫿]+")


def check_translations():
    strings = ROOT / "i18n" / "strings.json"
    if not strings.is_file():
        fail("缺少 i18n/strings.json")
        return
    rows = json.loads(strings.read_text(encoding="utf-8"))

    def nums(t):
        t = re.sub(r"<[^>]+>", "", t)
        return set(x.rstrip(",.") for x in re.findall(r"\d[\d,]*(?:\.\d+)?\+?", t))

    for r in rows:
        zh = r["zh"]
        for lang in ("en", "ms"):
            t = r.get(lang, "")
            where = f"[{lang}] {zh[:28]}…"
            if not t.strip():
                fail(f"缺翻译 {where}")
                continue
            extra = nums(t) - nums(zh) - {"1", "2", "3"} - EXTRA_NUM_OK
            if extra:
                fail(f"译文多出了中文里没有的数字 {sorted(extra)} {where}")
            # 中文里的关键数字（带小数、带逗号或三位以上）译文里也要有
            for k in nums(zh):
                if (len(k.replace(",", "").replace(".", "").rstrip("+")) >= 3 or "." in k) and k not in nums(t) and k not in ("352",):
                    # 年份、月份可以换成月份名；其余必须保留
                    if not re.fullmatch(r"20\d\d", k):
                        fail(f"译文漏了数字 {k} {where}")
            opens = re.findall(r"<([a-z]+)\b[^>]*>", t)
            closes = re.findall(r"</([a-z]+)>", t)
            if sorted(x for x in opens if x != "br") != sorted(closes):
                fail(f"译文里的标记不成对 {where}")
            if set(opens) - {"b", "span", "br", "a", "small", "em", "i"}:
                fail(f"译文里有不该出现的标记 {sorted(set(opens))} {where}")
            for marker in ("data-out=", "data-eq", "href=", "<em>", "<br>"):
                if zh.count(marker) != t.count(marker):
                    fail(f"译文与中文的标记数量不一致（{marker}） {where}")
            if re.search(r"[“”‘’，。；：、（）]", t):
                fail(f"译文里有全角或弯引号标点 {where}")
            left = [w for w in CJK.findall(re.sub(r"<[^>]+>", "", t)) if w.replace("住小叮", "")]
            if left:
                fail(f"译文里残留中文 {left} {where}")

    for lang, rule in LANG_RULES.items():
        f = BUILT[lang]
        if not f.is_file():
            fail(f"缺少 {f.name}，先运行 python3 tools/build.py")
            continue
        doc = f.read_text(encoding="utf-8")
        check_file_itself(lang, doc)
        static = re.sub(r'<script type="application/json" id="i18n">.*?</script>', "", doc, flags=re.S)
        static = re.sub(r"<[^>]*data-noi18n[^>]*>.*?</(?:div|span|button)>", "", static, flags=re.S)
        flat = visible_text(static).replace("\n", " ")
        for name, pat in rule["banned"].items():
            for m in re.finditer(pat, flat, flags=re.I):
                fail(f"[{lang}] 不该出现 · {name}：…{ctx(flat, m, 30)}…")
        check_numbers(flat, f"[{lang}]")
        for item in rule["soon_items"]:
            for m in re.finditer(re.escape(item), flat):
                if rule["soon"] not in flat[max(0, m.start() - 24):m.start()]:
                    fail(f"[{lang}] “{item}”前面要紧跟“{rule['soon']}”：…{ctx(flat, m, 30)}…")
            if item not in flat:
                fail(f"[{lang}] 缺少：{item}")
        for m in re.finditer(r"200\+", flat):
            if rule["target"] not in flat[max(0, m.start() - 16):m.start()]:
                fail(f"[{lang}] 200+ OTA 只能作为目标出现：…{ctx(flat, m, 30)}…")
        for m in re.finditer(r"(?<![\d,.])56(?![\d,.%])", flat):
            if rule["after_56"] not in flat[m.start():m.end() + 90]:
                fail(f"[{lang}] 56 后面要紧跟包含范围的说明：…{ctx(flat, m, 30)}…")
        for need in rule["required"]:
            if need not in flat:
                fail(f"[{lang}] 缺少必备内容：{need}")
        for price in ("699", "2,499", "9,980"):
            if price not in flat:
                fail(f"[{lang}] 缺少月费 {price}")
        left = sorted(set(w for w in CJK.findall(flat) if w.replace("住小叮", "")))
        if left:
            fail(f"[{lang}] 页面上残留中文：{left[:8]}")
    notes.append(f"英文、马来文各 {len(rows)} 条：数字、标记、标点已核对，页面上除品牌名“住小叮”外没有残留中文。")


def main():
    for lang, f in BUILT.items():
        if not f.is_file():
            sys.exit("先运行 python3 tools/build.py")
    doc = BUILT["zh"].read_text(encoding="utf-8")
    check_file_itself("zh", doc)
    check_chinese(doc)
    check_translations()
    size_mb = BUILT["zh"].stat().st_size / 1024 / 1024
    notes.append(f"成品大小 {size_mb:.2f} MB。")

    if problems:
        print(f"未通过：{len(problems)} 处")
        for p in problems:
            print("  ✗ " + p)
        for n in notes:
            print("  · " + n)
        sys.exit(1)
    print("通过：数字都在名单里、必备内容齐全、说法没有越界，三份成品文件无外部引用。")
    for n in notes:
        print("  · " + n)


if __name__ == "__main__":
    main()
