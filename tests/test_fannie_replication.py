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
import pytest
from polars.testing import assert_frame_equal

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

# hazard/config.py resolves the FRED key at import time; a dummy value keeps
# these tests hermetic when no .env is present.
os.environ.setdefault("FRED_API_KEY", "test-dummy-key")

PANEL_KEYS = ["vintage", "coupon", "fico_bucket", "ltv_bucket", "reporting_period"]

# Corrected snapshots retain exact observation month, loan terms, and cohort key.
SNAPSHOT_COLS = [
    "loan_id", "stratum_id", "fico", "property_state", "orig_ltv",
    "coupon", "orig_upb", "balance", "loan_age", "state", "vintage",
    "fico_bucket", "ltv_bucket", "cohort_coupon", "original_loan_term", "reporting_period",
]
HISTORY_COLS = ["cohort_original_upb", "historical_prepaid_upb", "survivor_original_upb",
                "history_first_observed_payoff_count", "history_gap_payoff_count",
                "initial_burnout", "burnout_denominator_multiplier"]
SAMPLE_COLS = SNAPSHOT_COLS + HISTORY_COLS + ["weight"]


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
        # Random seeds do not guarantee disjoint loan IDs. Source-quarter
        # prefixes do, while keeping the same vintage and cohort support.
        for path in (tagged_orig, tagged_perf):
            path.write_text(path.read_text().replace("F20Q1", f"F20Q{i + 1}"))
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


def _corrected_cells(periods, *, original=100., age_sum=30., age_count=1, loan_count=3):
    n = len(periods)
    return pl.DataFrame({
        "vintage": [2020] * n, "coupon": [3.5] * n,
        "fico_bucket": ["680-739"] * n, "ltv_bucket": ["80-90"] * n,
        "reporting_period": periods, "exposure_upb": [50.] * n,
        "orig_upb_sum": [50.] * n, "prepaid_upb": [0.] * n,
        "mean_loan_age": [age_sum / age_count if age_count else float("nan")] * n,
        "finite_age_sum": [age_sum] * n, "finite_age_count": [age_count] * n,
        "mode_state": ["Current"] * n, "loan_count": [loan_count] * n,
        "cohort_original_upb": [original] * n,
        "monthly_prepay_rate": [0.] * n, "period": periods, "burnout": [0.] * n,
    })


def test_combine_fixed_balance_survives_source_cohort_exit(tmp_path):
    from fannie_replication import combine_quarter_cells

    first = _corrected_cells(["202001"], original=100.).with_columns(pl.lit(100.).alias("prepaid_upb"))
    second = _corrected_cells(["202001", "202002"], original=200.)
    paths = [tmp_path / "first.parquet", tmp_path / "second.parquet"]
    for frame, path in zip([first, second], paths):
        frame.write_parquet(path)
    result = combine_quarter_cells(paths, tmp_path / "combined.parquet")
    assert result["cohort_original_upb"].to_list() == [300., 300.]
    assert result["burnout"].to_list() == pytest.approx([1 / 3, 1 / 3])


def test_combine_uses_finite_age_counts_not_all_loan_counts(tmp_path):
    from fannie_replication import combine_quarter_cells

    frames = [_corrected_cells(["202001"], age_sum=10., age_count=1, loan_count=5),
              _corrected_cells(["202001"], age_sum=90., age_count=3, loan_count=3)]
    paths = [tmp_path / f"part_{i}.parquet" for i in range(2)]
    for frame, path in zip(frames, paths):
        frame.write_parquet(path)
    result = combine_quarter_cells(paths, tmp_path / "combined.parquet")
    assert result["mean_loan_age"].item() == pytest.approx(25.)
    assert result["finite_age_count"].item() == 4
    assert result["loan_count"].item() == 8


@pytest.mark.parametrize("balances", [[100., 110.], [0., 0.], [-1., -1.], [float("nan"), float("nan")], [float("inf"), float("inf")], [None, None]])
def test_combine_rejects_invalid_fixed_cohort_balances(tmp_path, balances):
    from fannie_replication import combine_quarter_cells

    frame = _corrected_cells(["202001", "202002"]).with_columns(
        pl.Series("cohort_original_upb", balances, dtype=pl.Float64)
    )
    path = tmp_path / "cells.parquet"
    frame.write_parquet(path)
    with pytest.raises(ValueError, match="finite positive fixed"):
        combine_quarter_cells([path], tmp_path / "output.parquet")
    assert not (tmp_path / "output.parquet").exists()


def test_combine_legacy_requires_explicit_replay_and_rejects_mixed_inputs(tmp_path):
    from fannie_replication import combine_quarter_cells

    corrected = _corrected_cells(["202001"])
    legacy = corrected.drop("cohort_original_upb", "finite_age_sum", "finite_age_count")
    old_path, new_path = tmp_path / "old.parquet", tmp_path / "new.parquet"
    legacy.write_parquet(old_path)
    corrected.write_parquet(new_path)
    with pytest.raises(ValueError, match="lack fixed cohort"):
        combine_quarter_cells([old_path], tmp_path / "output.parquet")
    with pytest.warns(UserWarning, match="Historical quarter-cell replay"):
        replay = combine_quarter_cells([old_path], tmp_path / "output.parquet", allow_legacy_cells=True)
    assert "cohort_original_upb" not in replay.columns
    with pytest.raises(ValueError, match="Mixed or incomplete"):
        combine_quarter_cells([old_path, new_path], tmp_path / "mixed.parquet", allow_legacy_cells=True)


def test_combine_rejects_inconsistent_finite_age_statistics(tmp_path):
    from fannie_replication import combine_quarter_cells

    path = tmp_path / "cells.parquet"
    _corrected_cells(["202001"], age_count=4, loan_count=3).write_parquet(path)
    with pytest.raises(ValueError, match="finite-age sufficient"):
        combine_quarter_cells([path], tmp_path / "output.parquet")


def test_write_pool_piece_schema_and_size(tmp_path):
    from loan_sample_fannie import write_pool_piece, _piece_sidecar_paths

    (orig, perf), _ = _two_synthetic_pairs(tmp_path)
    out = tmp_path / "pool_piece.parquet"
    n = write_pool_piece(
        orig, perf, per_file=200, seed=42, output=out, vintage_years=[2020]
    )
    piece = pl.read_parquet(out)
    assert n == len(piece) == 200
    # Full-cohort history is attached only after all source pieces are present.
    assert piece.columns == SNAPSHOT_COLS
    assert piece["vintage"].unique().to_list() == [2020]
    assert piece["original_loan_term"].unique().to_list() == [360.]
    assert piece["reporting_period"].unique().to_list() == ["202205"]
    history_path, ids_path = _piece_sidecar_paths(out)
    assert pl.read_parquet(history_path).height > 0
    assert pl.read_parquet(ids_path).height >= piece.height

    # Out-of-window filter still writes a (zero-row) completion marker.
    out_empty = tmp_path / "pool_piece_empty.parquet"
    n_empty = write_pool_piece(
        orig, perf, per_file=200, seed=42, output=out_empty, vintage_years=[1999]
    )
    assert n_empty == 0
    assert out_empty.exists()
    assert len(pl.read_parquet(out_empty)) == 0
    history_path, ids_path = _piece_sidecar_paths(out_empty)
    assert pl.read_parquet(history_path).height == 0
    assert pl.read_parquet(ids_path).height == 0


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


def _snapshot_and_history(loan_id, original, prepaid, survivor_original):
    snapshot = pl.DataFrame({
        "loan_id": [loan_id], "stratum_id": ["2020_300_high_low"],
        "fico": [720], "property_state": ["PA"], "orig_ltv": [80.],
        "coupon": [.03], "orig_upb": [survivor_original], "balance": [survivor_original * .9],
        "loan_age": [28.], "state": ["Current"], "vintage": [2020],
        "fico_bucket": ["high"], "ltv_bucket": ["low"], "cohort_coupon": [.03],
        "original_loan_term": [360.], "reporting_period": ["202205"],
    })
    history = pl.DataFrame({
        "vintage": [2020], "cohort_coupon": [.03], "fico_bucket": ["high"],
        "ltv_bucket": ["low"], "cohort_original_upb": [original],
        "historical_prepaid_upb": [prepaid], "survivor_original_upb": [survivor_original],
        "history_first_observed_payoff_count": [0], "history_gap_payoff_count": [0],
    })
    if survivor_original == 0:
        snapshot = snapshot.head(0)
    return snapshot, history, [loan_id]


def test_fannie_history_includes_quarter_without_survivors(tmp_path, monkeypatch):
    import loan_sample_fannie as fannie
    sources = {"q1": _snapshot_and_history("F20Q1A", 100., 100., 0.),
               "q2": _snapshot_and_history("F20Q2B", 300., 30., 200.)}
    terms = []

    def inputs(orig, perf, *, term_months):
        terms.append(term_months)
        return sources[orig.name]

    monkeypatch.setattr(fannie, "_snapshot_inputs_one_pair", inputs)
    paths = [tmp_path / "pool_q1.parquet", tmp_path / "pool_q2.parquet"]
    for name, path in zip(sources, paths):
        fannie.write_pool_piece(Path(name), Path("perf"), 10, 42, path, vintage_years=[2020])
    sample = fannie.finalize_fannie_sample(paths, n_loans=1, output=tmp_path / "sample.parquet")
    assert terms == [360, 360]
    assert sample["cohort_original_upb"].item() == 400.
    assert sample["historical_prepaid_upb"].item() == 130.
    assert sample["initial_burnout"].item() == pytest.approx(130 / 400)
    assert sample["burnout_denominator_multiplier"].item() == 2.


def test_fannie_source_overlap_detected_outside_sampled_survivors(tmp_path, monkeypatch):
    import loan_sample_fannie as fannie
    sources = {"q1": _snapshot_and_history("F20Q1A", 200., 100., 100.),
               "q2": _snapshot_and_history("F20Q2B", 200., 100., 100.)}
    sources = {name: (snap, history, ids + ["F20Q1TERMINATED"])
               for name, (snap, history, ids) in sources.items()}
    monkeypatch.setattr(fannie, "_snapshot_inputs_one_pair",
                        lambda orig, perf, **kw: sources[orig.name])
    paths = [tmp_path / "pool_q1.parquet", tmp_path / "pool_q2.parquet"]
    for name, path in zip(sources, paths):
        fannie.write_pool_piece(Path(name), Path("perf"), 10, 42, path)
    with pytest.raises(ValueError, match="Overlapping origination"):
        fannie.finalize_fannie_sample(paths, n_loans=1, output=tmp_path / "sample.parquet")
    assert not (tmp_path / "sample.parquet").exists()


def test_fannie_legacy_pieces_require_explicit_replay(tmp_path):
    from loan_sample_fannie import finalize_fannie_sample
    snapshot, _, _ = _snapshot_and_history("F20Q1A", 100., 0., 100.)
    path = tmp_path / "legacy.parquet"
    snapshot.write_parquet(path)
    with pytest.raises(ValueError, match="lack.*history"):
        finalize_fannie_sample([path], n_loans=1, output=tmp_path / "new.parquet")
    with pytest.warns(UserWarning, match="Historical Fannie"):
        replay = finalize_fannie_sample([path], n_loans=1, output=tmp_path / "replay.parquet",
                                        allow_legacy_inputs=True)
    assert "initial_burnout" not in replay.columns


def test_fannie_partial_sidecars_rejected_even_with_legacy_opt_in(tmp_path, monkeypatch):
    import loan_sample_fannie as fannie
    inputs = _snapshot_and_history("F20Q1A", 100., 0., 100.)
    monkeypatch.setattr(fannie, "_snapshot_inputs_one_pair", lambda *a, **kw: inputs)
    path = tmp_path / "piece.parquet"
    fannie.write_pool_piece(Path("orig"), Path("perf"), 10, 42, path)
    _, ids_path = fannie._piece_sidecar_paths(path)
    ids_path.unlink()
    with pytest.raises(ValueError, match="Mixed or incomplete"):
        fannie.finalize_fannie_sample([path], n_loans=1, output=tmp_path / "sample.parquet",
                                      allow_legacy_inputs=True)


@pytest.mark.parametrize('corruption', ['missing', 'duplicated', 'negative', 'nonfinite'])
def test_fannie_invalid_history_cannot_be_written_as_corrected_sample(tmp_path, monkeypatch, corruption):
    import loan_sample_fannie as fannie
    inputs = _snapshot_and_history('F20Q1A', 100., 0., 100.)
    monkeypatch.setattr(fannie, '_snapshot_inputs_one_pair', lambda *a, **kw: inputs)
    path = tmp_path / 'piece.parquet'
    fannie.write_pool_piece(Path('orig'), Path('perf'), 10, 42, path)
    history_path, _ = fannie._piece_sidecar_paths(path)
    history = pl.read_parquet(history_path)
    if corruption == 'missing':
        history = history.head(0)
    elif corruption == 'duplicated':
        history = pl.concat([history, history])
    else:
        history = history.with_columns(pl.lit(-1. if corruption == 'negative' else float('nan')).alias('historical_prepaid_upb'))
    history.write_parquet(history_path)
    with pytest.raises(ValueError, match='[Hh]istory|cohort'):
        fannie.finalize_fannie_sample([path], n_loans=1, output=tmp_path / 'sample.parquet')
    assert not (tmp_path / 'sample.parquet').exists()


def test_fannie_other_source_cannot_mask_missing_history(tmp_path, monkeypatch):
    import loan_sample_fannie as fannie
    sources = {'q1': _snapshot_and_history('F20Q1A', 100., 0., 100.),
               'q2': _snapshot_and_history('F20Q2B', 100., 0., 100.)}
    monkeypatch.setattr(fannie, '_snapshot_inputs_one_pair', lambda orig, perf, **kw: sources[orig.name])
    paths = [tmp_path/'q1.parquet', tmp_path/'q2.parquet']
    for name, path in zip(sources, paths):
        fannie.write_pool_piece(Path(name), Path('perf'), 10, 42, path)
    history, _ = fannie._piece_sidecar_paths(paths[0])
    pl.read_parquet(history).head(0).write_parquet(history)
    with pytest.raises(ValueError, match='Missing history'):
        fannie.finalize_fannie_sample(paths, n_loans=1, output=tmp_path/'sample.parquet')


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
