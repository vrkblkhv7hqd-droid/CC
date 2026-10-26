# HogentX 开场视频

新马市场介绍的开场短片：英文解说、轻背景音乐、中文字幕，1920×1080，30 fps，约 1 分 48 秒。

| 文件 | 用途 |
| --- | --- |
| `HogentX-开场视频.mp4` | 成片（H.264 + AAC），直接播放 |
| `opening/` | [HyperFrames](https://github.com/heygen-com/hyperframes) 工程，可改字、改时序后重新渲染 |

## 内容结构（8 段，跟随解说）

1. 酒店公式：可售房晚 × 入住率 × 房价 − 渠道成本 − 人力
2. 每天都在流失：空房、定错价、低价挂一夜、差评
3. 没有人能每小时盯住五个后台
4. 四个数字员工：收益经理、宾客关系专员、质检主管、总经理助理
5. 规则：AI 只读取，人来确认
6. 验证：住小叮 29 家门店，480 → 174 分钟/天，约 −64%，内部口径
7. 新加坡 · 马来西亚：五种语言、已接入 Agoda / Booking.com、数据拟托管于新加坡
8. 收尾：用更少的人，提前看到收入风险；HogentX，懂经营的酒店数字员工

措辞口径与 `deck/` 一致：不出现 PMS 对接承诺（海外 PMS 尚未接入）、不出现收益保证、数据托管写「拟」。

## 工程文件（`opening/`）

| 文件 | 说明 |
| --- | --- |
| `script.json` | 解说词（英文）与字幕（中文）的唯一来源，按段落分组 |
| `tts.py` | 用 edge-tts 生成每段解说 `assets/voice/sNN.mp3`，并记录逐词时间戳到 `timings.json` |
| `tools/make-bgm.py` | 用本地 MusicGen（facebook/musicgen-small）生成背景音乐 `assets/bgm/track.wav` |
| `tools/build.py` | 根据 `script.json` + `timings.json` 生成 `index.html`、`compositions/*.html`（场景、字幕、角标），画面动作对齐到解说词 |
| `assets/fonts/` | 思源宋体 / 思源黑体按用字子集化的 woff2，与 Fraunces 数字字体 |

## 修改与重新渲染

```bash
cd video/opening
# 1. 改词：编辑 script.json（en = 解说，zh = 字幕分组）
# 2. 重新配音（需要网络）：SSL_CERT_FILE=/root/.ccr/ca-bundle.crt python3 tts.py
# 3. 重新生成页面与时序
python3 tools/build.py
# 4. 检查、看帧、渲染
npx hyperframes@0.8.205 check
npx hyperframes@0.8.205 snapshot --at 3,20,50,75,100
npx hyperframes@0.8.205 render --quality delivery -o ../HogentX-开场视频.mp4
```

字幕、解说与画面均由 `build.py` 生成；不要直接改 `index.html` 或 `compositions/`，改了会被下一次构建覆盖。

## 声音

- 解说：edge-tts `en-US-AndrewMultilingualNeural`，语速 −6%
- 音乐：MusicGen 生成的轻柔管弦/钢琴铺底，解说下自动压低（`index.html` 中 `#music` 的音量包络）
- 成片整体响度约 −18 LUFS，峰值 −3 dBFS 以内
