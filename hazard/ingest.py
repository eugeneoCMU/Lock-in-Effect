"""
Freddie Mac loan-level ingest → cohort-month panel (Polars lazy scan).

Never materializes full loan-level frames; aggregates immediately to
(vintage, coupon, fico_bucket, ltv_bucket, period) cells.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
import polars as pl

from config import (
    COUPON_STEP,
    DATA_DIR,
    FICO_BINS,
    LTV_THRESHOLD,
    PANEL_PATH,
    RAW_DIR,
    VINTAGE_YEARS,
)
from schema import ORIG_COLS, PERF_COLS, ZB_VOLUNTARY_PREPAY

# Columns to read from raw files (by name after rename)
ORIG_READ = [
    "credit_score", "first_payment_date", "original_upb", "original_ltv",
    "original_interest_rate", "loan_sequence_number", "amortization_type",
    "property_state",
]
PERF_READ = [
    "loan_sequence_number", "reporting_period", "current_upb",
    "delinquency_status", "loan_age", "zero_balance_code", "borrower_assistance",
]


def _fico_bucket(score: pl.Expr) -> pl.Expr:
    return (
        pl.when(score < 680).then(pl.lit("<680"))
        .when(score < 740).then(pl.lit("680-740"))
        .otherwise(pl.lit("740+"))
    )


def _ltv_bucket(ltv: pl.Expr) -> pl.Expr:
    return pl.when(ltv <= LTV_THRESHOLD).then(pl.lit("≤80")).otherwise(pl.lit(">80"))


def _coupon_bucket(rate: pl.Expr) -> pl.Expr:
    return (rate / COUPON_STEP).round(0) * COUPON_STEP


def _vintage_from_seq(seq: pl.Expr) -> pl.Expr:
    """Extract origination year from F20Q1XXXXXXX (year at positions 1-2)."""
    return seq.str.slice(1, 2).cast(pl.Int64) + 2000


def _map_servicer_state(delinq: pl.Expr, assistance: pl.Expr, zb: pl.Expr) -> pl.Expr:
    """Map raw delinquency / assistance / ZB code to Markov pipeline state."""
    return (
        pl.when(zb == ZB_VOLUNTARY_PREPAY).then(pl.lit("Prepaid"))
        .when(zb.is_in(["02", "03", "09", "15"])).then(pl.lit("Defaulted"))
        .when(assistance == "F").then(pl.lit("Forbearance"))
        .when(delinq == "0").then(pl.lit("Current"))
        .when(delinq == "1").then(pl.lit("D30"))
        .when(delinq == "2").then(pl.lit("D60"))
        .when(delinq.is_in(["3", "4", "5", "6", "7", "8", "9"])).then(pl.lit("D90+"))
        .when(delinq.is_in(["RA", "RP"])).then(pl.lit("Defaulted"))
        .otherwise(pl.lit("Current"))
    )


def _scan_orig(path: Path) -> pl.LazyFrame:
    lf = pl.scan_csv(
        path,
        separator="|",
        has_header=False,
        new_columns=ORIG_COLS,
        infer_schema_length=0,
        truncate_ragged_lines=True,
    )
    return (
        lf.select([
            pl.col("credit_score").cast(pl.Float64, strict=False),
            pl.col("first_payment_date").cast(pl.Utf8),
            pl.col("original_upb").cast(pl.Float64, strict=False),
            pl.col("original_ltv").cast(pl.Float64, strict=False),
            pl.col("original_interest_rate").cast(pl.Float64, strict=False),
            pl.col("loan_sequence_number").cast(pl.Utf8),
            pl.col("amortization_type").cast(pl.Utf8),
            pl.col("property_state").cast(pl.Utf8),
        ])
        .filter(pl.col("amortization_type") == "FRM")
        .filter(pl.col("original_upb") > 0)
        .filter(pl.col("original_ltv").is_between(1, 200))
        .filter(pl.col("credit_score").is_between(300, 850))
        .with_columns([
            _coupon_bucket(pl.col("original_interest_rate") / 100.0).alias("coupon"),
            _fico_bucket(pl.col("credit_score")).alias("fico_bucket"),
            _ltv_bucket(pl.col("original_ltv")).alias("ltv_bucket"),
            _vintage_from_seq(pl.col("loan_sequence_number")).alias("vintage"),
        ])
    )


def _scan_perf(path: Path) -> pl.LazyFrame:
    lf = pl.scan_csv(
        path,
        separator="|",
        has_header=False,
        new_columns=PERF_COLS,
        infer_schema_length=0,
        truncate_ragged_lines=True,
    )
    return (
        lf.select([
            pl.col("loan_sequence_number").cast(pl.Utf8),
            pl.col("reporting_period").cast(pl.Utf8),
            pl.col("current_upb").cast(pl.Float64, strict=False),
            pl.col("delinquency_status").cast(pl.Utf8),
            pl.col("loan_age").cast(pl.Float64, strict=False).alias("loan_age"),
            pl.col("zero_balance_code").cast(pl.Utf8).fill_null(""),
            pl.col("borrower_assistance").cast(pl.Utf8).fill_null(""),
        ])
        .filter(pl.col("current_upb") >= 0)
        .with_columns([
            _map_servicer_state(
                pl.col("delinquency_status"),
                pl.col("borrower_assistance"),
                pl.col("zero_balance_code"),
            ).alias("servicer_state"),
            (pl.col("zero_balance_code") == ZB_VOLUNTARY_PREPAY).alias("is_prepay"),
        ])
    )


def discover_raw_files(raw_dir: Path = RAW_DIR) -> list[tuple[Path, Path]]:
    """Return (orig_path, perf_path) pairs found in raw_dir."""
    pairs = []
    if not raw_dir.exists():
        return pairs
    for year in VINTAGE_YEARS:
        for pattern in [
            (f"orig_{year}.txt", f"perf_{year}.txt"),
            (f"orig_{year}Q1.txt", f"perf_{year}Q1.txt"),
        ]:
            o, p = raw_dir / pattern[0], raw_dir / pattern[1]
            if o.exists() and p.exists():
                pairs.append((o, p))
    # Also pick up any orig_*.txt / perf_*.txt pairs
    for o in sorted(raw_dir.glob("orig_*.txt")):
        suffix = o.stem.replace("orig_", "")
        p = raw_dir / f"perf_{suffix}.txt"
        if p.exists() and (o, p) not in pairs:
            pairs.append((o, p))
    return pairs


def filter_pairs(
    pairs: list[tuple[Path, Path]],
    years: list[int] | None = None,
) -> list[tuple[Path, Path]]:
    """Keep pairs whose suffix starts with one of `years` (e.g. 2020, 2020Q1)."""
    if not years:
        return pairs
    yr = {str(y) for y in years}
    out = []
    for o, p in pairs:
        suffix = o.stem.replace("orig_", "")
        if any(suffix.startswith(y) for y in yr):
            out.append((o, p))
    return out


def build_panel_from_files(
    pairs: Iterable[tuple[Path, Path]],
    output: Path = PANEL_PATH,
) -> pl.DataFrame:
    """Lazy-scan Freddie files and aggregate to cohort-month panel."""
    agg_dfs: list[pl.DataFrame] = []
    for orig_path, perf_path in pairs:
        print(f"  Scanning {orig_path.name} + {perf_path.name} …")
        orig = _scan_orig(orig_path)
        perf = _scan_perf(perf_path)
        joined = perf.join(orig, on="loan_sequence_number", how="inner")
        joined = joined.with_columns([
            pl.col("current_upb")
            .shift(1)
            .over("loan_sequence_number")
            .alias("prev_upb"),
        ])
        agg = (
            joined
            .group_by([
                "vintage", "coupon", "fico_bucket", "ltv_bucket",
                "reporting_period",
            ])
            .agg([
                pl.col("current_upb").sum().alias("exposure_upb"),
                pl.col("original_upb").sum().alias("orig_upb_sum"),
                pl.when(pl.col("is_prepay"))
                  .then(
                      pl.col("prev_upb").fill_null(pl.col("original_upb"))
                  )
                  .otherwise(0.0)
                  .sum()
                  .alias("prepaid_upb"),
                pl.col("loan_age").mean().alias("mean_loan_age"),
                pl.col("servicer_state").mode().first().alias("mode_state"),
                pl.len().alias("loan_count"),
            ])
        )
        agg_dfs.append(agg.collect())
        print(f"    → {len(agg_dfs[-1]):,} cohort-month cells")

    if not agg_dfs:
        raise FileNotFoundError("No Freddie orig/perf file pairs found.")

    panel = pl.concat(agg_dfs)
    # Same vintage year spans multiple origination quarters — sum cohort-month cells
    panel = panel.group_by([
        "vintage", "coupon", "fico_bucket", "ltv_bucket", "reporting_period",
    ]).agg([
        pl.col("exposure_upb").sum(),
        pl.col("orig_upb_sum").sum(),
        pl.col("prepaid_upb").sum(),
        pl.col("mean_loan_age").mean(),
        pl.col("mode_state").first(),
        pl.col("loan_count").sum(),
    ])
    panel = (
        panel
        .sort(["vintage", "coupon", "fico_bucket", "ltv_bucket", "reporting_period"])
        .with_columns([
            (pl.col("prepaid_upb") / pl.col("exposure_upb").clip(lower_bound=1))
            .alias("monthly_prepay_rate"),
        ])
    )
    # Dynamic burnout: cumulative prepaid share of original balance per cohort
    panel = panel.with_columns([
        pl.col("reporting_period").str.to_datetime("%Y%m").alias("period"),
    ])
    panel = panel.sort(["vintage", "coupon", "fico_bucket", "ltv_bucket", "period"])
    panel = panel.with_columns([
        (pl.col("prepaid_upb").cum_sum().over(
            ["vintage", "coupon", "fico_bucket", "ltv_bucket"]
        ) / pl.col("orig_upb_sum").clip(lower_bound=1))
        .alias("burnout"),
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    panel.write_parquet(output)
    print(f"Cohort-month panel saved: {output} ({len(panel):,} rows)")
    return panel


def generate_synthetic_fixture(
    n_loans: int = 5000,
    n_months: int = 48,
    output_dir: Path = RAW_DIR,
    seed: int = 42,
) -> tuple[Path, Path]:
    """
    Write minimal orig_2020.txt + perf_2020.txt for pipeline testing
    before real Freddie files are downloaded.
    """
    rng = np.random.default_rng(seed)
    output_dir.mkdir(parents=True, exist_ok=True)
    orig_path = output_dir / "orig_2020.txt"
    perf_path = output_dir / "perf_2020.txt"

    coupons = [0.020, 0.025, 0.030, 0.035]
    fico_centers = [650, 710, 780]
    orig_lines, perf_lines = [], []

    def _pad(row: list, n: int = 32) -> str:
        while len(row) < n:
            row.append("")
        return "|".join(row[:n])

    for i in range(n_loans):
        seq = f"F20Q1{rng.integers(1000000, 9999999):07d}"
        coupon = rng.choice(coupons)
        fico = int(rng.choice(fico_centers) + rng.integers(-30, 30))
        fico = int(np.clip(fico, 300, 850))
        ltv = int(rng.choice([70, 75, 80, 85, 90]))
        upb = round(rng.uniform(100_000, 400_000), 2)
        fpd = "202006"
        rate_str = f"{coupon:.3f}"

        orig_row = [""] * 32
        orig_row[0] = str(fico)
        orig_row[1] = fpd
        orig_row[10] = f"{upb:.2f}"
        orig_row[11] = str(ltv)
        orig_row[12] = rate_str
        orig_row[15] = "FRM"
        orig_row[16] = "CA"
        orig_row[19] = seq
        orig_row[21] = "360"
        orig_lines.append(_pad(orig_row))

        balance = upb
        cum_prepay = 0.0
        yr, mo = 2020, 6
        for m in range(n_months):
            period = f"{yr}{mo:02d}"

            gap = max(0, coupon - 0.065)
            hazard = 0.002 + 0.01 * gap + rng.uniform(0, 0.003)
            hazard *= max(0.3, 1.0 - cum_prepay / upb)
            prepay = balance * hazard
            zb = "01" if prepay > balance * 0.9 else ""
            if zb == "01":
                balance = 0
            else:
                balance = max(0, balance - prepay)
                cum_prepay += prepay
            delinq = "0" if rng.random() > 0.02 else "1"
            assist = "F" if delinq != "0" and rng.random() < 0.1 else ""

            perf_row = [""] * 32
            perf_row[0] = seq
            perf_row[1] = period
            perf_row[2] = f"{balance:.2f}"
            perf_row[3] = delinq
            perf_row[4] = str(m + 1)
            perf_row[8] = zb
            perf_row[28] = assist
            perf_lines.append(_pad(perf_row))
            mo += 1
            if mo > 12:
                mo = 1
                yr += 1
            if balance <= 0:
                break

    orig_path.write_text("\n".join(orig_lines))
    perf_path.write_text("\n".join(perf_lines))
    print(f"Synthetic fixture: {orig_path} ({n_loans} loans), {perf_path}")
    return orig_path, perf_path


def load_or_build_panel(
    raw_dir: Path = RAW_DIR,
    force_synthetic: bool = False,
    force_rebuild: bool = False,
    years: list[int] | None = None,
) -> pl.DataFrame:
    """Load cached panel or build from raw Freddie files / synthetic fixture."""
    from prepare_freddie import ensure_raw_files

    if PANEL_PATH.exists() and not force_synthetic and not force_rebuild:
        print(f"Loading cached panel from {PANEL_PATH}")
        return pl.read_parquet(PANEL_PATH)

    if ensure_raw_files(dest_dir=raw_dir):
        force_synthetic = False
        if PANEL_PATH.exists() and force_rebuild:
            PANEL_PATH.unlink()

    pairs = discover_raw_files(raw_dir)
    pairs = filter_pairs(pairs, years)
    if not pairs or force_synthetic:
        if pairs:
            print("No usable pairs after prepare; falling back to synthetic fixture …")
        else:
            print("Building panel from synthetic fixture …")
        if PANEL_PATH.exists():
            PANEL_PATH.unlink()
        generate_synthetic_fixture()
        pairs = discover_raw_files(raw_dir)

    return build_panel_from_files(pairs)


if __name__ == "__main__":
    panel = load_or_build_panel(force_synthetic=True)
    print(panel.head())
    print(f"Shape: {panel.shape}")
    print(f"Cohorts: {panel.select(['vintage','coupon','fico_bucket','ltv_bucket']).unique().shape[0]}")
