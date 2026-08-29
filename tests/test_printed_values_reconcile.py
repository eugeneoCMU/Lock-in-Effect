"""
Reconciliation battery: every value below is RE-DERIVED from its committed
artifact and then required to appear in the manuscript at the precision the
manuscript prints it.

Why this exists (2026-08-18). A systematic pass re-derived 1,446 printed
numbers against the artifact each one's own footnote or run tag names. Nine
disagreed. Two were not roundings:

  * tab:estimators printed the lag-0 correlation (v4_r_lag0 = -0.378) under a
    "(-2)" label, while the artifact's peak-lag value at v4_best_lag = -2 is
    v4_peak_lag_r = -0.438.
  * the tab:ladder paragraph attributed the binding layer to the Webb wild-t
    rung, which does not even qualify under the frozen rule
    (90.84/91.42 against a 93.0/91.0 bar); binding_construction is
    "restricted_webb". Two other sites in the same manuscript already said so.

The other seven were last-digit drift (9.44/9.43, +5.05/+5.04, 1,940.9/1,940.8,
30.7/30.6 at two sites, 915.0/915.1, +3.64/+3.63), plus the two tab:danish mean
CPR cells corrected just before them (47.10/47.14, 3.40/3.36).

NONE of these was gated. Only 12 of 129 liveness gates tie a printed number to
an artifact, and every one of these cells fell outside them.

DESIGN. The expected value is never hardcoded here -- it is computed from the
artifact at import time and formatted at the printed precision. A test that
hardcoded "47.14" would pin today's text; this one fails if EITHER the
manuscript drifts OR the artifact is re-cut without the manuscript following.
Where a stale sibling is possible, the retired form is also held at zero
occurrences: the berger battery learned that asserting the new string is
present cannot detect a wrong sibling elsewhere, but asserting the old one is
absent can.

Run:  python3 -m pytest tests/test_printed_values_reconcile.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
_TEX = _ROOT / "paper" / "final" / "paper_final_v1.tex"
_VARIANT = _ROOT / "paper" / "final" / "paper_final_v1_long_abstract.tex"

CANONICAL = _TEX.read_text()
VARIANT = _VARIANT.read_text()

BOTH = pytest.mark.parametrize(
    "tex", [CANONICAL, VARIANT], ids=["canonical", "variant"]
)


def _load(rel: str):
    p = _ROOT / rel
    if not p.exists():  # un-shipped artifact (see .gitignore); skip, do not fail
        pytest.skip(f"artifact not present in this checkout: {rel}")
    return json.loads(p.read_text())


def _dig(obj, *keys):
    for k in keys:
        obj = obj[k]
    return obj


def _tex_thousands(value: float, places: int) -> str:
    """Render like the manuscript does: 1940.8033 -> '1{,}940.8'."""
    return f"{value:,.{places}f}".replace(",", "{,}")


# --------------------------------------------------------------------------
# tab:danish -- the two Danish mean-CPR cells, each against its own run
# --------------------------------------------------------------------------

@BOTH
def test_danish_mechanism_extrapolated_cell(tex):
    m = _load("abm/data/runs/run-2026-07-04-15yr-foldin/manifest.json")
    us = _dig(m, "metrics", "cpr_pct", "us_abm", "mean")
    dk = _dig(m, "metrics", "cpr_pct", "danish", "mean")
    cell = f"{us:.2f}\\% / {dk:.2f}\\%"
    assert cell in tex, f"tab:danish mechanism-extrapolated cell should read {cell}"
    assert "11.68\\% / 47.10\\%" not in tex, "the superseded 47.10% cell is back"


@BOTH
def test_danish_berger_level_cell(tex):
    m = _load("abm/data/runs/run-2026-07-05-berger/manifest.json")
    us = _dig(m, "metrics", "cpr_pct", "us_abm", "mean")
    dk = _dig(m, "metrics", "cpr_pct", "danish", "mean")
    cell = f"{us:.2f}\\% / {dk:.2f}\\%"
    assert cell in tex, f"tab:danish Berger Danish-level cell should read {cell}"
    assert "11.76\\% / 3.40\\%" not in tex, "the superseded 3.40% cell is back"


@BOTH
def test_danish_prose_range_tracks_the_table(tex):
    """V.C cites the two Danish-level legs as a range; its lower bound is the
    Berger ABM cell, so it drifts whenever that cell does. Adopted from the
    R33 branch's danish_cpr_manifest_check, which carried this check and my
    first battery did not. The 3.39 upper bound is the hybrid leg, whose value
    has no manifest in this pair (different pipeline), so it is pinned as a
    literal rather than derived."""
    berger = _load("abm/data/runs/run-2026-07-05-berger/manifest.json")
    dk = _dig(berger, "metrics", "cpr_pct", "danish", "mean")
    assert f"({dk:.2f}--3.39\\%, Table~\\ref{{tab:danish}})" in tex
    assert "(3.39--3.40\\%, Table~\\ref{tab:danish})" not in tex, (
        "the retired 3.39--3.40 range is back"
    )


@BOTH
def test_danish_row_dollar_figures_match_foldin(tex):
    m = _load("abm/data/runs/run-2026-07-04-15yr-foldin/manifest.json")
    d = _dig(m, "metrics", "dollars_b")
    for key, printed in (
        ("us_trapped", f"$+\\${d['us_trapped']:.1f}$B"),
        ("danish_trapped", f"$-\\${abs(d['danish_trapped']):.1f}$B"),
        ("institutional_gap", f"$+\\${d['institutional_gap']:.1f}$B"),
    ):
        assert printed in tex, f"tab:danish {key} should print {printed}"


# --------------------------------------------------------------------------
# The two substantive corrections
# --------------------------------------------------------------------------

@BOTH
def test_pathA_peak_lag_correlation_is_the_peak_lag_value(tex):
    """The (-2) label must carry the lag--2 correlation, not the lag-0 one."""
    a = _load("hazard/data/pathA_seasonal_adoption_results.json")
    lag, r, r0 = a["v4_best_lag"], a["v4_peak_lag_r"], a["v4_r_lag0"]
    assert f"$r = {r:.3f}$ (${lag}$)" in tex, (
        f"tab:estimators should print r = {r:.3f} at lag {lag}"
    )
    assert f"$r = {r0:.3f}$" not in tex, (
        f"the lag-0 correlation {r0:.3f} is printed as if it were the peak-lag value"
    )


@BOTH
def test_binding_layer_is_attributed_to_the_qualifying_construction(tex):
    """Webb wild-t does not qualify under the frozen rule; it cannot be binding."""
    a = _load("hazard/data/fewcluster_coverage_results.json")
    assert a["binding_construction"] == "restricted_webb", (
        "artifact no longer names the restricted inversion as binding; "
        "this battery and the manuscript both need revisiting"
    )
    assert "webb_wild_t" not in a.get("qualifying", []), (
        "Webb now qualifies; the manuscript's attribution needs revisiting"
    )
    assert (
        "quotes the Webb wild-$t$ rung of Table~\\ref{tab:ladder} as the binding layer"
        not in tex
    ), "the binding layer is attributed to a construction that fails the frozen bar"
    assert (
        "quotes the restricted wild-cluster inversion rung of "
        "Table~\\ref{tab:ladder} as the binding layer" in tex
    )


# --------------------------------------------------------------------------
# Last-digit reconciliations
# --------------------------------------------------------------------------

@BOTH
def test_episode_realized_cpr_shallowest_bucket(tex):
    a = _load("hazard/data/episode_confrontation_results.json")
    v = _dig(a, "part_a", "primary_age_matched", "buckets", "[-1,0)", "realized", "cpr_pct")
    assert f"{v:.2f}\\% annualized CPR" in tex
    assert "9.44\\%" not in tex, "retired 9.44% is back"


@BOTH
def test_lowband_offwindow_marginal(tex):
    a = _load("hazard/data/band_low_extension_results.json")
    row = _dig(a, "curves", "4.991", "curve")[7]
    assert row["p_q_shock_pct"] == 5.5, "tab:lowband row 7 is no longer the 5.5 shock"
    assert f"$+{row['marginal_pp']:.2f}$" in tex
    assert "$+5.05$" not in tex, "retired +5.05 is back"


@BOTH
def test_wal_soma_book_total(tex):
    a = _load("hazard/data/composition_shift_results.json")
    latest = _dig(a, "soma_book", "latest")
    assert latest["as_of"] == "2026-07-15"
    assert f"\\${_tex_thousands(latest['total_mbs_face_b'], 1)} billion" in tex
    assert "1{,}940.9" not in tex, "retired 1,940.9 is back"


@BOTH
def test_specv3_point_trapped(tex):
    a = _load("hazard/data/bootstrap_resimulate_results.json")
    assert f"\\${a['point_trapped_b']:.1f} billion" in tex
    # three sites print this value; presence alone cannot detect one reverting
    assert "\\$915.0 billion" not in tex, "retired 915.0 is back at some site"


@BOTH
def test_temporal_friction_basic_interval(tex):
    a = _load("hazard/data/temporal_block_bootstrap.json")
    point = _dig(a, "point_production_units", "friction")
    pct_lo, pct_hi = _dig(a, "stats", "friction", "ci_95_percentile")
    lo, hi = 2 * point - pct_hi, 2 * point - pct_lo
    assert f"$[{lo:.2f},\\,+{hi:.2f}]$" in tex
    assert "+3.64]$" not in tex, "retired +3.64 upper is back"


def test_surviving_balance_vintage_shares():
    """Derived from loan_sample.parquet, which is un-shipped for licensing."""
    p = _ROOT / "hazard" / "data" / "loan_sample.parquet"
    if not p.exists():
        pytest.skip("loan_sample.parquet is not shipped (Freddie licensing)")
    pd = pytest.importorskip("pandas")
    df = pd.read_parquet(p)
    sur = df[df.balance > 0]
    by = sur.groupby("vintage").balance.sum()
    total = by.sum()
    share_2020 = by.loc[2020] / total * 100.0
    share_2021 = by.loc[2021] / total * 100.0
    early = sum(by.loc[y] for y in (2017, 2018, 2019)) / total * 100.0
    for tex in (CANONICAL, VARIANT):
        assert (
            f"2017--19 is {early:.1f}\\%, 2020 {share_2020:.1f}\\% "
            f"and 2021 {share_2021:.1f}\\%" in tex
        )
        assert (
            f"\\emph{{surviving balance}}: 0.0; {early:.1f}; "
            f"{share_2020:.1f}; {share_2021:.1f}; 0.0" in tex
        )
        assert "2020 30.7\\%" not in tex, "retired 30.7% share is back"
        assert "30.7; 42.3" not in tex, "retired 30.7 list entry is back"
