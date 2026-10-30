"""Step 6c: real brain at equal activity vs the step 6a inside-only brains already
at that activity, following results/exp06c_plan.md.

  .venv-brian/Scripts/python.exe experiments/exp06c_equal_activity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from exp06_shiu_spiking import COMP, CON, META, N_TRIALS, ROOT, score, sugar_783  # noqa: E402
from exp06b_matched_activity import keep_awake  # noqa: E402

OUT = ROOT / "results" / "exp06c"
CSV = ROOT / "results" / "exp06c_real_rates.csv"
TARGET, LO, HI = 177, 159, 195
TYPES = ("interior_degree_preserving", "interior_block_preserving")


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
    rows = []

    def run(rate):
        p = dict(default_params)
        p["n_run"] = N_TRIALS
        p["r_poi"] = rate * Hz
        name = f"real_{rate}Hz".replace(".", "p")
        run_exp(exp_name=name, neu_exc=neu, path_res=str(OUT), path_comp=str(COMP),
                path_con=str(CON), params=p, n_proc=N_TRIALS, force_overwrite=True)
        rows.append({"rate_hz": rate, **score(OUT / f"{name}.parquet", ids, readout)})
        pd.DataFrame(rows).sort_values("rate_hz").to_csv(CSV, index=False)
        print(rows[-1], flush=True)

    for rate in (40, 30, 20, 10):
        run(rate)
    for _ in range(3):
        d = pd.DataFrame(rows).sort_values("rate_hz")
        if d.brain_active.between(LO, HI).any():
            break
        below, above = d[d.brain_active < TARGET], d[d.brain_active > HI]
        if not (len(below) and len(above)):
            break
        run((below.rate_hz.max() + above.rate_hz.min()) / 2)

    d = pd.DataFrame(rows).sort_values("rate_hz")
    print(d.round(3).to_string(index=False))
    band = d[d.brain_active.between(LO, HI)]
    if band.empty:
        print("\nNO ANSWER: no tested rate landed in the band.", flush=True)
        return
    m = band.iloc[(band.brain_active - TARGET).abs().argmin()]
    a = pd.read_csv(ROOT / "results" / "exp06_all_brains.csv")
    res = []
    for g in TYPES:
        x = a[(a.network == g) & a.brain_active.between(LO, HI)]
        k = int((x.spread <= m.spread).sum())
        res.append({"network": g, "N": len(x), "real_rate_hz": m.rate_hz, "real_active": m.brain_active,
                    "real_spread": m.spread, "mean": x.spread.mean(), "sd": x.spread.std(ddof=1),
                    "min": x.spread.min(), "k_le_real": k, "p": (1 + k) / (len(x) + 1)})
    t = pd.DataFrame(res)
    t.to_csv(ROOT / "results" / "exp06c_summary.csv", index=False)
    print(t.round(4).to_string(index=False))
    print(f"\nRule: {'YES' if (t.p < 0.05).all() else 'NO'}", flush=True)


if __name__ == "__main__":
    main()
