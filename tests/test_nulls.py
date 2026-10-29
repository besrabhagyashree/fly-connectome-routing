"""Verify every surrogate keeps the invariant it claims, on a small subgraph.

Run this before trusting any result: a null model that breaks its own invariant
produces a difference that means nothing.
"""
import time
import unittest

import numpy as np
from scipy import sparse

from flynull import data as fw
from flynull import nulls


def subgraph(c, k=4000, seed=0):
    rng = np.random.default_rng(seed)
    deg = np.asarray((c.A != 0).sum(axis=1)).ravel() + np.asarray((c.A != 0).sum(axis=0)).ravel()
    idx = np.sort(rng.choice(np.flatnonzero(deg > 0), size=k, replace=False))
    W = c.W[idx][:, idx].tocsr()
    sign = c.meta["nt_sign"].to_numpy()[idx]
    labels = c.meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()[idx]
    return W, sign, labels


def main():
    c = fw.load()
    W, sign, labels = subgraph(c)
    print(f"subgraph: {W.shape[0]} neurons, {W.nnz} edges\n")

    rng = np.random.default_rng(1)
    expect = {
        "weight_shuffle":   {"out_degree_equal", "in_degree_equal", "weight_multiset_equal"},
        "block_preserving": {"out_degree_equal", "weight_multiset_equal"},
        "degree_preserving": {"out_degree_equal", "in_degree_equal", "weight_multiset_equal"},
        "erdos_renyi":      {"weight_multiset_equal"},
    }

    ok_all = True
    for name, fn in nulls.GENERATORS.items():
        t0 = time.time()
        kw = {"labels": labels} if name == "block_preserving" else {}
        if name in ("degree_preserving", "block_preserving"):
            kw["swaps_per_edge"] = 5
        S = fn(W, rng, sign=sign, **kw)
        checks = nulls.check_preserved(W, S)
        dt = time.time() - t0

        missing = [k for k in expect[name] if not checks[k]]
        dale = bool(np.all(np.sign(S.data) == sign[S.tocoo().row]))
        status = "OK " if not missing and dale and checks["n_edges_equal"] else "FAIL"
        if status == "FAIL":
            ok_all = False
        print(f"{status} {name:18s} {dt:5.1f}s  overlap={checks['edge_overlap']:.3f}  "
              f"dale={dale}  " + (f"broken={missing}" if missing else ""))

    print("\nEdge overlap should fall as the ladder destroys more structure.")
    print("All invariants held." if ok_all else "INVARIANT BROKEN - do not use these results.")
    return ok_all


class TestNulls(unittest.TestCase):
    def test_every_generator_keeps_its_invariants(self):
        self.assertTrue(main())


if __name__ == "__main__":
    main()
