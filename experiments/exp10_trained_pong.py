"""Step 10: the connectome itself trained to play Pong, following
results/exp10_trained_pong_plan.md. Settings (learning rate, epochs, brains per
type) are read from results/exp10_config.json, written with the plan.

  python experiments/exp10_trained_pong.py --worker 1
  python experiments/exp10_trained_pong.py --summary
"""
from __future__ import annotations

import argparse
import ctypes
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.stats import binomtest

sys.path.insert(0, str(Path(__file__).parent))
from exp10_tune import setup, train  # noqa: E402

from flynull import nulls, pong  # noqa: E402
from flynull import pong_train as pt  # noqa: E402
from flynull import rate_operator as op  # noqa: E402
from flynull.routing import make_surrogate  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
HITS = OUT / "exp10_hits"
CLAIMS = OUT / "exp10_claims"
INSIDE = ("interior_degree_preserving", "interior_block_preserving")
CFG = json.loads((OUT / "exp10_config.json").read_text())


def schedule():
    jobs = [("real", 0), ("no_wiring", 0)]
    for r in range(1, CFG["n_per_type"] + 1):
        jobs += [(g, r) for g in INSIDE]
    return jobs


def claim(name):
    CLAIMS.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(CLAIMS / name, os.O_CREAT | os.O_EXCL))
        return True
    except FileExistsError:
        return False


def run(worker):
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    c, sign, labels, boundary, readout, types, inp, screen = setup()
    g9 = pd.read_csv(OUT / "exp09_pong_all.csv").set_index(["network", "replicate"]).gain
    balls = pt.record_balls(np.random.default_rng(11), 200, screen)
    HITS.mkdir(parents=True, exist_ok=True)
    csv, prog = OUT / f"exp10_run_w{worker}.csv", OUT / f"exp10_run_w{worker}.json"
    rows = pd.read_csv(csv).to_dict("records") if csv.exists() else []
    total, t_start = len(schedule()), int(time.time())

    def progress():
        done = len(list(HITS.glob("*.npy")))
        prog.write_text(json.dumps({"brains_done": done, "brains_total": total, "start": t_start,
                                    "now": int(time.time()),
                                    "pace": int(np.median([r["seconds"] for r in rows])) if rows else 3600}))
    progress()
    for gen, r in schedule():
        name = f"{gen}_{r}"
        if not claim(name):
            continue
        t = time.time()
        ok = bok = None
        if gen == "no_wiring":
            # Same model and training with the wiring removed; the readout reads the eye cells.
            m = pt.Trainable(sparse.csr_matrix((c.n, c.n), dtype=np.float32), inp, inp, 0.0, types,
                             int(types.max()) + 1)
            gain = 0.0
        else:
            if gen == "real":
                W = c.W
            else:
                W = make_surrogate(gen, c.W, np.random.default_rng(1000 + r - 1), sign, labels, 10, boundary)
                chk = nulls.check_preserved(c.W, W)
                ok = bool(chk["n_edges_equal"] and chk["weight_multiset_equal"]
                          and chk["out_degree_equal"] and chk["in_degree_equal"])
                bok = nulls.check_boundary(c.W, W, *boundary)["boundary_identical"]  # raises if moved
            Wn, _ = op.normalise(W)
            WT = Wn.T.astype(np.float32).tocsr()
            del Wn
            gain = float(g9.loc[(gen, r)])   # step 9 calibration of the same brain (5% active)
            m = pt.Trainable(WT, inp, readout, gain, types, int(types.max()) + 1)
        train(m, balls, CFG["lr"], CFG["epochs"])
        res = m.reservoir()
        hits = pong.play(res.step, m.policy(), np.random.default_rng(22), 300, screen, reset=res.reset)
        np.save(HITS / f"{name}.npy", hits)
        rows.append({"network": gen, "replicate": r, "hit_rate": float(hits.mean()), "hits": int(hits.sum()),
                     "gain": gain, "theta_sd": float(m.theta.std()), "theta_min": float(m.theta.min()),
                     "theta_max": float(m.theta.max()), "invariants_ok": ok, "boundary_ok": bok,
                     "seconds": round(time.time() - t)})
        pd.DataFrame(rows).to_csv(csv, index=False)
        progress()
        print(f"{time.strftime('%H:%M')} {name:32s} done ({round(time.time() - t)}s)", flush=True)
    progress()


def load_all():
    fs = sorted(OUT.glob("exp10_run_w*.csv"))
    return pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates(["network", "replicate"])


def summary():
    d = load_all()
    real = d[d.network == "real"].iloc[0]
    print(d.groupby("network").agg(N=("hit_rate", "size"), mean=("hit_rate", "mean"),
                                   sd=("hit_rate", "std")).to_string())
    out = {}
    a, b = np.load(HITS / "real_0.npy"), np.load(HITS / "no_wiring_0.npy")
    n10, n01 = int((a & ~b).sum()), int((~a & b).sum())
    p1 = binomtest(n10, n10 + n01, 0.5, alternative="greater").pvalue if n10 + n01 else 1.0
    out["q1"] = {"real": a.mean(), "no_wiring": b.mean(), "real_only": n10, "no_wiring_only": n01, "p": p1,
                 "yes": bool(p1 < 0.05)}
    print(f"\nQ1 real {a.mean():.3f} vs no wiring {b.mean():.3f}; real-only {n10}, no-wiring-only {n01}; "
          f"McNemar one-sided p = {p1:.4g} -> {'YES' if p1 < 0.05 else 'NO'}")
    ps = {}
    for g in INSIDE:
        x = d[d.network == g].hit_rate
        k = int((x >= real.hit_rate).sum())
        ps[g] = (1 + k) / (len(x) + 1)
        out[g] = {"N": int(len(x)), "mean": float(x.mean()), "k": k, "p": ps[g]}
        print(f"Q2 {g}: N={len(x)} mean {x.mean():.3f}; k={k}; p = {ps[g]:.4f}")
    done = all((d.network == g).sum() == CFG["n_per_type"] for g in INSIDE)
    out["q2_yes"] = bool(all(p < 0.05 for p in ps.values())) if done else None
    print("Q2:", ("YES" if out["q2_yes"] else "NO") if done else "incomplete")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--worker", type=int)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    summary() if a.summary else run(a.worker)
