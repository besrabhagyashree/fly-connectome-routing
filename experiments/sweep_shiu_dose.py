"""Reproduce the dose-response of Shiu et al. Fig. 1c: MN9 rate vs sugar drive.

Their figure sweeps sugar GRN firing rate and reads motor neuron 9. We sweep the
Poisson drive over the same span using their model, so the two curves can be put
side by side.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402
from brian2 import Hz  # noqa: E402

from model import default_params, run_exp  # noqa: E402
import utils as utl  # noqa: E402
from repro_shiu import NEU_SUGAR  # noqa: E402

MN9 = 720575940660219265


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rates", type=int, nargs="*", default=[25, 50, 75, 100, 150, 200])
    ap.add_argument("--n-run", type=int, default=3)
    ap.add_argument("--n-proc", type=int, default=2)
    args = ap.parse_args()

    out_dir = ROOT / "results" / "repro_shiu" / "dose"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []

    for r in args.rates:
        name = f"sugar_{r}Hz"
        params = dict(default_params)
        params["n_run"] = args.n_run
        params["r_poi"] = r * Hz
        t0 = time.time()
        run_exp(exp_name=name, neu_exc=NEU_SUGAR, path_res=str(out_dir),
                path_comp=str(REPO / "2023_03_23_completeness_630_final.csv"),
                path_con=str(REPO / "2023_03_23_connectivity_630_final.parquet"),
                params=params, n_proc=args.n_proc, force_overwrite=True)

        df = utl.load_exps([str(out_dir / f"{name}.parquet")])
        rate, _ = utl.get_rate(df, t_run=params["t_run"], n_run=args.n_run)
        s = pd.to_numeric(rate.iloc[:, 0], errors="coerce")
        s.index = s.index.astype("int64")
        driven = s.reindex(NEU_SUGAR).dropna()
        rows.append({
            "drive_hz": r,
            "grn_rate": float(driven.mean()),
            "mn9_rate": float(s.get(MN9, float("nan"))),
            "n_active": int((s > 0).sum()),
        })
        pd.DataFrame(rows).to_csv(out_dir / "dose_response.csv", index=False)
        print(f"drive {r:3d} Hz -> GRN {rows[-1]['grn_rate']:6.1f} Hz, "
              f"MN9 {rows[-1]['mn9_rate']:6.1f} Hz, active {rows[-1]['n_active']:4d} "
              f"({time.time()-t0:.0f}s)", flush=True)

    print("\n" + pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
