"""A frozen rate operator on the connectome, and the two families of measurement
that the larval result says should come apart.

Dynamics (no single-neuron parameter is fitted -- the wiring is the model):

    x(t+1) = (1 - leak) * x(t) + leak * tanh(gain * (x(t) @ W) + drive(t))

GROSS measures describe the operator as a dynamical system: how strongly it
amplifies, how many dimensions its activity occupies. The larval result predicts
these survive degree- and weight-matched rewiring.

ROUTING measures describe where a given sensory channel's signal lands. The larval
result predicts these do NOT survive rewiring. The adult test is whether sensory
channels still reach distinguishable sets of descending neurons.
"""
from __future__ import annotations

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigs


def spectral_radius(W: sparse.csr_matrix, tol: float = 1e-3) -> float:
    try:
        val = eigs(W.astype(np.float64), k=1, which="LM", return_eigenvectors=False,
                   tol=tol, maxiter=5000)
        return float(np.abs(val[0]))
    except Exception:
        # Power iteration fallback: fine for a scale factor.
        rng = np.random.default_rng(0)
        v = rng.standard_normal(W.shape[0])
        v /= np.linalg.norm(v)
        lam = 0.0
        for _ in range(200):
            u = v @ W
            nrm = np.linalg.norm(u)
            if nrm == 0:
                return 0.0
            v, lam = u / nrm, nrm
        return float(lam)


def normalise(W: sparse.csr_matrix, target_rho: float = 0.95, rho: float | None = None):
    """Scale so every network is compared at the same distance from instability.
    Without this, a difference in performance is only a difference in gain."""
    rho = spectral_radius(W) if rho is None else rho
    if rho <= 0:
        return W.copy(), 0.0
    return (W * (target_rho / rho)).tocsr(), rho


def run(W, drive_idx, steps=60, leak=0.3, gain=1.0, amp=1.0, seed=0):
    """Pulse a set of neurons, let activity settle, return the trajectory."""
    n = W.shape[0]
    x = np.zeros(n, dtype=np.float64)
    u = np.zeros(n, dtype=np.float64)
    u[drive_idx] = amp
    traj = np.empty((steps, n), dtype=np.float32)
    for t in range(steps):
        x = (1 - leak) * x + leak * np.tanh(gain * (x @ W) + u)
        traj[t] = x
    return traj


def participation_ratio(v: np.ndarray) -> float:
    """Effective number of active units: 1 if one unit carries everything,
    N if activity is spread evenly."""
    p = np.abs(v).astype(np.float64)
    s = p.sum()
    if s == 0:
        return 0.0
    p = p / s
    return float(1.0 / np.sum(p ** 2))


def calibrate_gain(W, drive_idx, target_active=0.05, steps=40, lo=1e-3, hi=50.0, iters=12, **kw):
    """Find the gain at which this network is as excitable as the reference one.

    Without this, a rewired network can look like it "loses routing" when in fact
    it was merely driven into a saturated regime where everything is active.
    Matching the operating point is what makes the routing comparison mean anything.
    """
    def active(g):
        x = run(W, drive_idx, steps=steps, gain=g, **kw)[-1]
        return float(np.mean(np.abs(x) > 1e-3))

    if active(lo) > target_active:
        return float(lo), active(lo)
    if active(hi) < target_active:
        return float(hi), active(hi)
    for _ in range(iters):
        mid = float(np.sqrt(lo * hi))
        if active(mid) < target_active:
            lo = mid
        else:
            hi = mid
    g = float(np.sqrt(lo * hi))
    return g, active(g)


def gross_signatures(W, drive_idx, **kw) -> dict:
    traj = run(W, drive_idx, **kw)
    final = traj[-1]
    return {
        "mean_abs_activity": float(np.mean(np.abs(final))),
        "active_fraction": float(np.mean(np.abs(final) > 1e-3)),
        "dimensionality": participation_ratio(final),
        "settling": float(np.mean(np.abs(traj[-1] - traj[-2]))),
    }


def routing_profile(W, drive_idx, readout_idx, **kw) -> np.ndarray:
    """Where does this channel land? Magnitude of steady activity on the readout
    population, normalised to a unit vector so only the pattern is compared."""
    final = run(W, drive_idx, **kw)[-1]
    p = np.abs(final[readout_idx]).astype(np.float64)
    nrm = np.linalg.norm(p)
    return p / nrm if nrm > 0 else p


def channel_separation(profiles: dict[str, np.ndarray]) -> dict:
    """How distinguishable are the channels at the readout?

    separation = mean pairwise cosine DISTANCE between channel profiles.
    1.0 means every channel drives a disjoint set of readout neurons; 0.0 means
    the readout cannot tell the channels apart -- the network routes nothing.
    """
    names = sorted(profiles)
    sims = []
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            pa, pb = profiles[names[a]], profiles[names[b]]
            if np.linalg.norm(pa) == 0 or np.linalg.norm(pb) == 0:
                continue
            sims.append(float(np.dot(pa, pb)))
    if not sims:
        return {"separation": float("nan"), "n_pairs": 0}
    return {
        "separation": float(1.0 - np.mean(sims)),
        "min_separation": float(1.0 - np.max(sims)),
        "n_pairs": len(sims),
        "mean_specificity": float(np.mean([participation_ratio(p) for p in profiles.values()])),
    }
