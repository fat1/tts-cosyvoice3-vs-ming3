"""CosyVoice3 克隆 ref/ 下的标准参考音（REF=zh|en），原句直接合成（不套读音表、不重试）。在 tts-gpu 环境运行。
用法: python gen_cv3.py [句子编号…]   输出 out/<CV3_OUT，默认 cv3>/<编号>_<第几次>.wav；CV3_SET=en 用整句英文测试集。
"""
from __future__ import annotations

import json
import os
import sys
import time

COSYVOICE_ROOT = r"D:\steven\models\CosyVoice"
sys.path[:0] = [COSYVOICE_ROOT, COSYVOICE_ROOT + r"\third_party\Matcha-TTS"]

import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from cosyvoice.cli.cosyvoice import CosyVoice3  # noqa: E402

from common import PROMPT_TEXT, ROOT, RUNS, SAMPLE, load_en, load_sentences  # noqa: E402

PREFIX = "You are a helpful assistant.<|endofprompt|>"


def main() -> None:
    only = set(sys.argv[1:])
    out = ROOT / "out" / os.environ.get("CV3_OUT", "cv3")
    out.mkdir(parents=True, exist_ok=True)
    model = CosyVoice3(COSYVOICE_ROOT + r"\pretrained_models\Fun-CosyVoice3-0.5B", load_trt=False, fp16=False)
    model.add_zero_shot_spk(PREFIX + PROMPT_TEXT, str(SAMPLE), "user")
    tpath = out / "timing.json"
    timing = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else {}
    for s in (load_en() if os.environ.get("CV3_SET") == "en" else load_sentences()):
        if only and s["id"] not in only:
            continue
        for k in range(1, RUNS + 1):
            t0 = time.time()
            parts = []
            for seg in model.frontend.text_normalize(s["text"], split=True):  # 只做文本归一化，不套读音表
                chunks = model.inference_zero_shot(seg, "", "", zero_shot_spk_id="user", stream=False, text_frontend=False)
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
