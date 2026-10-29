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
  .venv-brian/Scripts/python.exe experiments/exp06_shiu_spiking.py run --worker 1 --n-proc 1   (one of several drivers)
  .venv-brian/Scripts/python.exe experiments/exp06_shiu_spiking.py summary
"""
from __future__ import annotations

import argparse
import os
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


CLAIMS = OUT / "claims"
STALE_H = 3  # a claim with no result after this long is from a driver that died


def free_gb():
    """Available physical memory (Windows GlobalMemoryStatusEx; no psutil in .venv-brian)."""
    import ctypes

    class M(ctypes.Structure):
        _fields_ = [("len", ctypes.c_ulong), ("load", ctypes.c_ulong)] + \
                   [(f, ctypes.c_ulonglong) for f in ("tot", "avail", "tpf", "apf", "tv", "av", "ax")]
    m = M()
    m.len = ctypes.sizeof(M)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.avail / 2**30


def claim(name):
    """Atomically claim a brain for this driver; False if another live driver holds it."""
    CLAIMS.mkdir(parents=True, exist_ok=True)
    f = CLAIMS / f"{name}.claim"
    if f.exists() and time.time() - f.stat().st_mtime > STALE_H * 3600:
        f.unlink(missing_ok=True)
    try:
        os.close(os.open(f, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        return False


def run(n_proc, shard="0/1", worker=None, min_free_gb=3.0):
    """shard i/k: fixed every-k-th split. worker w: take the next unclaimed brain (any number of drivers)."""
    i, k = map(int, shard.split("/"))
    tag = f"w{worker}" if worker is not None else (f"s{i}" if k > 1 else "")
    csv = CSV.with_name(f"exp06_shiu_{tag}.csv") if tag else CSV
    tmp = TMP.with_name(f"_surrogate_{tag}.parquet") if tag else TMP
    OUT.mkdir(parents=True, exist_ok=True)
    W, ids, sign, meta = load()
    channels = sensory_channels(meta)
    readout = np.flatnonzero(meta["super_class"].eq("descending").to_numpy())
    labels = meta["super_class"].fillna("na").astype("category").cat.codes.to_numpy()
    boundary = boundary_masks(W.shape[0], channels, readout)
    neu = sugar_783(ids)
    print(f"{W.nnz:,} edges; {len(channels)} sensory channels; {len(readout)} DNs; "
          f"{len(neu)} sugar GRNs; {int(boundary[0].sum())} boundary sources", flush=True)
    mine = pd.read_csv(csv) if csv.exists() else pd.DataFrame(columns=["network", "replicate"])
    rows = mine.to_dict("records")
    done = load_all()
    seen = set(zip(done["network"], done["replicate"].astype(int)))

    for j, (gen, r) in enumerate(schedule()):
        name = f"{gen}_{r}"
        if worker is None and j % k != i:
            continue
        if worker is not None:
            done = load_all()
            seen = set(zip(done["network"], done["replicate"].astype(int)))
        if (gen, r) in seen or (worker is not None and not claim(name)):
            continue
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
            write_their_format(S, ids, tmp)
            del S
            while free_gb() < min_free_gb:  # several drivers: don't start a 2.4 GB simulation into swap
                time.sleep(30)
            simulate(name, tmp, neu, n_proc)
        row = {"network": gen, "replicate": r, **score(OUT / f"{name}.parquet", ids, readout),
               "invariants_ok": ok, "boundary_ok": bok, "seconds": round(time.time() - t)}
        rows.append(row)
        pd.DataFrame(rows).to_csv(csv, index=False)
        build = f" build {t_build:.0f}s" if gen != "real" else ""
        print(f"{name:32s} spread={row['spread']:.2f}  dn_active={row['dn_active']}  "
              f"({row['seconds']}s{build})", flush=True)
    tmp.unlink(missing_ok=True)


def load_all():
    """Rows from the single-driver CSV and every shard CSV."""
    fs = sorted(CSV.parent.glob("exp06_shiu*.csv"))
    if not fs:
        return pd.DataFrame(columns=["network", "replicate", "spread"])
    return pd.concat([pd.read_csv(f) for f in fs]).drop_duplicates(["network", "replicate"])


def p_lower(real, null):
    k = int((null <= real).sum())
    return k, (1 + k) / (len(null) + 1)


def summary():
    d = load_all()
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
    ap.add_argument("--shard", default="0/1", help="i/k: this driver runs every k-th brain, starting at i")
    ap.add_argument("--worker", type=int, help="claim-queue mode: run as driver number W")
    a = ap.parse_args()
    run(a.n_proc, a.shard, a.worker) if a.stage == "run" else summary()
