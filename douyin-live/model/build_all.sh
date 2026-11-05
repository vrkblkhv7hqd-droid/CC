#!/usr/bin/env bash
# 一键重建：模型（主工作簿 + 6 个变体）→ 重算 → 表格 → 图 → 文档（md/docx/pdf）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RECALC="${RECALC:-/mnt/skills/public/xlsx/scripts/recalc.py}"
B="$ROOT/report/build"; M="$ROOT/model"
cd "$M"
python3 build_model.py "$M/住小叮抖音直播财务模型.xlsx" >/dev/null
OVERRIDES='{"B_START":[5,5,5],"B_ADS_START":[6,5,5],"C_START":[5,5,5]}' python3 build_model.py "$B/variant_phased.xlsx" >/dev/null
OVERRIDES='{"ABSORB_BRAND":0}' python3 build_model.py "$B/variant_noabsorb.xlsx" >/dev/null
OVERRIDES='{"PRICING_SEL":3}' python3 build_model.py "$B/variant_tier3.xlsx" >/dev/null
OVERRIDES='{"CH_FEE":0.01}' python3 build_model.py "$B/variant_chfee.xlsx" >/dev/null
OVERRIDES='{"SUP_HIRE":1}' python3 build_model.py "$B/variant_sup.xlsx" >/dev/null
OVERRIDES='{"AP_TRAIN_ONEOFF":0,"PILOT_EQUIP":0,"PILOT_CONTENT":0}' python3 build_model.py "$B/variant_zero.xlsx" >/dev/null
for f in "$M/住小叮抖音直播财务模型.xlsx" "$B"/variant_*.xlsx; do python3 "$RECALC" "$f" | grep -q '"total_errors": 0' || { echo "recalc error in $f"; exit 1; }; done
python3 tables.py "$M/住小叮抖音直播财务模型.xlsx" "$B/tables.json"
python3 charts.py "$M/住小叮抖音直播财务模型.xlsx" "$ROOT/report/charts" 2>&1 | grep -v findfont || true
python3 "$B/build_doc.py"
cd "$ROOT/report" && soffice --headless --convert-to pdf --outdir "$B" "住小叮抖音直播组织方案_股东决策文档.docx" >/dev/null 2>&1 && cp "$B/住小叮抖音直播组织方案_股东决策文档.pdf" ./ && echo "pdf pages: $(pdfinfo 住小叮抖音直播组织方案_股东决策文档.pdf | awk '/Pages/{print $2}')"
