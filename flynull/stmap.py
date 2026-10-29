"""Stuerner et al. 2025 DN map: modality names, our sense -> modality mapping,
loading the per-type ranks, and scoring a simulation against them (Exp04a)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parent.parent
ST = ROOT / "data" / "external_tables" / "sturner2025"

# Our 7 driven sensory classes -> the matching modality in Stuerner's sensory
# ranking (DN_ranking_df_783_sensory_combined_byDNtype.tsv). FlyWire class
# "visual" = photoreceptors; "bilateral" = bilateral visual projection neurons.
SENSE_TO_STURNER = {
    "gustatory": "gustatory", "hygrosensory": "hygrosensory",
    "mechanosensory": "mechanosensory", "olfactory": "olfactory",
    "visual": "visual", "bilateral": "visual_projection", "unknown_sensory": None,
}
MAIN_MODALITIES = ["gustatory", "hygrosensory", "mechanosensory", "olfactory",
                   "thermosensory", "visual_projection", "visual", "ocellar"]


def load_map(dn_ids):
    """DN root_id -> Stuerner type, and the per-type modality ranks."""
    f5 = pd.read_csv(ST / "Supplemental_file5_FAFB_DNs.tsv", sep="\t", dtype={"root_id": "int64"})
    rk = pd.read_csv(ST / "DN_ranking_df_783_sensory_combined_byDNtype.tsv", sep="\t", index_col=0)
    # DNg06 is listed twice (clusters 14 and 16, different ranks); drop it rather than pick one.
    rk = rk[~rk["type"].duplicated(keep=False)].set_index("type")[MAIN_MODALITIES].astype(float)
    typ = pd.Series(dn_ids).map(f5.drop_duplicates("root_id").set_index("root_id")["type"])
    return typ.to_numpy(), rk


def score(profiles, dn_type, rk):
    """Spearman rho of type-mean |activity| vs -rank, every sense x modality."""
    rows = []
    for sense, mod in SENSE_TO_STURNER.items():
        if mod is None or sense not in profiles:
            continue
        act = pd.Series(profiles[sense]).groupby(dn_type).mean()
        act = act[act.index.isin(rk.index)]
        r = {m: spearmanr(act.to_numpy(), -rk.loc[act.index, m].to_numpy()).statistic
             for m in MAIN_MODALITIES}
        rows.append({"sense": sense, "modality": mod, "n_types": len(act),
                     "rho_own": r[mod], "best_modality": max(r, key=r.get),
                     "diagonal": max(r, key=r.get) == mod,
                     **{f"rho_{m}": v for m, v in r.items()}})
    return pd.DataFrame(rows)
