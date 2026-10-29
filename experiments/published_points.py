"""Measure the published runs' own sensory and MN9 rates, instead of assuming them."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "external" / "Drosophila_brain_model"
sys.path.insert(0, str(REPO))

import pandas as pd  # noqa: E402

from model import default_params  # noqa: E402
import utils as utl  # noqa: E402
from repro_shiu import NEU_SUGAR  # noqa: E402

MN9 = 720575940660219265

for label, fname in (("published, drive 150 Hz", "sugarR.parquet"),
                     ("published, drive 100 Hz", "sugarR_100Hz.parquet")):
    df = utl.load_exps([str(REPO / "results" / "example" / fname)])
    n = df["trial"].nunique()
    r, _ = utl.get_rate(df, t_run=default_params["t_run"], n_run=n)
    s = pd.to_numeric(r.iloc[:, 0], errors="coerce")
    s.index = s.index.astype("int64")
    grn = s.reindex(NEU_SUGAR).dropna()
    print(f"{label}: trials={n}  GRN mean={grn.mean():.2f} Hz  MN9={s.get(MN9, float('nan')):.2f} Hz")
