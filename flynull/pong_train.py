"""Training the connectome itself to play Pong, with the wiring kept.

Connectome-constrained training as in Lappalainen et al. (2024, Nature): which
neurons connect, the synapse counts and the signs stay fixed; only shared
strength parameters are learned. Here each presynaptic cell type gets one
output scale s_k = exp(theta_k), so every edge from a type-k neuron is
multiplied by s_k (signs are kept because s_k > 0). Degree shuffles keep every
neuron's type and out-degree, so every brain, real or shuffled, has exactly the
same parameters. A linear readout from the descending neurons is learned jointly.

Training is supervised imitation of the teacher (behavioural cloning) with
backpropagation through time over each ball, and Adam (Kingma & Ba 2015).
Inputs in training do not depend on the model, because the teacher (with 30%
random actions) moves the paddle; so a ball's frames can be recorded once.

Model (column form of pong.Reservoir; WT = W.T, post x pre):
    a_t = gain * (WT_eff @ x_t) + u_t,    x_{t+1} = (1 - L) x_t + L tanh(a_t)
    WT_eff = WT * s[type(pre)]
"""
from __future__ import annotations

import numpy as np
from scipy import sparse

from . import pong

L, STEPS = pong.LEAK, pong.STEPS_PER_FRAME


def record_balls(rng, n, screen, eps=0.3):
    """Drives, teacher targets and ball number for n teacher-played balls."""
    _, D, y, grp = pong.play(lambda d: d.astype(np.float32), lambda f, b, px: pong.teacher(b, px), rng, n,
                             screen, eps=eps, record=True)
    return [(D[grp == i], y[grp == i]) for i in range(n)]


class Trainable:
    def __init__(self, WT, input_idx, readout_idx, gain, pre_group, n_groups):
        self.WT = WT.tocsr().astype(np.float32)
        self.W = self.WT.T.tocsr()                       # pre x post, for the backward pass
        self.colgrp = pre_group[self.WT.indices]         # group of each stored edge's presynaptic neuron
        self.inp, self.out, self.gain = input_idx, readout_idx, float(gain)
        self.grp, self.ng = pre_group, n_groups
        self.n = WT.shape[0]
        self.theta = np.zeros(n_groups, dtype=np.float32)
        self.wr = np.zeros(len(readout_idx), dtype=np.float32)
        self.br = np.float32(0.0)
        self._base = self.WT.data.copy()
        self._applied = None
        self.apply()

    def apply(self):
        """Write the current scales into the edge weights."""
        s = np.exp(self.theta)
        self.WT.data = self._base * s[self.colgrp]
        self.W = self.WT.T.tocsr()
        self._applied = self.theta.copy()

    # ---- forward / backward over one ball -------------------------------------------------
    def forward(self, D, keep=True):
        n, T = self.n, len(D)
        x = np.zeros(n, dtype=np.float32)
        u = np.zeros(n, dtype=np.float32)
        xs, hs, feats = [], [], np.empty((T, len(self.out)), dtype=np.float32)
        for f in range(T):
            u[:] = 0
            u[self.inp] = D[f]
            for _ in range(STEPS):
                h = np.tanh(self.gain * (self.WT @ x) + u)
                if keep:
                    xs.append(x)
                    hs.append(h)
                x = (1 - L) * x + L * h
            feats[f] = x[self.out]
        return feats, xs, hs

    def loss_grad(self, D, y):
        """Mean squared error of the readout against the teacher, and its gradients."""
        feats, xs, hs = self.forward(D)
        pred = feats @ self.wr + self.br
        err = pred - y
        T = len(y)
        loss = float(np.mean(err ** 2))
        dpred = (2.0 / T) * err
        g_wr = feats.T @ dpred
        g_br = float(dpred.sum())
        g_theta = np.zeros(self.ng, dtype=np.float64)
        lam = np.zeros(self.n, dtype=np.float32)        # dLoss / dx_{t+1}
        t = len(xs)
        for f in range(T - 1, -1, -1):
            lam[self.out] += dpred[f] * self.wr
            for _ in range(STEPS):
                t -= 1
                mu = lam * L * (1 - hs[t] ** 2)          # dLoss / da_t
                back = self.gain * (self.W @ mu)         # dLoss / dx_t through the recurrence
                # d a_t / d theta_k = gain * sum over edges from type-k neurons of w_e x_pre:
                # sum_i in k  x_t[i] * (gain * W_eff @ mu)[i]
                g_theta += np.bincount(self.grp, weights=xs[t] * back, minlength=self.ng)
                lam = (1 - L) * lam + back
        return loss, {"theta": g_theta.astype(np.float32), "wr": g_wr, "br": np.float32(g_br)}

    # ---- closed-loop play with the trained readout --------------------------------------------
    def reservoir(self):
        res = pong.Reservoir(self.WT, self.inp, self.out, self.gain)
        return res

    def policy(self):
        wr, br = self.wr.copy(), float(self.br)
        return lambda f, b, px: float(f @ wr + br)


class Adam:
    def __init__(self, shapes, lr, b1=0.9, b2=0.999, eps=1e-8):
        self.lr, self.b1, self.b2, self.eps, self.t = lr, b1, b2, eps, 0
        self.m = {k: np.zeros(s, dtype=np.float64) for k, s in shapes.items()}
        self.v = {k: np.zeros(s, dtype=np.float64) for k, s in shapes.items()}

    def step(self, params, grads):
        self.t += 1
        out = {}
        for k, g in grads.items():
            self.m[k] = self.b1 * self.m[k] + (1 - self.b1) * g
            self.v[k] = self.b2 * self.v[k] + (1 - self.b2) * np.square(g)
            mh = self.m[k] / (1 - self.b1 ** self.t)
            vh = self.v[k] / (1 - self.b2 ** self.t)
            out[k] = (params[k] - self.lr * mh / (np.sqrt(vh) + self.eps)).astype(np.float32)
        return out
