"""Figures drawn in the style of Shiu et al. Figure 1, from our own runs.

Panel C  MN9 firing rate vs sugar sensory firing rate, with s.d. across trials
         (their Fig. 1c, which also splits ipsilateral vs contralateral MN9)
Panel D  heatmap of responsive neurons x sugar drive, ordered by firing rate
         (their Fig. 1d)

Their panels sweep drive in fine steps; ours has the levels we ran, so the
heatmap is coarser along x. Everything else follows their layout.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))
DOSE = ROOT / "results" / "repro_shiu" / "dose"
FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

from model import default_params  # noqa: E402
import utils as utl  # noqa: E402

MN9 = 720575940660219265
T_RUN = 1.0  # seconds per trial
OURS, THEIRS, INK, MUTED, SURFACE = "#eb6834", "#2a78d6", "#0b0b0b", "#898781", "#fcfcfb"

plt.rcParams.update({
    "font.size": 9, "font.family": "DejaVu Sans",
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
})


def per_trial_rates(path):
    """Rate per neuron per trial, so we can show spread the way their panel does."""
    df = utl.load_exps([str(path)])
    counts = df.groupby(["flywire_id", "trial"]).size().rename("n").reset_index()
    counts["rate"] = counts["n"] / T_RUN
    wide = counts.pivot(index="flywire_id", columns="trial", values="rate").fillna(0.0)
    wide.index = wide.index.astype("int64")
    return wide


def collect():
    runs = {}
    for p in sorted(DOSE.glob("sugar_*Hz.parquet")):
        hz = int(p.stem.split("_")[1].replace("Hz", ""))
        runs[hz] = per_trial_rates(p)
    dose = pd.read_csv(DOSE / "dose_response.csv").set_index("drive_hz")
    return runs, dose


def panel_c(runs, dose):
    fig, ax = plt.subplots(figsize=(4.6, 3.8), dpi=200)
    xs, ys, es = [], [], []
    for hz in sorted(runs):
        wide = runs[hz]
        grn = dose.loc[hz, "grn_rate"]
        row = wide.loc[MN9] if MN9 in wide.index else pd.Series([0.0, 0.0, 0.0])
        xs.append(grn); ys.append(row.mean()); es.append(row.std(ddof=1))

    ax.errorbar(xs, ys, yerr=es, fmt="-o", color=OURS, ecolor=OURS, elinewidth=1.2,
                capsize=3, ms=6, lw=1.8, markeredgecolor=SURFACE, markeredgewidth=1.0,
                label="ours (reproduction)", zorder=3)
    # Measured from the authors' own stored runs (published_points.py), not assumed.
    ax.plot([196.75, 98.98], [93.27, 67.03], "s", color=THEIRS, ms=9,
            markeredgecolor=SURFACE, markeredgewidth=1.2, label="published runs", zorder=4)

    ax.set_xlabel("Sugar GRN firing rate (Hz)")
    ax.set_ylabel("Predicted MN9 firing rate (Hz)")
    ax.set_xlim(0, 215); ax.set_ylim(-4, 105)
    ax.set_title("c", loc="left", fontweight="bold", fontsize=12, color=INK, pad=8)
    ax.legend(frameon=False, fontsize=8, labelcolor=INK, loc="lower right")
    ax.grid(True, alpha=0.35, color="#e1e0d9")
    fig.tight_layout()
    out = FIG / "paper_panel_c_dose_response.png"
    fig.savefig(out); plt.close(fig)
    return out


def panel_d(runs, dose, n_top=200):
    levels = sorted(runs)
    mat = pd.DataFrame({hz: runs[hz].mean(axis=1) for hz in levels}).fillna(0.0)
    top = mat[levels[-1]].sort_values(ascending=False).head(n_top).index
    mat = mat.loc[top]

    fig, ax = plt.subplots(figsize=(4.6, 4.4), dpi=200)
    im = ax.imshow(mat.to_numpy(), aspect="auto", cmap="plasma",
                   extent=[0, len(levels), len(mat), 0], interpolation="nearest")
    ax.set_xticks(np.arange(len(levels)) + 0.5)
    ax.set_xticklabels([f"{dose.loc[h, 'grn_rate']:.0f}" for h in levels])
    ax.set_xlabel("Sugar GRN firing rate (Hz)")
    ax.set_ylabel(f"Responsive neurons (top {len(mat)})")
    ax.set_title("d", loc="left", fontweight="bold", fontsize=12, color=INK, pad=8)
    cb = fig.colorbar(im, ax=ax, pad=0.03)
    cb.set_label("Predicted firing rate (Hz)", color=INK, fontsize=8.5)
    cb.ax.tick_params(colors=MUTED, labelsize=8)
    cb.outline.set_edgecolor("#c3c2b7")
    fig.tight_layout()
    out = FIG / "paper_panel_d_heatmap.png"
    fig.savefig(out); plt.close(fig)
    return out


if __name__ == "__main__":
    runs, dose = collect()
    print("drive levels available:", sorted(runs))
    print("wrote", panel_c(runs, dose))
    print("wrote", panel_d(runs, dose))
