"""从已完成系列的英文旁白里挑 20 句难词最多的整句英文，写 sentences_en.txt。"""
import re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
SER = Path(r"D:\steven\videos_generated_CC\studio\series")
lex = {l.split("|")[0].strip().lower() for l in (SER.parent / "pronounce_en.txt").read_text(encoding="utf-8").splitlines()
       if "|" in l and not l.startswith("#")}
cands = []
for s in ("quant", "engineering", "physical_ai", "ug_cam"):
    for md in sorted(SER.glob(f"{s}/*/episode.md")):
        if not list(md.parent.glob("*_EN.mp4")) or "## 3. Bilingual" not in md.read_text(encoding="utf-8"):
            continue
        for row in re.findall(r"^\|[^|\n]+\|[^|\n]+\|([^|\n]+)\|\s*$", md.read_text(encoding="utf-8").split("## 3.")[1].split("## 4.")[0], re.M):
            for sent in re.split(r"(?<=[.!?])\s+", row.strip()):
                words = re.findall(r"[A-Za-z][A-Za-z'-]*", sent)
                if not 12 <= len(words) <= 32:
                    continue
                hard = [w for w in words if (w.isupper() and len(w) >= 2) or len(w) >= 9 or w.lower() in lex]
                cands.append((len(set(hard)), s, md.parent.name, sent, hard))
cands.sort(key=lambda c: -c[0])
picked, per = [], {}
for c in cands:  # 每个系列最多 5 句，句子不重复
    if per.get(c[1], 0) < 5 and c[3] not in [p[3] for p in picked]:
        picked.append(c); per[c[1]] = per.get(c[1], 0) + 1
    if len(picked) == 20:
        break
out = ["# 整句英文测试：编号 | 来源 | 句子（原文，CV3 生成时套 pronounce_en.txt，Ming 原样）"]
for i, (n, s, ep, sent, hard) in enumerate(picked, 1):
    out.append(f"{i:02d} | {ep} | {sent}")
    print(f"{i:02d} {ep} [{','.join(dict.fromkeys(hard))}] {sent}")
(Path(__file__).parent / "sentences_en.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
