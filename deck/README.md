# HogentX · 新加坡 / 马来西亚 合作交流演示稿

面向新马投资人的中文演示稿，共 15 页正文和 4 页附录，按 30 分钟内讲完设计。

## 怎么打开、怎么讲

1. 用 Chrome 打开 `index.html`。字体从 Google Fonts 加载；没有网络时会换成系统中文字体，字重和字宽会略有变化。现场网络不稳时，建议直接用 PDF 演示（PDF 已内嵌字体）。
2. 翻页：← → 键、空格、鼠标滚轮，触屏可左右滑动。按 F11 全屏。
3. **N**：打开或关闭讲稿面板。面板浮在幻灯片下方，投屏时观众也能看到，所以正式演讲时请关掉，可在手机或另一台设备上看 `speaker-notes.md`。
4. **E**：进入编辑模式，可以直接点文字修改。改动会自动保存在这台电脑的浏览器里。按 **Ctrl/⌘ + S** 把改好的版本下载成新的 HTML 文件。
5. 网址后面加 `#9` 可以直接跳到第 9 页。

## 导出 PDF（会后发送用）

```bash
cd deck
node tools/export-pdf.js            # 生成 HogentX-SGMY-Investor-Deck.pdf
```

导出需要安装 Playwright（Chromium）。生成的 PDF 是矢量文字，每页 1920×1080，动画以最终状态呈现。

## 文件结构

```
deck/
  index.html                 演示稿（单文件，样式与脚本都在内）
  speaker-notes.md           讲稿与时间分配（由 index.html 里的讲稿生成）
  HogentX-SGMY-Investor-Deck.pdf    PDF 版
  assets/brand/              商标矢量图（据商标注册申请图样描摹）
  assets/site/               官网截图、吉祥物、数字员工图标
  assets/product/            AI 直销官网的页面原型截图
  tools/export-pdf.js        PDF 导出脚本
  video/STORYLINES.md        60 秒开场视频的三个故事方向（待选）
```

## 数据口径

- 外部市场数据都已逐条回查原始出处，出处列在附录 A4 和各页底部。
- 住小叮实测：实验范围是 29 家自有门店；计量口径是“店长管理 2 家门店时，6 项任务的合计用时”。
- 收益管理提升 10–20% 是验证中的目标，不是承诺；AI 直销与免费官网仍在开发中。
- 附录 A2 中标为“规划中”的数据合规措施，以实际落地为准。
