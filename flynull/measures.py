"""Published methods, reimplemented as measures over one connectome.

Each function is one paper's way of asking what a connectome does. Running them
all over the same surrogate ladder answers a question no single paper does:
*which published method's conclusion actually depends on the exact wiring?*

  memory_capacity      Jaeger's benchmark, as used by connectome reservoir work
                       (conn2res, Suarez et al. 2024; Drosophila reservoir study,
                       PMC12109256). Calibration-free: it does not depend on the
                       operating point we tuned, so it is an independent check on
                       the claim that gross dynamics survive rewiring.

  linear_influence     Pospisil et al. 2024 (effectome): treat the connectome as a
                       linear dynamical system and read steady-state influence of
                       one population on another. No simulation, no nonlinearity,
                       no free parameters beyond the spectral scale.

  reciprocity, hub_share
                       Lin et al. 2024 (network statistics): structural quantities
                       computed from the graph alone, for reference.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import gmres

import rate_operator as op


def memory_capacity(W, rng, n_probe=2000, steps=1200, washout=200, max_delay=40,
                    leak=0.3, gain=1.0, ridge=1e-6, in_scale=1.0):
    """How many past inputs can be read back out of the network's state?

    One random input stream is injected; linear readouts try to reconstruct it at
    delays 1..max_delay. Memory capacity is the summed r^2 over delays. This is the
    standard reservoir-computing benchmark, and it needs no operating-point
    calibration, so it cannot inherit that circularity.
    """
    n = W.shape[0]
    probe = rng.choice(n, size=min(n_probe, n), replace=False)
    w_in = rng.standard_normal(n) * in_scale

    u = rng.uniform(-1, 1, size=steps)
    x = np.zeros(n)
    states = np.empty((steps, len(probe)), dtype=np.float32)
    for t in range(steps):
        x = (1 - leak) * x + leak * np.tanh(gain * (x @ W) + w_in * u[t])
        states[t] = x[probe]

    S = states[washout:]
    S = np.column_stack([S, np.ones(len(S))]).astype(np.float64)
    G = S.T @ S + ridge * np.eye(S.shape[1])

    total, per_delay = 0.0, []
    for k in range(1, max_delay + 1):
        target = u[washout - k: steps - k]
        beta = np.linalg.solve(G, S.T @ target)
        pred = S @ beta
        var = target.var()
        r2 = 0.0 if var <= 0 else max(0.0, 1.0 - ((target - pred).var() / var))
        per_delay.append(r2)
        total += r2
    return {"memory_capacity": float(total),
            "mc_delay1": float(per_delay[0]),
            "mc_half_life": float(next((i + 1 for i, r in enumerate(per_delay) if r < 0.5),
                                       max_delay))}


def linear_influence(W, source_idx, target_idx, alpha=0.9, tol=1e-6, maxiter=400):
    """Steady-state influence of a source population on a target population.

    Pospisil et al. model the brain as x' = A x + u and read effects off
    (I - A)^-1. Here A is the connectome scaled to spectral radius alpha, so the
    series converges; the result is a routing profile with no dynamics simulated
    and no threshold applied.
    """
    n = W.shape[0]
    Wn, _ = op.normalise(W, target_rho=alpha)
    u = np.zeros(n)
    u[source_idx] = 1.0 / max(len(source_idx), 1)

    # (I - A^T) x = u , because influence flows along rows (pre -> post).
    A = sparse.eye(n, format="csr") - Wn.T.tocsr()
    x, info = gmres(A, u, rtol=tol, maxiter=maxiter)
    p = np.abs(x[target_idx])
    nrm = np.linalg.norm(p)
    return (p / nrm if nrm > 0 else p), int(info)


def structural_stats(W) -> dict:
    """Graph-level quantities of the kind Lin et al. 2024 report."""
    A = (W != 0).astype(np.int8).tocsr()
    n, m = A.shape[0], A.nnz
    recip = int((A.multiply(A.T)).nnz)
    out_deg = np.asarray(A.sum(axis=1)).ravel()
    order = np.argsort(out_deg)[::-1]
    top = order[: max(1, n // 100)]
    return {
        "reciprocity": float(recip / m) if m else 0.0,
        "hub_share_top1pct": float(out_deg[top].sum() / out_deg.sum()) if out_deg.sum() else 0.0,
        "mean_out_degree": float(out_deg.mean()),
    }
