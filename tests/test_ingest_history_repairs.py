"""Fixed cohort history and exact age statistics across raw source partitions."""
import os
import sys
from pathlib import Path

import polars as pl
import pytest
from polars.testing import assert_frame_equal

os.environ.setdefault("FRED_API_KEY", "test-no-network")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))
from hazard import ingest
from hazard.fannie_replication import combine_quarter_cells


def origins(ids, coupons=None):
    n = len(ids)
    return pl.DataFrame({
        "loan_sequence_number": ids, "vintage": [2020] * n,
        "coupon": coupons if coupons is not None else [.03] * n,
        "fico_bucket": ["high"] * n, "ltv_bucket": ["low"] * n,
        "original_upb": [100.] * n,
    })


def histories(ids, ages):
    n = len(ids)
    return pl.DataFrame({
        "loan_sequence_number": ids, "reporting_period": ["202301"] * n,
        "current_upb": [80.] * n, "is_prepay": [False] * n,
        "loan_age": pl.Series(ages, dtype=pl.Float64),
        "servicer_state": ["Current"] * n,
    })


def mock_sources(monkeypatch, tmp_path, frames):
    pairs = [(tmp_path / f"orig_{i}", tmp_path / f"perf_{i}") for i in range(len(frames))]
    origs = {op: frame[0] for (op, _), frame in zip(pairs, frames)}
    perfs = {pp: frame[1] for (_, pp), frame in zip(pairs, frames)}
    monkeypatch.setattr(ingest, "_scan_orig", lambda path: origs[path].lazy())
    monkeypatch.setattr(ingest, "_scan_perf", lambda path: perfs[path].lazy())
    return pairs


def test_missing_loan_ages_pool_by_finite_count_across_unequal_sources(monkeypatch, tmp_path):
    # File means are 10 and 30; file sizes are 3 and 4, but only one and
    # three ages respectively are observed. The exact pooled mean is 25.
    pairs = mock_sources(monkeypatch, tmp_path, [
        (origins(["a", "b", "c"]), histories(["a", "b", "c"], [10., None, float("nan")])),
        (origins(["d", "e", "f", "g"]), histories(["d", "e", "f", "g"], [20., 30., 40., float("inf")])),
    ])
    one_shot = ingest.build_panel_from_files(pairs, tmp_path / "one_shot.parquet")
    cell_paths = []
    for i, pair in enumerate(pairs):
        dest = tmp_path / f"cells_{i}.parquet"
        ingest.build_panel_from_files([pair], dest)
        cell_paths.append(dest)
    combined = combine_quarter_cells(cell_paths, tmp_path / "combined.parquet")
    assert_frame_equal(combined, one_shot)
    assert combined["finite_age_sum"].item() == 100.
    assert combined["finite_age_count"].item() == 4
    assert combined["loan_count"].item() == 7
    assert combined["mean_loan_age"].item() == pytest.approx(25.)
    assert combined["cohort_original_upb"].item() == 700.


def test_duplicate_performance_loan_month_rejected_before_output(monkeypatch, tmp_path):
    perf = histories(["a", "a"], [1., 1.])
    pairs = mock_sources(monkeypatch, tmp_path, [(origins(["a"]), perf)])
    output = tmp_path / "panel.parquet"
    with pytest.raises(ValueError, match="Duplicate loan-month"):
        ingest.build_panel_from_files(pairs, output)
    assert not output.exists()


def test_overlapping_origination_sources_rejected_before_output(monkeypatch, tmp_path):
    pairs = mock_sources(monkeypatch, tmp_path, [
        (origins(["a", "b"]), histories(["a", "b"], [1., 1.])),
        (origins(["b", "c"]), histories(["b", "c"], [1., 1.])),
    ])
    output = tmp_path / "panel.parquet"
    with pytest.raises(ValueError, match="overlapping source"):
        ingest.build_panel_from_files(pairs, output)
    assert not output.exists()


def test_source_cohort_without_any_performance_rejected(monkeypatch, tmp_path):
    # The .04 cohort cannot be represented in any output row. Silently
    # dropping it would break fixed-denominator parity across source files.
    pairs = mock_sources(monkeypatch, tmp_path, [
        (origins(["a", "b"], coupons=[.03, .04]), histories(["a"], [1.])),
    ])
    output = tmp_path / "panel.parquet"
    with pytest.raises(ValueError, match="no performance history"):
        ingest.build_panel_from_files(pairs, output)
    assert not output.exists()


def test_unobserved_loan_history_cannot_be_assumed_zero(monkeypatch, tmp_path):
    pairs = mock_sources(monkeypatch, tmp_path, [
        (origins(["a", "b"]), histories(["a"], [1.])),
    ])
    with pytest.raises(ValueError, match="no performance history"):
        ingest.build_panel_from_files(pairs, tmp_path / "panel.parquet")
