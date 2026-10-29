"""SMOKE TEST for Step 1 (inside-only / boundary-preserving nulls). Not a result.

One replicate each of interior_degree_preserving and interior_block_preserving at
reduced mixing (default 2 swaps/edge), plus the real network, through exactly the
Exp01 surrogate + evaluate code path. Also runs path statistics (direct sense->DN
share, BFS hop distance to DNs) on real vs the smoke interior nulls vs a standard
degree_preserving null at the same mixing.

Outputs:
  results/exp01_smoke_C.csv          Exp01 metrics + invariants + timing
  results/exp01_smoke_paths_C.csv    per-sense path statistics per network

Usage:
  python smoke_interior_C.py [--swaps-per-edge 2] [--time-full 10]
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from flynull import data as fw
from flynull import nulls
from flynull import path_stats as ps
from flynull.routing import boundary_masks, evaluate, make_surrogate, sensory_channels

OUT = Path(__file__).resolve().parent.parent / "results"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--swaps-per-edge", type=int, default=2)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--time-full", type=int, default=10,
                    help="also time surrogate generation alone at this many swaps/edge (0 = skip)")
    args = ap.parse_args()

    c = fw.load()
    print(c.summary())
    meta = c.meta
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    sign = meta["nt_sign"].to_numpy()
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, channels, readout)

    src, dst = c.W.tocoo().row, c.W.tocoo().col
    from_sens = boundary[0][src]
    to_dn = boundary[1][dst]
    is_b = from_sens | to_dn
    print(f"\nsensory classes: {', '.join(f'{k}={len(v)}' for k, v in channels.items())}")
    print(f"sensory neurons (boundary sources): {int(boundary[0].sum()):,}")
    print(f"DNs (boundary targets):             {int(boundary[1].sum()):,}")
    print(f"boundary edges: {int(is_b.sum()):,}  (sensory-out {int(from_sens.sum()):,}, "
          f"DN-in {int(to_dn.sum()):,}, both {int((from_sens & to_dn).sum()):,})")
    print(f"interior edges: {int((~is_b).sum()):,} of {c.W.nnz:,}\n", flush=True)

    rows, path_rows = [], []
    t = time.time()
    r, _ = evaluate(c.W, channels, readout, "real", steps=args.steps)
    r.update(swaps_per_edge=np.nan, smoke=True, t_generate_s=0.0, t_evaluate_s=time.time() - t)
    rows.append(r)
    for pr in ps.sense_to_dn_stats(c.W, channels, readout):
        path_rows.append({"network": "real", **pr})
    print(f"real  sep={r['separation']:.4f}  spec={r['mean_specificity']:.1f}  "
          f"({r['t_evaluate_s']:.0f}s)", flush=True)

    for gen in ("interior_degree_preserving", "interior_block_preserving", "degree_preserving"):
        rng = np.random.default_rng(1000)
        t = time.time()
        S = make_surrogate(gen, c.W, rng, sign, labels, args.swaps_per_edge, boundary)
        t_gen = time.time() - t
        chk = nulls.check_preserved(c.W, S)
        dale = bool(np.all(np.sign(S.data) == sign[S.tocoo().row]))
        row = {"network": gen, "swaps_per_edge": args.swaps_per_edge, "smoke": True,
               "t_generate_s": t_gen, **chk, "dale_ok": dale}
        if gen in nulls.INTERIOR_GENERATORS:
            row.update(nulls.check_boundary(c.W, S, *boundary))   # raises on failure
            ok = all(chk[k] for k in ("n_edges_equal", "out_degree_equal",
                                      "in_degree_equal", "weight_multiset_equal")) and dale
            if not ok:
                raise AssertionError(f"{gen}: invariant broken {chk} dale={dale}")
            t = time.time()
            ev, _ = evaluate(S, channels, readout, gen, steps=args.steps)
            row.update({k: v for k, v in ev.items() if k != "network"})
            row["t_evaluate_s"] = time.time() - t
            print(f"{gen}  sep={row['separation']:.4f}  spec={row['mean_specificity']:.1f}  "
                  f"dim={row['dimensionality']:.1f}  act={row['active_fraction']:.4f}  "
                  f"overlap={chk['edge_overlap']:.3f}  gen={t_gen:.0f}s  eval={row['t_evaluate_s']:.0f}s",
                  flush=True)
        else:
            print(f"{gen} (path stats only)  overlap={chk['edge_overlap']:.3f}  gen={t_gen:.0f}s",
                  flush=True)
        rows.append(row)
        for pr in ps.sense_to_dn_stats(S, channels, readout):
            path_rows.append({"network": f"{gen}_smoke{args.swaps_per_edge}", **pr})
        pd.DataFrame(rows).to_csv(OUT / "exp01_smoke_C.csv", index=False)

    if args.time_full:
        for gen in nulls.INTERIOR_GENERATORS:
            t = time.time()
            S = make_surrogate(gen, c.W, np.random.default_rng(2000), sign, labels,
                               args.time_full, boundary)
            t_gen = time.time() - t
            b = nulls.check_boundary(c.W, S, *boundary)
            ov = nulls.check_preserved(c.W, S)["edge_overlap"]
            rows.append({"network": f"{gen}_timing_only", "swaps_per_edge": args.time_full,
                         "smoke": True, "t_generate_s": t_gen, "edge_overlap": ov,
                         "boundary_identical": b["boundary_identical"]})
            print(f"{gen} @ {args.time_full} swaps/edge: generate {t_gen:.0f}s  overlap={ov:.3f}",
                  flush=True)

    pd.DataFrame(rows).to_csv(OUT / "exp01_smoke_C.csv", index=False)
    P = pd.DataFrame(path_rows)
    P.to_csv(OUT / "exp01_smoke_paths_C.csv", index=False)
    pd.set_option("display.width", 200)
    print("\n=== path stats: direct share sense->DN ===")
    print(P.pivot(index="sense", columns="network", values="direct_share").to_string())
    print("\n=== mean hops sense->DN ===")
    print(P.pivot(index="sense", columns="network", values="mean_hops").to_string())
    print("\n=== DNs at 1 hop ===")
    print(P.pivot(index="sense", columns="network", values="hop1").to_string())


if __name__ == "__main__":
    main()
