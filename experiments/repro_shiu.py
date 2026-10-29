"""Faithful reproduction of Shiu et al. 2024, using the authors' own code.

Runs THEIR model.py, THEIR connectivity file and THEIR published parameters, on
the sugar-sensing neurons from their example. Then compares our spike rates
against their stored output (results/sugarR.parquet).

This is the acceptance test: a method counts as implemented only when it
reproduces a number the authors published. Nothing here is our own modelling.

  python repro_shiu.py            # full protocol, 30 trials
  python repro_shiu.py --quick    # 3 trials, for a fast check
"""
from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

from model import default_params, run_exp  # noqa: E402
import utils as utl  # noqa: E402

# The 21 sugar-sensing neurons from the authors' example notebook.
NEU_SUGAR = [
    720575940624963786, 720575940630233916, 720575940637568838, 720575940638202345,
    720575940617000768, 720575940630797113, 720575940632889389, 720575940621754367,
    720575940621502051, 720575940640649691, 720575940639332736, 720575940616885538,
    720575940639198653, 720575940620900446, 720575940617937543, 720575940632425919,
    720575940633143833, 720575940612670570, 720575940628853239, 720575940629176663,
    720575940611875570,
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="3 trials instead of 30")
    ap.add_argument("--n-proc", type=int, default=2)
    ap.add_argument("--compare-only", action="store_true",
                    help="skip the simulation and compare an existing output")
    args = ap.parse_args()

    out_dir = ROOT / "results" / "repro_shiu"
    out_dir.mkdir(parents=True, exist_ok=True)

    params = dict(default_params)
    if args.quick:
        params["n_run"] = 3

    name = "sugarR_quick" if args.quick else "sugarR_repro"
    target = out_dir / f"{name}.parquet"

    if not args.compare_only:
        if target.exists():
            target.unlink()
        print(f"running Shiu et al. model: {params['n_run']} trials, "
              f"{len(NEU_SUGAR)} sugar neurons excited", flush=True)
        t0 = time.time()
        run_exp(
            exp_name=name,
            neu_exc=NEU_SUGAR,
            path_res=str(out_dir),
            path_comp=str(REPO / "2023_03_23_completeness_630_final.csv"),
            path_con=str(REPO / "2023_03_23_connectivity_630_final.parquet"),
            params=params,
            n_proc=args.n_proc,
            force_overwrite=True,
        )
        print(f"simulation finished in {time.time()-t0:.0f}s", flush=True)

    ours = utl.load_exps([str(target)])
    theirs = utl.load_exps([str(REPO / "results" / "example" / "sugarR.parquet")])

    # Keep raw flywire ids as the index: renaming a subset makes it mixed-type.
    r_ours, _ = utl.get_rate(ours, t_run=params["t_run"], n_run=params["n_run"])
    r_theirs, _ = utl.get_rate(theirs, t_run=default_params["t_run"],
                               n_run=default_params["n_run"])

    a = pd.to_numeric(r_ours.iloc[:, 0], errors="coerce")
    b = pd.to_numeric(r_theirs.iloc[:, 0], errors="coerce")
    a.index = a.index.astype("int64")
    b.index = b.index.astype("int64")
    joined = pd.concat([a.rename("ours"), b.rename("published")], axis=1).dropna()

    print(f"\nneurons with a rate in both: {len(joined)}")
    if len(joined) > 2:
        print(f"correlation (Pearson):  {joined['ours'].corr(joined['published']):.4f}")
        print(f"correlation (Spearman): {joined['ours'].corr(joined['published'], method='spearman'):.4f}")
        diff = (joined["ours"] - joined["published"]).abs()
        print(f"median |difference|: {diff.median():.3f} Hz   max: {diff.max():.3f} Hz")
        print("\ntop 12 neurons by published rate:")
        print(joined.sort_values("published", ascending=False).head(12).to_string())
    joined.to_csv(out_dir / f"{name}_vs_published.csv")
    print(f"\nwrote {out_dir / (name + '_vs_published.csv')}")


if __name__ == "__main__":
    main()

