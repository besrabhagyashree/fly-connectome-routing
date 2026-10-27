"""Matched surrogate (null) connectomes.

The question these answer: when a connectome-derived network performs well, is it
the *exact wiring* doing the work, or only coarse statistics that any random graph
with the same degrees and weights would have?

Each surrogate destroys one property and preserves the rest, so a performance drop
localises which property mattered. All generators preserve Dale's law, because
sign is a property of the presynaptic neuron (the matrix row) and every generator
keeps edges attached to their source row.

Ladder, from most to least structure preserved:
  weight_shuffle      topology kept, weight-topology alignment destroyed
  block_preserving    rewired only within super_class -> super_class blocks
  degree_preserving   in/out degree kept exactly, wiring otherwise randomised
  erdos_renyi         density kept, everything else destroyed
"""
from __future__ import annotations

import numpy as np
from scipy import sparse


def _decompose(W: sparse.csr_matrix):
    coo = W.tocoo()
    return coo.row.astype(np.int64), coo.col.astype(np.int64), coo.data.copy()


def _rebuild(src, dst, w, n) -> sparse.csr_matrix:
    # csr_matrix sums duplicate coordinates, which would hide a broken surrogate
    # as a quiet drop in edge count. Refuse instead.
    keys = src.astype(np.int64) * n + dst.astype(np.int64)
    if len(np.unique(keys)) != len(keys):
        raise AssertionError("surrogate produced duplicate edges; degree sequence would be corrupted")
    return sparse.csr_matrix((w, (src, dst)), shape=(n, n))


def _resign(src, w, sign):
    """Force each edge's sign to match its presynaptic neuron (Dale's law)."""
    return np.abs(w) * sign[src]


def weight_shuffle(W, rng, sign=None):
    src, dst, w = _decompose(W)
    perm = rng.permutation(len(w))
    w = np.abs(w)[perm]
    if sign is not None:
        w = _resign(src, w, sign)
    else:
        w = w * np.sign(_decompose(W)[2])
    return _rebuild(src, dst, w, W.shape[0])


def erdos_renyi(W, rng, sign=None):
    """Same neuron count, edge count and weight distribution; wiring random."""
    n = W.shape[0]
    src0, dst0, w0 = _decompose(W)
    m = len(w0)

    keys = set()
    src = np.empty(m, np.int64)
    dst = np.empty(m, np.int64)
    filled = 0
    while filled < m:
        need = m - filled
        cand_s = rng.integers(0, n, size=need * 2)
        cand_d = rng.integers(0, n, size=need * 2)
        ok = cand_s != cand_d
        cand_s, cand_d = cand_s[ok], cand_d[ok]
        for s, d in zip(cand_s, cand_d):
            k = s * n + d
            if k in keys:
                continue
            keys.add(k)
            src[filled], dst[filled] = s, d
            filled += 1
            if filled == m:
                break

    w = np.abs(w0)[rng.permutation(m)]
    w = _resign(src, w, sign) if sign is not None else w
    return _rebuild(src, dst, w, n)


def _swap_pass(src, dst, w, n, rng, n_swaps, restrict=None):
    """Vectorised directed double-edge swaps: (a->b, c->d) becomes (a->d, c->b).

    Preserves every neuron's in-degree and out-degree exactly. Weights travel
    with their edge, so the weight sequence is preserved too.
    """
    m = len(src)
    keys = src * n + dst
    order = np.argsort(keys)
    sorted_keys = keys[order]

    done = 0
    batch = max(1024, min(200_000, m // 4))
    while done < n_swaps:
        i = rng.integers(0, m, size=batch)
        j = rng.integers(0, m, size=batch)

        a, b, c, d = src[i], dst[i], src[j], dst[j]
        ok = (i != j) & (a != d) & (c != b) & (a != c) & (b != d)
        if restrict is not None:
            # only swap partners drawn from the same block pair
            ok &= (restrict[b] == restrict[d])
        i, j, a, b, c, d = i[ok], j[ok], a[ok], b[ok], c[ok], d[ok]
        if len(i) == 0:
            continue

        k1, k2 = a * n + d, c * n + b
        pos1 = np.searchsorted(sorted_keys, k1)
        pos2 = np.searchsorted(sorted_keys, k2)
        exists1 = (pos1 < len(sorted_keys)) & (sorted_keys[np.minimum(pos1, len(sorted_keys) - 1)] == k1)
        exists2 = (pos2 < len(sorted_keys)) & (sorted_keys[np.minimum(pos2, len(sorted_keys) - 1)] == k2)
        ok = ~exists1 & ~exists2
        i, j, b, d = i[ok], j[ok], b[ok], d[ok]
        if len(i) == 0:
            continue

        # Keep only proposals that are independent of every other proposal in this
        # batch: no shared edge slot, and no shared newly created edge. Either
        # collision would assign one slot twice and destroy the degree sequence.
        touched = np.concatenate([i, j])
        u_t, c_t = np.unique(touched, return_counts=True)
        repeated_slot = u_t[c_t > 1]

        k1, k2 = src[i] * n + d, src[j] * n + b
        u_k, c_k = np.unique(np.concatenate([k1, k2]), return_counts=True)
        repeated_key = u_k[c_k > 1]

        keep = ~(
            np.isin(i, repeated_slot) | np.isin(j, repeated_slot)
            | np.isin(k1, repeated_key) | np.isin(k2, repeated_key)
        )
        i, j, b, d = i[keep], j[keep], b[keep], d[keep]
        if len(i) == 0:
            continue

        dst[i], dst[j] = d, b
        keys = src * n + dst
        sorted_keys = np.sort(keys)
        done += len(i)

    return src, dst, w


def degree_preserving(W, rng, sign=None, swaps_per_edge: int = 10):
    src, dst, w = _decompose(W)
    n = W.shape[0]
    src, dst, w = _swap_pass(src, dst, w, n, rng, int(swaps_per_edge * len(w)))
    if sign is not None:
        w = _resign(src, w, sign)
    return _rebuild(src, dst, w, n)


def block_preserving(W, rng, labels, sign=None, swaps_per_edge: int = 10):
    """Degree-preserving, but a target may only be exchanged for one in the same
    block (e.g. same super_class). Coarse projection structure survives; the exact
    target identity inside each block does not."""
    src, dst, w = _decompose(W)
    n = W.shape[0]
    codes = np.asarray(labels)
    src, dst, w = _swap_pass(src, dst, w, n, rng, int(swaps_per_edge * len(w)), restrict=codes)
    if sign is not None:
        w = _resign(src, w, sign)
    return _rebuild(src, dst, w, n)


GENERATORS = {
    "weight_shuffle": weight_shuffle,
    "block_preserving": block_preserving,
    "degree_preserving": degree_preserving,
    "erdos_renyi": erdos_renyi,
}


def check_preserved(W, S) -> dict:
    """Report which invariants a surrogate actually kept. Always run this:
    a null model that silently breaks its own invariant invalidates the result."""
    A, B = (W != 0), (S != 0)
    return {
        "n_edges_equal": W.nnz == S.nnz,
        "out_degree_equal": bool(np.array_equal(
            np.asarray(A.sum(axis=1)).ravel(), np.asarray(B.sum(axis=1)).ravel())),
        "in_degree_equal": bool(np.array_equal(
            np.asarray(A.sum(axis=0)).ravel(), np.asarray(B.sum(axis=0)).ravel())),
        "weight_multiset_equal": bool(np.array_equal(
            np.sort(np.abs(W.data)), np.sort(np.abs(S.data)))),
        "edge_overlap": float(len(np.intersect1d(
            W.tocoo().row * W.shape[0] + W.tocoo().col,
            S.tocoo().row * S.shape[0] + S.tocoo().col)) / W.nnz),
    }


# ---------------------------------------------------------------------------
# Inside-only (boundary-preserving) nulls.
#
# Standard degree-preserving swaps can hand a sensory neuron's edge a descending
# neuron (DN) as its new target, creating direct sensory->DN shortcuts that the
# real brain does not have (Park 2026, arXiv:2609.39248). These variants freeze
# the sensory-motor boundary and rewire only the interior:
#
#   boundary edge  = source is a sensory neuron  OR  target is a DN
#   interior edge  = everything else
#
# Boundary edges are kept bit-identical (same src, dst, weight). Interior edges are
# Maslov-Sneppen swapped among themselves. The interior set is closed under the
# swap (a->b, c->d) -> (a->d, c->b): sources never move, so no sensory source
# appears; the new targets b, d were interior targets, so no DN target appears.
# A new interior edge can never duplicate a boundary edge for the same reason.
# All of this is asserted, not assumed.
# ---------------------------------------------------------------------------

def _as_mask(x, n) -> np.ndarray:
    """Accept a boolean mask of length n or an index array; return a boolean mask."""
    x = np.asarray(x)
    if x.dtype == bool:
        if x.shape != (n,):
            raise ValueError(f"boundary mask has shape {x.shape}, expected ({n},)")
        return x
    m = np.zeros(n, dtype=bool)
    m[x.astype(np.int64)] = True
    return m


def boundary_edge_mask(src, dst, boundary_src, boundary_dst) -> np.ndarray:
    """True for edges that touch the sensory-motor boundary (masks are boolean)."""
    return boundary_src[src] | boundary_dst[dst]


def _interior_swap(W, rng, boundary_src, boundary_dst, sign, swaps_per_edge, restrict=None):
    n = W.shape[0]
    bsrc, bdst = _as_mask(boundary_src, n), _as_mask(boundary_dst, n)
    src, dst, w = _decompose(W)
    inner = np.flatnonzero(~boundary_edge_mask(src, dst, bsrc, bdst))

    s_i, d_i, w_i = src[inner].copy(), dst[inner].copy(), w[inner].copy()
    s_i, d_i, w_i = _swap_pass(s_i, d_i, w_i, n, rng, int(swaps_per_edge * len(inner)),
                               restrict=restrict)
    # Closure of the interior set under the swap (see note above).
    if np.any(bsrc[s_i]) or np.any(bdst[d_i]):
        raise AssertionError("interior swap created a boundary edge (sensory source or DN target)")
    if sign is not None:
        w_i = _resign(s_i, w_i, sign)

    src2, dst2, w2 = src.copy(), dst.copy(), w.copy()   # boundary slots untouched
    src2[inner], dst2[inner], w2[inner] = s_i, d_i, w_i
    return _rebuild(src2, dst2, w2, n)


def interior_degree_preserving(W, rng, boundary_src, boundary_dst, sign=None,
                               swaps_per_edge: int = 10):
    """degree_preserving applied to interior edges only; boundary edges frozen."""
    return _interior_swap(W, rng, boundary_src, boundary_dst, sign, swaps_per_edge)


def interior_block_preserving(W, rng, labels, boundary_src, boundary_dst, sign=None,
                              swaps_per_edge: int = 10):
    """block_preserving applied to interior edges only; boundary edges frozen."""
    return _interior_swap(W, rng, boundary_src, boundary_dst, sign, swaps_per_edge,
                          restrict=np.asarray(labels))


# Kept out of GENERATORS because they take boundary arguments; test_nulls.py and
# exp02 iterate GENERATORS with the original signatures.
INTERIOR_GENERATORS = {
    "interior_degree_preserving": interior_degree_preserving,
    "interior_block_preserving": interior_block_preserving,
}


def check_boundary(W, S, boundary_src, boundary_dst) -> dict:
    """Assert the sensory-motor boundary is identical in W and S. RAISES on failure.

    Every boundary edge of W must appear in S with the same (src, dst, weight),
    and S must contain no boundary edge that W lacks.
    """
    n = W.shape[0]
    bsrc, bdst = _as_mask(boundary_src, n), _as_mask(boundary_dst, n)

    def split(M):
        coo = M.tocoo()
        r, c, d = coo.row.astype(np.int64), coo.col.astype(np.int64), coo.data
        keep = boundary_edge_mask(r, c, bsrc, bdst)
        r, c, d = r[keep], c[keep], d[keep]
        o = np.lexsort((c, r))
        return r[o], c[o], d[o], int((~keep).sum())

    r0, c0, d0, n_int0 = split(W)
    r1, c1, d1, n_int1 = split(S)
    same = (len(r0) == len(r1) and np.array_equal(r0, r1) and np.array_equal(c0, c1)
            and np.array_equal(d0, d1))
    if not same:
        raise AssertionError(
            f"boundary not preserved: real has {len(r0)} boundary edges, surrogate {len(r1)} "
            f"(or same count but differing src/dst/weight)")
    if n_int0 != n_int1:
        raise AssertionError(f"interior edge count changed: {n_int0} -> {n_int1}")
    return {"boundary_identical": True, "n_boundary_edges": int(len(r0)),
            "n_interior_edges": n_int0}
