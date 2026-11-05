#!/usr/bin/env bash
# 一键重建：模型（主工作簿 + 14 个变体）→ 重算 → 表格 → 图 → 文档（md/docx/pdf）
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RECALC="${RECALC:-/mnt/skills/public/xlsx/scripts/recalc.py}"
B="$ROOT/report/build"; M="$ROOT/model"
cd "$M"
python3 build_model.py "$M/住小叮抖音直播财务模型.xlsx" >/dev/null
OVERRIDES='{"B_START":[5,5,5],"B_ADS_START":[6,5,5],"C_START":[5,5,5]}' python3 build_model.py "$B/variant_phased.xlsx" >/dev/null
OVERRIDES='{"ABSORB_BRAND":1}' python3 build_model.py "$B/variant_absorb.xlsx" >/dev/null
OVERRIDES='{"PRICING_SEL":3}' python3 build_model.py "$B/variant_tier3.xlsx" >/dev/null
OVERRIDES='{"CH_FEE":0.01}' python3 build_model.py "$B/variant_chfee.xlsx" >/dev/null
OVERRIDES='{"SUP_HIRE":1}' python3 build_model.py "$B/variant_sup.xlsx" >/dev/null
OVERRIDES='{"AP_TRAIN_ONEOFF":0,"PILOT_EQUIP":0,"PILOT_CONTENT":0}' python3 build_model.py "$B/variant_zero.xlsx" >/dev/null
OVERRIDES='{"B_SAL_CTRL":0,"B_SAL_ADS":0,"B_HOURS":[80,80,80],"B_ADS":0,"B_BACKUP_HOST":[3000,3000,3000]}' python3 build_model.py "$B/variant_team2.xlsx" >/dev/null
OVERRIDES='{"PRESALE_ON":0}' python3 build_model.py "$B/variant_nopresale.xlsx" >/dev/null
OVERRIDES='{"CAL_MODE":2}' python3 build_model.py "$B/variant_share145.xlsx" >/dev/null
OVERRIDES='{"SHARE0":0.10}' python3 build_model.py "$B/variant_share10.xlsx" >/dev/null
OVERRIDES='{"MKT_FEE":0.005}' python3 build_model.py "$B/variant_mkt05.xlsx" >/dev/null
OVERRIDES='{"MKT_FEE":0.01}' python3 build_model.py "$B/variant_mkt10.xlsx" >/dev/null
OVERRIDES='{"MKT_FEE":0.005,"AP_TRAIN_ONEOFF":0,"PILOT_EQUIP":0,"PILOT_CONTENT":0}' python3 build_model.py "$B/variant_zeromkt05.xlsx" >/dev/null
OVERRIDES='{"MECH_ON":0}' python3 build_model.py "$B/variant_mech0.xlsx" >/dev/null
for f in "$M/住小叮抖音直播财务模型.xlsx" "$B"/variant_*.xlsx; do python3 "$RECALC" "$f" | grep -q '"total_errors": 0' || { echo "recalc error in $f"; exit 1; }; done
python3 tables.py "$M/住小叮抖音直播财务模型.xlsx" "$B/tables.json"
python3 charts.py "$M/住小叮抖音直播财务模型.xlsx" "$ROOT/report/charts" 2>&1 | grep -v findfont || true
python3 "$B/build_doc.py"
cd "$ROOT/report" && soffice --headless --convert-to pdf --outdir "$B" "住小叮抖音直播组织方案_股东决策文档.docx" >/dev/null 2>&1 && cp "$B/住小叮抖音直播组织方案_股东决策文档.pdf" ./ && echo "pdf pages: $(pdfinfo 住小叮抖音直播组织方案_股东决策文档.pdf | awk '/Pages/{print $2}')"
python3 "$B/build_doc.py" "$ROOT/report/住小叮抖音直播方案_股东会简版.template.md" "$ROOT/report/住小叮抖音直播方案_股东会简版.md" "$ROOT/report/住小叮抖音直播方案_股东会简版.docx"
cd "$ROOT/report" && soffice --headless --convert-to pdf --outdir "$B" "住小叮抖音直播方案_股东会简版.docx" >/dev/null 2>&1 && cp "$B/住小叮抖音直播方案_股东会简版.pdf" ./ && echo "simple pdf pages: $(pdfinfo 住小叮抖音直播方案_股东会简版.pdf | awk '/Pages/{print $2}')"
