"""Step 10 tuning, before the plan: choose the learning rate and number of epochs
on a brain that is NOT tested, by validation error, never by hit rate.

Brain: inside-only degree shuffle, replicate 51 (seed 1050). Test brains are
replicates 1-50, so this one is outside the test set.
Data: the 200 training balls of step 9 (seed 11, teacher + 30% random actions),
split by ball into 160 for training (balls 0-159) and 40 for validation (160-199).
Grid: learning rate 1e-3, 3e-3, 1e-2 (Adam), 10 epochs each, 10 balls per update,
ball order shuffled each epoch (seed 7 + epoch).

Selection rule (fixed before running): the learning rate and epoch count with
the lowest validation mean squared error. If two are within 1% of each other,
the smaller learning rate, then the fewer epochs. This (lr, epochs) is then
used unchanged for every brain in the plan.

  python experiments/exp10_tune.py --lr 1e-3     # one worker per learning rate
  python experiments/exp10_tune.py --summary
"""
from __future__ import annotations

import argparse
import ctypes
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from flynull import data as fw
from flynull import pong
from flynull import pong_train as pt
from flynull import rate_operator as op
from flynull.routing import boundary_masks, make_surrogate, sensory_channels

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
LRS, EPOCHS, BATCH, NTRAIN = (1e-3, 3e-3, 1e-2), 10, 10, 160
GEN, REP = "interior_degree_preserving", 51


def setup():
    """Brain, inputs and training balls shared by tuning and the main run."""
    c = fw.load()
    meta, sign = c.meta, c.meta["nt_sign"].to_numpy()
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(c.n, channels, readout)
    types = meta.primary_type.fillna(meta.super_class.fillna("na") + "_untyped").astype("category").cat.codes.to_numpy()
    inp, screen = pong.eye_inputs(meta)
    return c, sign, labels, boundary, readout, types, inp, screen


def train(m, balls, lr, epochs, on_epoch=None):
    opt = pt.Adam({"theta": m.theta.shape, "wr": m.wr.shape, "br": ()}, lr)
    for ep in range(epochs):
        order = np.random.default_rng(7 + ep).permutation(len(balls))
        for s in range(0, len(order), BATCH):
            G = {"theta": 0.0, "wr": 0.0, "br": 0.0}
            idx = order[s:s + BATCH]
            for i in idx:
                _, g = m.loss_grad(*balls[i])
                for k in G:
                    G[k] = G[k] + g[k] / len(idx)
            new = opt.step({"theta": m.theta, "wr": m.wr, "br": m.br}, G)
            m.theta, m.wr, m.br = new["theta"], new["wr"], np.float32(new["br"])
            m.apply()
        if on_epoch:
            on_epoch(ep)
    return m


def val_mse(m, balls):
    tot = n = 0
    for D, y in balls:
        f, _, _ = m.forward(D, keep=False)
        tot += float(np.sum((f @ m.wr + m.br - y) ** 2))
        n += len(y)
    return tot / n


def run(lr):
    ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)
    import exp09_pong as e9
    c, sign, labels, boundary, readout, types, inp, screen = setup()
    W = make_surrogate(GEN, c.W, np.random.default_rng(1000 + REP - 1), sign, labels, 10, boundary)
    Wn, _ = op.normalise(W)
    WT = Wn.T.astype(np.float32).tocsr()
    del Wn, W
    gfile = OUT / "exp10_tune_gain.json"
    if gfile.exists():
        gain = json.loads(gfile.read_text())["gain"]
    else:
        gain, active, flag = e9.calibrate(WT, inp, readout, screen)
        gfile.write_text(json.dumps({"gain": gain, "active": active, "flag": flag}))
    balls = pt.record_balls(np.random.default_rng(11), 200, screen)
    tr, va = balls[:NTRAIN], balls[NTRAIN:]
    m = pt.Trainable(WT, inp, readout, gain, types, int(types.max()) + 1)
    rows, t0 = [], time.time()
    prog = OUT / f"exp10_tune_lr{lr:g}.json"

    def log(ep):
        rows.append({"lr": lr, "epoch": ep + 1, "val_mse": val_mse(m, va),
                     "theta_sd": float(m.theta.std()), "seconds": round(time.time() - t0)})
        pd.DataFrame(rows).to_csv(OUT / f"exp10_tune_lr{lr:g}.csv", index=False)
        prog.write_text(json.dumps({"done": ep + 1, "of": EPOCHS, "start": int(t0), "now": int(time.time())}))
        print(f"{time.strftime('%H:%M')} lr {lr:g} epoch {ep + 1}: val {rows[-1]['val_mse']:.4f} "
              f"theta sd {rows[-1]['theta_sd']:.3f} ({rows[-1]['seconds']}s)", flush=True)

    prog.write_text(json.dumps({"done": 0, "of": EPOCHS, "start": int(t0), "now": int(t0)}))
    print(f"gain {gain:.4g}", flush=True)
    train(m, tr, lr, EPOCHS, log)


def summary():
    d = pd.concat([pd.read_csv(f) for f in sorted(OUT.glob("exp10_tune_lr*.csv"))])
    print(d.pivot(index="epoch", columns="lr", values="val_mse").round(4).to_string())
    best = d.val_mse.min()
    ok = d[d.val_mse <= best * 1.01].sort_values(["lr", "epoch"])
    pick = ok.iloc[0]
    print(f"\nChosen: lr {pick.lr:g}, {int(pick.epoch)} epochs (val {pick.val_mse:.4f}; best {best:.4f})")
    return pick


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    ap = argparse.ArgumentParser()
    ap.add_argument("--lr", type=float)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    summary() if a.summary else run(a.lr)
