"""Load the FlyWire v783 connectome into a signed, weighted sparse matrix.

Data source: https://storage.googleapis.com/flywire-data/codex/data/fafb/783
FlyWire data is CC BY-NC 4.0 -- cite Dorkenwald et al. 2024 and Schlegel et al. 2024.

Convention: W[i, j] is the weight of the connection FROM i TO j, signed by the
presynaptic neuron's predicted neurotransmitter. Activity updates therefore use
x @ W (row vector times matrix), not W @ x.
"""
from __future__ import annotations

import gzip
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "flywire783"
CACHE = ROOT / "data" / "cache"

# Predicted neurotransmitters, mapped to synaptic sign.
# Acetylcholine is excitatory; GABA and glutamate are inhibitory in the fly.
# Monoamines are modulatory: treated as excitatory here, and flagged so their
# effect can be tested separately.
NT_SIGN = {
    "ACH": +1.0,
    "GABA": -1.0,
    "GLUT": -1.0,
    "DA": +1.0,
    "SER": +1.0,
    "OCT": +1.0,
    "UNK": +1.0,
}
MODULATORY = {"DA", "SER", "OCT"}


@dataclass
class Connectome:
    W: sparse.csr_matrix          # signed weights, shape (N, N), row = presynaptic
    A: sparse.csr_matrix          # unsigned synapse counts
    ids: np.ndarray               # root_id per index
    meta: pd.DataFrame            # per-neuron annotations, indexed 0..N-1
    min_syn: int

    @property
    def n(self) -> int:
        return self.W.shape[0]

    def index_of(self, mask: pd.Series) -> np.ndarray:
        return np.flatnonzero(mask.to_numpy())

    def summary(self) -> str:
        nnz = self.W.nnz
        pos = int((self.W.data > 0).sum())
        return (
            f"neurons={self.n:,}  edges={nnz:,}  "
            f"excitatory={pos / nnz:.1%}  min_syn={self.min_syn}  "
            f"density={nnz / (self.n ** 2):.2e}"
        )


def _read(name: str, **kw) -> pd.DataFrame:
    path = DATA / name
    if not path.exists():
        raise FileNotFoundError(
            f"{path} missing. Download it from "
            f"https://storage.googleapis.com/flywire-data/codex/data/fafb/783/{name}"
        )
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as fh:
        return pd.read_csv(fh, **kw)


def load(min_syn: int = 5, use_cache: bool = True) -> Connectome:
    """Build the connectome. min_syn=5 matches the Codex default threshold."""
    CACHE.mkdir(parents=True, exist_ok=True)
    stem = CACHE / f"flywire783_minsyn{min_syn}"
    npz, meta_path = stem.with_suffix(".npz"), stem.with_suffix(".meta.parquet")

    if use_cache and npz.exists() and meta_path.exists():
        z = np.load(npz, allow_pickle=False)
        W = sparse.csr_matrix((z["w_data"], z["w_indices"], z["w_indptr"]), shape=tuple(z["shape"]))
        A = sparse.csr_matrix((z["a_data"], z["w_indices"], z["w_indptr"]), shape=tuple(z["shape"]))
        return Connectome(W, A, z["ids"], pd.read_parquet(meta_path), min_syn)

    conn = _read("connections.csv.gz")
    cls = _read("classification.csv.gz")
    neu = _read("neurons.csv.gz", usecols=["root_id", "nt_type", "nt_type_score"])
    types = _read("consolidated_cell_types.csv.gz", usecols=["root_id", "primary_type"])

    # Aggregate the per-neuropil rows into one edge per ordered neuron pair.
    conn = conn.groupby(["pre_root_id", "post_root_id"], sort=False)["syn_count"].sum().reset_index()
    conn = conn[conn["syn_count"] >= min_syn]

    meta = (
        cls.merge(neu, on="root_id", how="outer")
           .merge(types, on="root_id", how="left")
           .drop_duplicates("root_id")
    )

    # Neuron set: every annotated neuron, so counts match the published figure
    # even for neurons left isolated by the synapse threshold.
    ids = np.sort(meta["root_id"].unique())
    pos = pd.Series(np.arange(len(ids)), index=ids)
    meta = meta.set_index("root_id").loc[ids].reset_index()

    keep = conn["pre_root_id"].isin(pos.index) & conn["post_root_id"].isin(pos.index)
    conn = conn[keep]
    r = pos.loc[conn["pre_root_id"]].to_numpy()
    c = pos.loc[conn["post_root_id"]].to_numpy()
    w = conn["syn_count"].to_numpy(dtype=np.float64)

    nt = meta["nt_type"].fillna("UNK").to_numpy()
    sign = np.array([NT_SIGN.get(str(t).upper(), 1.0) for t in nt])

    n = len(ids)
    A = sparse.csr_matrix((w, (r, c)), shape=(n, n))
    W = sparse.csr_matrix((w * sign[r], (r, c)), shape=(n, n))

    meta["nt_sign"] = sign
    meta["is_modulatory"] = [str(t).upper() in MODULATORY for t in nt]
    meta["out_degree"] = np.asarray((A != 0).sum(axis=1)).ravel()
    meta["in_degree"] = np.asarray((A != 0).sum(axis=0)).ravel()

    np.savez_compressed(
        npz, w_data=W.data, w_indices=W.indices, w_indptr=W.indptr,
        a_data=A.data, shape=np.array(W.shape), ids=ids,
    )
    meta.to_parquet(meta_path, index=False)
    return Connectome(W, A, ids, meta, min_syn)


if __name__ == "__main__":
    c = load()
    print(c.summary())
    print()
    print("super_class counts:")
    print(c.meta["super_class"].value_counts(dropna=False).head(12).to_string())
    print()
    print("neurotransmitter counts:")
    print(c.meta["nt_type"].value_counts(dropna=False).head(10).to_string())
    print()
    published = 139_255
    print(f"published neuron count (Dorkenwald et al. 2024): {published:,}")
    print(f"loaded: {c.n:,}  delta: {c.n - published:+,}")
