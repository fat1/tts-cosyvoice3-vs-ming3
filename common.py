"""两个生成脚本共用：读测试句、steven 样本路径。"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
SAMPLE = ROOT.parent / "studio" / "role" / "steven" / "steven.wav"
PROMPT_TEXT = SAMPLE.with_suffix(".txt").read_text(encoding="utf-8").strip()
RUNS = 3  # 每句生成几次


def load_sentences() -> list[dict]:
    """sentences.txt → [{id, text, terms}]。"""
    out = []
    for line in (ROOT / "sentences.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        sid, text, terms = (s.strip() for s in line.split("|"))
        out.append({"id": sid, "text": text, "terms": [t.strip() for t in terms.split(",")]})
    return out


def load_en() -> list[dict]:
    """en/sentences_en.txt → [{id, src, text}]（整句英文测试）。"""
    out = []
    for line in (ROOT / "en" / "sentences_en.txt").read_text(encoding="utf-8").splitlines():
        if line.strip() and not line.startswith("#"):
            sid, src, text = (s.strip() for s in line.split("|", 2))
            out.append({"id": sid, "src": src, "text": text})
    return out
