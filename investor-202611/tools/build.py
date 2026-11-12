"""把 src/ 里的样式、幻灯片和脚本拼成一个自包含的 HTML 文件（图片内嵌），并生成讲稿。

用法（在 investor-202611 目录下）：  python3 tools/build.py
产出：
  HogentX-Investor-Update-202611.html   单文件演示稿，拷到任何电脑用 Chrome 打开即可
  speaker-notes.md                      讲稿与时间分配
"""
import base64, datetime, html, mimetypes, pathlib, re

deck = pathlib.Path(__file__).resolve().parent.parent
src = deck / "src"
OUT = deck / "HogentX-Investor-Update-202611.html"
TITLE = "HogentX 进展汇报 · 2026 年 11 月"
FONTS = ("https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700"
         "&family=IBM+Plex+Mono:wght@400;500&family=Noto+Sans+SC:wght@400;500;700"
         "&family=Noto+Serif+SC:wght@600;700;900&display=swap")

style = (src / "style.css").read_text(encoding="utf-8")
slides = (src / "slides.html").read_text(encoding="utf-8")
controls = (src / "controls.html").read_text(encoding="utf-8")
script = (src / "script.js").read_text(encoding="utf-8")

# 1. 页码：正文页从 02 起顺序编号（封面不显示页码）
counter = [1]
def number(_):
    counter[0] += 1
    return f"{counter[0]:02d}"
slides = re.sub(r"\{\{n\}\}", number, slides)

# 2. 图片内嵌为 data URI，文件可以单独拷走
def inline(match):
    path = deck / match.group(1)
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f'src="data:{mime};base64,{data}"'
slides, n_img = re.subn(r'src="(assets/[^"]+)"', inline, slides)

# 3. 版本号：行内编辑的草稿只对同一版文件生效
build_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
script = script.replace("__BUILD_ID__", build_id)

page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{TITLE}</title>
<!-- 字体：Google Fonts。没有网络时退回系统中文字体，版式不变 -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="{FONTS}">
<style>
{style}
</style>
</head>
<body>
<div class="deck-viewport">
<main class="deck-stage" id="deckStage" aria-label="幻灯片">
{slides}
</main>
</div>

{controls}
<script>
{script}
</script>
</body>
</html>
"""
OUT.write_text(page, encoding="utf-8")

# 4. 讲稿
sections = re.findall(r'<section class="slide[^"]*" data-label="([^"]+)"(?: data-appendix="([^"]+)")?>(.*?)</section>', slides, re.S)
lines = ["# HogentX 进展汇报 · 讲稿", "",
         "由演示稿里的讲稿自动生成。演示时按 **N** 可以在屏幕右侧打开同样的内容；投屏时观众也看得到，正式讲的时候建议关掉，用手机看这份。", ""]
total = 0.0
body = []
main_no = 0
for label, appendix, content in sections:
    title = re.search(r"<h[12][^>]*>(.*?)</h[12]>", content, re.S)
    title = re.sub(r"<[^>]+>", "", title.group(1)).strip() if title else ""
    note = re.search(r'<aside class="notes">(.*?)</aside>', content, re.S)
    note = html.unescape(note.group(1).strip()) if note else ""
    m = re.search(r"约 ([\d.]+) (分钟|秒)", note)
    if m and not appendix:
        total += float(m.group(1)) / (60 if m.group(2) == "秒" else 1)
    if appendix:
        head = f"附录 {appendix}"
    else:
        main_no += 1
        head = f"第 {main_no} 页"
    body += [f"## {head} · {label}", "", f"**页面标题**：{title}", "", note, ""]
lines += [f"正文合计约 **{total:.0f} 分钟**，其余时间留给讨论；附录只在被问到时翻。", ""] + body
QA = """## 可能被追问的问题

不在演示稿里，只给讲的人看。答法是建议，请按实际情况调整。

1. **收入到底能提升多少？** 还在测试，结果出来第一时间同步。内部目标是 15% 左右。行业里厂商自报的数是 +19%（RoomPriceGenie，567 家）和 +21%（Lighthouse，84 家），都没有对照组，只能说明量级。
2. **一次巡检为什么有 498 条“有房却关了房”？** 按实际情况说明：哪些是有意不开售的（比如个别平台、远期日期），哪些是漏开的。重点是以前没有办法一次看全，现在可以每小时核对。
3. **截图里的 355 元、378 元是成交价吗？** 不是，是划线价。成交价是促销之后的价格。
4. **替酒店在平台后台操作，会不会被平台限制？** 现在是酒店授权账号后，在酒店本地的客户端里操作；正在对接平台和聚合商的正式接口。携程今年 3 月下线了自己的调价助手，说明自动跟价很敏感，所以我们只做“建议加人工确认”。
5. **AI 订房，Lighthouse 和 SiteMinder 都在做，凭什么是你们？** 他们服务已经有官网和订房系统的酒店；我们服务连官网都没有的小酒店，免费，当敲门砖用，不靠它赚钱。不说“首个”。
6. **ChatGPT 审核不过怎么办？** MCP 是开放协议，不只接 ChatGPT；酒店官网本身不依赖审核，照常上线。
7. **硬件为什么不用手机通知？** 目前没有数据证明专用设备更好，所以先在 3–5 家店做试点对照，看任务处理率和响应时间。
8. **不到 100 元是什么口径？** 是物料成本。每台设备每月还有语音合成等云端费用，粗算在十几元以内（估算）。
9. **硬件会对外卖吗？** 试点数据好再决定。海外每个国家都要过无线电认证，还有库存和售后，不会在现在这个阶段铺开。
10. **5 个人做得过来吗？** 主线只有一条：年底前 10 家海外酒店上线。硬件只在住小叮试点，一次只打一个国家。
11. **订阅收入的天花板在哪？** 马来西亚约 5,300 家酒店，其中三星及以下约 2,900 家；之后是新加坡和日本。订阅之外还有直订单的成交抽成。
12. **为什么不按增收分成收费？** 增收的归因说不清，小团队也难对账催款。先用固定月费，前 3 个月免费来降低酒店的顾虑。
13. **海外没有接酒店管理系统，10 项能力怎么用？** 今天能用 5 项，加官网和 AI 渠道。订房平台接口打通后 10 项都能用，因为小酒店的订单绝大部分来自订房平台。没有管理系统的酒店用我们自带的房量日历。
"""
(deck / "speaker-notes.md").write_text("\n".join(lines) + "\n" + QA, encoding="utf-8")

print(f"wrote {OUT.name}: {OUT.stat().st_size / 1e6:.2f} MB, slides {len(sections)}, images inlined {n_img}, build {build_id}, talk ≈ {total:.1f} min")
