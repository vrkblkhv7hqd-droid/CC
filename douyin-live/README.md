# 住小叮抖音直播：组织方案、定价机制与牵头部门（股东决策材料）

生成日期：2026 年 11 月 4 日。

## 交付物

| 文件 | 用途 | 导入飞书 |
|---|---|---|
| `report/住小叮抖音直播组织方案_股东决策文档.docx` | 股东决策文档（Word 版，含图表） | 飞书云文档 → 导入 → 选择 .docx，标题、表格、图片保留 |
| `report/住小叮抖音直播组织方案_股东决策文档.md` | 同内容 Markdown 版 | 飞书云文档 → 导入 → 选择 .md（图片需手动插入 `report/charts/` 下的 PNG） |
| `model/住小叮抖音直播财务模型.xlsx` | 财务模型，参数可调，全部为公式 | 飞书表格 → 导入 .xlsx |
| `report/charts/*.png` | 文档中的六张图 | 已嵌入 Word 版 |
| `research_notes/住小叮抖音直播方案研究/` | 九条研究线的笔记与核验记录，来源逐条可查 | 按需 |

## 怎么改数

1. 打开模型的「假设」表，只改蓝色单元格；黄色底是对结论影响最大的关键假设。改完后所有表自动重算。
2. 如需同步更新文档里的表格和图：在仓库目录执行

```bash
python3 douyin-live/model/build_model.py
python3 "<xlsx skill 目录>/scripts/recalc.py" "douyin-live/model/住小叮抖音直播财务模型.xlsx"
python3 douyin-live/model/tables.py
python3 douyin-live/model/charts.py
python3 douyin-live/report/build/build_doc.py
```

`build_model.py` 生成模型；`recalc.py` 用 LibreOffice 重算公式（任何能重算公式的方式都可以）；`tables.py` 把模型数值导出为文档表格；`charts.py` 画图；`build_doc.py` 用模板生成 Markdown 并用 pandoc 导出 Word。文档正文在 `report/住小叮抖音直播组织方案_股东决策文档.template.md`，占位符 `{{...}}` 由 `tables.py` 的输出替换。

## 核验状态（重要）

外部数据来自 2026 年 11 月 4 日的网络检索，逐条标注来源。11 月 5 日放开网络后补做了两道核验：逐条打开引用页面核对原文（`report/build/verification.md` 为逐 URL 明细），以及不看原文的独立交叉检索。核验导致的修正（支付手续费已含在 8% 内、划线价规则措辞、携程处罚口径、同业数据标注、薪酬注释）已写入正文与模型；文档附录 D 逐条列出 16 条关键事实的核验状态。仍未能核对的条目在正文中有标注，不作为结论依据。
