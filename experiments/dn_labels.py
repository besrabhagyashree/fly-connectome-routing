"""Step 3: label the descending neurons (DNs) each sense reaches.

Two stages:

  python dn_labels.py run      re-run ONLY the real network with the exact Exp01
                               settings and dump per-sense DN activity
                               -> results/dn_labels_per_sense_raw.csv
  python dn_labels.py label    join those DNs to published identities
                               (Stuerner et al. 2025; FlyWire annotations,
                               Schlegel et al. 2024) and to published behaviours
                               -> results/dn_labels_per_sense.csv
                               -> results/dn_labels_summary.md

Which DNs "carry the signal"
----------------------------
Exp01 does not threshold DNs. Its "specificity" is the participation ratio (PR)
of each sense's DN activity profile -- the effective number of DNs carrying the
signal (rate_operator.participation_ratio). The mean PR over the 7 senses is
17.1. To turn that effective number into a concrete list without inventing a
new threshold, we take, per sense, the top round(PR) DNs by |activity|. Every DN
above Exp01's own activity threshold (|x| > 1e-3, rate_operator.calibrate_gain)
is also kept in the raw file, flagged `in_top_pr`.

Nothing in exp01_routing_vs_gross.py, nulls.py or measures.py is modified; they
are imported read-only.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from flynull.stmap import MAIN_MODALITIES, SENSE_TO_STURNER  # noqa: F401

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

ROOT = HERE.parent
OUT = ROOT / "results"
EXT = ROOT / "data" / "external_tables"
RAW = OUT / "dn_labels_per_sense_raw.csv"
FULL = OUT / "dn_labels_full_profiles.csv"
ACTIVE_THRESH = 1e-3  # Exp01's activity threshold (rate_operator.calibrate_gain)


# --------------------------------------------------------------------- stage 1
def run_real(steps: int = 60, target_active: float = 0.05) -> pd.DataFrame:
    from flynull import data as fw
    from flynull import rate_operator as op
    from flynull.routing import sensory_channels

    c = fw.load()
    print(c.summary(), flush=True)
    meta = c.meta
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    print(f"channels={ {k: len(v) for k, v in channels.items()} }  readout={len(readout)}", flush=True)

    # Exactly Exp01.evaluate(): normalise, calibrate gain on all channels, then run.
    Wn, rho = op.normalise(c.W)
    cal_idx = np.concatenate(list(channels.values()))
    gain, achieved = op.calibrate_gain(Wn, cal_idx, target_active=target_active, steps=steps)
    print(f"rho_raw={rho:.2f} gain={gain:g} calibrated_active={achieved:.4f}", flush=True)

    rows, prs, full = [], {}, {"root_id": c.ids[readout].astype("int64")}
    for name, idx in channels.items():
        final = op.run(Wn, idx, steps=steps, gain=gain)[-1]
        act = final[readout].astype(np.float64)
        full[name] = act
        prof = np.abs(act)
        nrm = np.linalg.norm(prof)
        prof_n = prof / nrm if nrm > 0 else prof
        pr = op.participation_ratio(prof_n)
        prs[name] = pr
        k = int(round(pr))
        order = np.argsort(-prof)
        rank = np.empty(len(order), dtype=int)
        rank[order] = np.arange(1, len(order) + 1)
        share = prof / prof.sum() if prof.sum() > 0 else prof
        keep = (prof > ACTIVE_THRESH) | (rank <= k)
        for j in np.flatnonzero(keep):
            rows.append({
                "sense": name, "n_driven": len(idx), "pr_specificity": pr, "k_top": k,
                "root_id": int(c.ids[readout[j]]), "activity": float(act[j]),
                "abs_activity": float(prof[j]), "share_of_abs": float(share[j]),
                "rank": int(rank[j]), "in_top_pr": bool(rank[j] <= k),
                "above_exp01_thresh": bool(prof[j] > ACTIVE_THRESH),
            })
        print(f"{name:16s} PR={pr:6.2f}  top={k}  above_thresh={(prof > ACTIVE_THRESH).sum()}", flush=True)
    mean_pr = float(np.mean(list(prs.values())))
    print(f"mean specificity (PR) = {mean_pr:.3f}  (Exp01 real: 17.099)", flush=True)
    df = pd.DataFrame(rows).sort_values(["sense", "rank"])
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW, index=False)
    # Full signed activity of all 1,305 DNs per sense, to rank any DN of interest.
    pd.DataFrame(full).to_csv(FULL, index=False)
    return df


# --------------------------------------------------------------------- stage 2
# Published DN -> behaviour links. `pattern` is matched (case-insensitive) against
# the Stuerner type, the type with its _a/_b suffix removed, Namiki_name and each
# synonym. `src` says where the link comes from:
#   file4  = the reference is listed in Stuerner et al. 2025 Supplemental file 4
#   lit    = well-established literature link supplied for this step (not listed
#            in file 4); the paper is cited but was not re-read here.
# Anything not matched is "unknown". No behaviour is inferred from anatomy.
BEHAVIOUR_LINKS = [
    ("MDN", "backward walking (moonwalker)", "Bidaye et al. 2014 Science, doi:10.1126/science.1249964", "file4"),
    ("DNp50", "backward walking (moonwalker)", "Bidaye et al. 2014 Science, doi:10.1126/science.1249964", "file4"),
    ("DNp01", "escape take-off (Giant Fiber)", "von Reyn et al. 2014 Nat Neurosci; GF identity: file4 doi:10.1007/BF00603798", "lit"),
    ("DNp09", "forward walking / object-directed stopping", "Bidaye et al. 2020 Neuron; Braun et al. 2024 Nature", "lit"),
    ("aDN1", "antennal grooming", "Hampel et al. 2015 eLife", "lit"),
    ("aDN2", "antennal grooming", "Hampel et al. 2015 eLife", "lit"),
    ("DNg11", "front-leg rubbing (anterior grooming)", "Cande et al. 2018 eLife; Guo et al. 2022 Curr Biol", "lit"),
    ("DNg12", "head grooming (anterior grooming)", "Cande et al. 2018 eLife; Guo et al. 2022 Curr Biol", "lit"),
    ("DNa01", "steering (turning while walking)", "Rayshubskiy et al. 2020 bioRxiv", "lit"),
    ("DNa02", "steering (turning while walking)", "Rayshubskiy et al. 2020 bioRxiv", "lit"),
    ("DNp42", "backward walking", "Cande et al. 2018 eLife; Sen et al. 2019", "lit"),
    ("oviDN", "egg-laying (oviposition)", "Wang et al. 2020 Nature", "lit"),
    ("DNg02", "wing-stroke amplitude / flight power", "Namiki et al. 2022 Curr Biol", "lit"),
    ("DNb05", "steering", "Cande et al. 2018 eLife; Stuerner et al. 2025 Nature", "lit"),
    ("DNb06", "steering", "Cande et al. 2018 eLife; Stuerner et al. 2025 Nature", "lit"),
    ("DNg13", "turning", "Cande et al. 2018 eLife", "lit"),
    # Links whose reference is listed in Stuerner file 4:
    ("DSOG1", "feeding restraint (GABAergic SEZ descending neuron)",
     "Pool et al. 2014 Neuron (file4: Neuron S0896-6273(14)00392-4)", "file4"),
    ("DNHS1", "encodes visual self-motion (optic flow)", "Suver et al. 2016 J Neurosci 36:11768 (file4)", "file4"),
    ("DNOVS1", "encodes visual self-motion (optic flow)", "Suver et al. 2016 J Neurosci 36:11768 (file4)", "file4"),
    ("DNOVS2", "encodes visual self-motion (optic flow)", "Suver et al. 2016 J Neurosci 36:11768 (file4)", "file4"),
]



NOTES = """\
Plain-language reading (numbers from the tables above; ranks are out of 1,305 DNs).

1. **The ~17 average hides very uneven routing.** Mechanosensory (PR 41), bilateral visual
   projection neurons (39), unknown sensory (22) and gustatory (13) spread over many DNs;
   hygrosensory (2), photoreceptors (`visual`, 1.8) and olfactory (1.05) collapse onto 1-2 DN types.

2. **Identity is almost complete; behaviour is not.** 1,303 of 1,305 DNs match Stürner file 5 by
   root_id, and every DN in the per-sense lists is identified. But only a handful of the DN types
   reached have a published behaviour in the sources used here; most are SEZ types (DNg/DNge/DNpe)
   whose function has not been tested. They are marked "unknown", not guessed.

3. **Gustatory -> gustatory DNs, but not to a DN with a published feeding role.** All 13 listed DNs
   are SEZ types (DNg67, DNg103, DNpe049, DNg65, DNpe007...); 85% have gustatory as their closest
   sense in Stürner's own ranking and 69% sit in Stürner's gustatory-dominated clusters 1 and 2.
   So the routing agrees with Stürner's anatomy. The only feeding-labelled DNs in our sources are
   the DSOG1 pair (feeding restraint; Pool et al. 2014): DNg70 ranks 73 and DNg98 ranks 109 for
   gustatory, i.e. outside the top 13. We cannot say anything about *sugar*: FlyWire's
   `gustatory` class pools all gustatory receptor neurons (sweet, bitter, water, ...).

4. **Mechanosensory -> mechanosensory DNs, but not the known grooming DNs.** 100% of the 41 listed
   DNs are in mechanosensory-dominated Stürner clusters (3, 4, 10, 13, 14). The top DN is DNg15
   (synonym AMMC-Db5, an antennal mechanosensory/motor-centre DN) and DNp33 (AMMC-D1) is in the list.
   The grooming DNs are not: aDN2 (DNge078) ranks 75, aDN1 (DNg62) 262, DNg12 >= 260, DNg11 411.
   The Giant Fiber (DNp01) ranks 70.

5. **Photoreceptors (`visual`) -> DNp28**, in Stürner's ocellar-dominated cluster 5. Just outside
   the 2-DN list are DNb06 (steering; rank 4), DNOVS1 (DNp20; rank 6) and DNOVS2 (DNp22; rank 13),
   which encode visual self-motion (Suver et al. 2016) - a sensible near-hit. The escape DN DNp01
   (Giant Fiber) ranks 210: this run drives *all* photoreceptors, not a looming stimulus, so
   it is not a test of looming -> escape.

6. **Bilateral visual projection neurons -> visual-projection DNs.** 100% of listed DNs have visual
   projection as their closest sense (clusters 6 and 16). DNg11 (front-leg rubbing) is in the list;
   DNHS1 (DNp15, self-motion) ranks 47.

7. **Hygrosensory -> DNb05** (both copies; steering, per Cande 2018 / Stürner 2025). Stürner's
   ranking puts DNb05 closest to visual projection neurons, so the strict cluster test fails.
   **Olfactory -> DNc01** (cluster 7, whose best sense is visual projection and second-best
   olfactory); DNb05 is olfactory's rank-2 DN.

8. **Not reached by any sense** (rank > 100 in every sense): MDN (backward walking, best 217),
   DNp09 (130), DNg02 (132), DNa02 (108). DNa01 is closest for unknown_sensory (94).
   **Unexpected near-hits:** two egg-laying DNs rank high for olfactory - oviDNv (DNpe046) rank 10,
   oviDNb' (DNpe038) rank 29 - and DNp42 (backward walking) ranks 46 for olfactory. None is
   inside olfactory's 1-DN list, and we draw no behavioural conclusion from this.

### Caveats
- DN activity in this regime is tiny: only 1 DN (mechanosensory) crosses Exp01's 1e-3 active
  threshold. The lists show where each sense's signal is *concentrated*, not DNs that would fire.
- The list length round(PR) is our way of turning Exp01's effective number into names; it is not
  a threshold from Exp01. Full ranks are in `results/dn_labels_full_profiles.csv`.
- "Cluster matches sense" uses the lowest mean rank in Stürner's published ranking table; that
  summary step is ours, the ranks are theirs.
- `lit` behaviour links are cited from the literature but were not re-read against the papers in
  this step. DNp13 is NOT labelled oviDN: Stürner lists it as pMN1 and gives the oviDNs their own
  types. The DNp42 backward-walking citation (Cande 2018 / Sen 2019) should be checked.
- One frozen operator, one operating point, one replicate; FlyWire sensory classes are coarse.
"""


def _read_tsv(path: Path, **kw) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", low_memory=False, encoding="utf-8",
                       encoding_errors="replace", **kw)


def _names(row) -> list[str]:
    out = []
    for col in ("type", "Namiki_name"):
        v = row.get(col)
        if isinstance(v, str) and v:
            out += [v, re.sub(r"_[a-z]$", "", v)]
    syn = row.get("synonyms")
    if isinstance(syn, str):
        out += [t.strip() for t in syn.split(";") if t.strip()]
    return out


def _behaviour(row):
    names = [n.lower() for n in _names(row)]
    for pat, beh, cit, src in BEHAVIOUR_LINKS:
        p = pat.lower()
        if p == "ovidn":
            hit = any(n.startswith("ovidn") for n in names)
        else:
            hit = p in names
        if hit:
            return beh, cit, src
    return "unknown", "", ""


def label():
    raw = pd.read_csv(RAW)
    st = EXT / "sturner2025"
    f5 = _read_tsv(st / "Supplemental_file5_FAFB_DNs.tsv")
    f4 = _read_tsv(st / "Supplemental_file4_DN_identification.tsv")
    rk = _read_tsv(st / "DN_ranking_df_783_sensory_combined_byDNtype.tsv", index_col=0)
    f5["root_id"] = f5["root_id"].astype("int64")
    f5 = f5.drop_duplicates("root_id")

    # Fallback: FlyWire v783 annotations (Schlegel et al. 2024).
    fwa_path = EXT / "flywire_annotations" / "Supplemental_file1_neuron_annotations.tsv"
    fwa = _read_tsv(fwa_path, usecols=lambda c: c in {"root_id", "super_class", "cell_type",
                                                      "hemibrain_type", "top_nt", "side"})
    fwa = fwa.dropna(subset=["root_id"])
    fwa["root_id"] = fwa["root_id"].astype("int64")
    fwa = fwa.drop_duplicates("root_id").set_index("root_id")

    # Stuerner sensory ranking: per DN type rank for each modality (lower = fewer
    # layers from that sense). Cluster signature = mean rank per modality.
    rk = rk[rk["cluster"].astype(str) != "sensory descending"].copy()
    rk["cluster"] = rk["cluster"].astype(str)
    clus_mean = rk.groupby("cluster")[MAIN_MODALITIES].mean()
    clus_dom = clus_mean.idxmin(axis=1)
    rk_by_type = rk.drop_duplicates("type").set_index("type")

    f4 = f4.drop_duplicates("dn_type").set_index("dn_type")

    # ---- join
    all_dn_ids = None
    df = raw.merge(f5[["root_id", "type", "Namiki_name", "synonyms", "cluster", "side",
                       "soma_location", "neuropil"]], on="root_id", how="left")
    df["in_sturner"] = df["type"].notna()
    fb = df["root_id"].map(fwa["cell_type"]) if "cell_type" in fwa else pd.Series(np.nan, index=df.index)
    df["flywire_cell_type"] = fb
    df["flywire_super_class"] = df["root_id"].map(fwa["super_class"]) if "super_class" in fwa else np.nan
    # Second fallback: FlyWire Codex consolidated cell types already in our meta.
    from flynull import data as fw
    meta_all = pd.read_parquet(fw.CACHE / "flywire783_minsyn5.meta.parquet").set_index("root_id")
    codex = df["root_id"].map(meta_all["primary_type"])
    df["label_source"] = np.where(df["in_sturner"], "Stuerner2025_file5",
                                  np.where(df["flywire_cell_type"].notna(), "FlyWire_annotations",
                                           np.where(codex.notna(), "FlyWire_codex_types", "none")))
    df["type_final"] = df["type"].fillna(df["flywire_cell_type"]).fillna(codex)

    beh = df.apply(lambda r: _behaviour({"type": r["type_final"], "Namiki_name": r["Namiki_name"],
                                         "synonyms": r["synonyms"]}), axis=1)
    df["behaviour"] = [b[0] for b in beh]
    df["citation"] = [b[1] for b in beh]
    df["behaviour_source"] = [b[2] for b in beh]

    def f4_ref(r):
        for n in _names({"type": r["type_final"], "Namiki_name": r["Namiki_name"]}):
            if n in f4.index and isinstance(f4.loc[n, "reference"], str):
                return f4.loc[n, "reference"]
        return ""
    df["file4_reference"] = df.apply(f4_ref, axis=1)

    df["cluster"] = df["cluster"].astype("string")
    df["cluster_dominant_modality"] = df["cluster"].map(clus_dom)
    df["sturner_modality_for_sense"] = df["sense"].map(SENSE_TO_STURNER)

    def dn_rank(r):
        t, m = r["type_final"], r["sturner_modality_for_sense"]
        if isinstance(t, str) and t in rk_by_type.index and isinstance(m, str):
            return float(rk_by_type.loc[t, m])
        return np.nan

    def dn_best(r):
        t = r["type_final"]
        if isinstance(t, str) and t in rk_by_type.index:
            return str(rk_by_type.loc[t, MAIN_MODALITIES].astype(float).idxmin())
        return np.nan
    df["sturner_rank_for_sense"] = df.apply(dn_rank, axis=1)
    df["dn_best_modality"] = df.apply(dn_best, axis=1)
    df["cluster_matches_sense"] = (df["cluster_dominant_modality"] == df["sturner_modality_for_sense"]) \
        & df["sturner_modality_for_sense"].notna()
    df["dn_best_matches_sense"] = (df["dn_best_modality"] == df["sturner_modality_for_sense"]) \
        & df["sturner_modality_for_sense"].notna()

    cols = ["sense", "rank", "in_top_pr", "root_id", "type_final", "Namiki_name", "synonyms",
            "cluster", "cluster_dominant_modality", "dn_best_modality", "sturner_rank_for_sense",
            "cluster_matches_sense", "dn_best_matches_sense", "behaviour", "citation",
            "behaviour_source", "file4_reference", "label_source", "flywire_cell_type",
            "activity", "abs_activity", "share_of_abs", "pr_specificity", "k_top",
            "above_exp01_thresh", "side"]
    df = df[cols].rename(columns={"type_final": "type"}).sort_values(["sense", "rank"])
    df.to_csv(OUT / "dn_labels_per_sense.csv", index=False)

    # ---- match rate over ALL 1,305 DNs in our readout, and over the reached set
    from flynull import data as fw
    meta = pd.read_parquet(fw.CACHE / "flywire783_minsyn5.meta.parquet")
    dn_ids = meta.loc[meta["super_class"].eq("descending"), "root_id"].astype("int64")
    s5 = set(f5["root_id"])
    all_rate = dn_ids.isin(s5).mean()
    fb_all = dn_ids[~dn_ids.isin(s5)].isin(fwa.index[fwa["cell_type"].notna()]).mean() \
        if (~dn_ids.isin(s5)).any() else float("nan")
    top = df[df["in_top_pr"]]

    # ---- per-sense summary over the top-round(PR) DNs
    srows = []
    for sense, g in top.groupby("sense"):
        has_mod = g["sturner_modality_for_sense"].notna() if "sturner_modality_for_sense" in g else None
        srows.append({
            "sense": sense, "PR_specificity": round(g["pr_specificity"].iloc[0], 2),
            "n_DNs_listed": len(g), "unique_types": g["type"].nunique(),
            "frac_identified": round(g["type"].notna().mean(), 2),
            "frac_with_behaviour": round((g["behaviour"] != "unknown").mean(), 2),
            "frac_cluster_matches_sense": (round(g["cluster_matches_sense"].mean(), 2)
                                           if SENSE_TO_STURNER[sense] else "n/a"),
            "frac_DN_best_modality_matches": (round(g["dn_best_matches_sense"].mean(), 2)
                                              if SENSE_TO_STURNER[sense] else "n/a"),
            "behaviours": "; ".join(sorted({f"{t}: {b}" for t, b in zip(g["type"], g["behaviour"])
                                            if b != "unknown"})) or "none",
            "types": ", ".join(pd.unique(g["type"].fillna("unidentified").astype(str))),
            "clusters": ", ".join(f"{k}x{v}" for k, v in
                                  g["cluster"].fillna("NA").value_counts().items()),
        })
    summ = pd.DataFrame(srows)
    summ.to_csv(OUT / "dn_labels_summary_table.csv", index=False)

    # Where do the known behaviour DNs sit for each sense? (rank among 1,305)
    known = df[df["behaviour"] != "unknown"].groupby(["sense", "type", "behaviour"])["rank"].min()

    # ---- expected-pair check: where do DNs with a published behaviour rank in
    # each sense's full 1,305-DN profile? (rank 1 = most activity)
    full = pd.read_csv(FULL)
    senses = [c for c in full.columns if c != "root_id"]
    rank_tab = full[["root_id"]].copy()
    for sname in senses:
        rank_tab[sname] = full[sname].abs().rank(ascending=False, method="min").astype(int)
    f5b = f5.copy()
    bb = f5b.apply(_behaviour, axis=1)
    f5b["behaviour"] = [b[0] for b in bb]
    f5b["citation"] = [b[1] for b in bb]
    kb = f5b[f5b["behaviour"] != "unknown"].merge(rank_tab, on="root_id", how="inner")
    kb["label"] = kb["type"].astype(str) + np.where(kb["Namiki_name"].notna() & (kb["Namiki_name"] != kb["type"]),
                                                    " (" + kb["Namiki_name"].astype(str) + ")", "")
    kb["label"] = kb["label"] + np.where(kb["synonyms"].notna(), " [" + kb["synonyms"].astype(str) + "]", "")
    known_rank = kb.groupby(["label", "behaviour", "citation"])[senses].min().reset_index()
    known_rank.to_csv(OUT / "dn_labels_known_behaviour_ranks.csv", index=False)
    print(known_rank.drop(columns=["citation"]).to_string(index=False))

    _write_md(summ, clus_mean, clus_dom, all_rate, fb_all, len(dn_ids), top, raw, known_rank, senses)
    print(summ.drop(columns=["types", "behaviours", "clusters"]).to_string(index=False))
    print(f"\nmatch rate (all {len(dn_ids)} DNs -> Stuerner file5): {all_rate:.3f}; "
          f"fallback FlyWire cell_type for misses: {fb_all:.3f}")
    print(f"match rate (DNs listed in top-PR sets): {top['label_source'].eq('Stuerner2025_file5').mean():.3f}")
    return df, summ


def _write_md(summ, clus_mean, clus_dom, all_rate, fb_all, n_dn, top, raw, known_rank, senses):
    L = []
    L.append("# Step 3 — which descending neurons each sense reaches, and what they are known to do\n")
    L.append("Generated by `experiments/dn_labels.py` (real FlyWire v783 network only, exact Exp01 settings: "
             "spectral radius normalised to 0.95, gain calibrated on all 7 sensory classes, 60 steps, "
             "leak 0.3).\n")
    L.append("## How the DN lists were made\n")
    L.append("Exp01's *specificity* is the participation ratio (PR) of each sense's activity profile over the "
             "1,305 descending neurons — an *effective number* of DNs, not a thresholded count. The re-run "
             f"reproduces Exp01 exactly: mean PR = {raw.groupby('sense')['pr_specificity'].first().mean():.3f} "
             "(Exp01: 17.099). For each sense we list the top round(PR) DNs by |activity|; no new threshold "
             "was introduced. Note: almost no DN crosses Exp01's own 1e-3 'active' threshold (only 1 DN, for "
             "mechanosensory), so these lists describe *where the signal is concentrated*, not DNs that are "
             "strongly driven.\n")
    L.append("## Identity match\n")
    L.append(f"- {all_rate:.1%} of all {n_dn} FlyWire v783 descending neurons match a row of Stürner et al. 2025 "
             "Supplemental file 5 by root_id.")
    L.append(f"- {top['label_source'].eq('Stuerner2025_file5').mean():.1%} of the DNs in the per-sense lists match; "
             f"fallback to FlyWire cell_type (Schlegel et al. 2024) covers {fb_all:.1%} of the overall misses.\n")
    L.append("## Per-sense summary\n")
    L.append("`cluster matches` = the DN's Stürner cluster has the driven sense as its lowest mean "
             "sensory rank (fewest layers from that sense) in Stürner's published ranking table. "
             "`DN best matches` = the same test for the DN's own type row. These two use Stürner's ranks only.\n")
    L.append("| sense | PR | DNs listed | identified | with known behaviour | cluster matches sense | DN best modality matches | known-behaviour DNs |")
    L.append("|---|---|---|---|---|---|---|---|")
    for _, r in summ.iterrows():
        L.append(f"| {r['sense']} | {r['PR_specificity']} | {r['n_DNs_listed']} | {r['frac_identified']:.0%} | "
                 f"{r['frac_with_behaviour']:.0%} | {r['frac_cluster_matches_sense']} | "
                 f"{r['frac_DN_best_modality_matches']} | {r['behaviours']} |")
    L.append("\n### DN types per sense (in activity order)\n")
    for _, r in summ.iterrows():
        L.append(f"- **{r['sense']}**: {r['types']}  \n  clusters: {r['clusters']}")
    L.append("\n## Stürner cluster signatures (mean sensory rank; lower = closer to that sense)\n")
    L.append("| cluster | dominant modality | " + " | ".join(MAIN_MODALITIES) + " |")
    L.append("|---|---|" + "---|" * len(MAIN_MODALITIES))
    for c in sorted(clus_mean.index, key=lambda x: int(x)):
        L.append(f"| {c} | {clus_dom[c]} | " + " | ".join(f"{v:.1f}" for v in clus_mean.loc[c]) + " |")
    L.append("\n## Sources\n")
    L.append("- Stürner T. et al. 2025, *Comparative connectomics of Drosophila descending and ascending neurons*, "
             "Nature — github.com/flyconnectome/2023neckconnective (Supplemental files 4, 5; "
             "code/DN_ranking_df_783_sensory_combined_byDNtype.tsv).")
    L.append("- Schlegel P. et al. 2024 Nature; Dorkenwald S. et al. 2024 Nature — FlyWire v783 annotations "
             "(github.com/flyconnectome/flywire_annotations).")
    L.append("- Behaviour citations are per row in `results/dn_labels_per_sense.csv` (`citation`, "
             "`behaviour_source`: `file4` = reference listed in Stürner file 4; `lit` = established "
             "literature link, cited but not re-verified against the paper text in this step).")
    L.append("\n## Interpretation notes\n")
    L.append(NOTES)
    (OUT / "dn_labels_summary.md").write_text("\n".join(L), encoding="utf-8")
if __name__ == "__main__":
    stage = sys.argv[1] if len(sys.argv) > 1 else "run"
    if stage == "run":
        run_real()
    else:
        label()
