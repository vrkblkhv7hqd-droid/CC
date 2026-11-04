# -*- coding: utf-8 -*-
"""从财务模型（已重算的 xlsx）读取数值，生成决策文档用的图表 PNG。"""
import os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from openpyxl import load_workbook

MODEL = sys.argv[1] if len(sys.argv) > 1 else "/home/user/CC/douyin-live/model/住小叮抖音直播财务模型.xlsx"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/home/user/CC/douyin-live/report/charts"
os.makedirs(OUT, exist_ok=True)

# 字体
for f in font_manager.findSystemFonts():
    if "wqy-zenhei" in f.lower():
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "WenQuanYi Zen Hei"
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 11

# 调色板（dataviz 参考调色板）
C_BLUE, C_ORANGE, C_AQUA, C_YELLOW, C_VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#6250d6"
C_GRAY, C_GRID, C_AXIS, C_INK, C_INK2, C_MUTED = "#b5b4ad", "#e1e0d9", "#c3c2b7", "#0b0b0b", "#52514e", "#898781"
SURFACE = "#ffffff"
OPT_COLORS = {"A": C_GRAY, "B1": C_BLUE, "B2": C_ORANGE, "B2M": C_VIOLET, "C": C_AQUA}
OPT_NAMES = {"A": "方案一A 门店自播·现状延续", "B1": "方案一B 规范化门店直播", "B2": "方案二 总部直播团队（现有分成）", "B2M": "方案二+ 总部团队 + 配套机制", "C": "方案三 外包服务商（参照）"}
CODES = ["A", "B1", "B2", "B2M", "C"]

wb = load_workbook(MODEL, data_only=True)

def style_ax(ax):
    ax.set_facecolor(SURFACE)
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]:
        ax.spines[s].set_color(C_AXIS); ax.spines[s].set_linewidth(0.8)
    ax.yaxis.grid(True, color=C_GRID, linewidth=0.8); ax.set_axisbelow(True)
    ax.tick_params(colors=C_INK2, length=0)
    for lab in ax.get_xticklabels() + ax.get_yticklabels(): lab.set_color(C_INK2)

def rows_by_label(ws):
    d = {}
    for r in range(1, ws.max_row + 1):
        v = ws.cell(row=r, column=1).value
        if v: d.setdefault(v, []).append(r)
    return d

def monthly_series(sheet, label, idx):
    ws = wb[sheet]; d = rows_by_label(ws); r = d[label][idx]
    return [ws.cell(row=r, column=c).value or 0 for c in range(4, 16)]  # 第1到12月

def wan(v): return v / 10000.0

# ---------- 图1：基准情景累计总部净收益 ----------
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=200)
style_ax(ax)
months = list(range(1, 13))
for i, code in enumerate(CODES):
    ys = [wan(v) for v in monthly_series("月度_基准", "累计净收益（第 1 月起）", i)]
    ax.plot(months, ys, color=OPT_COLORS[code], linewidth=2.2, marker="o", markersize=4.5, label=OPT_NAMES[code])
    ax.annotate(f"{ys[-1]:.0f}", (12, ys[-1]), textcoords="offset points", xytext=(6, 0), va="center", fontsize=10, color=C_INK2)
ax.axhline(0, color=C_AXIS, linewidth=0.8)
ax.set_xticks(months); ax.set_xticklabels([f"第{m}月" for m in months])
ax.set_ylabel("总部累计增量净收益（万元）", color=C_INK2)
ax.set_title("基准情景：五个方案的总部累计增量净收益（第 1 到 12 月）", loc="left", color=C_INK, fontsize=12, fontweight="bold")
ax.legend(frameon=False, loc="upper left", fontsize=9.5)
fig.tight_layout(); fig.savefig(f"{OUT}/chart1_cum_net_base.png", facecolor=SURFACE); plt.close(fig)

# ---------- 图2：三情景 × 四方案 总部 12 个月净收益 ----------
ws = wb["情景对比"]
_d = rows_by_label(ws)
scen_rows = {sn: _d[f"{sn}情景"][0] + 1 for sn in ["悲观", "基准", "乐观"]}
codes = CODES
fig, ax = plt.subplots(figsize=(9.5, 4.8), dpi=200)
style_ax(ax)
scens = ["悲观", "基准", "乐观"]
width = 0.16
for i, code in enumerate(codes):
    vals = [wan(ws.cell(row=scen_rows[s] + i, column=8).value) for s in scens]
    xs = [j + (i - 2) * width for j in range(3)]
    bars = ax.bar(xs, vals, width=width - 0.02, color=OPT_COLORS[code], label=OPT_NAMES[code])
    for x, v in zip(xs, vals):
        ax.annotate(f"{v:.0f}", (x, v), textcoords="offset points", xytext=(0, 4 if v >= 0 else -12), ha="center", fontsize=9, color=C_INK2)
ax.axhline(0, color=C_AXIS, linewidth=0.8)
ax.set_xticks(range(3)); ax.set_xticklabels([f"{s}情景" for s in scens])
ax.set_ylabel("12 个月总部增量净收益（万元）", color=C_INK2)
ax.set_title("三种情景下五个方案的 12 个月总部增量净收益", loc="left", color=C_INK, fontsize=12, fontweight="bold")
ax.legend(frameon=False, loc="upper left", fontsize=9.5)
fig.tight_layout(); fig.savefig(f"{OUT}/chart2_scenarios.png", facecolor=SURFACE); plt.close(fig)

# ---------- 图3：每间夜 100 元去哪了（单位经济）----------
u = wb["单位经济"]
cols = {"OTA 订单": 2, "抖音九折券": 3, "抖音平价券": 4, "抖音平价加权益券": 5}
fig, ax = plt.subplots(figsize=(9, 4.0), dpi=200)
style_ax(ax); ax.xaxis.grid(True, color=C_GRID, linewidth=0.8); ax.yaxis.grid(False)
labels = list(cols.keys())
segs = [("客人节省", lambda c: 100 - u.cell(row=5, column=c).value, "#f0efec"),
        ("平台拿走", lambda c: u.cell(row=6, column=c).value, C_GRAY),
        ("总部收入", lambda c: u.cell(row=10, column=c).value, C_BLUE),
        ("门店净得", lambda c: u.cell(row=11, column=c).value, C_AQUA)]
left = [0] * len(labels)
for name, fn, color in segs:
    vals = [fn(c) for c in cols.values()]
    ax.barh(labels, vals, left=left, color=color, height=0.55, label=name, edgecolor=SURFACE, linewidth=2)
    for i, (l, v) in enumerate(zip(left, vals)):
        if v >= 6:
            ax.text(l + v / 2, i, f"{v:.1f}", ha="center", va="center", fontsize=9.5, color=("#ffffff" if color in (C_BLUE, C_AQUA) else C_INK))
    left = [l + v for l, v in zip(left, vals)]
ax.invert_yaxis(); ax.set_xlim(0, 100)
ax.set_xlabel("元（以挂牌价 100 元的一间夜为基准）", color=C_INK2)
ax.set_title("一间夜 100 元去哪了：OTA 订单与三档抖音券的分配", loc="left", color=C_INK, fontsize=12, fontweight="bold")
ax.legend(frameon=False, loc="lower right", fontsize=9.5, ncol=4, bbox_to_anchor=(1, -0.32))
fig.tight_layout(); fig.savefig(f"{OUT}/chart3_unit_economics.png", facecolor=SURFACE); plt.close(fig)

# ---------- 图4：门店每抖音间夜期望收益 vs 增量比例 ----------
contrib = {t: u.cell(row=14, column=c).value for t, c in [("九折", 3), ("平价", 4), ("平价加权益", 5)]}
loss = {t: u.cell(row=19, column=c).value for t, c in [("九折", 3), ("平价", 4), ("平价加权益", 5)]}
inc_any, inc_wd = u.cell(row=25, column=3).value, u.cell(row=26, column=3).value
fig, ax = plt.subplots(figsize=(9, 4.8), dpi=200)
style_ax(ax)
xs = [i / 100 for i in range(0, 71)]
tier_colors = {"九折": C_BLUE, "平价": C_ORANGE, "平价加权益": C_AQUA}
for t in ["九折", "平价", "平价加权益"]:
    ys = [x * contrib[t] - (1 - x) * loss[t] for x in xs]
    ax.plot([x * 100 for x in xs], ys, color=tier_colors[t], linewidth=2.2, label=f"{t}券")
    be = loss[t] / (contrib[t] + loss[t]) * 100
    ax.scatter([be], [0], color=tier_colors[t], s=36, zorder=5)
    ax.annotate(f"盈亏平衡 {be:.0f}%", (be, 0), textcoords="offset points", xytext=(4, -14 - (0 if t == "九折" else (12 if t == "平价" else 24))), fontsize=9, color=tier_colors[t])
ax.axhline(0, color=C_AXIS, linewidth=0.8)
for x, lab in [(inc_any * 100, "不限日期券假设"), (inc_wd * 100, "工作日券假设")]:
    ax.axvline(x, color=C_MUTED, linewidth=0.9, linestyle=(0, (4, 3)))
    ax.text(x + 0.6, ax.get_ylim()[1] * 0.92, f"{lab} {x:.0f}%", fontsize=9, color=C_MUTED)
ax.set_xlabel("抖音核销间夜中真正增量的比例（%）", color=C_INK2)
ax.set_ylabel("门店每个抖音间夜的期望收益（元）", color=C_INK2)
ax.set_title("门店视角：抖音间夜的增量比例超过盈亏平衡点，门店就是赚的", loc="left", color=C_INK, fontsize=12, fontweight="bold")
ax.legend(frameon=False, loc="upper left", fontsize=9.5)
fig.tight_layout(); fig.savefig(f"{OUT}/chart4_store_breakeven.png", facecolor=SURFACE); plt.close(fig)

# ---------- 图5：方案二边际净收益热力图（每小时 GMV × ROI）----------
s = wb["敏感性"]
d = rows_by_label(s)
hdr = d["每小时 GMV \\ ROI"][0]
rois = [s.cell(row=hdr, column=c).value for c in range(2, 8)]
gphs, grid = [], []
r = hdr + 1
while s.cell(row=r, column=1).value is not None and isinstance(s.cell(row=r, column=1).value, (int, float)):
    gphs.append(s.cell(row=r, column=1).value)
    grid.append([wan(s.cell(row=r, column=c).value) for c in range(2, 8)])
    r += 1
import numpy as np
arr = np.array(grid)
vmax = max(abs(arr.min()), abs(arr.max()))
from matplotlib.colors import LinearSegmentedColormap
cmap = LinearSegmentedColormap.from_list("div", ["#d03b3b", "#f0efec", "#2a78d6"])
fig, ax = plt.subplots(figsize=(8.6, 5.2), dpi=200)
im = ax.imshow(arr, cmap=cmap, vmin=-vmax, vmax=vmax, aspect="auto")
ax.set_xticks(range(len(rois))); ax.set_xticklabels([f"ROI {r:g}" for r in rois], color=C_INK2)
ax.set_yticks(range(len(gphs))); ax.set_yticklabels([f"{g:,.0f} 元/小时" for g in gphs], color=C_INK2)
for i in range(len(gphs)):
    for j in range(len(rois)):
        v = arr[i, j]
        ax.text(j, i, f"{v:+.1f}", ha="center", va="center", fontsize=9.5, color=("#ffffff" if abs(v) > vmax * 0.55 else C_INK))
ax.set_xlabel("投流 ROI（售出 GMV / 投流花费）", color=C_INK2)
ax.set_ylabel("总部直播间成熟期每小时售出 GMV", color=C_INK2)
ax.set_title("方案二相对方案一B 的稳态每月边际净收益（总部口径，万元）", loc="left", color=C_INK, fontsize=12, fontweight="bold")
for sp in ax.spines.values(): sp.set_visible(False)
ax.tick_params(length=0)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.outline.set_visible(False); cb.ax.tick_params(colors=C_INK2, length=0)
fig.tight_layout(); fig.savefig(f"{OUT}/chart5_sensitivity.png", facecolor=SURFACE); plt.close(fig)

# ---------- 图6：集中团队的边际价值：总部 vs 门店（三情景）----------
ws = wb["情景对比"]
d = rows_by_label(ws)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), dpi=200, sharey=True)
scens = ["悲观", "基准", "乐观"]
for ax, (lab, ttl) in zip(axes, [("边际：方案二（现有分成）相对方案一B", "方案二：现有分成"), ("边际：方案二+（配套机制）相对方案一B", "方案二+：配套机制后")]):
    style_ax(ax)
    r0 = d[lab][0]
    rows = {ws.cell(row=r, column=2).value: r for r in range(r0 + 1, r0 + 4)}
    hq = [wan(ws.cell(row=rows[sn], column=7).value) for sn in scens]
    st = [wan(ws.cell(row=rows[sn], column=8).value) for sn in scens]
    sysv = [wan(ws.cell(row=rows[sn], column=9).value) for sn in scens]
    w = 0.26
    for i, (vals, name, color) in enumerate([(hq, "总部净收益差", C_BLUE), (st, "门店端净收益差", C_AQUA), (sysv, "系统合计差", C_ORANGE)]):
        xs = [j + (i - 1) * w for j in range(3)]
        ax.bar(xs, vals, width=w - 0.03, color=color, label=name)
        for x, v in zip(xs, vals):
            ax.annotate(f"{v:+.0f}", (x, v), textcoords="offset points", xytext=(0, 4 if v >= 0 else -12), ha="center", fontsize=8.5, color=C_INK2)
    ax.axhline(0, color=C_AXIS, linewidth=0.8)
    ax.set_xticks(range(3)); ax.set_xticklabels([f"{s}情景" for s in scens])
    ax.set_title(ttl, loc="left", color=C_INK, fontsize=11, fontweight="bold")
axes[0].set_ylabel("相对方案一B 的 12 个月差额（万元）", color=C_INK2)
axes[0].legend(frameon=False, loc="upper left", fontsize=9)
fig.suptitle("集中团队多带来的价值在总部与门店之间怎么分", x=0.01, ha="left", color=C_INK, fontsize=12, fontweight="bold")
fig.tight_layout(); fig.savefig(f"{OUT}/chart6_marginal_split.png", facecolor=SURFACE); plt.close(fig)

print("charts written to", OUT)
