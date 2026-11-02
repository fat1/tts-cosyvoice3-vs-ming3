"""给 out/<模型>/ 下的所有 wav 打分，写 report.csv、汇总.txt、试听.wav、试听_目录.txt。在 tts-gpu 环境运行。
用法: python score.py [模型目录名…]（默认 cv3 ming）

英文词判定（两个模型用同一个裁判）：Whisper large-v3-turbo 分别按 zh 和 en 各转写一遍，
任一结果里能找到这个词（只比字母，滑动窗口相似度 ≥ pronounce.EN_MIN / EN_MIN_SHORT）就算念对。
中文部分：Paraformer 转写后用 pronounce.compare() 统计漏读和读错的字。
音色：CosyVoice3 自带的 campplus 说话人向量，与 steven.wav 的余弦相似度。
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
import torchaudio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "studio"))
import pronounce  # noqa: E402

from common import ROOT, RUNS, SAMPLE, load_sentences  # noqa: E402

CAMPPLUS = r"D:\steven\models\CosyVoice\pretrained_models\Fun-CosyVoice3-0.5B\campplus.onnx"
CATEGORY = {"A": range(1, 25), "W": range(25, 35), "M": range(35, 50), "R": range(50, 57), "H": range(57, 61)}
CAT_NAME = {"A": "字母缩写", "W": "单词/工具名", "M": "多词术语", "R": "曾经念错的词", "H": "同形异音"}
RATE_ZH = (2.5, 6.5)  # 与 cosyvoice_worker.RATE 相同：每秒字数（英文词按 2 字）


def category(sid: str) -> str:
    return next(c for c, r in CATEGORY.items() if int(sid) in r)


def load16(path: Path) -> np.ndarray:
    a, sr = sf.read(path, dtype="float32")
    return torchaudio.functional.resample(torch.from_numpy(a)[None], sr, 16000)[0].numpy()


class Spk:
    def __init__(self):
        import onnxruntime as ort

        self.sess = ort.InferenceSession(CAMPPLUS, providers=["CPUExecutionProvider"])
        self.ref = self(load16(SAMPLE))

    def __call__(self, a16: np.ndarray) -> np.ndarray:
        import torchaudio.compliance.kaldi as kaldi

        feat = kaldi.fbank(torch.from_numpy(a16)[None], num_mel_bins=80, dither=0, sample_frequency=16000)
        feat = feat - feat.mean(dim=0, keepdim=True)
        e = self.sess.run(None, {self.sess.get_inputs()[0].name: feat.unsqueeze(0).numpy()})[0].flatten()
        return e / np.linalg.norm(e)


def units(text: str) -> int:
    return len(re.findall(r"[一-鿿]", text)) + 2 * len(re.findall(r"[A-Za-z0-9]+", text))


def hit(term: str, heard_zh: str, heard_en: str) -> tuple[bool, str]:
    t = pronounce._letters(term)
    r, seg = max(pronounce._match(t, pronounce._letters(heard_zh)), pronounce._match(t, pronounce._letters(heard_en)))
    return r >= (pronounce.EN_MIN_SHORT if len(t) <= 4 else pronounce.EN_MIN), seg


def main() -> None:
    import whisper

    models = sys.argv[1:] or [m for m in ("cv3", "ming") if (ROOT / "out" / m / "timing.json").exists()]
    sents = load_sentences()
    asr = whisper.load_model("large-v3-turbo", device="cuda", download_root=str(pronounce.WHISPER_DIR))
    spk = Spk()
    rows = []
    for m in models:
        timing = json.loads((ROOT / "out" / m / "timing.json").read_text(encoding="utf-8"))
        for s in sents:
            for k in range(1, RUNS + 1):
                name = f"{s['id']}_{k}"
                wav = ROOT / "out" / m / f"{name}.wav"
                if not wav.exists():
                    continue
                a16 = load16(wav)
                zh = asr.transcribe(a16, language="zh", condition_on_previous_text=False, fp16=True)["text"]
                en = asr.transcribe(a16, language="en", condition_on_previous_text=False, fp16=True)["text"]
                terms = [(t, *hit(t, zh, en)) for t in s["terms"]]
                zh_issues = pronounce.compare(s["text"], pronounce.transcribe(str(wav)))
                dur = len(a16) / 16000
                rate = units(s["text"]) / dur
                rows.append({
                    "model": m, "id": s["id"], "run": k, "cat": category(s["id"]),
                    "terms": ";".join(t for t, _, _ in terms),
                    "ok": ";".join("1" if ok else "0" for _, ok, _ in terms),
                    "heard": ";".join(seg for _, _, seg in terms),
                    "zh_err": sum(1 for i in zh_issues if i["type"] != "读音不同"),
                    "zh_diff": sum(1 for i in zh_issues if i["type"] == "读音不同"),
                    "spk_sim": round(float(spk(a16) @ spk.ref), 3),
                    "dur_s": round(dur, 2), "rate_ok": int(RATE_ZH[0] <= rate <= RATE_ZH[1]),
                    "rtf": round(timing[name]["gen_s"] / timing[name]["dur_s"], 2),
                    "asr_zh": zh.strip(), "asr_en": en.strip(), "text": s["text"],
                })
                print(m, name, rows[-1]["ok"], rows[-1]["heard"], flush=True)
    with open(ROOT / "report.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summarize(rows, models)
    listening(sents, models)


def summarize(rows: list[dict], models: list[str]) -> None:
    per_term = defaultdict(lambda: defaultdict(list))  # 词 → 模型 → [0/1…]
    cat_of = {}
    for r in rows:
        for t, ok in zip(r["terms"].split(";"), r["ok"].split(";")):
            per_term[t][r["model"]].append(int(ok))
            cat_of[t] = r["cat"]
    L = ["CosyVoice3 vs Ming-3.0-tts-0.5B：中英混读英文发音对比（不套读音表，steven 克隆，每句 3 次）",
         "判定：Whisper large-v3-turbo zh/en 双转写，任一能识别出该词即算念对。识别对 ≠ 念得地道，以试听为准。", ""]
    L.append(f"{'指标':<14}" + "".join(f"{m:>12}" for m in models))

    def line(label, f):
        L.append(f"{label:<14}" + "".join(f"{f(m):>12}" for m in models))

    def rate(m, cat=None):
        v = [x for t, d in per_term.items() if cat in (None, cat_of[t]) for x in d[m]]
        return f"{100 * sum(v) / len(v):.1f}%" if v else "-"

    line("英文词正确率", rate)
    for c, n in CAT_NAME.items():
        line(f"  {n}", lambda m, c=c: rate(m, c))
    line("3次全对的词", lambda m: f"{sum(1 for d in per_term.values() if d[m] and all(d[m]))}/{len(per_term)}")
    by = {m: [r for r in rows if r["model"] == m] for m in models}
    line("中文读错字/条", lambda m: f"{np.mean([r['zh_err'] for r in by[m]]):.2f}")
    line("中文存疑字/条", lambda m: f"{np.mean([r['zh_diff'] for r in by[m]]):.2f}")
    line("音色相似度", lambda m: f"{np.mean([r['spk_sim'] for r in by[m]]):.3f}")
    line("语速异常条数", lambda m: f"{sum(1 - r['rate_ok'] for r in by[m])}/{len(by[m])}")
    line("RTF", lambda m: f"{np.median([r['rtf'] for r in by[m]]):.2f}")
    L += ["", "逐词（命中次数/3）："]
    L.append(f"{'词':<24}" + "".join(f"{m:>8}" for m in models))
    for t in sorted(per_term, key=lambda t: (cat_of[t], t.lower())):
        L.append(f"{t:<24}" + "".join(f"{sum(per_term[t][m])}/{len(per_term[t][m]):>3}".rjust(8) for m in models))
    if len(models) >= 2:
        a, b = models[:2]
        sc = {t: {m: sum(d[m]) / max(1, len(d[m])) for m in models} for t, d in per_term.items()}
        L += ["", f"{a} 差、{b} 好（差 ≥ 2/3）：" + "、".join(t for t, v in sc.items() if v[b] - v[a] >= 0.66),
              f"{b} 差、{a} 好（差 ≥ 2/3）：" + "、".join(t for t, v in sc.items() if v[a] - v[b] >= 0.66),
              "两边都不行（都 ≤ 1/3）：" + "、".join(t for t, v in sc.items() if max(v.values()) <= 0.34)]
    (ROOT / "汇总.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def listening(sents: list[dict], models: list[str], sr: int = 44100) -> None:
    """每句：提示音 → 模型1 第1次 → 提示音 → 模型2 第1次 …；目录写时间。"""
    t = np.arange(int(0.15 * sr)) / sr
    beep = (0.2 * np.sin(2 * np.pi * 1000 * t)).astype("float32")
    gap = np.zeros(int(0.4 * sr), dtype="float32")
    rows = {(r["model"], r["id"]): r for r in csv.DictReader(open(ROOT / "report.csv", encoding="utf-8-sig")) if r["run"] == "1"}
    audio, cat, pos, n = [], ["CV3 vs Ming 试听：每句先 cv3 后 ming，每段前一声提示音。", ""], 0, 0
    for s in sents:
        for m in models:
            wav = ROOT / "out" / m / f"{s['id']}_1.wav"
            if not wav.exists():
                continue
            a, r0 = sf.read(wav, dtype="float32")
            a = torchaudio.functional.resample(torch.from_numpy(a)[None], r0, sr)[0].numpy()
            n += 1
            r = rows.get((m, s["id"]), {})
            cat.append(f"{n:>3}  {pos // sr // 60}:{pos / sr % 60:04.1f}  {s['id']} {m:<5} {','.join(s['terms'])}  "
                       f"对={r.get('ok', '')}  听成={r.get('heard', '')}  | {s['text']}")
            for x in (beep, gap, a, gap):
                audio.append(x)
                pos += len(x)
    sf.write(ROOT / "试听.wav", np.concatenate(audio), sr, subtype="PCM_16")
    (ROOT / "试听_目录.txt").write_text("\n".join(cat) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
