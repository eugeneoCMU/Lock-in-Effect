"""
Stratified Freddie loan sample for literature microsim.

Materializes loan-level rows (unlike ingest.py cohort aggregation) with
stratum_id for cohort-level burnout broadcast.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import polars as pl

from config import (
    COUPON_STEP,
    FICO_BINS,
    LOAN_SAMPLE_PATH,
    N_LOANS,
    QT_START,
    RAW_DIR,
    RNG_SEED,
)
from ingest import (
    _coupon_bucket,
    _fico_bucket,
    _ltv_bucket,
    _map_servicer_state,
    _scan_orig,
    _scan_perf,
    _vintage_from_seq,
    discover_raw_files,
    generate_synthetic_fixture,
)
from schema import ORIG_COLS, PERF_COLS


def _stratum_id_expr() -> pl.Expr:
    return (
        pl.col("vintage").cast(pl.Utf8)
        + pl.lit("_")
        + (pl.col("coupon") * 10000).round(0).cast(pl.Int64).cast(pl.Utf8)
        + pl.lit("_")
        + pl.col("fico_bucket")
    )


def _loan_snapshot_one_pair(orig_path: Path, perf_path: Path) -> pl.DataFrame:
    """Join orig + latest pre-QT perf row per loan for one quarterly file pair."""
    qt_ym = QT_START.strftime("%Y%m")
    orig = _scan_orig(orig_path)
    perf = _scan_perf(perf_path)
    return (
        perf.join(orig, on="loan_sequence_number", how="inner")
        .filter(pl.col("reporting_period") < qt_ym)
        .sort("reporting_period")
        .group_by("loan_sequence_number")
        .last()
        .collect()
        .with_columns([
            pl.col("loan_sequence_number").alias("loan_id"),
            pl.col("current_upb").alias("balance"),
            pl.col("original_interest_rate").alias("coupon_pct"),
            (pl.col("original_interest_rate") / 100.0).alias("coupon"),
            pl.col("credit_score").cast(pl.Int64).alias("fico"),
            pl.col("original_ltv").alias("orig_ltv"),
            pl.col("original_upb").alias("orig_upb"),
            _stratum_id_expr().alias("stratum_id"),
            pl.col("servicer_state").alias("state"),
        ])
        .select([
            "loan_id", "stratum_id", "fico", "property_state", "orig_ltv",
            "coupon", "orig_upb", "balance", "loan_age", "state", "vintage",
            "fico_bucket", "ltv_bucket",
        ])
    )


def _build_loan_universe(pairs: list[tuple[Path, Path]]) -> pl.DataFrame:
    """Join orig + latest pre-QT perf row per loan."""
    chunks = [_loan_snapshot_one_pair(o, p) for o, p in pairs]
    if not chunks:
        raise FileNotFoundError("No Freddie orig/perf file pairs found.")
    return pl.concat(chunks)


def _build_loan_sample_pool(
    pairs: list[tuple[Path, Path]],
    pool_target: int,
    seed: int,
) -> pl.DataFrame:
    """
    Memory-safe pool: oversample per quarterly file instead of materializing
    the full loan universe (~12M rows).
    """
    per_file = max(1000, pool_target // max(len(pairs), 1))
    chunks = []
    for i, (orig_path, perf_path) in enumerate(pairs):
        df = _loan_snapshot_one_pair(orig_path, perf_path)
        if len(df) == 0:
            continue
        k = min(per_file, len(df))
        chunks.append(df.sample(n=k, seed=seed + i))
    if not chunks:
        raise FileNotFoundError("No Freddie orig/perf file pairs found.")
    return pl.concat(chunks)


def _stratified_sample(df: pl.DataFrame, n_loans: int, seed: int) -> pl.DataFrame:
    """Sample n_loans proportionally within stratum_id; with-replacement if needed."""
    strata = df.group_by("stratum_id").agg(pl.len().alias("count"))
    total = strata["count"].sum()
    if total == 0:
        raise ValueError("Empty loan universe.")

    strata = strata.with_columns([
        (pl.col("count") / total * n_loans).round().cast(pl.Int64).alias("target_n"),
    ])

    samples = []
    for i, row in enumerate(strata.iter_rows(named=True)):
        pool = df.filter(pl.col("stratum_id") == row["stratum_id"])
        if len(pool) == 0:
            continue
        k = max(1, int(row["target_n"]))
        replace = k > len(pool)
        samples.append(pool.sample(n=k, with_replacement=replace, seed=seed + i))

    if not samples:
        raise ValueError("Stratified sample produced no loans.")

    out = pl.concat(samples)
    if len(out) > n_loans:
        out = out.sample(n=n_loans, seed=seed)
    elif len(out) < n_loans:
        extra = df.sample(
            n=n_loans - len(out), seed=seed + 1, with_replacement=True
        )
        out = pl.concat([out, extra])

    return out.head(n_loans)


def build_loan_sample(
    n_loans: int = N_LOANS,
    raw_dir: Path = RAW_DIR,
    output: Path = LOAN_SAMPLE_PATH,
    seed: int = RNG_SEED,
    force_rebuild: bool = False,
) -> pl.DataFrame:
    """Build stratified loan sample parquet for microsim."""
    if output.exists() and not force_rebuild:
        print(f"Loading cached loan sample from {output}")
        return pl.read_parquet(output)

    pairs = discover_raw_files(raw_dir)
    if not pairs:
        print("No raw files; generating synthetic fixture …")
        generate_synthetic_fixture()
        pairs = discover_raw_files(raw_dir)

    print(f"Building stratified loan pool from {len(pairs)} file pair(s) …")
    pool = _build_loan_sample_pool(pairs, pool_target=n_loans * 4, seed=seed)
    print(f"  Pool: {len(pool):,} loans, {pool['stratum_id'].n_unique()} strata")

    sample = _stratified_sample(pool, n_loans, seed)
    sample = sample.with_columns([
        pl.lit(1.0).alias("weight"),  # normalized below after scaling
    ])

    output.parent.mkdir(parents=True, exist_ok=True)
    sample.write_parquet(output)
    print(f"Loan sample saved: {output} ({len(sample):,} loans)")
    return sample


def load_or_build_loan_sample(
    n_loans: int = N_LOANS,
    force_rebuild: bool = False,
) -> pl.DataFrame:
    # Raw-file verification (and the Drive download fallback) only when a
    # build is actually needed: a cache hit must return the committed frozen
    # sample without touching raw files. The unconditional pre-check made
    # every caller crash on machines without raw files via the dead
    # authenticate_service_account path (removed in 506ca2b) — the defect
    # tests/test_loan_sample_cache.py was written to catch.
    if force_rebuild or not LOAN_SAMPLE_PATH.exists():
        from prepare_freddie import ensure_raw_files
        ensure_raw_files()
        if force_rebuild and LOAN_SAMPLE_PATH.exists():
            LOAN_SAMPLE_PATH.unlink()
    # Pass the module-global path explicitly: build_loan_sample's default was
    # bound at def time, which silently ignored any override of
    # loan_sample.LOAN_SAMPLE_PATH (same value in production either way).
    return build_loan_sample(n_loans=n_loans, output=LOAN_SAMPLE_PATH,
                             force_rebuild=force_rebuild)


if __name__ == "__main__":
    df = build_loan_sample(force_rebuild=True)
    print(df.head())
    print(f"Strata: {df['stratum_id'].n_unique()}")
