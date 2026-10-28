"""Step 5: scale steps 1 and 4a from 35 to 200 randomised brains per type.

The gate (real more focused than the inside-only shuffles at p < 0.05 for both
types) said yes, so the same experiments are extended, unchanged: same generators,
same seeds (replicate r uses default_rng(1000 + r - 1), as in Exp01/Exp04, so
replicates 1-35 are the brains already run), 10 swaps per edge, same rate model.

Each surrogate is built once and scored for both steps:
  step 1   Exp01's row (spread = mean_specificity, separation, gross signatures,
           invariant and boundary checks)            -> results/exp05_exp01{tag}.csv
  step 4a  Exp04's agreement with Stuerner's map     -> results/exp05_exp04{tag}.csv
Profiles are saved to results/exp04_profiles/<generator>_<r>.npz (reused by step 7).

  python exp05_scale.py --spec interior_degree_preserving:36-159 --tag _j1
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

import data as fw
import nulls
from exp01_routing_vs_gross import boundary_masks, evaluate, make_surrogate, sensory_channels
from exp04_sim_vs_map import load_map, score

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
PROF = OUT / "exp04_profiles"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", nargs="+", required=True, metavar="GENERATOR:FIRST-LAST",
                    help="one or more generator:replicate-range pieces, e.g. degree_preserving:36-118")
    ap.add_argument("--swaps-per-edge", type=int, default=10)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--tag", required=True)
    args = ap.parse_args()
    pieces = []
    for s in args.spec:
        gen, rng_ = s.split(":")
        first, last = map(int, rng_.split("-"))
        if gen not in nulls.GENERATORS and gen not in nulls.INTERIOR_GENERATORS:
            raise SystemExit(f"unknown generator {gen}")
        pieces.append((gen, first, last))

    c = fw.load()
    meta = c.meta
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    dn_type, rk = load_map(c.ids[readout].astype("int64"))
    sign = meta["nt_sign"].to_numpy()
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, channels, readout)
    out1, out4 = OUT / f"exp05_exp01{args.tag}.csv", OUT / f"exp05_exp04{args.tag}.csv"
    rows1, rows4 = [], []

    for gen, first, last in pieces:
        for r in range(first, last + 1):
            t = time.time()
            S = make_surrogate(gen, c.W, np.random.default_rng(1000 + r - 1), sign, labels,
                               args.swaps_per_edge, boundary)
            checks = nulls.check_preserved(c.W, S)
            ok = checks["n_edges_equal"] and checks["weight_multiset_equal"]
            bok = None
            if gen in nulls.INTERIOR_GENERATORS:
                ok = ok and checks["out_degree_equal"] and checks["in_degree_equal"]
                bok = nulls.check_boundary(c.W, S, *boundary)["boundary_identical"]  # raises if moved
                if not ok:
                    raise AssertionError(f"{gen} r{r}: invariant broken {checks}")
            row, prof = evaluate(S, channels, readout, gen, steps=args.steps)
            rows1.append({**row, "replicate": r, "edge_overlap": checks["edge_overlap"],
                          "invariants_ok": ok, "boundary_ok": bok})
            np.savez_compressed(PROF / f"{gen}_{r}.npz", **prof)
            s = score(prof, dn_type, rk).assign(network=gen, replicate=r)
            rows4.append(s)
            pd.DataFrame(rows1).to_csv(out1, index=False)
            pd.concat(rows4).to_csv(out4, index=False)
            print(f"{gen[:18]:18s} r{r}  spread={row['mean_specificity']:.3f}  "
                  f"rho_own={s.rho_own.mean():.3f}  ({time.time()-t:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
