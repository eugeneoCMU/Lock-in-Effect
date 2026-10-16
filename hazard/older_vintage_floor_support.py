#!/usr/bin/env python3
"""Bounded, local-only Fannie acquisition-tail support pilot.

See specs/SPEC_2026-10-09_older_vintage_floor_support.md. This module does not
import production configuration, modify the model, or write to source data.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/SPEC_2026-10-09_older_vintage_floor_support.md"
DEFAULT_SOURCE = Path("/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data")
DEFAULT_OUTPUT = ROOT / "output/research-limits/2026-10-09/floor"
RATE_URL = ("https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"
            "&cosd=2018-01-01&coed=2018-12-31")
STRATA = ["vintage", "coupon", "fico_bucket", "ltv_bucket"]
KEYS = STRATA + ["reporting_period"]
ADDITIVE = ["exposure_upb", "orig_upb_sum", "prepaid_upb", "loan_count"]
OPENING = ["opening_exposure_upb", "opening_prepaid_upb", "opening_end_exposure_upb"]
GAPS_BP = [0, -25, -50, -100, -200]
MIN_AGES = [12, 24, 36, 60]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _check_source_rows(rows: pd.DataFrame, allow_missing_age: bool = False) -> None:
    if rows.duplicated(["source_quarter"] + KEYS).any():
        raise ValueError("Duplicate cohort-month rows within an acquisition quarter")
    required = KEYS + ADDITIVE + ([] if allow_missing_age else ["mean_loan_age"])
    if rows[required].isna().any().any():
        raise ValueError("Missing input sufficient statistics")
    if (rows[ADDITIVE] < 0).any().any() or (rows.loan_count <= 0).any():
        raise ValueError("Negative sufficient statistic or nonpositive loan count")


def prepare_source_rows(rows: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Remove pre-acquisition history and form genuine adjacent-quarter lags."""
    _check_source_rows(rows, allow_missing_age=True)
    frame = rows.copy()
    parts = frame.source_quarter.str.extract(r"^FNMA(\d{4})Q([1-4])$")
    if parts.isna().any().any():
        raise ValueError("Invalid acquisition-quarter identifier")
    frame["period"] = pd.to_datetime(frame.reporting_period, format="%Y%m")
    starts = pd.to_datetime(dict(year=parts[0].astype(int),
                                month=(parts[1].astype(int) - 1) * 3 + 1,
                                day=1))
    before = frame.period < starts
    audit = {
        "performance_before_acquisition_rows": int(before.sum()),
        "performance_before_acquisition_exposure": float(frame.loc[before, "exposure_upb"].sum()),
        "performance_before_acquisition_2018_rows": int((before & (frame.period.dt.year == 2018)).sum()),
    }
    frame = frame.loc[~before].copy().sort_values(["source_quarter"] + KEYS)
    within = frame.groupby(["source_quarter"] + STRATA, sort=False, observed=True)
    lag_date = within.period.shift()
    lag_upb = within.exposure_upb.shift()
    adjacent = ((frame.period.dt.year * 12 + frame.period.dt.month)
                - (lag_date.dt.year * 12 + lag_date.dt.month) == 1)
    valid = adjacent & lag_upb.gt(0)
    frame["opening_exposure_upb"] = lag_upb.where(valid, 0.0)
    frame["opening_prepaid_upb"] = frame.prepaid_upb.where(valid, 0.0)
    frame["opening_end_exposure_upb"] = frame.exposure_upb.where(valid, 0.0)
    # A missing current age cannot qualify for an age cut. Its prior balance can
    # still be a valid denominator for the following month, so form lags first.
    missing_age = frame.mean_loan_age.isna()
    audit['missing_age_rows'] = int(missing_age.sum())
    audit['missing_age_2018_rows'] = int((missing_age & (frame.period.dt.year == 2018)).sum())
    audit['missing_age_2018_exposure'] = float(frame.loc[missing_age & (frame.period.dt.year == 2018), 'exposure_upb'].sum())
    frame = frame.loc[~missing_age].copy()
    audit["kept_rows"] = len(frame)
    return frame, audit


def combine_cells(rows: pd.DataFrame, age_convention: str = "loan_count_weighted") -> pd.DataFrame:
    """Combine additive cells; age is recoverable from count and mean age."""
    _check_source_rows(rows)
    if age_convention not in {"loan_count_weighted", "legacy"}:
        raise ValueError("Unknown age convention")
    frame = rows.copy()
    frame["age_count_sum"] = frame.mean_loan_age * frame.loan_count
    for col in OPENING:
        if col not in frame:
            frame[col] = 0.0
    grouped = frame.groupby(KEYS, sort=True, observed=True, dropna=False)
    result = grouped[ADDITIVE + OPENING + ["age_count_sum"]].sum()
    result["mean_loan_age"] = (result.age_count_sum / result.loan_count
                               if age_convention == "loan_count_weighted"
                               else grouped.mean_loan_age.mean())
    result["mode_state"] = grouped.mode_state.first()
    result = result.reset_index().drop(columns="age_count_sum")
    result["period"] = pd.to_datetime(result.reporting_period, format="%Y%m")
    for col in ADDITIVE + OPENING:
        if not np.isclose(result[col].sum(), frame[col].sum(), rtol=1e-12, atol=1e-7):
            raise ValueError(f"Additive conservation failed: {col}")
    return result


def legacy_parity(paths: list[Path], reference_path: Path) -> dict:
    """Reproduce the frozen production combination before inspecting outcomes."""
    frames = [pl.read_parquet(p).drop(["monthly_prepay_rate", "period", "burnout"])
              for p in paths]
    rebuilt = (pl.concat(frames).group_by(KEYS).agg([
        pl.col("exposure_upb").sum(), pl.col("orig_upb_sum").sum(),
        pl.col("prepaid_upb").sum(), pl.col("mean_loan_age").mean(),
        pl.col("mode_state").first(), pl.col("loan_count").sum(),
    ]).filter(pl.col("vintage").is_in(list(range(2017, 2022)))).sort(KEYS)
        .with_columns((pl.col("prepaid_upb") / pl.col("exposure_upb").clip(lower_bound=1))
                      .alias("monthly_prepay_rate"))
        .with_columns(pl.col("reporting_period").str.to_datetime("%Y%m").alias("period"))
        .sort(STRATA + ["period"])
        .with_columns((pl.col("prepaid_upb").cum_sum().over(STRATA)
                       / pl.col("orig_upb_sum").clip(lower_bound=1)).alias("burnout")))
    reference = pl.read_parquet(reference_path).sort(STRATA + ["period"])
    a, b = rebuilt.to_pandas(), reference.to_pandas()
    keys_equal = len(a) == len(b) and a[KEYS].equals(b[KEYS])
    audit = {"rows": len(a), "reference_rows": len(b), "keys_exact": keys_equal,
             "absolute_tolerance": 1e-7, "relative_tolerance": 1e-12, "numeric": {}}
    if not keys_equal:
        audit["passed"] = False
        return audit
    for col in ADDITIVE + ["mean_loan_age", "monthly_prepay_rate", "burnout"]:
        x, y = a[col].to_numpy(), b[col].to_numpy()
        ok = bool(np.array_equal(x, y)) if col == "loan_count" else bool(
            np.allclose(x, y, rtol=1e-12, atol=1e-7, equal_nan=True))
        audit["numeric"][col] = {"passed": ok, "exact_equal_rows": int(np.sum(x == y)),
                                  "max_abs_difference": float(np.nanmax(np.abs(x.astype(float) - y)))}
    audit["period_exact"] = a.period.equals(b.period)
    audit["mode_state_differences"] = int((a.mode_state != b.mode_state).sum())
    audit["passed"] = audit["period_exact"] and all(x["passed"] for x in audit["numeric"].values())
    return audit


def monthly_rates(payload: bytes, require_complete: bool = True) -> dict[str, float]:
    data = pd.read_csv(io.BytesIO(payload))
    if "MORTGAGE30US" not in data or data.columns[0] not in {"observation_date", "DATE"}:
        raise ValueError("Unexpected FRED response schema")
    data["date"] = pd.to_datetime(data.iloc[:, 0])
    data["value"] = pd.to_numeric(data.MORTGAGE30US, errors="coerce")
    data = data[(data.date.dt.year == 2018) & data.value.notna()].copy()
    if data.date.duplicated().any():
        raise ValueError("Duplicate FRED observation dates")
    if (data.value <= 0).any():
        raise ValueError("Nonpositive FRED mortgage rate")
    data["ym"] = data.date.dt.strftime("%Y%m")
    rates = (data.groupby("ym").value.mean() / 100).to_dict()
    if require_complete and set(rates) != {f"2018{m:02d}" for m in range(1, 13)}:
        raise ValueError("Require all twelve months of 2018 rates")
    return rates


def _annualized_pct(prepaid: float, exposure: float) -> float | None:
    smm = prepaid / exposure if exposure > 0 else np.nan
    return float(100 * (1 - (1 - smm) ** 12)) if 0 <= smm <= 1 else None


def summarize_support(selected: pd.DataFrame, min_outcome_cells: int = 30,
                      min_outcome_strata: int = 5) -> dict:
    """Dollar-month support and aggregate annualization; no cell outcomes emitted."""
    selected = selected[selected.exposure_upb > 0]
    exposure = float(selected.exposure_upb.sum())
    by_stratum = selected.groupby(STRATA, observed=True).exposure_upb.sum()
    n, k = len(selected), len(by_stratum)
    visible = n >= min_outcome_cells and k >= min_outcome_strata
    opening = float(selected.opening_exposure_upb.sum()) if "opening_exposure_upb" in selected else 0.0
    opening_end = float(selected.opening_end_exposure_upb.sum()) if "opening_end_exposure_upb" in selected else 0.0
    opening_prepaid = float(selected.opening_prepaid_upb.sum()) if "opening_prepaid_upb" in selected else 0.0
    # Apply disclosure threshold again to the smaller lag-matched subset.
    matched = selected[selected.opening_exposure_upb > 0] if "opening_exposure_upb" in selected else selected.iloc[:0]
    opening_visible = (len(matched) >= min_outcome_cells
                       and len(matched[STRATA].drop_duplicates()) >= min_outcome_strata)
    return {
        "cohort_months": n, "strata": k, "months": int(selected.reporting_period.nunique()),
        "exposure_dollar_months": exposure, "loan_months": int(selected.loan_count.sum()),
        "effective_cohort_months": float(exposure**2 / selected.exposure_upb.pow(2).sum()) if exposure else 0.0,
        "effective_strata": float(exposure**2 / by_stratum.pow(2).sum()) if exposure else 0.0,
        "largest_stratum_exposure_share": float(by_stratum.max() / exposure) if exposure else None,
        "annualized_end_exposure_cpr_pct": _annualized_pct(float(selected.prepaid_upb.sum()), exposure) if visible else None,
        "outcome_suppressed_for_small_support": not visible,
        "opening_exposure_dollar_months": opening,
        "opening_matched_cohort_months": len(matched),
        "opening_matched_end_exposure_share": opening_end / exposure if exposure else None,
        "annualized_lag_opening_cpr_pct": _annualized_pct(opening_prepaid, opening) if opening_visible else None,
    }


def _population(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if name == "production_origins_2017_2021":
        return frame[frame.vintage.between(2017, 2021)]
    if name == "older_acquisition_tail_le2016":
        return frame[frame.vintage <= 2016]
    if name == "older_tail_2015_2016":
        return frame[frame.vintage.between(2015, 2016)]
    if name == "older_tail_le2014":
        return frame[frame.vintage <= 2014]
    return frame[frame.vintage <= 2021]


def _select(frame: pd.DataFrame, age: int, gap_bp: int) -> pd.DataFrame:
    return frame[(frame.mean_loan_age >= age - 1e-10) & (frame.gap <= gap_bp / 10000 + 1e-12)]


def run(source_data: Path, output: Path, fetch_rates: bool = False) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    spec_hash = sha256(SPEC)
    frozen = output / "spec_frozen.md"
    if frozen.exists() and sha256(frozen) != spec_hash:
        raise ValueError("Frozen specification differs; do not overwrite it")
    if not frozen.exists():
        shutil.copyfile(SPEC, frozen)
        (output / "spec_freeze.json").write_text(json.dumps({
            "sha256": spec_hash, "frozen_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2) + "\n")
    quarter_dir = source_data / "fannie_quarters"
    tags = [f"FNMA{y}Q{q}" for y in range(2017, 2023) for q in range(1, 5)]
    paths = [quarter_dir / f"cells_{tag}.parquet" for tag in tags]
    reference_path = source_data / "cohort_month_panel_fannie.parquet"
    manifest_path = quarter_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if not set(tags).issubset(manifest):
        raise ValueError("Required quarter absent from source manifest")
    if len({p.resolve() for p in paths}) != 24:
        raise ValueError("Duplicate quarter input paths")
    hashes = {str(p): sha256(p) for p in paths + [reference_path, manifest_path]}
    rows = []
    for tag, path in zip(tags, paths):
        frame = pd.read_parquet(path)
        if len(frame) != manifest[tag]["cells_rows"]:
            raise ValueError(f"Manifest row mismatch: {tag}")
        frame["source_quarter"] = tag
        rows.append(frame)
    raw = pd.concat(rows, ignore_index=True)
    _check_source_rows(raw, allow_missing_age=True)
    parity = legacy_parity(paths, reference_path)
    (output / "parity.json").write_text(json.dumps(parity, indent=2) + "\n")
    if not parity["passed"]:
        raise ValueError("Filtered Fannie parity failed; no new outcomes calculated")
    prepared, acquisition_audit = prepare_source_rows(raw)
    rate_path = output / "MORTGAGE30US_2018_fred.csv"
    if not rate_path.exists():
        if not fetch_rates:
            raise ValueError("Missing frozen rates: use --fetch-rates once")
        with urlopen(RATE_URL, timeout=45) as response:
            payload = response.read()
            metadata = {"url": RATE_URL, "response_url": response.url,
                        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                        "content_type": response.headers.get("Content-Type"),
                        "sha256": hashlib.sha256(payload).hexdigest()}
        monthly_rates(payload)  # Validate before persisting the downloaded bytes.
        rate_path.write_bytes(payload)
        (output / "rate_source.json").write_text(json.dumps(metadata, indent=2) + "\n")
    metadata = json.loads((output / "rate_source.json").read_text())
    if metadata["sha256"] != sha256(rate_path):
        raise ValueError("Frozen rate bytes failed recorded hash")
    rates = monthly_rates(rate_path.read_bytes())
    (output / "monthly_rates.json").write_text(json.dumps(rates, indent=2) + "\n")
    panels = {}
    for convention in ("loan_count_weighted", "legacy"):
        panel = combine_cells(prepared, convention)
        panel = panel[(panel.period.dt.year == 2018) & (panel.coupon > 0)
                      & (panel.exposure_upb > 0)].copy()
        panel["market_rate"] = panel.reporting_period.map(rates)
        if panel.market_rate.isna().any():
            raise ValueError("Unmatched 2018 market rate")
        panel["gap"] = panel.coupon - panel.market_rate
        panels[convention] = panel
    populations = ["production_origins_2017_2021", "older_acquisition_tail_le2016",
                   "older_tail_2015_2016", "older_tail_le2014", "union_le2021"]
    grid, age_bins, membership = [], [], []
    for convention, panel in panels.items():
        for name in populations:
            population = _population(panel, name)
            for age in MIN_AGES:
                base_exposure = float(_select(population, age, 0).exposure_upb.sum())
                for gap_bp in GAPS_BP:
                    selected = _select(population, age, gap_bp)
                    row = dict(age_convention=convention, population=name, minimum_age=age,
                               gap_max_bp=gap_bp, **summarize_support(selected))
                    row["exposure_share_of_gap0_same_age"] = row["exposure_dollar_months"] / base_exposure if base_exposure else None
                    grid.append(row)
            for low, high in ((12, 24), (24, 36), (36, 60), (60, None)):
                selected = _select(population, low, -25)
                if high is not None:
                    selected = selected[selected.mean_loan_age < high - 1e-10]
                age_bins.append(dict(age_convention=convention, population=name,
                                     age_lower=low, age_upper=high, gap_max_bp=-25,
                                     **summarize_support(selected)))
    for name in populations:
        for age in MIN_AGES:
            for gap in GAPS_BP:
                a = _select(_population(panels["loan_count_weighted"], name), age, gap).set_index(KEYS)
                b = _select(_population(panels["legacy"], name), age, gap).set_index(KEYS)
                added, removed = a.index.difference(b.index), b.index.difference(a.index)
                membership.append(dict(population=name, minimum_age=age, gap_max_bp=gap,
                                       added_cohort_months=len(added), removed_cohort_months=len(removed),
                                       added_exposure=float(a.loc[added, "exposure_upb"].sum()),
                                       removed_exposure=float(b.loc[removed, "exposure_upb"].sum())))
    raw_2018 = prepared[(prepared.period.dt.year == 2018) & (prepared.exposure_upb > 0)]
    acquisition_support = []
    for name in populations:
        for quarter, sub in _population(raw_2018, name).groupby("source_quarter"):
            acquisition_support.append(dict(population=name, source_quarter=quarter,
                quarter_cohort_months=len(sub), exposure_dollar_months=float(sub.exposure_upb.sum()),
                loan_months=int(sub.loan_count.sum()), earliest_vintage=int(sub.vintage.min()),
                latest_vintage=int(sub.vintage.max())))
    unchanged = all(sha256(Path(path)) == digest for path, digest in hashes.items())
    if not unchanged:
        raise ValueError("A source input changed during analysis")
    results = {
        "created_utc": datetime.now(timezone.utc).isoformat(), "spec_sha256": spec_hash,
        "source_data": str(source_data.resolve()), "source_hashes": hashes,
        "source_inputs_unchanged": unchanged, "source_quarters": len(paths),
        "raw_quarter_cohort_months": len(raw), "combined_2018_cohort_months": len(panels["loan_count_weighted"]),
        "parity": parity, "acquisition_audit": acquisition_audit,
        "rate_source": metadata, "grid": grid, "age_bins_at_minus25bp": age_bins,
        "age_convention_membership_changes": membership,
        "acquisition_quarter_support": acquisition_support,
        "limitations": [
            "Older origins are a selected acquisition tail, not representative older Fannie or Freddie loans.",
            "Age cuts use cohort mean ages; individual-loan age support cannot be recovered.",
            "Exposure sums are dollar-months, not a point-in-time balance or unique loan exposure.",
            "Effective cell/stratum counts measure exposure concentration, not independent sample size.",
            "Voluntary payoff includes both refinancing and sale; CPR is a descriptive annualization.",
            "End-UPB and lagged-opening-UPB rates are accounting sensitivities, not identified causal turnover floors.",
            "Aggregate cells cannot establish individual-loan disjointness or correct late-acquisition selection.",
        ],
    }
    (output / "results.json").write_text(json.dumps(results, indent=2, allow_nan=False) + "\n")
    pd.DataFrame(grid).to_csv(output / "support_grid.csv", index=False)
    pd.DataFrame(age_bins).to_csv(output / "age_bins.csv", index=False)
    pd.DataFrame(membership).to_csv(output / "age_convention_changes.csv", index=False)
    pd.DataFrame(acquisition_support).to_csv(output / "acquisition_support.csv", index=False)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-data", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fetch-rates", action="store_true")
    args = parser.parse_args()
    results = run(args.source_data, args.output, args.fetch_rates)
    headline = [r for r in results["grid"] if r["age_convention"] == "loan_count_weighted"
                and r["minimum_age"] == 24 and r["gap_max_bp"] == -25
                and r["population"] in {"production_origins_2017_2021", "older_acquisition_tail_le2016"}]
    print(json.dumps({"parity_passed": results["parity"]["passed"], "headline": headline,
                      "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
