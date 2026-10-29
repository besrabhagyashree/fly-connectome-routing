"""Side-by-side: our reproduction against Shiu et al.'s own published outputs.

The paper's Figure 1 traces sugar-sensing neurons through a named circuit to
motor neuron 9 (MN9), whose firing rate is the headline read-out. Their repo ships
the runs behind that figure, so we can compare neuron by neuron.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

from model import default_params  # noqa: E402
import utils as utl  # noqa: E402

MN9 = 720575940660219265  # from the authors' example notebook


def rates(path, n_run=None):
    df = utl.load_exps([str(path)])
    n = n_run or df["trial"].nunique()
    r, _ = utl.get_rate(df, t_run=default_params["t_run"], n_run=n)
    s = pd.to_numeric(r.iloc[:, 0], errors="coerce")
    s.index = s.index.astype("int64")
    return s


theirs_150 = rates(REPO / "results" / "example" / "sugarR.parquet")
theirs_100 = rates(REPO / "results" / "example" / "sugarR_100Hz.parquet")
ours_150 = rates(ROOT / "results" / "repro_shiu" / "sugarR_quick.parquet")

print("=" * 74)
print("MOTOR NEURON 9 — the paper's headline read-out (Fig. 1c)")
print("=" * 74)
for label, s in (("their run, 150 Hz drive", theirs_150),
                 ("their run, 100 Hz drive", theirs_100),
                 ("OUR run, 150 Hz drive", ours_150)):
    val = s.get(MN9)
    print(f"  {label:26s}  MN9 = {val:7.2f} Hz" if val is not None and val == val
          else f"  {label:26s}  MN9 = silent / absent")

print()
print("=" * 74)
print("WHOLE POPULATION")
print("=" * 74)
joined = pd.concat([ours_150.rename("ours"), theirs_150.rename("theirs")], axis=1).dropna()
print(f"  neurons active in both        : {len(joined)}")
print(f"  neurons active, theirs / ours : {(theirs_150 > 0).sum()} / {(ours_150 > 0).sum()}")
print(f"  Pearson r                     : {joined['ours'].corr(joined['theirs']):.4f}")
print(f"  Spearman r                    : {joined['ours'].corr(joined['theirs'], method='spearman'):.4f}")
print(f"  median rate                   : ours {joined['ours'].median():.2f} Hz, "
      f"theirs {joined['theirs'].median():.2f} Hz")

driven = joined.loc[joined.index.isin([
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
    720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
])]
downstream = joined.drop(index=driven.index, errors="ignore")
print()
print(f"  directly driven sugar neurons : ours {driven['ours'].mean():6.1f} Hz vs "
      f"theirs {driven['theirs'].mean():6.1f} Hz   ({driven['ours'].mean()/driven['theirs'].mean():.2f}x)")
print(f"  everything downstream         : ours {downstream['ours'].mean():6.1f} Hz vs "
      f"theirs {downstream['theirs'].mean():6.1f} Hz   ({downstream['ours'].mean()/downstream['theirs'].mean():.2f}x)")

print()
print("=" * 74)
print("TOP 10 MOST ACTIVE NEURONS IN THEIR RUN, WITH OUR RATES")
print("=" * 74)
top = joined.sort_values("theirs", ascending=False).head(10)
top = top.assign(ratio=(top["ours"] / top["theirs"]).round(2))
print(top.to_string())

out = ROOT / "results" / "repro_shiu" / "side_by_side.csv"
joined.to_csv(out)
print(f"\nwrote {out}")
