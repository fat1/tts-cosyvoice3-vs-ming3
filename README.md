# TTS 实测：CosyVoice 3 vs Ming-3.0-tts（不建读音表）

在**两边都不用读音表**、**克隆同一段第三方标准声音**的条件下，比较 [Fun-CosyVoice3-0.5B](https://github.com/FunAudioLLM/CosyVoice) 和 [Ming-3.0-tts-0.5B](https://github.com/inclusionAI/Ming-3.0-tts) 的英文发音。

- Q1 中英混读：中文旁白夹英文缩写和术语（60 句，58 个英文词）
- Q2 纯英文：整句英文旁白里的专业术语（20 句）——英文还需要建读音表吗？

完整报告：[TTS模型选型与实测_为什么考虑换Ming3.md](TTS模型选型与实测_为什么考虑换Ming3.md)

## 主要结论

| 指标 | CosyVoice 3 | Ming-3.0-tts |
|---|---|---|
| Q1 英文词正确率 | 82.5% | **85.7%** |
| Q1 字母缩写 | **78.2%** | 73.1% |
| Q1 单词 / 工具名 | 81.8% | **100%** |
| Q1 3 次全对的词 | 39 / 58 | **49 / 58** |
| Q2 整句错词率 WER | 3.9% | **3.2%** |
| Q2 整句一字不差 | 31 / 60 | **40 / 60** |
| Q2 难词识别率 | 98.5% | 98.2% |
| Q2 不建读音表仍需处理的词 | reusable、CAM | ROS |
| 音色相似度（与参考音） | **0.89** | 0.77 |
| 速度 RTF（越小越快） | **1.9** | 4.6 |

## 参考音（Open Speech Repository）

- 中文：[OSR_cn_000_0072_8k.wav](https://www.voiptroubleshooter.com/open_speech/chinese/OSR_cn_000_0072_8k.wav)，取前 3 句（8.6 秒）
- 英文：[OSR_us_000_0010_8k.wav](https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav)，取前 4 句（10.2 秒）
- `prep_ref.py` 负责下载、转 16 kHz、截取并写出逐字稿（`ref/zh.txt`、`ref/en.txt`）。原音是 8 kHz，对两个模型影响相同，但音色相似度的绝对值会偏低。

## 目录

| 路径 | 内容 |
|---|---|
| `sentences.txt` / `en/sentences_en.txt` | Q1 / Q2 测试句 |
| `prep_ref.py` | 准备参考音 |
| `gen_cv3.py` / `gen_ming.py` | 生成（原句直接合成，不套读音表） |
| `score.py` / `score_en.py` | Whisper large-v3-turbo + Paraformer + campplus 打分 |
| `run_std.sh` | 一键跑完全部生成和打分 |
| `std/report.csv`、`std/汇总.txt` | Q1 每条明细、逐词汇总 |
| `std/en/report_en.csv`、`std/en/汇总_en.txt` | Q2 每条明细、逐词汇总 |
| `std/试听.mp3`、`std/en/试听_en.mp3` | 全部句子试听合集（先 CV3 后 Ming），目录见 `_目录.txt` |
| `audio_cases/` | 报告里引用的案例音频（每个文件连放同一句的 3 次生成）和参考音 |

## 复现

```bash
bash run_std.sh   # 依次：prep_ref → CV3/Ming 生成 Q1、Q2 → 打分
```

- 脚本里的模型 / 环境路径（`D:\steven\models\...`、`D:\miniconda3\envs\...`）是作者本机路径，请改成自己的。
- 打分复用作者项目里的 `studio/pronounce.py`（字母相似度阈值、中文比对、Whisper 路径），不在本仓库中。
- 原始 wav（`out/`）体积大，未入库。
- 测试环境：Windows 10，RTX 3060 Laptop 6GB；CosyVoice 3 fp32，Ming bf16（SDPA，无 flash-attn）。
