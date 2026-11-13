"""Step 9: Pong played by the frozen connectome, following results/exp09_pong_plan.md.

  python experiments/exp09_pong.py --worker 1     # any number of workers; each claims the next brain
  python experiments/exp09_pong.py --summary
"""
from __future__ import annotations

import argparse
import ctypes
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import binomtest

from flynull import data as fw
from flynull import nulls
from flynull import pong
from flynull import rate_operator as op
from flynull.routing import boundary_masks, make_surrogate, sensory_channels

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
HITS = OUT / "exp09_hits"
CLAIMS = OUT / "exp09_claims"
SWAPS = 10
TARGET, LO, HI, HALVINGS = 0.05, 1e-3, 50.0, 14
INSIDE = ("interior_degree_preserving", "interior_block_preserving")


def schedule():
    jobs = [("real", 0), ("no_wiring", 0)]
    for r in range(1, 51):
        jobs += [(g, r) for g in INSIDE]
        if r <= 20:
            jobs.append(("degree_preserving", r))
    return jobs


def claim(name):
    CLAIMS.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(CLAIMS / name, os.O_CREAT | os.O_EXCL))
        return True
    except FileExistsError:
        return False


def mean_active(res, screen):
    """Active fraction averaged over every frame of 5 teacher-played balls (seed 99)."""
    acts = []

    def step(d):
        f = res.step(d)
        acts.append(res.active_fraction())
        return f
    pong.play(step, lambda f, b, px: pong.teacher(b, px), np.random.default_rng(99), 5, screen, reset=res.reset)
    return float(np.mean(acts))


def calibrate(WT, inp, out, screen):
    def act(g):
        return mean_active(pong.Reservoir(WT, inp, out, g), screen)
    a_lo, a_hi = act(LO), act(HI)
    if a_lo > TARGET:
        return LO, a_lo, "above_target_at_lower_limit"
    if a_hi < TARGET:
        return HI, a_hi, "below_target_at_upper_limit"
    lo, hi = LO, HI
    for _ in range(HALVINGS):
        mid = float(np.sqrt(lo * hi))
        lo, hi = (mid, hi) if act(mid) < TARGET else (lo, mid)
    g = float(np.sqrt(lo * hi))
    return g, act(g), ""


def play_brain(res, screen):
    """Train the readout on 200 teacher-driven balls (30% random actions), test on 300."""
    _, F, y, grp = pong.play(res.step, lambda f, b, px: pong.teacher(b, px), np.random.default_rng(11), 200,
                             screen, eps=0.3, record=True, reset=res.reset)
    m = pong.fit_ridge(F, y, grp)
    hits = pong.play(res.step, pong.readout_policy(m), np.random.default_rng(22), 300, screen, reset=res.reset)
    return hits, m


def run(worker):
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # block sleep while running
    c = fw.load()
    meta, sign = c.meta, c.meta["nt_sign"].to_numpy()
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, channels, readout)
    inp, screen = pong.eye_inputs(meta)
    HITS.mkdir(parents=True, exist_ok=True)
    csv = OUT / f"exp09_pong_w{worker}.csv"
    rows = pd.read_csv(csv).to_dict("records") if csv.exists() else []
    print(f"{c.W.nnz:,} edges; {len(inp)} eye cells; {len(readout)} DNs", flush=True)
    for gen, r in schedule():
        name = f"{gen}_{r}"
        if not claim(name):
            continue
        t = time.time()
        ok = bok = None
        flag, rho = "", float("nan")
        if gen == "no_wiring":
            res = pong.Reservoir(None, inp, inp, 0.0)
            gain, active = 0.0, float("nan")
        else:
            if gen == "real":
                W = c.W
            else:
                W = make_surrogate(gen, c.W, np.random.default_rng(1000 + r - 1), sign, labels, SWAPS, boundary)
                checks = nulls.check_preserved(c.W, W)
                ok = bool(checks["n_edges_equal"] and checks["weight_multiset_equal"]
                          and checks["out_degree_equal"] and checks["in_degree_equal"])
                if gen in INSIDE:
                    bok = nulls.check_boundary(c.W, W, *boundary)["boundary_identical"]  # raises if moved
            Wn, rho = op.normalise(W)
            WT = Wn.T.astype(np.float32).tocsr()
            del Wn
            gain, active, flag = calibrate(WT, inp, readout, screen)
            res = pong.Reservoir(WT, inp, readout, gain)
        hits, m = play_brain(res, screen)
        np.save(HITS / f"{name}.npy", hits)
        rows.append({"network": gen, "replicate": r, "hit_rate": float(hits.mean()), "hits": int(hits.sum()),
                     "gain": gain, "active": active, "calibration_flag": flag, "spectral_radius_raw": rho,
                     "alpha": m["alpha"], "cv_mse": m["cv_mse"], "n_features": m["n_features"],
                     "invariants_ok": ok, "boundary_ok": bok, "seconds": round(time.time() - t)})
        pd.DataFrame(rows).to_csv(csv, index=False)
        print(f"{time.strftime('%H:%M')} {name:32s} hit={hits.mean():.3f} gain={gain:.4g} "
              f"active={active:.3f} {flag} ({round(time.time() - t)}s)", flush=True)


def load_all():
    fs = sorted(OUT.glob("exp09_pong_w*.csv"))
    return pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates(["network", "replicate"]) if fs else None


def summary():
    d = load_all()
    real = d[d.network == "real"].iloc[0]
    print(d.groupby("network").agg(N=("hit_rate", "size"), mean=("hit_rate", "mean"), sd=("hit_rate", "std"),
                                   flagged=("calibration_flag", lambda s: int(s.fillna("").ne("").sum()))).to_string())
    if real.calibration_flag == real.calibration_flag and real.calibration_flag:
        print(f"\nGATE FAILED: real brain {real.calibration_flag}. Stop and replan.")
        return
    if (HITS / "no_wiring_0.npy").exists():
        a, b = np.load(HITS / "real_0.npy"), np.load(HITS / "no_wiring_0.npy")
        n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
        p = binomtest(n10, n10 + n01, 0.5, alternative="greater").pvalue if n10 + n01 else 1.0
        print(f"\nQ1 real {a.mean():.3f} vs no wiring {b.mean():.3f}; real-only {n10}, no-wiring-only {n01}; "
              f"McNemar one-sided p = {p:.4g} -> {'YES' if p < 0.05 else 'NO'}")
    ps = {}
    for g in INSIDE:
        x = d[d.network == g].hit_rate
        k = int((x >= real.hit_rate).sum())
        ps[g] = (1 + k) / (len(x) + 1)
        print(f"Q2 {g}: N={len(x)} mean {x.mean():.3f}; k={k}; p = {ps[g]:.4f}")
    done = all((d.network == g).sum() == 50 for g in INSIDE)
    print("Q2:", ("YES" if all(p < 0.05 for p in ps.values()) else "NO") if done else "incomplete")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    summary() if a.summary else run(a.worker)
