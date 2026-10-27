"""Run the sugar experiment on their v783 connectivity, the version our own work uses.

Removes the version mismatch between this reproduction (v630) and everything in
flynull/ (v783), so results can legitimately be carried between them.
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

from model import default_params, run_exp  # noqa: E402
import utils as utl  # noqa: E402
from repro_shiu import NEU_SUGAR  # noqa: E402

MN9 = 720575940660219265


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-run", type=int, default=3)
    ap.add_argument("--n-proc", type=int, default=2)
    args = ap.parse_args()

    out_dir = ROOT / "results" / "repro_shiu"
    params = dict(default_params)
    params["n_run"] = args.n_run
    name = "sugarR_783"

    t0 = time.time()
    run_exp(exp_name=name, neu_exc=NEU_SUGAR, path_res=str(out_dir),
            path_comp=str(REPO / "Completeness_783.csv"),
            path_con=str(REPO / "Connectivity_783.parquet"),
            params=params, n_proc=args.n_proc, force_overwrite=True)
    print(f"v783 run finished in {time.time()-t0:.0f}s", flush=True)

    def rates(path, n):
        df = utl.load_exps([str(path)])
        r, _ = utl.get_rate(df, t_run=params["t_run"], n_run=n)
        s = pd.to_numeric(r.iloc[:, 0], errors="coerce")
        s.index = s.index.astype("int64")
        return s

    v783 = rates(out_dir / f"{name}.parquet", args.n_run)
    v630 = rates(out_dir / "sugarR_quick.parquet", 3)
    both = pd.concat([v630.rename("v630"), v783.rename("v783")], axis=1).dropna()

    print(f"\nactive neurons: v630 {(v630 > 0).sum()}, v783 {(v783 > 0).sum()}, "
          f"in both {len(both)}")
    print(f"correlation across versions: Pearson {both['v630'].corr(both['v783']):.4f}, "
          f"Spearman {both['v630'].corr(both['v783'], method='spearman'):.4f}")
    print(f"MN9: v630 {v630.get(MN9, float('nan')):.1f} Hz, v783 {v783.get(MN9, float('nan')):.1f} Hz")
    driven = both.reindex(NEU_SUGAR).dropna()
    print(f"stimulated neurons: v630 {driven['v630'].mean():.1f} Hz, v783 {driven['v783'].mean():.1f} Hz")
    both.to_csv(out_dir / "version_comparison.csv")
    print(f"wrote {out_dir / 'version_comparison.csv'}")


if __name__ == "__main__":
    main()
