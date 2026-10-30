"""Step 6b (exploratory): the real brain at lower input rates, following
results/exp06b_plan.md. Finds the rate where about 177 neurons fire, the mean of the
100 inside-only brains of step 6, and compares spread there.

  .venv-brian/Scripts/python.exe experiments/exp06b_matched_activity.py
"""
from __future__ import annotations

import ctypes
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp06_shiu_spiking import COMP, CON, META, MN9, N_TRIALS, ROOT, score, sugar_783  # noqa: E402

OUT = ROOT / "results" / "exp06b"
CSV = ROOT / "results" / "exp06b_matched.csv"
TARGET = 177
INSIDE = {"interior_degree_preserving": 20.664, "interior_block_preserving": 21.725}


def keep_awake():
    """Block system sleep while this process runs; no setting is changed."""
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)


def main():
    from brian2 import Hz
    from model import default_params, run_exp

    keep_awake()
    OUT.mkdir(parents=True, exist_ok=True)
    ids = pd.read_csv(COMP, index_col=0).index.astype("int64").to_numpy()
    meta = pd.read_parquet(META)
    meta = meta.set_index(meta["root_id"].astype("int64")).reindex(ids).reset_index(drop=True)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    neu = sugar_783(ids)

    rows = [{"rate_hz": 150, **score(ROOT / "results" / "exp06" / "real_0.parquet", ids, readout)}]

    def run(rate):
        p = dict(default_params)
        p["n_run"] = N_TRIALS
        p["r_poi"] = rate * Hz
        run_exp(exp_name=f"real_{rate}Hz", neu_exc=neu, path_res=str(OUT), path_comp=str(COMP),
                path_con=str(CON), params=p, n_proc=N_TRIALS, force_overwrite=True)
        rows.append({"rate_hz": rate, **score(OUT / f"real_{rate}Hz.parquet", ids, readout)})
        pd.DataFrame(rows).sort_values("rate_hz").to_csv(CSV, index=False)
        print(rows[-1], flush=True)

    for rate in (50, 75, 100, 125):
        run(rate)
    d = pd.DataFrame(rows).sort_values("rate_hz")
    below, above = d[d.brain_active < TARGET], d[d.brain_active >= TARGET]
    if len(below) and len(above):
        mid = int(round((below.rate_hz.max() + above.rate_hz.min()) / 2))
        if mid not in set(d.rate_hz):
            run(mid)
    d = pd.DataFrame(rows).sort_values("rate_hz")
    m = d.iloc[(d.brain_active - TARGET).abs().argmin()]
    go = all(m.spread < v for v in INSIDE.values())
    print(d.round(3).to_string(index=False))
    print(f"\nMatched rate {m.rate_hz} Hz: {m.brain_active} active, spread {m.spread:.2f}, "
          f"MN9 {m.mn9_hz:.1f} Hz. Run step 6c: {'YES' if go else 'NO'}", flush=True)


if __name__ == "__main__":
    main()
