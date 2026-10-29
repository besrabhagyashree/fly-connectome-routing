"""Fast checks of the package: modules import, the flow model's fast form matches
navis' loop, and inside-only surrogates leave the boundary untouched."""
import unittest

import numpy as np

import flynull
from flynull import data as fw
from flynull import nulls
from flynull.flow import selftest
from flynull.routing import boundary_masks, make_surrogate, sensory_channels
from flynull.stmap import MAIN_MODALITIES, SENSE_TO_STURNER


class TestPackage(unittest.TestCase):
    def test_version_and_map_names(self):
        self.assertEqual(flynull.__version__, "0.1.0")
        self.assertEqual(len(MAIN_MODALITIES), 8)
        self.assertTrue(all(m is None or m in MAIN_MODALITIES for m in SENSE_TO_STURNER.values()))

    def test_flow_fast_form_matches_navis_loop(self):
        # Recorded in results/exp04b_flow_settings.md: mean |diff| 0.015 (Monte-Carlo noise).
        st = selftest()
        self.assertGreater(st["nodes"], 300)
        self.assertLess(st["mean_abs_diff"], 0.03)


class TestInsideOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = fw.load()

    def test_inside_only_keeps_boundary_and_degrees(self):
        c, meta = self.c, self.c.meta
        channels = sensory_channels(meta)
        readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
        boundary = boundary_masks(c.n, channels, readout)
        sign = meta["nt_sign"].to_numpy()
        labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
        for gen in ("interior_degree_preserving", "interior_block_preserving"):
            with self.subTest(gen=gen):
                S = make_surrogate(gen, c.W, np.random.default_rng(1000), sign, labels, 1, boundary)
                chk = nulls.check_preserved(c.W, S)
                for k in ("n_edges_equal", "weight_multiset_equal", "out_degree_equal", "in_degree_equal"):
                    self.assertTrue(chk[k], k)
                self.assertTrue(nulls.check_boundary(c.W, S, *boundary)["boundary_identical"])


if __name__ == "__main__":
    unittest.main()
