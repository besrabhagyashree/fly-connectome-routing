"""Step 8c: the real brain at the effective gain of the shuffles, following
results/exp08c_plan.md.

  python experiments/exp08c_effective_gain.py
"""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd

from exp08_gain_sweep import score
from flynull import data as fw
from flynull import rate_operator as op
from flynull.routing import sensory_channels

OUT = Path(__file__).resolve().parent.parent / "results"
TYPES = ("interior_degree_preserving", "interior_block_preserving")


def main():
    d = pd.concat([pd.read_csv(f) for f in glob.glob(str(OUT / "exp01_routing_vs_gross_[AC]*.csv")) + glob.glob(str(OUT / "exp05_exp01_j*.csv"))])
    real_rho = float(d[d.network == "real"].spectral_radius_raw.iloc[0])
    c = fw.load()
    channels = sensory_channels(c.meta)
    readout = np.flatnonzero(c.meta["super_class"].eq("descending").to_numpy())
    Wn, _ = op.normalise(c.W)
    rows = []
    for g in TYPES:
        x = d[d.network == g].drop_duplicates("replicate")
        gain = 0.001 * real_rho / x.spectral_radius_raw.mean()
        r = score(Wn, channels, readout, gain)
        ks, kp = int((x.mean_specificity <= r["spread"]).sum()), int((x.separation >= r["separation"]).sum())
        rows.append({"network": g, "N": len(x), "effective_gain": gain, "real_spread": r["spread"], "shuffle_spread": x.mean_specificity.mean(),
                     "sd_spread": x.mean_specificity.std(ddof=1), "k_spread": ks, "p_spread": (1 + ks) / (len(x) + 1),
                     "real_separation": r["separation"], "shuffle_separation": x.separation.mean(), "k_separation": kp,
                     "p_separation": (1 + kp) / (len(x) + 1)})
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "exp08c_summary.csv", index=False)
    print(t.round(5).T.to_string())
    print("\nRule, spread:", "SURVIVES" if (t.p_spread < 0.05).all() else "ARTEFACT")
    print("Separation:", "SURVIVES" if (t.p_separation < 0.05).all() else "ARTEFACT")


if __name__ == "__main__":
    main()
