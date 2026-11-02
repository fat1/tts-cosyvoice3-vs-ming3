# 开源 TTS 选型与实测：为什么我考虑从 CosyVoice 3 换到 Ming-3.0-tts

> 测试时间：2026-11-01 至 11-02。测试机：Windows 10，RTX 3060 Laptop（6GB）。
> 背景：我的视频系列（工程、量化、UG 编程等）一直用 CosyVoice 克隆我自己的声音配音，2026-10-31 起用 Fun-CosyVoice3-0.5B。中文旁白里常夹英文缩写和术语，一直靠手工维护读音表（`pronounce.json` / `pronounce_en.txt`）。这篇文章回答三个问题：
> 1. 主流开源 TTS 里，为什么挑 Ming-3.0-tts？
> 2. **不建读音表**的情况下，它和 CosyVoice 3 的英文发音差多少？
> 3. Ming 3.0 有哪些优势，值不值得换？
---

## 一、候选模型：许可证与活跃度

许可证信息截至 2026-11。权重许可证和代码许可证经常不一样，**能否商用看的是权重许可证**。

| 模型 | 代码许可证 | 权重许可证 | 能否商用（权重） | 最近一次重要发布 | 活跃度判断 |
|---|---|---|---|---|---|
| **Ming-3.0-tts**（inclusionAI / 蚂蚁） | MIT | MIT | ✅ 可以 | 2026-10（0.5B 稠密版 + Tiny MoE 版） | 🟢 刚发布，最新 |
| **CosyVoice 3**（阿里通义 FunAudioLLM） | Apache-2.0 | 按 Apache-2.0 发布 | ✅ 可以 | 2025-12（Fun-CosyVoice3-0.5B-2512） | 🟡 2026 年仓库无新版本 |
| **IndexTTS-2 / 2.5**（B 站） | bilibili 模型使用协议 | bilibili 模型使用协议 | ⚠️ 要先联系 B 站获得授权 | 2026-08（IndexTTS-2.5） | 🟢 活跃 |
| **Fish Speech / Fish Audio S2 Pro** | Apache-2.0（fish-speech 仓库） | Fish Audio Research License | ❌ 仅限研究和非商用，商用需另购授权 | 2026（S2 Pro） | 🟢 活跃（公司刚融资） |
| **GPT-SoVITS** | MIT | MIT | ✅ 可以 | 2025-06（v2Pro / v2ProPlus） | 🟡 社区活跃，模型一年多没大更新 |
| **F5-TTS** | MIT | CC-BY-NC（训练数据 Emilia 带来的限制） | ❌ 非商用，微调后同样受限 | 2025-03（F5TTS_v1_Base） | 🟡 维护中，模型没有新版本 |
| **ChatTTS** | AGPL-3.0 | CC BY-NC 4.0 | ❌ 非商用（官方称仅供学术） | 小版本维护 | 🔴 基本停滞 |
| **Coqui TTS / XTTS v2** | MPL-2.0（Idiap 维护的 coqui-tts 分支） | Coqui Public Model License | ❌ 非商用，Coqui 公司 2023 年底已倒闭，买不到商用授权 | 原仓库 2024-08 停更，Idiap 分支 2026-01 有小版本 | 🔴 模型冻结 |

### 为什么选 Ming-3.0-tts 来对比

**1. 许可证：只有 3 家的权重能放心商用。**

我的视频要发到抖音、B 站、YouTube、TikTok，带货和广告分成都算商业使用。按权重许可证筛一遍：

- **直接出局：** Fish S2 Pro、F5-TTS、ChatTTS、XTTS v2。这 4 个权重都是非商用，效果再好也只能用来做研究。其中 XTTS v2 连购买商用授权的渠道都没有了。
- **有门槛：** IndexTTS-2 用的是 B 站自定协议，商用要先找 B 站谈。对个人创作者来说，不确定因素太多。
- **剩下的：** CosyVoice 3（Apache-2.0）、GPT-SoVITS（MIT）、Ming-3.0-tts（MIT）。

**2. 活跃度：Ming 是这三家里最新的。**

- **CosyVoice 3：** 最后一次开源是 2025-12，之后一直没更新。而且只开源了 0.5B 版，更大的 1.5B 版没有开放。
- **GPT-SoVITS：** 主力版本 v2Pro 是 2025-06 的。它的定位也不同：要先用少量样本微调，再做推理。和"给一段样本就能克隆、不用训练"的 CosyVoice 不是一类做法，不适合直接对比。
- **Ming-3.0-tts：** 2026-10 刚开源。底座是 Qwen2.5-0.5B 大模型，后面接流匹配（DiT）解码，输出 44.1 kHz。官方支持中、英、德、西、法、韩、日 7 种语言，加上四川话和粤语。规模和 CosyVoice3-0.5B 相当，正好一对一比较。

**3. 架构上可能解决我的痛点。**

Ming 的文字端是一个通用大模型（Qwen2.5），英文词汇量更大。理论上，不加读音表也能念好英文术语。这正是这次要验证的。

---

## 二、实测过程

### 2.1 测试设计

**测试句**

- 新写 60 句中英混读句子，写法贴近真实的量化、工程旁白。
- 句子里共有 58 个英文词，分 5 类：

| 类别 | 例子 | 词数 |
|---|---|---|
| 字母缩写 | ETF、HFT、VWAP、TWAP、MACD、ATR、VaR、OHLC、RAG、LLM、GBDT、PPO、EMA… | 21 |
| 单词 / 工具名 | Python、PyTorch、Transformer、LightGBM、NumPy、Pandas、Docker、GitHub、ROS… | 11 |
| 多词术语 | Sharpe Ratio、Moving Average、Flow Matching、Kalman Filter、Bollinger Bands… | 15 |
| 以前念错过的词 | encoder、preload、reusable、semiconductor、dataset、timestamp、gearbox | 7 |
| 同形异音词 | lead screw、live data、wind turbine、close | 4 |

- "以前念错过的词"都是 CosyVoice 在实际生产中念错过、后来进了读音表的词。这次**用原写法**测。

**控制条件**

- **音色：** 两边都克隆同一段样本 `role/steven/steven.wav`，prompt 文本用同一份逐字稿。
- **不用读音表：** 两边都不套 `pronounce.json` 和 `pronounce_en.txt`，原句直接送进模型。只保留各自自带的文本归一化：CosyVoice 用 wetext，Ming 用 pynini。
- **每句生成 3 次：** 两个模型都带随机采样，单次结果不可靠。60 句 × 3 次 × 2 个模型 = 360 条音频。
- **CosyVoice 3 的配置和生产一致：** fp32、zero-shot 模式、带 `You are a helpful assistant.<|endofprompt|>` 前缀。去掉了生产流程里的"念错就重试"质检，看模型的裸能力。
- **Ming 的配置：** bf16、`language_id=Chinese`、`use_spk_emb=True`，其余参数用默认值。

**怎么判定念对**

- 用 **Whisper large-v3-turbo** 做裁判。它比生产里用的 small 准得多，而且和两个被测模型都没有关系。
- 每条音频分别按中文、英文各转写一遍。任意一次能识别出这个英文词，就算念对。比较时只看字母：缩写允许的相似度 ≥ 0.85，长词 ≥ 0.75，阈值和生产质检一致。
- 中文部分用 Paraformer 转写，按拼音对齐，统计漏读和念错的字，确认英文变好不是拿中文质量换的。
- 音色相似度用 campplus 说话人向量和原样本算余弦相似度。两边用同一个提取器。

### 2.2 环境搭建（Windows，不用 WSL）

- **CosyVoice 3：** 沿用原来的 `tts-gpu` 环境。
- **Ming：** 新建了 conda 环境 `ming-tts`，按官方 requirements 装（torch 2.6 + cu124）。官方只在 Linux H800 上测过，但 Windows 上没遇到兼容问题：
  - pynini 从 conda-forge 一次装好，文本归一化可以正常开着。
  - 没装 flash-attn，自动退回到 PyTorch 自带的 SDPA，不影响结果。
- **踩过的坑：**
  - HuggingFace 直连只有约 100 KB/s，ModelScope 连不上，最后从 hf-mirror 续传（约 480 KB/s），下完用 sha256 校验通过。
  - 中途 D 盘写满一次，清理后重跑。

### 2.3 结果

| 指标 | CosyVoice 3 | Ming-3.0-tts-0.5B |
|---|---|---|
| **英文词正确率（总）** | **87.3%** | **87.3%** |
| 　字母缩写 | **83.3%** | 74.4% |
| 　单词 / 工具名 | 87.9% | **100%** |
| 　多词术语 | **95.6%** | 91.1% |
| 　以前念错过的词 | 81.0% | **100%** |
| 　同形异音词 | 91.7% | **100%** |
| 3 次都念对的词 | 43 / 58 | **49 / 58** |
| 中文读错字（平均每句） | 0.02 | 0.01 |
| 中文存疑字（平均每句） | 0.10 | 0.08 |
| 音色相似度 | **0.894** | 0.867 |
| 语速异常（漏读、拖音） | 4 / 180 | **0 / 180** |
| 速度（生成耗时 / 音频时长，越小越快） | **2.10** | 4.69 |
| 显存峰值 | 3.8 GB | 3.1 GB |
| 输出采样率 | 24 kHz | **44.1 kHz** |

**典型的念错例子**（Whisper 听到的内容）：

| 词 | CosyVoice 3 | Ming-3.0-tts |
|---|---|---|
| MACD | "MyCD" / "Mars CD"（1/3 次对） | 3/3 次对 |
| NumPy | "Nampi" / "能拍"（1/3 次对） | 3/3 次对 |
| timestamp | "Timo" / "Type Temp" / "TypeSame"（0/3 次对） | 3/3 次对 |
| RAG | "REC" / "Ryde"（4/6 次对） | "RG" / "REG" / "Array"（2/6 次对） |
| TWAP / VWAP | 4/6、5/6 次对 | 2/6、2/6 次对（例："Type"、"VB"） |
| LLM | 5/6 次对 | 3/6 次对 |
| Kalman Filter | 2/3 次对 | "Common Filter"（0/3 次对，需要试听确认） |
| VaR | "VR"（0/3 次对） | "VR" / "YR"（0/3 次对） |

### 2.4 逐句案例：输入什么、念成了什么

下面的结果全部来自真实生成的音频。

- **怎么读表：** "Whisper 听写"是 Whisper large-v3-turbo 按中文模式转写的原文，每个模型 3 次生成依次列出，用 / 隔开。它反映的是"听起来像什么"，不一定等于实际发音，有争议的地方以试听为准。
- **怎么听：** 每个音频链接里连着放同一句的 3 次生成，中间空 0.8 秒。文件在 `tts_compare/audio_cases/`，可以直接点开。

#### 示例：一句话完整拆解

**输入文本**（原样送进两个模型，不套读音表）：

> 把 **LLM** 和 **RAG** 结合起来，就能做一个研报问答助手。

| | CosyVoice 3 | Ming-3.0-tts |
|---|---|---|
| 第 1 次 | 把 LLM 和 RAG 结合起来就能做一个言报问答助手 | 把 LLM 和 RAG 结合起来，就能做一个言报问答助手 |
| 第 2 次 | 把 LLM 和 RAG 结合起来就能做一个言报问答助手 | 把 LLM 和 **Array** 结合起来就能做一个言报问答助手 |
| 第 3 次 | 把 LLM 和 RAG 结合起来就能做一个言报问答助手 | 把 LLM 和 **Array** 结合起来就能做一个言报问答助手 |
| 试听 | <audio controls src="audio_cases/zh04_cv3.mp3"></audio> [▶ CV3](audio_cases/zh04_cv3.mp3) | <audio controls src="audio_cases/zh04_ming.mp3"></audio> [▶ Ming](audio_cases/zh04_ming.mp3) |

逐词判定：

- **LLM：** 两边 3/3 都念准。三个字母逐个念出来，Whisper 每次都写成 LLM。
- **RAG：**
  - CosyVoice 3 是 3/3。
  - Ming 只有 1/3：后两次把 R-A-G 连成了一个单词，听起来像 "array"。这是 Ming 在缩写上的典型问题，它容易把字母缩写当成单词来拼。
  - **需要调整：** 给 Ming 用时，要把 RAG 写成 "R A G" 这种拆字母的形式。
- **中文部分：** "研报"两边都被 Whisper 听成"言报"。两个模型都一样，更可能是 Whisper 的问题（"研报"是行业词），不算念错。

#### 中英混读：8 个代表性案例

| # | 输入（英文词加粗） | CosyVoice 3：Whisper 听写（念对次数） | Ming：Whisper 听写（念对次数） | 结论 / 要怎么调 | 试听 |
|---|---|---|---|---|---|
| 1 | 每一笔成交都带着 **timestamp**，精确到毫秒。 | "Timo" / "Type Temp" / "TypeSame"（**0/3**） | timestamp / timestamp / timestamp（**3/3**） | Ming 胜。CV3 要靠读音表（写成 time stamp）才行 | [CV3](audio_cases/zh01_cv3.mp3) · [Ming](audio_cases/zh01_ming.mp3) |
| 2 | **MACD** 由两条均线的差值算出来，用来判断趋势。 | "MyCD" / "Mars CD" / "MyACD"（1/3） | MACD / MACD / MACD（**3/3**） | Ming 胜。CV3 把 M 念成 "My"，需要拆字母 | [CV3](audio_cases/zh02_cv3.mp3) · [Ming](audio_cases/zh02_ming.mp3) |
| 3 | 处理矩阵运算，**NumPy** 比纯循环快几十倍。 | "NAMPi" / "NumPi" / "**能拍**"（1/3） | "NumpPi" / "Numpi" / "NumpPi"（**3/3**） | Ming 胜。CV3 第 3 次直接念成了中文"能拍" | [CV3](audio_cases/zh03_cv3.mp3) · [Ming](audio_cases/zh03_ming.mp3) |
| 4 | 把 **LLM** 和 **RAG** 结合起来，就能做一个研报问答助手。 | 见上面的示例 | 见上面的示例 | LLM 两边都对。RAG 是 CV3 胜 | [CV3](audio_cases/zh04_cv3.mp3) · [Ming](audio_cases/zh04_ming.mp3) |
| 5 | 如果成交量分布很不均匀，**TWAP** 和 **VWAP** 的差别就会变大。 | TWAP·VWUP / TWAP·VWAP / "Table AP"·VWAP（3/3） | "TWAPO"·"VIPA" / TWAP·"Webup" / "**Type**"·"**VB**"（2/3） | CV3 胜。Ming 第 3 次两个缩写都念糊了；前两次按阈值算对，但听写结果也不干净 | [CV3](audio_cases/zh05_cv3.mp3) · [Ming](audio_cases/zh05_ming.mp3) |
| 6 | 风控部门每天都要计算组合的 **VaR**。 | "VR" / "WAR" / "VR"（**0/3**） | "YR" / "VR" / "YR"（**0/3**） | 两边都不行。A 被吞掉了。要改写成 "V A R"，或者直接说"风险价值" | [CV3](audio_cases/zh06_cv3.mp3) · [Ming](audio_cases/zh06_ming.mp3) |
| 7 | 用 **Kalman Filter** 可以从噪声里估计出真实的价差。 | "Common Filter" / "Kelman Filter" / "Killman Filter"（2/3） | "Common Filter" × 3（0/3） | 待试听。Kalman 和 common 发音很近，可能只是 Whisper 的写法偏好 | [CV3](audio_cases/zh07_cv3.mp3) · [Ming](audio_cases/zh07_ming.mp3) |
| 8 | 关节上的 **encoder** 会实时告诉控制器电机转了多少。 | encoder × 3（3/3）。但中文"转了"3 次都被听成"**赚**了" | encoder × 3（3/3）。但"关节"有 2 次被听成"**弯节**" | 英文两边都对（encoder 以前在 CV3 上念错过，这次没错）。中文各有一个疑点，要试听确认 | [CV3](audio_cases/zh08_cv3.mp3) · [Ming](audio_cases/zh08_ming.mp3) |

从这 8 句能看出规律：

- **Ming 念对的，多是"认识的单词"：** timestamp、NumPy、MACD。
- **CosyVoice 3 念对的，多是"要逐个字母念的缩写"：** RAG、TWAP、VWAP。
- **两边都需要人工处理的：** VaR 这类容易被当成单词的缩写。

### 2.5 补充测试：整句英文旁白（英文版视频的真实场景）

2.3 测的是中文旁白里夹英文词。我的每集视频还有英文版，旁白整句都是英文，所以又补测了一轮。

**测试设计**

- **测试句：** 从已经发布的量化、工程、Physical AI、UG 编程 4 个系列的英文旁白里，挑出难词最多的 20 句，原文照搬。
- **CosyVoice 3：** 完全按生产方式。中文样本跨语种克隆，**套用英文读音表** `pronounce_en.txt`。也就是说 CV3 这边是带着"答案"考的。
- **Ming：** `language_id=English`，原句直接输入，**不套读音表**。
- 每句 3 次，Whisper 按英文模式转写，统计整句错词率（WER）。

**结果**

| 指标 | CosyVoice 3（套读音表） | Ming-3.0-tts（不套） |
|---|---|---|
| 整句错词率 WER | **2.5%** | 3.3% |
| 整句一字不差 | **41 / 60** | 33 / 60 |
| 难词识别率 | 98.5% | 98.5% |
| 音色相似度 | 0.751 | **0.805** |
| 语速异常 | 1 / 60 | **0 / 60** |
| 速度 RTF | **1.92** | 4.73 |

**案例**

| # | 输入（来源） | CosyVoice 3：Whisper 听写 | Ming：Whisper 听写 | 结论 | 试听 |
|---|---|---|---|---|---|
| 1 | Turn on the **in-process** workpiece, and the software remembers what the previous operation left behind…（U03E03） | in-process ×3 ✅ | "in**,** process" / "IN**,** process" / "IN**,** process" | Ming 3 次都在连字符处停顿 | [CV3](audio_cases/en01_cv3.mp3) · [Ming](audio_cases/en01_ming.mp3) |
| 2 | **Ultra-precision** machines sit in **temperature-controlled**, **vibration-isolated** rooms and **diamond-turn** optics with **nanometer-level** surface roughness.（S01E08） | 第 1、3 次连贯。第 2 次在 temperature、vibration 后各停顿一次 | 3 次都是 "Ultra**,** precision… temperature**,** controlled**,** vibration**,** isolated… nanometer**,** level" | 遇到连字符词，Ming 一顿一顿的。这是它在英文上最明显的问题 | [CV3](audio_cases/en02_cv3.mp3) · [Ming](audio_cases/en02_ming.mp3) |
| 3 | An AI model is no different: in **ROS 2**, it's just an ordinary node…（P01E02） | ROS2 ×3 ✅（读音表里写成 Ross） | "RAS 2" / ROS2 / "OS2"（1/3） | CV3 胜，但它是靠读音表。Ming 也需要同样的读音提示 | [CV3](audio_cases/en03_cv3.mp3) · [Ming](audio_cases/en03_ming.mp3) |
| 4 | First, follow the drawing's **datums**: wherever the dimensions start, put zero there…（U01E02） | datums ×3 ✅ | "drawing **statums**" ×3 | Ming 3 次都错，需要加读音提示 | [CV3](audio_cases/en04_cv3.mp3) · [Ming](audio_cases/en04_ming.mp3) |
| 5 | The most common tool is **OpenCV**: take a **checkerboard**…, and **OpenCV** finds every corner, computes the **intrinsics**…（P01E03） | 第 1 次 "**OpenZV**… **OpenZeeb**"，后 2 次对（2/3） | OpenCV ×3 ✅ | Ming 不靠读音表就 3/3。CV3 套了读音表（Open-C-V），仍然错 1 次 | [CV3](audio_cases/en05_cv3.mp3) · [Ming](audio_cases/en05_ming.mp3) |
| 6 | In NX, you can save a finished program as a **reusable** group of operations…（U06E01） | 第 2 次 "**re-insolver**"（2/3） | reusable ×3 ✅ | Ming 胜。reusable 是 CV3 生产中念错过、已经进了读音表的词，这次仍错 1 次 | [CV3](audio_cases/en06_cv3.mp3) · [Ming](audio_cases/en06_ming.mp3) |

**整句英文的结论**

- 单看英文单词，Ming 不用读音表就能达到 CV3 套读音表后的水平，难词识别率都是 98.5%。OpenCV、reusable 这种 CV3 套了读音表还偶尔出错的词，Ming 3 次全对。
- **Ming 新暴露的问题是连字符停顿。** in-process、temperature-controlled 这类词在工程类旁白里很常见，WER 偏高主要就是这个原因。
- 英文版音色 Ming 更像本人：0.805 对 0.751。CV3 是用中文样本跨语种克隆英文，相似度比它念中文时（0.894）低不少。

### 2.6 怎么理解这些数据

**1. 总分一样，强项正好相反。**

- **Ming 强在英文单词。** 它的文字端是通用大模型，NumPy、timestamp、LightGBM 这类词它"认识"，按英文单词的读法念出来。以前 CosyVoice 要靠读音表才念对的 encoder、preload、reusable，Ming 不加读音表也全对。
- **CosyVoice 3 强在字母缩写。** TWAP、VWAP、RAG、LLM 要一个字母一个字母地念，CosyVoice 3 更稳。Ming 容易把缩写当成一个单词去拼（RAG → "REG"），或者吞掉字母（RAG → "RG"）。

**2. Ming 更稳定。** 180 条里没有一条漏读、拖音或提前截断。CosyVoice 3 有 4 条，这也是我的生产流程里要做"念错就重试"的原因之一。

**3. 中文两边都没问题。** 每句平均读错的字都接近 0，换模型不会损失中文质量。

**4. 局限：**

- **裁判本身有偏差。** Whisper 识别对了不等于念得地道，识别错了也不一定是念错了。比如 Kalman 被听成 "Common"，可能只是 Whisper 的习惯写法；VaR 的标准读法有争议，可以读 V-A-R，也可以读成单词 "var"。这几个要靠试听判断（`试听.wav` + `试听_目录.txt`）。
- **测试范围有限。** 只测了一个说话人（中文样本、男声），每句 3 次。
- **没调参。** Ming 用的都是默认参数，没有调 cfg 等。`language_id=English` 只在 2.5 的整句英文测试里用过。

---

## 三、总结：Ming-3.0-tts 的优势，以及我考虑换过去的理由

### 3.1 Ming 3.0 的优势

1. **英文单词不用读音表就能念对。** 单词和工具名 100%，以前念错过的词 100%，同形异音词 100%。CosyVoice 3 在这三类分别是 87.9%、81.0%、91.7%。timestamp、NumPy、MACD 这些 CosyVoice 3 反复念错的词，Ming 3 次全对。原因在架构：Ming 的文字端是通用大模型 Qwen2.5，"认识"的英文单词多得多，不用靠人告诉它怎么念。
2. **更稳定。** 180 条里语速异常（漏读、拖音、提前截断）是 0 条，CosyVoice 3 有 4 条。3 次都念对的词也更多：49 个对 43 个。同一句话多生成几次，Ming 的结果更一致，这对批量出片很重要。
3. **音质更高。** 输出 44.1 kHz，CosyVoice 3 是 24 kHz。视频平台都能播放高采样率音频，Ming 的高频细节更多。
4. **中文没有退步。** 每句平均读错字 0.01，CosyVoice 3 是 0.02，两边都接近 0。换模型不用拿中文质量换英文。
5. **显存更省。** 峰值 3.1 GB，CosyVoice 3 是 3.8 GB。在 6GB 的笔记本卡上，可以给数字人渲染多留一点余地。
6. **许可证最宽松，版本最新。**
   - MIT 许可，代码和权重都能商用，没有附加条款。CosyVoice 用的 Apache-2.0 也能商用，但 MIT 更简单。
   - 2026-10 刚开源。CosyVoice 3 最后一次开源是 2025-12，之后没有新版本，更大的 1.5B 版也没有开放。
   - 选一个正在活跃更新的模型，后续的修复、加速方案和新版本都更有指望。
7. **多语言。** 官方支持中、英、德、西、法、韩、日 7 种语言，加上四川话和粤语。我以后如果做日语、西语版本，不用再换一套模型。

### 3.2 我考虑换到 Ming 3.0 的理由

1. **读音表的维护成本是长期负担。**
   - 每开一个新系列，都要先跑一遍术语测试，挑出念错的词，试改写，再听一遍确认。量化系列光这一步就测了两轮、花了好几个小时。
   - 有些词怎么改写都念不好，最后只能在旁白里改说中文。
   - Ming 在英文单词上不用读音表就能念对。剩下要处理的主要是字母缩写。缩写的改写规则很简单（比如拆成"V、W、A、P"），不用逐词试。读音表能大幅缩小，写稿的限制也能放松。
2. **稳定性好，生产流程里的重试会少很多。**
   - 我的流程里每句都要质检，音色、语速或读音不对就重新生成，最多 3 次。
   - Ming 语速异常为 0，英文词 3 次一致的也更多，重试次数会明显下降。
   - 这样一来，它的速度劣势（RTF 4.7 对 2.1）在实际流程里会被抵消一部分。
3. **英文版音色更像本人，读音表可以省掉。**
   - 整句英文测试里（2.5），Ming 不套读音表，难词识别率就和套了读音表的 CV3 一样，都是 98.5%。
   - 音色相似度 0.805 对 0.751，英文版听起来更像我本人。
   - 但它有一个要先解决的问题：遇到连字符会停顿，整句错词率 3.3%，比 CV3 的 2.5% 略高。最简单的办法是送进模型前把连字符换成空格。这个办法还没测。
4. **速度和音色差距有办法缩小。**
   - **速度：** 这次在 Windows 上没装 flash-attn，用的是 PyTorch 自带的 SDPA，也没上 vLLM。Ming 是刚发布的模型，推理加速方案会陆续出来，同门的 Ming-omni-tts 已经有 vLLM 部署方案。
   - **音色：** 相似度 0.867 对 0.894，差 0.03。这次只用了默认参数，还没调 cfg、没试换一段更好的样本。实际听起来像不像，以试听为准。
5. **字母缩写这一块，可以先用简单办法补。**
   - Ming 在缩写上是 74.4%，CosyVoice 3 是 83.3%，这是它唯一明显落后的地方。
   - 错误集中在 RAG、TWAP、VWAP、LLM 几个词。它们正好都能用"拆字母"这种通用写法解决。
   - 补完以后，Ming 在缩写上的劣势应该能大幅缩小，单词上的优势还在。
6. **长远看押注更新的技术路线。** "大模型 + 流匹配解码"是现在 TTS 的主流方向。Ming 在 0.5B 这个量级就能在不加读音表时追平 CosyVoice 3 的总分。往后无论官方出新版本还是社区出微调方案，跟进都更容易。

### 3.3 换之前还要确认的事

- **试听：** 听 `试听.wav`，确认 Ming 的音色和英文发音实际是否满意。VaR、Kalman 这几个 Whisper 判错的词要重点听。
- **缩写补测：** 给 RAG、TWAP、VWAP、LLM 加上拆字母的写法再测一遍，看缩写能不能追平。
- **连字符补测：** 英文版把连字符换成空格再测一遍，看 in-process、temperature-controlled 这类词的停顿能不能消除。
- **整集试跑：** 拿 1 集量化视频走完整流程（中英两版），比较整集耗时、重试次数和成片效果。
- **切换方式：** 在 `cosyvoice_worker.py` 旁边加一个 Ming 的配音进程，用环境变量切换，和当初从 CosyVoice 2 换到 3 的做法一样。可以先只在英文版上启用，确认没问题再推到中文版。

**一句话结论：** 不加读音表时，Ming-3.0-tts 和 CosyVoice 3 总分打平（87.3%），但 Ming 在英文单词和稳定性上明显更强，而且 MIT 许可、2026-10 刚发布。它的短板（字母缩写、连字符停顿、速度）都有清楚的改进办法，但都还没验证。我打算先补测缩写和连字符，跑一集完整流程，再决定要不要切换。在这之前，生产上继续用 CosyVoice 3。

---

### 附：测试文件

- 测试句：`tts_compare/sentences.txt`
- 生成脚本：`gen_cv3.py`（tts-gpu 环境）、`gen_ming.py`（ming-tts 环境）
- 打分脚本：`score.py`
- 结果：`汇总.txt`（逐词对比）、`report.csv`（360 条明细）
- 试听：`试听.wav` + `试听_目录.txt`（每句先放 CosyVoice 3，再放 Ming）
- 文中案例音频：`audio_cases/`（zh01–zh08 是中英混读，en01–en06 是整句英文；每个文件连放同一句的 3 次生成）
- 整句英文测试：`en/sentences_en.txt`、`gen_cv3_en.py`、`score_en.py`，结果在 `en/汇总_en.txt`、`en/report_en.csv`，试听在 `en/试听_en.wav`

### 参考资料

- [CosyVoice（GitHub）](https://github.com/FunAudioLLM/CosyVoice)
- [Ming-3.0-tts（GitHub）](https://github.com/inclusionAI/Ming-3.0-tts)、[Ming-3.0-tts-0.5B（HuggingFace）](https://huggingface.co/inclusionAI/Ming-3.0-tts-0.5B)
- [IndexTTS（GitHub）](https://github.com/index-tts/index-tts)
- [Fish Audio S2：我们说的开源是什么意思](https://fish.audio/ru/blog/what-we-mean-by-open-source-for-s2/)
- [F5-TTS（PyPI）](https://pypi.org/pypi/f5-tts)
- [ChatTTS（GitHub）](https://github.com/2noise/chattts)
- [XTTS v2 review](https://www.promptquorum.com/power-local-llm/xtts-v2-review)、[Coqui TTS](https://vantaige.io/ai-tool/coqui-tts)
- [GPT-SoVITS 指南](https://localaimaster.com/blog/gpt-sovits-voice-cloning-guide)
