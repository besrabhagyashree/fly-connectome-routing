"""Can we feed Shiu's model a rewired connectome? Check the file's shape."""
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent.parent / "external" / "Drosophila_brain_model"

for name in ("2023_03_23_connectivity_630_final.parquet", "Connectivity_783.parquet"):
    p = REPO / name
    df = pd.read_parquet(p)
    print(f"=== {name}  ({p.stat().st_size/1e6:.0f} MB) ===")
    print("columns:", list(df.columns))
    print("rows:", f"{len(df):,}")
    print(df.head(3).to_string())
    num = df.select_dtypes("number")
    if len(num.columns):
        print("weight-like column stats:")
        print(num.describe().loc[["min", "50%", "max"]].to_string())
    print()

comp = pd.read_csv(REPO / "2023_03_23_completeness_630_final.csv")
comp783 = pd.read_csv(REPO / "Completeness_783.csv")
print("completeness 630:", comp.shape, "| 783:", comp783.shape)
ids630 = set(comp.iloc[:, 0].astype("int64"))
ids783 = set(comp783.iloc[:, 0].astype("int64"))
print(f"shared neuron ids between versions: {len(ids630 & ids783):,} "
      f"({len(ids630 & ids783)/max(len(ids630),1):.1%} of v630)")
print("MN9 720575940660219265 in 630:", 720575940660219265 in ids630,
      "| in 783:", 720575940660219265 in ids783)
