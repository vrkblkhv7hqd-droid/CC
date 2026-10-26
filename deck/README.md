# HogentX 新马市场介绍材料

面向两位在新加坡、马来西亚做投资的引荐人的 30 分钟介绍。2026 年 10 月。

## 文件

| 文件 | 用途 |
| --- | --- |
| `index.html` | 24 页幻灯片，浏览器直接打开即可演示（单文件，图片在 `assets/`） |
| `HogentX-新马市场介绍.pdf` | 同一份幻灯片的 PDF，会后转发用（无动画） |
| `onepager.html` / `HogentX-新马一页纸.pdf` | 一页纸摘要，A4 |
| `讲稿与预备问答.md` | 逐页讲稿、30 分钟时间分配、12 个预备问答 |
| `商业与落地建议.md` | 定价、代理商分成、数据托管与合规的建议与理由 |

## 演示操作

- `←` `→` 或空格翻页；`Home` / `End` 跳到首尾；手机上左右滑动
- `N` 打开右侧演讲者备注；`F` 全屏
- `E` 进入行内编辑（直接点文字修改），再按 `E` 退出并自动保存草稿到浏览器；`Ctrl+S` 另存为新的 HTML
- 地址栏 `#12` 可直接跳到第 12 页

字体通过 Google Fonts 加载；离线时自动回退到系统中文字体，版式不变。

## 重新导出 PDF

```bash
# 需要 Node 22 与 Playwright（npm i playwright 后 npx playwright install chromium）
cd deck
node tools/export-deck.js index.html ../shots --pdf "HogentX-新马市场介绍.pdf"     # 幻灯片 PDF + 每页截图与溢出检查
node tools/export-onepager.js onepager.html "HogentX-新马一页纸.pdf"               # 一页纸 PDF
```

## 修改原则

- 每个外部数字都有页脚来源；改数字请同时改来源。
- 收益提升写「预计」，验证结果写「内部口径」，无外部付费客户如实写。
- 模块 11（AI 入口直订）只在路线图一句带过；不放团队与融资信息。
