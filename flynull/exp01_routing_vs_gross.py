"""Experiment 1: does exact wiring matter for gross dynamics, or only for routing?

Hypothesis (extending the larval result, arXiv:2606.17745, to the adult brain):
  H1  gross dynamical measures survive degree- and weight-matched rewiring
  H2  sensory-channel separation at the descending neurons does NOT survive it

If both hold, every frozen-reservoir demo (chess, Tetris) is measuring something a
rewired graph would give equally well, while the sensory-to-motor routing that any
embodied model depends on is destroyed. One experiment, two conclusions.

Usage:
  python exp01_routing_vs_gross.py --n-nulls 3 --scale 1.0
  # boundary-preserving (inside-only) nulls, Step 1; write *_C files:
  python exp01_routing_vs_gross.py --generators interior_degree_preserving       interior_block_preserving --n-nulls 35 --swaps-per-edge 10 --tag _C
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import data as fw
import nulls
import rate_operator as op

OUT = Path(__file__).resolve().parent.parent / "results"


def sensory_channels(meta: pd.DataFrame, min_size: int = 50) -> dict[str, np.ndarray]:
    """Sensory populations, grouped by modality as annotated in FlyWire."""
    sens = meta[meta["super_class"].isin(["sensory", "visual_projection"])]
    out = {}
    for name, grp in sens.groupby("class", dropna=True):
        if len(grp) >= min_size:
            out[str(name)] = grp.index.to_numpy()
    return out


def boundary_masks(n, channels, readout):
    """Sensory-motor boundary for the interior-only nulls: the sensory neurons are
    exactly the union of the Exp01 channels; the DNs are exactly the readout."""
    bsrc = np.zeros(n, dtype=bool)
    bsrc[np.concatenate(list(channels.values()))] = True
    bdst = np.zeros(n, dtype=bool)
    bdst[readout] = True
    return bsrc, bdst


def make_surrogate(gen, W, rng, sign, labels, swaps_per_edge, boundary=None):
    """Build one surrogate. Existing generators get exactly the kwargs they always
    got; interior_* additionally get the boundary masks."""
    fn = nulls.GENERATORS.get(gen) or nulls.INTERIOR_GENERATORS[gen]
    kw = {"sign": sign}
    if gen in ("degree_preserving", "block_preserving",
               "interior_degree_preserving", "interior_block_preserving"):
        kw["swaps_per_edge"] = swaps_per_edge
    if gen in ("block_preserving", "interior_block_preserving"):
        kw["labels"] = labels
    if gen in nulls.INTERIOR_GENERATORS:
        kw["boundary_src"], kw["boundary_dst"] = boundary
    return fn(W, rng, **kw)


def evaluate(W, channels, readout, label, steps=60, target_active=0.05):
    """Normalise spectral radius, THEN calibrate gain so every network is compared
    at the same operating point. Only then is a routing difference attributable to
    wiring rather than to excitability."""
    Wn, rho = op.normalise(W)
    cal_idx = np.concatenate(list(channels.values()))
    gain, achieved = op.calibrate_gain(Wn, cal_idx, target_active=target_active, steps=steps)

    gross_all, profiles = [], {}
    for name, idx in channels.items():
        gross_all.append(op.gross_signatures(Wn, idx, steps=steps, gain=gain))
        profiles[name] = op.routing_profile(Wn, idx, readout, steps=steps, gain=gain)

    gross = {k: float(np.mean([g[k] for g in gross_all])) for k in gross_all[0]}
    sep = op.channel_separation(profiles)
    return ({"network": label, "spectral_radius_raw": rho, "gain": gain,
             "calibrated_active": achieved, **gross, **sep}, profiles)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-nulls", type=int, default=3)
    ap.add_argument("--swaps-per-edge", type=int, default=5)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--generators", nargs="*",
                    default=["weight_shuffle", "degree_preserving", "erdos_renyi"],
                    choices=list(nulls.GENERATORS) + list(nulls.INTERIOR_GENERATORS))
    ap.add_argument("--tag", default="", help="suffix for output files, to run batches in parallel")
    args = ap.parse_args()

    OUT.mkdir(parents=True, exist_ok=True)
    c = fw.load()
    print(c.summary())

    meta = c.meta
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    print(f"\nchannels: {len(channels)} sensory classes "
          f"({', '.join(list(channels)[:6])}{'...' if len(channels) > 6 else ''})")
    print(f"readout: {len(readout)} descending neurons\n")

    sign = meta["nt_sign"].to_numpy()
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, channels, readout)
    if any(g in nulls.INTERIOR_GENERATORS for g in args.generators):
        print(f"boundary: {int(boundary[0].sum())} sensory sources, "
              f"{int(boundary[1].sum())} DN targets (frozen in interior_* nulls)")

    csv_path = OUT / f"exp01_routing_vs_gross{args.tag}.csv"

    def checkpoint(rows):
        """Write after every replicate: a run of hours must not lose its results."""
        pd.DataFrame(rows).to_csv(csv_path, index=False)

    rows = []
    t0 = time.time()
    real_row, real_profiles = evaluate(c.W, channels, readout, "real", steps=args.steps)
    rows.append(real_row)
    checkpoint(rows)
    print(f"real  separation={real_row['separation']:.4f}  "
          f"dim={real_row['dimensionality']:.1f}  ({time.time()-t0:.0f}s)", flush=True)

    for gen in args.generators:
        for k in range(args.n_nulls):
            t1 = time.time()
            rng = np.random.default_rng(1000 + k)
            S = make_surrogate(gen, c.W, rng, sign, labels, args.swaps_per_edge, boundary)

            checks = nulls.check_preserved(c.W, S)
            if gen in nulls.INTERIOR_GENERATORS:
                # Raises (aborting the run) if any boundary edge moved.
                bchk = nulls.check_boundary(c.W, S, *boundary)
            row, _ = evaluate(S, channels, readout, gen, steps=args.steps)
            row["replicate"] = k
            row["edge_overlap"] = checks["edge_overlap"]
            row["invariants_ok"] = all(
                checks[key] for key in ("n_edges_equal", "weight_multiset_equal")
            )
            if gen in nulls.INTERIOR_GENERATORS:
                row["invariants_ok"] = row["invariants_ok"] and all(
                    checks[key] for key in ("out_degree_equal", "in_degree_equal"))
                row["boundary_ok"] = bchk["boundary_identical"]
                if not row["invariants_ok"]:
                    raise AssertionError(f"{gen} r{k}: invariant broken {checks}")
            rows.append(row)
            checkpoint(rows)
            print(f"{gen[:18]:18s} r{k+1}/{args.n_nulls}  separation={row['separation']:.4f}  "
                  f"dim={row['dimensionality']:.1f}  overlap={row['edge_overlap']:.3f}  "
                  f"({time.time()-t1:.0f}s)", flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)

    print("\n=== summary (mean over replicates) ===")
    cols = ["separation", "mean_specificity", "dimensionality", "mean_abs_activity", "active_fraction"]
    print(df.groupby("network")[cols].mean().to_string())

    real = df[df.network == "real"].iloc[0]
    print("\n=== hypothesis test ===")
    print(f"{'surrogate':18s} {'n':>3s} {'separation':>20s} {'p':>8s} {'z':>7s} "
          f"{'specificity':>18s} {'gross shift':>11s}")
    stats_rows = []
    for gen in args.generators:
        sub = df[df.network == gen]
        if sub.empty:
            continue
        n = len(sub)
        sep_mu, sep_sd = sub["separation"].mean(), sub["separation"].std(ddof=1)
        # Empirical p: how often does a surrogate reach the real network's routing?
        # +1 correction keeps p > 0 with a finite number of replicates.
        p = (int((sub["separation"] >= real["separation"]).sum()) + 1) / (n + 1)
        z = (real["separation"] - sep_mu) / sep_sd if sep_sd > 0 else float("nan")
        spec_mu, spec_sd = sub["mean_specificity"].mean(), sub["mean_specificity"].std(ddof=1)
        d_dim = (real["dimensionality"] - sub["dimensionality"].mean()) / max(real["dimensionality"], 1e-9)
        print(f"{gen:18s} {n:3d} {sep_mu:8.4f} ± {sep_sd:.4f} {p:8.4f} {z:7.1f} "
              f"{spec_mu:8.1f} ± {spec_sd:5.1f} {d_dim:+10.2%}")
        stats_rows.append({"surrogate": gen, "n": n, "sep_mean": sep_mu, "sep_sd": sep_sd,
                           "sep_real": real["separation"], "p_empirical": p, "z": z,
                           "spec_mean": spec_mu, "spec_sd": spec_sd,
                           "spec_real": real["mean_specificity"],
                           "spec_ratio": spec_mu / max(real["mean_specificity"], 1e-9),
                           "gross_dim_shift": d_dim})
    pd.DataFrame(stats_rows).to_csv(OUT / f"exp01_stats{args.tag}.csv", index=False)
    print(f"\nreal separation = {real['separation']:.4f}, "
          f"real specificity = {real['mean_specificity']:.1f} descending neurons")
    print("p is the fraction of surrogates matching or beating the real wiring.")
    print("Routing claim holds if p is small AND the gross shift stays near zero.")

    json.dump({"channels": {k: len(v) for k, v in channels.items()},
               "n_readout": int(len(readout))},
              open(OUT / f"exp01_setup{args.tag}.json", "w"), indent=2)


if __name__ == "__main__":
    main()


