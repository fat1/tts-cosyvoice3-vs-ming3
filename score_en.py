"""整句英文测试打分（TAG=std 时读 out/std_en_*，写 std/en/；参考音用 REF=en）：out/en_cv3、out/en_ming → en/report_en.csv、en/汇总_en.txt、en/试听_en.wav、en/试听_en_目录.txt。在 tts-gpu 环境运行。

WER：Whisper large-v3-turbo（language=en）转写，原文和转写都过 Whisper 的 EnglishTextNormalizer（统一数字、大小写、标点）后按词算编辑距离。
难词：缩写（≥2 个大写字母）、≥9 个字母的词、英文读音表里的词，按 pronounce 的字母相似度判定有没有被识别出来。
"""
from __future__ import annotations

import csv
import json
import re
import sys

import numpy as np
import soundfile as sf
import torch
import torchaudio

from common import ROOT, RUNS, load_en
from score import RES, TAG, Spk, load16, pronounce

MODELS = {m: f"{TAG}_en_{m}" if TAG else f"en_{m}" for m in ("cv3", "ming")}
RATE_EN = (1.5, 4.2)  # 每秒词数，与 cosyvoice_worker.RATE 相同
LEX = {e["word"].lower() for e in pronounce.load_lexicon_en()}


def hard_words(text: str) -> list[str]:
    ws = re.findall(r"[A-Za-z][A-Za-z'-]*", text)
    return list(dict.fromkeys(w for w in ws if (sum(c.isupper() for c in w) >= 2) or len(re.sub(r"[^a-z]", "", w.lower())) >= 9
                              or w.lower() in LEX))


def wer(ref: list[str], hyp: list[str]) -> tuple[int, int]:
    d = list(range(len(hyp) + 1))
    for i, r in enumerate(ref, 1):
        prev, d[0] = d[0], i
        for j, h in enumerate(hyp, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (r != h))
    return d[-1], len(ref)


def main() -> None:
    import whisper
    from whisper.normalizers import EnglishTextNormalizer

    norm = EnglishTextNormalizer()
    asr = whisper.load_model("large-v3-turbo", device="cuda", download_root=str(pronounce.WHISPER_DIR))
    spk = Spk()
    rows = []
    for m, sub in MODELS.items():
        timing = json.loads((ROOT / "out" / sub / "timing.json").read_text(encoding="utf-8"))
        for s in load_en():
            for k in range(1, RUNS + 1):
                name = f"{s['id']}_{k}"
                a16 = load16(ROOT / "out" / sub / f"{name}.wav")
                heard = asr.transcribe(a16, language="en", condition_on_previous_text=False, fp16=True)["text"].strip()
                err, n = wer(norm(s["text"]).split(), norm(heard).split())
                hw = hard_words(s["text"])
                hl = pronounce._letters(heard)
                ok = [pronounce._match(pronounce._letters(w), hl)[0] >= (pronounce.EN_MIN_SHORT if len(pronounce._letters(w)) <= 4 else pronounce.EN_MIN)
                      for w in hw]
                dur = len(a16) / 16000
                rate = len(re.findall(r"[A-Za-z0-9]+", s["text"])) / dur
                rows.append({"model": m, "id": s["id"], "run": k, "src": s["src"], "wer_err": err, "wer_n": n,
                             "hard": ";".join(hw), "hard_ok": ";".join("1" if o else "0" for o in ok),
                             "missed": ";".join(w for w, o in zip(hw, ok) if not o),
                             "spk_sim": round(float(spk(a16) @ spk.ref), 3), "dur_s": round(dur, 2),
                             "rate_ok": int(RATE_EN[0] <= rate <= RATE_EN[1]),
                             "rtf": round(timing[name]["gen_s"] / timing[name]["dur_s"], 2),
                             "heard": heard, "text": s["text"]})
                print(m, name, f"WER {err}/{n}", rows[-1]["missed"], flush=True)
    out = RES / "en"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "report_en.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    summarize(rows, out)
    listening(rows, out)


def summarize(rows: list[dict], out) -> None:
    by = {m: [r for r in rows if r["model"] == m] for m in MODELS}
    L = ["整句英文测试：CV3 vs Ming，两边都不套读音表、克隆同一段英文参考音（Ming 用 language_id=English）",
         "20 句来自已完成系列的英文旁白，每句 3 次；Whisper large-v3-turbo 转写。", "",
         f"{'指标':<16}" + "".join(f"{m:>12}" for m in MODELS)]

    def line(label, f):
        L.append(f"{label:<16}" + "".join(f"{f(m):>12}" for m in MODELS))

    line("WER（越低越好）", lambda m: f"{100 * sum(r['wer_err'] for r in by[m]) / sum(r['wer_n'] for r in by[m]):.1f}%")
    line("整句全对的条数", lambda m: f"{sum(r['wer_err'] == 0 for r in by[m])}/{len(by[m])}")

    def hard(m):
        v = [int(x) for r in by[m] for x in r["hard_ok"].split(";") if x]
        return f"{100 * sum(v) / len(v):.1f}%"

    line("难词识别率", hard)
    line("音色相似度", lambda m: f"{np.mean([r['spk_sim'] for r in by[m]]):.3f}")
    line("语速异常条数", lambda m: f"{sum(1 - r['rate_ok'] for r in by[m])}/{len(by[m])}")
    line("RTF", lambda m: f"{np.median([r['rtf'] for r in by[m]]):.2f}")
    L += ["", "逐句 WER（3 次合计错词数 / 词数×3）与没识别出的难词："]
    for sid in dict.fromkeys(r["id"] for r in rows):
        parts = []
        for m in MODELS:
            rs = [r for r in by[m] if r["id"] == sid]
            miss = sorted({w for r in rs for w in r["missed"].split(";") if w})
            parts.append(f"{m} {sum(r['wer_err'] for r in rs):>2}/{sum(r['wer_n'] for r in rs):<3} 漏:{','.join(miss) or '-'}")
        L.append(f"{sid} {rs[0]['src']:<7} " + " | ".join(parts))
    # 回答"英文还要不要读音表"：逐个难词统计 3 次里念对几次
    words = {}
    for r in rows:
        for w, o in zip(r["hard"].split(";"), r["hard_ok"].split(";")):
            if w:
                words.setdefault(w, {m: [] for m in MODELS})[r["model"]].append(int(o))
    L += ["", f"逐个难词（共 {len(words)} 个）：3 次里至少错 1 次 → 不建读音表时需要处理"]
    for m in MODELS:
        bad = [f"{w}({sum(v[m])}/{len(v[m])})" for w, v in words.items() if v[m] and not all(v[m])]
        L.append(f"  {m} 需处理 {len(bad)} 个：{'、'.join(bad) or '无'}")
    inlex = [w for w in words if w.lower() in LEX]
    L += ["", f"生产读音表 pronounce_en.txt 里的词出现在测试句中的有 {len(inlex)} 个：{'、'.join(inlex) or '无'}"]
    for m in MODELS:
        ok = [w for w in inlex if all(words[w][m])]
        L.append(f"  {m} 不用读音表 3 次全对：{len(ok)}/{len(inlex)}  仍错：{'、'.join(w for w in inlex if w not in ok) or '无'}")
    (out / "汇总_en.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))


def listening(rows: list[dict], out, sr: int = 44100) -> None:
    t = np.arange(int(0.15 * sr)) / sr
    beep = (0.2 * np.sin(2 * np.pi * 1000 * t)).astype("float32")
    gap = np.zeros(int(0.4 * sr), dtype="float32")
    audio, cat, pos, n = [], ["整句英文试听：每句先 cv3 后 ming（各取第 1 次），每段前一声提示音。", ""], 0, 0
    for r in [r for r in rows if r["run"] == 1 and r["model"] == "cv3"]:
        for m, sub in MODELS.items():
            rr = next(x for x in rows if x["model"] == m and x["id"] == r["id"] and x["run"] == 1)
            a, r0 = sf.read(ROOT / "out" / sub / f"{r['id']}_1.wav", dtype="float32")
            a = torchaudio.functional.resample(torch.from_numpy(a)[None], r0, sr)[0].numpy()
            n += 1
            cat.append(f"{n:>3}  {pos // sr // 60}:{pos / sr % 60:04.1f}  {r['id']} {m:<5} WER {rr['wer_err']}/{rr['wer_n']}"
                       f"  漏:{rr['missed'] or '-'}  听成: {rr['heard']}")
            for x in (beep, gap, a, gap):
                audio.append(x)
                pos += len(x)
        cat.append(f"          原文: {r['text']}")
    sf.write(out / "试听_en.wav", np.concatenate(audio), sr, subtype="PCM_16")
    (out / "试听_en_目录.txt").write_text("\n".join(cat) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
