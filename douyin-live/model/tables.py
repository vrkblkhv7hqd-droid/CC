# -*- coding: utf-8 -*-
"""从已重算的模型读取数值，输出决策文档用的 Markdown 表格（JSON：占位符 -> 表格文本）。"""
import sys, json
from openpyxl import load_workbook

MODEL = sys.argv[1] if len(sys.argv) > 1 else "/home/user/CC/douyin-live/model/住小叮抖音直播财务模型.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/user/CC/douyin-live/report/build/tables.json"
wb = load_workbook(MODEL, data_only=True)
T = {}

def wan(v, d=1):
    if v is None or isinstance(v, str): return v if v else ""
    return f"{v/10000:,.{d}f}"
def num(v, d=0):
    if v is None or isinstance(v, str): return v if v else ""
    return f"{v:,.{d}f}"
def pct(v, d=0):
    if v is None or isinstance(v, str): return v if v else ""
    return f"{v*100:.{d}f}%"
def md(headers, rows, align=None):
    align = align or (["---"] + ["---:"] * (len(headers) - 1))
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(align) + " |"]
    for r in rows: out.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(out)
def rows_by_label(ws):
    d = {}
    for r in range(1, ws.max_row + 1):
        v = ws.cell(row=r, column=1).value
        if v: d.setdefault(v, []).append(r)
    return d

# ---- 情景对比（三情景）----
ws = wb["情景对比"]
OPTS = ["方案一A 门店自播，现状延续", "方案一B 规范化门店直播", "方案二 总部直播团队（现有分成）", "方案二+ 总部直播团队 + 配套机制", "方案三 外包服务商（参照）"]
_d = rows_by_label(ws)
scen_rows = {sn: _d[f"{sn}情景"][0] + 1 for sn in ["基准", "悲观", "乐观"]}
NOPT = len(OPTS)
SHORT = ["一A 现状延续", "一B 规范化门店直播", "二 总部直播团队（现有分成）", "二+ 总部直播团队（配套机制）", "三 外包服务商（参照）"]
for sn, r0 in scen_rows.items():
    rows = []
    for i in range(NOPT):
        r = r0 + i
        rows.append([SHORT[i], wan(ws.cell(row=r, column=3).value, 0), wan(ws.cell(row=r, column=6).value, 1), wan(ws.cell(row=r, column=7).value, 1),
                     wan(ws.cell(row=r, column=8).value, 1), ws.cell(row=r, column=9).value if isinstance(ws.cell(row=r, column=9).value, str) else f"第 {ws.cell(row=r, column=9).value} 月",
                     wan(ws.cell(row=r, column=10).value, 0), wan(ws.cell(row=r, column=11).value, 0)])
    T[f"TABLE_SCEN_{sn}"] = md(["方案", "核销 GMV（万元）", "总部增量收入（万元）", "总部成本（万元）", "总部净收益（万元）", "相对现状转正", "门店端变化（万元）", "系统合计（万元）"], rows)
# 三情景总部净收益汇总
rows = []
for i, o in enumerate(OPTS):
    rows.append([SHORT[i]] + [wan(ws.cell(row=scen_rows[sn] + i, column=8).value, 1) for sn in ["悲观", "基准", "乐观"]] +
                [wan(ws.cell(row=scen_rows[sn] + i, column=11).value, 0) for sn in ["悲观", "基准", "乐观"]])
T["TABLE_SCEN_SUMMARY"] = md(["方案", "总部净收益 悲观（万元）", "总部净收益 基准（万元）", "总部净收益 乐观（万元）", "系统合计 悲观（万元）", "系统合计 基准（万元）", "系统合计 乐观（万元）"], rows)
# 边际
d = rows_by_label(ws)
for key, lab in [("TABLE_MARGINAL", "边际：方案二（现有分成）相对方案一B"), ("TABLE_MARGINAL_M", "边际：方案二+（配套机制）相对方案一B")]:
    r0 = d[lab][0]
    rows = []
    for r in range(r0 + 1, r0 + 4):
        rows.append([ws.cell(row=r, column=2).value] + [wan(ws.cell(row=r, column=c).value, 1) for c in range(3, 10)])
    T[key] = md(["情景", "多售出 GMV（万元）", "多核销 GMV（万元）", "总部多增收入（万元）", "总部多成本（万元）", "总部净收益差（万元）", "门店端差（万元）", "系统合计差（万元）"], rows)

# ---- 单位经济 ----
u = wb["单位经济"]
rows = []
for r, dec in [(5, 1), (6, 2), (7, 2), (8, 2), (9, 2), (10, 2), (11, 2), (12, 1), (13, 1), (14, 2)]:
    rows.append([u.cell(row=r, column=1).value] + [num(u.cell(row=r, column=c).value, dec) for c in range(2, 6)])
T["TABLE_UNIT"] = md(["每间夜（元）", "OTA 订单", "抖音九折券", "抖音平价券", "抖音平价加权益券"], rows)
rows = []
for r, fmt in [(17, "n2"), (18, "n2"), (19, "n2"), (20, "n2"), (21, "n1"), (22, "p")]:
    f = (lambda v: pct(v, 0)) if fmt == "p" else (lambda v: num(v, int(fmt[1])))
    rows.append([u.cell(row=r, column=1).value] + [f(u.cell(row=r, column=c).value) for c in range(2, 6)])
T["TABLE_SUB"] = md(["替代一夜（元）", "OTA 订单", "抖音九折券", "抖音平价券", "抖音平价加权益券"], rows)
rows = []
for r in [25, 26]:
    rows.append([u.cell(row=r, column=1).value, pct(u.cell(row=r, column=2).value, 1)])
for r in [27, 28, 29, 30]:
    rows.append([u.cell(row=r, column=1).value] + [num(u.cell(row=r, column=c).value, 2) for c in range(3, 6)])
T["TABLE_EXPECT"] = md(["项目", "九折券", "平价券", "平价加权益券"], [r if len(r) == 4 else [r[0], r[1], r[1], r[1]] for r in rows])
T["INC_ANY"] = pct(u.cell(row=25, column=2).value, 1); T["INC_WD"] = pct(u.cell(row=26, column=2).value, 1)
T["BE_P1"] = pct(u.cell(row=22, column=3).value, 0); T["BE_P2"] = pct(u.cell(row=22, column=4).value, 0); T["BE_P3"] = pct(u.cell(row=22, column=5).value, 0)
for key, r, c in [("U_OTA_STORE", 11, 2), ("U_P1_STORE", 11, 3), ("U_P2_STORE", 11, 4), ("U_OTA_HQ", 10, 2), ("U_P1_HQ", 10, 3), ("U_P2_HQ", 10, 4),
                  ("U_P1_LOSS", 19, 3), ("U_P2_LOSS", 19, 4), ("U_P3_LOSS", 19, 5), ("U_P1_HQGAIN", 20, 3), ("U_P2_HQGAIN", 20, 4), ("U_P1_CONTRIB", 14, 3), ("U_P2_CONTRIB", 14, 4),
                  ("U_P1_EXP_WD", 28, 3), ("U_P2_EXP_WD", 28, 4), ("U_P3_EXP_WD", 28, 5), ("U_P1_EXP_ANY", 27, 3), ("U_P1_HQEXP_WD", 30, 3)]:
    T[key] = num(u.cell(row=r, column=c).value, 1)

# ---- 定价对比 ----
p = wb["定价对比"]
rows = []
spec = [(5, "n0"), (6, "n2"), (7, "n0"), (8, "w"), (9, "n0"), (10, "w"), (11, "p"), (12, "w1"), (13, "w1"), (14, "w1"), (15, "n0"), (16, "n0")]
for r, fmt in spec:
    if fmt == "w": f = lambda v: wan(v, 0)
    elif fmt == "w1": f = lambda v: wan(v, 1)
    elif fmt == "p": f = lambda v: pct(v, 0)
    else: f = lambda v, d=int(fmt[1]): num(v, d)
    lab = p.cell(row=r, column=1).value
    if fmt.startswith("w"): lab += "（万元）"
    rows.append([lab] + [f(p.cell(row=r, column=c).value) for c in range(2, 5)])
for r in range(18, 23):
    lab = p.cell(row=r, column=1).value
    if not lab: continue
    vals = [p.cell(row=r, column=c).value for c in range(2, 5)]
    if all(v is None for v in vals): rows.append([f"**{lab}**", "", "", ""])
    else: rows.append([lab] + [v or "" for v in vals])
T["TABLE_PRICING"] = md(["项目（稳态月度，30 家店，门店自播产出）", "九折券", "平价券", "平价加权益券"], rows)

# ---- 门店损益 ----
s = wb["门店损益"]
T["ST_NIGHTS"] = num(s.cell(row=4, column=2).value); T["ST_REV"] = wan(s.cell(row=5, column=2).value, 1)
T["ST_VPS"] = num(s.cell(row=7, column=2).value); T["ST_DN"] = num(s.cell(row=8, column=2).value); T["ST_SHARE"] = pct(s.cell(row=9, column=2).value, 1)
rows = [[s.cell(row=r, column=1).value] + [num(s.cell(row=r, column=c).value) for c in range(2, 5)] for r in (13, 14)]
T["TABLE_STORE_PL"] = md(["单店每月净收益变化（元）", "九折券", "平价券", "平价加权益券"], rows)
rows = [[s.cell(row=r, column=1).value] + [num(s.cell(row=r, column=c).value) for c in range(2, 5)] for r in (19, 20)]
T["TABLE_STORE_HQ"] = md(["总部每月从该店抖音单获得的增量收入（元）", "九折券", "平价券", "平价加权益券"], rows)

# ---- 敏感性 ----
sv = wb["敏感性"]
d = rows_by_label(sv)
def grid(hdr_label, col_fmt):
    hdr = d[hdr_label][0]
    cols = [sv.cell(row=hdr, column=c).value for c in range(2, 9) if sv.cell(row=hdr, column=c).value is not None]
    rows = []
    r = hdr + 1
    while isinstance(sv.cell(row=r, column=1).value, (int, float)):
        rows.append([num(sv.cell(row=r, column=1).value)] + [wan(sv.cell(row=r, column=c).value, 1) for c in range(2, 2 + len(cols))])
        r += 1
    return md([hdr_label.replace("\\", "/")] + [col_fmt(c) for c in cols], rows)
T["TABLE_SENS1"] = grid("每小时 GMV \\ ROI", lambda c: f"ROI {c:g}")
T["TABLE_SENS2"] = grid("每小时 GMV \\ 人力成本", lambda c: f"人力 {c/10000:.0f} 万/月")
hdr = d["增量比例 \\ 定价档"][0]
rows = []
r = hdr + 1
while isinstance(sv.cell(row=r, column=1).value, (int, float)):
    rows.append([pct(sv.cell(row=r, column=1).value)] + [num(sv.cell(row=r, column=c).value, 1) for c in range(2, 5)])
    r += 1
T["TABLE_SENS3"] = md(["增量比例 / 定价档", "九折", "平价", "平价加权益"], rows)
T["S_TAKE"] = f"{sv.cell(row=8, column=2).value:.4f}"
T["S_COST"] = wan(sv.cell(row=9, column=2).value, 1)

# ---- 月度（基准）关键行：方案二与方案一B 的月度净收益 ----
m = wb["月度_基准"]
d = rows_by_label(m)
def series(label, idx):
    r = d[label][idx]
    return [m.cell(row=r, column=c).value or 0 for c in range(4, 16)]
# 月度表转置：行 = 月份
def tcol(lab, idx, f): return [f(v) for v in series(lab, idx)]
cols = [("门店数", tcol("门店数（月末）", 0, lambda v: num(v))),
        ("一A 总部净收益", tcol("总部增量净收益", 0, lambda v: wan(v, 1))),
        ("一B 总部净收益", tcol("总部增量净收益", 1, lambda v: wan(v, 1))),
        ("二 总部净收益", tcol("总部增量净收益", 2, lambda v: wan(v, 1))),
        ("二+ 总部净收益", tcol("总部增量净收益", 3, lambda v: wan(v, 1))),
        ("三 总部净收益", tcol("总部增量净收益", 4, lambda v: wan(v, 1))),
        ("一B 累计", tcol("累计净收益（第 1 月起）", 1, lambda v: wan(v, 1))),
        ("二+ 累计", tcol("累计净收益（第 1 月起）", 3, lambda v: wan(v, 1)))]
rows = [[f"第 {i+1} 月"] + [c[1][i] for c in cols] for i in range(12)]
T["TABLE_MONTHLY_BASE"] = md(["月份（万元）"] + [c[0] for c in cols], rows)
def block_table(idx):
    cols = [("售出 GMV", tcol("售出 GMV（券面）", idx, lambda v: wan(v, 0))), ("核销 GMV", tcol("核销 GMV（结算口径）", idx, lambda v: wan(v, 0))),
            ("总部增量收入", tcol("总部增量收入", idx, lambda v: wan(v, 1))), ("总部成本", tcol("总部成本合计", idx, lambda v: wan(v, 1))),
            ("总部净收益", tcol("总部增量净收益", idx, lambda v: wan(v, 1))), ("门店端变化", tcol("门店端净收益变化（全系统）", idx, lambda v: wan(v, 1)))]
    rows = [[f"第 {i+1} 月"] + [c[1][i] for c in cols] for i in range(12)]
    return md(["月份（万元）"] + [c[0] for c in cols], rows)
T["TABLE_B2_MONTHLY"] = block_table(2)
T["TABLE_B2M_MONTHLY"] = block_table(3)

# ---- 假设表（附录）----
a = wb["假设"]
rows = []
for r in range(5, a.max_row + 1):
    lab = a.cell(row=r, column=1).value
    if not lab: continue
    key = a.cell(row=r, column=2).value
    if not key:
        rows.append([f"**{lab}**", "", "", "", "", ""]); continue
    fmt = a.cell(row=r, column=4).number_format
    def f(v):
        if v is None: return ""
        if "%" in fmt: return pct(v, 1)
        if isinstance(v, float) and abs(v) < 100 and v != int(v): return f"{v:,.2f}"
        return f"{v:,.0f}"
    rows.append([lab, f(a.cell(row=r, column=3).value), f(a.cell(row=r, column=4).value), f(a.cell(row=r, column=5).value), a.cell(row=r, column=6).value or "", (a.cell(row=r, column=7).value or "").replace("|", "／")])
T["TABLE_ASSUMPTIONS"] = md(["参数", "悲观", "基准", "乐观", "单位", "说明与来源"], rows, ["---", "---:", "---:", "---:", "---", "---"])

# 基线数字
def base(key):
    for r in range(5, a.max_row + 1):
        if a.cell(row=r, column=2).value == key: return a.cell(row=r, column=4).value
T["SYS_REV_MONTH"] = wan(base("STORES0") * base("ROOMS") * base("ADR") * base("OCC") * base("DAYS"), 0)
T["HQ_FEE_MONTH"] = wan(m.cell(row=d["总部管理费基线（无抖音）"][0], column=3).value, 1)
T["BASE_SOLD0"] = wan(base("BASE_HQ_COMM") / base("HQ_TAKE") / base("BASE_REDEEM_EST"), 0)
T["BASE_RED0"] = wan(base("BASE_HQ_COMM") / base("HQ_TAKE"), 0)
T["BASE_VOUCHERS0"] = num(base("BASE_HQ_COMM") / base("HQ_TAKE") / base("BASE_REDEEM_EST") / base("P1_PRICE"))
T["BASE_NIGHTS0"] = num(base("BASE_HQ_COMM") / base("HQ_TAKE") / base("P1_PRICE"))
T["TEAM_SAL"] = wan((base("B_SAL_LEAD") + base("B_SAL_HOST") + base("B_SAL_CTRL") + base("B_SAL_ADS")) * (1 + base("SOCIAL")) + base("B_BACKUP_HOST"), 1)
T["BRAND_CREDIT"] = wan(base("BRAND_BUDGET") + base("BRAND_SALARY") * (1 + base("SOCIAL")), 1)

# ---- 文档正文用的单值占位符 ----
CODES = ["A", "B1", "B2", "B2M", "C"]
for sn, r0 in scen_rows.items():
    for i, code in enumerate(CODES):
        r = r0 + i
        T[f"NET_{code}_{sn}"] = wan(ws.cell(row=r, column=8).value, 1)
        T[f"COST_{code}_{sn}"] = wan(ws.cell(row=r, column=7).value, 1)
        T[f"STORE_{code}_{sn}"] = wan(ws.cell(row=r, column=10).value, 0)
        T[f"SYS_{code}_{sn}"] = wan(ws.cell(row=r, column=11).value, 0)
    T[f"DIFF_B1_A_{sn}"] = wan(ws.cell(row=r0 + 1, column=8).value - ws.cell(row=r0, column=8).value, 1)
    T[f"DIFF_B1_A_ST_{sn}"] = f"{round(ws.cell(row=r0 + 1, column=10).value / 10000) - round(ws.cell(row=r0, column=10).value / 10000):,}"
ds = rows_by_label(ws)
for key, lab in [("B2", "边际：方案二（现有分成）相对方案一B"), ("B2M", "边际：方案二+（配套机制）相对方案一B")]:
    r0 = ds[lab][0]
    for r in range(r0 + 1, r0 + 4):
        sn = ws.cell(row=r, column=2).value
        hq, st, sy = ws.cell(row=r, column=7).value, ws.cell(row=r, column=8).value, ws.cell(row=r, column=9).value
        T[f"MARG_{key}_{sn}_HQ"] = wan(hq, 1); T[f"MARG_{key}_{sn}_ST"] = wan(st, 1); T[f"MARG_{key}_{sn}_SYS"] = wan(sy, 1)
        T[f"MARG_{key}_{sn}_HQ_ABS"] = wan(abs(hq), 1); T[f"MARG_{key}_{sn}_SYS_ABS"] = wan(abs(sy), 1); T[f"MARG_{key}_{sn}_ST_ABS"] = wan(abs(st), 1)
T["S_TAKE_FEN"] = f"{float(T['S_TAKE'])*100*base('REDEEM'):.1f}"   # 每元售出 GMV 核销后总部增量收入（分）
# 团队稳态每月净增成本（扣抵减）：团队薪酬 + 设备摊销 + 场地 + 投流一半 − 品牌抵减
team_month = (base("B_SAL_LEAD") + base("B_SAL_HOST") + base("B_SAL_CTRL") + base("B_SAL_ADS")) * (1 + base("SOCIAL")) + base("B_EQUIP") / base("B_EQUIP_MONTHS") + base("B_SPACE") + base("B_ADS") * (1 - base("B_ADS_STORE_SHARE")) - (base("BRAND_BUDGET") + base("BRAND_SALARY") * (1 + base("SOCIAL")))
T["B2_MARGIN_MONTHLY"] = wan(team_month, 1)
T["STORE_MONTH_P1"] = wan(p.cell(row=13, column=2).value, 1)
T["HQ_MONTH_P1"] = wan(p.cell(row=12, column=2).value, 1)
# 上月复盘（不限日期券口径）
_nights = base("BASE_HQ_COMM") / base("HQ_TAKE") / base("P1_PRICE")
_red = base("BASE_HQ_COMM") / base("HQ_TAKE")
_inc_any = u.cell(row=25, column=2).value
T["RETRO_STORE"] = wan(_nights * u.cell(row=27, column=3).value, 1)
T["RETRO_HQ"] = wan(_nights * u.cell(row=29, column=3).value, 1)
T["RETRO_DYFEE"] = wan(_red * (base("MGMT_FEE") if base("MGMT_BASE") == 1 else (1 - base("DY_FEE") - base("DY_PAY_FEE") - base("HQ_TAKE")) * base("MGMT_FEE")), 1)
T["RETRO_SUBFEE"] = wan(_nights * (1 - _inc_any) * u.cell(row=18, column=2).value, 1)
T["ST_PL_WD_P3"] = num(s.cell(row=14, column=4).value); T["ST_PL_ANY_P1"] = num(s.cell(row=13, column=2).value)
# ---- 补充占位符 ----
T["WB_BASE"] = pct(base("WOULD_BOOK"), 0)
T["REDEEM_BASE"] = pct(base("REDEEM"), 0)
def pess(key):
    for r in range(5, a.max_row + 1):
        if a.cell(row=r, column=2).value == key: return a.cell(row=r, column=3).value
def opt(key):
    for r in range(5, a.max_row + 1):
        if a.cell(row=r, column=2).value == key: return a.cell(row=r, column=5).value
T["REDEEM_PESS"] = pct(pess("REDEEM"), 0); T["REDEEM_OPT"] = pct(opt("REDEEM"), 0)
T["REDEEM_DROP_PCT"] = pct((base("REDEEM") - pess("REDEEM")) / base("REDEEM"), 0)
T["WEEKDAY_VOL_BASE"] = pct(1 - base("WEEKDAY_VOL"), 0)
T["DY_PAY_FEE"] = pct(base("DY_PAY_FEE"), 1)
T["STORE_RATE_PCT"] = pct(1 - base("DY_FEE") - base("DY_PAY_FEE") - base("HQ_TAKE"), 1)
T["VAR_COST_BASE"] = num(base("VAR_COST"))
T["B_START"] = num(base("B_START"))
_months_active = 12 - int(base("B_START")) + 1
T["BRAND_CREDIT_12M"] = wan((base("BRAND_BUDGET") + base("BRAND_SALARY") * (1 + base("SOCIAL"))) * _months_active, 1)
for sn in ["基准", "悲观", "乐观"]:
    r0 = scen_rows[sn]
    net_b2m = ws.cell(row=r0 + 3, column=8).value
    T[f"NET_B2M_{sn}_NOABSORB"] = wan(net_b2m - (base("BRAND_BUDGET") + base("BRAND_SALARY") * (1 + base("SOCIAL"))) * _months_active, 1)
    T[f"RED_B1_{sn}"] = wan(ws.cell(row=r0 + 1, column=3).value, 0)
    T[f"CHANNEL_FEE_1PCT_{sn}"] = wan(ws.cell(row=r0 + 1, column=3).value * (1 - base("DY_FEE") - base("DY_PAY_FEE") - base("HQ_TAKE")) * 0.01, 1)
T["CHANNEL_FEE_1PCT"] = T["CHANNEL_FEE_1PCT_基准"]
T["C_HOURS"] = num(base("C_HOURS"))
T["COST_B2M_INCR_基准"] = wan(ws.cell(row=scen_rows["基准"] + 3, column=7).value - ws.cell(row=scen_rows["基准"] + 1, column=7).value, 1)
T["ST_PL_WD_P1"] = num(s.cell(row=14, column=2).value)
T["ST_DN0"] = num(base("BASE_HQ_COMM") / base("HQ_TAKE") / base("P1_PRICE") / base("STORES0"))
T["ST_SHARE0"] = pct(base("BASE_HQ_COMM") / base("HQ_TAKE") / base("P1_PRICE") / base("STORES0") / (base("ROOMS") * base("OCC") * base("DAYS")), 1)
T["ST_PL_ANY_P3"] = num(s.cell(row=13, column=4).value)
# 达人代播参照：每个核销间夜（九折券 90 元，达人佣金 15% 按核销结算）
_price = base("P1_PRICE"); _kol = 0.15
_plat = _price * (base("DY_FEE") + base("DY_PAY_FEE")); _hq = _price * (base("HQ_TAKE") + base("MGMT_FEE"))
_store = _price * (1 - base("DY_FEE") - base("DY_PAY_FEE") - base("HQ_TAKE") - base("MGMT_FEE")); _comm = _price * _kol
rows = [["总部收入", num(_hq, 1), num(_hq - _comm, 1), num(_hq, 1)],
        ["门店净得", num(_store, 1), num(_store, 1), num(_store - _comm, 1)],
        ["与 OTA 订单门店净得的差", "", num(_store - u.cell(row=11, column=2).value, 1), num(_store - _comm - u.cell(row=11, column=2).value, 1)]]
T["TABLE_KOL"] = md(["每个核销间夜（元）", "自播九折券", "达人代播，总部付佣", "达人代播，门店付佣"], rows)
# ---- 变体工作簿（分阶段启动、不抵减品牌、平价加权益档）----
import os
def read_variant(path, tag):
    if not os.path.exists(path): return
    vb = load_workbook(path, data_only=True); vs = vb["情景对比"]; vd = rows_by_label(vs)
    vrows = {sn: vd[f"{sn}情景"][0] + 1 for sn in ["基准", "悲观", "乐观"]}
    for sn, r0 in vrows.items():
        for i, code in enumerate(CODES):
            T[f"NET_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=8).value, 1)
            T[f"SYS_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=11).value, 0)
            T[f"STORE_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=10).value, 0)
read_variant("/home/user/CC/douyin-live/report/build/variant_phased.xlsx", "PHASED")
read_variant("/home/user/CC/douyin-live/report/build/variant_noabsorb.xlsx", "NOABSORB")
read_variant("/home/user/CC/douyin-live/report/build/variant_tier3.xlsx", "T3")
# 方案二+ 相对一B 的第 12 月成本差、方案三第 12 月成本
dm = rows_by_label(m)
def m12(label, idx):
    return m.cell(row=dm[label][idx], column=15).value or 0
T["B2M_MARGIN_COST_M12"] = wan(m12("总部成本合计", 3) - m12("总部成本合计", 1), 1)
T["B2_MARGIN_COST_M12"] = wan(m12("总部成本合计", 2) - m12("总部成本合计", 1), 1)
T["C_COST_M12"] = wan(m12("总部成本合计", 4), 1)
T["B2M_HQSOLD_M12"] = wan(m12("总部直播间与投流售出 GMV", 1), 0)
# 打平所需月售出 GMV（总部口径）：稳态月成本差 ÷ 每元售出 GMV 的总部增量收入
_take_sold = float(T["S_TAKE"]) * base("REDEEM")
T["BREAKEVEN_SOLD_MONTH"] = wan((m12("总部成本合计", 3) - m12("总部成本合计", 1)) / _take_sold, 0)
T["BREAKEVEN_SOLD_MONTH_B2"] = wan((m12("总部成本合计", 2) - m12("总部成本合计", 1)) / _take_sold, 0)
T["HQ_ADS_BREAKEVEN_ROI"] = f"{1/_take_sold:.0f}"
# 敏感性矩阵最大值
def grid_max(hdr_label):
    dsv = rows_by_label(sv); hdr = dsv[hdr_label][0]; vals = []
    r = hdr + 1
    while isinstance(sv.cell(row=r, column=1).value, (int, float)):
        vals += [sv.cell(row=r, column=c).value for c in range(2, 9) if sv.cell(row=r, column=c).value is not None]; r += 1
    return max(vals)
T["SENS1_MAX"] = wan(grid_max("每小时 GMV \\ ROI"), 1); T["SENS2_MAX"] = wan(grid_max("每小时 GMV \\ 人力成本"), 1)

# ---- 核验统计（report/build/verification.json，由 verify_summary.py 生成）----
import os as _os, re as _re
_vp = "/home/user/CC/douyin-live/report/build/verification.json"
if _os.path.exists(_vp):
    _V = json.load(open(_vp, encoding="utf-8"))
    _checks = _V["checks"]
    T["VER_URL_TOTAL"] = str(len(_checks))
    T["VER_URL_OK"] = str(sum(1 for c in _checks if c.get("status") != "unreachable"))
    T["VER_URL_UNREACH"] = str(sum(1 for c in _checks if c.get("status") == "unreachable"))
    # 同一编号有「补」记录时以补抓结果为准
    _rows = {}
    for _k, _v in _V["row_verdicts"].items():
        _b = _re.sub(r"（.*?）", "", _k)
        if _b not in _rows or "补" in _k: _rows[_b] = _v["verdict"]
    T["VER_ROW_SUP"] = str(sum(1 for v in _rows.values() if v == "supported"))
    T["VER_ROW_PART"] = str(sum(1 for v in _rows.values() if v == "partially_supported"))
    T["VER_ROW_UNV"] = str(sum(1 for v in _rows.values() if v not in ("supported", "partially_supported")))
    _vd = _V["verdicts"]
    T["VER_COR_ITEMS"] = str(len(_vd))
    for _name, _key in [("VER_COR_CONF", "confirmed"), ("VER_COR_ADJ", "adjust"), ("VER_COR_REF", "refuted"), ("VER_COR_UNV", "unverifiable")]:
        T[_name] = str(sum(1 for v in _vd if v.get("verdict") == _key))
    T["VER_SEARCHES"] = str(_V.get("searches", 0))
json.dump(T, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("tables:", len(T), "->", OUT)
