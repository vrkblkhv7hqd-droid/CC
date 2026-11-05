# -*- coding: utf-8 -*-
"""汇总两路核验结果（来源核对、独立交叉验证），生成附录 D 用的核验状态表与原始明细。核验日期 2026-11-05。"""
import json, sys, re
W = "/root/.claude/projects/-home-user-CC/f2fc4d9d-a896-563c-b59a-2b4100561ba6/subagents/workflows"
FID = f"{W}/wf_1471eb55-0a9/journal.jsonl"
COR = f"{W}/wf_ede03787-949/journal.jsonl"
OUT_MD = "/home/user/CC/douyin-live/report/build/verification.md"
OUT_JSON = "/home/user/CC/douyin-live/report/build/verification.json"

def results(path):
    out = []
    for line in open(path, encoding="utf-8"):
        try: j = json.loads(line)
        except Exception: continue
        if j.get("type") == "result" and j.get("result"):
            out.append(j["result"])
    return out

import os
SUP = f"{W}/wf_7c720a95-3a3/journal.jsonl"
fid = results(FID) + (results(SUP) if os.path.exists(SUP) else []); cor = results(COR)
# ---- 来源核对 ----
checks, row_verdicts = [], {}
for r in fid:
    res = r if "checks" in r else (r.get("result") or {})
    for c in res.get("checks", []): checks.append(c)
    for v in res.get("row_verdicts", []): row_verdicts[v["id"]] = v
# ---- 交叉验证 ----
verdicts, searches = [], 0
for r in cor:
    res = r if "verdicts" in r else (r.get("result") or {})
    for v in res.get("verdicts", []): v["topic"] = r.get("label") or res.get("summary", "")[:20]; verdicts.append(v)
    searches += res.get("searches_used", 0) or 0

ZH = {"supported": "原文支持", "partially_supported": "部分支持", "not_supported": "原文不支持", "unreachable": "页面打不开", "irrelevant": "页面无关", "unverifiable": "无法核验",
      "confirmed": "独立来源一致", "adjust": "独立来源数值或口径不同", "refuted": "独立来源相反"}
lines = []
lines.append("## 来源核对（逐 URL）\n")
lines.append("| 编号 | URL | 可打开 | 判定 | 页面日期 | 说明 |")
lines.append("|---|---|---|---|---|---|")
for c in checks:
    lines.append(f"| {c.get('id','')} | {c.get('url','')} | {'否' if c.get('status') == 'unreachable' else '是'} | {ZH.get(c.get('status'), c.get('status'))} | {c.get('page_date','') or ''} | {(c.get('note','') or '').replace('|','／')[:300]} |")
lines.append("\n## 来源核对（按编号）\n")
lines.append("| 编号 | 综合判定 | 说明 |")
lines.append("|---|---|---|")
def _key(x):
    m = re.search(r'C-(\d+)', x); return (int(m.group(1)) if m else 999, x)
for k in sorted(row_verdicts, key=_key):
    v = row_verdicts[k]
    lines.append(f"| {k} | {ZH.get(v['verdict'], v['verdict'])} | {(v.get('note','') or '').replace('|','／')[:400]} |")
lines.append(f"\n## 独立交叉验证（共用检索约 {searches} 次）\n")
lines.append("| 专题 | 条目 | 判定 | 独立来源给出的值 | 来源 | 日期 | 说明 |")
lines.append("|---|---|---|---|---|---|---|")
for v in verdicts:
    lines.append(f"| {v.get('topic','')} | {(v.get('item','') or '')[:120]} | {ZH.get(v.get('verdict'), v.get('verdict'))} | {(v.get('found_value','') or '').replace('|','／')[:200]} | {v.get('source_url','') or ''} | {v.get('source_date','') or ''} | {(v.get('note','') or '').replace('|','／')[:300]} |")
open(OUT_MD, "w", encoding="utf-8").write("\n".join(lines))
json.dump({"checks": checks, "row_verdicts": row_verdicts, "verdicts": verdicts, "searches": searches}, open(OUT_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# 统计
from collections import Counter
print("URL checks:", Counter(c.get("status") for c in checks))
print("row verdicts:", Counter(v["verdict"] for v in row_verdicts.values()))
print("corroboration:", Counter(v.get("verdict") for v in verdicts), "searches:", searches)
print("\n需要关注的条目：")
for k, v in sorted(row_verdicts.items(), key=lambda kv: _key(kv[0])):
    if v["verdict"] != "supported": print(" [来源核对]", k, ZH.get(v["verdict"]), "-", (v.get("note") or "")[:200])
for v in verdicts:
    if v.get("verdict") in ("adjust", "refuted"): print(" [交叉验证]", v.get("topic"), "|", v.get("item", "")[:60], "->", v.get("verdict"), "|", (v.get("found_value") or "")[:120], "|", (v.get("note") or "")[:160])
