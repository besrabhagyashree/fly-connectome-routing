"""Step 10 timing pilot (before the plan). Prints timings and memory only: no loss,
no hit rate, so nothing here can steer the plan's rules.

1. Gradient check of flynull/pong_train.py on a small random network
   (finite differences), so the backward pass is known to be right.
2. Real brain: seconds per training ball (forward + backward), per test ball,
   and peak memory, to size how many brains the plan can afford.
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

from flynull import data as fw
from flynull import pong
from flynull import pong_train as pt
from flynull import rate_operator as op

ROOT = Path(__file__).resolve().parent.parent
PROG = ROOT / "results" / "exp10_pilot_progress.json"
STAGES = ["gradient check", "load + normalise real brain", "record balls",
          "time training balls", "time test balls", "write timing"]


class PMC(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("PageFaultCount", wt.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t), ("a", ctypes.c_size_t), ("b", ctypes.c_size_t),
                ("c", ctypes.c_size_t), ("d", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t)]


def peak_gb():
    c = PMC()
    c.cb = ctypes.sizeof(PMC)
    k = ctypes.windll.kernel32
    k.GetCurrentProcess.restype = wt.HANDLE
    k.K32GetProcessMemoryInfo.argtypes = [wt.HANDLE, ctypes.POINTER(PMC), wt.DWORD]
    k.K32GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return c.PeakWorkingSetSize / 2 ** 30


T0 = time.time()


def progress(i, note=""):
    PROG.write_text(json.dumps({"stage": i, "of": len(STAGES), "name": STAGES[min(i, len(STAGES) - 1)],
                                "start": int(T0), "now": int(time.time()), "note": note}))
    print(f"{time.strftime('%H:%M:%S')} [{i}/{len(STAGES)}] {STAGES[min(i, len(STAGES) - 1)]} {note}", flush=True)


def gradient_check():
    rng = np.random.default_rng(0)
    n, ng = 60, 7
    A = sparse.random(n, n, density=0.15, random_state=1, format="csr", dtype=np.float32)
    A.data = (A.data - 0.5).astype(np.float32)
    WT, _ = op.normalise(A.T.tocsr())
    grp = rng.integers(0, ng, n)
    m = pt.Trainable(WT, np.arange(5), np.arange(40, 52), 1.5, grp, ng)
    m.theta = rng.normal(0, 0.3, ng).astype(np.float32)
    m.wr = rng.normal(0, 1, 12).astype(np.float32)
    m.apply()
    D = rng.uniform(0, 1, (6, 5)).astype(np.float32)
    y = rng.uniform(-1, 1, 6).astype(np.float32)
    _, g = m.loss_grad(D, y)
    worst = 0.0
    for k in range(ng):
        old = m.theta[k]
        h = 1e-2
        m.theta[k] = old + h; m.apply(); lp, _ = m.loss_grad(D, y)
        m.theta[k] = old - h; m.apply(); lm, _ = m.loss_grad(D, y)
        m.theta[k] = old; m.apply()
        num = (lp - lm) / (2 * h)
        worst = max(worst, abs(num - g["theta"][k]) / max(1e-6, abs(num) + abs(g["theta"][k])))
    for j in range(3):
        old = m.wr[j]
        m.wr[j] = old + 1e-2; lp, _ = m.loss_grad(D, y)
        m.wr[j] = old - 1e-2; lm, _ = m.loss_grad(D, y)
        m.wr[j] = old
        num = (lp - lm) / 2e-2
        worst = max(worst, abs(num - g["wr"][j]) / max(1e-6, abs(num) + abs(g["wr"][j])))
    return worst


def main():
    progress(0)
    worst = gradient_check()
    print(f"  worst relative gradient error {worst:.2e} ({'OK' if worst < 1e-2 else 'FAIL'})", flush=True)
    if worst >= 1e-2:
        raise SystemExit("gradient check failed")
    progress(1, f"gradient error {worst:.1e}")
    c = fw.load()
    meta = c.meta
    inp, screen = pong.eye_inputs(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    types = meta.primary_type.fillna(meta.super_class.fillna("na") + "_untyped").astype("category").cat.codes.to_numpy()
    Wn, _ = op.normalise(c.W)
    WT = Wn.T.astype(np.float32).tocsr()
    del Wn
    gain = float(pd.read_csv(ROOT / "results" / "exp09_pong_all.csv").query("network == 'real'").gain.iloc[0])
    m = pt.Trainable(WT, inp, readout, gain, types, int(types.max()) + 1)
    progress(2, f"{len(np.unique(types)):,} type scales, gain {gain:.3g}")
    balls = pt.record_balls(np.random.default_rng(11), 6, screen)
    frames = [len(b[1]) for b in balls]
    progress(3, f"{np.mean(frames):.0f} frames per ball")
    tt = []
    for D, y in balls:
        t = time.time()
        m.loss_grad(D, y)                      # loss deliberately not printed
        tt.append(time.time() - t)
        print(f"  training ball {time.time() - t:.1f}s  peak {peak_gb():.2f} GB", flush=True)
    progress(4, f"{np.median(tt):.1f}s per training ball")
    res = m.reservoir()
    t = time.time()
    pong.play(res.step, m.policy(), np.random.default_rng(5), 5, screen, reset=res.reset)  # hits not read
    te = (time.time() - t) / 5
    progress(5, f"{te:.1f}s per test ball")
    out = {"gradient_rel_error": float(worst), "frames_per_ball": float(np.mean(frames)),
           "train_ball_s": float(np.median(tt)), "test_ball_s": te, "peak_gb": peak_gb(),
           "n_type_scales": int(len(np.unique(types)))}
    (ROOT / "results" / "exp10_pilot_timing.json").write_text(json.dumps(out, indent=1))
    progress(6, json.dumps(out))


if __name__ == "__main__":
    main()
