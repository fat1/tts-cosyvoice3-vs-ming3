# 开源 TTS 实测：不建读音表，CosyVoice 3 和 Ming-3.0-tts 的英文念得怎么样？

我做的视频是中文旁白，里面经常夹英文缩写和术语；同时每集还有一个纯英文版本。目前我用 CosyVoice 3 配音，为了让英文念准，一直在手工维护读音表。2026 年 10 月 Ming-3.0-tts 开源后，我用同样的条件对比测了这两个模型，想回答两个问题：

1. **中英混读：** 中文旁白里夹着英文缩写和术语，不建读音表，两个模型的英文念得怎么样？
2. **纯英文：** 整句英文旁白里遇到专业术语，不建读音表，两个模型念得怎么样？英文还需要建读音表吗？

**代码、测试句、全部结果和案例音频都已开源：**
<https://github.com/fat1/tts-cosyvoice3-vs-ming3>

## 一、为什么挑 Ming-3.0-tts

**1. 许可证：能放心商用的只有 3 个。**

视频要发到各个平台，带货和广告分成都算商业使用。判断能不能商用，要看模型权重的许可证，不是代码的许可证。

- **可以商用：** CosyVoice 3（Apache-2.0）、GPT-SoVITS（MIT）、Ming-3.0-tts（MIT）
- **要先找 B 站授权：** IndexTTS-2
- **权重不能商用：** Fish Audio S2 Pro、F5-TTS、ChatTTS、XTTS v2

**2. 活跃度：Ming 是这三个里最新的。**

- CosyVoice 3 最后一次开源是 2025-12，之后没有更新。
- GPT-SoVITS 要先微调再推理，做法不同，不适合直接对比。
- Ming-3.0-tts 在 2026-10 刚开源。它的底座是 Qwen2.5-0.5B，后面接流匹配解码，输出 44.1 kHz。规模和 CosyVoice3-0.5B 相当，正好一对一比较。

**3. 架构上可能解决我的痛点。**

Ming 的文字端是通用大模型，认识的英文单词更多。理论上，不加读音表也能念好英文术语。这正是这次要验证的。

## 二、怎么测

- **两边都不用读音表：** 原句直接送进模型，只保留各自自带的文本归一化。
- **同一个第三方标准声音：** 两个模型克隆的是同一段公开录音，来自 Open Speech Repository 的标准朗读：
  - 中英混读测试用中文参考音：[OSR_cn_000_0072](https://www.voiptroubleshooter.com/open_speech/chinese/OSR_cn_000_0072_8k.wav)，截取前 3 句，8.6 秒；
  - 纯英文测试用美式英语参考音：[OSR_us_000_0010](https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav)，截取前 4 句，10.2 秒。
  - 试听参考音：[中文](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/ref_zh.mp3) ｜ [英文](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/ref_en.mp3)
- **测试句：**
  - 中英混读 60 句，覆盖 58 个英文词，分 5 类：字母缩写、工具名、多词术语、以前念错过的词、同形异音词；
  - 纯英文 20 句，取自我已发布的工程、量化、机器人、UG 编程视频的英文旁白，挑的是难词最多的句子。
- **每句生成 3 次：** 两个模型都带随机性，只看一次不可靠。两项测试合计 480 条音频。
- **怎么判断念对：** 用 Whisper large-v3-turbo 转写，能识别出这个英文词就算念对。中文另外用 Paraformer 检查有没有错字。

## 三、问题 1：中英混读，不建读音表

**主要数据**

- **英文词正确率：** Ming 85.7%，CosyVoice 3 82.5%。
- **单词和工具名：** Ming 100%，CosyVoice 3 81.8%。
- **多词术语：** Ming 91.1%，CosyVoice 3 86.7%。
- **以前念错过的词：** Ming 90.5%，CosyVoice 3 85.7%。
- **同形异音词：** Ming 100%，CosyVoice 3 91.7%。
- **字母缩写：** CosyVoice 3 78.2%，Ming 73.1%。
- **3 次都念对的词（共 58 个）：** Ming 49 个，CosyVoice 3 39 个。
- **中文错字：** 两边每句平均都接近 0。
- **漏读、拖音：** 两边都是 0。
- **生成速度：** 生成耗时除以音频时长，CosyVoice 3 是 1.9，Ming 是 4.6，CosyVoice 3 更快。

### 一句话完整拆解

输入：**MACD 由两条均线的差值算出来，用来判断趋势。**

- **CosyVoice 3：** 3 次都被听成 "MyCD"，M 念成了 "my"，0/3。
- **Ming：** 3 次都是 MACD，3/3。
- **要怎么调：** 用 CosyVoice 3 时，要把 MACD 写成 "M A C D" 这样拆开的字母，或者加进读音表。用 Ming 不用改。
- **中文部分：** 两边都念对了。

试听（每个文件连放同一句的 3 次生成）：[CosyVoice 3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh07_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh07_ming.mp3)

### 更多案例

**1. 每一笔成交都带着 timestamp，精确到毫秒。**
CosyVoice 3 被听成 "time palm" 之类，0/3。Ming 3/3。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh55_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh55_ming.mp3)

**2. Sharpe Ratio 衡量的是每承担一份风险，能换来多少收益。**
CosyVoice 3 被听成 "Sup Ratio"、"Shop Ratio"，1/3。Ming 3/3。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh35_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh35_ming.mp3)

**3. 处理矩阵运算，NumPy 比纯循环快几十倍。**
CosyVoice 3 被听成 "NAMP"、"NinPi"，1/3。Ming 3/3。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh32_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh32_ming.mp3)

**4. 把 LLM 和 RAG 结合起来，就能做一个研报问答助手。**
CosyVoice 3 的 LLM 3/3，Ming 1/3。RAG 两边都只对了 1 次。这类连续的字母缩写，两个模型都需要写成 "L L M"、"R A G"。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh13_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh13_ming.mp3)

**5. 风控部门每天都要计算组合的 VaR。**
两边都是 0/3，中间的 A 被吞掉，听成 "VR"。要写成 "V A R"，或者直接说"风险价值"。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh09_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/zh09_ming.mp3)

**结论：** 不建读音表时，Ming 的英文整体更准。它的优势在"认识的单词"，比如 timestamp、NumPy、Sharpe Ratio、MACD、Backtest、ROS。两个模型都要处理的是少数连续字母缩写，比如 RAG、VaR。办法很简单：统一拆成字母写，不用逐词维护读音表。

## 四、问题 2：纯英文，不建读音表

**主要数据**

- **整句错词率：** Ming 3.2%，CosyVoice 3 3.9%。
- **整句一字不差（共 60 条）：** Ming 40 条，CosyVoice 3 31 条。
- **难词识别率：** 两边差不多，CosyVoice 3 98.5%，Ming 98.2%。
- **漏读、拖音：** 两边都是 0。

**不建读音表时，还需要处理哪些词？**

20 句里共有 91 个难词，包括缩写、长单词和以前进过读音表的词。

- **CosyVoice 3 需要处理 2 个：** reusable（2/3）、CAM（5/6）。
- **Ming 需要处理 1 个：** ROS（0/3，被听成 "RS"）。
- 另有 ninety-eight 两边都被判错。实际上两边都念对了，只是 Whisper 把它写成了数字 "1998"，属于判分误差。

我生产用的英文读音表里，有 6 个词出现在测试句中：encoder、ROS、OpenCV、intrinsics、MPC、reusable。不用读音表，两个模型都能 3 次全对其中 5 个。

案例：

- **OpenCV：** CosyVoice 3 有一次被听成 "OpenSev"。Ming 3 次全对，整句一字不差。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/en08_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/en08_ming.mp3)
- **reusable：** CosyVoice 3 有两次念错，被听成 "ruvro"、"reasonable"。Ming 3 次全对。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/en12_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/en12_ming.mp3)
- **ROS 2：** CosyVoice 3 3/3。Ming 念成 "RS 2"，需要写成 "Ross 2"。
[CV3](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/en07_cv3.mp3) ｜ [Ming](https://github.com/fat1/tts-cosyvoice3-vs-ming3/blob/main/audio_cases/en07_ming.mp3)

**结论：英文基本不需要读音表了。** 两个模型不用读音表，难词识别率都在 98% 以上，每个模型只剩 1–2 个词要处理。留一张只有几个词的小表就够了。Ming 的整句准确率更高。

## 五、总结

**Ming-3.0-tts 的优势**

- 不建读音表时英文更准：中英混读里，单词和工具名 100% 念对；纯英文整句一字不差的有 40 条，CosyVoice 3 是 31 条。
- 更稳定：58 个英文词里，3 次都念对的有 49 个，CosyVoice 3 是 39 个。
- 中文质量没有退步，没有漏读和拖音。
- 输出 44.1 kHz；MIT 许可；版本最新；支持 7 种语言，外加四川话和粤语。

**还需要注意的地方**

- 连续字母缩写（LLM、VWAP）不如 CosyVoice 3 稳，统一拆成字母写就能解决。
- 生成速度大约慢一倍，这次没装 flash-attn，也没用 vLLM，还有优化空间。
- 克隆音色相似度比 CosyVoice 3 低：0.77 对 0.89。原因之一可能是参考音只有 8 kHz，而 Ming 输出 44.1 kHz 宽频。实际像不像，以试听为准。

**一句话：** 不建读音表时，Ming-3.0-tts 在中英混读和纯英文上都比 CosyVoice 3 念得准。字母缩写用拆字母的写法统一处理，英文只需要保留几个词的小读音表。

完整数据和全部音频：<https://github.com/fat1/tts-cosyvoice3-vs-ming3>
