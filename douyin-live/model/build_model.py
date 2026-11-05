# -*- coding: utf-8 -*-
"""
住小叮抖音直播方案 财务模型生成器
生成 douyin-live/model/住小叮抖音直播财务模型.xlsx
所有计算用公式，参数集中在"假设"表，蓝色为可改输入。
"""
import sys, json, os
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
P("NEW_OCC1", "新店开业第 1 个月入住率", [0.4, 0.5, 0.6], "%", "假设：新店爬坡，需用北京既有新店前 3 个月的实际入住率替换", FMT_PCT)
P("NEW_OCC2", "新店开业第 2 个月入住率", [0.6, 0.7, 0.75], "%", "假设", FMT_PCT)
P("NEW_OCC3", "新店开业第 3 个月入住率", [0.75, 0.8, 0.85], "%", "假设；第 4 个月起按平均入住率", FMT_PCT)
P("ADR", "平均挂牌房价", 100, "元/晚", "决策人提供", FMT_INT)
P("OCC", "平均入住率", 0.85, "%", "决策人：85% 以上，很多门店 90% 以上", FMT_PCT)
P("DAYS", "每月天数", 30, "天", "简化口径", FMT_INT)
P("OTA_SHARE", "OTA 渠道间夜占比", 0.85, "%", "假设；其余为直订或上门，不付佣金", FMT_PCT, key_cell=True)
P("OTA_COMM", "OTA 佣金率", 0.08, "%", "决策人提供：携程、美团约 8%", FMT_PCT)
P("OTA_CTRL", "OTA 平台控价比例", 0.04, "%", "决策人提供：4% 由平台控制，酒店收不到", FMT_PCT)
P("MGMT_FEE", "总部管理费率", 0.035, "%", "决策人提供：流水的 3.5%；计费基数由“管理费计费基数”开关选择（1 = 客人支付金额，0 = 门店到账），抖音单同样计提", FMT_PCT)
P("VAR_COST", "单间夜变动成本", [15, 12, 10], "元", "假设：清洁、布草、水电、耗材；4 平米无独卫房型；需公司用实际成本替换", FMT_DEC, key_cell=True)
P("MGR_SALARY", "店长月薪", 10000, "元/月", "决策人提供：约 1 万，记在门店损益", FMT_INT)
P("WORK_HOURS", "店长月标准工时", 176, "小时", "按 22 天 × 8 小时", FMT_INT)

S("二、抖音平台与通兑券（决策人提供与研究）")
P("DY_FEE", "抖音平台综合费率", 0.08, "%", "决策人提供：平台 8%；住宿类目费率 2024-07-01 起由 4.5% 升至 8%；核验（2026-11-05）：商家后台显示的 8% 为综合费率 = 7.4% 团购服务费 + 0.6% 支付手续费", FMT_PCT)
P("DY_PAY_FEE", "抖音支付手续费（8% 之外另扣部分）", 0.0, "%", "核验：0.6% 支付手续费已包含在公示的 8% 综合费率内，不在 8% 之外另收，故默认 0；若财务结算单显示另扣，改为 0.006", FMT_PCT, key_cell=True)
P("HQ_TAKE", "总部分成", 0.04, "%", "决策人提供：总部 4%，门店到账 88%", FMT_PCT)
P("REDEEM", "核销率", [0.45, 0.55, 0.65], "%", "决策人估计 60%；行业参照：酒旅团购核销率不足 50%（虎嗅 2026-03）、国信证券估算约 30%（含达人与度假囤券）、搜索型 68% 到 75%；三份核验建议基准 50% 到 55%，取 55%，公司自估落在基准与乐观之间；以来客后台成熟批次数据替换", FMT_PCT, key_cell=True)
P("LAG0", "核销时间分布：售出当月", 0.5, "%", "假设：90 天有效期下的核销节奏", FMT_PCT)
P("LAG1", "核销时间分布：次月", 0.3, "%", "假设", FMT_PCT)
P("LAG2", "核销时间分布：第三月", 0.2, "%", "假设", FMT_PCT)
P("SOLDOUT_ANY", "不限日期券核销落在满房日的比例", [0.35, 0.30, 0.25], "%", "决策人：周末基本满房，约 9 晚/30 天；券用户偏好周末，取略高", FMT_PCT, key_cell=True)
P("SOLDOUT_WD", "工作日券核销落在满房日的比例", [0.08, 0.05, 0.03], "%", "假设：周日至周四可用，偶有满房", FMT_PCT)
P("CAP_SHARE", "抖音增量间夜可占用的空房比例上限", [0.6, 0.7, 0.8], "%", "假设：空房集中在平日，抖音增量不可能把全部空房填满；增量间夜 = MIN(核销间夜 × 增量比例, 空房间夜 × 该比例)", FMT_PCT)
P("INC_DECAY", "增量比例随份额递减：份额每高于基线 10 个百分点，增量比例相对下降", [0.4, 0.2, 0.1], "%", "假设：份额越高，新增的抖音买家中本来就会订本品牌的比例越高（选择效应）；下限见下一行；12 个月内影响小，主要约束份额情景表", FMT_PCT)
P("INC_FLOOR", "增量比例相对基线的下限", 0.4, "倍", "假设：递减后不低于基线增量比例的 40%", FMT_DEC)
P("WOULD_BOOK", "抖音买家中原本就会订本品牌的比例", [0.7, 0.5, 0.35], "%", "关键假设：替代率核心。参照：度假与高星酒店直播核销客新客占比 71% 到 80%（洲际 2026、Club Med 2025）；经济型连锁按平日核销中 50% 为真实增量（区间 40% 到 70%）推断；叠加满房日后不限日期券总体增量约 35%（情景区间 20% 到 49%）", FMT_PCT, key_cell=True)
P("BASE_HQ_COMM", "上月总部抖音相关收入（实际）", 40000, "元", "决策人提供：上月总部抖音收入 4 万；按 7% 份额校准时对应「4% 分成 + 3.5% 管理费」合计约 7.5% × 核销 GMV（见说明表的口径核对）；仅校准方式 2 用它倒推", FMT_INT)
P("SHARE0", "当前抖音核销间夜占系统间夜比例", 0.07, "%", "决策人提供：当前抖音订单占比约 7%；校准方式 1 用它定基线", FMT_PCT, key_cell=True)
P("SHARE_VPO", "份额口径换算：每个抖音订单对应的间夜数", 1.0, "倍", "决策人的 7% 为「订单占比」；若一个抖音订单平均含多张券或多晚，填实际倍数（例如 1.5）把订单份额换算为间夜份额；默认 1", FMT_DEC)
P("N0_ACTUAL", "实测当前每月抖音核销间夜（校准方式 3 用）", 0, "间夜", "从来客后台导出上月核销券数后填入；校准方式 3 直接用它定基线", FMT_INT)
P("HQ40K_BASIS", "上月 4 万的口径（仅用于校验行）", 2, "开关", "1 = 纯 4% 核销分成；2 = 4% 分成 + 3.5% 管理费合计；3 = 4% 按售出（支付）计提。只影响「校准核对」行，不驱动计算", FMT_INT)
P("CAL_MODE", "基线校准方式", 1, "开关", "1 = 按 7% 份额 × 每订单间夜数校准（默认）；2 = 按上月 4 万 ÷ 4% 倒推核销 GMV（旧口径，份额约 14.5%）；3 = 按实测核销间夜", FMT_INT, key_cell=True)
P("PAYBACK_RULE", "回本规则：含固定人头的方案（月）", 3, "月", "决策人：12 个月才能回本一定不投；本文建议含固定人头（不可逆）的投入以 3 个月为通过线：相对现状延续的总部累计净现金在第 N 月转正且此后不再转负", FMT_INT, key_cell=True)
P("PAYBACK_RULE_VAR", "回本规则：零固定成本的方案（月）", 6, "月", "按单付费、现有人员兼任等可随时停止的投入，以 6 个月为通过线", FMT_INT, key_cell=True)
P("TROUGH_RULE", "回本规则：允许的现金谷底（元）", -100000, "元", "相对现状延续的累计净现金最低点不得低于此值（约为当前总部一年抖音分成的三分之一）", FMT_INT)
P("PESS_LOSS_RULE", "回本规则：悲观情景 12 个月允许的最大亏损（元）", -50000, "元", "悲观情景相对现状延续的 12 个月累计净现金不得低于此值", FMT_INT)
P("PRESALE_V", "每家新店开业预售券数（总部主导直播）", [150, 300, 500], "张/店", "关键假设：新店开业前后由总部直播间与按单付费主播预售，新店爬坡期空房多，这部分是最接近纯增量的间夜；参照华住等集团的开业预售做法，数值为假设", FMT_INT, key_cell=True)
P("PRESALE_ON", "是否启用新店开业预售", 1, "开关", "1 = 总部主导方案在新店开业当月预售；0 = 关闭（用于看预售贡献）", FMT_INT)
P("PRESALE_INC", "新店预售券的增量比例", [0.7, 0.85, 1.0], "%", "新店开业前三个月入住率低，预售间夜大部分填补空房；仍受空房上限约束", FMT_PCT)
P("STORE_HOURS", "门店每月直播小时数", [20, 16, 12], "小时/店/月", "假设：每周 2 场 × 2 小时", FMT_INT)
P("WEEKDAY_VOL", "改为工作日券后的销量系数", [0.75, 0.85, 0.95], "倍", "关键假设：取消周五周六可用会流失偏好周末的买家；按不限日期券核销落在满房日的比例（约 30%）为上限校准，建议用后台周末核销占比替换", FMT_DEC, key_cell=True)

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
P("A_DRIFT", "现状延续：单店产出月变化率", [-0.03, 0.0, 0.01], "%/月", "假设：无总部支持时，悲观按新鲜感衰减与人员流动每月 -3%，基准持平，乐观略增；上月是唯一数据点，无趋势信息", FMT_PCT, key_cell=True)
P("AP_DRIFT", "规范化后：单店产出月变化率", [-0.01, 0.0, 0.01], "%/月", "假设：有督导与激励时基本稳定", FMT_PCT)
P("AP_UPLIFT", "规范化后单店产出提升倍数", [1.15, 1.3, 1.5], "倍", "关键假设：培训、SOP、激励带来的提升；研究区间见文档", FMT_DEC, key_cell=True)
P("AP_RAMP", "提升达成所需月数", [4, 3, 2], "月", "假设", FMT_INT)
P("AP_UPLIFT_LITE", "无专职督导（现有人员兼任）时的提升倍数", [1.10, 1.20, 1.35], "倍", "假设：兼任督导的效果取专职版的约三分之二；无外部证据，第一阶段用实测替换", FMT_DEC, key_cell=True)
P("PART", "门店参与率（签署协议且不关库存的门店比例）", [0.9, 1.0, 1.0], "%", "关键假设：不签参与协议的门店退出通兑券，其现有产出一并消失；基准按全部参与", FMT_PCT, key_cell=True)
P("PART_MIN", "门店约束：最低参与率", 0.8, "%", "规则：参与率低于此值视为机制未成立", FMT_PCT)
P("STORE_MIN_GAIN", "门店约束：门店每抖音间夜最低期望收益", 0, "元", "规则：12 个月门店端净收益变化 ÷ 核销间夜不低于此值（0 = 不亏即可；加盟谈判经验值可填 10）", FMT_DEC)
P("SUP_HIRE", "一B 是否新增直播督导岗", 0, "开关", "1 = 新招 1 名直播督导（固定成本）；0 = 由运营部现有人员（抖音运营副总监与片区负责人）兼任，不增加现金成本（默认，符合回本规则）", FMT_INT, key_cell=True)
P("AP_SUP_SALARY", "直播督导月薪（若新招，1 人）", [14000, 12500, 12500], "元/月", "北京抖音直播运营 55.3% 在 8,000 到 15,000 元，1 到 3 年经验约 1.27 万元（职友集近一年统计，截至 2026-11-05）；督导取区间上端", FMT_INT)
P("SOCIAL", "社保公积金等综合系数", 0.42, "%", "北京 2025 年度单位社保约 26.3% + 工伤 + 公积金 5% 到 12%，法定附加约 31.5% 到 40%，加招聘培训等杂项取全口径 1.42；社保基数 2025 年度 7,162 到 35,811 元、2026 年 7 月起 7,270 到 36,348 元，最低工资 2,540 元（已核对人社局原文）", FMT_PCT)
P("AP_TRAIN_ONEOFF", "一次性培训与 SOP 建设", 20000, "元", "假设：外部讲师、话术库、脚本", FMT_INT)
P("AP_TRAIN_MONTHLY", "每月持续培训与巡检", 3000, "元/月", "假设", FMT_INT)
P("AP_STORE_KIT", "每店直播设备补贴（总部承担部分）", 0, "元/店", "补光灯、支架、麦克风约 800 元/店，建议门店自购；若总部补贴填 800", FMT_INT)
P("AP_COMM", "开播门店或员工提成（按核销 GMV）", 0.025, "%", "行业建议员工直播提成按核销计 2% 到 5%，跨店来源奖励 1% 到 3%；按核销而非售出计提，避免为过期退款的券付提成", FMT_PCT, key_cell=True)
P("COMM_BY_STORE", "提成由门店承担的比例", 1.0, "%", "机制设计：提成从核销门店到账中划转，总部只做清分；设 0 则由总部从 4% 分成中支付", FMT_PCT, key_cell=True)
P("MKT_FEE", "品牌营销费率（按门店全渠道流水向门店收取）", 0.0, "%", "决策人：传统酒店连锁向门店收取 0.5% 到 1% 的营销费，用于品牌部与渠道投入；默认 0，变体按 0.5% 与 1% 测算；对所有方案（含现状延续）同样适用，是独立于直播方案的机制决策", FMT_PCT, key_cell=True)
P("MKT_FEE_START", "品牌营销费开始月份", 1, "第几月", "假设：随参与协议同步生效", FMT_INT)
P("CH_FEE", "渠道运营费（按门店抖音核销 GMV 向门店收取）", 0.0, "%", "机制选项：总部为覆盖督导、培训、清分成本向参与门店收取的渠道费，默认 0；文档测算 1% 的情形；现状延续不收", FMT_PCT, key_cell=True)
P("COMM_TO_STAFF", "提成中付给员工的比例", 1.0, "%", "付给开播员工的部分是全系统的真实成本；门店之间的划转在全系统口径下抵销。默认全部付给员工（保守）", FMT_PCT)

S("五、方案二：总部直播团队（含门店赋能）")
P("MECH_ON", "总部主导订单是否执行提高分成（8%）", 1, "开关", "1 = 总部直播间、按单付费主播与投流带来的订单总部分成按下方「总部主导订单分成」执行；0 = 仍按 4%", FMT_INT, key_cell=True)
P("PILOT_START", "总部直播试点开播月份", 2, "第几月", "第 1 月筹备（账号、脚本、设备），第 2 月开播", FMT_INT)
P("PILOT_HOURS", "试点每月开播小时（现有品牌人员）", [40, 60, 80], "小时/月", "假设：品牌营销人员每周 3 到 5 场、每场 3 到 4 小时；不新增人力", FMT_INT)
P("PILOT_GPH", "试点成熟期每小时售出 GMV（九折口径）", [1500, 2500, 3500], "元/小时", "关键假设：比专职团队低（兼顾品牌工作、无投流）；参照门店自播与同业冷启动区间", FMT_INT, key_cell=True)
P("PILOT_RAMP", "试点达到成熟所需月数", 3, "月", "假设", FMT_INT)
P("PILOT_EQUIP", "试点设备一次性投入", 15000, "元", "手机、灯光、声卡、背景；独立来源显示 1 到 2 万元即可", FMT_INT)
P("PILOT_CONTENT", "试点每月内容与杂费", 3000, "元/月", "假设：从现有品牌预算内调剂，若视为新增成本则计入", FMT_INT)
P("V_START", "按单付费主播开播月份", 3, "第几月", "试点跑通后，第 3 月起引入兼职主播或达人按单付费", FMT_INT)
P("V_HOURS", "按单付费主播每月开播小时", [60, 100, 150], "小时/月", "假设：2 到 4 名兼职主播轮播；按人数可调", FMT_INT)
P("V_GPH", "按单付费主播成熟期每小时售出 GMV（九折口径）", [2000, 3000, 4000], "元/小时", "关键假设：兼职或达人主播有带货经验，略高于试点、低于专职团队", FMT_INT, key_cell=True)
P("V_RAMP", "按单付费主播达到成熟所需月数", 3, "月", "假设", FMT_INT)
P("V_COMM", "按单付费主播佣金（按核销 GMV，从门店到账中划转）", [0.15, 0.12, 0.10], "%", "达人与兼职主播常见佣金 10% 到 20%；按核销结算，不占用总部现金", FMT_PCT, key_cell=True)
P("V_COMM_HQ_SHARE", "按单付费主播佣金中由总部承担的比例", 0.0, "%", "默认 0：佣金全部由核销门店从到账中划转；若总部分担部分佣金填比例", FMT_PCT)
P("VH_HOURS", "方案二H：总部付费主播每月开播小时", [40, 60, 80], "小时/月", "后备结构：门店不接受付佣时由总部按小时付费", FMT_INT)
P("HOST_HOURLY", "方案二H：兼职主播时薪", [150, 135, 120], "元/小时", "北京本地生活兼职主播 120 到 150 元/小时（研究笔记 03）", FMT_INT)
P("VH_COMM", "方案二H：主播低提成（按核销 GMV，总部承担）", 0.02, "%", "假设", FMT_PCT)
P("V_COORD", "按单付费模式总部协调成本", [3000, 2000, 1000], "元/月", "假设：排班、素材、结算清分的杂费；人力由现有品牌与运营人员兼任", FMT_INT)
P("B_START", "团队到位月份", 2, "第几月", "第 1 月招聘，第 2 月开播", FMT_INT)
P("B_RECRUIT", "一次性招聘费用", 10000, "元", "假设", FMT_INT)
P("B_SAL_LEAD", "直播运营负责人月薪", [15000, 13000, 13000], "元/月", "北京抖音直播运营 55.3% 在 8,000 到 15,000 元（职友集近一年统计）；负责人取区间上端略高", FMT_INT)
P("B_SAL_HOST", "主播月薪（底薪）", [10000, 8000, 8000], "元/月", "北京抖音主播 55.8% 在 1 万到 2 万元（职友集近一年统计，111 份样本）；招聘标价 7,000 到 13,000 元为检索摘录；底薪取下端，另有提成", FMT_INT)
P("B_SAL_CTRL", "中控兼剪辑月薪", [9000, 8000, 8000], "元/月", "北京直播中控约 9,200 元，全国 73.1% 在 4,500 到 8,000 元（职友集近一年统计）；剪辑 8,000 到 15,000 元", FMT_INT)
P("B_SAL_ADS", "投手兼内容月薪", [14000, 12000, 12000], "元/月", "北京千川投手 72.7% 在 1 万到 2 万元（职友集近一年统计，2025 年较 2024 年下降 7%）；兼内容取中位", FMT_INT)
P("B_HOST_COMM", "主播提成（按总部直播间核销 GMV）", 0.02, "%", "行业主播提成底薪 + 核销 GMV 1% 到 5%", FMT_PCT)
P("B_BACKUP_HOST", "兼职备播主播月费", [4000, 3000, 2000], "元/月", "北京本地生活兼职主播 120 到 150 元/小时，按每月约 20 小时；用于轮班与主播流失时顶岗", FMT_INT)
P("B_EQUIP", "直播设备一次性投入", 35000, "元", "办公室绿幕方案：手机或相机、灯光、声卡、采集卡、绿幕；网上含税清单约 4.7 万（2025，来源页面未能打开核对）、企业进阶清单 0.85 到 1.5 万；取 3.5 万，属内部估算（独立来源：1 到 2 万元即可达到高画质标准，3.5 万偏保守）", FMT_INT)
P("B_EQUIP_MONTHS", "设备摊销月数", 12, "月", "仅 EQUIP_CASH = 0 时使用", FMT_INT)
P("EQUIP_CASH", "设备按现金在开播月一次性计入", 1, "开关", "1 = 回本按现金口径，设备在开播当月全额计入（默认）；0 = 按摊销月数分摊", FMT_INT)
P("B_SPACE", "场地与杂费", 3000, "元/月", "假设：办公室内搭建", FMT_INT)
P("B_HOURS", "总部直播间每月开播小时", [100, 120, 140], "小时/月", "品牌自播常见要求每周 6 天、每天 5 小时以上；冷启动 1 到 2 班每班 6 小时", FMT_INT)
P("B_GPH_START", "开播首月每小时售出 GMV（九折口径）", 1000, "元/小时", "假设：冷启动期；参照某品牌测试期第 3 个月单场 6 小时产出 7,000 元后放量", FMT_INT)
P("B_GPH_MATURE", "成熟期每小时售出 GMV（九折口径）", [2500, 4000, 6000], "元/小时", "关键假设。参照：丽枫门店店总直播 8 小时近 10 万（中端，按客单价折算经济型 1/3 到 1/5 约 2,500 到 4,000/小时）；尚客优区域总部首场 2.8 万", FMT_INT, key_cell=True)
P("B_RAMP", "达到成熟所需月数", [6, 4, 3], "月", "开播首月按起点值，此后线性爬坡，开播后第 N 个月达到成熟（行业经验：起号 1 到 3 个月、见效 3 到 6 个月）", FMT_INT)
P("B_ADS", "月投流预算", [20000, 30000, 50000], "元/月", "本地生活经验：投流占支付 GMV 10% 到 20%；冷启动 0.5 到 2 万/月", FMT_INT)
P("B_ROI", "投流 ROI（售出 GMV / 投流）", [3, 5, 7], "倍", "关键假设。无酒旅权威基准：温泉酒店案例 3 到 6.8；餐饮服务商保底目标 10；总部独自承担投流的保本 ROI 约 33（不计主播提成）", FMT_DEC, key_cell=True)
P("B_ADS_START", "投流开始月份", [3, 2, 2], "第几月", "假设", FMT_INT)
P("B_CANNIB", "总部直播间对门店自播的挤占比例", [0.25, 0.15, 0.1], "%", "假设：总部直播间每卖 1 张券，门店自播少卖的张数；同一抖音流量池", FMT_PCT)
P("BRAND_BUDGET", "现有品牌营销月预算", 20000, "元/月", "决策人提供", FMT_INT)
P("B_HQ_TAKE_ROOM", "总部主导订单的总部分成（方案二+、试点、按单付费）", 0.08, "%", "机制设计：谁投入谁分成；总部直播间、按单付费主播与投流带来的订单总部分成从 4% 提至 8%，门店到账 84%", FMT_PCT, key_cell=True)
P("B_ADS_STORE_SHARE", "方案二+：门店分担投流的比例", 0.5, "%", "机制设计：投流基金由门店按抖音到账分担一半；按总部直播间订单的核销到账折算", FMT_PCT, key_cell=True)
P("BRAND_SALARY", "现有品牌营销人员月薪", 10000, "元/月", "假设：决策人未提供", FMT_INT)

S("六、方案三：外包服务商（参照）")
P("C_START", "服务商开播月份", 2, "第几月", "假设", FMT_INT)
P("C_RETAINER", "服务商月固定服务费", [15000, 8000, 5000], "元/月", "酒旅代运营：基础服务费 4 到 5 万/年或月维护费 6,000 元；带货型 3 到 8 万/月；取中低档", FMT_INT)
P("C_COMM", "服务商佣金（按售出 GMV）", [0.12, 0.10, 0.08], "%", "酒旅代运营佣金 8% 到 12%（观点指数 2024）、10% 到 15%（服务商自述）", FMT_PCT)
P("C_HOURS", "服务商每月代播小时", [80, 90, 100], "小时/月", "参照服务商约 1.2 场/日，每场 2 到 3 小时；每小时产出与爬坡按总部直播间同一假设，保证参照公允", FMT_INT)
P("C_RAMP", "服务商达到成熟所需月数", 3, "月", "假设", FMT_INT)
P("C_ADS", "服务商要求的月投流预算", 20000, "元/月", "假设；投流代运营另收消耗 10% 到 20%", FMT_INT)
P("C_ROI", "服务商投流 ROI", [3, 4, 5], "倍", "假设", FMT_DEC)

S("七、开关（1 = 开，0 = 关；定价 1/2/3）")
P("PRICING_SEL", "月度模型采用的定价档", 1, "档", "1 = 九折，2 = 平价，3 = 平价加权益", FMT_INT, key_cell=True)
P("WEEKDAY_ONLY", "是否改为工作日券（周日至周四）", 1, "开关", "1 = 是：核销落在满房日的比例取工作日券口径", FMT_INT, key_cell=True)
P("ABSORB_BRAND", "方案二是否抵减现有品牌预算与人员", 0, "开关", "1 = 现有品牌营销人员派驻进团队、月预算转为直播内容预算，计入抵减；0 = 品牌部保留原预算与人员，团队成本不抵减", FMT_INT, key_cell=True)
P("MGMT_BASE", "管理费计费基数", 1, "开关", "1 = 按客人支付金额（流水）计提 3.5%，与决策人口径一致；0 = 按门店到账金额计提", FMT_INT, key_cell=True)

# ---------------- 参数覆盖（变体工作簿，用 OVERRIDES 环境变量传 JSON，如 {"B_START":[5,5,5]}） ----------------
_ov = json.loads(os.environ.get("OVERRIDES", "{}"))
for _p in PARAMS:
    if "key" in _p and _p["key"] in _ov:
        v = _ov[_p["key"]]
        _p["values"] = list(v) if isinstance(v, (list, tuple)) else [v, v, v]

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
ws_dec = wb.create_sheet("总部决策")
ws_sh = wb.create_sheet("份额情景")
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
     f"=C5*({A_base('DY_FEE')}+{A_base('DY_PAY_FEE')})", f"=D5*({A_base('DY_FEE')}+{A_base('DY_PAY_FEE')})", f"=E5*({A_base('DY_FEE')}+{A_base('DY_PAY_FEE')})"); r += 1
urow(r, "总部分成", "=0", f"=C5*{A_base('HQ_TAKE')}", f"=D5*{A_base('HQ_TAKE')}", f"=E5*{A_base('HQ_TAKE')}"); r += 1
urow(r, "门店到账", "=B5-B6-B7", "=C5-C6-C7", "=D5-D6-D7", "=E5-E6-E7"); r += 1
urow(r, "总部管理费（3.5%，基数按开关）", f"=IF({A_base('MGMT_BASE')}=1,B5,B8)*{A_base('MGMT_FEE')}", f"=IF({A_base('MGMT_BASE')}=1,C5,C8)*{A_base('MGMT_FEE')}", f"=IF({A_base('MGMT_BASE')}=1,D5,D8)*{A_base('MGMT_FEE')}", f"=IF({A_base('MGMT_BASE')}=1,E5,E8)*{A_base('MGMT_FEE')}"); r += 1
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
    D("VOL_EFF", "有效销量系数（含工作日券折减）", f"={L['VOL']}*IF({L['WEEKDAY_ONLY']}=1,{L['WEEKDAY_VOL']},1)")
    D("STORE_RATE", "门店到账比例", f"=1-{L['DY_FEE']}-{L['DY_PAY_FEE']}-{L['HQ_TAKE']}", FMT_PCT)
    D("DY_FEE_RATE", "抖音间夜管理费占券价比例", f"=IF({L['MGMT_BASE']}=1,{L['MGMT_FEE']},{L['STORE_RATE']}*{L['MGMT_FEE']})", '0.00%')
    D("DY_STORE_NET", "抖音间夜门店净得", f"={L['PRICE']}*({L['STORE_RATE']}-{L['DY_FEE_RATE']})")
    D("DY_HQ_NIGHT", "抖音间夜总部收入", f"={L['PRICE']}*({L['HQ_TAKE']}+{L['DY_FEE_RATE']})")
    D("OTA_FEE_NIGHT", "OTA 间夜总部管理费", f"=IF({L['MGMT_BASE']}=1,{L['ADR']},{L['ADR']}*(1-{L['OTA_CTRL']})*(1-{L['OTA_COMM']}))*{L['MGMT_FEE']}")
    D("CF_STORE_NET", "被替代间夜门店净得（加权）", f"={L['OTA_SHARE']}*({L['ADR']}*(1-{L['OTA_CTRL']})*(1-{L['OTA_COMM']})-{L['OTA_FEE_NIGHT']})+(1-{L['OTA_SHARE']})*{L['ADR']}*(1-{L['MGMT_FEE']})")
    D("CF_HQ_NIGHT", "被替代间夜总部收入（加权）", f"={L['OTA_SHARE']}*{L['OTA_FEE_NIGHT']}+(1-{L['OTA_SHARE']})*{L['ADR']}*{L['MGMT_FEE']}")
    D("INC", "增量比例（按开关）", f"=(1-IF({L['WEEKDAY_ONLY']}=1,{L['SOLDOUT_WD']},{L['SOLDOUT_ANY']}))*(1-{L['WOULD_BOOK']})", FMT_PCT)
    D("INC_ANY", "增量比例（不限日期券，现状口径）", f"=(1-{L['SOLDOUT_ANY']})*(1-{L['WOULD_BOOK']})", FMT_PCT)
    D("STORE_INC_CONTRIB", "增量一夜门店贡献", f"={L['DY_STORE_NET']}-{L['PERK']}-{L['VAR_COST']}")
    D("STORE_SUB_LOSS", "替代一夜门店损失", f"={L['CF_STORE_NET']}-{L['DY_STORE_NET']}+{L['PERK']}")
    D("BASE_RED0", "基线：当前每月抖音核销 GMV", f"=CHOOSE({L['CAL_MODE']},{L['SHARE0']}*{L['SHARE_VPO']}*{L['STORES0']}*{L['ROOMS']}*{L['OCC']}*{L['DAYS']}*{L['P1_PRICE']},{L['BASE_HQ_COMM']}/{L['HQ_TAKE']},{L['N0_ACTUAL']}*{L['P1_PRICE']})", FMT_INT)
    D("CAL_IMPLIED_RED", "校准核对：按「上月 4 万口径」隐含的月核销 GMV", f"={L['BASE_HQ_COMM']}/CHOOSE({L['HQ40K_BASIS']},{L['HQ_TAKE']},{L['HQ_TAKE']}+{L['MGMT_FEE']},{L['HQ_TAKE']}/{L['REDEEM']})", FMT_INT)
    D("CAL_IMPLIED_SHARE", "校准核对：隐含的间夜份额", f"={L['CAL_IMPLIED_RED']}/{L['P1_PRICE']}/({L['STORES0']}*{L['ROOMS']}*{L['OCC']}*{L['DAYS']})", FMT_PCT)
    D("CAL_GAP", "校准缺口：隐含份额 ÷ 采用的份额 − 1（绝对值大于 20% 需核对）", f"={L['CAL_IMPLIED_SHARE']}/({L['SHARE0']}*{L['SHARE_VPO']})-1", FMT_PCT)
    D("UPLIFT_EFF", "规范化后实际采用的提升倍数（按是否新招督导）", f"=IF({L['SUP_HIRE']}=1,{L['AP_UPLIFT']},{L['AP_UPLIFT_LITE']})", FMT_DEC)
    D("BASE_SOLD0", "基线：对应的每月售出 GMV（按本情景核销率倒推）", f"={L['BASE_RED0']}/{L['REDEEM']}", FMT_INT)
    D("HQ_TAKE_M", "总部主导订单实际分成", f"=IF({L['MECH_ON']}=1,{L['B_HQ_TAKE_ROOM']},{L['HQ_TAKE']})", FMT_PCT)
    D("HQ_SUB_GAIN", "总部每替代间夜净得（4% 分成）", f"={L['DY_HQ_NIGHT']}-{L['CF_HQ_NIGHT']}")
    D("HQ_INC_GAIN", "总部每增量间夜净得（4% 分成）", f"={L['DY_HQ_NIGHT']}")
    D("HQ_SUB_GAIN_M", "总部每替代间夜净得（总部主导订单分成）", f"={L['HQ_SUB_GAIN']}+({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*{L['PRICE']}")
    D("HQ_INC_GAIN_M", "总部每增量间夜净得（总部主导订单分成）", f"={L['HQ_INC_GAIN']}+({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*{L['PRICE']}")
    D("HQ_PER_PT", "份额每提升 1 个百分点总部月净得（当前门店数，替代口径）", f"={L['STORES0']}*{L['ROOMS']}*{L['OCC']}*{L['DAYS']}*0.01*{L['HQ_SUB_GAIN']}", FMT_INT)
    D("HQ_MIX_GAIN", "总部每抖音间夜净得（混合口径，4%）", f"={L['INC']}*{L['HQ_INC_GAIN']}+(1-{L['INC']})*{L['HQ_SUB_GAIN']}")
    D("HQ_MIX_GAIN_M", "总部每抖音间夜净得（混合口径，总部主导分成）", f"={L['INC']}*{L['HQ_INC_GAIN_M']}+(1-{L['INC']})*{L['HQ_SUB_GAIN_M']}")
    D("HQ_PER_PT_MIX", "份额每提升 1 个百分点总部月净得（当前门店数，混合口径 4%）", f"={L['STORES0']}*{L['ROOMS']}*{L['OCC']}*{L['DAYS']}*0.01*{L['HQ_MIX_GAIN']}", FMT_INT)
    D("HQ_PER_PT_MIX_M", "份额每提升 1 个百分点总部月净得（当前门店数，混合口径 8%）", f"={L['STORES0']}*{L['ROOMS']}*{L['OCC']}*{L['DAYS']}*0.01*{L['HQ_MIX_GAIN_M']}", FMT_INT)
    D("BASE_VPS", "倒推单店月售出券数（九折）", f"={L['BASE_SOLD0']}/{L['P1_PRICE']}/{L['STORES0']}", FMT_DEC)
    D("MGR_HOURLY", "店长小时成本", f"={L['MGR_SALARY']}/{L['WORK_HOURS']}")
    D("TEAM_SAL", "团队月薪合计（含社保与兼职备播）", f"=({L['B_SAL_LEAD']}+{L['B_SAL_HOST']}+{L['B_SAL_CTRL']}+{L['B_SAL_ADS']})*(1+{L['SOCIAL']})+{L['B_BACKUP_HOST']}", FMT_INT)
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
    def ramp_gap(m, c, p, pp):
        if m == 0: return "=0"
        terms = [f"MAX(0,{L['OCC']}-{L['NEW_OCC1']})*{ref('newstores', c)}"]
        if m >= 2: terms.append(f"MAX(0,{L['OCC']}-{L['NEW_OCC2']})*{ref('newstores', p)}")
        if m >= 3: terms.append(f"MAX(0,{L['OCC']}-{L['NEW_OCC3']})*{ref('newstores', pp)}")
        return f"={L['ROOMS']}*{L['DAYS']}*(" + "+".join(terms) + ")"
    mrow("rampgap", "新店爬坡减少的间夜", "间夜", ramp_gap)
    mrow("nights", "系统间夜", "间夜", lambda m, c, p, pp: f"={ref('stores', c)}*{L['ROOMS']}*{L['OCC']}*{L['DAYS']}-{ref('rampgap', c)}")
    mrow("rev", "系统流水（挂牌口径）", "元", lambda m, c, p, pp: f"={ref('nights', c)}*{L['ADR']}")
    mrow("empty", "系统空房间夜（含新店爬坡期空房）", "间夜", lambda m, c, p, pp: f"={ref('stores', c)}*{L['ROOMS']}*(1-{L['OCC']})*{L['DAYS']}+{ref('rampgap', c)}")
    mrow("hqfee_base", "总部管理费基线（无抖音）", "元", lambda m, c, p, pp: f"={ref('nights', c)}*{L['CF_HQ_NIGHT']}")

    def option_block(code, title, vouch_fn, cost_fns, store_hours_fn, extra_income_fn=None, extra_store_fn=None, store_comm=False, inc_ref=None, oneoff_fn=None):
        """vouch_fn(m,c,p,pp) -> 售出券数公式（含子项行自行添加后再汇总）；若辅助行里已有 {code}_prev（新店预售券），自动按预售口径计算增量"""
        inc_ref = inc_ref or L['INC']
        presale = f"{code}_prev" in R
        section(title)
        if presale:
            def pren_fn(m, c, p, pp):
                if m == 0: return "=0"
                return f"={L['REDEEM']}*({L['LAG0']}*{ref(f'{code}_prev', c)}+{L['LAG1']}*{ref(f'{code}_prev', p)}+{L['LAG2']}*{ref(f'{code}_prev', pp)})"
            mrow(f"{code}_pren", "其中：新店预售券核销间夜", "间夜", pren_fn)
        mrow(f"{code}_v", "售出券数", "张", vouch_fn)
        mrow(f"{code}_sold", "售出 GMV（券面）", "元", lambda m, c, p, pp: f"={ref(f'{code}_v', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref(f'{code}_v', c)}*{L['PRICE']}")
        def redeem_fn(m, c, p, pp):
            if m == 0: return f"={L['BASE_RED0']}"
            return f"={L['REDEEM']}*({L['LAG0']}*{ref(f'{code}_sold', c)}+{L['LAG1']}*{ref(f'{code}_sold', p)}+{L['LAG2']}*{ref(f'{code}_sold', pp)})"
        mrow(f"{code}_red", "核销 GMV（结算口径）", "元", redeem_fn)
        def rednights_fn(m, c, p, pp):
            if m == 0: return f"={L['BASE_RED0']}/{L['P1_PRICE']}"
            return f"={L['REDEEM']}*({L['LAG0']}*{ref(f'{code}_v', c)}+{L['LAG1']}*{ref(f'{code}_v', p)}+{L['LAG2']}*{ref(f'{code}_v', pp)})"
        mrow(f"{code}_n", "核销间夜", "间夜", rednights_fn)
        mrow(f"{code}_share", "抖音份额（核销间夜 ÷ 系统间夜）", "%", lambda m, c, p, pp: f"={ref(f'{code}_n', c)}/{ref('nights', c)}", FMT_PCT)
        mrow(f"{code}_incr", "本月适用的增量比例（随份额递减）", "%", lambda m, c, p, pp: f"={inc_ref}*MAX({L['INC_FLOOR']},1-{L['INC_DECAY']}*MAX(0,{ref(f'{code}_share', c)}-{L['SHARE0']}*{L['SHARE_VPO']})/0.1)", FMT_PCT)
        if presale:
            mrow(f"{code}_inc", "其中：增量间夜（受空房上限约束；新店预售按预售增量比例）", "间夜", lambda m, c, p, pp: f"=MIN(({ref(f'{code}_n', c)}-{ref(f'{code}_pren', c)})*{ref(f'{code}_incr', c)}+{ref(f'{code}_pren', c)}*{L['PRESALE_INC']},{ref('empty', c)}*{L['CAP_SHARE']})")
        else:
            mrow(f"{code}_inc", "其中：增量间夜（受空房上限约束）", "间夜", lambda m, c, p, pp: f"=MIN({ref(f'{code}_n', c)}*{ref(f'{code}_incr', c)},{ref('empty', c)}*{L['CAP_SHARE']})")
        mrow(f"{code}_sub", "其中：替代间夜", "间夜", lambda m, c, p, pp: f"={ref(f'{code}_n', c)}-{ref(f'{code}_inc', c)}")
        mrow(f"{code}_hqc", "总部分成收入", "元", lambda m, c, p, pp: f"={ref(f'{code}_red', c)}*{L['HQ_TAKE']}")
        mrow(f"{code}_hqf", "总部管理费（抖音单）", "元", lambda m, c, p, pp: f"={ref(f'{code}_red', c)}*{L['DY_FEE_RATE']}")
        if store_comm:
            def storered_fn(m, c, p, pp):
                if m == 0: return f"={L['REDEEM']}*{ref(f'{code}_storesold', c)}"
                return f"={L['REDEEM']}*({L['LAG0']}*{ref(f'{code}_storesold', c)}+{L['LAG1']}*{ref(f'{code}_storesold', p)}+{L['LAG2']}*{ref(f'{code}_storesold', pp)})"
            mrow(f"{code}_storered", "其中：门店自播部分核销 GMV", "元", storered_fn)
        mrow(f"{code}_hqcf", "减：被替代订单原有管理费", "元", lambda m, c, p, pp: f"=-{ref(f'{code}_sub', c)}*{L['CF_HQ_NIGHT']}")
        mrow(f"{code}_hqx", "机制：总部主导订单加成分成（总部多得）", "元", extra_income_fn or (lambda m, c, p, pp: "=0"))
        mrow(f"{code}_chf", "机制：渠道运营费（向门店收取）", "元", (lambda m, c, p, pp: "=0") if code == "A" else (lambda m, c, p, pp: "=0" if m == 0 else f"={L['CH_FEE']}*{ref(f'{code}_red', c)}"))
        mrow(f"{code}_mkf", "机制：品牌营销费（按门店全渠道流水向门店收取）", "元", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['MKT_FEE_START']},{L['MKT_FEE']}*{ref('rev', c)},0)")
        mrow(f"{code}_hqpre", "其中：新店预售贡献的总部增量收入（归因，不重复计入）", "元", (lambda m, c, p, pp: "=0") if not presale else (lambda m, c, p, pp: "=0" if m == 0 else f"={ref(f'{code}_pren', c)}*({L['PRESALE_INC']}*{L['HQ_INC_GAIN_M']}+(1-{L['PRESALE_INC']})*{L['HQ_SUB_GAIN_M']})"))
        mrow(f"{code}_hqgross", "总部抖音收入合计（分成 + 管理费 + 加成 + 渠道费 + 营销费）", "元", lambda m, c, p, pp: f"={ref(f'{code}_hqc', c)}+{ref(f'{code}_hqf', c)}+{ref(f'{code}_hqx', c)}+{ref(f'{code}_chf', c)}+{ref(f'{code}_mkf', c)}")
        mrow(f"{code}_hqinc", "总部增量收入（扣被替代订单原有管理费）", "元", lambda m, c, p, pp: f"={ref(f'{code}_hqc', c)}+{ref(f'{code}_hqf', c)}+{ref(f'{code}_hqcf', c)}+{ref(f'{code}_hqx', c)}+{ref(f'{code}_chf', c)}+{ref(f'{code}_mkf', c)}", bold=True)
        has_led = f"{code}_hqred" in R
        mrow(f"{code}_brandinc", "其中：总部主导订单带来的总部收入（可归属品牌部：分成 + 管理费 − 被替代管理费）", "元", (lambda m, c, p, pp: "=0") if not has_led else (lambda m, c, p, pp: "=0" if m == 0 else f"={ref(f'{code}_hqred', c)}*({L['HQ_TAKE_M']}+{L['DY_FEE_RATE']})-{ref(f'{code}_hqred', c)}/{L['PRICE']}*(1-{ref(f'{code}_incr', c)})*{L['CF_HQ_NIGHT']}"))
        for ck, clabel, cfn in cost_fns:
            mrow(f"{code}_{ck}", clabel, "元", cfn)
        cost_keys = [f"{code}_{ck}" for ck, _, _ in cost_fns]
        mrow(f"{code}_cost", "总部成本合计", "元", lambda m, c, p, pp: "=" + "+".join(ref(k, c) for k in cost_keys), bold=True)
        mrow(f"{code}_oneoff", "其中：一次性现金（培训、设备补贴、设备、招聘）", "元", oneoff_fn or (lambda m, c, p, pp: "=0"))
        mrow(f"{code}_net", "总部增量净收益", "元", lambda m, c, p, pp: f"={ref(f'{code}_hqinc', c)}-{ref(f'{code}_cost', c)}", bold=True, fill=FILL_TOTAL)
        mrow(f"{code}_cum", "累计净收益（第 1 月起）", "元", lambda m, c, p, pp: "=0" if m == 0 else (f"={ref(f'{code}_net', c)}" if m == 1 else f"={ref(f'{code}_cum', p)}+{ref(f'{code}_net', c)}"))
        mrow(f"{code}_paid", "累计净收益已转正标记（本月起不再转负）", "", lambda m, c, p, pp: "=0" if m == 0 else f"=IF(MIN({c}{R[f'{code}_cum']}:{col_m(MONTHS)}{R[f'{code}_cum']})>=0,1,0)")
        mrow(f"{code}_cumrel", "相对现状延续的累计净收益", "元", lambda m, c, p, pp: "=0" if (m == 0 or code == "A") else f"={ref(f'{code}_cum', c)}-{ref('A_cum', c)}")
        mrow(f"{code}_paidrel", "相对现状已回本标记（本月起累计不再转负）", "", lambda m, c, p, pp: "=0" if (m == 0 or code == "A") else f"=IF(MIN({c}{R[f'{code}_cumrel']}:{col_m(MONTHS)}{R[f'{code}_cumrel']})>0,1,0)")
        mrow(f"{code}_relm", "相对现状延续的当月净收益", "元", lambda m, c, p, pp: "=0" if (m == 0 or code == "A") else f"={ref(f'{code}_net', c)}-{ref('A_net', c)}")
        mrow(f"{code}_paidm", "月度转正标记（本月起当月净增不再为负）", "", lambda m, c, p, pp: "=0" if (m == 0 or code == "A") else f"=IF(MIN({c}{R[f'{code}_relm']}:{col_m(MONTHS)}{R[f'{code}_relm']})>=0,1,0)")
        mrow(f"{code}_sh", "门店直播投入小时", "小时", store_hours_fn)
        mrow(f"{code}_stx", "机制：门店让渡的分成与分担的投流", "元", extra_store_fn or (lambda m, c, p, pp: "=0"))
        mrow(f"{code}_stc", "门店承担的开播提成（付给员工部分）", "元", (lambda m, c, p, pp: "=0" if m == 0 else f"=-{L['AP_COMM']}*{L['COMM_BY_STORE']}*{L['COMM_TO_STAFF']}*{ref(f'{code}_storered', c)}") if store_comm else (lambda m, c, p, pp: "=0"))
        mrow(f"{code}_store", "门店端净收益变化（全系统）", "元", lambda m, c, p, pp: f"={ref(f'{code}_inc', c)}*{L['STORE_INC_CONTRIB']}-{ref(f'{code}_sub', c)}*{L['STORE_SUB_LOSS']}-{ref(f'{code}_sh', c)}*{L['MGR_HOURLY']}+{ref(f'{code}_stx', c)}+{ref(f'{code}_stc', c)}-{ref(f'{code}_chf', c)}-{ref(f'{code}_mkf', c)}", bold=True)
        mrow(f"{code}_sys", "系统合计净收益（总部 + 门店）", "元", lambda m, c, p, pp: f"={ref(f'{code}_net', c)}+{ref(f'{code}_store', c)}", bold=True, fill=FILL_TOTAL)

    zero = lambda m, c, p, pp: "=0"
    # 方案一A：现状延续
    def va_fn(m, c, p, pp):
        if m == 0: return f"={L['BASE_VPS']}*{L['STORES0']}"
        return f"={L['BASE_VPS']}*{L['VOL']}*{ref('effstores', c)}*(1+{L['A_DRIFT']})^{m}"
    option_block("A", "方案一A：门店自播，现状延续（总部不投入；不限日期券口径）", va_fn,
                 [("c_people", "成本：人力", zero), ("c_ads", "成本：投流或服务商", zero), ("c_equip", "成本：设备摊销与场地", zero), ("c_train", "成本：培训与激励", zero), ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", inc_ref=L['INC_ANY'])
    # 方案一B：规范化门店直播
    def vb_store_fn(m, c, p, pp):
        if m == 0: return f"={L['BASE_VPS']}*{L['STORES0']}"
        return f"={L['BASE_VPS']}*{L['VOL_EFF']}*{L['PART']}*{ref('effstores', c)}*(1+{L['AP_DRIFT']})^{m}*(1+({L['UPLIFT_EFF']}-1)*MIN(1,{m}/{L['AP_RAMP']}))"
    def train_fn(code):
        def f(m, c, p, pp):
            if m == 0: return "=0"
            kit = f"{L['AP_STORE_KIT']}*{ref('stores', c)}" if m == 1 else f"{L['AP_STORE_KIT']}*{ref('newstores', c)}"
            oneoff = f"+{L['AP_TRAIN_ONEOFF']}" if m == 1 else ""
            return f"={kit}{oneoff}+{L['AP_TRAIN_MONTHLY']}+{L['AP_COMM']}*(1-{L['COMM_BY_STORE']})*{ref(f'{code}_storered', c)}"
        return f
    def oneoff_b1(m, c, p, pp):
        if m == 0: return "=0"
        kit = f"{L['AP_STORE_KIT']}*{ref('stores', c)}" if m == 1 else f"{L['AP_STORE_KIT']}*{ref('newstores', c)}"
        return f"={kit}" + (f"+{L['AP_TRAIN_ONEOFF']}" if m == 1 else "")
    def oneoff_pilot(m, c, p, pp):
        if m == 0: return "=0"
        return oneoff_b1(m, c, p, pp) + f"+IF(AND({L['EQUIP_CASH']}=1,{m}={L['PILOT_START']}),{L['PILOT_EQUIP']},0)"
    def oneoff_team(m, c, p, pp):
        if m == 0: return "=0"
        return oneoff_b1(m, c, p, pp) + (f"+{L['B_RECRUIT']}" if m == 1 else "") + f"+IF(AND({L['EQUIP_CASH']}=1,{m}={L['B_START']}),{L['B_EQUIP']},0)"
    pilot_equip = lambda code: (lambda m, c, p, pp: "=0" if m == 0 else f"=IF({L['EQUIP_CASH']}=1,IF({m}={L['PILOT_START']},{L['PILOT_EQUIP']},0),{ref(f'{code}_active', c)}*{L['PILOT_EQUIP']}/{L['B_EQUIP_MONTHS']})+{ref(f'{code}_active', c)}*{L['PILOT_CONTENT']}")
    team_equip = lambda code: (lambda m, c, p, pp: "=0" if m == 0 else f"=IF({L['EQUIP_CASH']}=1,IF({m}={L['B_START']},{L['B_EQUIP']},0),{ref(f'{code}_active', c)}*{L['B_EQUIP']}/{L['B_EQUIP_MONTHS']})+{ref(f'{code}_active', c)}*{L['B_SPACE']}")
    # 需要门店部分售出 GMV 的辅助行：先放辅助行再放 block
    section("方案一B：规范化门店直播（总部督导 + 培训 + 提成）— 辅助行")
    mrow("B1_storev", "门店自播售出券数", "张", vb_store_fn)
    mrow("B1_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('B1_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('B1_storev', c)}*{L['PRICE']}")
    option_block("B1", "方案一B：规范化门店直播（总部督导 + 培训 + 提成）", lambda m, c, p, pp: f"={ref('B1_storev', c)}",
                 [("c_people", "成本：人力（直播督导，按开关）", lambda m, c, p, pp: "=0" if m == 0 else f"={L['SUP_HIRE']}*{L['AP_SUP_SALARY']}*(1+{L['SOCIAL']})"),
                  ("c_ads", "成本：投流或服务商", zero),
                  ("c_equip", "成本：设备摊销与场地", zero),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("B1")),
                  ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", store_comm=True, oneoff_fn=oneoff_b1)
    # ---------- 方案二P：总部直播试点（现有品牌人员，零增量人力）----------
    def hq_room_rows(code, start_key, hours_key, gph_key, ramp_key, tag="试点"):
        mrow(f"{code}_active", f"{tag}是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L[start_key]},1,0)")
        mrow(f"{code}_gph", f"{tag}每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref(f'{code}_active', c)}*({L['B_GPH_START']}+({L[gph_key]}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L[start_key]})/{L[ramp_key]}))")
        mrow(f"{code}_livev", f"{tag}直播售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L[hours_key]}*{ref(f'{code}_gph', c)}/{L['P1_PRICE']}*{L['VOL_EFF']}")
        mrow(f"{code}_prev", "新店开业预售券数（总部主导）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['PRESALE_ON']}*{ref(f'{code}_active', c)}*{L['PRESALE_V']}*{ref('newstores', c)}")
        mrow(f"{code}_roomv", f"{tag}售出券数合计（直播 + 新店预售）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref(f'{code}_livev', c)}+{ref(f'{code}_prev', c)}")
        mrow(f"{code}_hqsold", f"{tag}售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"={ref(f'{code}_roomv', c)}*{L['PRICE']}")
        def hqred(m, c, p, pp):
            if m == 0: return "=0"
            return f"={L['REDEEM']}*({L['LAG0']}*{ref(f'{code}_hqsold', c)}+{L['LAG1']}*{ref(f'{code}_hqsold', p)}+{L['LAG2']}*{ref(f'{code}_hqsold', pp)})"
        mrow(f"{code}_hqred", f"{tag}核销 GMV", "元", hqred)
        mrow(f"{code}_storev", "门店自播售出券数（规范化后，扣除挤占）", "张", lambda m, c, p, pp: vb_store_fn(m, c, p, pp) if m == 0 else f"=MAX(0,{vb_store_fn(m, c, p, pp)[1:]}-{L['B_CANNIB']}*{ref(f'{code}_livev', c)})")
        mrow(f"{code}_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref(f'{code}_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref(f'{code}_storev', c)}*{L['PRICE']}")
    mech_income = lambda code: (lambda m, c, p, pp: "=0" if m == 0 else f"=({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*IF({L['MGMT_BASE']}=1,1,1-{L['MGMT_FEE']})*{ref(f'{code}_hqred', c)}")
    section("方案二P：总部直播试点（现有品牌营销人员开播，不新增人力）— 辅助行")
    hq_room_rows("P", "PILOT_START", "PILOT_HOURS", "PILOT_GPH", "PILOT_RAMP")
    option_block("P", "方案二P：规范化门店直播 + 总部直播试点（现有品牌人员）", lambda m, c, p, pp: f"={ref('P_storev', c)}+{ref('P_roomv', c)}",
                 [("c_people", "成本：人力（直播督导，按开关；品牌人员不新增）", lambda m, c, p, pp: "=0" if m == 0 else f"={L['SUP_HIRE']}*{L['AP_SUP_SALARY']}*(1+{L['SOCIAL']})"),
                  ("c_ads", "成本：投流或服务商", zero),
                  ("c_equip", "成本：试点设备（现金或摊销）与内容杂费", pilot_equip("P")),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("P")),
                  ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", store_comm=True, oneoff_fn=oneoff_pilot,
                 extra_income_fn=mech_income("P"),
                 extra_store_fn=lambda m, c, p, pp: "=0" if m == 0 else f"=-({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*IF({L['MGMT_BASE']}=1,1,1-{L['MGMT_FEE']})*{ref('P_hqred', c)}")
    # ---------- 方案二V：总部主导、按单付费（试点 + 兼职主播或达人佣金制）----------
    section("方案二V：总部主导、按单付费（试点直播间 + 兼职主播或达人按核销佣金）— 辅助行")
    hq_room_rows("V0", "PILOT_START", "PILOT_HOURS", "PILOT_GPH", "PILOT_RAMP")
    mrow("V_active", "按单付费主播是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['V_START']},1,0)")
    mrow("V_gph", "按单付费主播每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('V_active', c)}*({L['B_GPH_START']}+({L['V_GPH']}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L['V_START']})/{L['V_RAMP']}))")
    mrow("V_kolv", "按单付费主播售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['V_HOURS']}*{ref('V_gph', c)}/{L['P1_PRICE']}*{L['VOL_EFF']}")
    mrow("V_prev", "新店开业预售券数（总部主导，同试点）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('V0_prev', c)}")
    mrow("V_roomv", "总部主导售出券数合计（试点 + 新店预售 + 按单付费）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('V0_roomv', c)}+{ref('V_kolv', c)}")
    mrow("V_hqsold", "总部主导售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('V_roomv', c)}*{L['PRICE']}")
    mrow("V_kolsold", "其中：按单付费主播售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('V_kolv', c)}*{L['PRICE']}")
    def v_red(key):
        def f(m, c, p, pp):
            if m == 0: return "=0"
            return f"={L['REDEEM']}*({L['LAG0']}*{ref(key, c)}+{L['LAG1']}*{ref(key, p)}+{L['LAG2']}*{ref(key, pp)})"
        return f
    mrow("V_hqred", "总部主导核销 GMV", "元", v_red("V_hqsold"))
    mrow("V_kolred", "其中：按单付费主播核销 GMV", "元", v_red("V_kolsold"))
    mrow("V_storev", "门店自播售出券数（规范化后，扣除挤占）", "张", lambda m, c, p, pp: vb_store_fn(m, c, p, pp) if m == 0 else f"=MAX(0,{vb_store_fn(m, c, p, pp)[1:]}-{L['B_CANNIB']}*({ref('V0_livev', c)}+{ref('V_kolv', c)}))")
    mrow("V_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('V_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('V_storev', c)}*{L['PRICE']}")
    option_block("V", "方案二V：规范化门店直播 + 总部主导、按单付费直播", lambda m, c, p, pp: f"={ref('V_storev', c)}+{ref('V_roomv', c)}",
                 [("c_people", "成本：人力（直播督导，按开关）+ 协调杂费 + 总部承担的主播佣金", lambda m, c, p, pp: "=0" if m == 0 else f"={L['SUP_HIRE']}*{L['AP_SUP_SALARY']}*(1+{L['SOCIAL']})+{ref('V_active', c)}*{L['V_COORD']}+{L['V_COMM']}*{L['V_COMM_HQ_SHARE']}*{ref('V_kolred', c)}"),
                  ("c_ads", "成本：投流或服务商", zero),
                  ("c_equip", "成本：试点设备（现金或摊销）与内容杂费", pilot_equip("V0")),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("V")),
                  ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", store_comm=True, oneoff_fn=oneoff_pilot,
                 extra_income_fn=mech_income("V"),
                 extra_store_fn=lambda m, c, p, pp: "=0" if m == 0 else f"=-({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*IF({L['MGMT_BASE']}=1,1,1-{L['MGMT_FEE']})*{ref('V_hqred', c)}-{L['V_COMM']}*(1-{L['V_COMM_HQ_SHARE']})*{ref('V_kolred', c)}")
    # ---------- 方案二H：总部主导、总部付费主播（按小时 + 低提成）----------
    section("方案二H：总部主导、总部付费主播（试点直播间 + 兼职主播按小时付费，总部承担）— 辅助行")
    hq_room_rows("VH0", "PILOT_START", "PILOT_HOURS", "PILOT_GPH", "PILOT_RAMP")
    mrow("VH_active", "总部付费主播是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['V_START']},1,0)")
    mrow("VH_gph", "总部付费主播每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('VH_active', c)}*({L['B_GPH_START']}+({L['V_GPH']}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L['V_START']})/{L['V_RAMP']}))")
    mrow("VH_kolv", "总部付费主播售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['VH_HOURS']}*{ref('VH_gph', c)}/{L['P1_PRICE']}*{L['VOL_EFF']}")
    mrow("VH_prev", "新店开业预售券数（总部主导，同试点）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('VH0_prev', c)}")
    mrow("VH_roomv", "总部主导售出券数合计（试点 + 新店预售 + 付费主播）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('VH0_roomv', c)}+{ref('VH_kolv', c)}")
    mrow("VH_hqsold", "总部主导售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('VH_roomv', c)}*{L['PRICE']}")
    mrow("VH_kolsold", "其中：付费主播售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('VH_kolv', c)}*{L['PRICE']}")
    mrow("VH_hqred", "总部主导核销 GMV", "元", v_red("VH_hqsold"))
    mrow("VH_kolred", "其中：付费主播核销 GMV", "元", v_red("VH_kolsold"))
    mrow("VH_storev", "门店自播售出券数（规范化后，扣除挤占）", "张", lambda m, c, p, pp: vb_store_fn(m, c, p, pp) if m == 0 else f"=MAX(0,{vb_store_fn(m, c, p, pp)[1:]}-{L['B_CANNIB']}*({ref('VH0_livev', c)}+{ref('VH_kolv', c)}))")
    mrow("VH_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('VH_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('VH_storev', c)}*{L['PRICE']}")
    option_block("VH", "方案二H：规范化门店直播 + 总部主导、总部付费主播（后备结构）", lambda m, c, p, pp: f"={ref('VH_storev', c)}+{ref('VH_roomv', c)}",
                 [("c_people", "成本：人力（直播督导，按开关）+ 协调杂费 + 主播时薪 + 主播低提成", lambda m, c, p, pp: "=0" if m == 0 else f"={L['SUP_HIRE']}*{L['AP_SUP_SALARY']}*(1+{L['SOCIAL']})+{ref('VH_active', c)}*({L['V_COORD']}+{L['HOST_HOURLY']}*{L['VH_HOURS']})+{L['VH_COMM']}*{ref('VH_kolred', c)}"),
                  ("c_ads", "成本：投流或服务商", zero),
                  ("c_equip", "成本：试点设备（现金或摊销）与内容杂费", pilot_equip("VH0")),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("VH")),
                  ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", store_comm=True, oneoff_fn=oneoff_pilot,
                 extra_income_fn=mech_income("VH"),
                 extra_store_fn=lambda m, c, p, pp: "=0" if m == 0 else f"=-({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*IF({L['MGMT_BASE']}=1,1,1-{L['MGMT_FEE']})*{ref('VH_hqred', c)}")
    # 方案二：总部直播团队 + 门店赋能
    section("方案二：总部直播团队（含门店赋能）— 辅助行")
    mrow("B2_active", "团队是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_START']},1,0)")
    mrow("B2_gph", "总部直播间每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2_active', c)}*({L['B_GPH_START']}+({L['B_GPH_MATURE']}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L['B_START']})/{L['B_RAMP']}))")
    mrow("B2_livev", "总部直播间直播售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['B_HOURS']}*{ref('B2_gph', c)}/{L['P1_PRICE']}*{L['VOL_EFF']}")
    mrow("B2_prev", "新店开业预售券数（总部主导）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['PRESALE_ON']}*{ref('B2_active', c)}*{L['PRESALE_V']}*{ref('newstores', c)}")
    mrow("B2_roomv", "总部直播间售出券数合计（直播 + 新店预售）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2_livev', c)}+{ref('B2_prev', c)}")
    mrow("B2_adsv", "投流带来的售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']}*{L['B_ROI']}/{L['P1_PRICE']}*{L['VOL_EFF']},0)")
    mrow("B2_hqsold", "总部直播间与投流售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"=({ref('B2_roomv', c)}+{ref('B2_adsv', c)})*{L['PRICE']}")
    def b2_hqred(m, c, p, pp):
        if m == 0: return "=0"
        return f"={L['REDEEM']}*({L['LAG0']}*{ref('B2_hqsold', c)}+{L['LAG1']}*{ref('B2_hqsold', p)}+{L['LAG2']}*{ref('B2_hqsold', pp)})"
    mrow("B2_hqred", "总部直播间与投流核销 GMV", "元", b2_hqred)
    mrow("B2_storev", "门店自播售出券数（赋能后，扣除总部直播间挤占）", "张", lambda m, c, p, pp: vb_store_fn(m, c, p, pp) if m == 0 else f"=MAX(0,{vb_store_fn(m, c, p, pp)[1:]}-{L['B_CANNIB']}*({ref('B2_livev', c)}+{ref('B2_adsv', c)}))")
    mrow("B2_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('B2_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('B2_storev', c)}*{L['PRICE']}")
    option_block("B2", "方案二：总部直播团队（含门店赋能）", lambda m, c, p, pp: f"={ref('B2_storev', c)}+{ref('B2_roomv', c)}+{ref('B2_adsv', c)}",
                 [("c_people", "成本：直播督导 + 团队人力（4 人含社保、兼职备播）+ 主播提成 + 招聘", lambda m, c, p, pp: "=0" if m == 0 else f"={L['SUP_HIRE']}*{L['AP_SUP_SALARY']}*(1+{L['SOCIAL']})+{ref('B2_active', c)}*{L['TEAM_SAL']}+{L['B_HOST_COMM']}*{ref('B2_hqred', c)}" + (f"+{L['B_RECRUIT']}" if m == 1 else "")),
                  ("c_ads", "成本：投流", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']},0)"),
                  ("c_equip", "成本：设备（现金或摊销）与场地", team_equip("B2")),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("B2")),
                  ("c_credit", "减：抵减的品牌预算与人员", lambda m, c, p, pp: "=0" if m == 0 else f"=-{ref('B2_active', c)}*{L['BRAND_CREDIT']}")],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", store_comm=True, oneoff_fn=oneoff_team)
    # 方案二+：总部直播团队 + 配套分成机制
    section("方案二+：总部直播团队 + 配套机制（团队订单总部分成提高、门店分担投流）— 辅助行")
    mrow("B2M_active", "团队是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_START']},1,0)")
    mrow("B2M_gph", "总部直播间每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2M_active', c)}*({L['B_GPH_START']}+({L['B_GPH_MATURE']}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L['B_START']})/{L['B_RAMP']}))")
    mrow("B2M_livev", "总部直播间直播售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['B_HOURS']}*{ref('B2M_gph', c)}/{L['P1_PRICE']}*{L['VOL_EFF']}")
    mrow("B2M_prev", "新店开业预售券数（总部主导）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['PRESALE_ON']}*{ref('B2M_active', c)}*{L['PRESALE_V']}*{ref('newstores', c)}")
    mrow("B2M_roomv", "总部直播间售出券数合计（直播 + 新店预售）", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('B2M_livev', c)}+{ref('B2M_prev', c)}")
    mrow("B2M_adsv", "投流带来的售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']}*{L['B_ROI']}/{L['P1_PRICE']}*{L['VOL_EFF']},0)")
    mrow("B2M_hqsold", "总部直播间与投流售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"=({ref('B2M_roomv', c)}+{ref('B2M_adsv', c)})*{L['PRICE']}")
    def b2m_hqred(m, c, p, pp):
        if m == 0: return "=0"
        return f"={L['REDEEM']}*({L['LAG0']}*{ref('B2M_hqsold', c)}+{L['LAG1']}*{ref('B2M_hqsold', p)}+{L['LAG2']}*{ref('B2M_hqsold', pp)})"
    mrow("B2M_hqred", "总部直播间与投流核销 GMV", "元", b2m_hqred)
    mrow("B2M_storev", "门店自播售出券数（赋能后，扣除总部直播间挤占）", "张", lambda m, c, p, pp: vb_store_fn(m, c, p, pp) if m == 0 else f"=MAX(0,{vb_store_fn(m, c, p, pp)[1:]}-{L['B_CANNIB']}*({ref('B2M_livev', c)}+{ref('B2M_adsv', c)}))")
    mrow("B2M_storesold", "门店自播售出 GMV", "元", lambda m, c, p, pp: f"={ref('B2M_storev', c)}*{L['P1_PRICE']}" if m == 0 else f"={ref('B2M_storev', c)}*{L['PRICE']}")
    option_block("B2M", "方案二+：总部直播团队 + 配套机制", lambda m, c, p, pp: f"={ref('B2M_storev', c)}+{ref('B2M_roomv', c)}+{ref('B2M_adsv', c)}",
                 [("c_people", "成本：直播督导 + 团队人力（4 人含社保、兼职备播）+ 主播提成 + 招聘", lambda m, c, p, pp: "=0" if m == 0 else f"={L['SUP_HIRE']}*{L['AP_SUP_SALARY']}*(1+{L['SOCIAL']})+{ref('B2M_active', c)}*{L['TEAM_SAL']}+{L['B_HOST_COMM']}*{ref('B2M_hqred', c)}" + (f"+{L['B_RECRUIT']}" if m == 1 else "")),
                  ("c_ads", "成本：投流（扣除门店分担部分）", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['B_ADS_START']},{L['B_ADS']}*(1-{L['B_ADS_STORE_SHARE']}),0)"),
                  ("c_equip", "成本：设备（现金或摊销）与场地", team_equip("B2M")),
                  ("c_train", "成本：培训、门店设备补贴与开播提成", train_fn("B2M")),
                  ("c_credit", "减：抵减的品牌预算与人员", lambda m, c, p, pp: "=0" if m == 0 else f"=-{ref('B2M_active', c)}*{L['BRAND_CREDIT']}")],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}",
                 extra_income_fn=lambda m, c, p, pp: "=0" if m == 0 else f"=({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*IF({L['MGMT_BASE']}=1,1,1-{L['MGMT_FEE']})*{ref('B2M_hqred', c)}",
                 extra_store_fn=lambda m, c, p, pp: "=0" if m == 0 else f"=-({L['HQ_TAKE_M']}-{L['HQ_TAKE']})*IF({L['MGMT_BASE']}=1,1,1-{L['MGMT_FEE']})*{ref('B2M_hqred', c)}-IF({m}>={L['B_ADS_START']},{L['B_ADS']}*{L['B_ADS_STORE_SHARE']},0)", store_comm=True, oneoff_fn=oneoff_team)
    # 方案三：外包服务商
    section("方案三：外包服务商代播（参照）— 辅助行")
    mrow("C_storev_raw", "门店自播售出券数（同现状延续，扣除挤占前）", "张", va_fn)
    mrow("C_active", "服务商是否已开播", "0/1", lambda m, c, p, pp: "=0" if m == 0 else f"=IF({m}>={L['C_START']},1,0)")
    mrow("C_gph", "服务商直播间每小时售出 GMV（九折口径）", "元/小时", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('C_active', c)}*({L['B_GPH_START']}+({L['B_GPH_MATURE']}-{L['B_GPH_START']})*MIN(1,MAX(0,{m}-{L['C_START']})/{L['C_RAMP']}))")
    mrow("C_agv", "服务商直播间售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={L['C_HOURS']}*{ref('C_gph', c)}/{L['P1_PRICE']}*{L['VOL_EFF']}")
    mrow("C_adsv", "服务商投流带来的售出券数", "张", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('C_active', c)}*{L['C_ADS']}*{L['C_ROI']}/{L['P1_PRICE']}*{L['VOL_EFF']}")
    mrow("C_agsold", "服务商直播间与投流售出 GMV", "元", lambda m, c, p, pp: "=0" if m == 0 else f"=({ref('C_agv', c)}+{ref('C_adsv', c)})*{L['PRICE']}")
    mrow("C_storev", "门店自播售出券数（扣除服务商直播间挤占）", "张", lambda m, c, p, pp: f"={ref('C_storev_raw', c)}" if m == 0 else f"=MAX(0,{ref('C_storev_raw', c)}-{L['B_CANNIB']}*({ref('C_agv', c)}+{ref('C_adsv', c)}))")
    option_block("C", "方案三：外包服务商代播（参照）", lambda m, c, p, pp: f"={ref('C_storev', c)}+{ref('C_agv', c)}+{ref('C_adsv', c)}",
                 [("c_people", "成本：人力", zero),
                  ("c_ads", "成本：服务商固定费 + 佣金 + 投流", lambda m, c, p, pp: "=0" if m == 0 else f"={ref('C_active', c)}*({L['C_RETAINER']}+{L['C_ADS']})+{L['C_COMM']}*{ref('C_agsold', c)}"),
                  ("c_equip", "成本：设备摊销与场地", zero),
                  ("c_train", "成本：培训与激励", zero),
                  ("c_credit", "减：抵减的品牌预算", zero)],
                 lambda m, c, p, pp: f"={ref('effstores', c)}*{L['STORE_HOURS']}", inc_ref=L['INC_ANY'])
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
ws["A2"] = "全部为公式，引用三张月度表。相对现状转正月（回本月）指该方案相对现状延续（方案一A）的累计总部净收益转正且此后到第 12 月不再转负的最早月份。"; ws["A2"].font = F_NOTE
OPTS = [("A", "方案一A 门店自播，现状延续"), ("B1", "方案一B 规范化门店直播"), ("P", "方案二P 总部直播试点（现有人员）"), ("V", "方案二V 总部主导、按单付费"), ("VH", "方案二H 总部付费主播（按小时）"), ("B2", "方案二 总部直播团队（现有分成）"), ("B2M", "方案二+ 总部直播团队（配套机制）"), ("C", "方案三 外包服务商（参照）")]
METRICS = [("sold", "售出 GMV", FMT_INT), ("red", "核销 GMV", FMT_INT), ("n", "核销间夜", FMT_INT), ("inc", "增量间夜", FMT_INT),
           ("hqgross", "总部抖音收入合计", FMT_INT), ("hqinc", "总部增量收入", FMT_INT), ("cost", "总部成本", FMT_INT), ("net", "总部增量净收益", FMT_INT), ("relnet", "相对现状延续的净收益", FMT_INT), ("paidrel", "相对现状转正月", FMT_INT),
           ("share12", "第 12 月抖音份额", FMT_PCT), ("store", "门店端净收益变化", FMT_INT), ("sys", "系统合计净收益", FMT_INT),
           ("trough", "相对现状的现金谷底", FMT_INT), ("paidm", "月度转正月", FMT_INT),
           ("hqpre", "其中新店预售贡献", FMT_INT), ("oneoff", "一次性现金", FMT_INT), ("stnight", "门店每抖音间夜期望收益", FMT_DEC), ("storeok", "门店约束", FMT_INT),
           ("brandinc", "总部主导订单带来的总部收入（可归属品牌部）", FMT_INT), ("mkf", "品牌营销费收入", FMT_INT)]
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
            if mk == "paidrel":
                rr = R[f"{code}_paidrel"]
                f = "—" if code == "A" else f"=IFERROR(MATCH(1,'{sname}'!$D${rr}:$O${rr},0),\"12 个月内未转正\")"
            elif mk == "share12":
                rr = R[f"{code}_share"]; f = f"='{sname}'!$O${rr}"
            elif mk == "trough":
                rr = R[f"{code}_cumrel"]; f = "0" if code == "A" else f"=MIN(0,MIN('{sname}'!$D${rr}:$O${rr}))"
            elif mk == "paidm":
                rr = R[f"{code}_paidm"]
                f = "—" if code == "A" else f"=IFERROR(MATCH(1,'{sname}'!$D${rr}:$O${rr},0),\"12 个月内未转正\")"
            elif mk == "stnight":
                rs, rn = R[f"{code}_store"], R[f"{code}_n"]; f = f"=SUM('{sname}'!$D${rs}:$O${rs})/SUM('{sname}'!$D${rn}:$O${rn})"
            elif mk == "storeok":
                rs, rn = R[f"{code}_store"], R[f"{code}_n"]
                f = "—" if code == "A" else f"=IF(AND(SUM('{sname}'!$D${rs}:$O${rs})>=0,SUM('{sname}'!$D${rs}:$O${rs})/SUM('{sname}'!$D${rn}:$O${rn})>={A_base('STORE_MIN_GAIN')},INDEX({A_rng('PART')},1,{sidx})>={A_base('PART_MIN')}),\"满足\",\"不满足\")"
            elif mk == "relnet":
                rr = R[f"{code}_net"]; ra = R["A_net"]; f = f"=SUM('{sname}'!$D${rr}:$O${rr})-SUM('{sname}'!$D${ra}:$O${ra})"
            else:
                rr = R[f"{code}_{mk}"]; f = f"=SUM('{sname}'!$D${rr}:$O${rr})"
            c = ws.cell(row=r, column=j, value=f); c.font = F_LINK; c.number_format = fmt; c.alignment = ALIGN_R
        SUMMARY_ROWS[(sname, code)] = r
        r += 1
    r += 1
# 边际对比：方案二相对方案一B
for mcode, mtitle in [("P", "边际：方案二P（试点）相对方案一B"), ("V", "边际：方案二V（按单付费）相对方案一B"), ("B2", "边际：方案二（现有分成）相对方案一B"), ("B2M", "边际：方案二+（配套机制）相对方案一B")]:
    c = ws.cell(row=r, column=1, value=mtitle); c.font = F_H2; c.fill = FILL_H2
    for j, h in enumerate(["情景", "多售出 GMV", "多核销 GMV", "总部多增收入", "总部多成本", "总部净收益差", "门店端差", "系统合计差"], 2):
        c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
    r += 1
    for sname in ["月度_悲观", "月度_基准", "月度_乐观"]:
        ws.cell(row=r, column=2, value=sname.split("_")[1]).font = F_LABEL
        rb2 = SUMMARY_ROWS[(sname, mcode)]; rb1 = SUMMARY_ROWS[(sname, "B1")]
        _mcol = {mk: j for j, (mk, _, _) in enumerate(METRICS, 2)}
        pairs = [("sold", _mcol["sold"]), ("red", _mcol["red"]), ("hqinc", _mcol["hqinc"]), ("cost", _mcol["cost"]), ("net", _mcol["net"]), ("store", _mcol["store"]), ("sys", _mcol["sys"])]
        for j, (mk, colidx) in enumerate(pairs, 3):
            colL = get_column_letter(colidx)
            c = ws.cell(row=r, column=j, value=f"={colL}{rb2}-{colL}{rb1}"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
        r += 1
    r += 1
ws.column_dimensions["A"].width = 34
for j in range(2, 24): ws.column_dimensions[get_column_letter(j)].width = 15
ws.freeze_panes = "B5"


# ---------------- 总部决策（回本规则、单位经济、各方案总部口径汇总）----------------
ws = ws_dec
ws["A1"] = "总部决策：每个方案对总部的投入、收益与回本（全部为公式）"; ws["A1"].font = F_H1
ws["A2"] = "回本月 = 相对现状延续（方案一A）的总部累计净收益转正且此后不再转负的最早月份。判定：门店约束不满足 → 不可执行；基准回本月 ≤ 适用通过线 且 基准现金谷底 ≥ 允许谷底 且 悲观 12 个月相对现状 ≥ 允许亏损 → 通过（悲观 12 个月内未回本则为条件通过）；否则不通过。稳态月成本取第 12 月。盈亏平衡所需份额提升 = 稳态月成本 ÷（系统月间夜 × 总部每间夜净得），三种口径：替代（最保守）、混合 4%、混合 8%。"; ws["A2"].font = F_NOTE
LB, RB, _ = MS["月度_基准"]; LP, RP, _ = MS["月度_悲观"]; LO, RO, _ = MS["月度_乐观"]
def mref(sname, addr): return f"'{sname}'!{addr}"
r = 4
ws.cell(row=r, column=1, value="总部单位经济（基准情景，按选用定价档）").font = F_BOLD; ws.cell(row=r, column=1).fill = FILL_SEC
for col in range(2, 5): ws.cell(row=r, column=col).fill = FILL_SEC
r += 1
UE = {}
for key, lab, fmt in [("HQ_SUB_GAIN", "总部每替代间夜净得（现有 4% 分成）", FMT_DEC), ("HQ_INC_GAIN", "总部每增量间夜净得（现有 4% 分成）", FMT_DEC),
                      ("HQ_SUB_GAIN_M", "总部每替代间夜净得（总部主导订单分成）", FMT_DEC), ("HQ_INC_GAIN_M", "总部每增量间夜净得（总部主导订单分成）", FMT_DEC),
                      ("HQ_MIX_GAIN", "总部每抖音间夜净得（混合口径，4%）", FMT_DEC), ("HQ_MIX_GAIN_M", "总部每抖音间夜净得（混合口径，总部主导分成）", FMT_DEC),
                      ("HQ_PER_PT", "份额每提升 1 个百分点的总部月净得（当前门店数，替代口径）", FMT_INT),
                      ("HQ_PER_PT_MIX", "份额每提升 1 个百分点的总部月净得（当前门店数，混合口径 4%）", FMT_INT),
                      ("HQ_PER_PT_MIX_M", "份额每提升 1 个百分点的总部月净得（当前门店数，混合口径 8%）", FMT_INT)]:
    ws.cell(row=r, column=1, value=lab).font = F_LABEL
    c = ws.cell(row=r, column=2, value=f"={mref('月度_基准', LB[key])}"); c.font = F_LINK; c.number_format = fmt; c.alignment = ALIGN_R
    UE[key] = f"$B${r}"; r += 1
N12 = mref('月度_基准', '$O$' + str(RB['nights']))
for key, lab, g in [("HQ_PER_PT_12", "份额每提升 1 个百分点的总部月净得（第 12 月门店数，替代口径）", "HQ_SUB_GAIN"), ("HQ_PER_PT_MIX_12", "同上，混合口径 4%", "HQ_MIX_GAIN"), ("HQ_PER_PT_MIX_M_12", "同上，混合口径 8%", "HQ_MIX_GAIN_M")]:
    ws.cell(row=r, column=1, value=lab).font = F_LABEL
    c = ws.cell(row=r, column=2, value=f"={N12}*0.01*{UE[g]}"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    UE[key] = f"$B${r}"; r += 1
# 保本每小时产出（总部主导订单分成；主播按小时付费）
ws.cell(row=r, column=1, value="保本每小时售出 GMV：总部付费主播，时薪无提成（含挤占；8% 分成，九折口径）").font = F_LABEL
hourly_net_per_gmv = f"({A_base('REDEEM')}*{A_base('WEEKDAY_VOL')}/{A_base('P1_PRICE')}*({UE['HQ_MIX_GAIN_M']}-{A_base('B_CANNIB')}*{UE['HQ_MIX_GAIN']}))"
c = ws.cell(row=r, column=2, value=f"={A_base('HOST_HOURLY')}/{hourly_net_per_gmv}"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R; UE["BE_GPH_HOURLY"] = f"$B${r}"; r += 1
ws.cell(row=r, column=1, value="保本每小时售出 GMV：时薪 + 2% 提成").font = F_LABEL
c = ws.cell(row=r, column=2, value=f"={A_base('HOST_HOURLY')}/({hourly_net_per_gmv}-{A_base('REDEEM')}*{A_base('WEEKDAY_VOL')}*{A_base('VH_COMM')})"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R; UE["BE_GPH_HOURLY_COMM"] = f"$B${r}"; r += 1
ws.cell(row=r, column=1, value="总部独自投流的保本 ROI（4% 分成，混合口径，含工作日系数）").font = F_LABEL
c = ws.cell(row=r, column=2, value=f"=1/({A_base('REDEEM')}*{A_base('WEEKDAY_VOL')}/{A_base('P1_PRICE')}*{UE['HQ_MIX_GAIN']})"); c.font = F_CALC; c.number_format = FMT_DEC; c.alignment = ALIGN_R; UE["ADS_BE_ROI"] = f"$B${r}"; r += 1
ws.cell(row=r, column=1, value="总部独自投流的保本 ROI（总部主导订单分成）").font = F_LABEL
c = ws.cell(row=r, column=2, value=f"=1/({A_base('REDEEM')}*{A_base('WEEKDAY_VOL')}/{A_base('P1_PRICE')}*{UE['HQ_MIX_GAIN_M']})"); c.font = F_CALC; c.number_format = FMT_DEC; c.alignment = ALIGN_R; UE["ADS_BE_ROI_M"] = f"$B${r}"; r += 1
ws.cell(row=r, column=1, value="份额上限：空房上限隐含的增量份额点（当前门店数）").font = F_LABEL
c = ws.cell(row=r, column=2, value=f"={A_base('CAP_SHARE')}*{A_base('STORES0')}*{A_base('ROOMS')}*(1-{A_base('OCC')})*{A_base('DAYS')}/({A_base('STORES0')}*{A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')})"); c.font = F_CALC; c.number_format = FMT_PCT; c.alignment = ALIGN_R; UE["SHARE_CAP_INC"] = f"$B${r}"; r += 1
ws.cell(row=r, column=1, value="份额上限：按增量比例折算的总份额（当前门店数，基准增量比例）").font = F_LABEL
c = ws.cell(row=r, column=2, value=f"={UE['SHARE_CAP_INC']}/{mref('月度_基准', LB['INC'])}"); c.font = F_CALC; c.number_format = FMT_PCT; c.alignment = ALIGN_R; UE["SHARE_CAP_TOTAL"] = f"$B${r}"; r += 1
ws.cell(row=r, column=1, value="回本规则：含固定人头的方案通过线（月）").font = F_LABEL
c = ws.cell(row=r, column=2, value=f"={A_base('PAYBACK_RULE')}"); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R; RULE = f"$B${r}"; r += 1
ws.cell(row=r, column=1, value="回本规则：零固定成本方案通过线（月）").font = F_LABEL
c = ws.cell(row=r, column=2, value=f"={A_base('PAYBACK_RULE_VAR')}"); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R; RULE_VAR = f"$B${r}"; r += 2
HDR = ["方案", "成本类型", "一次性现金（元）", "稳态月成本（第 12 月，基准，元）", "12 个月总部净收益 悲观", "基准", "乐观", "相对现状延续 悲观", "基准", "乐观", "其中新店预售贡献（基准）", "回本月 悲观", "基准", "乐观", "月度转正月 基准", "现金谷底 悲观", "现金谷底 基准", "第 12 月份额 悲观", "基准", "乐观", "盈亏平衡所需份额提升：替代口径（30 家店）", "替代口径（第 12 月门店数）", "混合 4%（30 家店）", "混合 8%（30 家店）", "门店约束", "门店每抖音间夜期望收益（基准）", "适用通过线（月）", "判定", "覆盖稳态月成本所需的营销费率（30 家店流水）", "同上（第 12 月门店数）", "总部主导订单带来的总部收入（基准，12 个月）"]
for j, h in enumerate(HDR, 1):
    c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
HC = {h: get_column_letter(j) for j, h in enumerate(HDR, 1)}
r += 1
DEC_ROWS = {}
_mcol = {mk: get_column_letter(j) for j, (mk, _, _) in enumerate(METRICS, 2)}
CTYPE = {"B1": "零固定成本（可随时停止）", "P": "零固定成本（可随时停止）", "V": "零固定成本（可随时停止）", "VH": "准固定（30 天可停）", "B2": "固定人头", "B2M": "固定人头", "C": "固定人头"}
for code, olabel in OPTS:
    if code == "A": continue
    rb = SUMMARY_ROWS[("月度_基准", code)]; rp = SUMMARY_ROWS[("月度_悲观", code)]; ro = SUMMARY_ROWS[("月度_乐观", code)]
    def sc(mk, rr): return f"='情景对比'!{_mcol[mk]}{rr}"
    # 列写入（重复表头“基准/乐观”按顺序处理）
    row_vals = [olabel, CTYPE[code], sc("oneoff", rb), f"={mref('月度_基准', '$O$' + str(RB[code + '_cost']))}",
                sc("net", rp), sc("net", rb), sc("net", ro), sc("relnet", rp), sc("relnet", rb), sc("relnet", ro), sc("hqpre", rb),
                sc("paidrel", rp), sc("paidrel", rb), sc("paidrel", ro), sc("paidm", rb), sc("trough", rp), sc("trough", rb),
                sc("share12", rp), sc("share12", rb), sc("share12", ro)]
    for j, v in enumerate(row_vals, 1):
        c = ws.cell(row=r, column=j, value=v); c.alignment = ALIGN_R if j > 2 else ALIGN_L
        c.font = F_LINK if (isinstance(v, str) and v.startswith("=")) else F_LABEL
        if 18 <= j <= 20: c.number_format = FMT_PCT
        elif j >= 3: c.number_format = FMT_INT
    cost = f"{HC['稳态月成本（第 12 月，基准，元）']}{r}"
    nights0 = f"({A_base('STORES0')}*{A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')})"
    def colnum(h):
        L_ = HC[h]; return (ord(L_) - 64) if len(L_) == 1 else (26 * (ord(L_[0]) - 64) + ord(L_[1]) - 64)
    for h, formula in [("盈亏平衡所需份额提升：替代口径（30 家店）", f"={cost}/({nights0}*{UE['HQ_SUB_GAIN']})"),
                       ("替代口径（第 12 月门店数）", f"={cost}/({N12}*{UE['HQ_SUB_GAIN']})"),
                       ("混合 4%（30 家店）", f"={cost}/({nights0}*{UE['HQ_MIX_GAIN']})"),
                       ("混合 8%（30 家店）", f"={cost}/({nights0}*{UE['HQ_MIX_GAIN_M']})")]:
        c = ws.cell(row=r, column=colnum(h), value=formula); c.font = F_CALC; c.number_format = FMT_PCT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=colnum("门店约束"), value=sc("storeok", rb)); c.font = F_LINK; c.alignment = ALIGN_C
    c = ws.cell(row=r, column=colnum("门店每抖音间夜期望收益（基准）"), value=sc("stnight", rb)); c.font = F_LINK; c.number_format = FMT_DEC; c.alignment = ALIGN_R
    fixed = code in ("B2", "B2M", "C")
    rule_cell = f"={RULE}" if fixed else f"=IF({A_base('SUP_HIRE')}=1,{RULE},{RULE_VAR})"
    c = ws.cell(row=r, column=colnum("适用通过线（月）"), value=rule_cell); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    pb_b = f"{get_column_letter(13)}{r}"; pb_p = f"{get_column_letter(12)}{r}"; trough_b = f"{get_column_letter(17)}{r}"; rel_p = f"{get_column_letter(8)}{r}"; ok = f"{get_column_letter(colnum('门店约束'))}{r}"; rl = f"{get_column_letter(colnum('适用通过线（月）'))}{r}"
    judge = f'=IF({ok}="不满足","不可执行",IF(AND(ISNUMBER({pb_b}),{pb_b}<={rl},{trough_b}>={A_base("TROUGH_RULE")},{rel_p}>={A_base("PESS_LOSS_RULE")}),IF(ISNUMBER({pb_p}),"通过","条件通过（悲观 12 个月内未回本）"),"不通过"))'
    c = ws.cell(row=r, column=colnum("判定"), value=judge); c.font = F_BOLD; c.alignment = ALIGN_C
    rev0 = f"({A_base('STORES0')}*{A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')}*{A_base('ADR')})"
    rev12 = mref('月度_基准', '$O$' + str(RB['rev']))
    c = ws.cell(row=r, column=colnum("覆盖稳态月成本所需的营销费率（30 家店流水）"), value=f"={cost}/{rev0}"); c.font = F_CALC; c.number_format = '0.00%'; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=colnum("同上（第 12 月门店数）"), value=f"={cost}/{rev12}"); c.font = F_CALC; c.number_format = '0.00%'; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=colnum("总部主导订单带来的总部收入（基准，12 个月）"), value=sc("brandinc", rb)); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    DEC_ROWS[code] = r; r += 1
r += 1
# 品牌营销费与品牌部损益
ws.cell(row=r, column=1, value="品牌营销费能收多少（按门店全渠道流水，稳态月度）").font = F_BOLD; ws.cell(row=r, column=1).fill = FILL_SEC
for col in range(2, 6): ws.cell(row=r, column=col).fill = FILL_SEC
r += 1
for j, h in enumerate(["门店数", "月流水（元）", "0.5% 营销费/月", "1.0% 营销费/月", "品牌部现有月成本（薪酬含社保 + 预算）"], 1):
    c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
r += 1
MKT_ROWS = {}
for st in [30, 50, 80]:
    c = ws.cell(row=r, column=1, value=st); c.font = F_INPUT; c.number_format = FMT_INT
    c = ws.cell(row=r, column=2, value=f"=A{r}*{A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')}*{A_base('ADR')}"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=3, value=f"=B{r}*0.005"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=4, value=f"=B{r}*0.01"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=5, value=f"={A_base('BRAND_SALARY')}*(1+{A_base('SOCIAL')})+{A_base('BRAND_BUDGET')}"); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    MKT_ROWS[st] = r; r += 1
r += 1
ws.cell(row=r, column=1, value="品牌部损益：从成本中心到销售部门（12 个月，基准 / 悲观 / 乐观）").font = F_BOLD; ws.cell(row=r, column=1).fill = FILL_SEC
for col in range(2, 11): ws.cell(row=r, column=col).fill = FILL_SEC
r += 1
for j, h in enumerate(["方案", "品牌部现有成本（12 个月）", "可归属收入 悲观", "基准", "乐观", "该方案新增的总部成本（相对一B，基准，12 个月）", "覆盖率（基准，不含营销费）", "覆盖率（基准，加 0.5% 营销费）", "覆盖率（基准，加 1% 营销费）", "0.5% 营销费 12 个月收入"], 1):
    c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
r += 1
BR_ROWS = {}
brand_cost12 = f"(({A_base('BRAND_SALARY')}*(1+{A_base('SOCIAL')})+{A_base('BRAND_BUDGET')})*12)"
rev_sum = f"SUM('月度_基准'!$D${RB['rev']}:$O${RB['rev']})"
for code, olabel in OPTS:
    if code not in ("P", "V", "VH", "B2M"): continue
    rb = SUMMARY_ROWS[("月度_基准", code)]; rp = SUMMARY_ROWS[("月度_悲观", code)]; ro = SUMMARY_ROWS[("月度_乐观", code)]; rb1 = SUMMARY_ROWS[("月度_基准", "B1")]
    ws.cell(row=r, column=1, value=olabel).font = F_LABEL
    c = ws.cell(row=r, column=2, value=f"={brand_cost12}"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    for j, rr in zip((3, 4, 5), (rp, rb, ro)):
        c = ws.cell(row=r, column=j, value=f"='情景对比'!{_mcol['brandinc']}{rr}"); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=6, value=f"='情景对比'!{_mcol['cost']}{rb}-'情景对比'!{_mcol['cost']}{rb1}"); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=7, value=f"=D{r}/(B{r}+F{r})"); c.font = F_CALC; c.number_format = FMT_PCT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=8, value=f"=(D{r}+0.005*{rev_sum})/(B{r}+F{r})"); c.font = F_CALC; c.number_format = FMT_PCT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=9, value=f"=(D{r}+0.01*{rev_sum})/(B{r}+F{r})"); c.font = F_CALC; c.number_format = FMT_PCT; c.alignment = ALIGN_R
    c = ws.cell(row=r, column=10, value=f"=0.005*{rev_sum}"); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    BR_ROWS[code] = r; r += 1
r += 1
ws.cell(row=r, column=1, value="注：一次性现金含培训、门店设备补贴（默认门店自购为 0）、试点或团队设备（按现金开关）与招聘；稳态月成本含按核销计提的提成与佣金中由总部承担的部分。方案二P/二V/二H 的品牌营销人员薪酬不计为新增成本（现有编制），其机会成本是品牌工作被挤占。方案二/二+ 默认不抵减品牌预算（全成本口径），现金口径见变体 absorb。").font = F_NOTE
ws.column_dimensions["A"].width = 36
for j in range(2, len(HDR) + 1): ws.column_dimensions[get_column_letter(j)].width = 14
ws.freeze_panes = "B5"

# ---------------- 份额情景（目标份额 × 门店规模 → 总部与门店的月度结果，基准口径）----------------
ws = ws_sh
ws["A1"] = "份额情景：抖音份额从当前值提升到目标值，总部与门店每月的变化（基准情景参数，稳态）"; ws["A1"].font = F_H1
ws["A2"] = "蓝色单元格可改。相对现状 = 相对当前份额（假设表 SHARE0）的变化；增量比例随份额递减（假设表 INC_DECAY）；替代口径 = 新增间夜全部替代 OTA（最保守，等于总部可承受的月固定成本上限）；混合口径按该份额下的增量比例；产能换算说明把份额目标做到需要买多少产出。"; ws["A2"].font = F_NOTE
shares = [0.07, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30]
store_list = [30, 50, 80]
r = 4
SH_ROWS = {}
LBm = MS["月度_基准"][0]
for st in store_list:
    ws.cell(row=r, column=1, value="门店数：").font = F_BOLD
    c = ws.cell(row=r, column=2, value=st); c.font = F_INPUT; c.number_format = FMT_INT; c.fill = FILL_KEY
    stcell = f"$B${r}"; r += 1
    hdr = ["目标份额", "抖音核销间夜/月", "相对现状新增间夜/月", "该份额下的增量比例", "增量间夜/月（受空房上限约束）", "总部 4% 分成/月", "总部抖音收入合计/月（分成 + 管理费）", "相对现状的总部月增量：替代口径（4%）", "混合口径（4%）", "新增部分按总部主导分成（混合口径）", "加 1% 渠道费后的总部月增量（混合 4%）", "门店端月变化（混合口径）", "新增间夜占系统空房比例", "产能换算：所需新增售出 GMV/月", "产能换算：所需总部直播小时/月（成熟期）"]
    for j, h in enumerate(hdr, 1):
        c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
    r += 1
    for shv in shares:
        c = ws.cell(row=r, column=1, value=shv); c.font = F_INPUT; c.number_format = FMT_PCT
        nights = f"({stcell}*{A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')})"
        empty = f"({stcell}*{A_base('ROOMS')}*(1-{A_base('OCC')})*{A_base('DAYS')})"
        dn = f"$A{r}*{nights}"; ddn = f"MAX(0,$A{r}-{A_base('SHARE0')}*{A_base('SHARE_VPO')})*{nights}"
        price = mref('月度_基准', LBm['PRICE']); inc0 = mref('月度_基准', LBm['INC'])
        incr = f"({inc0}*MAX({A_base('INC_FLOOR')},1-{A_base('INC_DECAY')}*MAX(0,$A{r}-{A_base('SHARE0')}*{A_base('SHARE_VPO')})/0.1))"
        incn = f"MIN({ddn}*{incr},{empty}*{A_base('CAP_SHARE')})"
        hq_inc, hq_sub = mref('月度_基准', LBm['HQ_INC_GAIN']), mref('月度_基准', LBm['HQ_SUB_GAIN'])
        hq_inc_m, hq_sub_m = mref('月度_基准', LBm['HQ_INC_GAIN_M']), mref('月度_基准', LBm['HQ_SUB_GAIN_M'])
        f = [f"={dn}",
             f"={ddn}",
             f"={incr}",
             f"={incn}",
             f"={dn}*{price}*{A_base('HQ_TAKE')}",
             f"={dn}*{price}*({A_base('HQ_TAKE')}+{mref('月度_基准', LBm['DY_FEE_RATE'])})",
             f"={ddn}*{hq_sub}",
             f"=E{r}*{hq_inc}+({ddn}-E{r})*{hq_sub}",
             f"=E{r}*{hq_inc_m}+({ddn}-E{r})*{hq_sub_m}",
             f"=I{r}+0.01*{ddn}*{price}",
             f"=E{r}*{mref('月度_基准', LBm['STORE_INC_CONTRIB'])}-({ddn}-E{r})*{mref('月度_基准', LBm['STORE_SUB_LOSS'])}",
             f"=IF({ddn}>0,E{r}/{empty},0)",
             f"={ddn}/{A_base('REDEEM')}*{price}",
             f"=N{r}/({A_base('B_GPH_MATURE')}*{A_base('WEEKDAY_VOL')})"]
        for j, ff in enumerate(f, 2):
            c = ws.cell(row=r, column=j, value=ff); c.font = F_CALC; c.alignment = ALIGN_R
            c.number_format = FMT_PCT if j in (4, 13) else FMT_INT
        SH_ROWS[(st, shv)] = r; r += 1
    ws.cell(row=r, column=1, value="份额上限").font = F_BOLD
    c = ws.cell(row=r, column=2, value=f"=\"增量份额上限 \"&TEXT({A_base('CAP_SHARE')}*(1-{A_base('OCC')})/{A_base('OCC')},\"0.0%\")&\"；按基准增量比例折算的总份额上限 \"&TEXT({A_base('CAP_SHARE')}*(1-{A_base('OCC')})/{A_base('OCC')}/{inc0},\"0.0%\")"); c.font = F_NOTE
    r += 2
ws.column_dimensions["A"].width = 14
for j in range(2, 17): ws.column_dimensions[get_column_letter(j)].width = 18
ws.freeze_panes = "B4"

# ---------------- 敏感性（稳态月度，基准情景参数）----------------
ws = ws_sens
ws["A1"] = "敏感性：总部直播间的每小时经济、投流保本 ROI、门店视角"; ws["A1"].font = F_H1
ws["A2"] = "公式引用假设表基准列与基准月度表的派生参数。矩阵一回答「总部付费主播每小时要卖多少才不亏」，矩阵二回答「总部出钱投流要多高 ROI 才打平」，矩阵三回答「门店什么时候不亏」。"; ws["A2"].font = F_NOTE
# 稳态参数（基准列）
sr = 4
def sp(label, formula, fmt=FMT_DEC):
    global sr
    ws.cell(row=sr, column=1, value=label).font = F_LABEL
    c = ws.cell(row=sr, column=2, value=formula); c.font = F_CALC; c.number_format = fmt
    sr += 1
    return f"$B${sr-1}"
S_PRICE = sp("券价（基准定价档）", f"=CHOOSE({A_base('PRICING_SEL')},{A_base('P1_PRICE')},{A_base('P2_PRICE')},{A_base('P3_PRICE')})")
S_VOL = sp("有效销量系数", f"=CHOOSE({A_base('PRICING_SEL')},{A_base('P1_VOL')},{A_base('P2_VOL')},{A_base('P3_VOL')})*IF({A_base('WEEKDAY_ONLY')}=1,{A_base('WEEKDAY_VOL')},1)")
S_INC = sp("增量比例", f"=(1-IF({A_base('WEEKDAY_ONLY')}=1,{A_base('SOLDOUT_WD')},{A_base('SOLDOUT_ANY')}))*(1-{A_base('WOULD_BOOK')})", FMT_PCT)
S_CFHQ = sp("被替代间夜总部收入", f"={A_base('OTA_SHARE')}*IF({A_base('MGMT_BASE')}=1,{A_base('ADR')},{A_base('ADR')}*(1-{A_base('OTA_CTRL')})*(1-{A_base('OTA_COMM')}))*{A_base('MGMT_FEE')}+(1-{A_base('OTA_SHARE')})*{A_base('ADR')}*{A_base('MGMT_FEE')}")
S_TAKE = sp("每元核销 GMV 的总部增量收入", f"={A_base('HQ_TAKE')}+IF({A_base('MGMT_BASE')}=1,{A_base('MGMT_FEE')},(1-{A_base('DY_FEE')}-{A_base('DY_PAY_FEE')}-{A_base('HQ_TAKE')})*{A_base('MGMT_FEE')})-(1-{S_INC})*{S_CFHQ}/{S_PRICE}", '0.0000')
S_COST = sp("团队稳态月成本（人力、设备、场地、投流，扣抵减）", f"=({A_base('B_SAL_LEAD')}+{A_base('B_SAL_HOST')}+{A_base('B_SAL_CTRL')}+{A_base('B_SAL_ADS')})*(1+{A_base('SOCIAL')})+{A_base('B_BACKUP_HOST')}+{A_base('B_EQUIP')}/{A_base('B_EQUIP_MONTHS')}+{A_base('B_SPACE')}+{A_base('B_ADS')}-{A_base('ABSORB_BRAND')}*({A_base('BRAND_BUDGET')}+{A_base('BRAND_SALARY')}*(1+{A_base('SOCIAL')}))", FMT_INT)
ws.cell(row=sr, column=1, value="注：方案二保留督导岗，督导人力两方案相同，边际成本中相抵；主播提成在矩阵公式内按核销 GMV 计。").font = F_NOTE
sr += 2
# 矩阵一：总部直播间每小时经济（总部每小时净得 − 主播成本，含挤占；基准参数，混合口径）
ws.cell(row=sr, column=1, value="矩阵一：行 = 成熟期每小时售出 GMV（九折口径，元/小时）；列 = 总部分成 × 主播付费方式。单元格 = 总部每小时净得（扣主播成本与对门店自播的挤占）。").font = F_BOLD
sr += 1
gph_list = [1500, 2000, 2500, 3000, 4000, 5000, 6000]
cols_def = [("4%，时薪 150 无提成", "HQ_MIX_GAIN", "150", "0"), ("8%，时薪 150 无提成", "HQ_MIX_GAIN_M", "150", "0"), ("8%，时薪 135 + 2% 提成", "HQ_MIX_GAIN_M", "135", f"{A_base('VH_COMM')}"), ("8%，纯提成 5%（总部付）", "HQ_MIX_GAIN_M", "0", "0.05"), ("8%，门店付佣 12%（二V）", "HQ_MIX_GAIN_M", "0", "0")]
ws.cell(row=sr, column=1, value="每小时 GMV \\ 分成与付费").font = F_BOLD
for j, (lab, _, _, _) in enumerate(cols_def, 2):
    c = ws.cell(row=sr, column=j, value=lab); c.font = F_BOLD; c.alignment = ALIGN_C
hdr_row = sr; sr += 1
LBm = MS["月度_基准"][0]
for gph in gph_list:
    c = ws.cell(row=sr, column=1, value=gph); c.font = F_INPUT; c.number_format = FMT_INT
    for j, (lab, gain, hourly, comm) in enumerate(cols_def, 2):
        nights_h = f"($A{sr}*{A_base('WEEKDAY_VOL')}*{A_base('REDEEM')}/{A_base('P1_PRICE')})"
        f = f"={nights_h}*('月度_基准'!{LBm[gain]}-{A_base('B_CANNIB')}*'月度_基准'!{LBm['HQ_MIX_GAIN']})-{hourly}-({comm})*$A{sr}*{A_base('WEEKDAY_VOL')}*{A_base('REDEEM')}"
        c = ws.cell(row=sr, column=j, value=f); c.font = F_CALC; c.number_format = FMT_INT; c.alignment = ALIGN_R
    sr += 1
sr += 1
# 矩阵二：投流保本 ROI
ws.cell(row=sr, column=1, value="矩阵二：投流保本 ROI（售出 GMV ÷ 投流）。行 = 总部承担的投流比例；列 = 总部分成 × 核销率。单元格 = 总部口径打平所需的 ROI（混合口径，含工作日系数）。").font = F_BOLD
sr += 1
share_list = [1.0, 0.5, 0.25]
cols2 = [("4%，核销 45%", "HQ_MIX_GAIN", 0.45), ("4%，核销 55%", "HQ_MIX_GAIN", 0.55), ("4%，核销 65%", "HQ_MIX_GAIN", 0.65), ("8%，核销 45%", "HQ_MIX_GAIN_M", 0.45), ("8%，核销 55%", "HQ_MIX_GAIN_M", 0.55), ("8%，核销 65%", "HQ_MIX_GAIN_M", 0.65)]
ws.cell(row=sr, column=1, value="总部承担比例 \\ 分成与核销率").font = F_BOLD
for j, (lab, _, _) in enumerate(cols2, 2):
    c = ws.cell(row=sr, column=j, value=lab); c.font = F_BOLD; c.alignment = ALIGN_C
hdr_row2 = sr; sr += 1
for shr in share_list:
    c = ws.cell(row=sr, column=1, value=shr); c.font = F_INPUT; c.number_format = FMT_PCT
    for j, (lab, gain, rd) in enumerate(cols2, 2):
        f = f"=$A{sr}/({rd}*{A_base('WEEKDAY_VOL')}/{A_base('P1_PRICE')}*'月度_基准'!{LBm[gain]})"
        c = ws.cell(row=sr, column=j, value=f); c.font = F_CALC; c.number_format = FMT_DEC; c.alignment = ALIGN_R
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
ST_VPS = srow("单店月售出券数（九折、按基线校准倒推）", f"=IF({A_base('CAL_MODE')}=1,{A_base('SHARE0')}*{A_base('STORES0')}*{A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')}*{A_base('P1_PRICE')},{A_base('BASE_HQ_COMM')}/{A_base('HQ_TAKE')})/{A_base('REDEEM')}/{A_base('P1_PRICE')}/{A_base('STORES0')}", FMT_DEC)
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
        wd = f"IF({inc_row}=26,{A_base('WEEKDAY_VOL')},1)"
        f = f"={ST_VPS}*{A_base(volkey)}*{wd}*{A_base('REDEEM')}*('单位经济'!{ucol}${inc_row}*'单位经济'!{ucol}$14-(1-'单位经济'!{ucol}${inc_row})*'单位经济'!{ucol}$19-{A_base('AP_COMM')}*{A_base('COMM_BY_STORE')}*'单位经济'!{ucol}$5)-{A_base('STORE_HOURS')}*{A_base('MGR_SALARY')}/{A_base('WORK_HOURS')}"
        c = ws.cell(row=r, column=j, value=f); c.font = F_LINK; c.number_format = FMT_INT; c.alignment = ALIGN_R
    r += 1
ws.cell(row=r, column=1, value="注：已扣除门店自播的店长时间成本（按假设表的每月直播小时数 × 店长小时成本）和门店承担的开播提成（按核销 GMV）。").font = F_NOTE; r += 2
ws.cell(row=r, column=1, value="总部每月从该店抖音单获得的增量收入（元）").font = F_BOLD; r += 1
for j, h in enumerate(hdr, 1):
    c = ws.cell(row=r, column=j, value=h); c.font = F_H2; c.fill = FILL_H2; c.alignment = ALIGN_C
r += 1
for lab, inc_row in [("不限日期券", 29), ("工作日券（周日至周四）", 30)]:
    ws.cell(row=r, column=1, value=lab).font = F_LABEL
    for j, (ucol, volkey) in enumerate([("C", "P1_VOL"), ("D", "P2_VOL"), ("E", "P3_VOL")], 2):
        wd = f"IF({inc_row}=30,{A_base('WEEKDAY_VOL')},1)"
        f = f"={ST_VPS}*{A_base(volkey)}*{wd}*{A_base('REDEEM')}*'单位经济'!{ucol}${inc_row}"
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
    ("流水均按挂牌价口径；总部管理费 3.5% 默认按客人支付金额计提（决策人口径“流水”），可切换为按门店到账；抖音平台侧扣费 = 住宿类目综合费率 8%（已含 0.6% 支付手续费，核验确认），支付手续费参数默认 0；抖音售出 GMV 为券面金额，核销 GMV 为结算口径，按 50% / 30% / 20% 分三个月核销；工作日券按销量系数折减。", F_LABEL),
    ("增量比例 = （1 − 核销落在满房日的比例）×（1 − 原本就会预订本品牌的比例）。替代间夜按 OTA 与直订加权的对照口径计算门店与总部的得失。", F_LABEL),
    ("方案一A 与方案三的门店自播按现状口径（不限日期券、不做工作日折减）计算；新店前 3 个月按爬坡入住率计算间夜与空房；增量间夜受空房上限约束：增量间夜 = MIN(核销间夜 × 增量比例, 系统空房间夜 × 上限比例)。方案一A 不含总部投入；方案一B 增加 1 名直播督导、培训、门店设备补贴，开播提成按核销 GMV 计、默认由门店承担（可切换）；方案二在一B 基础上（保留督导）增加 4 人团队与兼职备播、设备、场地、投流，并可抵减现有品牌预算（开关）；方案二+ 在方案二基础上加入配套机制（团队直播间订单的总部分成提高、门店分担投流）；方案三为服务商代播参照，按与总部直播间相同的每小时产出假设。", F_LABEL),
    ("门店端净收益变化 = 增量间夜 × 单夜贡献 − 替代间夜 × 单夜损失 − 门店直播时间成本。", F_LABEL),
    ("", F_LABEL),
    ("基线校准与口径核对", F_BOLD),
    ("决策人提供两项事实：当前抖音订单占比约 7%；上月总部抖音收入 4 万（无投流，按核销结算）。按系统 30 家店 × 100 间 × 85% × 30 天 = 76,500 间夜计：7% 份额对应约 5,355 个核销间夜、九折券核销 GMV 约 48 万/月，总部 4% 分成约 1.9 万，加抖音订单的 3.5% 管理费约 1.7 万，合计约 3.6 万，与「4 万」基本吻合；若把 4 万理解为纯 4% 分成，则核销 GMV 为 100 万、份额约 14.5%，与 7% 矛盾。模型默认按 7% 份额校准（CAL_MODE = 1），上月 4 万按「分成 + 管理费」口径核对；如公司确认 4 万为纯分成，把 CAL_MODE 改为 2 即可。", F_LABEL),
    ("方案口径：一A 现状延续；一B 规范化门店直播（默认不新招督导，由运营部现有人员兼任）；二P 在一B 基础上由现有品牌营销人员做总部直播试点（不新增人力）；二V 在二P 基础上引入兼职主播或达人按核销佣金带货（佣金从门店到账中划转，总部零固定成本）；二 / 二+ 为专职总部直播团队（现有分成 / 配套机制）；三为外包服务商。总部主导订单（试点、按单付费、团队、投流）的总部分成按 MECH_ON 开关执行 8%。", F_LABEL),
    ("回本规则（三道门）：基准回本月 ≤ 适用通过线（含固定人头 3 个月、零固定成本 6 个月）、基准现金谷底 ≥ 允许谷底（默认 −10 万）、悲观情景 12 个月相对现状 ≥ 允许亏损（默认 −5 万），三者同时成立为「通过」（悲观 12 个月内未回本则为「条件通过」）；门店约束（12 个月门店端净收益 ≥ 0、每抖音间夜期望收益 ≥ 下限、参与率 ≥ 下限）不满足则「不可执行」。「总部决策」表汇总每个方案的一次性现金、稳态月成本、12 个月净收益、回本月、现金谷底、第 12 月份额、新店预售贡献与盈亏平衡所需的份额提升。", F_LABEL),
    ("第三版新增口径：门店参与率 PART（不签协议的门店退出通兑券）；无专职督导时的提升倍数 AP_UPLIFT_LITE；增量比例随份额递减 INC_DECAY；新店开业预售 PRESALE_ON/PRESALE_V 与「其中新店预售贡献」归因行；设备按现金在开播月计入 EQUIP_CASH；方案二/二+ 默认不抵减品牌预算（ABSORB_BRAND = 0，全成本口径）；方案二H 为总部按小时付费主播的后备结构。第 1、2 月的核销滞后项取第 0 月稳态值，不存在人为低谷。", F_LABEL),
    ("", F_LABEL),
    ("数据来源与核验状态", F_BOLD),
    ("决策人提供的事实见假设表说明列；研究参数的来源见决策文档附录 C 与 research_notes 目录。", F_LABEL),
    ("外部参数来自 2026 年 11 月 4 日的网络检索，并于 11 月 5 日放开网络后做了两道核验（逐条打开引用页面核对原文；不看原文的独立交叉检索）。核验后的修正：支付手续费改为已含在 8% 内（参数设 0）、薪酬注释按职友集近一年口径更新；核验状态逐条见决策文档附录 D。核对后只需改假设表的对应单元格。", F_LABEL),
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
prow("v", "月售出券数（全系统，含工作日券折减）", [f"=IF({A_base('CAL_MODE')}=1,{A_base('SHARE0')}*{A_base('STORES0')}*{A_base('ROOMS')}*{A_base('OCC')}*{A_base('DAYS')}*{A_base('P1_PRICE')},{A_base('BASE_HQ_COMM')}/{A_base('HQ_TAKE')})/{A_base('REDEEM')}/{A_base('P1_PRICE')}*{A_base(t+'_VOL')}*IF({A_base('WEEKDAY_ONLY')}=1,{A_base('WEEKDAY_VOL')},1)" for t, _ in tiers])
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
    ("OTA 最低价规则风险", "中：携程已取消条款，美团条款仍在，但通兑券未被纳入比价", "低：与 OTA 展示价持平", "低：价格持平，权益不构成价格违规"),
    ("加盟店接受度", "低：替代间夜每夜少赚约 11 元", "高：替代间夜损失约 6 元", "中高：权益有少量成本"),
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
