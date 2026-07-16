"""
Gates for the Fannie W4 replication layer (hazard/fannie_replication.py +
hazard/loan_sample_fannie.py).

1. The quarter-at-a-time panel path must be EXACTLY the one-shot ingest.py
   build: per-quarter build_panel_from_files cells, recombined by
   combine_quarter_cells, must reproduce build_panel_from_files over the same
   pairs in one call. This is what licenses the disk-constrained
   download→stage→aggregate→delete loop as "the estimator's panel, unchanged".
2. The vintage filter (Fannie acquisition files carry a seasoned origination
   tail; Freddie files are vintage-sliced at the source) must drop exactly
   out-of-window cohorts and nothing else.
3. Path B pool pieces (per-quarter oversample of pre-QT loan snapshots, drawn
   while the staged pair still exists) must land the loan_sample.parquet
   schema, and finalize_fannie_sample must produce exactly n_loans rows.
4. The pre-committed envelope gate (marginal positive AND inside the Freddie
   floor/band box) must be pure arithmetic — testable without any data.

Run with: python3 -m pytest tests/test_fannie_replication.py
"""

import os
import sys
from pathlib import Path

import polars as pl
from polars.testing import assert_frame_equal

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

# hazard/config.py resolves the FRED key at import time; a dummy value keeps
# these tests hermetic when no .env is present.
os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

PANEL_KEYS = ["vintage", "coupon", "fico_bucket", "ltv_bucket", "reporting_period"]

# Column order of the committed production loan_sample.parquet.
SAMPLE_COLS = [
    "loan_id", "stratum_id", "fico", "property_state", "orig_ltv",
    "coupon", "orig_upb", "balance", "loan_age", "state", "vintage",
    "fico_bucket", "ltv_bucket", "weight",
]


def _two_synthetic_pairs(tmp_path):
    """Two distinct Freddie-shaped pairs with overlapping cohort cells."""
    from ingest import generate_synthetic_fixture

    pairs = []
    for i, seed in enumerate((11, 22)):
        d = tmp_path / f"fix{i}"
        orig, perf = generate_synthetic_fixture(
            n_loans=400, n_months=36, output_dir=d, seed=seed
        )
        tagged_orig = d / f"orig_T{i}.txt"
        tagged_perf = d / f"perf_T{i}.txt"
        orig.rename(tagged_orig)
        perf.rename(tagged_perf)
        pairs.append((tagged_orig, tagged_perf))
    return pairs


def test_combine_quarter_cells_matches_one_shot_build(tmp_path):
    from ingest import build_panel_from_files
    from fannie_replication import combine_quarter_cells

    pairs = _two_synthetic_pairs(tmp_path)

    one_shot = build_panel_from_files(pairs, output=tmp_path / "one_shot.parquet")

    cell_paths = []
    for i, pair in enumerate(pairs):
        out = tmp_path / f"cells_{i}.parquet"
        build_panel_from_files([pair], output=out)
        cell_paths.append(out)
    combined = combine_quarter_cells(
        cell_paths, output=tmp_path / "combined.parquet", vintage_years=None
    )

    assert combined.columns == one_shot.columns
    # mode_state is excluded from strict equality: ingest.py's mode().first()
    # breaks modal TIES in nondeterministic order, so the two builds can
    # legitimately disagree on tied cells (each path recomputes the per-pair
    # aggregates here). Tie semantics are covered by the gate tests below;
    # every estimator-consumed column must match exactly.
    non_mode = [c for c in one_shot.columns if c != "mode_state"]
    assert_frame_equal(
        combined.sort(PANEL_KEYS).select(non_mode),
        one_shot.sort(PANEL_KEYS).select(non_mode),
    )


def test_combine_quarter_cells_vintage_filter(tmp_path):
    from ingest import build_panel_from_files
    from fannie_replication import combine_quarter_cells

    pairs = _two_synthetic_pairs(tmp_path)
    cell_paths = []
    for i, pair in enumerate(pairs):
        out = tmp_path / f"cells_{i}.parquet"
        build_panel_from_files([pair], output=out)
        cell_paths.append(out)

    # The fixture is all vintage-2020: an in-window filter is a no-op ...
    kept = combine_quarter_cells(
        cell_paths, output=tmp_path / "kept.parquet", vintage_years=[2020]
    )
    unfiltered = combine_quarter_cells(
        cell_paths, output=tmp_path / "unfiltered.parquet", vintage_years=None
    )
    assert_frame_equal(kept.sort(PANEL_KEYS), unfiltered.sort(PANEL_KEYS))

    # ... and an out-of-window filter drops every cohort.
    dropped = combine_quarter_cells(
        cell_paths, output=tmp_path / "dropped.parquet", vintage_years=[2019]
    )
    assert len(dropped) == 0


def test_write_pool_piece_schema_and_size(tmp_path):
    from loan_sample_fannie import write_pool_piece

    (orig, perf), _ = _two_synthetic_pairs(tmp_path)
    out = tmp_path / "pool_piece.parquet"
    n = write_pool_piece(
        orig, perf, per_file=200, seed=42, output=out, vintage_years=[2020]
    )
    piece = pl.read_parquet(out)
    assert n == len(piece) == 200
    # Snapshot schema = loan_sample columns minus the weight added at finalize.
    assert piece.columns == SAMPLE_COLS[:-1]
    assert piece["vintage"].unique().to_list() == [2020]

    # Out-of-window filter still writes a (zero-row) completion marker.
    out_empty = tmp_path / "pool_piece_empty.parquet"
    n_empty = write_pool_piece(
        orig, perf, per_file=200, seed=42, output=out_empty, vintage_years=[1999]
    )
    assert n_empty == 0
    assert out_empty.exists()
    assert len(pl.read_parquet(out_empty)) == 0


def test_finalize_fannie_sample_exact_n(tmp_path):
    from loan_sample_fannie import finalize_fannie_sample, write_pool_piece

    pairs = _two_synthetic_pairs(tmp_path)
    piece_paths = []
    for i, (orig, perf) in enumerate(pairs):
        out = tmp_path / f"pool_{i}.parquet"
        write_pool_piece(
            orig, perf, per_file=300, seed=42 + i, output=out, vintage_years=[2020]
        )
        piece_paths.append(out)

    sample = finalize_fannie_sample(
        piece_paths, n_loans=500, seed=42, output=tmp_path / "sample.parquet"
    )
    assert len(sample) == 500
    assert sample.columns == SAMPLE_COLS
    assert sample["weight"].unique().to_list() == [1.0]
    # Written artifact round-trips.
    assert_frame_equal(pl.read_parquet(tmp_path / "sample.parquet"), sample)


def _pad(row, n=32):
    row = list(row) + [""] * (n - len(row))
    return "|".join(row[:n])


def _tie_pair(tmp_path, n_current=1):
    """Staged pair with one cohort cell holding 1 Prepaid + n_current Current
    loans in the same month: a modal tie iff n_current == 1."""
    orig_rows, perf_rows = [], []
    for i in range(1 + n_current):
        seq = f"F20Q1TIE{i:04d}"
        o = [""] * 32
        o[0], o[1], o[10], o[11], o[12] = "700", "202006", "100000.00", "80", "3.500"
        o[15], o[16], o[19], o[21] = "FRM", "CA", seq, "360"
        orig_rows.append(_pad(o))
        p = [""] * 32
        p[0], p[1], p[4] = seq, "202006", "1"
        if i == 0:
            p[2], p[3], p[8] = "0.00", "0", "01"      # Prepaid (ZBC 01)
        else:
            p[2], p[3], p[8] = "100000.00", "0", ""   # Current
        perf_rows.append(_pad(p))
    orig = tmp_path / "orig_TIE.txt"
    perf = tmp_path / "perf_TIE.txt"
    orig.write_text("\n".join(orig_rows))
    perf.write_text("\n".join(perf_rows))
    return orig, perf


def _flip_mode(cells: pl.DataFrame, to_value: str) -> pl.DataFrame:
    return cells.with_columns(pl.lit(to_value).alias("mode_state"))


def test_gate_accepts_tied_mode_state_divergence(tmp_path):
    from ingest import build_panel_from_files
    from fannie_replication import gate_2019q1_cells

    pair = _tie_pair(tmp_path, n_current=1)  # Prepaid vs Current: exact tie
    cells_path = tmp_path / "cells.parquet"
    cells = build_panel_from_files([pair], output=cells_path)
    other = "Current" if cells["mode_state"][0] == "Prepaid" else "Prepaid"
    probe_path = tmp_path / "probe.parquet"
    _flip_mode(cells, other).write_parquet(probe_path)

    gate = gate_2019q1_cells(cells_path, probe_path, staged_pair=pair)
    assert gate["pass"]
    assert gate["mode_state_diffs"] == 1
    assert gate["mode_diffs_all_ties"]


def test_gate_rejects_non_tie_mode_state_divergence(tmp_path):
    from ingest import build_panel_from_files
    from fannie_replication import gate_2019q1_cells

    pair = _tie_pair(tmp_path, n_current=2)  # Current wins 2-1: no tie
    cells_path = tmp_path / "cells.parquet"
    cells = build_panel_from_files([pair], output=cells_path)
    assert cells["mode_state"][0] == "Current"
    probe_path = tmp_path / "probe.parquet"
    _flip_mode(cells, "Prepaid").write_parquet(probe_path)

    gate = gate_2019q1_cells(cells_path, probe_path, staged_pair=pair)
    assert not gate["pass"]
    assert not gate["mode_diffs_all_ties"]


def test_gate_rejects_deterministic_column_divergence(tmp_path):
    from ingest import build_panel_from_files
    from fannie_replication import gate_2019q1_cells

    pair = _tie_pair(tmp_path, n_current=1)
    cells_path = tmp_path / "cells.parquet"
    cells = build_panel_from_files([pair], output=cells_path)
    probe_path = tmp_path / "probe.parquet"
    cells.with_columns(
        (pl.col("exposure_upb") + 1.0).alias("exposure_upb")
    ).write_parquet(probe_path)

    gate = gate_2019q1_cells(cells_path, probe_path, staged_pair=pair)
    assert not gate["pass"]


def test_envelope_gate_logic():
    from fannie_replication import evaluate_envelope_gate

    inside = evaluate_envelope_gate(5.0, box_min=2.11, box_max=13.17)
    assert inside["positive"] and inside["in_envelope"] and inside["pass"]

    below_box = evaluate_envelope_gate(1.0, box_min=2.11, box_max=13.17)
    assert below_box["positive"] and not below_box["in_envelope"]
    assert not below_box["pass"]

    negative = evaluate_envelope_gate(-3.0, box_min=2.11, box_max=13.17)
    assert not negative["positive"] and not negative["pass"]

    above_box = evaluate_envelope_gate(14.0, box_min=2.11, box_max=13.17)
    assert above_box["positive"] and not above_box["in_envelope"]
    assert not above_box["pass"]
