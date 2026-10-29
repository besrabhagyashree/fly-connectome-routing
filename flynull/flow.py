"""Information-flow model behind Stuerner's DN map (navis 1.5.0 TraversalModel,
Schlegel et al. 2021), in its exact shortest-path form. See experiments/
exp04b_flow_model.py for the derivation and results/exp04b_flow_settings.md."""
from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.sparse.csgraph import dijkstra
from scipy.stats import spearmanr

from .stmap import MAIN_MODALITIES, score

ROOT = Path(__file__).resolve().parent.parent
ST = ROOT / "data" / "external_tables" / "sturner2025"
MAX_W, MAX_STEPS = 0.3, 15


# ------------------------------------------------------------------ graph, seeds
def flow_graph(A: sparse.csr_matrix):
    """CSR structure of the thresholded graph and the traversal probability per
    stored edge (same order as A.data). Weight = synapses / kept input of target."""
    A = A.tocsr()
    tot = np.asarray(A.sum(0)).ravel()
    p = np.minimum(A.data / tot[A.indices] / MAX_W, 1.0)
    return A.indices, A.indptr, p


def seed_sets(meta: pd.DataFrame) -> dict[str, np.ndarray]:
    """v783 classification, one seed set per Stuerner main modality."""
    sc, cl, sub = meta["super_class"], meta["class"], meta["sub_class"]
    sens = sc.eq("sensory")
    masks = {
        "gustatory": sens & cl.eq("gustatory"),
        "hygrosensory": sens & cl.eq("hygrosensory"),
        "mechanosensory": sens & cl.eq("mechanosensory"),
        "olfactory": sens & cl.eq("olfactory"),
        "thermosensory": sens & cl.eq("thermosensory"),
        "visual_projection": sc.eq("visual_projection"),
        "visual": sens & sub.eq("photo_receptor"),
        "ocellar": sens & sub.eq("ocellar"),
    }
    return {m: np.flatnonzero(masks[m].to_numpy()) for m in MAIN_MODALITIES}


# ------------------------------------------------------------------ the model
def traverse(indices, indptr, p, seeds, runs, rng, targets):
    """Mean layer (over runs that reach it) and reach count for each target."""
    n = len(indptr) - 1
    seeds = seeds[np.diff(indptr)[seeds] > 0]  # navis drops seeds with no out-edges
    tot = np.zeros(len(targets))
    hit = np.zeros(len(targets), dtype=np.int64)
    for _ in range(runs):
        g = rng.geometric(p).astype(np.float64)
        G = sparse.csr_matrix((g, indices, indptr), shape=(n, n))
        d = dijkstra(G, directed=True, indices=seeds, min_only=True, limit=MAX_STEPS - 1 + 0.5)
        d = d[targets]
        ok = np.isfinite(d)
        tot[ok] += d[ok] + 1
        hit += ok
    with np.errstate(invalid="ignore"):
        return tot / hit, hit


def navis_literal(edges, seeds, rng, max_steps=MAX_STEPS):
    """navis 1.5.0 TraversalModel.run, one iteration, transcribed (L241-312)."""
    enc = np.array([[1, s] for s in seeds])
    this = edges
    for i in range(2, max_steps + 1):
        pre = np.isin(this[:, 0], enc[:, 1])
        post = np.isin(this[pre, 1], enc[:, 1])
        out = this[np.where(pre)[0][~post]]
        this = np.delete(this, np.where(pre)[0][post], axis=0)
        if out.size == 0:
            break
        pr = np.minimum(out[:, 2] / MAX_W, 1.0)
        tr = out[pr >= rng.random(len(pr))]
        if tr.size:
            enc = np.concatenate((enc, [[i, b] for b in np.unique(tr[:, 1]).astype(int)]))
    return enc


def selftest(n=400, deg=6, runs=3000):
    """Random graph: navis' loop vs the shortest-path form, per-node mean layer."""
    rng = np.random.default_rng(7)
    r = rng.integers(0, n, n * deg)
    c = rng.integers(0, n, n * deg)
    keep = r != c
    A = sparse.csr_matrix((rng.integers(5, 40, keep.sum()).astype(float), (r[keep], c[keep])), shape=(n, n))
    A.sum_duplicates()
    indices, indptr, p = flow_graph(A)
    coo = A.tocoo()
    tot = np.asarray(A.sum(0)).ravel()
    edges = np.column_stack([coo.row, coo.col, coo.data / tot[coo.col]])
    seeds = np.arange(5)
    lit_tot, lit_hit = np.zeros(n), np.zeros(n)
    for _ in range(runs):
        e = navis_literal(edges, seeds, rng)
        np.add.at(lit_tot, e[:, 1].astype(int), e[:, 0])
        np.add.at(lit_hit, e[:, 1].astype(int), 1)
    fast, hit = traverse(indices, indptr, p, seeds, runs, rng, np.arange(n))
    lit = lit_tot / np.maximum(lit_hit, 1)
    ok = (lit_hit > 100) & (hit > 100)
    diff = np.abs(fast[ok] - lit[ok])
    stats = {"nodes": int(ok.sum()), "max_abs_diff": float(diff.max()), "mean_abs_diff": float(diff.mean())}
    print(f"selftest: {ok.sum()} nodes, mean layer navis-literal {lit[ok].mean():.3f} vs fast "
          f"{fast[ok].mean():.3f}; max |diff| {diff.max():.3f}, mean |diff| {diff.mean():.4f}; "
          f"reach rate {lit_hit.sum()/runs:.1f} vs {hit.sum()/runs:.1f} nodes/run")
    return stats


# ------------------------------------------------------------------ DN types
def load_types(dn_ids):
    """DN root_id -> Stuerner type; published table (SD cluster and the doubled
    DNg06 removed, as in Exp04a)."""
    f5 = pd.read_csv(ST / "Supplemental_file5_FAFB_DNs.tsv", sep="\t", dtype={"root_id": "int64"})
    rk = pd.read_csv(ST / "DN_ranking_df_783_sensory_combined_byDNtype.tsv", sep="\t", index_col=0)
    rk = rk[rk["cluster"].astype(str).ne("sensory descending")]
    rk = rk[~rk["type"].duplicated(keep=False)].set_index("type")[MAIN_MODALITIES].astype(float)
    typ = pd.Series(dn_ids).map(f5.drop_duplicates("root_id").set_index("root_id")["type"])
    return typ.to_numpy(), rk


def type_ranks(layers: dict[str, np.ndarray], dn_type, rk) -> pd.DataFrame:
    """Per DN type, mean of per-neuron mean layer (neurons never reached skipped)."""
    df = pd.DataFrame(layers).assign(type=dn_type).dropna(subset=["type"])
    return df.groupby("type").mean().reindex(rk.index)


def compare(ours: pd.DataFrame, rk: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for m in MAIN_MODALITIES:
        ok = ours[m].notna() & rk[m].notna()
        rows.append({"modality": m, "n_types": int(ok.sum()),
                     "spearman": spearmanr(ours.loc[ok, m], rk.loc[ok, m]).statistic,
                     "median_abs_diff": float((ours.loc[ok, m] - rk.loc[ok, m]).abs().median()),
                     "mean_ours": ours.loc[ok, m].mean(), "mean_published": rk.loc[ok, m].mean()})
    return pd.DataFrame(rows)


def flow_map(A, seeds, readout, runs, seed, log=True):
    """Per-DN mean layer for every modality; seed*100+k seeds modality k."""
    indices, indptr, p = flow_graph(A)
    layers = {}
    for k, (m, s) in enumerate(seeds.items()):
        t = time.time()
        layers[m], hit = traverse(indices, indptr, p, s, runs, np.random.default_rng(seed * 100 + k), readout)
        if log:
            print(f"{m:18s} {runs} runs  DNs reached {np.mean(hit > 0):.1%}  ({time.time()-t:.0f}s)", flush=True)
    return layers


def sim_vs_map(profiles, dn_type, mp):
    """Exp04a's agreement (mean rho_own over senses) against a given map."""
    s = score(profiles, dn_type, mp.dropna())
    return s.rho_own.mean(), int(s.diagonal.sum())
