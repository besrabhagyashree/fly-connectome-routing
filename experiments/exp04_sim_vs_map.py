"""Step 4a: does the simulated routing agree with Stuerner's structural map, and
does that agreement survive randomisation?

Stuerner et al. 2025 rank every descending-neuron (DN) type by how many layers it
sits from each sensory modality (information-flow model of Schlegel et al. 2021,
DN_ranking_df_783_sensory_combined_byDNtype.tsv; lower = closer). Our rate model
gives, per driven sense, the steady |activity| of all 1,305 DNs (Exp01's
routing_profile). For each sense we average |activity| over the DNs of each
Stuerner type and compute Spearman's rho against -rank for every modality.

  agreement   rho(sense, its own modality)            -- does the simulation put
                                                         the signal where the map
                                                         says that sense is close?
  diagonal    own modality has the highest rho of the 8  -- is the agreement
                                                           specific to that sense?

The real brain is compared with the same surrogates Exp01 used (same generators,
same seeds 1000+k), so inside-only brains here are the C1 brains. The map itself
is always the published real-brain map; step 4b recomputes the map on surrogates.
Empirical p = (1 + surrogates >= real) / (N + 1), as in Exp01.

  python exp04_sim_vs_map.py --generators interior_degree_preserving --n-nulls 35 --tag _C1
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from flynull import data as fw
from flynull import nulls
from flynull.routing import boundary_masks, evaluate, make_surrogate, sensory_channels
from flynull.stmap import load_map, score

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
PROF = OUT / "exp04_profiles"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-nulls", type=int, default=35)
    ap.add_argument("--swaps-per-edge", type=int, default=10)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--generators", nargs="*", default=["interior_degree_preserving"],
                    choices=list(nulls.GENERATORS) + list(nulls.INTERIOR_GENERATORS))
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    PROF.mkdir(parents=True, exist_ok=True)
    c = fw.load()
    meta = c.meta
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    dn_type, rk = load_map(c.ids[readout].astype("int64"))
    print(f"DNs typed: {pd.notna(dn_type).mean():.1%}; types in map: {rk.shape[0]}", flush=True)
    sign = meta["nt_sign"].to_numpy()
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, channels, readout)
    out = OUT / f"exp04_sim_vs_map{args.tag}.csv"

    frames = []

    def record(profiles, net, k):
        np.savez_compressed(PROF / f"{net}_{k}.npz", **profiles)
        s = score(profiles, dn_type, rk).assign(network=net, replicate=k)
        frames.append(s)
        pd.concat(frames).to_csv(out, index=False)
        print(f"{net[:18]:18s} r{k}  mean rho_own={s.rho_own.mean():.3f}  "
              f"diagonal {int(s.diagonal.sum())}/{len(s)}", flush=True)

    t0 = time.time()
    _, prof = evaluate(c.W, channels, readout, "real", steps=args.steps)
    record(prof, "real", 0)
    print(score(prof, dn_type, rk).round(3).to_string(), flush=True)
    print(f"({time.time()-t0:.0f}s)", flush=True)

    for gen in args.generators:
        for k in range(args.n_nulls):
            t1 = time.time()
            S = make_surrogate(gen, c.W, np.random.default_rng(1000 + k), sign, labels,
                               args.swaps_per_edge, boundary)
            if gen in nulls.INTERIOR_GENERATORS:
                nulls.check_boundary(c.W, S, *boundary)  # raises if a boundary edge moved
            _, prof = evaluate(S, channels, readout, gen, steps=args.steps)
            record(prof, gen, k + 1)
            print(f"   ({time.time()-t1:.0f}s)", flush=True)

    df = pd.concat(frames)
    per = df.groupby(["network", "replicate"]).agg(rho=("rho_own", "mean"), diag=("diagonal", "sum"))
    real = per.loc[("real", 0)]
    print("\n=== agreement with Stuerner's map (mean rho_own over senses) ===")
    print(f"real: rho={real.rho:.3f}  diagonal={int(real.diag)}")
    for gen in args.generators:
        sub = per.loc[gen]
        p = (int((sub.rho >= real.rho).sum()) + 1) / (len(sub) + 1)
        print(f"{gen:28s} n={len(sub)}  rho={sub.rho.mean():.3f} ± {sub.rho.std(ddof=1):.3f}  "
              f"diag={sub['diag'].mean():.1f}  p(null >= real)={p:.4f}")


if __name__ == "__main__":
    main()
