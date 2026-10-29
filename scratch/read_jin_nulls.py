"""Print what Jin et al. 2026 (FlyGM) actually did with null models, and what they found."""
import os
import re

from pypdf import PdfReader

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = os.path.join(ROOT, "papers", "20_Jin2026_Whole-brain_connectomic_graph_model_locomotion_arXiv.pdf")

reader = PdfReader(F)
txt = " ".join((p.extract_text() or "") for p in reader.pages)
txt = re.sub(r"\s+", " ", txt)

pat = re.compile(r"(degree[- ]preserv\w+|rewir\w+|shuffl\w+|null|random graph|Erd)", re.I)
seen = set()
for s in re.split(r"(?<=[.!?]) +", txt):
    if pat.search(s) and 50 < len(s) < 420:
        key = s[:70]
        if key in seen:
            continue
        seen.add(key)
        print("-", s.strip(), "\n")
