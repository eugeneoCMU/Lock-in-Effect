"""
Fannie-aware Path B loan sampling over staged (Freddie-coded) pairs.

The Freddie 75k sample (loan_sample.py) draws its oversample pool with every
staged pair on disk at once. The Fannie production pull cannot afford that
(24 staged pairs ≈ 34 GB against single-digit GB free), so the pool is
materialized as per-quarter POOL PIECES — an oversample of pre-QT loan
snapshots drawn while that quarter's staged pair still exists — and the final
stratified draw runs over the concatenated pieces after the last quarter is
cleaned up. Corrected pieces retain separate full-source cohort histories and
eligible source IDs, including quarters with no surviving loans. Finalization
combines those histories before attaching initial burnout to sampled survivors.
Snapshot and draw logic are shared with loan_sample.py. The two operational
deviations from the all-pairs Freddie build remain:

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
import warnings

import polars as pl

from config import DATA_DIR, N_LOANS, RNG_SEED
from ingest import _vintage_from_seq
from loan_sample import _attach_history, _snapshot_inputs_one_pair, _stratified_sample

FANNIE_LOAN_SAMPLE_PATH = DATA_DIR / "loan_sample_fannie.parquet"


def _piece_sidecar_paths(piece_path: Path) -> tuple[Path, Path]:
    """Keep sidecars outside the production pool_*.parquet input glob."""
    piece_path = Path(piece_path)
    return (piece_path.parent / "pool_history" / piece_path.name,
            piece_path.parent / "pool_source_ids" / piece_path.name)


def write_pool_piece(
    orig_path: Path,
    perf_path: Path,
    per_file: int,
    seed: int,
    output: Path,
    vintage_years: Sequence[int] | None = None,
    *, term_months: int | None = 360,
) -> int:
    """
    Draw one quarter's pool piece from its staged pair and persist it.

    A zero-row piece is still written, with full-source history and ID sidecars.
    Its history can contribute to another quarter's surviving cohort. The piece
    itself is written last as the resume marker for the complete extraction.
    """
    output = Path(output)
    history_path, ids_path = _piece_sidecar_paths(output)
    if any(path.exists() for path in (output, history_path, ids_path)):
        raise FileExistsError("Preserve prior pool pieces and sidecars; choose a new output path")
    snap, history, ids = _snapshot_inputs_one_pair(orig_path, perf_path, term_months=term_months)
    source_ids = pl.DataFrame({"loan_sequence_number": ids},
                             schema={"loan_sequence_number": pl.String})
    if vintage_years is not None:
        snap = snap.filter(pl.col("vintage").is_in(list(vintage_years)))
        history = history.filter(pl.col("vintage").is_in(list(vintage_years)))
        source_ids = source_ids.filter(
            _vintage_from_seq(pl.col("loan_sequence_number")).is_in(list(vintage_years)))
    k = min(per_file, len(snap))
    piece = snap.sample(n=k, seed=seed) if k > 0 else snap.head(0)
    output.parent.mkdir(parents=True, exist_ok=True)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    ids_path.parent.mkdir(parents=True, exist_ok=True)
    history.write_parquet(history_path)
    source_ids.write_parquet(ids_path)
    piece.write_parquet(output)
    return len(piece)


def finalize_fannie_sample(
    piece_paths: Iterable[Path],
    n_loans: int = N_LOANS,
    seed: int = RNG_SEED,
    output: Path = FANNIE_LOAN_SAMPLE_PATH,
    *, allow_legacy_inputs: bool = False,
) -> pl.DataFrame:
    """Combine full source histories before drawing the final survivor sample."""
    output = Path(output)
    if output.exists():
        raise FileExistsError("Preserve the prior Fannie sample; choose a new output path")
    piece_paths = [Path(p) for p in piece_paths]
    if not piece_paths:
        raise ValueError("No Fannie pool pieces supplied")
    sidecars = [_piece_sidecar_paths(p) for p in piece_paths]
    present = [(history.exists(), ids.exists()) for history, ids in sidecars]
    corrected = all(history and ids for history, ids in present)
    if not corrected:
        if any(history or ids for history, ids in present):
            raise ValueError("Mixed or incomplete Fannie history/source-ID sidecars; rebuild all pieces")
        if not allow_legacy_inputs:
            raise ValueError("Fannie pool pieces lack full source history sidecars; rebuild or explicitly replay legacy inputs")
        warnings.warn("Historical Fannie pool replay has no audited global cohort history", UserWarning)
    pieces = [pl.read_parquet(p) for p in piece_paths]
    if corrected:
        # Check every eligible source ID, including terminated and unsampled
        # loans. Checking just the oversample would miss duplicated source cash.
        source_scans = [pl.scan_parquet(ids).select("loan_sequence_number") for _, ids in sidecars]
        all_ids = pl.concat(source_scans)
        if all_ids.filter(pl.col("loan_sequence_number").is_null()).limit(1).collect().height:
            raise ValueError("Missing source loan ID in Fannie sidecar")
        if all_ids.group_by("loan_sequence_number").len().filter(pl.col("len") > 1).limit(1).collect().height:
            raise ValueError("Overlapping origination files in Fannie source-ID sidecars")
        for piece, (history, ids) in zip(pieces, sidecars):
            if "initial_burnout" in piece.columns or "cohort_original_upb" in piece.columns:
                raise ValueError("Corrected pool pieces must retain raw survivors; attach global history only at finalization")
            missing = piece.select("loan_id").join(
                pl.read_parquet(ids).rename({"loan_sequence_number": "loan_id"}),
                on="loan_id", how="anti")
            if missing.height:
                raise ValueError("Fannie pool contains loans absent from its source-ID sidecar")
            # Validate coverage per source before another quarter can mask a
            # missing cohort in this source's sidecar. Discard the local shares;
            # only the global attachment below is used for the final sample.
            _attach_history(piece, [pl.read_parquet(history)])
    pool = pl.concat(pieces)
    if len(pool) == 0:
        raise ValueError("Fannie pool pieces are all empty — nothing to sample.")
    if corrected:
        pool = _attach_history(pool, [pl.read_parquet(history) for history, _ in sidecars])
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
