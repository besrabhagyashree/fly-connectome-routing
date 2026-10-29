"""Is the rate gap caused by running 3 trials instead of 30, or by something real?

Takes the authors' own 30-trial output, keeps only its first 3 trials, and scores
it the same way. If their first 3 trials also give ~199 Hz, trial count is not the
explanation and the difference is in the simulator.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

from model import default_params  # noqa: E402
import utils as utl  # noqa: E402

DRIVEN = [720575940637568838, 720575940621502051, 720575940639198653, 720575940617937543]

theirs = utl.load_exps([str(REPO / "results" / "example" / "sugarR.parquet")])
ours = utl.load_exps([str(ROOT / "results" / "repro_shiu" / "sugarR_quick.parquet")])

print("their trials:", sorted(theirs["trial"].unique())[:8], "count:", theirs["trial"].nunique())
print("our trials:  ", sorted(ours["trial"].unique()), "count:", ours["trial"].nunique())

theirs_3 = theirs[theirs["trial"] < 3]
r_all, _ = utl.get_rate(theirs, t_run=default_params["t_run"], n_run=theirs["trial"].nunique())
r_3, _ = utl.get_rate(theirs_3, t_run=default_params["t_run"], n_run=3)
r_ours, _ = utl.get_rate(ours, t_run=default_params["t_run"], n_run=ours["trial"].nunique())

tbl = pd.DataFrame({
    "theirs_30trials": pd.to_numeric(r_all.iloc[:, 0], errors="coerce"),
    "theirs_first3": pd.to_numeric(r_3.iloc[:, 0], errors="coerce"),
    "ours_3trials": pd.to_numeric(r_ours.iloc[:, 0], errors="coerce"),
})
tbl.index = tbl.index.astype("int64")

print("\ndirectly driven sugar neurons (Hz):")
print(tbl.loc[[d for d in DRIVEN if d in tbl.index]].to_string())

print("\nwhole-population medians (Hz):")
print(tbl.median().to_string())
print("\nneurons firing at all:")
print((tbl > 0).sum().to_string())
