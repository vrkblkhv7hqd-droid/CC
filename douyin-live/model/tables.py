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
OPTS = ["方案一A 门店自播，现状延续", "方案一B 规范化门店直播", "方案二P 总部直播试点（现有人员）", "方案二V 总部主导、按单付费", "方案二H 总部付费主播（按小时）", "方案二 总部直播团队（现有分成）", "方案二+ 总部直播团队（配套机制）", "方案三 外包服务商（参照）"]
# 情景对比表列号（v2 指标顺序）
COL = {"sold": 2, "red": 3, "n": 4, "inc": 5, "hqgross": 6, "hqinc": 7, "cost": 8, "net": 9, "relnet": 10, "paidrel": 11, "share12": 12, "store": 13, "sys": 14, "trough": 15, "paidm": 16, "hqpre": 17, "oneoff": 18, "stnight": 19, "storeok": 20, "brandinc": 21, "mkf": 22}
CODES = ["A", "B1", "P", "V", "VH", "B2", "B2M", "C"]
CIDX = {c: i for i, c in enumerate(CODES)}
_d = rows_by_label(ws)
scen_rows = {sn: _d[f"{sn}情景"][0] + 1 for sn in ["基准", "悲观", "乐观"]}
NOPT = len(OPTS)
SHORT = ["一A 现状延续", "一B 规范化门店直播", "二P 总部直播试点（现有人员）", "二V 总部主导、按单付费", "二H 总部付费主播（按小时）", "二 总部直播团队（现有分成）", "二+ 总部直播团队（配套机制）", "三 外包服务商（参照）"]
for sn, r0 in scen_rows.items():
    rows = []
    for i in range(NOPT):
        r = r0 + i
        pb = ws.cell(row=r, column=COL["paidrel"]).value
        rows.append([SHORT[i], wan(ws.cell(row=r, column=COL["red"]).value, 0), wan(ws.cell(row=r, column=COL["hqgross"]).value, 1), wan(ws.cell(row=r, column=COL["hqinc"]).value, 1), wan(ws.cell(row=r, column=COL["cost"]).value, 1),
                     wan(ws.cell(row=r, column=COL["net"]).value, 1), wan(ws.cell(row=r, column=COL["relnet"]).value, 1), ("—" if i == 0 else (pb if isinstance(pb, str) else f"第 {pb} 月")), pct(ws.cell(row=r, column=COL["share12"]).value, 1),
                     wan(ws.cell(row=r, column=COL["store"]).value, 0), wan(ws.cell(row=r, column=COL["sys"]).value, 0)])
    rows = [[x[0], x[1], x[3], x[4], x[5], x[6], x[7], x[9], x[10]] for x in rows]
    T[f"TABLE_SCEN_{sn}"] = md(["方案", "核销 GMV（万元）", "总部增量收入（万元）", "总部成本（万元）", "总部净收益（万元）", "相对现状（万元）", "回本月", "门店端变化（万元）", "系统合计（万元）"], rows)
# 三情景总部净收益汇总
rows = []
for i, o in enumerate(OPTS):
    rows.append([SHORT[i]] + [wan(ws.cell(row=scen_rows[sn] + i, column=COL["relnet"]).value, 1) for sn in ["悲观", "基准", "乐观"]] +
                [(lambda v: "—" if i == 0 else (v if isinstance(v, str) else f"第 {v} 月"))(ws.cell(row=scen_rows[sn] + i, column=COL["paidrel"]).value) for sn in ["悲观", "基准", "乐观"]] +
                [wan(ws.cell(row=scen_rows[sn] + i, column=COL["sys"]).value, 0) for sn in ["悲观", "基准", "乐观"]])
rows = [[x[0], x[1], x[2], x[3], x[5], x[8]] for x in rows]
T["TABLE_SCEN_SUMMARY"] = md(["方案", "相对现状的总部净收益 悲观（万元）", "基准（万元）", "乐观（万元）", "回本月（基准）", "系统合计 基准（万元）"], rows)
# 边际
d = rows_by_label(ws)
for key, lab in [("TABLE_MARGINAL", "边际：方案二（现有分成）相对方案一B"), ("TABLE_MARGINAL_M", "边际：方案二+（配套机制）相对方案一B"), ("TABLE_MARGINAL_P", "边际：方案二P（试点）相对方案一B"), ("TABLE_MARGINAL_V", "边际：方案二V（按单付费）相对方案一B")]:
    if lab not in d: continue
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
        ("一A 总部净收益", tcol("总部增量净收益", CIDX["A"], lambda v: wan(v, 1))),
        ("一B 总部净收益", tcol("总部增量净收益", CIDX["B1"], lambda v: wan(v, 1))),
        ("二P 总部净收益", tcol("总部增量净收益", CIDX["P"], lambda v: wan(v, 1))),
        ("二V 总部净收益", tcol("总部增量净收益", CIDX["V"], lambda v: wan(v, 1))),
        ("二+ 总部净收益", tcol("总部增量净收益", CIDX["B2M"], lambda v: wan(v, 1))),
        ("一B 相对现状累计", tcol("相对现状延续的累计净收益", CIDX["B1"], lambda v: wan(v, 1))),
        ("二V 相对现状累计", tcol("相对现状延续的累计净收益", CIDX["V"], lambda v: wan(v, 1))),
        ("二+ 相对现状累计", tcol("相对现状延续的累计净收益", CIDX["B2M"], lambda v: wan(v, 1)))]
rows = [[f"第 {i+1} 月"] + [c[1][i] for c in cols] for i in range(12)]
T["TABLE_MONTHLY_BASE"] = md(["月份（万元）"] + [c[0] for c in cols], rows)
def block_table(idx):
    cols = [("核销 GMV", tcol("核销 GMV（结算口径）", idx, lambda v: wan(v, 0))),
            ("份额", tcol("抖音份额（核销间夜 ÷ 系统间夜）", idx, lambda v: pct(v, 1))),
            ("总部增量收入", tcol("总部增量收入（扣被替代订单原有管理费）", idx, lambda v: wan(v, 1))), ("总部成本", tcol("总部成本合计", idx, lambda v: wan(v, 1))),
            ("总部净收益", tcol("总部增量净收益", idx, lambda v: wan(v, 1))), ("相对现状累计", tcol("相对现状延续的累计净收益", idx, lambda v: wan(v, 1))), ("门店端变化", tcol("门店端净收益变化（全系统）", idx, lambda v: wan(v, 1)))]
    rows = [[f"第 {i+1} 月"] + [c[1][i] for c in cols] for i in range(12)]
    return md(["月份（万元）"] + [c[0] for c in cols], rows)
T["TABLE_B2_MONTHLY"] = block_table(CIDX["B2"])
T["TABLE_B2M_MONTHLY"] = block_table(CIDX["B2M"])
T["TABLE_P_MONTHLY"] = block_table(CIDX["P"])
T["TABLE_V_MONTHLY"] = block_table(CIDX["V"])
T["TABLE_B1_MONTHLY"] = block_table(CIDX["B1"])

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
_nights_sys0 = base("STORES0") * base("ROOMS") * base("OCC") * base("DAYS")
_red0 = (base("SHARE0") * _nights_sys0 * base("P1_PRICE")) if base("CAL_MODE") == 1 else base("BASE_HQ_COMM") / base("HQ_TAKE")
T["BASE_SOLD0"] = wan(_red0 / base("REDEEM"), 0)
T["BASE_RED0"] = wan(_red0, 0)
T["BASE_VOUCHERS0"] = num(_red0 / base("REDEEM") / base("P1_PRICE"))
T["BASE_NIGHTS0"] = num(_red0 / base("P1_PRICE"))
T["SHARE0"] = pct(base("SHARE0"), 0)
T["SYS_NIGHTS0"] = num(_nights_sys0)
T["BASE_HQ_TAKE0"] = wan(_red0 * base("HQ_TAKE"), 1)
T["BASE_HQ_FEE0"] = wan(_red0 * base("MGMT_FEE"), 1)
T["BASE_HQ_TOTAL0"] = wan(_red0 * (base("HQ_TAKE") + base("MGMT_FEE")), 1)
T["BASE_HQ_COMM"] = wan(base("BASE_HQ_COMM"), 1)
T["OLD_RED0"] = wan(base("BASE_HQ_COMM") / base("HQ_TAKE"), 0)
T["OLD_SHARE0"] = pct(base("BASE_HQ_COMM") / base("HQ_TAKE") / base("P1_PRICE") / _nights_sys0, 1)
T["TEAM_SAL"] = wan((base("B_SAL_LEAD") + base("B_SAL_HOST") + base("B_SAL_CTRL") + base("B_SAL_ADS")) * (1 + base("SOCIAL")) + base("B_BACKUP_HOST"), 1)
T["BRAND_CREDIT"] = wan(base("BRAND_BUDGET") + base("BRAND_SALARY") * (1 + base("SOCIAL")), 1)

# ---- 文档正文用的单值占位符 ----
for sn, r0 in scen_rows.items():
    for i, code in enumerate(CODES):
        r = r0 + i
        T[f"NET_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["net"]).value, 1)
        T[f"REL_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["relnet"]).value, 1)
        T[f"GROSS_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["hqgross"]).value, 1)
        T[f"COST_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["cost"]).value, 1)
        T[f"STORE_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["store"]).value, 0)
        T[f"SYS_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["sys"]).value, 0)
        T[f"SHARE12_{code}_{sn}"] = pct(ws.cell(row=r, column=COL["share12"]).value, 1)
        _pb = ws.cell(row=r, column=COL["paidrel"]).value
        T[f"PB_{code}_{sn}"] = "—" if code == "A" else (_pb if isinstance(_pb, str) else f"第 {_pb} 月")
        T[f"STOREDIFF_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["store"]).value - ws.cell(row=r0, column=COL["store"]).value, 0)
        T[f"TROUGH_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["trough"]).value or 0, 1)
        T[f"HQPRE_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["hqpre"]).value or 0, 1)
        T[f"ONEOFF_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["oneoff"]).value or 0, 1)
        T[f"STNIGHT_{code}_{sn}"] = num(ws.cell(row=r, column=COL["stnight"]).value or 0, 1)
        T[f"STOREOK_{code}_{sn}"] = "—" if code == "A" else str(ws.cell(row=r, column=COL["storeok"]).value)
        T[f"BRANDINC_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["brandinc"]).value or 0, 1)
        T[f"MKF_{code}_{sn}"] = wan(ws.cell(row=r, column=COL["mkf"]).value or 0, 1)
        _pm = ws.cell(row=r, column=COL["paidm"]).value
        T[f"PBM_{code}_{sn}"] = "—" if code == "A" else (_pm if isinstance(_pm, str) else f"第 {_pm} 月")
    T[f"DIFF_B1_A_{sn}"] = wan(ws.cell(row=r0 + 1, column=COL["net"]).value - ws.cell(row=r0, column=COL["net"]).value, 1)
    T[f"DIFF_B1_A_ST_{sn}"] = f"{round(ws.cell(row=r0 + 1, column=COL['store']).value / 10000) - round(ws.cell(row=r0, column=COL['store']).value / 10000):,}"
ds = rows_by_label(ws)
for key, lab in [("B2", "边际：方案二（现有分成）相对方案一B"), ("B2M", "边际：方案二+（配套机制）相对方案一B"), ("P", "边际：方案二P（试点）相对方案一B"), ("V", "边际：方案二V（按单付费）相对方案一B")]:
    if lab not in ds: continue
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
_nights = _red0 / base("P1_PRICE")
_red = _red0
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
    net_b2m = ws.cell(row=r0 + CIDX["B2M"], column=COL["net"]).value
    T[f"NET_B2M_{sn}_NOABSORB"] = wan(net_b2m - (base("BRAND_BUDGET") + base("BRAND_SALARY") * (1 + base("SOCIAL"))) * _months_active, 1)
    T[f"RED_B1_{sn}"] = wan(ws.cell(row=r0 + 1, column=COL["red"]).value, 0)
    T[f"CHANNEL_FEE_1PCT_{sn}"] = wan(ws.cell(row=r0 + 1, column=COL["red"]).value * 0.01, 1)
T["CHANNEL_FEE_1PCT"] = T["CHANNEL_FEE_1PCT_基准"]
T["C_HOURS"] = num(base("C_HOURS"))
T["COST_B2M_INCR_基准"] = wan(ws.cell(row=scen_rows["基准"] + CIDX["B2M"], column=COL["cost"]).value - ws.cell(row=scen_rows["基准"] + 1, column=COL["cost"]).value, 1)
T["ST_PL_WD_P1"] = num(s.cell(row=14, column=2).value)
T["ST_DN0"] = num(_red0 / base("P1_PRICE") / base("STORES0"))
T["ST_SHARE0"] = pct(_red0 / base("P1_PRICE") / _nights_sys0, 1)
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
            T[f"NET_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=COL["net"]).value, 1)
            T[f"REL_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=COL["relnet"]).value, 1)
            T[f"SYS_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=COL["sys"]).value, 0)
            T[f"STORE_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=COL["store"]).value, 0)
            T[f"COST_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=COL["cost"]).value, 1)
            T[f"TROUGH_{code}_{sn}_{tag}"] = wan(vs.cell(row=r0 + i, column=COL["trough"]).value or 0, 1)
            _pb = vs.cell(row=r0 + i, column=COL["paidrel"]).value
            T[f"PB_{code}_{sn}_{tag}"] = "—" if code == "A" else (_pb if isinstance(_pb, str) else f"第 {_pb} 月")
VDIR = os.environ.get("VARIANT_DIR", "/home/user/CC/douyin-live/report/build")
read_variant(f"{VDIR}/variant_phased.xlsx", "PHASED")
read_variant(f"{VDIR}/variant_absorb.xlsx", "ABSORB")
read_variant(f"{VDIR}/variant_team2.xlsx", "TEAM2")
read_variant(f"{VDIR}/variant_nopresale.xlsx", "NOPRESALE")
read_variant(f"{VDIR}/variant_share145.xlsx", "SHARE145")
read_variant(f"{VDIR}/variant_share10.xlsx", "SHARE10")
read_variant(f"{VDIR}/variant_mkt05.xlsx", "MKT05")
read_variant(f"{VDIR}/variant_mkt10.xlsx", "MKT10")
read_variant(f"{VDIR}/variant_zeromkt05.xlsx", "ZEROMKT05")
read_variant(f"{VDIR}/variant_tier3.xlsx", "T3")
read_variant(f"{VDIR}/variant_chfee.xlsx", "CHFEE")
read_variant(f"{VDIR}/variant_zero.xlsx", "ZERO")
read_variant(f"{VDIR}/variant_sup.xlsx", "SUP")
# 方案二+ 相对一B 的第 12 月成本差、方案三第 12 月成本
dm = rows_by_label(m)
def m12(label, idx):
    return m.cell(row=dm[label][idx], column=15).value or 0
T["B2M_MARGIN_COST_M12"] = wan(m12("总部成本合计", CIDX["B2M"]) - m12("总部成本合计", 1), 1)
T["B2_MARGIN_COST_M12"] = wan(m12("总部成本合计", CIDX["B2"]) - m12("总部成本合计", 1), 1)
T["C_COST_M12"] = wan(m12("总部成本合计", CIDX["C"]), 1)
T["V_COST_M12"] = wan(m12("总部成本合计", CIDX["V"]), 1); T["P_COST_M12"] = wan(m12("总部成本合计", CIDX["P"]), 1); T["B1_COST_M12"] = wan(m12("总部成本合计", 1), 1)
T["B2M_HQSOLD_M12"] = wan(m12("总部直播间与投流售出 GMV", 1), 0)
# 打平所需月售出 GMV（总部口径）：稳态月成本差 ÷ 每元售出 GMV 的总部增量收入
_take_sold = float(T["S_TAKE"]) * base("REDEEM")
_take_sold_m = (float(T["S_TAKE"]) + (base("B_HQ_TAKE_ROOM") - base("HQ_TAKE")) - base("B_HOST_COMM")) * base("REDEEM")
_take_sold_b2 = (float(T["S_TAKE"]) - base("B_HOST_COMM")) * base("REDEEM")
T["BREAKEVEN_SOLD_MONTH"] = wan((m12("总部成本合计", CIDX["B2M"]) - m12("总部成本合计", 1)) / _take_sold_m, 0)
T["BREAKEVEN_SOLD_MONTH_B2"] = wan((m12("总部成本合计", CIDX["B2"]) - m12("总部成本合计", 1)) / _take_sold_b2, 0)
# 敏感性矩阵最大值
def grid_max(hdr_label):
    dsv = rows_by_label(sv); hdr = dsv[hdr_label][0]; vals = []
    r = hdr + 1
    while isinstance(sv.cell(row=r, column=1).value, (int, float)):
        vals += [sv.cell(row=r, column=c).value for c in range(2, 9) if sv.cell(row=r, column=c).value is not None]; r += 1
    return max(vals)
pass

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

def payback(v):
    if isinstance(v, (int, float)): return f"第 {int(v)} 月"
    return "12 个月内未回本"
# ---- 总部决策 ----
ws = wb["总部决策"]
ue = {}
for r in range(5, 30):
    lab = ws.cell(row=r, column=1).value; val = ws.cell(row=r, column=2).value
    if lab and lab != "方案": ue[lab] = val
    if lab == "方案": break
def ue_get(prefix):
    for k, v in ue.items():
        if k.startswith(prefix): return v
    return None
T["HQ_SUB_GAIN"] = num(ue_get("总部每替代间夜净得（现有"), 1)
T["HQ_INC_GAIN"] = num(ue_get("总部每增量间夜净得（现有"), 1)
T["HQ_SUB_GAIN_M"] = num(ue_get("总部每替代间夜净得（总部主导"), 1)
T["HQ_INC_GAIN_M"] = num(ue_get("总部每增量间夜净得（总部主导"), 1)
T["HQ_MIX_GAIN"] = num(ue_get("总部每抖音间夜净得（混合口径，4%"), 1)
T["HQ_MIX_GAIN_M"] = num(ue_get("总部每抖音间夜净得（混合口径，总部主导"), 1)
T["HQ_PER_PT_30"] = num(ue_get("份额每提升 1 个百分点的总部月净得（当前门店数，替代"), 0)
T["HQ_PER_PT_MIX_30"] = num(ue_get("份额每提升 1 个百分点的总部月净得（当前门店数，混合口径 4%"), 0)
T["HQ_PER_PT_MIX_M_30"] = num(ue_get("份额每提升 1 个百分点的总部月净得（当前门店数，混合口径 8%"), 0)
T["HQ_PER_PT_12"] = num(ue_get("份额每提升 1 个百分点的总部月净得（第 12 月门店数，替代"), 0)
T["HQ_PER_PT_MIX_12"] = num(ue.get("同上，混合口径 4%"), 0)
T["HQ_PER_PT_MIX_M_12"] = num(ue.get("同上，混合口径 8%"), 0)
T["BE_GPH_HOURLY"] = num(ue_get("保本每小时售出 GMV：总部付费主播，时薪无提成"), 0)
T["BE_GPH_HOURLY_COMM"] = num(ue_get("保本每小时售出 GMV：时薪 + 2% 提成"), 0)
T["HQ_ADS_BREAKEVEN_ROI"] = num(ue_get("总部独自投流的保本 ROI（4%"), 0)
T["HQ_ADS_BREAKEVEN_ROI_M"] = num(ue_get("总部独自投流的保本 ROI（总部主导"), 0)
T["SHARE_CAP_INC"] = pct(ue_get("份额上限：空房上限隐含的增量份额点"), 1)
T["SHARE_CAP_TOTAL"] = pct(ue_get("份额上限：按增量比例折算的总份额"), 0)
T["PAYBACK_RULE"] = str(int(ue_get("回本规则：含固定人头")))
T["PAYBACK_RULE_VAR"] = str(int(ue_get("回本规则：零固定成本")))
hdr_row = None
for r in range(10, 40):
    if ws.cell(row=r, column=1).value == "方案": hdr_row = r; break
HDR = [ws.cell(row=hdr_row, column=c).value for c in range(1, 40) if ws.cell(row=hdr_row, column=c).value]
NC = len(HDR)
# 重复表头（基准/乐观）按出现顺序编号
HIDX = {}
seen = {}
for i, h in enumerate(HDR):
    seen[h] = seen.get(h, 0) + 1
    HIDX[(h, seen[h])] = i
def hcol(h, k=1): return HIDX[(h, k)]
SHORT_DEC = {"方案一B 规范化门店直播": "一B 规范化门店直播", "方案二P 总部直播试点（现有人员）": "二P 总部直播试点（现有人员）", "方案二V 总部主导、按单付费": "二V 总部主导、按单付费", "方案二H 总部付费主播（按小时）": "二H 总部付费主播（按小时）",
             "方案二 总部直播团队（现有分成）": "二 总部直播团队（现有分成）", "方案二+ 总部直播团队（配套机制）": "二+ 总部直播团队（配套机制）", "方案三 外包服务商（参照）": "三 外包服务商（参照）"}
DEC_KEYS = {"一B 规范化门店直播": "B1", "二P 总部直播试点（现有人员）": "P", "二V 总部主导、按单付费": "V", "二H 总部付费主播（按小时）": "VH", "二 总部直播团队（现有分成）": "B2", "二+ 总部直播团队（配套机制）": "B2M", "三 外包服务商（参照）": "C"}
def read_dec_rows(ws_, hdr_row_):
    out = {}
    r = hdr_row_ + 1
    while ws_.cell(row=r, column=1).value:
        v = [ws_.cell(row=r, column=c).value for c in range(1, NC + 1)]
        lab = SHORT_DEC.get(v[0], v[0]); key = DEC_KEYS.get(lab)
        if key: out[key] = v
        r += 1
    return out
def dec_fill(T_, v, key, tag=""):
    sfx = f"_{tag}" if tag else ""
    ct = str(v[hcol("成本类型")])
    T_[f"DEC_{key}_CTYPE{sfx}"] = "固定" if "固定人头" in ct else ("准固定" if "准固定" in ct else "变动")
    T_[f"DEC_{key}_ONEOFF{sfx}"] = wan(v[hcol("一次性现金（元）")], 1); T_[f"DEC_{key}_MCOST{sfx}"] = wan(v[hcol("稳态月成本（第 12 月，基准，元）")], 1)
    for i, sc in enumerate(["悲观", "基准", "乐观"]):
        net = v[hcol("12 个月总部净收益 悲观")] if i == 0 else v[hcol("基准", 1)] if i == 1 else v[hcol("乐观", 1)]
        rel = v[hcol("相对现状延续 悲观")] if i == 0 else v[hcol("基准", 2)] if i == 1 else v[hcol("乐观", 2)]
        pb = v[hcol("回本月 悲观")] if i == 0 else v[hcol("基准", 3)] if i == 1 else v[hcol("乐观", 3)]
        sh = v[hcol("第 12 月份额 悲观")] if i == 0 else v[hcol("基准", 4)] if i == 1 else v[hcol("乐观", 4)]
        T_[f"DEC_{key}_NET_{sc}{sfx}"] = wan(net, 1); T_[f"DEC_{key}_REL_{sc}{sfx}"] = wan(rel, 1); T_[f"DEC_{key}_REL_{sc}_ABS{sfx}"] = wan(abs(rel), 1)
        T_[f"DEC_{key}_PB_{sc}{sfx}"] = payback(pb); T_[f"DEC_{key}_SH12_{sc}{sfx}"] = pct(sh, 1)
    T_[f"DEC_{key}_HQPRE{sfx}"] = wan(v[hcol("其中新店预售贡献（基准）")], 1)
    T_[f"DEC_{key}_PBM_基准{sfx}"] = payback(v[hcol("月度转正月 基准")])
    T_[f"DEC_{key}_TROUGH_悲观{sfx}"] = wan(v[hcol("现金谷底 悲观")], 1); T_[f"DEC_{key}_TROUGH_基准{sfx}"] = wan(v[hcol("现金谷底 基准")], 1)
    T_[f"DEC_{key}_BE30{sfx}"] = pct(v[hcol("盈亏平衡所需份额提升：替代口径（30 家店）")], 1); T_[f"DEC_{key}_BE12{sfx}"] = pct(v[hcol("替代口径（第 12 月门店数）")], 1)
    T_[f"DEC_{key}_BE30_MIX{sfx}"] = pct(v[hcol("混合 4%（30 家店）")], 1); T_[f"DEC_{key}_BE30_MIX_M{sfx}"] = pct(v[hcol("混合 8%（30 家店）")], 1)
    T_[f"DEC_{key}_STOREOK{sfx}"] = str(v[hcol("门店约束")]); T_[f"DEC_{key}_STNIGHT{sfx}"] = num(v[hcol("门店每抖音间夜期望收益（基准）")], 1)
    T_[f"DEC_{key}_RULE_MONTHS{sfx}"] = str(int(v[hcol("适用通过线（月）")])); T_[f"DEC_{key}_RULE{sfx}"] = str(v[hcol("判定")]).replace("条件通过（悲观 12 个月内未回本）", "条件通过（悲观未回本）")
    T_[f"DEC_{key}_MKT30{sfx}"] = f"{v[hcol('覆盖稳态月成本所需的营销费率（30 家店流水）')]*100:.2f}%"; T_[f"DEC_{key}_MKT12{sfx}"] = f"{v[hcol('同上（第 12 月门店数）')]*100:.2f}%"
    T_[f"DEC_{key}_BRANDINC{sfx}"] = wan(v[hcol("总部主导订单带来的总部收入（基准，12 个月）")], 1)
DEC = read_dec_rows(ws, hdr_row)
rows, rows2 = [], []
for lab, key in DEC_KEYS.items():
    if key not in DEC: continue
    v = DEC[key]; dec_fill(T, v, key)
    rows.append(f"| {lab} | {T[f'DEC_{key}_CTYPE']} | {T[f'DEC_{key}_ONEOFF']} | {T[f'DEC_{key}_MCOST']} | {T[f'DEC_{key}_PB_悲观']} | {T[f'DEC_{key}_PB_基准']} | {T[f'DEC_{key}_PB_乐观']} | {T[f'DEC_{key}_TROUGH_基准']} | {T[f'DEC_{key}_RULE']} |")
    rows2.append(f"| {lab} | {T[f'DEC_{key}_REL_悲观']} | {T[f'DEC_{key}_REL_基准']} | {T[f'DEC_{key}_REL_乐观']} | {T[f'DEC_{key}_HQPRE']} | {T[f'DEC_{key}_SH12_基准']} | {T[f'DEC_{key}_BE30']} | {T[f'DEC_{key}_BE30_MIX_M']} | {T[f'DEC_{key}_STOREOK']} |")
T["TABLE_HQ_DECISION"] = "\n".join(["| 方案 | 成本 | 一次性现金（万元） | 稳态月成本（万元） | 回本月 悲观 | 回本月 基准 | 回本月 乐观 | 现金谷底 基准（万元） | 判定 |", "|---|---|---:|---:|---|---|---|---:|---|"] + rows)
# 品牌营销费与品牌部损益
_r = hdr_row + 1
while ws.cell(row=_r, column=1).value: _r += 1
_mk_hdr = None; _br_hdr = None
for _rr in range(_r, _r + 40):
    _v = ws.cell(row=_rr, column=1).value
    if _v == "门店数": _mk_hdr = _rr
    if _v == "方案" and _mk_hdr: _br_hdr = _rr; break
if _mk_hdr:
    rows_mk = []
    for _rr in range(_mk_hdr + 1, _mk_hdr + 4):
        _v = [ws.cell(row=_rr, column=c).value for c in range(1, 6)]
        rows_mk.append(f"| {int(_v[0])} | {wan(_v[1],0)} | {wan(_v[2],1)} | {wan(_v[3],1)} | {wan(_v[4],1)} |")
        T[f"MKT{int(_v[0])}_REV"] = wan(_v[1], 0); T[f"MKT{int(_v[0])}_05"] = wan(_v[2], 1); T[f"MKT{int(_v[0])}_10"] = wan(_v[3], 1)
    T["BRAND_COST_MONTH"] = wan(ws.cell(row=_mk_hdr + 1, column=5).value, 1)
    T["TABLE_MKT_FEE"] = "\n".join(["| 门店数 | 月流水（万元） | 0.5% 营销费/月（万元） | 1.0% 营销费/月（万元） | 品牌部现有月成本（万元） |", "|---:|---:|---:|---:|---:|"] + rows_mk)
if _br_hdr:
    rows_br = []
    _rr = _br_hdr + 1
    while ws.cell(row=_rr, column=1).value:
        _v = [ws.cell(row=_rr, column=c).value for c in range(1, 11)]
        _lab = SHORT_DEC.get(_v[0], _v[0]); _key = DEC_KEYS.get(_lab)
        rows_br.append(f"| {_lab} | {wan(_v[1],1)} | {wan(_v[2],1)} | {wan(_v[3],1)} | {wan(_v[4],1)} | {wan(_v[5],1)} | {pct(_v[6],0)} | {pct(_v[7],0)} | {pct(_v[8],0)} |")
        if _key:
            T[f"BR_{_key}_INC_悲观"] = wan(_v[2], 1); T[f"BR_{_key}_INC_基准"] = wan(_v[3], 1); T[f"BR_{_key}_INC_乐观"] = wan(_v[4], 1); T[f"BR_{_key}_ADDCOST"] = wan(_v[5], 1); T[f"BR_{_key}_COV"] = pct(_v[6], 0); T[f"BR_{_key}_COV05"] = pct(_v[7], 0); T[f"BR_{_key}_COV10"] = pct(_v[8], 0)
        _rr += 1
    T["BRAND_COST_12M"] = wan(ws.cell(row=_br_hdr + 1, column=2).value, 1)
    T["MKT05_12M"] = wan(ws.cell(row=_br_hdr + 1, column=10).value, 1)
    T["TABLE_BRAND_PL"] = "\n".join(["| 方案 | 品牌部现有成本（12 个月，万元） | 可归属收入 悲观（万元） | 基准（万元） | 乐观（万元） | 该方案新增的总部成本（相对一B，基准，万元） | 覆盖率：不含营销费 | 加 0.5% 营销费 | 加 1% 营销费 |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"] + rows_br)
T["TABLE_HQ_DECISION2"] = "\n".join(["| 方案 | 相对现状 悲观（万元） | 基准（万元） | 乐观（万元） | 其中新店预售（基准，万元） | 第 12 月份额（基准） | 月度打平所需份额提升：替代口径（30 家店） | 混合口径 8%（30 家店） | 门店约束 |", "|---|---:|---:|---:|---:|---:|---:|---:|---|"] + rows2)
# ---- 份额情景 ----
ws = wb["份额情景"]
r = 4
blocks = {}
while r <= ws.max_row:
    if ws.cell(row=r, column=1).value == "门店数：":
        st = int(ws.cell(row=r, column=2).value); r += 2; rows = []
        while isinstance(ws.cell(row=r, column=1).value, (int, float)):
            v = [ws.cell(row=r, column=c).value for c in range(1, 16)]
            rows.append(v); r += 1
        blocks[st] = rows
    else: r += 1
for st, rows in blocks.items():
    lines = ["| 份额 | 抖音间夜/月 | 增量比例 | 总部抖音收入合计/月（万元） | 总部月增量：替代口径（万元） | 混合口径（万元） | 新增部分按 8%（万元） | 门店端月变化（万元） | 新增间夜占空房 | 所需新增售出 GMV/月（万元） |", "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for v in rows:
        lines.append(f"| {pct(v[0],0)} | {num(v[1])} | {pct(v[3],0)} | {wan(v[6],1)} | {wan(v[7],1)} | {wan(v[8],1)} | {wan(v[9],1)} | {wan(v[11],1)} | {pct(v[12],0)} | {wan(v[13],0)} |")
    T[f"TABLE_SHARE_{st}"] = "\n".join(lines)
    for v in rows:
        tag = f"{int(round(v[0]*100))}"
        T[f"SH{st}_{tag}_NIGHTS"] = num(v[1]); T[f"SH{st}_{tag}_INC"] = pct(v[3], 0); T[f"SH{st}_{tag}_HQTAKE"] = wan(v[5], 1); T[f"SH{st}_{tag}_HQGROSS"] = wan(v[6], 1)
        T[f"SH{st}_{tag}_DSUB"] = wan(v[7], 1); T[f"SH{st}_{tag}_DMIX"] = wan(v[8], 1); T[f"SH{st}_{tag}_DM8"] = wan(v[9], 1); T[f"SH{st}_{tag}_DFEE"] = wan(v[10], 1)
        T[f"SH{st}_{tag}_STORE"] = wan(v[11], 1); T[f"SH{st}_{tag}_EMPTY"] = pct(v[12], 0); T[f"SH{st}_{tag}_GMV"] = wan(v[13], 0); T[f"SH{st}_{tag}_HOURS"] = num(v[14])
# ---- 基线校准（基准月度表派生区）----
ws = wb["月度_基准"]
D = {}
for r in range(1, 200):
    lab = ws.cell(row=r, column=1).value
    if lab: D[lab] = ws.cell(row=r, column=2).value
T["BASE_RED0_V2"] = wan(D["基线：当前每月抖音核销 GMV"], 0)
T["BASE_SOLD0_V2"] = wan(D["基线：对应的每月售出 GMV（按本情景核销率倒推）"], 0)

# 变体的总部决策表（渠道费 1%、新招督导）
for _tag, _fn in [("CHFEE", "variant_chfee.xlsx"), ("SUP", "variant_sup.xlsx"), ("ZERO", "variant_zero.xlsx"), ("ABSORB", "variant_absorb.xlsx"), ("TEAM2", "variant_team2.xlsx"), ("NOPRESALE", "variant_nopresale.xlsx"), ("SHARE145", "variant_share145.xlsx"), ("SHARE10", "variant_share10.xlsx"), ("MKT05", "variant_mkt05.xlsx"), ("MKT10", "variant_mkt10.xlsx"), ("ZEROMKT05", "variant_zeromkt05.xlsx")]:
    _vch = f"{VDIR}/{_fn}"
    if not os.path.exists(_vch): continue
    _wb2 = load_workbook(_vch, data_only=True); _ws2 = _wb2["总部决策"]
    _hr = None
    for _r in range(10, 40):
        if _ws2.cell(row=_r, column=1).value == "方案": _hr = _r; break
    for _key, _v in read_dec_rows(_ws2, _hr).items():
        dec_fill(T, _v, _key, _tag)
# 起点份额 × 情景 → 回本月（一B、二P、二V）
rows = []
for lab, key in [("一B 规范化门店直播", "B1"), ("二P 总部直播试点（现有人员）", "P"), ("二V 总部主导、按单付费", "V")]:
    for tag, sh in [("", "7%"), ("_SHARE10", "10%"), ("_SHARE145", "14.5%（上月 4 万倒推）")]:
        if f"DEC_{key}_PB_基准{tag}" in T:
            rows.append(f"| {lab} | {sh} | {T[f'DEC_{key}_PB_悲观{tag}']} | {T[f'DEC_{key}_PB_基准{tag}']} | {T[f'DEC_{key}_PB_乐观{tag}']} | {T[f'DEC_{key}_REL_基准{tag}']} |")
T["TABLE_PAYBACK_SHARE"] = "\n".join(["| 方案 | 起点份额 | 回本月 悲观 | 回本月 基准 | 回本月 乐观 | 12 个月相对现状 基准（万元） |", "|---|---|---|---|---|---:|"] + rows)
# 敏感性：矩阵一、二导出
_sv = wb["敏感性"]; _dsv = rows_by_label(_sv)
def grid_table(hdr_label, ncols, fmt_cell, fmt_row, headers):
    hdr = _dsv[hdr_label][0]; lines = ["| " + " | ".join(headers) + " |", "|" + "---:|" * len(headers)]
    r = hdr + 1
    while isinstance(_sv.cell(row=r, column=1).value, (int, float)):
        lines.append("| " + fmt_row(_sv.cell(row=r, column=1).value) + " | " + " | ".join(fmt_cell(_sv.cell(row=r, column=c).value) for c in range(2, 2 + ncols)) + " |"); r += 1
    return "\n".join(lines)
T["TABLE_HOURLY"] = grid_table("每小时 GMV \\ 分成与付费", 5, lambda v: num(v, 0), lambda v: num(v, 0), ["每小时售出 GMV（元）", "4%，时薪 150 无提成", "8%，时薪 150 无提成", "8%，时薪 135 + 2% 提成", "8%，纯提成 5%（总部付）", "8%，门店付佣 12%（二V）"])
T["TABLE_ADS_ROI"] = grid_table("总部承担比例 \\ 分成与核销率", 6, lambda v: num(v, 1), lambda v: pct(v, 0), ["总部承担的投流比例", "4%，核销 45%", "4%，核销 55%", "4%，核销 65%", "8%，核销 45%", "8%，核销 55%", "8%，核销 65%"])
# 督导与团队的盈亏平衡份额（替代口径）
_sup_cost = base("AP_SUP_SALARY") * (1 + base("SOCIAL"))
T["SUP_COST"] = wan(_sup_cost, 1)
T["SUP_BE30"] = T.get("DEC_B1_BE30_SUP", "")
T["SUP_BE12"] = T.get("DEC_B1_BE12_SUP", "")
_stores12 = base("STORES0") + base("NEW_PM") * 12
T["STORES12"] = num(round(_stores12))
T["TEAM_COST_GROSS"] = wan((base("B_SAL_LEAD") + base("B_SAL_HOST") + base("B_SAL_CTRL") + base("B_SAL_ADS")) * (1 + base("SOCIAL")) + base("B_BACKUP_HOST") + base("B_EQUIP") / base("B_EQUIP_MONTHS") + base("B_SPACE") + base("B_ADS"), 1)
T["V_COMM_BASE"] = pct(base("V_COMM"), 0); T["V_HOURS_BASE"] = num(base("V_HOURS")); T["V_GPH_BASE"] = num(base("V_GPH"))
T["PILOT_HOURS_BASE"] = num(base("PILOT_HOURS")); T["PILOT_GPH_BASE"] = num(base("PILOT_GPH")); T["PILOT_EQUIP"] = wan(base("PILOT_EQUIP"), 1)
T["B_HQ_TAKE_ROOM"] = pct(base("B_HQ_TAKE_ROOM"), 0)
T["V_START"] = num(base("V_START")); T["PRESALE_V_BASE"] = num(base("PRESALE_V")); T["PRESALE_V_PESS"] = num(pess("PRESALE_V")); T["PRESALE_V_OPT"] = num(opt("PRESALE_V")); T["PRESALE_INC_BASE"] = pct(base("PRESALE_INC"), 0)
T["PAYBACK_RULE_VAR"] = str(int(base("PAYBACK_RULE_VAR"))); T["TROUGH_RULE"] = wan(abs(base("TROUGH_RULE")), 0); T["PESS_LOSS_RULE"] = wan(abs(base("PESS_LOSS_RULE")), 0)
T["SHARE_VPO"] = num(base("SHARE_VPO"), 1)
T["AP_UPLIFT_LITE_BASE"] = f"{base('AP_UPLIFT_LITE'):.2f}"; T["AP_UPLIFT_BASE"] = f"{base('AP_UPLIFT'):.2f}"; T["PART_PESS"] = pct(pess("PART"), 0); T["INC_DECAY_BASE"] = pct(base("INC_DECAY"), 0)
T["HOST_HOURLY_BASE"] = num(base("HOST_HOURLY")); T["VH_HOURS_BASE"] = num(base("VH_HOURS")); T["VH_COMM"] = pct(base("VH_COMM"), 0)
T["TROUGH_RULE"] = wan(abs(base("TROUGH_RULE")), 0); T["PESS_LOSS_RULE"] = wan(abs(base("PESS_LOSS_RULE")), 0)
# 校准三口径
_n0 = _nights_sys0
for _k, _den, _lab in [("A", base("HQ_TAKE"), "纯 4% 分成"), ("B", base("HQ_TAKE") + base("MGMT_FEE"), "分成 + 管理费"), ("C", base("HQ_TAKE") / base("REDEEM"), "4% 按售出计提")]:
    _red = base("BASE_HQ_COMM") / _den
    T[f"CAL_{_k}_RED"] = wan(_red, 0); T[f"CAL_{_k}_NIGHTS"] = num(_red / base("P1_PRICE")); T[f"CAL_{_k}_SHARE"] = pct(_red / base("P1_PRICE") / _n0, 1)
T["A_DRIFT_PESS"] = pct(abs(pess("A_DRIFT")), 0)
json.dump(T, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("tables:", len(T), "->", OUT)
