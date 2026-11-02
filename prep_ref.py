"""准备第三方标准参考音（Open Speech Repository）：下载 → 16 kHz 单声道 → 截取前几句、句间停顿压到 0.35 秒。
输出 ref/zh.wav、ref/zh.txt、ref/en.wav、ref/en.txt。在 tts-gpu 环境运行：python prep_ref.py
切点由 ffmpeg silencedetect（-30dB, 0.25s）得到，逐字稿由 Whisper large-v3-turbo + Paraformer 转写并核对。
"""
from __future__ import annotations

import urllib.request
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

ROOT = Path(__file__).resolve().parent
REF = ROOT / "ref"
SR = 16000
GAP = 0.35  # 句间停顿（秒）
PAD = 0.08  # 每句前后留白（秒）

SOURCES = {
    "zh": {
        "url": "https://www.voiptroubleshooter.com/open_speech/chinese/OSR_cn_000_0072_8k.wav",
        "spans": [(0.69, 3.13), (4.23, 6.61), (7.82, 10.43)],
        "text": "院子门口不远处就是一个地铁站。这是一个美丽而神奇的景象。树上长满了又大又甜的桃子。",
    },
    "en": {
        "url": "https://www.voiptroubleshooter.com/open_speech/american/OSR_us_000_0010_8k.wav",
        "spans": [(0.52, 2.87), (4.17, 6.42), (7.83, 9.65), (10.90, 12.95)],
        "text": "The birch canoe slid on the smooth planks. Glue the sheet to the dark blue background. "
                "It is easy to tell the depth of a well. These days a chicken leg is a rare dish.",
    },
}


def main() -> None:
    (REF / "raw").mkdir(parents=True, exist_ok=True)
    for lang, src in SOURCES.items():
        raw = REF / "raw" / f"{lang}_src.wav"
        if not raw.exists():
            urllib.request.urlretrieve(src["url"], raw)
        a, sr = sf.read(raw, dtype="float32")
        a = resample_poly(a, SR, sr).astype(np.float32)
        gap = np.zeros(int(GAP * SR), np.float32)
        parts = []
        for s, e in src["spans"]:
            parts += [a[int(max(0, s - PAD) * SR):int((e + PAD) * SR)], gap]
        out = np.concatenate(parts[:-1])
        out = out / max(1e-6, np.abs(out).max()) * 0.9
        sf.write(REF / f"{lang}.wav", out, SR, subtype="PCM_16")
        (REF / f"{lang}.txt").write_text(src["text"] + "\n", encoding="utf-8")
        print(f"{lang}: {len(out) / SR:.2f}s  {src['text']}")


if __name__ == "__main__":
    main()
