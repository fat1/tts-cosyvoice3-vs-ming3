"""整句英文测试：CosyVoice3 按生产方式合成（中文样本 → 跨语种克隆、套 pronounce_en.txt 读音表、不重试）。在 tts-gpu 环境运行。
用法: python gen_cv3_en.py [句子编号…]   输出 out/en_cv3/<编号>_<第几次>.wav 和 timing.json
"""
from __future__ import annotations

import json
import sys
import time

COSYVOICE_ROOT = r"D:\steven\models\CosyVoice"
sys.path[:0] = [COSYVOICE_ROOT, COSYVOICE_ROOT + r"\third_party\Matcha-TTS", r"D:\steven\videos_generated_CC\studio"]

import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from cosyvoice.cli.cosyvoice import CosyVoice3  # noqa: E402
from pronounce import apply_lexicon  # noqa: E402

from common import ROOT, RUNS, SAMPLE, load_en  # noqa: E402

PREFIX = "You are a helpful assistant.<|endofprompt|>"


def main() -> None:
    only = set(sys.argv[1:])
    out = ROOT / "out" / "en_cv3"
    out.mkdir(parents=True, exist_ok=True)
    model = CosyVoice3(COSYVOICE_ROOT + r"\pretrained_models\Fun-CosyVoice3-0.5B", load_trt=False, fp16=False)
    tpath = out / "timing.json"
    timing = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else {}
    for s in load_en():
        if only and s["id"] not in only:
            continue
        for k in range(1, RUNS + 1):
            t0 = time.time()
            parts = []
            for seg in model.frontend.text_normalize(apply_lexicon(s["text"], lang="en"), split=True):
                chunks = model.inference_cross_lingual(PREFIX + seg, str(SAMPLE), stream=False, text_frontend=False)
                parts += [c["tts_speech"].float().cpu() for c in chunks]
            a = torch.cat(parts, dim=1).squeeze(0).numpy()
            dt = time.time() - t0
            name = f"{s['id']}_{k}"
            sf.write(out / f"{name}.wav", a, model.sample_rate, subtype="PCM_16")
            timing[name] = {"gen_s": round(dt, 2), "dur_s": round(len(a) / model.sample_rate, 2)}
            print(f"{name} {dt:.1f}s / {len(a) / model.sample_rate:.1f}s", flush=True)
        tpath.write_text(json.dumps(timing, indent=1), encoding="utf-8")
    print(f"VRAM_PEAK_GB {torch.cuda.max_memory_allocated() / 1e9:.2f}")


if __name__ == "__main__":
    main()
