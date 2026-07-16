"""
Fannie-aware Path B loan sampling over staged (Freddie-coded) pairs.

The Freddie 75k sample (loan_sample.py) draws its oversample pool with every
staged pair on disk at once. The Fannie production pull cannot afford that
(24 staged pairs ≈ 34 GB against single-digit GB free), so the pool is
materialized as per-quarter POOL PIECES — an oversample of pre-QT loan
snapshots drawn while that quarter's staged pair still exists — and the final
stratified draw runs over the concatenated pieces after the last quarter is
cleaned up. Snapshot and draw logic are imported from loan_sample.py
UNCHANGED (_loan_snapshot_one_pair, _stratified_sample), so the Fannie sample
is the same construction as the committed Freddie sample except for the two
deviations the spec in fannie_replication.py records ex ante:

  1. per-quarter pieces instead of an all-pairs pool (equal per-file draw
     size and per-file seed offsets exactly as _build_loan_sample_pool);
  2. an explicit vintage filter on the snapshot (Freddie files are
     vintage-sliced at the source; Fannie acquisition files carry a seasoned
     origination tail that must not enter the 2017–2021 universe).

Seeds: a piece drawn for the quarter at index i of the spec's QUARTERS list
uses seed = RNG_SEED + i, mirroring loan_sample._build_loan_sample_pool's
`seed + i` convention, and tied to the fixed spec order — NOT the runtime
processing order — so the draw is deterministic under resume.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

import polars as pl

from config import DATA_DIR, N_LOANS, RNG_SEED
from loan_sample import _loan_snapshot_one_pair, _stratified_sample

FANNIE_LOAN_SAMPLE_PATH = DATA_DIR / "loan_sample_fannie.parquet"


def write_pool_piece(
    orig_path: Path,
    perf_path: Path,
    per_file: int,
    seed: int,
    output: Path,
    vintage_years: Sequence[int] | None = None,
) -> int:
    """
    Draw one quarter's pool piece from its staged pair and persist it.

    A zero-row piece is still written: the file is the resume marker that the
    quarter's Path B extraction is complete (late acquisition quarters have no
    pre-QT rows and legitimately contribute nothing).
    """
    snap = _loan_snapshot_one_pair(orig_path, perf_path)
    if vintage_years is not None:
        snap = snap.filter(pl.col("vintage").is_in(list(vintage_years)))
    k = min(per_file, len(snap))
    piece = snap.sample(n=k, seed=seed) if k > 0 else snap.head(0)
    output.parent.mkdir(parents=True, exist_ok=True)
    piece.write_parquet(output)
    return len(piece)


def finalize_fannie_sample(
    piece_paths: Iterable[Path],
    n_loans: int = N_LOANS,
    seed: int = RNG_SEED,
    output: Path = FANNIE_LOAN_SAMPLE_PATH,
) -> pl.DataFrame:
    """Concatenate pool pieces and run the production stratified draw."""
    pieces = [pl.read_parquet(p) for p in piece_paths]
    pool = pl.concat(pieces)
    if len(pool) == 0:
        raise ValueError("Fannie pool pieces are all empty — nothing to sample.")
    sample = _stratified_sample(pool, n_loans, seed).with_columns(
        pl.lit(1.0).alias("weight")
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    sample.write_parquet(output)
    print(
        f"Fannie loan sample saved: {output} ({len(sample):,} loans, "
        f"{sample['stratum_id'].n_unique()} strata, pool {len(pool):,})"
    )
    return sample
