# TTS 实测：CosyVoice 3 vs Ming-3.0-tts（中英混读 / 整句英文）

不套读音表的条件下，比较 [Fun-CosyVoice3-0.5B](https://github.com/FunAudioLLM/CosyVoice) 和 [Ming-3.0-tts-0.5B](https://github.com/inclusionAI/Ming-3.0-tts) 的英文发音、中文准确率、音色相似度、稳定性和速度。

- 完整报告：[TTS模型选型与实测_为什么考虑换Ming3.md](TTS模型选型与实测_为什么考虑换Ming3.md)

## 主要结论

| 指标 | CosyVoice 3 | Ming-3.0-tts |
|---|---|---|
| 中英混读：英文词正确率 | 87.3% | 87.3% |
| 　字母缩写 | **83.3%** | 74.4% |
| 　单词 / 工具名 | 87.9% | **100%** |
| 语速异常 | 4 / 180 | **0 / 180** |
| 整句英文 WER（CV3 套读音表，Ming 不套） | **2.5%** | 3.3% |
| 速度 RTF | **2.10** | 4.69 |
| 输出采样率 | 24 kHz | **44.1 kHz** |

## 目录

| 路径 | 内容 |
|---|---|
| `sentences.txt` | 60 句中英混读测试句（含要核对的英文词） |
| `en/sentences_en.txt` | 20 句整句英文测试句（摘自已发布视频旁白） |
| `gen_cv3.py` / `gen_cv3_en.py` | CosyVoice 3 生成（中英混读 / 整句英文） |
| `gen_ming.py` | Ming 生成（环境变量 `MING_SET` / `MING_LANG` / `MING_OUT` 切换测试集） |
| `score.py` / `score_en.py` | Whisper large-v3-turbo + Paraformer + campplus 打分 |
| `common.py` | 读测试句、样本路径 |
| `setup_env.sh` / `run_test.sh` / `run_en.sh` | 环境搭建与批量运行脚本 |
| `report.csv` / `en/report_en.csv` | 每条音频的明细（转写、判定、相似度、RTF） |
| `汇总.txt` / `en/汇总_en.txt` | 逐词汇总 |
| `audio_cases/` | 报告里引用的案例音频（每个文件连放同一句的 3 次生成） |
| `试听.mp3` / `en/试听_en.mp3` | 全部句子试听合集（先 CV3 后 Ming），目录见对应 `_目录.txt` |

## 复现说明

- 脚本里的模型 / 环境路径（`D:\steven\models\...`、`D:\miniconda3\envs\...`）是作者本机路径，复现时请改成自己的。
- 克隆用的说话人参考音频（`studio/role/steven/steven.wav`）和生产用读音表 `pronounce_en.txt` 不在本仓库中，需要自备。
- 原始 wav（`out/`）体积较大，未入库；报告中的文件名 `试听.wav` 对应本仓库的 `试听.mp3`。
- 测试环境：Windows 10，RTX 3060 Laptop 6GB；CosyVoice 3 用 fp32，Ming 用 bf16（SDPA，无 flash-attn）。
