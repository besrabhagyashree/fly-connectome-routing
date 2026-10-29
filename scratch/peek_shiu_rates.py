"""Inspect the structure of Shiu et al.'s rate output so the comparison uses the right column."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))

from model import default_params  # noqa: E402
import utils as utl  # noqa: E402

theirs = utl.load_exps([str(REPO / "results" / "example" / "sugarR.parquet")])
print("raw spike frame:", theirs.shape)
print(theirs.head(4).to_string())
print("dtypes:\n", theirs.dtypes)

r, r_std = utl.get_rate(theirs, t_run=default_params["t_run"], n_run=default_params["n_run"])
print("\nrate object type:", type(r), "shape:", getattr(r, "shape", None))
print(r.head(8).to_string())
print("\ndtypes:\n", r.dtypes if hasattr(r, "dtypes") else type(r))
