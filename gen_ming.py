"""Ming-3.0-tts-0.5B 克隆 steven，原句直接合成（不套读音表）。在 ming-tts 环境运行。
用法: python gen_ming.py [句子编号…]   输出 out/ming/<编号>_<第几次>.wav 和 out/ming/timing.json
环境变量 MING_LANG（默认 Chinese）、MING_TN=0 关掉文本归一化、MING_OUT 换输出子目录、MING_SET=en 用整句英文测试集。
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, r"D:\steven\models\Ming-3.0-tts")

import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from ming_tts import MingTTS  # noqa: E402

from common import PROMPT_TEXT, ROOT, RUNS, SAMPLE, load_en, load_sentences  # noqa: E402

LANG = os.environ.get("MING_LANG", "Chinese") or None


def main() -> None:
    only = set(sys.argv[1:])
    out = ROOT / "out" / os.environ.get("MING_OUT", "ming")
    out.mkdir(parents=True, exist_ok=True)
    model = MingTTS(r"D:\steven\models\Ming-3.0-tts-0.5B", text_normalization=os.environ.get("MING_TN", "1") != "0")
    tpath = out / "timing.json"
    timing = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else {}
    for s in (load_en() if os.environ.get("MING_SET") == "en" else load_sentences()):
        if only and s["id"] not in only:
            continue
        for k in range(1, RUNS + 1):
            torch.manual_seed(k)  # 流匹配头的采样噪声
            t0 = time.time()
            a = model.synthesize(task="TTS", text=s["text"], language_id=LANG, prompt_wav_path=str(SAMPLE),
                                 prompt_text=PROMPT_TEXT, use_spk_emb=True)
            a = a.float().cpu().squeeze(0).numpy()
            dt = time.time() - t0
            name = f"{s['id']}_{k}"
            sf.write(out / f"{name}.wav", a, model.sample_rate, subtype="PCM_16")
            timing[name] = {"gen_s": round(dt, 2), "dur_s": round(len(a) / model.sample_rate, 2)}
            print(f"{name} {dt:.1f}s / {len(a) / model.sample_rate:.1f}s", flush=True)
        tpath.write_text(json.dumps(timing, indent=1), encoding="utf-8")
    print(f"VRAM_PEAK_GB {torch.cuda.max_memory_allocated() / 1e9:.2f}")


if __name__ == "__main__":
    main()
