"""Experiment 2: which published method's conclusion depends on exact wiring?

Every method is applied to the same connectome and the same surrogate ladder.
A method whose score is unchanged by rewiring is a method that would report the
same thing about a scrambled brain.

  python exp02_method_zoo.py --n-nulls 3 --generators weight_shuffle degree_preserving
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

import data as fw
import measures
import nulls
import rate_operator as op

OUT = Path(__file__).resolve().parent.parent / "results"


def evaluate(W, channels, readout, label, rng_seed=0, steps=40):
    rng = np.random.default_rng(rng_seed)
    row = {"network": label}

    # 1. Reservoir benchmark (calibration-free)
    t0 = time.time()
    Wn, rho = op.normalise(W, target_rho=0.95)
    row.update(measures.memory_capacity(Wn, rng))
    row["spectral_radius_raw"] = rho
    row["t_mc"] = round(time.time() - t0, 1)

    # 2. Linear influence routing (Pospisil-style), no dynamics, no calibration
    t0 = time.time()
    profiles, infos = {}, []
    for name, idx in channels.items():
        p, info = measures.linear_influence(W, idx, readout)
        profiles[name] = p
        infos.append(info)
    lin = op.channel_separation(profiles)
    row["lin_separation"] = lin["separation"]
    row["lin_specificity"] = lin["mean_specificity"]
    row["lin_converged"] = int(sum(1 for i in infos if i == 0))
    row["t_lin"] = round(time.time() - t0, 1)

    # 3. Nonlinear simulated routing at a matched operating point (our Experiment 1)
    t0 = time.time()
    cal_idx = np.concatenate(list(channels.values()))
    gain, _ = op.calibrate_gain(Wn, cal_idx, target_active=0.05, steps=steps)
    sim = {n_: op.routing_profile(Wn, i_, readout, steps=steps, gain=gain)
           for n_, i_ in channels.items()}
    sim_sep = op.channel_separation(sim)
    row["sim_separation"] = sim_sep["separation"]
    row["sim_specificity"] = sim_sep["mean_specificity"]
    row["t_sim"] = round(time.time() - t0, 1)

    # 4. Structural statistics
    row.update(measures.structural_stats(W))
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-nulls", type=int, default=3)
    ap.add_argument("--swaps-per-edge", type=int, default=10)
    ap.add_argument("--generators", nargs="*",
                    default=["weight_shuffle", "degree_preserving", "erdos_renyi"])
    ap.add_argument("--tag", default="")
    args = ap.parse_args()

    c = fw.load()
    print(c.summary(), flush=True)
    meta = c.meta
    channels = {}
    for name, grp in meta[meta["super_class"].isin(["sensory", "visual_projection"])].groupby("class"):
        if len(grp) >= 50:
            channels[str(name)] = grp.index.to_numpy()
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    sign = meta["nt_sign"].to_numpy()
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()

    OUT.mkdir(parents=True, exist_ok=True)
    csv = OUT / f"exp02_method_zoo{args.tag}.csv"
    rows = []

    t0 = time.time()
    rows.append(evaluate(c.W, channels, readout, "real"))
    pd.DataFrame(rows).to_csv(csv, index=False)
    r = rows[0]
    print(f"real   MC={r['memory_capacity']:.2f}  lin_spec={r['lin_specificity']:.1f}  "
          f"sim_spec={r['sim_specificity']:.1f}  ({time.time()-t0:.0f}s)", flush=True)

    for gen in args.generators:
        fn = nulls.GENERATORS[gen]
        for k in range(args.n_nulls):
            t1 = time.time()
            rng = np.random.default_rng(2000 + k)
            kw = {"sign": sign}
            if gen in ("degree_preserving", "block_preserving"):
                kw["swaps_per_edge"] = args.swaps_per_edge
            if gen == "block_preserving":
                kw["labels"] = labels
            S = fn(c.W, rng, **kw)
            row = evaluate(S, channels, readout, gen, rng_seed=k)
            row["replicate"] = k
            rows.append(row)
            pd.DataFrame(rows).to_csv(csv, index=False)
            print(f"{gen[:18]:18s} r{k+1}/{args.n_nulls}  MC={row['memory_capacity']:.2f}  "
                  f"lin_spec={row['lin_specificity']:.1f}  sim_spec={row['sim_specificity']:.1f}  "
                  f"({time.time()-t1:.0f}s)", flush=True)

    df = pd.DataFrame(rows)
    print("\n=== does the method's answer depend on exact wiring? ===")
    real = df[df.network == "real"].iloc[0]
    cols = [("memory_capacity", "Jaeger memory capacity (reservoir papers)"),
            ("lin_specificity", "linear influence focus (effectome)"),
            ("sim_specificity", "simulated routing focus (ours)"),
            ("reciprocity", "reciprocity (network statistics)")]
    for gen in args.generators:
        sub = df[df.network == gen]
        if sub.empty:
            continue
        print(f"\n  vs {gen} (n={len(sub)}):")
        for col, label in cols:
            mu = sub[col].mean()
            change = (mu - real[col]) / abs(real[col]) if real[col] else float("nan")
            verdict = "UNCHANGED -> wiring-blind" if abs(change) < 0.10 else "shifts -> wiring-sensitive"
            print(f"    {label:48s} real={real[col]:9.3f}  null={mu:9.3f}  {change:+7.1%}  {verdict}")


if __name__ == "__main__":
    main()
