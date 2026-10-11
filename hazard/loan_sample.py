"""
Stratified Freddie loan sample for literature microsim.

Materializes loan-level rows (unlike ingest.py cohort aggregation) with
stratum_id for cohort-level burnout broadcast.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional
import pandas as pd

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
        + pl.lit("_")
        + pl.col("ltv_bucket")
    )


_HISTORY_KEYS = ["vintage", "cohort_coupon", "fico_bucket", "ltv_bucket"]


def _snapshot_inputs_one_pair(orig_path, perf_path, *, term_months=None):
    """Source cohort totals and active balances at the exact pre-QT month.

    History uses the same chronological payoff convention as ingestion. Counts
    expose first-observed and calendar-gap payoffs for the source audit; carrying
    these fields does not certify source coverage or resolve those assumptions.
    """
    snapshot_ym = (pd.Timestamp(QT_START).to_period('M') - 1).strftime('%Y%m')
    orig = _scan_orig(orig_path)
    if term_months is not None:
        orig = orig.filter(pl.col('original_loan_term') == term_months)
    # Exclude source originations that had not entered the payment population.
    orig = orig.filter(pl.col('first_payment_date') <= snapshot_ym)
    orig = orig.with_columns(pl.col('coupon').alias('cohort_coupon'))
    ids = orig.select('loan_sequence_number').collect()['loan_sequence_number'].to_list()
    if len(ids) != len(set(ids)):
        raise ValueError('Duplicate origination IDs in snapshot source')
    perf = _scan_perf(perf_path, reporting_end=snapshot_ym)
    if perf.group_by(['loan_sequence_number','reporting_period']).len().filter(pl.col('len') > 1).limit(1).collect().height:
        raise ValueError('Duplicate loan-month in snapshot source')
    joined = perf.join(orig, on='loan_sequence_number', how='inner').with_columns([
        pl.col('current_upb').shift(1).over('loan_sequence_number', order_by='reporting_period').alias('prev_upb'),
        pl.col('reporting_period').shift(1).over('loan_sequence_number', order_by='reporting_period').alias('prev_period'),
    ])
    observed_ids = joined.select('loan_sequence_number').unique().collect()['loan_sequence_number'].to_list()
    if set(ids).difference(observed_ids):
        raise ValueError('Eligible source loans lack pre-QT performance history; do not assume zero historical payoffs')
    history = joined.group_by(_HISTORY_KEYS).agg([
        pl.when(pl.col('is_prepay')).then(pl.col('prev_upb').fill_null(pl.col('original_upb')))
        .otherwise(0.).sum().alias('historical_prepaid_upb'),
        (pl.col('is_prepay') & pl.col('prev_upb').is_null()).sum().alias('history_first_observed_payoff_count'),
        (pl.col('is_prepay') & pl.col('prev_period').is_not_null()
         & (pl.col('reporting_period').str.to_date('%Y%m').dt.offset_by('-1mo')
            != pl.col('prev_period').str.to_date('%Y%m'))).sum().alias('history_gap_payoff_count'),
    ]).collect()
    fixed = orig.group_by(_HISTORY_KEYS).agg(pl.col('original_upb').sum().alias('cohort_original_upb')).collect()
    # A wholly unobserved source cohort cannot establish a zero payoff history.
    if fixed.join(history, on=_HISTORY_KEYS, how='anti').height:
        raise ValueError('Source cohort has no pre-QT history; audit missing performance coverage')
    snapshot = (
        joined.filter((pl.col('reporting_period') == snapshot_ym)
                      & (pl.col('current_upb') > 0)
                      & ~pl.col('servicer_state').is_in(['Prepaid','Defaulted','Liquidated']))
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
            "fico_bucket", "ltv_bucket", "cohort_coupon", "original_loan_term", "reporting_period",
        ])
    )
    surviving = snapshot.group_by(_HISTORY_KEYS).agg(pl.col('orig_upb').sum().alias('survivor_original_upb'))
    history = fixed.join(history, on=_HISTORY_KEYS).join(surviving, on=_HISTORY_KEYS, how='left').with_columns(
        pl.col('survivor_original_upb').fill_null(0.))
    if history.filter(~pl.col('cohort_original_upb').is_finite()
                      | (pl.col('cohort_original_upb') <= 0)
                      | ~pl.col('historical_prepaid_upb').is_finite()
                      | (pl.col('historical_prepaid_upb') < 0)
                      | (pl.col('historical_prepaid_upb') > pl.col('cohort_original_upb'))).height:
        raise ValueError('Invalid fixed cohort payoff history; audit source events')
    if snapshot.filter(~pl.col('loan_age').is_finite() | pl.col('loan_age').is_null()
                       | (pl.col('loan_age') < 0) | (pl.col('loan_age') != pl.col('loan_age').floor())
                       | ~pl.col('original_loan_term').is_finite() | pl.col('original_loan_term').is_null()
                       | (pl.col('original_loan_term') <= 0)
                       | (pl.col('original_loan_term') != pl.col('original_loan_term').floor())).height:
        raise ValueError('Snapshot requires known valid original loan terms and ages')
    return snapshot, history, ids


def _attach_history(snapshot, histories):
    value_columns = ['cohort_original_upb', 'historical_prepaid_upb', 'survivor_original_upb',
                     'history_first_observed_payoff_count', 'history_gap_payoff_count']
    for history in histories:
        if not set(_HISTORY_KEYS + value_columns).issubset(history.columns):
            raise ValueError('History is missing required cohort totals')
        if history.select(pl.struct(_HISTORY_KEYS).is_duplicated().any()).item():
            raise ValueError('Duplicate cohort rows in source history')
        invalid = history.filter(
            pl.any_horizontal([pl.col(c).is_null() for c in _HISTORY_KEYS])
            | pl.any_horizontal([pl.col(c).is_null() | ~pl.col(c).is_finite() | (pl.col(c) < 0) for c in value_columns])
            | (pl.col('cohort_original_upb') <= 0)
            | (pl.col('historical_prepaid_upb') > pl.col('cohort_original_upb'))
            | (pl.col('survivor_original_upb') > pl.col('cohort_original_upb'))
        )
        if invalid.height:
            raise ValueError('Invalid finite nonnegative cohort history totals')
    totals = pl.concat(histories).group_by(_HISTORY_KEYS).agg([
        pl.col('cohort_original_upb').sum(), pl.col('historical_prepaid_upb').sum(),
        pl.col('survivor_original_upb').sum(), pl.col('history_first_observed_payoff_count').sum(),
        pl.col('history_gap_payoff_count').sum(),
    ]).with_columns([
        (pl.col('historical_prepaid_upb') / pl.col('cohort_original_upb')).alias('initial_burnout'),
        (pl.col('cohort_original_upb') / pl.col('survivor_original_upb')).alias('burnout_denominator_multiplier'),
    ])
    supported = totals.filter(pl.col('survivor_original_upb') > 0).select(_HISTORY_KEYS)
    if snapshot.select(_HISTORY_KEYS).unique().join(supported, on=_HISTORY_KEYS, how='anti').height:
        raise ValueError('Missing history or surviving original balance for a sampled cohort')
    return snapshot.join(totals, on=_HISTORY_KEYS, how='left')


def _loan_snapshot_one_pair(orig_path: Path, perf_path: Path, *, term_months=None) -> pl.DataFrame:
    snapshot, history, _ = _snapshot_inputs_one_pair(orig_path, perf_path, term_months=term_months)
    return _attach_history(snapshot, [history])


def _build_loan_universe(pairs: list[tuple[Path, Path]]) -> pl.DataFrame:
    """Combine fixed source histories before attaching them to survivors."""
    chunks, histories, seen = [], [], set()
    for o, p in pairs:
        snapshot, history, ids = _snapshot_inputs_one_pair(o, p)
        if seen.intersection(ids):
            raise ValueError('Overlapping origination files in snapshot universe')
        seen.update(ids)
        chunks.append(snapshot)
        histories.append(history)
    if not chunks:
        raise FileNotFoundError("No Freddie orig/perf file pairs found.")
    return _attach_history(pl.concat(chunks), histories)


def _build_loan_sample_pool(
    pairs: list[tuple[Path, Path]],
    pool_target: int,
    seed: int,
    term_months: int | None = 360,
) -> pl.DataFrame:
    """
    Memory-safe pool: oversample per quarterly file instead of materializing
    the full loan universe (~12M rows).
    """
    per_file = max(1000, pool_target // max(len(pairs), 1))
    chunks, histories, seen = [], [], set()
    for i, (orig_path, perf_path) in enumerate(pairs):
        df, history, ids = _snapshot_inputs_one_pair(orig_path, perf_path, term_months=term_months)
        if seen.intersection(ids):
            raise ValueError('Overlapping origination files in sample pool')
        seen.update(ids)
        histories.append(history)
        if len(df) == 0:
            continue
        k = min(per_file, len(df))
        chunks.append(df.sample(n=k, seed=seed + i))
    if not chunks:
        raise FileNotFoundError("No Freddie orig/perf file pairs found.")
    return _attach_history(pl.concat(chunks), histories)


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
    term_months: int | None = 360,
) -> pl.DataFrame:
    """Build stratified loan sample parquet for microsim."""
    if output.exists() and not force_rebuild:
        print(f"Loading cached loan sample from {output}")
        return pl.read_parquet(output)
    if output.exists():
        raise FileExistsError('Preserve the prior sample; pass a new output path for the corrected rebuild')

    pairs = discover_raw_files(raw_dir)
    if not pairs:
        print("No raw files; generating synthetic fixture …")
        generate_synthetic_fixture()
        pairs = discover_raw_files(raw_dir)

    print(f"Building stratified loan pool from {len(pairs)} file pair(s) …")
    pool = _build_loan_sample_pool(pairs, pool_target=n_loans * 4, seed=seed, term_months=term_months)
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
        if LOAN_SAMPLE_PATH.exists():
            raise FileExistsError('Preserve the prior sample; use build_loan_sample with a new output path')
        from prepare_freddie import ensure_raw_files
        ensure_raw_files()
    # Pass the module-global path explicitly: build_loan_sample's default was
    # bound at def time, which silently ignored any override of
    # loan_sample.LOAN_SAMPLE_PATH (same value in production either way).
    return build_loan_sample(n_loans=n_loans, output=LOAN_SAMPLE_PATH,
                             force_rebuild=force_rebuild)


if __name__ == "__main__":
    df = build_loan_sample(force_rebuild=True)
    print(df.head())
    print(f"Strata: {df['stratum_id'].n_unique()}")
