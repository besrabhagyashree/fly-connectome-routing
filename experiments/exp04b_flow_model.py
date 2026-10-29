"""Step 4b: re-run the information-flow model behind Stuerner's DN map.

Stuerner et al. 2025 averaged, by DN type, the FlyWire flow ranks of Dorkenwald
et al. 2024, which used navis 1.5.0 TraversalModel (Schlegel et al. 2021):
edges with >4 synapses, weight w = synapses / total input of the target,
traversal probability p = clip(w / 0.3, 0, 1), seeds at layer 1, max_steps 15,
10,000 runs per modality, per-neuron layer = mean over runs that reach it.
Settings and sources: results/exp04b_flow_settings.md.

Exact fast form. In navis an edge u->v is tested once per step from the step
after u is traversed until it succeeds (failed edges are retried), so it fires
after a Geometric(p) number of steps. Hence, per run,
    layer(v) = min over in-edges (layer(u) + G_uv),   G_uv ~ Geometric(p_uv),
i.e. a multi-source shortest path with random integer edge lengths, kept only if
layer <= max_steps. One run = one geometric draw per edge + one Dijkstra.
`navis_literal` below is navis 1.5.0's loop transcribed, used by --selftest to
check that both give the same layer distribution.

  python exp04b_flow_model.py --selftest
  python exp04b_flow_model.py repro --runs 10000 --tag _real
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from flynull.flow import (compare, flow_map, load_types, seed_sets, selftest, sim_vs_map,
                           type_ranks)
from flynull.stmap import MAIN_MODALITIES

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", nargs="?", default="repro", choices=["repro", "nulls"])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--runs", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--generators", nargs="*", default=["interior_degree_preserving"])
    ap.add_argument("--replicates", nargs=2, type=int, default=[1, 35], metavar=("FIRST", "LAST"))
    ap.add_argument("--swaps-per-edge", type=int, default=10)
    ap.add_argument("--tag", default="")
    args = ap.parse_args()
    if args.selftest:
        selftest()
        return

    from flynull import data as fw
    c = fw.load()
    meta = c.meta
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    dn_type, rk = load_types(c.ids[readout].astype("int64"))
    seeds = seed_sets(meta)
    print(f"edges={c.A.nnz:,}  seeds={ {m: len(s) for m, s in seeds.items()} }", flush=True)

    if args.mode == "repro":
        layers = flow_map(c.A, seeds, readout, args.runs, args.seed)
        pd.DataFrame(layers).assign(root_id=c.ids[readout].astype("int64"), type=dn_type).to_csv(
            OUT / f"exp04b_dn_layers{args.tag}.csv", index=False)
        res = compare(type_ranks(layers, dn_type, rk), rk)
        res.to_csv(OUT / f"exp04b_repro{args.tag}.csv", index=False)
        print(res.round(3).to_string(index=False))
        print(f"pass (rho >= 0.90 every modality): {bool((res.spearman >= 0.90).all())}")
        return

    # nulls: recompute the map on each Exp04a surrogate (same generator, seed 1000+k).
    # Reference = our real-brain map at the same run count, so noise is matched.
    from flynull import nulls
    from flynull.routing import boundary_masks, make_surrogate, sensory_channels
    sign = meta["nt_sign"].to_numpy()
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, sensory_channels(meta), readout)
    prof_dir = OUT / "exp04_profiles"
    lay_dir = OUT / "exp04b_layers"
    lay_dir.mkdir(exist_ok=True)
    out = OUT / f"exp04b_nulls{args.tag}.csv"

    ref_file = lay_dir / f"real_0_r{args.runs}.npz"
    if ref_file.exists():
        real_layers = dict(np.load(ref_file))
    else:
        real_layers = flow_map(c.A, seeds, readout, args.runs, args.seed)
        np.savez_compressed(ref_file, **real_layers)
    real_map = type_ranks(real_layers, dn_type, rk)
    real_prof = dict(np.load(prof_dir / "real_0.npz"))
    r_rho, r_diag = sim_vs_map(real_prof, dn_type, real_map)
    print(f"real: sim vs own map rho={r_rho:.3f} diagonal {r_diag}", flush=True)

    rows = []
    for gen in args.generators:
        for k in range(args.replicates[0], args.replicates[1] + 1):
            t = time.time()
            S = make_surrogate(gen, c.W, np.random.default_rng(1000 + k - 1), sign, labels,
                               args.swaps_per_edge, boundary)
            if gen in nulls.INTERIOR_GENERATORS:
                nulls.check_boundary(c.W, S, *boundary)
            S = abs(S).tocsr()
            layers = flow_map(S, seeds, readout, args.runs, args.seed + k, log=False)
            np.savez_compressed(lay_dir / f"{gen}_{k}_r{args.runs}.npz", **layers)
            mp = type_ranks(layers, dn_type, rk)
            stab = {f"map_rho_{m}": spearmanr(mp[m], real_map[m], nan_policy="omit").statistic
                    for m in MAIN_MODALITIES}
            own_rho, own_diag = sim_vs_map(dict(np.load(prof_dir / f"{gen}_{k}.npz")), dn_type, mp)
            rows.append({"network": gen, "replicate": k, "sim_vs_own_map": own_rho,
                         "own_diagonal": own_diag, "map_vs_real_map": np.mean(list(stab.values())),
                         **stab, "real_sim_vs_own_map": r_rho})
            pd.DataFrame(rows).to_csv(out, index=False)
            print(f"{gen[:18]:18s} r{k}  map vs real map rho={rows[-1]['map_vs_real_map']:.3f}  "
                  f"sim vs own map rho={own_rho:.3f}  ({time.time()-t:.0f}s)", flush=True)


if __name__ == "__main__":
    main()
