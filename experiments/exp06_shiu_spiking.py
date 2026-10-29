"""Step 6: the step 1 focus test in Shiu et al. 2024's spiking model, following
results/exp06_plan.md (fixed before any step 6 shuffled brain was simulated).

For each brain: build the surrogate on THEIR v783 edge list (15.1M edges, sign
from the presynaptic neuron = Dale's law), with the step 1 boundary (sensory
channels + descending neurons, from our FlyWire annotation) frozen for the
inside-only types; check invariants and boundary; write it in their format; run
THEIR model (20 v783 sugar GRNs at 200 Hz, default params, 3 trials of 1 s);
score the spread (participation ratio) of the descending rate profile.

Resumable: brains whose rates file exists are scored, not re-simulated.
Runs in .venv-brian (Brian2 2.9, numpy 1.26):

  .venv-brian/Scripts/python.exe experiments/exp06_shiu_spiking.py run
  .venv-brian/Scripts/python.exe experiments/exp06_shiu_spiking.py summary
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
sys.path[:0] = [str(REPO), str(ROOT), str(Path(__file__).resolve().parent)]

from flynull import nulls  # noqa: E402
from flynull.routing import boundary_masks, make_surrogate, sensory_channels  # noqa: E402
from rewire_shiu_run import participation_ratio  # noqa: E402

OUT = ROOT / "results" / "exp06"
CSV = ROOT / "results" / "exp06_shiu.csv"
CON = REPO / "Connectivity_783.parquet"
COMP = REPO / "Completeness_783.csv"
TMP = OUT / "_surrogate.parquet"
META = ROOT / "data" / "cache" / "flywire783_minsyn5.meta.parquet"

# exp06_plan.md: N per type, fixed before launch.
PLAN = {"interior_degree_preserving": 50, "interior_block_preserving": 50, "degree_preserving": 19}
SWAPS, N_TRIALS = 10, 3
MN9 = 720575940660219265


def sugar_783(ids):
    from repro_shiu import NEU_SUGAR
    have = set(ids)
    return [n for n in NEU_SUGAR if int(n) in have]


def schedule():
    """Real first, then round-robin over replicates so partial results stay balanced."""
    jobs = [("real", 0)]
    for r in range(1, max(PLAN.values()) + 1):
        jobs += [(g, r) for g, n in PLAN.items() if r <= n]
    return jobs


def load():
    df = pd.read_parquet(CON)
    ids = pd.read_csv(COMP, index_col=0).index.astype("int64").to_numpy()
    n = len(ids)
    pre = df["Presynaptic_Index"].to_numpy(np.int64)
    post = df["Postsynaptic_Index"].to_numpy(np.int64)
    sign = np.ones(n)
    first = ~pd.Index(pre).duplicated()
    sign[pre[first]] = df["Excitatory"].to_numpy(np.float64)[first]
    W = sparse.csr_matrix((df["Connectivity"].to_numpy(np.float64) * sign[pre], (pre, post)), shape=(n, n))
    meta = pd.read_parquet(META)
    meta = meta.set_index(meta["root_id"].astype("int64")).reindex(ids).reset_index(drop=True)
    return W, ids, sign, meta


def write_their_format(S, ids, path):
    coo = S.tocoo()
    out = pd.DataFrame({
        "Presynaptic_ID": ids[coo.row], "Postsynaptic_ID": ids[coo.col],
        "Presynaptic_Index": coo.row, "Postsynaptic_Index": coo.col,
        "Connectivity": np.abs(coo.data).astype(np.int64),
        "Excitatory": np.sign(coo.data).astype(np.int64),
    })
    out["Excitatory x Connectivity"] = out["Excitatory"] * out["Connectivity"]
    out.to_parquet(path, index=False)


def simulate(name, path_con, neu_exc, n_proc):
    from model import default_params, run_exp
    p = dict(default_params)
    p["n_run"] = N_TRIALS
    run_exp(exp_name=name, neu_exc=neu_exc, path_res=str(OUT), path_comp=str(COMP),
            path_con=str(path_con), params=p, n_proc=n_proc, force_overwrite=True)


def score(rates_file, ids, readout):
    from model import default_params
    import utils as utl
    r, _ = utl.get_rate(utl.load_exps([str(rates_file)]), t_run=default_params["t_run"], n_run=N_TRIALS)
    s = pd.to_numeric(r.iloc[:, 0], errors="coerce")
    s.index = s.index.astype("int64")
    prof = s.reindex(ids[readout]).fillna(0.0)
    return {"spread": participation_ratio(prof), "dn_active": int((prof > 0).sum()),
            "dn_mean_hz": float(prof.mean()), "brain_active": int((s > 0).sum()),
            "mn9_hz": float(s.get(MN9, 0.0))}


def run(n_proc):
    OUT.mkdir(parents=True, exist_ok=True)
    W, ids, sign, meta = load()
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(W.shape[0], channels, readout)
    neu = sugar_783(ids)
    print(f"{W.nnz:,} edges; {len(channels)} sensory channels; {len(readout)} DNs; "
          f"{len(neu)} sugar GRNs; {int(boundary[0].sum())} boundary sources", flush=True)
    done = pd.read_csv(CSV) if CSV.exists() else pd.DataFrame(columns=["network", "replicate"])
    rows = done.to_dict("records")
    seen = set(zip(done["network"], done["replicate"].astype(int)))

    for gen, r in schedule():
        if (gen, r) in seen:
            continue
        name = f"{gen}_{r}"
        t = time.time()
        ok = bok = None
        if gen == "real":
            simulate(name, CON, neu, n_proc)
        else:
            S = make_surrogate(gen, W, np.random.default_rng(1000 + r - 1), sign, labels, SWAPS, boundary)
            checks = nulls.check_preserved(W, S)
            ok = bool(checks["n_edges_equal"] and checks["weight_multiset_equal"]
                      and checks["out_degree_equal"] and checks["in_degree_equal"])
            if gen in nulls.INTERIOR_GENERATORS:
                bok = nulls.check_boundary(W, S, *boundary)["boundary_identical"]  # raises if moved
            if not ok:
                print(f"{name}: invariant broken {checks}; not simulated", flush=True)
                continue
            t_build = time.time() - t
            write_their_format(S, ids, TMP)
            del S
            simulate(name, TMP, neu, n_proc)
        row = {"network": gen, "replicate": r, **score(OUT / f"{name}.parquet", ids, readout),
               "invariants_ok": ok, "boundary_ok": bok, "seconds": round(time.time() - t)}
        rows.append(row)
        pd.DataFrame(rows).to_csv(CSV, index=False)
        build = f" build {t_build:.0f}s" if gen != "real" else ""
        print(f"{name:32s} spread={row['spread']:.2f}  dn_active={row['dn_active']}  "
              f"({row['seconds']}s{build})", flush=True)
    TMP.unlink(missing_ok=True)


def p_lower(real, null):
    k = int((null <= real).sum())
    return k, (1 + k) / (len(null) + 1)


def summary():
    d = pd.read_csv(CSV)
    real = float(d.loc[d.network == "real", "spread"].iloc[0])
    rows = []
    for g in PLAN:
        x = d.loc[d.network == g, "spread"].to_numpy()
        if not len(x):
            continue
        k, p = p_lower(real, x)
        rows.append({"network": g, "N": len(x), "real": real, "mean": x.mean(), "sd": x.std(ddof=1),
                     "min": x.min(), "k_le_real": k, "p": p})
    t = pd.DataFrame(rows)
    t.to_csv(ROOT / "results" / "exp06_summary.csv", index=False)
    print(t.round(4).to_string(index=False))
    inside = t[t.network.str.startswith("interior")]
    full = len(inside) == 2 and all(inside.N == [PLAN[g] for g in inside.network])
    yes = full and bool((inside.p < 0.05).all())
    print(f"\nRule (real spread < both inside-only types, p < 0.05): "
          f"{'YES' if yes else 'NO' if full else 'incomplete'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["run", "summary"])
    ap.add_argument("--n-proc", type=int, default=3)
    a = ap.parse_args()
    run(a.n_proc) if a.stage == "run" else summary()
