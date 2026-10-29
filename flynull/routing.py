"""Sensory channels, the sensory-motor boundary, surrogate construction and the
rate-model evaluation used by steps 1, 4a and 5 (from Exp01, unchanged)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import nulls
from . import rate_operator as op


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
