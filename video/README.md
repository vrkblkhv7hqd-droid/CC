# HogentX 开场视频

新马市场介绍的开场短片：英文解说、轻背景音乐、中文字幕，1920×1080，30 fps，约 1 分钟。片子只提出问题，不给答案；答案、规则、数字、界面、新马落地全部留给紧接其后的 30 分钟演讲（评审依据见 `开场视频评审意见.md`）。

| 文件 | 用途 |
| --- | --- |
| `HogentX-开场视频.mp4` | 成片（H.264 + AAC），直接播放 |
| `opening/` | [HyperFrames](https://github.com/heygen-com/hyperframes) 工程，可改字、改时序后重新渲染 |

## 内容结构（6 段，跟随解说）

1. 酒店公式：可售房晚 × 入住率 × 房价 − 渠道成本 − 人力
2. 每天都在流失：空房、定错价、低价挂一夜、差评
3. 不是店长不用心，是没有人能每小时盯住五个后台（纯排版，不出现产品界面）
4. 立场：我们自己也经营着 29 家酒店（住小叮门头照，只给这一个公开事实）
5. 回到公式：这些变量里，哪一个没人管？（讲稿第 2 页的核心句，片子问、第 2 页接、第 19 页答）
6. 收尾：HogentX，懂经营的酒店数字员工；标志与口号停在最后一帧，不淡黑

留给现场的内容：四个数字员工角色、「AI 只读取，人来确认」、产品界面、住小叮的故事、480 → 174 / 约 64% / 内部口径、新加坡与马来西亚、五种语言与 OTA 接入、数据托管方案。

播放要点：播放器停在最后一帧（浏览器和 QuickTime 默认如此）直到幻灯片封面打开；片尾只有一个标志是有意的。演讲第 2 页开头已按片尾的问题改写（见 `deck/讲稿与预备问答.md`）。

英文解说里品牌写作 Hojent X，只是为了让语音读成「Ho-jent-X」（gent 同 agent）；字幕与画面仍是 HogentX。

## 工程文件（`opening/`）

| 文件 | 说明 |
| --- | --- |
| `script.json` | 解说词（英文）与字幕（中文）的唯一来源，按段落分组 |
| `tts.py` | 用 edge-tts 生成每段解说 `assets/voice/sNN.mp3`，并记录逐词时间戳到 `timings.json` |
| `tools/make-bgm.py` | 用本地 MusicGen（facebook/musicgen-small）生成背景音乐 `assets/bgm/track.wav` |
| `tools/build.py` | 根据 `script.json` + `timings.json` 生成 `index.html`、`compositions/*.html`（场景、字幕、角标），画面动作对齐到解说词；找到 Noto CJK 源字体时自动重新子集化 |
| `tools/subset-fonts.py` | 按片中用字把 Noto CJK 源字体子集化为 woff2（改字后必跑，否则缺字会静默回退成系统字体） |
| `assets/fonts/` | 思源宋体 / 思源黑体按用字子集化的 woff2，与 Fraunces 数字字体 |
| `assets/vendor/gsap.min.js` | 本地打包的 GSAP，离线可渲染 |

## 修改与重新渲染

```bash
cd video/opening
# 1. 改词：编辑 script.json（en = 解说，zh = 字幕分组）
# 2. 重新配音（需要网络）：SSL_CERT_FILE=/root/.ccr/ca-bundle.crt python3 tts.py
# 3. 重新生成页面与时序（NOTO_CJK_DIR 指向 Noto CJK 的 OTF 目录时自动重新子集化字库）
NOTO_CJK_DIR=/path/to/noto-cjk-otf python3 tools/build.py
# 4. 检查、看帧、渲染
npx hyperframes@0.8.205 check
npx hyperframes@0.8.205 snapshot --at 3,20,50,75,100
npx hyperframes@0.8.205 render --quality delivery -o ../HogentX-开场视频.mp4
```

字幕、解说与画面均由 `build.py` 生成；不要直接改 `index.html` 或 `compositions/`，改了会被下一次构建覆盖。

## 声音

- 解说：edge-tts `en-US-AndrewMultilingualNeural`，语速 −6%
- 音乐：MusicGen 生成的轻柔管弦/钢琴铺底；解说下压到 0.2，两处有意的静默（第 3 段后、问题后）抬到 0.32，片头片尾 0.45（`index.html` 中 `#music` 的音量包络由 `build.py` 生成）
- 成片整体响度约 −18 LUFS，峰值 −3 dBFS 以内
