"""Figures for the reproduction report.

Palette: categorical slots 1 and 2 from the dataviz reference palette, validated
with scripts/validate_palette.js for light and dark surfaces.
  theirs (published) = blue  #2a78d6
  ours  (reproduced) = orange #eb6834
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
RES = ROOT / "results" / "repro_shiu"
FIG = ROOT / "results" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

THEIRS, OURS = "#2a78d6", "#eb6834"
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#898781", "#e1e0d9", "#fcfcfb"
MN9 = 720575940660219265
SUGAR = [
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
    720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
    720575940621502051, 720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543, 720575940632425919,
    720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570,
]

plt.rcParams.update({
    "font.size": 9, "font.family": "DejaVu Sans",
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED,
    "axes.spines.top": False, "axes.spines.right": False,
    "grid.color": GRID, "grid.linewidth": 0.8,
})


def fig_scatter(df):
    fig, ax = plt.subplots(figsize=(5.4, 5.0), dpi=200)
    lim = (0.3, 300)
    ax.plot(lim, lim, ls="--", lw=1.2, color=MUTED, zorder=1)
    ax.annotate("equal rates", xy=(120, 120), xytext=(150, 75), color=MUTED, fontsize=8,
                rotation=0, ha="left")

    other = df.drop(index=[i for i in SUGAR if i in df.index], errors="ignore")
    driven = df.loc[[i for i in SUGAR if i in df.index]]

    ax.scatter(other["theirs"], other["ours"], s=16, color=OURS, alpha=0.55,
               linewidths=0.6, edgecolors=SURFACE, zorder=2, label="downstream neurons")
    ax.scatter(driven["theirs"], driven["ours"], s=34, color=OURS, alpha=0.95,
               linewidths=1.0, edgecolors=INK, zorder=3, label="stimulated sugar neurons")

    if MN9 in df.index:
        x, y = df.loc[MN9, "theirs"], df.loc[MN9, "ours"]
        ax.scatter([x], [y], s=90, color=THEIRS, edgecolors=SURFACE, linewidths=1.4, zorder=4)
        ax.annotate(f"motor neuron 9\n{y:.0f} vs {x:.0f} Hz", xy=(x, y), xytext=(x * 0.28, y * 1.9),
                    color=THEIRS, fontsize=8.5, ha="left",
                    arrowprops=dict(arrowstyle="-", color=THEIRS, lw=1.0))

    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(*lim); ax.set_ylim(*lim)
    ax.set_xlabel("published rate, Shiu et al. (Hz)")
    ax.set_ylabel("our reproduction (Hz)")
    ax.set_title("Every neuron fires, all of them a little slower", color=INK,
                 fontsize=10.5, loc="left", pad=10)
    r = df["ours"].corr(df["theirs"])
    ax.text(0.03, 0.96, f"n = {len(df)} neurons\nPearson r = {r:.4f}", transform=ax.transAxes,
            va="top", ha="left", fontsize=8.5, color=INK)
    ax.grid(True, which="major", alpha=0.7)
    ax.legend(frameon=False, loc="lower right", fontsize=8.5, labelcolor=INK)
    fig.tight_layout()
    out = FIG / "fig1_scatter_ours_vs_published.png"
    fig.savefig(out); plt.close(fig)
    return out


def fig_gradient(df):
    driven = df.loc[[i for i in SUGAR if i in df.index]]
    downstream = df.drop(index=driven.index, errors="ignore")
    groups = [
        ("stimulated\nsugar neurons", (driven["ours"] / driven["theirs"]).dropna()),
        ("downstream\npopulation", (downstream["ours"] / downstream["theirs"]).dropna()),
    ]
    fig, ax = plt.subplots(figsize=(5.4, 2.9), dpi=200)
    ax.axvline(1.0, ls="--", lw=1.2, color=MUTED)
    ax.text(1.02, 2.42, "identical", color=MUTED, fontsize=8, va="center")

    for i, (label, vals) in enumerate(groups):
        y = len(groups) - 1 - i
        ax.scatter(vals, np.full(len(vals), y) + np.random.default_rng(3).normal(0, 0.055, len(vals)),
                   s=13, color=OURS, alpha=0.4, linewidths=0, zorder=2)
        med = vals.median()
        ax.plot([med, med], [y - 0.22, y + 0.22], color=INK, lw=2.2, zorder=3)
        ax.text(med, y + 0.3, f"{med:.2f}×", ha="center", fontsize=9, color=INK)

    if MN9 in df.index:
        ratio = df.loc[MN9, "ours"] / df.loc[MN9, "theirs"]
        ax.scatter([ratio], [2], s=90, color=THEIRS, zorder=4)
        ax.text(ratio, 2.3, f"{ratio:.2f}×", ha="center", fontsize=9, color=THEIRS)

    ax.set_yticks([2, 1, 0])
    ax.set_yticklabels(["motor neuron 9\n(4 synapses out)", groups[0][0], groups[1][0]],
                       fontsize=8.5, color=INK)
    ax.set_ylim(-0.6, 2.75)
    ax.set_xlim(0.3, 1.45)
    ax.set_xlabel("our rate ÷ published rate")
    ax.set_title("The shortfall shrinks with distance from the stimulus", color=INK,
                 fontsize=10.5, loc="left", pad=10)
    ax.grid(True, axis="x", alpha=0.7)
    fig.tight_layout()
    out = FIG / "fig2_gradient.png"
    fig.savefig(out); plt.close(fig)
    return out


def fig_dose():
    path = RES / "dose" / "dose_response.csv"
    if not path.exists():
        return None
    d = pd.read_csv(path).sort_values("grn_rate")
    if len(d) < 2:
        return None
    fig, ax = plt.subplots(figsize=(5.4, 3.6), dpi=200)
    ax.plot(d["grn_rate"], d["mn9_rate"], "-o", color=OURS, lw=2, ms=7,
            markeredgecolor=SURFACE, markeredgewidth=1.2, label="ours")
    # The two published points available in their repo.
    pub = pd.DataFrame({"grn": [196.2, 131.5], "mn9": [93.27, 67.03]})
    ax.plot(pub["grn"], pub["mn9"], "s", color=THEIRS, ms=8, markeredgecolor=SURFACE,
            markeredgewidth=1.2, label="published runs")
    ax.set_xlabel("sugar sensory neuron firing rate (Hz)")
    ax.set_ylabel("motor neuron 9 (Hz)")
    ax.set_title("Dose–response: sugar input to proboscis motor output", color=INK,
                 fontsize=10.5, loc="left", pad=10)
    ax.grid(True, alpha=0.7)
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK, loc="upper left")
    fig.tight_layout()
    out = FIG / "fig3_dose_response.png"
    fig.savefig(out); plt.close(fig)
    return out


if __name__ == "__main__":
    df = pd.read_csv(RES / "side_by_side.csv", index_col=0)
    df.index = df.index.astype("int64")
    made = [fig_scatter(df), fig_gradient(df), fig_dose()]
    for m in made:
        print("wrote", m if m else "(dose sweep not finished yet)")
