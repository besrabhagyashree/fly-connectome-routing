"""Step 7: cross-behaviour leakage, exactly as fixed in results/exp07_leakage_plan.md
(written 28 Oct 2026 ~17:00 IST, before any leakage number was computed).

Main test (confirmatory): channel separation from Exp01 (rate_operator.
channel_separation; lower = senses overlap more at the DNs = more leakage).
Leakage = yes if the real brain's separation is higher than both inside-only
types' at p < 0.05, p = (1 + brains with separation >= real) / (N + 1).
Standard shuffles reported alongside, not part of the rule.

Exploratory: per sense, the share of its |DN activity| on Stuerner et al. 2025
DN clusters whose dominant modality (lowest mean rank) is another sense. Only
taste, touch, humidity and visual projection neurons can be scored this way.

  python experiments/exp07_leakage.py
"""
from __future__ import annotations

import glob
from pathlib import Path

import numpy as np
import pandas as pd

from flynull import data as fw
from flynull.stmap import MAIN_MODALITIES, SENSE_TO_STURNER, ST

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
PROF = OUT / "exp04_profiles"
GENS = ["interior_degree_preserving", "interior_block_preserving", "degree_preserving"]
SCORED = ["gustatory", "mechanosensory", "hygrosensory", "bilateral"]


def separation_table():
    """Real + every surrogate's separation from steps 1 (replicates 0-34 -> 1-35) and 5."""
    old = pd.concat([pd.read_csv(OUT / f"exp01_routing_vs_gross_{t}.csv") for t in ("A", "C1", "C2")])
    real = old[old.network == "real"].iloc[0]
    old = old[old.network != "real"].copy()
    old["replicate"] = old["replicate"] + 1
    new = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(str(OUT / "exp05_exp01_j*.csv")))])
    s = pd.concat([old, new])
    s = s[s.network.isin(GENS)].drop_duplicates(["network", "replicate"])
    return float(real.separation), s


def p_greater(real, null):
    """Empirical p that the real value is higher than the surrogates'."""
    k = int((null >= real).sum())
    return k, (1 + k) / (len(null) + 1)


def cluster_dominance():
    """Per Stuerner type: its cluster's dominant modality (lowest mean rank)."""
    rk = pd.read_csv(ST / "DN_ranking_df_783_sensory_combined_byDNtype.tsv", sep="\t", index_col=0)
    rk = rk[~rk["type"].duplicated(keep=False)]  # DNg06 listed twice, as in Exp04a
    dom = rk.groupby("cluster")[MAIN_MODALITIES].mean().idxmin(axis=1)
    return rk.set_index("type")["cluster"].map(dom), dom


def off_target_share(prof, dn_dom):
    """Share of each scored sense's |DN activity| on DNs of clusters dominated by another modality."""
    ok = dn_dom.notna()
    out = {}
    for s in SCORED:
        a = np.abs(prof[s])[ok]
        out[s] = float(a[dn_dom[ok] != SENSE_TO_STURNER[s]].sum() / a.sum())
    return out


def main():
    # ---- main test
    real_sep, sep = separation_table()
    rows = []
    for g in GENS:
        x = sep.loc[sep.network == g, "separation"].to_numpy()
        k, p = p_greater(real_sep, x)
        rows.append({"network": g, "N": len(x), "real": real_sep, "mean": x.mean(), "sd": x.std(ddof=1),
                     "max": x.max(), "k_ge_real": k, "p": p, "diff": real_sep - x.mean(),
                     "z": (real_sep - x.mean()) / x.std(ddof=1)})
    main_t = pd.DataFrame(rows)
    main_t.to_csv(OUT / "exp07_separation.csv", index=False)
    inside = main_t[main_t.network.str.startswith("interior")]
    verdict = bool((inside.p < 0.05).all())
    print(main_t.round(5).to_string(index=False))
    print(f"\nRule (real separation > both inside-only types, p < 0.05): leakage = {'YES' if verdict else 'NO'}\n")

    # ---- exploratory
    c = fw.load()
    readout = np.flatnonzero(c.meta["super_class"].eq("descending").to_numpy())
    f5 = pd.read_csv(ST / "Supplemental_file5_FAFB_DNs.tsv", sep="\t", dtype={"root_id": "int64"})
    dn_type = pd.Series(c.ids[readout].astype("int64")).map(
        f5.drop_duplicates("root_id").set_index("root_id")["type"])
    type_dom, dom = cluster_dominance()
    print("cluster -> dominant modality:", dom.to_dict())
    dn_dom = dn_type.map(type_dom).to_numpy(dtype=object)
    dn_dom = pd.Series(dn_dom)

    real = off_target_share(dict(np.load(PROF / "real_0.npz")), dn_dom)
    ex = []
    for g in GENS:
        files = sorted(PROF.glob(f"{g}_*.npz"))
        vals = pd.DataFrame([off_target_share(dict(np.load(f)), dn_dom) for f in files])
        for s in SCORED:
            k = int((vals[s] <= real[s]).sum())  # leakage: real should leak LESS
            ex.append({"sense": s, "network": g, "N": len(vals), "real": real[s], "mean": vals[s].mean(),
                       "sd": vals[s].std(ddof=1), "min": vals[s].min(), "k_le_real": k,
                       "p_real_leaks_less": (1 + k) / (len(vals) + 1)})
    ex = pd.DataFrame(ex)
    ex.to_csv(OUT / "exp07_offtarget_exploratory.csv", index=False)
    print("\nExploratory (not confirmatory): share of |DN activity| on other-modality clusters")
    print(ex.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
