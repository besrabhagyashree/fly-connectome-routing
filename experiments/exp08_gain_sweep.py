"""Step 8: the rate-model test at fixed gains, following results/exp08_gain_sweep_plan.md.

Stage 1, real brain at every grid gain, picks the primary gain before any shuffle:
  python experiments/exp08_gain_sweep.py stage1
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

from flynull import data as fw
from flynull import rate_operator as op
from flynull.routing import sensory_channels

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
GAINS = (0.001, 0.01, 0.03, 0.1, 0.3, 1.0)
STEPS = 60


def direct_share(W, idx, readout, prof):
    """Share of |descending activity| on descending neurons with a direct input from this sense."""
    direct = np.asarray((abs(W[idx][:, readout]).sum(axis=0))).ravel() > 0
    a = np.abs(prof)
    return float(a[direct].sum() / a.sum()) if a.sum() else float("nan")


def score(Wn, channels, readout, gain):
    cal = np.concatenate(list(channels.values()))
    x = op.run(Wn, cal, steps=STEPS, gain=gain)[-1]
    active = float(np.mean(np.abs(x) > 1e-3))
    prof = {k: op.routing_profile(Wn, v, readout, steps=STEPS, gain=gain) for k, v in channels.items()}
    sep = op.channel_separation(prof)
    share = float(np.mean([direct_share(Wn, channels[k], readout, prof[k]) for k in channels]))
    return {"gain": gain, "active_fraction": active, "direct_share": share,
            "spread": sep["mean_specificity"], "separation": sep["separation"]}


def stage1():
    c = fw.load()
    channels = sensory_channels(c.meta)
    readout = np.flatnonzero(c.meta["super_class"].eq("descending").to_numpy())
    Wn, _ = op.normalise(c.W)
    rows = []
    for g in GAINS:
        t = time.time()
        rows.append(score(Wn, channels, readout, g))
        print({**rows[-1], "seconds": round(time.time() - t)}, flush=True)
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "exp08_stage1_real.csv", index=False)
    print(d.round(4).to_string(index=False))
    ok = d[(d.direct_share < 0.5) & (d.active_fraction < 0.5)]
    print(f"\nPrimary gain: {ok.gain.min() if len(ok) else 'NONE (no answer)'}", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["stage1"])
    stage1() if ap.parse_args().stage == "stage1" else None
