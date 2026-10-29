"""The test this reproduction was for: give Shiu's spiking model a rewired connectome.

Our routing result (a sense reaches ~17 descending neurons in the real wiring,
~101-122 after rewiring) comes from our own rate model. If it also appears in the
authors' published, independently reproduced spiking model, it is not an artefact
of our modelling choices.

Steps:
  1. read their Connectivity_783.parquet (15.1M edges)
  2. rewire it degree-preservingly with flynull/nulls.py, keeping Dale's law
  3. write it back in their exact format
  4. run THEIR model on it, sugar neurons excited
  5. compare how widely the signal spreads over descending neurons

  python rewire_shiu_run.py --stage rewire
  python rewire_shiu_run.py --stage run
  python rewire_shiu_run.py --stage compare
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
OUT = ROOT / "results" / "repro_shiu"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flynull import nulls  # noqa: E402

CON783 = REPO / "Connectivity_783.parquet"
REWIRED = OUT / "Connectivity_783_rewired.parquet"
MN9 = 720575940660219265


def stage_rewire(swaps_per_edge: int, seed: int):
    t0 = time.time()
    df = pd.read_parquet(CON783)
    print(f"loaded {len(df):,} edges ({time.time()-t0:.0f}s)", flush=True)

    pre = df["Presynaptic_Index"].to_numpy(np.int64)
    post = df["Postsynaptic_Index"].to_numpy(np.int64)
    w = df["Connectivity"].to_numpy(np.float64)
    n = int(max(pre.max(), post.max())) + 1

    # Sign is a property of the presynaptic neuron in their file; keep it that way.
    sign_by_pre = np.ones(n)
    exc = df["Excitatory"].to_numpy(np.float64)
    first = ~pd.Index(pre).duplicated()
    sign_by_pre[pre[first]] = exc[first]

    W = sparse.csr_matrix((w * sign_by_pre[pre], (pre, post)), shape=(n, n))
    print(f"matrix {W.shape[0]:,} x {W.shape[1]:,}, {W.nnz:,} edges", flush=True)

    rng = np.random.default_rng(seed)
    t1 = time.time()
    S = nulls.degree_preserving(W, rng, sign=sign_by_pre, swaps_per_edge=swaps_per_edge)
    print(f"rewired in {time.time()-t1:.0f}s", flush=True)

    checks = nulls.check_preserved(W, S)
    print("invariants:", {k: v for k, v in checks.items()})
    if not (checks["out_degree_equal"] and checks["in_degree_equal"]):
        raise SystemExit("degree sequence broken - refusing to write")

    coo = S.tocoo()
    ids = pd.Series(df["Presynaptic_ID"].to_numpy(), index=pre).groupby(level=0).first()
    ids_post = pd.Series(df["Postsynaptic_ID"].to_numpy(), index=post).groupby(level=0).first()
    id_lookup = ids.combine_first(ids_post)

    out = pd.DataFrame({
        "Presynaptic_ID": id_lookup.reindex(coo.row).to_numpy(),
        "Postsynaptic_ID": id_lookup.reindex(coo.col).to_numpy(),
        "Presynaptic_Index": coo.row,
        "Postsynaptic_Index": coo.col,
        "Connectivity": np.abs(coo.data).astype(np.int64),
        "Excitatory": np.sign(coo.data).astype(np.int64),
    })
    out["Excitatory x Connectivity"] = out["Excitatory"] * out["Connectivity"]
    out = out.dropna(subset=["Presynaptic_ID", "Postsynaptic_ID"])
    out["Presynaptic_ID"] = out["Presynaptic_ID"].astype(np.int64)
    out["Postsynaptic_ID"] = out["Postsynaptic_ID"].astype(np.int64)
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_parquet(REWIRED, index=False)
    print(f"wrote {REWIRED} ({REWIRED.stat().st_size/1e6:.0f} MB, {len(out):,} edges)")


def stage_run(n_run: int, n_proc: int):
    from model import default_params, run_exp
    from repro_shiu import NEU_SUGAR

    params = dict(default_params)
    params["n_run"] = n_run
    t0 = time.time()
    run_exp(exp_name="sugarR_783_rewired", neu_exc=NEU_SUGAR, path_res=str(OUT),
            path_comp=str(REPO / "Completeness_783.csv"), path_con=str(REWIRED),
            params=params, n_proc=n_proc, force_overwrite=True)
    print(f"rewired-network run finished in {time.time()-t0:.0f}s")


def participation_ratio(v):
    p = np.abs(np.asarray(v, dtype=float))
    s = p.sum()
    if s == 0:
        return 0.0
    p = p / s
    return float(1.0 / np.sum(p ** 2))


def stage_compare(n_run: int):
    from model import default_params
    import utils as utl

    meta = pd.read_parquet(ROOT / "data" / "cache" / "flywire783_minsyn5.meta.parquet")
    dn = meta.loc[meta["super_class"].eq("descending"), "root_id"].astype("int64")
    print(f"descending neurons in v783 annotation: {len(dn):,}")

    def rates(path):
        df = utl.load_exps([str(path)])
        r, _ = utl.get_rate(df, t_run=default_params["t_run"], n_run=n_run)
        s = pd.to_numeric(r.iloc[:, 0], errors="coerce")
        s.index = s.index.astype("int64")
        return s

    real = rates(OUT / "sugarR_783.parquet")
    rew = rates(OUT / "sugarR_783_rewired.parquet")

    rows = []
    for label, s in (("real v783", real), ("rewired v783", rew)):
        prof = s.reindex(dn).fillna(0.0)
        rows.append({
            "network": label,
            "descending_active": int((prof > 0).sum()),
            "spread_effective_neurons": round(participation_ratio(prof), 1),
            "descending_mean_hz": round(float(prof.mean()), 2),
            "whole_brain_active": int((s > 0).sum()),
            "mn9_hz": round(float(s.get(MN9, 0.0)), 1),
        })
    out = pd.DataFrame(rows)
    print()
    print(out.to_string(index=False))
    out.to_csv(OUT / "rewiring_in_spiking_model.csv", index=False)
    print(f"\nwrote {OUT / 'rewiring_in_spiking_model.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["rewire", "run", "compare"], required=True)
    ap.add_argument("--swaps-per-edge", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1000)
    ap.add_argument("--n-run", type=int, default=3)
    ap.add_argument("--n-proc", type=int, default=2)
    a = ap.parse_args()
    if a.stage == "rewire":
        stage_rewire(a.swaps_per_edge, a.seed)
    elif a.stage == "run":
        stage_run(a.n_run, a.n_proc)
    else:
        stage_compare(a.n_run)
