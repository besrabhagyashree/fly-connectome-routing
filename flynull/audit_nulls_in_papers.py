"""Which of the papers in our library actually use null models?

Searches each PDF for the vocabulary of surrogate/null-model controls and prints
the sentences, so the answer is evidence rather than recollection.
"""
from __future__ import annotations

import glob
import os
import re
import sys

from pypdf import PdfReader

PAPERS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "papers")

PAT = re.compile(
    r"(null model|rewir\w+|shuffl\w+|randomi[sz]ed? (?:network|graph|connectome|control|version)"
    r"|degree[- ]preserv\w+|surrogate|configuration model|Erd[^\s]{0,3}s[- ]?R|random graph)",
    re.I,
)
MAX_PAGES = 45


def sentences(txt, pat, limit=2):
    out = []
    for s in re.split(r"(?<=[.!?]) +", txt):
        if pat.search(s) and 40 < len(s) < 320:
            out.append(re.sub(r"\s+", " ", s).strip())
        if len(out) >= limit:
            break
    return out


def main():
    verbose = "-v" in sys.argv
    for f in sorted(glob.glob(os.path.join(PAPERS, "*.pdf"))):
        name = os.path.basename(f)
        try:
            reader = PdfReader(f)
            txt = " ".join((p.extract_text() or "") for p in reader.pages[:MAX_PAGES])
        except Exception as exc:
            print(f"{name[:52]:54s} ERROR {exc}")
            continue
        txt = re.sub(r"\s+", " ", txt)
        hits = PAT.findall(txt)
        kinds = sorted({h.lower()[:20] for h in hits})
        mark = "YES" if len(hits) >= 3 else ("weak" if hits else "none")
        print(f"{name[:52]:54s} {mark:5s} {len(hits):4d}  {'; '.join(kinds[:5])}")
        if verbose and hits:
            for s in sentences(txt, PAT):
                print(f"      > {s}")


if __name__ == "__main__":
    main()
