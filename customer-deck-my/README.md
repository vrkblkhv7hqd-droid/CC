# HogentX · 给马来西亚酒店老板的 20 分钟汇报

一句话：**每一间房，每一晚，只能卖一次。** HogentX 帮酒店把这一次卖好：不漏卖、卖对价、算得清。

这一版是给老板看的成交稿：先用马来西亚的官方数据讲清“为什么是现在”，再让老板用自己酒店的数字算一笔，然后讲 HogentX 怎么补、我们是谁、三个方案，最后只请老板定一件事：先从哪家酒店开始。共 17 页：正文 13 页（计划 19 分 30 秒），附页 4 页。页面里可以切换 **中文 / English / Bahasa Melayu**。

## 文件

| 文件 | 用途 |
|---|---|
| `HogentX-Malaysia-Hotel-Briefing.html` | **交付文件，打开默认中文**。单个文件，图片、字体、样式、脚本全部内嵌，断网可用 |
| `HogentX-Malaysia-Hotel-Briefing-EN.html` | 同一份内容，打开默认 English |
| `HogentX-Malaysia-Hotel-Briefing-BM.html` | 同一份内容，打开默认 Bahasa Melayu |
| `HogentX-Malaysia-Hotel-Briefing.pdf`、`-EN.pdf`、`-BM.pdf` | 三种语言的 PDF 备用稿，每页 1920×1080 |
| `src/` | 源文件（`deck.html` 中文内容、`deck.css` 样式、`deck.js` 交互） |
| `i18n/strings.json` | 英文、马来文译文，和中文一一对应 |
| `assets/` | 6 张产品截图、字标、内嵌字体 |
| `tools/` | 生成与检查脚本，见“修改与重新生成” |

三份 HTML 都能在页面里切换三种语言，区别只是打开时先显示哪一种。有些手机上的文件预览不运行脚本，那时只能看到文件默认的那种语言，所以发给客户时按对方的语言选文件。

## 现场怎么用

用 Chrome、Edge 或 Safari 打开 HTML，有鼠标的宽屏会自动进入 16:9 翻页。

| 操作 | 按键 |
|---|---|
| 下一步 / 上一步（有分步的页面先一条一条出现，再翻页） | → ←、PageDown / PageUp、空格；翻页笔可用；触屏左右滑 |
| 第一页 / 最后一页 | Home / End |
| 目录（跳到任意一页，包括附页） | M |
| 计时：已用时间 / 讲完这一页的计划时间；落后 30 秒以上变色；点一下归零 | T |
| 黑屏（想让大家看人、不看屏幕时用），再按任意键恢复 | B 或句号 |
| 切换语言（中文 → English → Bahasa Melayu） | L，或控制条上的“中 / EN / BM” |
| 全屏 | F |
| 放大截图 | 点击截图；Esc 关闭 |
| 直达某页 | 网址末尾加 `#12` 或 `#plans`；加 `?lang=en` 或 `?lang=ms` 指定语言 |

鼠标动一下，右下方出现控制条（翻页、目录、全屏、语言、存为 PDF、阅读模式），几秒后自动隐藏；鼠标停住 3 秒，光标也会隐藏。投屏时会请求屏幕常亮。

**两处现场要填的地方**（内容不保存，刷新即清空；切换语言不会清掉）：

- 第 4 页“算一笔”：房间数、平均房价、入住率。先填的是全马平均水平（65 间、RM 231.3、51.2%），**请当场改成这位老板的数字**。后面方案页的“月费 ≈ 每月几个房晚”和“每月约有多少房晚空着”会跟着变。
- 第 13 页：先从哪家酒店开始、在用哪些 OTA。要留底就点控制条的“存为 PDF”。

**会后发给客户**：发对应语言的 HTML。手机上自动变成竖向阅读，所有内容直接可见，顶栏可以换语言。

## 20 分钟怎么讲

| 页 | 计划用时 | 标题 | 这一页只讲一件事 |
|---|---|---|---|
| 1 | 0:30 | 每一间房，每一晚，只能卖一次 | 开场就说：20 分钟，最后只请您定一件事 |
| 2 | 1:30 | 2026 年上半年，全马酒店入住率和房价都在降 | 三个官方数字一个一个出：51.2%、RM 231、−7.6%。结论：市场不帮忙，更不能自己漏 |
| 3 | 1:30 | 同一家酒店，钱常漏在三个地方 | 有房没在卖、价格没跟上、到手没算清；每一条配一个数 |
| 4 | 2:00 | 按您的酒店，算一笔 | 把数字换成老板自己的。入住率多 1 个百分点、每个房晚多卖 RM 5，各是多少钱 |
| 5 | 1:30 | HogentX：替您盯着这三笔账 | 四步：接上 OTA → 盯数据 → 给建议 → 您确认后执行。已支持的五个 OTA |
| 6 | 1:30 | 有房，就要在卖 | 住小叮实测：一次核对，1,890 条里 498 条有房却没开售 |
| 7 | 1:30 | 订得快，提价；订得慢，早动手 | 看见、建议、您说了算。行业研究：试点里每间可售房收入 +11.8% |
| 8 | 1:30 | 收了多少、到手多少 | RM 100 的房费到手 RM 80–83。现在有经营报表；实时收益报表、按日预计收益即将上线 |
| 9 | 1:30 | 6 项日常工作，每周用时少了 64% | 住小叮实测：480 分钟降到 174 分钟。每天早上一页简报，四位数字员工 |
| 10 | 1:30 | 守住口碑，让 AI 也找得到您 | 回复点评与评分、房价的关系；53% 的亚洲旅客用 AI 规划行程 |
| 11 | 1:00 | 我们自己就开酒店 | 住小叮 31 家已开业；产品先在自己的酒店里用 |
| 12 | 2:30 | 三个方案 | 主推专人陪跑 RM 2,499。月费 ≈ 每月 11 个房晚的房费，而这家酒店每月约有 965 个房晚空着（数字跟着第 4 页变） |
| 13 | 1:30 | 今天只定一件事 | 选一家酒店。我们接通账号后，先把这家酒店在各平台的开售状态核对一遍 |
| 14–17 | 备用 | 附页 | 产品界面实拍、谁来做谁说了算、效果怎么量、数据来源 |

正文合计 19 分 30 秒，留 30 秒机动。按 T 可以看到自己比计划快还是慢。

## 数据来源

页面上每一个百分比和金额都在 `tools/check.py` 的名单里；名单外的数字会让检查不通过。新增数字请先核实出处，再加进名单和下表。

### 行业数据

| 页 | 页面上的数字 | 出处 | 原文或算法 |
|---|---|---|---|
| 2 | 平均入住率 51.2%，去年同期 54.1% | Tourism Malaysia，Paid Accommodation Survey Performance，January–June 2026，第 1 页 | “Average Occupancy Rate, January – June 2026：2026 – 51.2%；2025 – 54.1%” |
| 2 | 平均房价 RM 231.3，去年同期 RM 236.8 | 同上，第 2 页 | “Average Room Rate：2026 – RM231.3；2025 – RM236.8” |
| 2 | 每间可售房的房费收入 −7.6%（RM 118 对 RM 128） | **计算值** | 51.2% × 231.3 ＝ 118.4；54.1% × 236.8 ＝ 128.1；118.4 ÷ 128.1 − 1 ＝ −7.6%。Tourism Malaysia 没有公布这个数，页面上写了“按入住率 × 平均房价计算” |
| 2 | 5,380 家酒店、350,069 间客房 | 同上，第 1 页 | “Hotels 5,380；Rooms 350,069” |
| 3、8 | 标准/经济型酒店 OTA 佣金 17–20%，通常没得谈；大型连锁 10–18% | 马来西亚竞争委员会（MyCC），Market Review on the Digital Economy Ecosystem under the Competition Act 2010，Book 4: Online Travel Agencies，2026，第 121–122 页，Table 20 | “commission rates for budget hotels are usually non-negotiable, ranging from 17% to 20%”。表格来源注明是与业界访谈及 MyCC 分析 |
| 3 | 40% 的受访者遇到过想订的日期或房型没房；平台常显示已满而酒店还有房 | 同上，第 164–165 页，Figure 56 | “Limited inventory visibility is an issue for 40% of survey respondents. Often, OTA platforms show full occupancy even when rooms may still be available directly through hotels or other channels”。消费者调查 262 人，2025 年 6 月 |
| 3 | 只做少量调价的酒店，每间可售房收入低约 3% | Abrate、Nicolau、Viglia，The impact of dynamic price variability on revenue maximization，Tourism Management 74，2019，224–233 | 把价格变动幅度从第一四分位提高到第三四分位，RevPAR 高 3.07%。17 个欧洲城市 840 家酒店，2016 年 4 月的数据 |
| 4 | 默认 65 间房 | **计算值** | 350,069 ÷ 5,380 ＝ 65.07 |
| 5 | 92%、89% 的马来西亚受访者用过 Agoda、Booking.com | MyCC，同上，第 161–162 页，Figure 53 | 问卷只列了四个平台供选择 |
| 5 | 中国游客 2026 年 1–9 月 +14.1%，352 万人次 | Tourism Malaysia，Malaysia Visitor Arrival Performance，January–September 2026 | Tourist Arrivals（过夜游客）：China 3,520,218，+14.1%。前六大客源里只有中国在增长 |
| 7 | 实地试点，每间可售房收入 +11.8% | Chen、Xu、Yu、Zhang，A reinforcement learning approach for hotel revenue management with evidence from field experiments，Journal of Operations Management 69(7)，2023，1176–1201 | 摘要：在一家经济型连锁酒店试点，用合成控制法评估，“improves … revenue per available room—by 11.80%” |
| 8 | 用虚拟卡结算另有约 2–3% 手续费 | MyCC，同上，第 135 页 | “this method incurs transaction fees (~2-3%) from external payment providers that the property must bear” |
| 10 | 开始回复点评的酒店，评分平均 +0.12 星 | Proserpio、Zervas，Online reputation management，Marketing Science 36(5)，2017，645–665 | 摘要：“a 0.12-star increase in ratings and a 12% increase in review volume for responding hotels”。美国得克萨斯州酒店的 TripAdvisor 数据 |
| 10 | 评分每高 1 分（5 分制），同样的入住率可以多卖 11.2% 的价 | Anderson，The Impact of Social Media on Lodging Performance，Cornell Hospitality Report 12(15)，2012 | “the hotel can increase its price by 11.2 percent and still maintain the same occupancy or market share”。美国数据 |
| 10 | 53% 的亚洲旅客用 AI 规划行程，一年前 33%；11 个市场含马来西亚 | Agoda，2027 Asia Travel Pulse，新加坡，2026-11-23 发布 | “more than half (53%) of surveyed Asian travelers now use AI to plan their trips, up from 33% last year”。3,395 人，2026 年 9–10 月 |

网址（页面本身不带任何外部链接，这里留给核对的人）：

- Tourism Malaysia 住宿调查：`https://data.tourism.gov.my/frontend/pdf/2026/hotel_survey/paid_accommodation/infografik_hotel%20_q2_2026_(v5).pdf`
- Tourism Malaysia 访客人次：`https://data.tourism.gov.my/frontend/pdf/2026/infographics/Infographic_Visitor_Performance_Jan-Sept_2026.pdf`
- MyCC 报告：`https://www.mycc.gov.my/sites/default/files/pdf/newsroom/MyCC_Non-confidential%20Report%20Book%204%20-%20Online%20travel%20agencies%20%28OTAs%29.pdf`
- Abrate 等：`https://doi.org/10.1016/j.tourman.2019.03.013`
- Chen 等：`https://doi.org/10.1002/joom.1246`
- Proserpio、Zervas：`https://doi.org/10.1287/mksc.2017.1043`
- Anderson：`https://hdl.handle.net/1813/71194`
- Agoda：`https://www.prnewswire.com/apac/news-releases/agoda-2027-asia-travel-pulse-53-of-asian-travelers-plan-with-ai-but-89-want-the-final-say-on-hotel-bookings-302948023.html`

### 住小叮实测

| 页 | 页面上的数字 | 口径 |
|---|---|---|
| 6 | 1,890 条记录里 498 条有房却没开售 | 一家酒店、一次核对（2026 年 11 月）：未来 90 天 × 3 个平台。一条记录＝一个房型某一天在一个平台上的状态 |
| 9 | 6 项日常工作每周用时 −64%，480 分钟降到 174 分钟 | 内部计时（2026 年 11 月），按一位经理管两家酒店统计。六项：房态与开售核对 120→30、周边同类酒店监控 120→60、入住率监测 60→30、每小时订房监测 60→30、调价 60→12、划线价核对 60→12 |
| 11 | 31 家已开业；合计 56 家（包含已开业、已签约及筹建中） | 2026-11-22 的事实表。56 已经包含 31 |

### 讲的时候要知道的口径

- **入住率用的是 Tourism Malaysia 这一个口径**（抽样调查，10 间房以上的酒店）。统计局和酒店协会的数字口径不同、水平更高，比如媒体引述统计局的数字：2026 年一季度三星级酒店入住率 70.4%（这个数我们只看到了新闻报道，没有读到统计局原文）。老板如果说“我们没这么低”，回到第 4 页用他自己的数字算。
- **行业研究讲的是行业，不是 HogentX 的成绩**。+11.8% 是一家经济型连锁酒店的试点，3% 来自欧洲城市酒店，评分与房价的关系来自美国。页面上都标了“行业研究”和出处，口头也请这样讲。
- **53% 说的是用 AI 规划行程，不是用 AI 订房**。同一份调查里，愿意让 AI 直接下单的只有 7%。所以页面写的是“让 AI 也找得到您”。
- MyCC 的佣金区间来自访谈和座谈，消费者调查样本是 262 人。
- 调研时查到、但没有采用的数据：厂商自己的问卷（比如多少酒店手工调价）、协会负责人的口头估计、2023 年以前的佣金说法。

## 这一版的写法

按最新的要求改了五件事：

1. **讲收益，不讲免责**。页面上没有“不承诺”“不包含”“未上线”这类说法，`check.py` 会拦住。
2. **即将上线的功能写“即将上线”**：实时收益报表、按日看未来预计收益。它们旁边是“现在就有”的经营报表与早安简报。
3. **点名已支持的 OTA**：Agoda、Booking.com、携程、美团、飞猪。“200+ OTA”只作为目标出现。
4. **主推专人陪跑（RM 2,499）**，方案页上标了“推荐”。
5. **数字都有出处**：行业数字标来源，自己酒店的数字标“住小叮实测”，示意图标“示意”。

事实表里的几个前提，改成了正面的写法，意思没有变：

| 事实表的说法 | 页面上的写法 |
|---|---|
| 调价建议不是自动执行 | “最低价、最高价、单次涨跌幅由您设定，确认后才执行”“改不改价，您说了算” |
| ChatGPT 预订面向符合条件的合作酒店，按实际接入情况 | “专人按您酒店的情况配置和接入” |
| OTA 全托管只按约定渠道和权限，酒店仍负责线下和财务 | “专人按约定的渠道和权限，接管线上 OTA 运营”“线上交给专人，您专心管好店里” |
| 点评回复不是默认自动发布 | “团队改一改就能发”；附页写“先出草稿，由人审核后发布” |
| AI 浏览器、AI 获客从专人陪跑起包含 | 方案页只在专人陪跑和 OTA 全托管两栏列出 |

没有写的内容：任何增收、省时的保证；“已上线”“自动改价”“一键发布”；外部客户数量；旧门店数、旧定价；可识别的酒店名和个人信息。

## 客户很可能会问的问题

页面上没有编答案，建议会前准备口头说法：

1. 我在用的 OTA 里，哪些现在就能接？各自只能看，还是也能改价、回复点评？
2. 实时收益报表、按日预计收益，什么时候能用？
3. 要不要接酒店管理系统（PMS）？从授权到能用要多久？授权能不能随时收回？
4. 数据存在哪里、谁能看、会不会接触住客资料？
5. 合约期多长、含不含税、怎么付款、中途能不能停？
6. ChatGPT 预订具体怎么接？客人下单、付款走哪条路？
7. 马来西亚现在有没有客户、有没有本地团队？住小叮的酒店在哪里？
8. OTA 全托管具体做哪些动作？
9. 住小叮的两个实测数，在马来西亚的酒店也会这样吗？（实话：这是我们自己酒店的记录，所以第 13 页的第一步就是先核对您这家酒店）

## 英文、马来文

- 译文在 `i18n/strings.json`。中文是唯一的内容来源：改了中文，对应的译文要一起改，否则 `build.py` 会报缺翻译。
- 方案和模块的译名：工具授权 = Tool Licence / Lesen Alat；专人陪跑 = Specialist Coaching / Bimbingan Pakar；OTA 全托管 = Full OTA Management / Pengurusan Penuh OTA；AI 浏览器 = AI Browser / Pelayar AI；AI 获客 = AI Guest Acquisition / Pemerolehan Tetamu AI；早安简报 = Morning Brief / Taklimat Pagi。“住小叮”保留中文原名。
- 英文、马来文句子比中文长，这两种语言在投屏时正文小一号，部分句子比中文更简短；房态示意表里的状态只显示图标，文字放在图例里。
- **马来文和英文都建议请母语同事通读一遍再对外使用**。脚本只核对了数字、标记和标点，不能代替母语校对。

## 修改与重新生成

改中文只动 `src/deck.html`，改译文只动 `i18n/strings.json`，然后在本目录依次运行：

```bash
python3 tools/build.py
```

```bash
python3 tools/check.py
```

```bash
node tools/selftest.js
```

```bash
node tools/export-pdf.js
```

- `build.py`：把源文件合成三份单文件 HTML，确认没有外部引用、没有缺翻译。改稿途中可以加 `--draft` 先看版面。
- `i18n.py`：`python3 tools/i18n.py missing` 列出还没翻译的文字；`list` 列出全部对照。图表里的文字也在翻译范围内。
- `check.py`：口径自检。数字白名单、不该出现的说法、必备内容、数据来源是否齐全；英文、马来文的数字是否和中文一致、有没有残留中文。
- `selftest.js`：功能自测 85 项（翻页与分步出现、目录、算一笔、计时与黑屏、三语切换、放大截图、三种语言逐页版面、手机阅读、关闭脚本、打印排版），需要 Playwright。
- `export-pdf.js`：导出三种语言的 PDF，需要 Playwright 和本机中文字体。
- 每页的计划用时写在 `src/deck.html` 各页的 `data-sec` 上（单位秒），合计应为 1170。
- 要让某句话只在手机阅读时出现，在它的标签上加 `class="only-read"`；只在投屏时出现用 `only-present`。分步出现用 `data-step="1"`、`data-step="2"`。

## 已知限制

- 只在 Chromium 里做了自动测试；Safari、Firefox 和真机没有实测。会前请用现场要用的电脑、浏览器和翻页笔过一遍。
- 现场填写的内容不保存。要留底请用“存为 PDF”或截图。
- 截图是中文界面，三种语言的版本用的是同一张图。

## 字体

中文使用系统黑体（苹方、微软雅黑、思源黑体），只用常规和加粗两个字重。西文和数字内嵌了 Inter 的子集（SIL Open Font License 1.1）。
