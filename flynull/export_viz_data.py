"""Export the real activation patterns behind Experiment 1, for visualisation.

Writes results/viz_data.json:
  - per sensory channel, the activation of all 1,305 descending neurons,
    for the real connectome and a degree-preserving rewiring, at a MATCHED
    operating point
  - whole-brain active fraction at an UNCALIBRATED gain (the "scream" artifact)
    and after calibration (the honest comparison)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import data as fw
import nulls
import rate_operator as op

OUT = Path(__file__).resolve().parent.parent / "results"
CHANNELS = ["olfactory", "gustatory", "mechanosensory", "hygrosensory"]
STEPS = 40


def profiles_for(W, channels, readout, gain):
    out = {}
    for name, idx in channels.items():
        final = op.run(W, idx, steps=STEPS, gain=gain)[-1]
        p = np.abs(final[readout])
        m = p.max()
        out[name] = np.round(p / m, 4).tolist() if m > 0 else p.tolist()
    return out


def main():
    c = fw.load()
    meta = c.meta
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    channels = {}
    for name in CHANNELS:
        idx = np.flatnonzero(meta["class"].eq(name).to_numpy())
        if len(idx):
            channels[name] = idx
    print({k: len(v) for k, v in channels.items()}, "readout", len(readout))

    sign = meta["nt_sign"].to_numpy()
    rng = np.random.default_rng(1000)
    print("generating degree-preserving surrogate ...")
    S = nulls.degree_preserving(c.W, rng, sign=sign, swaps_per_edge=2)

    Wr, rho_r = op.normalise(c.W)
    Ws, rho_s = op.normalise(S)
    cal_idx = np.concatenate(list(channels.values()))

    # Uncalibrated: identical gain for both networks -- the mistake case.
    uncal = {}
    for label, W in (("real", Wr), ("rewired", Ws)):
        x = op.run(W, cal_idx, steps=STEPS, gain=1.0)[-1]
        uncal[label] = float(np.mean(np.abs(x) > 1e-3))
    print("uncalibrated active fraction:", uncal)

    # Calibrated: each network driven to the same operating point.
    gains, cal = {}, {}
    for label, W in (("real", Wr), ("rewired", Ws)):
        g, achieved = op.calibrate_gain(W, cal_idx, target_active=0.05, steps=STEPS)
        gains[label], cal[label] = g, achieved
    print("calibrated:", cal, "gains:", gains)

    payload = {
        "n_neurons": int(c.n),
        "n_edges": int(c.W.nnz),
        "n_descending": int(len(readout)),
        "channel_sizes": {k: int(len(v)) for k, v in channels.items()},
        "spectral_radius": {"real": rho_r, "rewired": rho_s},
        "uncalibrated_active": uncal,
        "calibrated_active": cal,
        "gains": gains,
        "profiles": {
            "real": profiles_for(Wr, channels, readout, gains["real"]),
            "rewired": profiles_for(Ws, channels, readout, gains["rewired"]),
        },
    }

    for net in ("real", "rewired"):
        spread = []
        for name, p in payload["profiles"][net].items():
            spread.append(op.participation_ratio(np.array(p)))
        payload.setdefault("specificity", {})[net] = float(np.mean(spread))
    print("specificity (effective DNs carrying a channel):", payload["specificity"])

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "viz_data.json"
    json.dump(payload, open(path, "w"), separators=(",", ":"))
    print(f"wrote {path}  ({path.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
