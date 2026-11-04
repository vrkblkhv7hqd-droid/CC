# -*- coding: utf-8 -*-
"""
住小叮抖音直播方案 财务模型生成器
生成 douyin-live/model/住小叮抖音直播财务模型.xlsx
所有计算用公式，参数集中在"假设"表，蓝色为可改输入。
"""
import sys, json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.comments import Comment

FONT = "Microsoft YaHei"
F_INPUT = Font(name=FONT, color="0000FF", size=10)
F_CALC = Font(name=FONT, color="000000", size=10)
F_LINK = Font(name=FONT, color="008000", size=10)
F_LABEL = Font(name=FONT, size=10)
F_BOLD = Font(name=FONT, size=10, bold=True)
F_H1 = Font(name=FONT, size=14, bold=True)
F_H2 = Font(name=FONT, size=11, bold=True, color="FFFFFF")
F_NOTE = Font(name=FONT, size=9, color="595959", italic=True)
FILL_H2 = PatternFill("solid", fgColor="1F4E79")
FILL_KEY = PatternFill("solid", fgColor="FFFF00")
FILL_SEC = PatternFill("solid", fgColor="DDEBF7")
FILL_TOTAL = PatternFill("solid", fgColor="F2F2F2")
THIN = Side(style="thin", color="BFBFBF")
BORDER = Border(top=THIN, bottom=THIN, left=THIN, right=THIN)
ALIGN_L = Alignment(horizontal="left", vertical="center", wrap_text=True)
ALIGN_R = Alignment(horizontal="right", vertical="center")
ALIGN_C = Alignment(horizontal="center", vertical="center", wrap_text=True)

FMT_INT = '#,##0;(#,##0);-'
FMT_PCT = '0.0%;(0.0%);-'
FMT_DEC = '#,##0.00;(#,##0.00);-'
FMT_YUAN = '#,##0;(#,##0);-'

# 参数定义：key, 标签, [悲观, 基准, 乐观], 单位, 说明, 格式
PARAMS = []
def P(key, label, values, unit, note, fmt=FMT_DEC, key_cell=False):
    if not isinstance(values, (list, tuple)):
        values = [values, values, values]
    PARAMS.append(dict(key=key, label=label, values=list(values), unit=unit, note=note, fmt=fmt, key_cell=key_cell))

SECTIONS = {}
def S(title):
    PARAMS.append(dict(section=title))

# ---------------- 参数清单（占位值在研究完成后更新） ----------------
S("一、门店与系统基础（决策人提供）")
P("STORES0", "当前门店数", 30, "家", "决策人提供：北京 30 家", FMT_INT)
P("HQ_OP_SHARE", "总部代运营门店占比", 20/30, "%", "20 家代运营，10 家加盟自管；假设新店同比例", FMT_PCT)
P("NEW_PM", "月均新增门店", [2.5, 50/12, 50/12], "家/月", "决策人：12 个月北京新增约 40 家，沪深约 10 家；悲观按 30 家", FMT_DEC)
P("ROOMS", "单店房间数", 100, "间", "决策人提供", FMT_INT)
P("ADR", "平均挂牌房价", 100, "元/晚", "决策人提供", FMT_INT)
P("OCC", "平均入住率", 0.85, "%", "决策人：85% 以上，很多门店 90% 以上", FMT_PCT)
P("DAYS", "每月天数", 30, "天", "简化口径", FMT_INT)
P("OTA_SHARE", "OTA 渠道间夜占比", 0.85, "%", "假设；其余为直订或上门，不付佣金", FMT_PCT, key_cell=True)
P("OTA_COMM", "OTA 佣金率", 0.08, "%", "决策人提供：携程、美团约 8%", FMT_PCT)
P("OTA_CTRL", "OTA 平台控价比例", 0.04, "%", "决策人提供：4% 由平台控制，酒店收不到", FMT_PCT)
P("MGMT_FEE", "总部管理费率（按门店到账）", 0.035, "%", "决策人提供：3.5%；本模型按门店到账金额计提，抖音单同样计提", FMT_PCT)
P("VAR_COST", "单间夜变动成本", [12, 10, 8], "元", "假设：清洁、布草、水电、耗材；4 平米无独卫房型", FMT_DEC, key_cell=True)
P("MGR_SALARY", "店长月薪", 10000, "元/月", "决策人提供：约 1 万，记在门店损益", FMT_INT)
P("WORK_HOURS", "店长月标准工时", 176, "小时", "按 22 天 × 8 小时", FMT_INT)

S("二、抖音平台与通兑券（决策人提供 + 研究）")
P("DY_FEE", "抖音平台抽成", 0.08, "%", "决策人提供：平台 8%（含技术服务费等）", FMT_PCT)
P("HQ_TAKE", "总部分成", 0.04, "%", "决策人提供：总部 4%，门店到账 88%", FMT_PCT)
P("REDEEM", "核销率", [0.45, 0.6, 0.7], "%", "决策人估计 60%；行业参照：酒旅团购核销率不足 50%（虎嗅 2025）、国信证券估算约 30%（含达人与度假囤券）、搜索型 68% 到 75%；自播加刚需低价品类取上沿", FMT_PCT, key_cell=True)
P("BASE_REDEEM_EST", "倒推上月用的核销率", 0.6, "%", "仅用于把上月 4 万分成倒推为售出 GMV", FMT_PCT)
P("LAG0", "核销时间分布：售出当月", 0.5, "%", "假设：90 天有效期下的核销节奏", FMT_PCT)
P("LAG1", "核销时间分布：次月", 0.3, "%", "假设", FMT_PCT)
P("LAG2", "核销时间分布：第三月", 0.2, "%", "假设", FMT_PCT)
P("SOLDOUT_ANY", "不限日期券核销落在满房日的比例", [0.35, 0.30, 0.25], "%", "决策人：周末基本满房，约 9 晚/30 天；券用户偏好周末，取略高", FMT_PCT, key_cell=True)
P("SOLDOUT_WD", "工作日券核销落在满房日的比例", [0.08, 0.05, 0.03], "%", "假设：周日至周四可用，偶有满房", FMT_PCT)
P("WOULD_BOOK", "抖音买家中原本就会订本品牌的比例", [0.7, 0.5, 0.35], "%", "关键假设：替代率核心。参照：度假与高星酒店直播核销客新客占比 71% 到 80%（洲际 2026、Club Med 2025）；经济型连锁按平日核销中 50% 为真实增量（区间 40% 到 70%）推断；叠加满房日后不限日期券总体增量约 35%（区间 20% 到 55%）", FMT_PCT, key_cell=True)
P("BASE_HQ_COMM", "上月总部抖音分成（实际）", 40000, "元", "决策人提供：纯 4%，按核销结算，无投流", FMT_INT)
P("STORE_HOURS", "门店每月直播小时数", [20, 16, 12], "小时/店/月", "假设：每周 2 场 × 2 小时", FMT_INT)

S("三、通兑券定价三档")
P("P1_PRICE", "九折券价格", 90, "元", "现状：约九折", FMT_INT)
P("P1_VOL", "九折券销量系数", 1.0, "倍", "基准 = 1", FMT_DEC)
P("P1_PERK", "九折券权益成本", 0, "元/间夜", "无附加权益", FMT_DEC)
P("P2_PRICE", "平价券价格", 96, "元", "对标 OTA 实际展示价下限 96 到 100", FMT_INT)
P("P2_VOL", "平价券销量系数", [0.7, 0.85, 1.0], "倍", "关键假设。参照：Groupon 19,978 个团购的研究发现折扣每加深 1% 销量反降 0.035% 到 0.256%，评分与信任比折扣更影响销量；直播间冲动属性加大下行，取 15% 折减", FMT_DEC, key_cell=True)
P("P2_PERK", "平价券权益成本", 0, "元/间夜", "无附加权益", FMT_DEC)
P("P3_PRICE", "平价加权益券价格", 96, "元", "价格不降，加权益", FMT_INT)
P("P3_VOL", "平价加权益券销量系数", [0.8, 0.95, 1.1], "倍", "关键假设。参照：华住 19.9 元权益包售罄催补货、同业以权益替代降价的定性证据；相对平价券 +10%", FMT_DEC, key_cell=True)
P("P3_PERK", "平价加权益券权益成本", [3, 2.5, 2], "元/间夜", "假设：延迟退房（仅非满房日提供，机会成本约 0）、行李寄存、饮用水等低现金成本权益", FMT_DEC)

S("四、方案一：门店直播（现状延续 / 规范化）")
P("A_DRIFT", "现状延续：单店产出月变化率", [-0.05, -0.02, 0.0], "%/月", "假设：无总部支持时的新鲜感衰减与人员流动", FMT_PCT, key_cell=True)
P("AP_DRIFT", "规范化后：单店产出月变化率", [-0.01, 0.0, 0.01], "%/月", "假设：有督导与激励时基本稳定", FMT_PCT)
P("AP_UPLIFT", "规范化后单店产出提升倍数", [1.15, 1.3, 1.5], "倍", "关键假设：培训、SOP、激励带来的提升；研究区间见文档", FMT_DEC, key_cell=True)
P("AP_RAMP", "提升达成所需月数", [4, 3, 2], "月", "假设", FMT_INT)
P("AP_SUP_SALARY", "直播督导月薪（1 人）", [14000, 12500, 12500], "元/月", "北京抖音直播运营 56% 在 10 到 20K，1 到 3 年经验约 13.3K（职友集 2026）", FMT_INT)
P("SOCIAL", "社保公积金等综合系数", 0.42, "%", "北京 2025 年度单位社保约 26.3% + 工伤 + 公积金 5% 到 12%，法定附加约 31.5% 到 40%，加招聘培训等杂项取全口径 1.42", FMT_PCT)
P("AP_TRAIN_ONEOFF", "一次性培训与 SOP 建设", 20000, "元", "假设：外部讲师、话术库、脚本", FMT_INT)
P("AP_TRAIN_MONTHLY", "每月持续培训与巡检", 3000, "元/月", "假设", FMT_INT)
P("AP_STORE_KIT", "每店直播设备补贴", 800, "元/店", "假设：补光灯、支架、麦克风", FMT_INT)
P("AP_COMM", "开播门店或员工提成（按售出 GMV）", 0.015, "%", "约合核销 GMV 的 2.5%；行业建议员工直播提成按核销计 2% 到 5%，跨店来源奖励 1% 到 3%", FMT_PCT, key_cell=True)
P("COMM_BY_STORE", "提成由门店承担的比例", 1.0, "%", "机制设计：提成从核销门店到账中划转给开播门店或员工，总部只做清分；设 0 则由总部从 4% 分成中支付", FMT_PCT, key_cell=True)

S("五、方案二：总部直播团队（含门店赋能）")
P("B_START", "团队到位月份", 2, "第几月", "第 1 月招聘，第 2 月开播", FMT_INT)
P("B_RECRUIT", "一次性招聘费用", 10000, "元", "假设", FMT_INT)
P("B_SAL_LEAD", "直播运营负责人月薪", [15000, 13000, 13000], "元/月", "北京抖音直播运营 10 到 20K；负责人取中位略高", FMT_INT)
P("B_SAL_HOST", "主播月薪（底薪）", [10000, 8000, 8000], "元/月", "BOSS直聘北京酒旅主播标价 7,000 到 13,000；本地生活主播 6 到 11K；另有提成", FMT_INT)
P("B_SAL_CTRL", "中控兼剪辑月薪", [9000, 8000, 8000], "元/月", "北京直播中控约 9.1K，全国 73% 在 4.5 到 8K；剪辑 8 到 15K", FMT_INT)
P("B_SAL_ADS", "投手兼内容月薪", [14000, 12000, 12000], "元/月", "北京千川投手 65.9% 在 10 到 20K（2025 较 2024 +19%）；兼内容取中位", FMT_INT)
P("B_HOST_COMM", "主播提成（按总部直播间售出 GMV）", 0.012, "%", "约合核销 GMV 的 2%；行业主播提成底薪 + 核销 GMV 1% 到 5%", FMT_PCT)
P("B_EQUIP", "直播设备一次性投入", 35000, "元", "办公室绿幕方案：手机或相机、灯光、声卡、采集卡、绿幕，含税清单约 4.7 万（2025），企业进阶清单 0.85 到 1.5 万；取 3.5 万", FMT_INT)
P("B_EQUIP_MONTHS", "设备摊销月数", 12, "月", "假设", FMT_INT)
P("B_SPACE", "场地与杂费", 3000, "元/月", "假设：办公室内搭建", FMT_INT)
P("B_HOURS", "总部直播间每月开播小时", [100, 120, 140], "小时/月", "品牌自播常见要求每周 6 天、每天 5 小时以上；冷启动 1 到 2 班每班 6 小时", FMT_INT)
P("B_GPH_START", "开播首月每小时售出 GMV（九折口径）", 1000, "元/小时", "假设：冷启动期；参照某品牌测试期第 3 个月单场 6 小时产出 7,000 元后放量", FMT_INT)
P("B_GPH_MATURE", "成熟期每小时售出 GMV（九折口径）", [2500, 4000, 6000], "元/小时", "关键假设。参照：丽枫门店店总直播 8 小时近 10 万（中端，按客单价折算经济型 1/3 到 1/5 约 2,500 到 4,000/小时）；尚客优区域总部首场 2.8 万", FMT_INT, key_cell=True)
P("B_RAMP", "达到成熟所需月数", [6, 4, 3], "月", "起号 1 到 3 个月、见效 3 到 6 个月（行业经验）", FMT_INT)
P("B_ADS", "月投流预算", [20000, 30000, 50000], "元/月", "本地生活经验：投流占支付 GMV 10% 到 20%；冷启动 0.5 到 2 万/月", FMT_INT)
P("B_ROI", "投流 ROI（售出 GMV / 投流）", [3, 5, 7], "倍", "关键假设。无酒旅权威基准：温泉酒店案例 3 到 6.8；餐饮服务商保底目标 10；总部独自承担投流的保本 ROI 约 25", FMT_DEC, key_cell=True)
P("B_ADS_START", "投流开始月份", [3, 2, 2], "第几月", "假设", FMT_INT)
P("B_CANNIB", "总部直播间对门店自播的挤占比例", [0.25, 0.15, 0.1], "%", "假设：总部直播间每卖 1 张券，门店自播少卖的张数；同一抖音流量池", FMT_PCT)
P("BRAND_BUDGET", "现有品牌营销月预算", 20000, "元/月", "决策人提供", FMT_INT)
P("B_HQ_TAKE_ROOM", "方案二+：团队直播间订单的总部分成", 0.08, "%", "机制设计：谁投入谁分成；总部直播间与投流带来的订单总部分成从 4% 提至 8%，门店到账 84%", FMT_PCT, key_cell=True)
P("B_ADS_STORE_SHARE", "方案二+：门店分担投流的比例", 0.5, "%", "机制设计：投流基金由门店按抖音到账分担一半；按总部直播间订单的核销到账折算", FMT_PCT, key_cell=True)
P("BRAND_SALARY", "现有品牌营销人员月薪", 10000, "元/月", "假设：决策人未提供", FMT_INT)

S("六、方案三：外包服务商（参照）")
P("C_START", "服务商开播月份", 2, "第几月", "假设", FMT_INT)
P("C_RETAINER", "服务商月固定服务费", [15000, 8000, 5000], "元/月", "酒旅代运营：基础服务费 4 到 5 万/年或月维护费 6,000 元；带货型 3 到 8 万/月；取中低档", FMT_INT)
P("C_COMM", "服务商佣金（按售出 GMV）", [0.12, 0.10, 0.08], "%", "酒旅代运营佣金 8% 到 12%（观点指数 2024）、10% 到 15%（服务商自述）", FMT_PCT)
P("C_GMV_MATURE", "服务商直播间成熟期月售出 GMV（九折口径）", [150000, 250000, 400000], "元/月", "假设：服务商代播 1.2 场/日，经济型客单价下的月产出", FMT_INT)
P("C_RAMP", "服务商达到成熟所需月数", 3, "月", "假设", FMT_INT)
P("C_ADS", "服务商要求的月投流预算", 20000, "元/月", "假设；投流代运营另收消耗 10% 到 20%", FMT_INT)
P("C_ROI", "服务商投流 ROI", [3, 4, 5], "倍", "假设", FMT_DEC)

S("七、开关（1 = 开，0 = 关；定价 1/2/3）")
P("PRICING_SEL", "月度模型采用的定价档", 1, "档", "1 = 九折，2 = 平价，3 = 平价加权益", FMT_INT, key_cell=True)
P("WEEKDAY_ONLY", "是否改为工作日券（周日至周四）", 1, "开关", "1 = 是：核销落在满房日的比例取工作日券口径", FMT_INT, key_cell=True)
P("ABSORB_BRAND", "方案二是否抵减现有品牌预算与人员", 1, "开关", "1 = 团队承接品牌传播工作，原预算与人员计入抵减", FMT_INT, key_cell=True)

# ---------------- 工作簿 ----------------
wb = Workbook()
ws_readme = wb.active
ws_readme.title = "说明"
ws_a = wb.create_sheet("假设")
ws_u = wb.create_sheet("单位经济")
ws_p = wb.create_sheet("定价对比")
ws_m = {}
for name in ["月度_基准", "月度_悲观", "月度_乐观"]:
    ws_m[name] = wb.create_sheet(name)
ws_s = wb.create_sheet("情景对比")
ws_sens = wb.create_sheet("敏感性")
ws_store = wb.create_sheet("门店损益")

# ---------------- 假设表 ----------------
ADDR = {}   # key -> row
ws = ws_a
ws["A1"] = "假设与参数"; ws["A1"].font = F_H1
ws["A2"] = "蓝色为可修改输入；黄色底为对结论影响最大的关键假设；三列分别对应悲观、基准、乐观情景。其他表引用本表，不要改动表结构。"; ws["A2"].font = F_NOTE
hdr = ["参数", "键", "悲观", "基准", "乐观", "单位", "说明与来源"]
for i, h in enumerate(hdr, 1):
    c = ws.cell(row=4, column=i, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
row = 5
for p in PARAMS:
    if "section" in p:
        c = ws.cell(row=row, column=1, value=p["section"]); c.font = F_BOLD; c.fill = FILL_SEC
        for col in range(2, 8): ws.cell(row=row, column=col).fill = FILL_SEC
        row += 1; continue
    ws.cell(row=row, column=1, value=p["label"]).font = F_LABEL
    ws.cell(row=row, column=2, value=p["key"]).font = F_NOTE
    for j, v in enumerate(p["values"]):
        c = ws.cell(row=row, column=3 + j, value=v); c.font = F_INPUT; c.number_format = p["fmt"]; c.alignment = ALIGN_R
        if p["key_cell"]: c.fill = FILL_KEY
    ws.cell(row=row, column=6, value=p["unit"]).font = F_NOTE
    ws.cell(row=row, column=7, value=p["note"]).font = F_NOTE
    ADDR[p["key"]] = row
    row += 1
ws.column_dimensions["A"].width = 38; ws.column_dimensions["B"].width = 16
for col in "CDE": ws.column_dimensions[col].width = 12
ws.column_dimensions["F"].width = 12; ws.column_dimensions["G"].width = 70
ws.freeze_panes = "C5"

def A_base(key):   # 基准列引用
    return f"'假设'!$D${ADDR[key]}"
def A_rng(key):
    r = ADDR[key]; return f"'假设'!$C${r}:$E${r}"

# ---------------- 单位经济（基准情景，每间夜）----------------
ws = ws_u
ws["A1"] = "单位经济：每间夜（基准情景，挂牌价口径）"; ws["A1"].font = F_H1
ws["A2"] = "绿色为引用假设表；黑色为计算。OTA 列为被替代订单的对照；抖音三列对应三档定价。"; ws["A2"].font = F_NOTE
cols = ["项目", "OTA 订单", "抖音九折券", "抖音平价券", "抖音平价加权益"]
for i, h in enumerate(cols, 1):
    c = ws.cell(row=4, column=i, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
U = {}  # label -> row
def urow(r, label, f_ota, f_p1, f_p2, f_p3, fmt=FMT_DEC, bold=False, fill=None):
    ws.cell(row=r, column=1, value=label).font = F_BOLD if bold else F_LABEL
    for j, f in enumerate([f_ota, f_p1, f_p2, f_p3], 2):
        c = ws.cell(row=r, column=j, value=f); c.number_format = fmt; c.alignment = ALIGN_R
        c.font = F_LINK if (isinstance(f, str) and f.startswith("='假设'")) else (F_BOLD if bold else F_CALC)
        if fill: c.fill = fill
    U[label] = r

r = 5
urow(r, "客人支付（券价或挂牌价）", f"={A_base('ADR')}", f"={A_base('P1_PRICE')}", f"={A_base('P2_PRICE')}", f"={A_base('P3_PRICE')}", FMT_DEC); r += 1
urow(r, "平台拿走", f"=B5*{A_base('OTA_CTRL')}+B5*(1-{A_base('OTA_CTRL')})*{A_base('OTA_COMM')}",
     f"=C5*{A_base('DY_FEE')}", f"=D5*{A_base('DY_FEE')}", f"=E5*{A_base('DY_FEE')}"); r += 1
urow(r, "总部分成", "=0", f"=C5*{A_base('HQ_TAKE')}", f"=D5*{A_base('HQ_TAKE')}", f"=E5*{A_base('HQ_TAKE')}"); r += 1
urow(r, "门店到账", "=B5-B6-B7", "=C5-C6-C7", "=D5-D6-D7", "=E5-E6-E7"); r += 1
urow(r, "总部管理费（到账 × 3.5%）", f"=B8*{A_base('MGMT_FEE')}", f"=C8*{A_base('MGMT_FEE')}", f"=D8*{A_base('MGMT_FEE')}", f"=E8*{A_base('MGMT_FEE')}"); r += 1
urow(r, "总部收入合计", "=B7+B9", "=C7+C9", "=D7+D9", "=E7+E9", bold=True, fill=FILL_TOTAL); r += 1
urow(r, "门店净得（到账 − 管理费）", "=B8-B9", "=C8-C9", "=D8-D9", "=E8-E9", bold=True, fill=FILL_TOTAL); r += 1
urow(r, "权益成本", "=0", f"={A_base('P1_PERK')}", f"={A_base('P2_PERK')}", f"={A_base('P3_PERK')}"); r += 1
urow(r, "变动成本", f"={A_base('VAR_COST')}", f"={A_base('VAR_COST')}", f"={A_base('VAR_COST')}", f"={A_base('VAR_COST')}"); r += 1
urow(r, "增量一夜的门店贡献（净得 − 权益 − 变动成本）", "=B11-B12-B13", "=C11-C12-C13", "=D11-D12-D13", "=E11-E12-E13", bold=True); r += 1
r += 1
ws.cell(row=r, column=1, value="替代分析：一个本来会在 OTA 成交的间夜换到抖音").font = F_BOLD; ws.cell(row=r, column=1).fill = FILL_SEC
for col in range(2, 6): ws.cell(row=r, column=col).fill = FILL_SEC
r += 1
# 被替代订单的混合口径（OTA 与直订按渠道占比加权）
urow(r, "被替代间夜的门店净得（OTA 与直订加权）",
     f"={A_base('OTA_SHARE')}*B11+(1-{A_base('OTA_SHARE')})*B5*(1-{A_base('MGMT_FEE')})", "=B17", "=B17", "=B17"); r += 1
urow(r, "被替代间夜的总部收入（加权）",
     f"={A_base('OTA_SHARE')}*B10+(1-{A_base('OTA_SHARE')})*B5*{A_base('MGMT_FEE')}", "=B18", "=B18", "=B18"); r += 1
urow(r, "替代一夜：门店损失", "=0", "=C17-C11+C12", "=D17-D11+D12", "=E17-E11+E12", bold=True); r += 1
urow(r, "替代一夜：总部变化", "=0", "=C10-C18", "=D10-D18", "=E10-E18", bold=True); r += 1
urow(r, "替代一夜：客人节省", "=0", "=B5-C5", "=B5-D5", "=B5-E5"); r += 1
urow(r, "门店盈亏平衡所需增量比例", "=0", "=C19/(C14+C19)", "=D19/(D14+D19)", "=E19/(E14+E19)", FMT_PCT, bold=True); r += 1
r += 1
ws.cell(row=r, column=1, value="当前假设下的增量比例与期望值").font = F_BOLD; ws.cell(row=r, column=1).fill = FILL_SEC
for col in range(2, 6): ws.cell(row=r, column=col).fill = FILL_SEC
r += 1
urow(r, "增量比例：不限日期券", f"=(1-{A_base('SOLDOUT_ANY')})*(1-{A_base('WOULD_BOOK')})", "=B25", "=B25", "=B25", FMT_PCT); r += 1
urow(r, "增量比例：工作日券", f"=(1-{A_base('SOLDOUT_WD')})*(1-{A_base('WOULD_BOOK')})", "=B26", "=B26", "=B26", FMT_PCT); r += 1
urow(r, "门店每抖音间夜期望收益：不限日期券", "=0", "=C25*C14-(1-C25)*C19", "=D25*D14-(1-D25)*D19", "=E25*E14-(1-E25)*E19", bold=True); r += 1
urow(r, "门店每抖音间夜期望收益：工作日券", "=0", "=C26*C14-(1-C26)*C19", "=D26*D14-(1-D26)*D19", "=E26*E14-(1-E26)*E19", bold=True); r += 1
urow(r, "总部每抖音间夜期望增量收入：不限日期券", "=0", "=C10-(1-C25)*C18", "=D10-(1-D25)*D18", "=E10-(1-E25)*E18", bold=True); r += 1
urow(r, "总部每抖音间夜期望增量收入：工作日券", "=0", "=C10-(1-C26)*C18", "=D10-(1-D26)*D18", "=E10-(1-E26)*E18", bold=True); r += 1
ws.column_dimensions["A"].width = 46
for col in "BCDE": ws.column_dimensions[col].width = 16
ws.freeze_panes = "B5"

# ---------------- 月度模型 ----------------
MONTHS = 12
def col_m(m):   # m = 0..12 -> column letter, C = 第0月
    return get_column_letter(3 + m)

LOCAL_KEYS = [k for k in ADDR]  # 全部参数拉到本地

def build_monthly(ws, scen_idx, scen_name):
    ws["A1"] = f"月度模型：{scen_name}情景"; ws["A1"].font = F_H1
    ws["A2"] = "情景列（1 悲观 / 2 基准 / 3 乐观）"; ws["A2"].font = F_LABEL
    ws["B2"] = scen_idx; ws["B2"].font = F_INPUT; ws["B2"].fill = FILL_KEY
    ws["A3"] = "本表参数区从假设表按情景列取值；月度区全部为公式。单位：元、间夜、家。"; ws["A3"].font = F_NOTE
    # 参数区
    L = {}
    r = 5
    ws.cell(row=r, column=1, value="参数（按情景取值）").font = F_BOLD; ws.cell(row=r, column=1).fill = FILL_SEC; ws.cell(row=r, column=2).fill = FILL_SEC
    r += 1
    for p in PARAMS:
        if "section" in p: continue
        ws.cell(row=r, column=1, value=p["label"]).font = F_LABEL
        c = ws.cell(row=r, column=2, value=f"=INDEX({A_rng(p['key'])},1,$B$2)"); c.font = F_LINK; c.number_format = p["fmt"]
        L[p["key"]] = f"$B${r}"
        r += 1
    # 派生参数
    r += 1
    ws.cell(row=r, column=1, value="派生参数").font = F_BOLD; ws.cell(row=r, column=1).fill = FILL_SEC; ws.cell(row=r, column=2).fill = FILL_SEC
    r += 1
    def D(key, label, formula, fmt=FMT_DEC):
        nonlocal r
        ws.cell(row=r, column=1, value=label).font = F_LABEL
        c = ws.cell(row=r, column=2, value=formula); c.font = F_CALC; c.number_format = fmt
        L[key] = f"$B${r}"; r += 1
    D("PRICE", "选用定价档的券价", f"=CHOOSE({L['PRICING_SEL']},{L['P1_PRICE']},{L['P2_PRICE']},{L['P3_PRICE']})")
    D("VOL", "选用定价档的销量系数", f"=CHOOSE({L['PRICING_SEL']},{L['P1_VOL']},{L['P2_VOL']},{L['P3_VOL']})")
    D("PERK", "选用定价档的权益成本", f"=CHOOSE({L['PRICING_SEL']},{L['P1_PERK']},{L['P2_PERK']},{L['P3_PERK']})")
    D("STORE_RATE", "门店到账比例", f"=1-{L['DY_FEE']}-{L['HQ_TAKE']}", FMT_PCT)
    D("DY_STORE_NET", "抖音间夜门店净得", f"={L['PRICE']}*{L['STORE_RATE']}*(1-{L['MGMT_FEE']})")
    D("DY_HQ_NIGHT", "抖音间夜总部收入", f"={L['PRICE']}*({L['HQ_TAKE']}+{L['STORE_RATE']}*{L['MGMT_FEE']})")
    D("CF_STORE_NET", "被替代间夜门店净得（加权）", f"={L['OTA_SHARE']}*{L['ADR']}*(1-{L['OTA_CTRL']})*(1-{L['OTA_COMM']})*(1-{L['MGMT_FEE']})+(1-{L['OTA_SHARE']})*{L['ADR']}*(1-{L['MGMT_FEE']})")
    D("CF_HQ_NIGHT", "被替代间夜总部收入（加权）", f"={L['OTA_SHARE']}*{L['ADR']}*(1-{L['OTA_CTRL']})*(1-{L['OTA_COMM']})*{L['MGMT_FEE']}+(1-{L['OTA_SHARE']})*{L['ADR']}*{L['MGMT_FEE']}")
    D("INC", "增量比例", f"=(1-IF({L['WEEKDAY_ONLY']}=1,{L['SOLDOUT_WD']},{L['SOLDOUT_ANY']}))*(1-{L['WOULD_BOOK']})", FMT_PCT)
    D("STORE_INC_CONTRIB", "增量一夜门店贡献", f"={L['DY_STORE_NET']}-{L['PERK']}-{L['VAR_COST']}")
    D("STORE_SUB_LOSS", "替代一夜门店损失", f"={L['CF_STORE_NET']}-{L['DY_STORE_NET']}+{L['PERK']}")
    D("BASE_SOLD0", "倒推上月售出 GMV", f"={L['BASE_HQ_COMM']}/{L['HQ_TAKE']}/{L['BASE_REDEEM_EST']}", FMT_INT)
    D("BASE_VPS", "倒推单店月售出券数（九折）", f"={L['BASE_SOLD0']}/{L['P1_PRICE']}/{L['STORES0']}", FMT_DEC)
    D("MGR_HOURLY", "店长小时成本", f"={L['MGR_SALARY']}/{L['WORK_HOURS']}")
    D("TEAM_SAL", "团队月薪合计（含社保）", f"=({L['B_SAL_LEAD']}+{L['B_SAL_HOST']}+{L['B_SAL_CTRL']}+{L['B_SAL_ADS']})*(1+{L['SOCIAL']})", FMT_INT)
    D("BRAND_CREDIT", "可抵减的品牌预算与人员（月）", f"={L['ABSORB_BRAND']}*({L['BRAND_BUDGET']}+{L['BRAND_SALARY']}*(1+{L['SOCIAL']}))", FMT_INT)

    # 月度区
    r += 1
    start = r
    ws.cell(row=r, column=1, value="月度表").font = F_BOLD
    ws.cell(row=r, column=2, value="单位").font = F_BOLD
    for m in range(0, MONTHS + 1):
        c = ws.cell(row=r, column=3 + m, value=("第0月（现状）" if m == 0 else f"第{m}月")); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
    ws.cell(row=r, column=1).fill = FILL_H2; ws.cell(row=r, column=1).font = F_H2
    ws.cell(row=r, column=2).fill = FILL_H2; ws.cell(row=r, column=2).font = F_H2
    r += 1
    R = {}
    def mrow(key, label, unit, fn, fmt=FMT_INT, bold=False, fill=None):
        """fn(m, c, p, pp) -> formula string; c 当前列, p 前一列, pp 前两列"""
        nonlocal r
        R[key] = r
        ws.cell(row=r, column=1, value=label).font = F_BOLD if bold else F_LABEL
        ws.cell(row=r, column=2, value=unit).font = F_NOTE
        for m in range(0, MONTHS + 1):
            c = col_m(m); p = col_m(max(0, m - 1)); pp = col_m(max(0, m - 2))
            cell = ws.cell(row=r, column=3 + m, value=fn(m, c, p, pp)); cell.number_format = fmt; cell.alignment = ALIGN_R
            cell.font = F_BOLD if bold else F_CALC
            if fill: cell.fill = fill
        r += 1
    def ref(key, c): return f"{c}{R[key]}"
    def section(title):
        nonlocal r
        c = ws.cell(row=r, column=1, value=title); c.font = F_BOLD; c.fill = FILL_SEC
        for col in range(2, 4 + MONTHS): ws.cell(row=r, column=col).fill = FILL_SEC
        r += 1

    section("基线：门店与系统（无抖音）")
    mrow("month", "月份", "月", lambda m, c, p, pp: m, FMT_INT)
    mrow("stores", "门店数（月末）", "家", lambda m, c, p, pp: f"={L['STORES0']}" if m == 0 else f"=ROUND({L['STORES0']}+{L['NEW_PM']}*{m},0)")
    mrow("newstores", "当月新增门店", "家", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('stores', c)}-{ref('stores', p)}")
    mrow("effstores", "有效门店数（新店首月按半店计）", "家", lambda m, c, p, pp: f"={ref('stores', c)}" if m == 0 else f"={ref('stores', p)}+0.5*{ref('newstores', c)}", FMT_DEC)
    mrow("nights", "系统间夜", "间夜", lambda m, c, p, pp: f"={ref('stores', c)}*{L['ROOMS']}*{L['OCC']}*{L['DAYS']}")
    mrow("rev", "系统流水（挂牌口径）", "元", lambda m, c, p, pp: f"={ref('nights', c)}*{L['ADR']}")
    mrow("hqfee_base", "总部管理费基线（无抖音）", "元", lambda m, c, p, pp: f"={ref('nights', c)}*{L['CF_HQ_NIGHT']}")

    def option_block(code, title, vouch_fn, cost_fns, store_hours_fn, extra_income_fn=None, extra_store_fn=None, store_comm=False):
        """vouch_fn(m,c,p,pp) -> 售出券数公式（含子项行自行添加后再汇总）"""
        section(title)
        mrow(f"{code}_v", "售出券数", "张", vouch_fn)
        mrow(f"{code}_sold", "售出 GMV（券面）", "元", lambda m, c, p, pp: f"={ref(f'{code}_v', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref(f'{code}_v', c)}*{L['PRICE']}")
        def redeem_fn(m, c, p, pp):
            if m == 0: return f"={L['REDEEM']}*{ref(f'{code}_sold', c)}"
            return f"={L['REDEEM']}*({L['LAG0']}*{ref(f'{code}_sold', c)}+{L['LAG1']}*{ref(f'{code}_sold', p)}+{L['LAG2']}*{ref(f'{code}_sold', pp)})"
        mrow(f"{code}_red", "核销 GMV（结算口径）", "元", redeem_fn)
        def rednights_fn(m, c, p, pp):
            if m == 0: return f"={L['REDEEM']}*{ref(f'{code}_v', c)}"
            return f"={L['REDEEM']}*({L['LAG0']}*{ref(f'{code}_v', c)}+{L['LAG1']}*{ref(f'{code}_v', p)}+{L['LAG2']}*{ref(f'{code}_v', pp)})"
        mrow(f"{code}_n", "核销间夜", "间夜", rednights_fn)
        mrow(f"{code}_inc", "其中：增量间夜", "间夜", lambda m, c, p, pp: f"={ref(f'{code}_n', c)}*{L['INC']}")
        mrow(f"{code}_sub", "其中：替代间夜", "间夜", lambda m, c, p, pp: f"={ref(f'{code}_n', c)}-{ref(f'{code}_inc', c)}")
        mrow(f"{code}_hqc", "总部分成收入", "元", lambda m, c, p, pp: f"={ref(f'{code}_red', c)}*{L['HQ_TAKE']}")
        mrow(f"{code}_hqf", "总部管理费（抖音单）", "元", lambda m, c, p, pp: f"={ref(f'{code}_red', c)}*{L['STORE_RATE']}*{L['MGMT_FEE']}")
        mrow(f"{code}_hqcf", "减：被替代订单原有管理费", "元", lambda m, c, p, pp: f"=-{ref(f'{code}_sub', c)}*{L['CF_HQ_NIGHT']}")
        mrow(f"{code}_hqx", "机制：团队订单加成分成（总部多得）", "元", extra_income_fn or (lambda m, c, p, pp: "=0"))
        mrow(f"{code}_hqinc", "总部增量收入", "元", lambda m, c, p, pp: f"={ref(f'{code}_hqc', c)}+{ref(f'{code}_hqf', c)}+{ref(f'{code}_hqcf', c)}+{ref(f'{code}_hqx', c)}", bold=True)
        for ck, clabel, cfn in cost_fns:
            mrow(f"{code}_{ck}", clabel, "元", cfn)
        cost_keys = [f"{code}_{ck}" for ck, _, _ in cost_fns]
        mrow(f"{code}_cost", "总部成本合计", "元", lambda m, c, p, pp: "=" + "+".join(ref(k, c) for k in cost_keys), bold=True)
        mrow(f"{code}_net", "总部增量净收益", "元", lambda m, c, p, pp: f"={ref(f'{code}_hqinc', c)}-{ref(f'{code}_cost', c)}", bold=True, fill=FILL_TOTAL)
        mrow(f"{code}_cum", "累计净收益（第 1 月起）", "元", lambda m, c, p, pp: "=0" if m == 0 else (f"={ref(f'{code}_net', c)}" if m == 1 else f"={ref(f'{code}_cum', p)}+{ref(f'{code}_net', c)}"))
        mrow(f"{code}_paid", "已回本标记", "", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({ref(f'{code}_cum', c)}>=0,1,0)")
        mrow(f"{code}_sh", "门店直播投入小时", "小时", store_hours_fn)
        mrow(f"{code}_stx", "机制：门店让渡的分成与分担的投流", "元", extra_store_fn or (lambda m, c, p, pp: "=0"))
        mrow(f"{code}_stc", "门店承担的开播提成", "元", (lambda m, c, p, pp: "=0" if m == 0 else f"=-{L['AP_COMM']}*{L['COMM_BY_STORE']}*{ref(f'{code}_storesold', c)}") if store_comm else (lambda m, c, p, pp: "=0"))
        mrow(f"{code}_store", "门店端净收益变化（全系统）", "元", lambda m, c, p, pp: f"={ref(f'{code}_inc', c)}*{L['STORE_INC_CONTRIB']}-{ref(f'{code}_sub', c)}*{L['STORE_SUB_LOSS']}-{ref(f'{code}_sh', c)}*{L['MGR_HOURLY']}+{ref(f'{code}_stx', c)}+{ref(f'{code}_stc', c)}", bold=True)
        mrow(f"{code}_sys", "系统合计净收益（总部 + 门店）", "元", lambda m, c, p, pp: f"={ref(f'{code}_net', c)}+{ref(f'{code}_store', c)}", bold=True, fill=FILL_TOTAL)

    zero = lambda m, c, p, pp: "=0"
    # 方案一A：现状延续
    def va_fn(m, c, p, pp):
        if m == 0: return f"={L['BASE_VPS']}*{L['STORES0']}"
        return f"={L['BASE_VPS']}*{L['VOL']}*{ref('effstores', c)}*(1+{L['A_DRIFT']})^{m}"
    option_block("A", "方案一A：门店自播，现状延续（总部不投入）", va_fn,
                 [("c_people", "成本：人力", zero), ("c_ads", "成本：投流或服务商", zero), ("c_equip", "成本：设备摊销与场地", zero), ("c_train", "成本：培训与激励", zero), ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}")
    # 方案一B：规范化门店直播
    def vb_store_fn(m, c, p, pp):
        if m == 0: return f"={L['BASE_VPS']}*{L['STORES0']}"
        return f"={L['BASE_VPS']}*{L['VOL']}*{ref('effstores', c)}*(1+{L['AP_DRIFT']})^{m}*(1+({L['AP_UPLIFT']}-1)*MIN(1,{m}/{L['AP_RAMP']}))"
    def train_fn(code):
        def f(m, c, p, pp):
            if m == 0: return "=0"
            kit = f"{L['AP_STORE_KIT']}*{ref('stores', c)}" if m == 1 else f"{L['AP_STORE_KIT']}*{ref('newstores', c)}"
            oneoff = f"+{L['AP_TRAIN_ONEOFF']}" if m == 1 else ""
            return f"={kit}{oneoff}+{L['AP_TRAIN_MONTHLY']}+{L['AP_COMM']}*(1-{L['COMM_BY_STORE']})*{ref(f'{code}_storesold', c)}"
        return f
    # 需要门店部分售出 GMV 的辅助行：先放辅助行再放 block
    section("方案一B：规范化门店直播（总部督导 + 培训 + 提成）— 辅助行")
    mrow("B1_storev", "门店自播售出券数", "张", vb_store_fn)
    mrow("B1_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('B1_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('B1_storev', c)}*{L['PRICE']}")
    option_block("B1", "方案一B：规范化门店直播（总部督导 + 培训 + 提成）", lambda m, c, p, pp: f"={ref('B1_storev', c)}",
                 [("c_people", "成本：人力（直播督导 1 人）", lambda m, c, p, pp: "=0" if m == 0 else f"={L['AP_SUP_SALARY']}*(1+{L['SOCIAL']})"),
                  ("c_ads", "成本：投流或服务商", zero),
                  ("c_equip", "成本：设备摊销与场地", zero),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("B1")),
                  ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", store_comm=True)
    # 方案二：总部直播团队 + 门店赋能
    section("方案二：总部直播团队（含门店赋能）— 辅助行")
    mrow("B2_active", "团队是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_START']},1,0)")
    mrow("B2_gph", "总部直播间每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2_active', c)}*({L['B_GPH_START']}+({L['B_GPH_MATURE']}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L['B_START']}+1)/{L['B_RAMP']}))")
    mrow("B2_roomv", "总部直播间售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['B_HOURS']}*{ref('B2_gph', c)}/{L['P1_PRICE']}*{L['VOL']}")
    mrow("B2_adsv", "投流带来的售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']}*{L['B_ROI']}/{L['P1_PRICE']}*{L['VOL']},0)")
    mrow("B2_hqsold", "总部直播间与投流售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"=({ref('B2_roomv', c)}+{ref('B2_adsv', c)})*{L['PRICE']}")
    mrow("B2_storev", "门店自播售出券数（赋能后，扣除总部直播间挤占）", "张", lambda m, c, p, pp: vb_store_fn(m, c, p, pp) if m == 0 else f"=MAX(0,{vb_store_fn(m, c, p, pp)[1:]}-{L['B_CANNIB']}*({ref('B2_roomv', c)}+{ref('B2_adsv', c)}))")
    mrow("B2_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('B2_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('B2_storev', c)}*{L['PRICE']}")
    option_block("B2", "方案二：总部直播团队（含门店赋能）", lambda m, c, p, pp: f"={ref('B2_storev', c)}+{ref('B2_roomv', c)}+{ref('B2_adsv', c)}",
                 [("c_people", "成本：团队人力（4 人含社保）+ 主播提成 + 招聘", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2_active', c)}*{L['TEAM_SAL']}+{L['B_HOST_COMM']}*{ref('B2_hqsold', c)}" + (f"+{L['B_RECRUIT']}" if m == 1 else "")),
                  ("c_ads", "成本：投流", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']},0)"),
                  ("c_equip", "成本：设备摊销与场地", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2_active', c)}*({L['B_EQUIP']}/{L['B_EQUIP_MONTHS']}+{L['B_SPACE']})"),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("B2")),
                  ("c_credit", "减：抵减的品牌预算与人员", lambda m, c, p, pp: "=0" if m == 0 else f"=-{ref('B2_active', c)}*{L['BRAND_CREDIT']}")],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", store_comm=True)
    # 方案二+：总部直播团队 + 配套分成机制
    section("方案二+：总部直播团队 + 配套机制（团队订单总部分成提高、门店分担投流）— 辅助行")
    mrow("B2M_active", "团队是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_START']},1,0)")
    mrow("B2M_gph", "总部直播间每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2M_active', c)}*({L['B_GPH_START']}+({L['B_GPH_MATURE']}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L['B_START']}+1)/{L['B_RAMP']}))")
    mrow("B2M_roomv", "总部直播间售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['B_HOURS']}*{ref('B2M_gph', c)}/{L['P1_PRICE']}*{L['VOL']}")
    mrow("B2M_adsv", "投流带来的售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']}*{L['B_ROI']}/{L['P1_PRICE']}*{L['VOL']},0)")
    mrow("B2M_hqsold", "总部直播间与投流售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"=({ref('B2M_roomv', c)}+{ref('B2M_adsv', c)})*{L['PRICE']}")
    def b2m_hqred(m, c, p, pp):
        if m == 0: return "=0"
        return f"={L['REDEEM']}*({L['LAG0']}*{ref('B2M_hqsold', c)}+{L['LAG1']}*{ref('B2M_hqsold', p)}+{L['LAG2']}*{ref('B2M_hqsold', pp)})"
    mrow("B2M_hqred", "总部直播间与投流核销 GMV", "元", b2m_hqred)
    mrow("B2M_storev", "门店自播售出券数（赋能后，扣除总部直播间挤占）", "张", lambda m, c, p, pp: vb_store_fn(m, c, p, pp) if m == 0 else f"=MAX(0,{vb_store_fn(m, c, p, pp)[1:]}-{L['B_CANNIB']}*({ref('B2M_roomv', c)}+{ref('B2M_adsv', c)}))")
    mrow("B2M_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('B2M_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('B2M_storev', c)}*{L['PRICE']}")
    option_block("B2M", "方案二+：总部直播团队 + 配套机制", lambda m, c, p, pp: f"={ref('B2M_storev', c)}+{ref('B2M_roomv', c)}+{ref('B2M_adsv', c)}",
                 [("c_people", "成本：团队人力（4 人含社保）+ 主播提成 + 招聘", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2M_active', c)}*{L['TEAM_SAL']}+{L['B_HOST_COMM']}*{ref('B2M_hqsold', c)}" + (f"+{L['B_RECRUIT']}" if m == 1 else "")),
                  ("c_ads", "成本：投流（扣除门店分担部分）", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']}*(1-{L['B_ADS_STORE_SHARE']}),0)"),
                  ("c_equip", "成本：设备摊销与场地", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2M_active', c)}*({L['B_EQUIP']}/{L['B_EQUIP_MONTHS']}+{L['B_SPACE']})"),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("B2M")),
                  ("c_credit", "减：抵减的品牌预算与人员", lambda m, c, p, pp: "=0" if m == 0 else f"=-{ref('B2M_active', c)}*{L['BRAND_CREDIT']}")],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}",
                 extra_income_fn=lambda m, c, p, pp: "=0" if m == 0 else f"=({L['B_HQ_TAKE_ROOM']}-{L['HQ_TAKE']})*(1-{L['MGMT_FEE']})*{ref('B2M_hqred', c)}",
                 extra_store_fn=lambda m, c, p, pp: "=0" if m == 0 else f"=-({L['B_HQ_TAKE_ROOM']}-{L['HQ_TAKE']})*(1-{L['MGMT_FEE']})*{ref('B2M_hqred', c)}-IF({m}>={L['B_ADS_START']},{L['B_ADS']}*{L['B_ADS_STORE_SHARE']},0)", store_comm=True)
    # 方案三：外包服务商
    section("方案三：外包服务商代播（参照）— 辅助行")
    mrow("C_storev", "门店自播售出券数（同现状延续）", "张", va_fn)
    mrow("C_active", "服务商是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['C_START']},1,0)")
    mrow("C_agv", "服务商直播间售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('C_active', c)}*{L['C_GMV_MATURE']}*MIN(1,MAX(0,{m}-{L['C_START']}+1)/{L['C_RAMP']})/{L['P1_PRICE']}*{L['VOL']}")
    mrow("C_adsv", "服务商投流带来的售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('C_active', c)}*{L['C_ADS']}*{L['C_ROI']}/{L['P1_PRICE']}*{L['VOL']}")
    mrow("C_agsold", "服务商直播间与投流售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"=({ref('C_agv', c)}+{ref('C_adsv', c)})*{L['PRICE']}")
    option_block("C", "方案三：外包服务商代播（参照）", lambda m, c, p, pp: f"={ref('C_storev', c)}+{ref('C_agv', c)}+{ref('C_adsv', c)}",
                 [("c_people", "成本：人力", zero),
                  ("c_ads", "成本：服务商固定费 + 佣金 + 投流", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('C_active', c)}*({L['C_RETAINER']}+{L['C_ADS']})+{L['C_COMM']}*{ref('C_agsold', c)}"),
                  ("c_equip", "成本：设备摊销与场地", zero),
                  ("c_train", "成本：培训与激励", zero),
                  ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}")
    ws.column_dimensions["A"].width = 44; ws.column_dimensions["B"].width = 14
    for m in range(0, MONTHS + 1): ws.column_dimensions[col_m(m)].width = 13
    ws.freeze_panes = ws.cell(row=start + 1, column=3)
    return L, R, start

MS = {}
for name, idx in [("月度_基准", 2), ("月度_悲观", 1), ("月度_乐观", 3)]:
    MS[name] = build_monthly(ws_m[name], idx, name.split("_")[1])

# ---------------- 情景对比 ----------------
ws = ws_s
ws["A1"] = "情景对比：12 个月合计（第 1 到 12 月）"; ws["A1"].font = F_H1
ws["A2"] = "全部为公式，引用三张月度表。回本月指累计总部净收益首次转正的月份。"; ws["A2"].font = F_NOTE
OPTS = [("A", "方案一A 门店自播，现状延续"), ("B1", "方案一B 规范化门店直播"), ("B2", "方案二 总部直播团队（现有分成）"), ("B2M", "方案二+ 总部直播团队 + 配套机制"), ("C", "方案三 外包服务商（参照）")]
METRICS = [("sold", "售出 GMV", FMT_INT), ("red", "核销 GMV", FMT_INT), ("n", "核销间夜", FMT_INT), ("inc", "增量间夜", FMT_INT),
           ("hqinc", "总部增量收入", FMT_INT), ("cost", "总部成本", FMT_INT), ("net", "总部增量净收益", FMT_INT), ("paid", "回本月", FMT_INT),
           ("store", "门店端净收益变化", FMT_INT), ("sys", "系统合计净收益", FMT_INT)]
r = 4
SUMMARY_ROWS = {}
for sname, sidx in [("月度_基准", 2), ("月度_悲观", 1), ("月度_乐观", 3)]:
    L, R, start = MS[sname]
    c = ws.cell(row=r, column=1, value=f"{sname.split('_')[1]}情景"); c.font = F_H2; c.fill = FILL_H2
    for j, (mk, ml, _) in enumerate(METRICS, 2):
        c = ws.cell(row=r, column=j, value=ml); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
    r += 1
    for code, olabel in OPTS:
        ws.cell(row=r, column=1, value=olabel).font = F_LABEL
        for j, (mk, ml, fmt) in enumerate(METRICS, 2):
            rr = R[f"{code}_{mk}"]
            if mk == "paid":
                f = f"=IFERROR(MATCH(1,'{sname}'!$D${rr}:$O${rr},0),\"12 个月内未回本\")"
            else:
                f = f"=SUM('{sname}'!$D${rr}:$O${rr})"
            c = ws.cell(row=r, column=j, value=f); c.font = F_LINK; c.number_format = fmt; c.alignment = ALIGN_R
        SUMMARY_ROWS[(sname, code)] = r
        r += 1
    r += 1
# 边际对比：方案二相对方案一B
for mcode, mtitle in [("B2", "边际：方案二（现有分成）相对方案一B"), ("B2M", "边际：方案二+（配套机制）相对方案一B")]:
    c = ws.cell(row=r, column=1, value=mtitle); c.font = F_H2; c.fill = FILL_H2
    for j, h in enumerate(["情景", "多售出 GMV", "多核销 GMV", "总部多增收入", "总部多成本", "总部净收益差", "门店端差", "系统合计差"], 2):
        c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
    r += 1
    for sname in ["月度_悲观", "月度_基准", "月度_乐观"]:
        ws.cell(row=r, column=2, value=sname.split("_")[1]).font = F_LABEL
        rb2 = SUMMARY_ROWS[(sname, mcode)]; rb1 = SUMMARY_ROWS[(sname, "B1")]
        pairs = [("sold", 2), ("red", 3), ("hqinc", 6), ("cost", 7), ("net", 8), ("store", 10), ("sys", 11)]
        for j, (mk, colidx) in enumerate(pairs, 3):
            colL = get_column_letter(colidx)
            c = ws.cell(row=r, column=j, value=f"={colL}{rb2}-{colL}{rb1}"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
        r += 1
    r += 1
ws.column_dimensions["A"].width = 34
for j in range(2, 13): ws.column_dimensions[get_column_letter(j)].width = 15
ws.freeze_panes = "B5"

# ---------------- 敏感性（稳态月度，基准情景参数）----------------
ws = ws_sens
ws["A1"] = "敏感性：方案二相对方案一B 的稳态月度边际净收益（总部口径）"; ws["A1"].font = F_H1
ws["A2"] = "稳态 = 团队成熟期、投流已开始、门店数取当前值。公式引用假设表基准列。单元格为每月总部净收益差额（元）。"; ws["A2"].font = F_NOTE
# 稳态参数（基准列）
sr = 4
def sp(label, formula, fmt=FMT_DEC):
    global sr
    ws.cell(row=sr, column=1, value=label).font = F_LABEL
    c = ws.cell(row=sr, column=2, value=formula); c.font = F_CALC; c.number_format = fmt
    sr += 1
    return f"$B${sr-1}"
S_PRICE = sp("券价（基准定价档）", f"=CHOOSE({A_base('PRICING_SEL')},{A_base('P1_PRICE')},{A_base('P2_PRICE')},{A_base('P3_PRICE')})")
S_VOL = sp("销量系数", f"=CHOOSE({A_base('PRICING_SEL')},{A_base('P1_VOL')},{A_base('P2_VOL')},{A_base('P3_VOL')})")
S_INC = sp("增量比例", f"=(1-IF({A_base('WEEKDAY_ONLY')}=1,{A_base('SOLDOUT_WD')},{A_base('SOLDOUT_ANY')}))*(1-{A_base('WOULD_BOOK')})", FMT_PCT)
S_CFHQ = sp("被替代间夜总部收入", f"={A_base('OTA_SHARE')}*{A_base('ADR')}*(1-{A_base('OTA_CTRL')})*(1-{A_base('OTA_COMM')})*{A_base('MGMT_FEE')}+(1-{A_base('OTA_SHARE')})*{A_base('ADR')}*{A_base('MGMT_FEE')}")
S_TAKE = sp("每元核销 GMV 的总部增量收入", f"={A_base('HQ_TAKE')}+(1-{A_base('DY_FEE')}-{A_base('HQ_TAKE')})*{A_base('MGMT_FEE')}-(1-{S_INC})*{S_CFHQ}/{S_PRICE}", '0.0000')
S_COST = sp("团队稳态月成本（人力、设备、场地、投流，扣抵减）", f"=({A_base('B_SAL_LEAD')}+{A_base('B_SAL_HOST')}+{A_base('B_SAL_CTRL')}+{A_base('B_SAL_ADS')})*(1+{A_base('SOCIAL')})+{A_base('B_EQUIP')}/{A_base('B_EQUIP_MONTHS')}+{A_base('B_SPACE')}+{A_base('B_ADS')}-{A_base('ABSORB_BRAND')}*({A_base('BRAND_BUDGET')}+{A_base('BRAND_SALARY')}*(1+{A_base('SOCIAL')}))-{A_base('AP_SUP_SALARY')}*(1+{A_base('SOCIAL')})", FMT_INT)
ws.cell(row=sr, column=1, value="注：成本已扣除方案一B 本来就要付的督导人力，因此是边际成本；主播提成在矩阵公式内按售出 GMV 计。").font = F_NOTE
sr += 2
# 矩阵1：每小时 GMV × 投流 ROI
ws.cell(row=sr, column=1, value="矩阵一：行 = 成熟期每小时售出 GMV（九折口径，元/小时）；列 = 投流 ROI。投流预算与开播小时取基准值。").font = F_BOLD
sr += 1
gph_list = [2000, 3000, 4000, 5000, 6000, 8000, 10000]
roi_list = [2, 3, 4, 5, 6, 8]
ws.cell(row=sr, column=1, value="每小时 GMV \\ ROI").font = F_BOLD
for j, roi in enumerate(roi_list, 2):
    c = ws.cell(row=sr, column=j, value=roi); c.font = F_INPUT; c.number_format = '0.0"x"'; c.alignment = ALIGN_C
hdr_row = sr; sr += 1
for gph in gph_list:
    c = ws.cell(row=sr, column=1, value=gph); c.font = F_INPUT; c.number_format = FMT_INT
    for j, roi in enumerate(roi_list, 2):
        colL = get_column_letter(j)
        sold = f"(({A_base('B_HOURS')}*$A{sr}+{A_base('B_ADS')}*{colL}${hdr_row})/{A_base('P1_PRICE')}*{S_VOL}*{S_PRICE})"
        f = f"={sold}*{A_base('REDEEM')}*{S_TAKE}-{A_base('B_HOST_COMM')}*{sold}-{S_COST}"
        c = ws.cell(row=sr, column=j, value=f); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    sr += 1
sr += 1
# 矩阵2：每小时 GMV × 团队月人力成本
ws.cell(row=sr, column=1, value="矩阵二：行 = 成熟期每小时售出 GMV；列 = 团队月人力成本（含社保，元）。投流与 ROI 取基准值。").font = F_BOLD
sr += 1
sal_list = [40000, 50000, 60000, 70000, 80000]
ws.cell(row=sr, column=1, value="每小时 GMV \\ 人力成本").font = F_BOLD
for j, sal in enumerate(sal_list, 2):
    c = ws.cell(row=sr, column=j, value=sal); c.font = F_INPUT; c.number_format = FMT_INT; c.alignment = ALIGN_C
hdr_row2 = sr; sr += 1
for gph in gph_list:
    c = ws.cell(row=sr, column=1, value=gph); c.font = F_INPUT; c.number_format = FMT_INT
    for j, sal in enumerate(sal_list, 2):
        colL = get_column_letter(j)
        sold = f"(({A_base('B_HOURS')}*$A{sr}+{A_base('B_ADS')}*{A_base('B_ROI')})/{A_base('P1_PRICE')}*{S_VOL}*{S_PRICE})"
        other_cost = f"({A_base('B_EQUIP')}/{A_base('B_EQUIP_MONTHS')}+{A_base('B_SPACE')}+{A_base('B_ADS')}-{A_base('ABSORB_BRAND')}*({A_base('BRAND_BUDGET')}+{A_base('BRAND_SALARY')}*(1+{A_base('SOCIAL')}))-{A_base('AP_SUP_SALARY')}*(1+{A_base('SOCIAL')}))"
        f = f"={sold}*{A_base('REDEEM')}*{S_TAKE}-{A_base('B_HOST_COMM')}*{sold}-{colL}${hdr_row2}-{other_cost}"
        c = ws.cell(row=sr, column=j, value=f); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    sr += 1
sr += 1
# 矩阵3：增量比例 × 核销率 → 门店每张券的期望收益（九折）
ws.cell(row=sr, column=1, value="矩阵三：门店视角。行 = 增量比例；列 = 定价档。单元格 = 门店每个抖音核销间夜的期望收益（元）。").font = F_BOLD
sr += 1
inc_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7]
ws.cell(row=sr, column=1, value="增量比例 \\ 定价档").font = F_BOLD
for j, lab in enumerate(["九折", "平价", "平价加权益"], 2):
    c = ws.cell(row=sr, column=j, value=lab); c.font = F_BOLD; c.alignment = ALIGN_C
hdr3 = sr; sr += 1
for inc in inc_list:
    c = ws.cell(row=sr, column=1, value=inc); c.font = F_INPUT; c.number_format = FMT_PCT
    for j, ucol in enumerate(["C", "D", "E"], 2):
        f = f"=$A{sr}*'单位经济'!{ucol}$14-(1-$A{sr})*'单位经济'!{ucol}$19"
        c = ws.cell(row=sr, column=j, value=f); c.font = F_LINK; c.number_format = FMT_DEC; c.alignment = ALIGN_R
    sr += 1
ws.column_dimensions["A"].width = 44
for j in range(2, 9): ws.column_dimensions[get_column_letter(j)].width = 14

# ---------------- 门店损益（单店，基准情景）----------------
ws = ws_store
ws["A1"] = "门店损益：典型单店每月（基准情景）"; ws["A1"].font = F_H1
ws["A2"] = "回答加盟商最关心的问题：抖音单对我的店是赚是亏。全部为公式。"; ws["A2"].font = F_NOTE
r = 4
def srow(label, formula, fmt=FMT_DEC, bold=False):
    global r
    ws.cell(row=r, column=1, value=label).font = F_BOLD if bold else F_LABEL
    c = ws.cell(row=r, column=2, value=formula); c.number_format = fmt; c.font = F_BOLD if bold else F_CALC; c.alignment = ALIGN_R
    r += 1
    return f"$B${r-1}"
ST_NIGHTS = srow("单店月间夜", f"={A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')}", FMT_INT)
ST_REV = srow("单店月流水（挂牌口径）", f"={ST_NIGHTS}*{A_base('ADR')}", FMT_INT)
ST_PROFIT_CF = srow("单店月净得基线（扣平台费与管理费，不含房租人工）", f"={ST_NIGHTS}*'单位经济'!$B$17", FMT_INT)
ST_VPS = srow("单店月售出券数（九折、现状倒推）", f"={A_base('BASE_HQ_COMM')}/{A_base('HQ_TAKE')}/{A_base('BASE_REDEEM_EST')}/{A_base('P1_PRICE')}/{A_base('STORES0')}", FMT_DEC)
ST_DN = srow("单店月抖音核销间夜（九折）", f"={ST_VPS}*{A_base('REDEEM')}", FMT_DEC)
ST_SHARE = srow("抖音核销间夜占单店间夜比例", f"={ST_DN}/{ST_NIGHTS}", FMT_PCT)
r += 1
ws.cell(row=r, column=1, value="单店每月净收益变化（元）：行 = 券类型；列 = 定价档").font = F_BOLD; r += 1
hdr = ["", "九折", "平价", "平价加权益"]
for j, h in enumerate(hdr, 1):
    c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
r += 1
for lab, inc_row in [("不限日期券", 25), ("工作日券（周日至周四）", 26)]:
    ws.cell(row=r, column=1, value=lab).font = F_LABEL
    for j, (ucol, volkey) in enumerate([("C", "P1_VOL"), ("D", "P2_VOL"), ("E", "P3_VOL")], 2):
        # 核销间夜随销量系数变化；期望收益按单位经济表
        f = f"={ST_VPS}*{A_base(volkey)}*{A_base('REDEEM')}*('单位经济'!{ucol}${inc_row}*'单位经济'!{ucol}$14-(1-'单位经济'!{ucol}${inc_row})*'单位经济'!{ucol}$19)-{A_base('STORE_HOURS')}*{A_base('MGR_SALARY')}/{A_base('WORK_HOURS')}"
        c = ws.cell(row=r, column=j, value=f); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    r += 1
ws.cell(row=r, column=1, value="注：已扣除门店自播的店长时间成本（按假设表的每月直播小时数 × 店长小时成本）。").font = F_NOTE; r += 2
ws.cell(row=r, column=1, value="总部每月从该店抖音单获得的增量收入（元）").font = F_BOLD; r += 1
for j, h in enumerate(hdr, 1):
    c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
r += 1
for lab, inc_row in [("不限日期券", 29), ("工作日券（周日至周四）", 30)]:
    ws.cell(row=r, column=1, value=lab).font = F_LABEL
    for j, (ucol, volkey) in enumerate([("C", "P1_VOL"), ("D", "P2_VOL"), ("E", "P3_VOL")], 2):
        f = f"={ST_VPS}*{A_base(volkey)}*{A_base('REDEEM')}*'单位经济'!{ucol}${inc_row}"
        c = ws.cell(row=r, column=j, value=f); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    r += 1
ws.column_dimensions["A"].width = 52
for col in "BCD": ws.column_dimensions[col].width = 16

# ---------------- 说明 ----------------
ws = ws_readme
lines = [
    ("住小叮抖音直播方案 财务模型", F_H1),
    ("版本：2026 年 11 月；配合《住小叮抖音直播组织方案 股东决策文档》使用。", F_NOTE),
    ("", F_LABEL),
    ("怎么用", F_BOLD),
    ("1. 只改「假设」表里的蓝色单元格。黄色底的是对结论影响最大的关键假设。", F_LABEL),
    ("2. 三列分别是悲观、基准、乐观情景；三张月度表各取一列计算，「情景对比」汇总 12 个月结果。", F_LABEL),
    ("3. 「开关」区：定价档（1 九折 / 2 平价 / 3 平价加权益）、是否工作日券、方案二是否抵减现有品牌预算。", F_LABEL),
    ("4. 「单位经济」看每间夜的账；「定价对比」看三档定价的稳态比较；「门店损益」回答加盟商的问题；「敏感性」看方案二的边际收益对关键参数的敏感程度。", F_LABEL),
    ("", F_LABEL),
    ("颜色约定", F_BOLD),
    ("蓝色字 = 输入；黑色字 = 公式；绿色字 = 引用其他表；黄色底 = 关键假设。", F_LABEL),
    ("", F_LABEL),
    ("口径说明", F_BOLD),
    ("流水均按挂牌价口径；总部管理费按门店到账金额的 3.5% 计提（决策人口径）；抖音售出 GMV 为券面金额，核销 GMV 为结算口径，按 50% / 30% / 20% 分三个月核销。", F_LABEL),
    ("增量比例 = （1 − 核销落在满房日的比例）×（1 − 原本就会预订本品牌的比例）。替代间夜按 OTA 与直订加权的对照口径计算门店与总部的得失。", F_LABEL),
    ("方案一A 不含总部投入；方案一B 增加 1 名直播督导、培训、门店设备补贴，开播提成默认由门店承担（可切换）；方案二在一B 基础上增加 4 人团队、设备、场地、投流，并可抵减现有品牌预算；方案二+ 在方案二基础上加入配套机制（团队直播间订单的总部分成提高、门店分担投流）；方案三为服务商代播参照。", F_LABEL),
    ("门店端净收益变化 = 增量间夜 × 单夜贡献 − 替代间夜 × 单夜损失 − 门店直播时间成本。", F_LABEL),
    ("", F_LABEL),
    ("数据来源与核验状态", F_BOLD),
    ("决策人提供的事实见假设表说明列；研究参数的来源见决策文档附录 C 与 research_notes 目录。", F_LABEL),
    ("外部参数来自 2026 年 11 月 4 日的网络检索结果，原文未能再次打开核对（会话网络策略限制），独立交叉核验未能执行；决策文档附录 D 列出了 14 条建议会前核对的事实。核对后只需改假设表的对应单元格。", F_LABEL),
]
for i, (t, f) in enumerate(lines, 1):
    c = ws.cell(row=i, column=1, value=t); c.font = f; c.alignment = ALIGN_L
ws.column_dimensions["A"].width = 120

# ---------------- 定价对比（稳态月度，基准，当前门店数，门店自播产出）----------------
ws = ws_p
ws["A1"] = "定价对比：三档定价的稳态月度比较（基准情景，当前 30 家店，门店自播产出）"; ws["A1"].font = F_H1
ws["A2"] = "同一套门店直播产出下，只改价格与销量系数。行为公式，列为三档定价；是否工作日券按假设表开关。"; ws["A2"].font = F_NOTE
hdr = ["项目", "九折券", "平价券", "平价加权益券"]
for j, h in enumerate(hdr, 1):
    c = ws.cell(row=4, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
r = 5
PR = {}
def prow(key, label, fns, fmt=FMT_INT, bold=False):
    global r
    ws.cell(row=r, column=1, value=label).font = F_BOLD if bold else F_LABEL
    for j, f in enumerate(fns, 2):
        c = ws.cell(row=r, column=j, value=f); c.number_format = fmt; c.alignment = ALIGN_R; c.font = F_BOLD if bold else F_CALC
    PR[key] = r; r += 1
tiers = [("P1", "C"), ("P2", "D"), ("P3", "E")]
INCREF = f"IF({A_base('WEEKDAY_ONLY')}=1,'单位经济'!{{c}}$26,'单位经济'!{{c}}$25)"
prow("price", "券价", [f"={A_base(t+'_PRICE')}" for t, _ in tiers], FMT_DEC)
prow("vol", "销量系数", [f"={A_base(t+'_VOL')}" for t, _ in tiers], FMT_DEC)
prow("v", "月售出券数（全系统）", [f"={A_base('BASE_HQ_COMM')}/{A_base('HQ_TAKE')}/{A_base('BASE_REDEEM_EST')}/{A_base('P1_PRICE')}*{A_base(t+'_VOL')}" for t, _ in tiers])
prow("sold", "月售出 GMV", [f"=B{PR['v']}*B{PR['price']}".replace("B", colL) for colL in "BCD"])
prow("n", "月核销间夜", [f"={colL}{PR['v']}*{A_base('REDEEM')}" for colL in "BCD"])
prow("red", "月核销 GMV", [f"={colL}{PR['n']}*{colL}{PR['price']}" for colL in "BCD"])
prow("inc", "增量比例", [f"={INCREF.format(c=uc)}" for _, uc in tiers], FMT_PCT)
prow("hq", "总部月增量收入", [f"={colL}{PR['n']}*('单位经济'!{uc}$10-(1-{colL}{PR['inc']})*'单位经济'!{uc}$18)" for colL, (_, uc) in zip("BCD", tiers)], bold=True)
prow("store", "门店端月净收益变化（全系统，不含直播时间成本）", [f"={colL}{PR['n']}*({colL}{PR['inc']}*'单位经济'!{uc}$14-(1-{colL}{PR['inc']})*'单位经济'!{uc}$19)" for colL, (_, uc) in zip("BCD", tiers)], bold=True)
prow("sys", "系统合计", [f"={colL}{PR['hq']}+{colL}{PR['store']}" for colL in "BCD"], bold=True)
prow("perstore", "单店月净收益变化", [f"={colL}{PR['store']}/{A_base('STORES0')}" for colL in "BCD"])
prow("cust", "客人相对 OTA 挂牌价的节省（每夜）", [f"={A_base('ADR')}-{colL}{PR['price']}" for colL in "BCD"], FMT_DEC)
r += 1
ws.cell(row=r, column=1, value="定性因素").font = F_BOLD; r += 1
qual = [
    ("OTA 最低价规则风险", "高：券价明显低于 OTA 展示价", "低：与 OTA 展示价持平", "低：价格持平，权益不构成价格违规"),
    ("加盟店接受度", "低：替代间夜每夜少赚约 9 元", "高：替代间夜基本无损", "中高：权益有少量成本"),
    ("直播间转化难度", "低：有明显折扣锚点", "高：没有折扣理由", "中：用权益和灵活兑换做卖点"),
    ("对周末满房的影响", "需配合工作日券或不可用日期", "影响小", "影响小"),
]
for lab, a, b, cc in qual:
    ws.cell(row=r, column=1, value=lab).font = F_LABEL
    for j, v in enumerate([a, b, cc], 2):
        c = ws.cell(row=r, column=j, value=v); c.font = F_LABEL; c.alignment = ALIGN_L
    r += 1
ws.column_dimensions["A"].width = 46
for col in "BCD": ws.column_dimensions[col].width = 30

out = sys.argv[1] if len(sys.argv) > 1 else "/home/user/CC/douyin-live/model/住小叮抖音直播财务模型.xlsx"
wb.save(out)
print("saved", out)
print(json.dumps({"params": len(ADDR)}, ensure_ascii=False))
