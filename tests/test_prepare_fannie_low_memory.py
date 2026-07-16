"""
Gate for the low-memory Fannie staging path (hazard/prepare_fannie.py).

The 2020Q2 acquisition file is ~17 GB native (COVID refi wave) — the eager
stage_native_file collect() is a deterministic OOM kill on a 16 GiB machine.
The low-memory path must produce the SAME staged pair via streaming sinks
plus an on-disk sort:

1. perf_<TAG>.txt byte-identical to the eager path's output (the sort key
   (loan_sequence_number, reporting_period) is unique per row, so the order
   is total and engine-independent);
2. orig_<TAG>.txt equal as a frame up to row order (streaming unique does
   not preserve first-occurrence file order; downstream joins are key-based,
   and the low-memory orig is sorted by loan_sequence_number so it is
   deterministic run-to-run).

Run with: python3 -m pytest tests/test_prepare_fannie_low_memory.py
"""

import os
import sys
from pathlib import Path

import polars as pl
from polars.testing import assert_frame_equal

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

os.environ.setdefault("FRED_API_KEY", "test-dummy-key")


def _synthetic_native(path: Path, n_loans: int = 40, months: int = 5) -> None:
    """Small native-format SF LPH file: 113 pipe-delimited headerless cols."""
    from schema_fannie import FANNIE_COLS_WIRE

    idx = {name: i for i, name in enumerate(FANNIE_COLS_WIRE)}
    lines = []
    for j in range(n_loans):
        loan_id = f"9{j:011d}"
        for m in range(months):
            row = [""] * len(FANNIE_COLS_WIRE)
            row[idx["loan_identifier"]] = loan_id
            row[idx["reporting_period"]] = f"{(m % 12) + 1:02d}2020"
            row[idx["origination_date"]] = "112019"
            row[idx["first_payment_date"]] = "012020"
            row[idx["original_upb"]] = "250000.00"
            row[idx["current_upb"]] = f"{250000 - 500 * m:.2f}"
            row[idx["original_ltv"]] = "80"
            row[idx["original_interest_rate"]] = "3.750"
            row[idx["original_loan_term"]] = "360"
            row[idx["credit_score"]] = str(680 + (j % 3) * 40)
            row[idx["amortization_type"]] = "FRM"
            row[idx["property_state"]] = "OH"
            row[idx["loan_age"]] = str(m + 1)
            row[idx["delinquency_status"]] = "00"
            row[idx["zero_balance_code"]] = (
                "01" if (j % 7 == 0 and m == months - 1) else ""
            )
            lines.append("|".join(row))
    path.write_text("\n".join(lines))


def test_low_memory_staging_matches_eager(tmp_path):
    from prepare_fannie import stage_native_file

    native = tmp_path / "lph_FNMATEST.txt"
    _synthetic_native(native)

    eager_orig, eager_perf = stage_native_file(
        native, "EAGER", dest_dir=tmp_path / "eager"
    )
    lm_orig, lm_perf = stage_native_file(
        native, "LM", dest_dir=tmp_path / "lm", low_memory=True
    )

    # perf: byte-identical (unique total sort key -> engine-independent order)
    assert lm_perf.read_bytes() == eager_perf.read_bytes()

    # orig: identical as a frame, up to row order
    scan = dict(separator="|", has_header=False, infer_schema_length=0,
                missing_utf8_is_empty_string=True)
    e = pl.read_csv(eager_orig, **scan).sort("column_20")
    l = pl.read_csv(lm_orig, **scan).sort("column_20")
    assert_frame_equal(e, l)


def test_low_memory_can_delete_native_after_scan(tmp_path):
    from prepare_fannie import stage_native_file

    native = tmp_path / "lph_FNMATEST2.txt"
    _synthetic_native(native)
    orig, perf = stage_native_file(
        native, "LM2", dest_dir=tmp_path / "lm2",
        low_memory=True, delete_native_after_scan=True,
    )
    assert not native.exists()  # freed before the on-disk sort
    assert orig.exists() and perf.exists()
    assert len(pl.read_csv(perf, separator="|", has_header=False,
                           infer_schema_length=0)) == 40 * 5
