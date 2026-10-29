"""Regression: inside-only brain #1 rebuilt with the package reproduces its published
step 1 row (results/exp01_routing_vs_gross_C1.csv, replicate 0) and step 4a scores
(results/exp04_sim_vs_map_C1.csv, replicate 1). Takes ~4 min; run with
FLYNULL_SLOW=1 python -m unittest tests.test_regression"""
import os
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from flynull import data as fw
from flynull.routing import boundary_masks, evaluate, make_surrogate, sensory_channels
from flynull.stmap import load_map, score

RES = Path(__file__).resolve().parent.parent / "results"
GEN = "interior_degree_preserving"


@unittest.skipUnless(os.environ.get("FLYNULL_SLOW") == "1", "slow; set FLYNULL_SLOW=1")
class TestBrainOne(unittest.TestCase):
    def test_brain_1_reproduces_steps_1_and_4a(self):
        c = fw.load()
        meta = c.meta
        channels = sensory_channels(meta)
        readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
        sign = meta["nt_sign"].to_numpy()
        labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
        S = make_surrogate(GEN, c.W, np.random.default_rng(1000), sign, labels, 10,
                           boundary_masks(c.n, channels, readout))
        row, prof = evaluate(S, channels, readout, GEN)

        ref1 = pd.read_csv(RES / "exp01_routing_vs_gross_C1.csv")
        ref1 = ref1[(ref1.network == GEN) & (ref1.replicate == 0)].iloc[0]
        for k in ("mean_specificity", "separation", "min_separation", "active_fraction", "gain"):
            with self.subTest(step1=k):
                self.assertTrue(np.isclose(row[k], ref1[k], rtol=1e-5), f"{k}: {row[k]} vs {ref1[k]}")

        dn_type, rk = load_map(c.ids[readout].astype("int64"))
        got = score(prof, dn_type, rk).set_index("sense")
        ref4 = pd.read_csv(RES / "exp04_sim_vs_map_C1.csv")
        ref4 = ref4[(ref4.network == GEN) & (ref4.replicate == 1)].set_index("sense")
        for s in ref4.index:
            with self.subTest(step4a=s):
                self.assertAlmostEqual(got.loc[s, "rho_own"], ref4.loc[s, "rho_own"], places=6)
                self.assertEqual(bool(got.loc[s, "diagonal"]), bool(ref4.loc[s, "diagonal"]))


if __name__ == "__main__":
    unittest.main()
