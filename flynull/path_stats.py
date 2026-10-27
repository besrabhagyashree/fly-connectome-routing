"""Path statistics from each sensory set to the descending neurons (DNs).

Two structural quantities, after Park 2026 (arXiv:2609.39248), who showed that
standard degree-preserving nulls create direct sensory->DN shortcuts:

  direct_share   sum |W[sense -> DN]| / sum |W[sense -> all]|
                 fraction of a sense's outgoing synaptic weight that lands
                 directly on a DN.

  hop distance   multi-source BFS on the unweighted directed graph (pre -> post)
                 from the whole sense set; for every DN, the number of hops of the
                 shortest path from any neuron of that sense. Reported as a
                 histogram over hops plus the unreachable count.

No thresholds: every edge kept by the loader's min_syn filter counts as an edge.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse


def direct_share(W: sparse.csr_matrix, sense_idx, dn_idx) -> float:
    rows = abs(W[np.asarray(sense_idx)]).tocsc()
    total = rows.sum()
    if total == 0:
        return float("nan")
    return float(rows[:, np.asarray(dn_idx)].sum() / total)


def bfs_hops(W: sparse.csr_matrix, sources, max_hops: int = 50) -> np.ndarray:
    """Hop distance from the source set to every neuron; -1 = unreachable.
    Sources themselves are at distance 0."""
    A = W.tocsr()
    n = A.shape[0]
    dist = np.full(n, -1, dtype=np.int32)
    frontier = np.unique(np.asarray(sources, dtype=np.int64))
    dist[frontier] = 0
    h = 0
    while len(frontier) and h < max_hops:
        h += 1
        nbr = np.unique(A[frontier].indices.astype(np.int64))
        nbr = nbr[dist[nbr] < 0]
        dist[nbr] = h
        frontier = nbr
    return dist


def sense_to_dn_stats(W: sparse.csr_matrix, channels: dict, dn_idx) -> list[dict]:
    """One row per sense: direct share, hop histogram to DNs, mean/median hops."""
    dn_idx = np.asarray(dn_idx)
    out = []
    for name, idx in channels.items():
        d = bfs_hops(W, idx)[dn_idx]
        reach = d[d >= 0]
        # A DN that is itself in the sense set would sit at 0 hops; DNs and sensory
        # super_classes are disjoint, so this stays empty, but count it honestly.
        row = {"sense": name, "n_sense": int(len(idx)),
               "direct_share": direct_share(W, idx, dn_idx),
               "dn_reached": int(len(reach)), "dn_unreachable": int((d < 0).sum()),
               "mean_hops": float(reach.mean()) if len(reach) else float("nan"),
               "median_hops": float(np.median(reach)) if len(reach) else float("nan")}
        for h in range(0, 7):
            row[f"hop{h}"] = int((d == h).sum())
        row["hop7plus"] = int((d >= 7).sum())
        out.append(row)
    return out
