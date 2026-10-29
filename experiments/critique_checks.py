"""Referee checks on our own reproduction report.

Each block answers an objection a reviewer would raise:
  1. r = 0.99 across a 0.3-200 Hz range is inflated by dynamic range and by the
     clamped stimulated neurons. Recompute on logs, and on downstream cells only.
  2. 62 of their 448 active neurons never fired for us. Which ones, and how fast
     were they in the published run?
  3. Only one motor neuron 9 was tracked. Their Figure 1c shows two (ipsi- and
     contralateral). Is a second one identifiable?
  4. How much does our own run vary run to run, independent of theirs?
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
RES = ROOT / "results" / "repro_shiu"
sys.path.insert(0, str(REPO))

from model import default_params  # noqa: E402
import utils as utl  # noqa: E402
from repro_shiu import NEU_SUGAR  # noqa: E402

MN9 = 720575940660219265

df = pd.read_csv(RES / "side_by_side.csv", index_col=0)
df.index = df.index.astype("int64")
driven = df.loc[[i for i in NEU_SUGAR if i in df.index]]
downstream = df.drop(index=driven.index, errors="ignore")

print("=" * 72)
print("1. CORRELATION, STRESS-TESTED")
print("=" * 72)
print(f"  raw, all neurons          r = {df['ours'].corr(df['theirs']):.4f}  (n={len(df)})")
print(f"  raw, downstream only      r = {downstream['ours'].corr(downstream['theirs']):.4f}  (n={len(downstream)})")
lg = np.log10(downstream[["ours", "theirs"]].clip(lower=0.1))
print(f"  log10, downstream only    r = {lg['ours'].corr(lg['theirs']):.4f}")
print(f"  Spearman, downstream only r = {downstream['ours'].corr(downstream['theirs'], method='spearman'):.4f}")
print("  -> the headline number should be the downstream, log-scale one:"
      " the stimulated cells are clamped by the input and inflate the raw figure.")

print()
print("=" * 72)
print("2. THE NEURONS WE MISSED")
print("=" * 72)
theirs_all = utl.load_exps([str(REPO / "results" / "example" / "sugarR.parquet")])
r_theirs, _ = utl.get_rate(theirs_all, t_run=default_params["t_run"], n_run=30)
s_theirs = pd.to_numeric(r_theirs.iloc[:, 0], errors="coerce")
s_theirs.index = s_theirs.index.astype("int64")

ours_all = utl.load_exps([str(RES / "sugarR_quick.parquet")])
r_ours, _ = utl.get_rate(ours_all, t_run=default_params["t_run"], n_run=3)
s_ours = pd.to_numeric(r_ours.iloc[:, 0], errors="coerce")
s_ours.index = s_ours.index.astype("int64")

missing = s_theirs.index.difference(s_ours.index)
extra = s_ours.index.difference(s_theirs.index)
print(f"  active in theirs but not ours : {len(missing)}")
print(f"  active in ours but not theirs : {len(extra)}")
if len(missing):
    m = s_theirs.loc[missing]
    print(f"  their rates for the missing   : median {m.median():.2f} Hz, "
          f"90th pct {m.quantile(0.9):.2f} Hz, max {m.max():.2f} Hz")
    print(f"  fraction of missing below 2 Hz: {(m < 2).mean():.0%}")
    print("  -> consistent with 3 trials missing rare spikes, not with a structural difference.")

print()
print("=" * 72)
print("3. IS THERE A SECOND MOTOR NEURON 9?")
print("=" * 72)
comp = pd.read_csv(REPO / "2023_03_23_completeness_630_final.csv")
print("  completeness columns:", list(comp.columns)[:8])
hit = comp[comp.apply(lambda r: r.astype(str).str.contains("MN9|motor", case=False).any(), axis=1)]
print(f"  rows mentioning MN9/motor: {len(hit)}")
if len(hit):
    print(hit.head(6).to_string())
print(f"  MN9 present in completeness table: {(comp.iloc[:, 0] == MN9).any()}")

print()
print("=" * 72)
print("4. OUR OWN RUN-TO-RUN SPREAD (per-trial, driven cells and MN9)")
print("=" * 72)
counts = ours_all.groupby(["flywire_id", "trial"]).size().rename("n").reset_index()
counts["rate"] = counts["n"] / 1.0
wide = counts.pivot(index="flywire_id", columns="trial", values="rate").fillna(0.0)
wide.index = wide.index.astype("int64")
d = wide.reindex(NEU_SUGAR).dropna()
print(f"  stimulated cells: mean {d.mean(axis=1).mean():.1f} Hz, "
      f"between-trial sd {d.std(axis=1, ddof=1).mean():.1f} Hz")
if MN9 in wide.index:
    m9 = wide.loc[MN9]
    print(f"  MN9 per trial: {[round(v, 1) for v in m9.tolist()]}  "
          f"mean {m9.mean():.1f}  sd {m9.std(ddof=1):.1f}")
    print(f"  -> a 3-trial mean carries roughly +/- {m9.std(ddof=1)/np.sqrt(3):.1f} Hz of standard error.")
