"""Pong played by a frozen connectome: the game is shown on the eye, the wiring is
left untouched, and only a linear readout from the descending neurons is trained.

This is reservoir computing (Jaeger 2001; leaky units as in Jaeger et al. 2007):
the network is a fixed dynamical system, and a ridge-regression readout learns to
map its state to an action. Any skill the readout cannot get from the input
alone has to come from what the wiring does to the signal.

Game: a ball falls from the top of a unit square, bouncing off the side walls; a
paddle at the bottom moves left or right. One trial = one ball, ending in a hit
or a miss.

Eye: each eye column is one pixel. Lamina L1 and L2 cells (the photoreceptors'
direct targets) are placed on screen by their column coordinates in FlyWire's
column assignment (Matsliah et al. 2024). The left eye covers the left half of
the screen and the right eye the right half, mirrored. Which way the hex axes
point in visual space is a convention here, not a claim; it is the same for
every brain.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .data import DATA

SPEED = 0.03          # ball distance per frame
PADDLE_HALF = 0.1     # paddle half-width
PADDLE_SPEED = 0.04   # paddle distance per frame at full action
BALL_SIGMA = 0.04     # blob width on the eye
STEPS_PER_FRAME = 3   # model steps per game frame
LEAK = 0.3


def eye_inputs(meta: pd.DataFrame, types=("L1", "L2")):
    """Model indices of the input cells and their screen positions in [0, 1]^2."""
    col = pd.read_csv(DATA / "column_assignment.csv.gz")
    col = col[col["type"].isin(types)]
    pos = pd.Series(np.arange(len(meta)), index=meta["root_id"].to_numpy())
    col = col[col["root_id"].isin(pos.index)]
    xn = (col["x"] - col["x"].min()) / (col["x"].max() - col["x"].min())
    yn = (col["y"] - col["y"].min()) / (col["y"].max() - col["y"].min())
    right = col["hemisphere"].eq("right").to_numpy()
    sx = np.where(right, 0.5 + 0.5 * xn, 0.5 - 0.5 * xn)
    return pos.loc[col["root_id"]].to_numpy(), np.c_[sx, yn.to_numpy()]


@dataclass
class Ball:
    x: float
    y: float
    vx: float
    vy: float


def spawn(rng) -> Ball:
    ang = rng.uniform(np.deg2rad(30), np.deg2rad(150))
    return Ball(rng.uniform(0.1, 0.9), 0.95, SPEED * np.cos(ang), -SPEED * np.sin(ang))


def landing_x(b: Ball) -> float:
    """Where the ball will cross the paddle line, with side-wall bounces."""
    t = (b.y - 0.0) / -b.vy
    x = b.x + b.vx * t
    x = np.mod(x, 2.0)
    return float(2.0 - x if x > 1.0 else x)


def teacher(b: Ball, px: float) -> float:
    """The action that moves the paddle toward the landing point, in [-1, 1]."""
    return float(np.clip((landing_x(b) - px) / PADDLE_SPEED, -1, 1))


def render(b: Ball, px: float, screen: np.ndarray) -> np.ndarray:
    """Brightness at each input cell: the ball as a blob, the paddle as a bar."""
    d2 = (screen[:, 0] - b.x) ** 2 + (screen[:, 1] - b.y) ** 2
    ball = np.exp(-d2 / (2 * BALL_SIGMA ** 2))
    dx = np.maximum(np.abs(screen[:, 0] - px) - PADDLE_HALF, 0)
    paddle = np.exp(-(dx ** 2 + screen[:, 1] ** 2) / (2 * BALL_SIGMA ** 2))
    return np.maximum(ball, paddle)


def play(step_fn, policy, rng, n_trials, screen, eps=0.0, record=False, reset=None):
    """Run n_trials balls. step_fn(drive) advances the model one frame and returns
    the readout features; policy(features, ball, px) returns an action in [-1, 1].
    With eps > 0 a random action replaces the policy's on that share of frames,
    to widen the states seen in training. reset() is called before each ball.
    Returns hits per trial, and if record, the features, the teacher's action and
    the trial number on every frame."""
    hits, feats, targets, trial = np.zeros(n_trials, dtype=bool), [], [], []
    for i in range(n_trials):
        b, px = spawn(rng), 0.5
        if reset:
            reset()
        while True:
            f = step_fn(render(b, px, screen))
            if record:
                feats.append(f)
                targets.append(teacher(b, px))
                trial.append(i)
            a = rng.uniform(-1, 1) if eps and rng.random() < eps else policy(f, b, px)
            px = float(np.clip(px + PADDLE_SPEED * np.clip(a, -1, 1), PADDLE_HALF, 1 - PADDLE_HALF))
            b.x, b.y = b.x + b.vx, b.y + b.vy
            if b.x < 0 or b.x > 1:
                b.x, b.vx = (-b.x, -b.vx) if b.x < 0 else (2 - b.x, -b.vx)
            if b.y <= 0:
                hits[i] = abs(b.x - px) <= PADDLE_HALF + BALL_SIGMA
                break
    if record:
        return hits, np.asarray(feats, dtype=np.float32), np.asarray(targets, dtype=np.float32), np.asarray(trial)
    return hits


class Reservoir:
    """x(t+1) = (1 - leak) x(t) + leak * tanh(gain * x(t) W + amp * drive), held
    for STEPS_PER_FRAME steps per frame. The state is reset between trials by
    the caller (reset()), so no trial sees the end of the last one."""

    def __init__(self, WT, input_idx, readout_idx, gain, amp=1.0):
        self.WT, self.inp, self.out, self.gain, self.amp = WT, input_idx, readout_idx, gain, amp
        n = WT.shape[0] if WT is not None else int(input_idx.max()) + 1  # no wiring: eye cells only
        self.x = np.zeros(n, dtype=np.float32)
        self.u = np.zeros(n, dtype=np.float32)

    def reset(self):
        self.x[:] = 0

    def step(self, drive):
        self.u[:] = 0
        self.u[self.inp] = self.amp * drive
        for _ in range(STEPS_PER_FRAME):
            rec = self.WT @ self.x if self.gain else 0.0
            self.x = (1 - LEAK) * self.x + LEAK * np.tanh(self.gain * rec + self.u)
        return self.x[self.out].copy()

    def active_fraction(self):
        return float(np.mean(np.abs(self.x) > 1e-3))


def fit_ridge(F, y, groups, alphas=(1e-2, 1e-1, 1, 10, 1e2, 1e3, 1e4), folds=5):
    """Ridge readout on z-scored features, alpha by 5-fold cross-validation over
    whole trials. Zero-variance features are dropped."""
    keep = F.std(0) > 1e-8
    mu, sd = F[:, keep].mean(0), F[:, keep].std(0)
    Z = (F[:, keep] - mu) / sd
    fold = groups % folds

    def solve(Zt, yt, a):
        A = Zt.T @ Zt + a * np.eye(Zt.shape[1], dtype=np.float64)
        w = np.linalg.solve(A, Zt.T @ (yt - yt.mean()))
        return w, yt.mean()

    best, cv = None, {}
    for a in alphas:
        err = 0.0
        for k in range(folds):
            tr, te = fold != k, fold == k
            w, b0 = solve(Z[tr].astype(np.float64), y[tr], a)
            err += float(np.sum((Z[te] @ w + b0 - y[te]) ** 2))
        cv[a] = err / len(y)
        if best is None or cv[a] < cv[best]:
            best = a
    w, b0 = solve(Z.astype(np.float64), y, best)
    return {"keep": keep, "mu": mu, "sd": sd, "w": w, "b": b0, "alpha": best, "cv_mse": cv[best],
            "n_features": int(keep.sum())}


def readout_policy(m):
    def pol(f, b, px):
        return float(((f[m["keep"]] - m["mu"]) / m["sd"]) @ m["w"] + m["b"])
    return pol
