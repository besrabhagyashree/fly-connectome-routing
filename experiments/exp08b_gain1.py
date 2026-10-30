"""Step 8b: rate model at gain 1.0, following results/exp08b_plan.md.

  python experiments/exp08b_gain1.py run --job 0/4
  python experiments/exp08b_gain1.py summary
"""
from __future__ import annotations

import argparse
import ctypes
import glob
import time
from pathlib import Path

import numpy as np
import pandas as pd

from exp08_gain_sweep import direct_share
from flynull import data as fw
from flynull import nulls
from flynull import rate_operator as op
from flynull.routing import boundary_masks, make_surrogate, sensory_channels
from flynull.stmap import load_map, score

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
PLAN = {"interior_degree_preserving": 50, "interior_block_preserving": 50, "degree_preserving": 19}
GAIN, STEPS, SWAPS = 1.0, 60, 10


def schedule():
    jobs = []
    for r in range(1, 51):
        jobs += [(g, r) for g, n in PLAN.items() if r <= n]
    return jobs


def run(job):
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # block sleep while running
    i, k = map(int, job.split("/"))
    c = fw.load()
    meta = c.meta
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    dn_type, rk = load_map(c.ids[readout].astype("int64"))
    sign = meta["nt_sign"].to_numpy()
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, channels, readout)
    cal = np.concatenate(list(channels.values()))
    csv = OUT / f"exp08b_j{i}.csv"
    rows = pd.read_csv(csv).to_dict("records") if csv.exists() else []
    seen = {(x["network"], int(x["replicate"])) for x in rows}

    for j, (gen, r) in enumerate(schedule()):
        if j % k != i or (gen, r) in seen:
            continue
        t = time.time()
        S = make_surrogate(gen, c.W, np.random.default_rng(1000 + r - 1), sign, labels, SWAPS, boundary)
        ch = nulls.check_preserved(c.W, S)
        ok = bool(ch["n_edges_equal"] and ch["weight_multiset_equal"])
        bok = None
        if gen in nulls.INTERIOR_GENERATORS:
            ok = ok and bool(ch["out_degree_equal"] and ch["in_degree_equal"])
            bok = nulls.check_boundary(c.W, S, *boundary)["boundary_identical"]  # raises if moved
            if not ok:
                raise AssertionError(f"{gen} r{r}: invariant broken {ch}")
        Wn, _ = op.normalise(S)
        x = op.run(Wn, cal, steps=STEPS, gain=GAIN)[-1]
        prof = {n: op.routing_profile(Wn, v, readout, steps=STEPS, gain=GAIN) for n, v in channels.items()}
        sep = op.channel_separation(prof)
        rows.append({"network": gen, "replicate": r, "spread": sep["mean_specificity"], "separation": sep["separation"],
                     "active_fraction": float(np.mean(np.abs(x) > 1e-3)),
                     "direct_share": float(np.mean([direct_share(Wn, channels[n], readout, prof[n]) for n in channels])),
                     "rho_own": float(score(prof, dn_type, rk).rho_own.mean()), "invariants_ok": ok, "boundary_ok": bok,
                     "seconds": round(time.time() - t)})
        pd.DataFrame(rows).to_csv(csv, index=False)
        print(f"{gen[:18]:18s} r{r}  spread={rows[-1]['spread']:.3f}  ({rows[-1]['seconds']}s)", flush=True)


def summary():
    d = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(OUT / "exp08b_j*.csv")))]).drop_duplicates(["network", "replicate"])
    d.to_csv(OUT / "exp08b_all_brains.csv", index=False)
    real = float(pd.read_csv(OUT / "exp08_stage1_real.csv").set_index("gain").loc[1.0, "spread"])
    rows = []
    for g in PLAN:
        x = d.loc[d.network == g, "spread"]
        k = int((x <= real).sum())
        rows.append({"network": g, "N": len(x), "real": real, "mean": x.mean(), "sd": x.std(ddof=1), "min": x.min(),
                     "max": x.max(), "k_le_real": k, "p": (1 + k) / (len(x) + 1)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "exp08b_summary.csv", index=False)
    print(t.round(4).to_string(index=False))
    inside = t[t.network.str.startswith("interior")]
    print("\nRule:", "YES" if (inside.p < 0.05).all() and (inside.N == 50).all() else "NO" if (inside.N == 50).all() else "incomplete")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["run", "summary"])
    ap.add_argument("--job", default="0/1")
    a = ap.parse_args()
    run(a.job) if a.stage == "run" else summary()
