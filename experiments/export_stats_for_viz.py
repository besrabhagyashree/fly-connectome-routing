"""Collect the replicate runs into a compact JSON for the artifact page."""
from __future__ import annotations

import glob
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results"

frames = [pd.read_csv(f) for f in glob.glob(str(RES / "exp01_routing_vs_gross_*.csv"))]
df = pd.concat(frames, ignore_index=True)

real = df[df.network == "real"].iloc[0]
out = {
    "real": {
        "separation": float(real["separation"]),
        "specificity": float(real["mean_specificity"]),
        "dimensionality": float(real["dimensionality"]),
    },
    "surrogates": {},
    "complete": {},
}

for name, sub in df[df.network != "real"].groupby("network"):
    n = len(sub)
    out["surrogates"][name] = {
        "n": int(n),
        "separation": [round(float(v), 4) for v in sub["separation"]],
        "specificity": [round(float(v), 1) for v in sub["mean_specificity"]],
        "sep_mean": round(float(sub["separation"].mean()), 4),
        "sep_sd": round(float(sub["separation"].std(ddof=1)), 4) if n > 1 else None,
        "spec_mean": round(float(sub["mean_specificity"].mean()), 1),
        "spec_sd": round(float(sub["mean_specificity"].std(ddof=1)), 1) if n > 1 else None,
        "dim_mean": round(float(sub["dimensionality"].mean()), 1),
        "p_separation": round((int((sub["separation"] >= real["separation"]).sum()) + 1) / (n + 1), 4),
        "p_specificity": round((int((sub["mean_specificity"] <= real["mean_specificity"]).sum()) + 1) / (n + 1), 4),
        "edge_overlap": round(float(sub["edge_overlap"].mean()), 4),
    }
    out["complete"][name] = bool(n >= 35)

out["target_n"] = 35
out["total_runs"] = int(len(df[df.network != "real"]))
(RES / "viz_stats.json").write_text(json.dumps(out, separators=(",", ":")))
print(json.dumps({k: {kk: vv for kk, vv in v.items() if not isinstance(vv, list)}
                  for k, v in out["surrogates"].items()}, indent=2))
print("total surrogate runs:", out["total_runs"])
