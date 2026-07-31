"""Battery for gate #122 (R32 C-127: the benchmark's monthly series rebuilt).

This landing is BRANCH D, not Branch A, and almost everything here defends
that distinction.

THE EXCEPTION MAY NOT BE ROUNDED AWAY. E3 predicted all four clip months
would carry a stale published week. 2022-06 carries none. "Three of the four
... and June 2022 does not" is therefore the claim, and three tests attack it:
the overclaiming spellings must turn the gate red, the artifact's own E3 flag
must stay False, and giving 2022-06 a stale week must fail even though that
would make the manuscript's own sentence MORE conservative than the data.

STALENESS MAY NOT BE PROMOTED TO A MECHANISM. 59 of 192 published weeks and
36 of 44 months carry a stale week, so republication is ordinary and cannot
identify a clip month. Both counts are derived from the artifact's own map,
and drifting either breaks the printed literal.

THE ZEROS ARE NOT THIS RUN'S TO CLASSIFY. The four clip months and the
ARTIFACT verdict belong to h1_zero_months_diagnosis; the cap-relative
benchmark belongs to expectation_benchmark. The rebuilt net series must equal
the NEGATION of h1's month-end diff, month by month, and each tie has a
mutation test.

GROSS IS NOT NET. Gross face declines run $2,186bn against a $652.8bn net,
~3.35x, because face also falls on reinvestment settlement and roll. The
runner's second defect was summing gross against a net comparator; the
printed reconciliation is meaningless if that returns.

Every mutation is verified non-vacuous before it is applied.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    BMR_OVERCLAIM,
    BMR_SPANS,
    benchmark_monthly_rebuild_check,
)

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
GATES_SRC = (ROOT / "tools" / "liveness_gates.py").read_text()
BMR = json.loads((ROOT / "hazard" / "data"
                  / "benchmark_monthly_rebuild_results.json").read_text())
H1Z = json.loads((ROOT / "hazard" / "data"
                  / "h1_zero_months_diagnosis.json").read_text())
XB = json.loads((ROOT / "hazard" / "data"
                 / "expectation_benchmark_results.json").read_text())

# The literals the gate BUILDS from the artifact.
DERIVED = {
    "gross_vs_net": "gross face declines run \\$2{,}186 billion against a "
                    "\\$652.8 billion net",
    "weeks": "netted over 192 weekly as-of dates",
    "reconciles": "reproduces the committed month-end differencing, "
                  "\\$652.7517 billion against \\$652.7517 billion",
    "low_months": "returns the same four low months at $-\\$2.0$, \\$4.5, "
                  "\\$3.7 and \\$3.6 billion against a \\$16.8 billion window "
                  "median",
    "stale_counts": "59 of those 192 weeks and 36 of the 44 months they span "
                    "carry one",
}

CLIP = ["2022-06", "2023-02", "2024-04", "2025-09"]


def check(tex, bmr=None, h1z=None, xb=None):
    return benchmark_monthly_rebuild_check(
        tex, bmr or BMR, h1z or H1Z, xb or XB)


def test_gate_passes_on_the_manuscript():
    ok, info = check(TEX)
    assert ok, f"gate #122 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = check(VARIANT)
    assert ok, f"gate #122 fails on the long-abstract variant: {info}"


def test_the_gate_is_wired_into_the_suite():
    assert "BMR_RESULTS = " in GATES_SRC
    assert "H1Z_RESULTS = " in GATES_SRC
    assert ("benchmark_monthly_rebuild_check(tex, _bmr, _h1z, _xb122)"
            in GATES_SRC)
    assert "#122" in GATES_SRC


# --- (a) BRANCH D: the exception may not be rounded away ------------------
@pytest.mark.parametrize("lit", BMR_OVERCLAIM)
def test_the_overclaiming_spellings_are_absent_and_turn_the_gate_red(lit):
    """2022-06 carries NO stale week. Any prose asserting all four do is
    false. Trace: the conjunct is a bare absence test, so re-inserting the
    phrase anywhere turns the gate red through `overclaimed`, independently
    of every span still being present."""
    assert lit not in TEX and lit not in VARIANT
    ok, info = check(TEX + f"\n\nA stray restatement: {lit} are stale.\n")
    assert not ok
    assert lit in info["overclaimed"]
    assert info["missing"] == [], "this must be caught by absence, not presence"


def test_the_artifact_e3_flag_must_stay_false():
    """The manuscript names an exception BECAUSE E3 missed. Trace: an artifact
    claiming E3 passed contradicts the sentence on the page, so the gate must
    refuse it even though every printed literal is unchanged."""
    bmr = copy.deepcopy(BMR)
    bmr["expectations"]["E3_all_clip_months_have_a_stale_week"] = True
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]
    assert info["missing"] == []


def test_giving_the_june_2022_clip_a_stale_week_fails():
    """The tightest version of the same defence. Trace: if 2022-06 acquired a
    stale week the count would be four, not three, and the manuscript's
    "June 2022 does not" would be false -- so the gate must fail even though
    this mutation makes the DATA look tidier than the prose."""
    assert not BMR["expectations"]["E3_stale_weeks_in_clip_months"]["2022-06"]
    bmr = copy.deepcopy(BMR)
    bmr["expectations"]["E3_stale_weeks_in_clip_months"]["2022-06"] = [
        "2022-06-08"]
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]


def test_exactly_three_of_the_four_clip_months_carry_a_stale_week():
    e3 = BMR["expectations"]["E3_stale_weeks_in_clip_months"]
    assert sorted(e3) == CLIP
    assert sum(1 for m in CLIP if e3[m]) == 3
    assert e3["2022-06"] == []


# --- (b) staleness is ordinary, not diagnostic ---------------------------
def test_republication_is_the_norm_across_the_fetched_span():
    """The counts that stop staleness reading as a clip-month property."""
    stale = BMR["stale_weeks_by_month"]
    assert sum(len(v) for v in stale.values()) == 59
    assert len(stale) == 36
    assert BMR["parity"]["P4_weeks_retrieved"] == 192
    assert len(BMR["monthly_net_rolloff_b"]) == 44


@pytest.mark.parametrize("month", ["2023-03", "2024-06", "2025-05"])
def test_dropping_stale_weeks_breaks_the_printed_counts(month):
    """Trace: the two counts are derived from the artifact's own map, so
    removing entries moves the printed literal and `stale_counts` misses."""
    bmr = copy.deepcopy(BMR)
    assert bmr["stale_weeks_by_month"].get(month), f"vacuous: {month} not stale"
    del bmr["stale_weeks_by_month"][month]
    ok, info = check(TEX, bmr=bmr)
    assert not ok and "stale_counts" in info["missing"]


def test_a_stale_week_not_in_the_fetched_weeks_fails():
    """The map must reference weeks the run actually retrieved. Trace: an
    invented as-of date breaks counts_ok without moving any printed literal."""
    bmr = copy.deepcopy(BMR)
    bmr["stale_weeks_by_month"]["2023-03"] = ["1999-01-06"]
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["counts_ok"]


# --- (c) the zeros belong to h1_zero_months_diagnosis --------------------
def test_the_rebuilt_series_is_the_negation_of_the_committed_month_end_diff():
    """The tie, re-derived here. h1 stores the month-end level diff; the
    rebuild stores net roll-off, which is its negation."""
    rows = H1Z["parity_gates"]["P1_zeros_reproduce"]["rows"]
    assert sorted(rows) == CLIP
    for m in CLIP:
        assert abs(BMR["monthly_net_rolloff_b"][m]
                   + rows[m]["raw_me_diff_b"]) < 1e-6, m
        assert rows[m]["clip_binds"] is True


@pytest.mark.parametrize("month", CLIP)
def test_moving_any_clip_month_breaks_the_h1_tie(month):
    h1z = copy.deepcopy(H1Z)
    h1z["parity_gates"]["P1_zeros_reproduce"]["rows"][month][
        "raw_me_diff_b"] += 1.0
    ok, info = check(TEX, h1z=h1z)
    assert not ok and not info["cross_artifact_tie"]


def test_a_retracted_artifact_verdict_fails():
    """This disclosure STRENGTHENS h1's ARTIFACT classification by ruling out
    the alternative. Trace: if that classification were withdrawn the
    disclosure would be arguing for a verdict the repo no longer holds."""
    h1z = copy.deepcopy(H1Z)
    h1z["verdict"]["outcome"] = "BEHAVIORAL"
    ok, info = check(TEX, h1z=h1z)
    assert not ok and not info["cross_artifact_tie"]

    h1z2 = copy.deepcopy(H1Z)
    h1z2["classification_summary"]["spike_followed_all_artifact"] = False
    ok2, info2 = check(TEX, h1z=h1z2)
    assert not ok2 and not info2["cross_artifact_tie"]


def test_the_committed_benchmark_is_the_expectation_runs():
    assert (BMR["parity"]["P1_committed_benchmark_b"]
            == XB["cap_benchmark_b"] == 764.7482532227002)
    xb = copy.deepcopy(XB)
    xb["cap_benchmark_b"] = 700.0
    ok, info = check(TEX, xb=xb)
    assert not ok and not info["cross_artifact_tie"]


# --- (d) gross is not net -------------------------------------------------
def test_gross_face_declines_run_about_three_and_a_third_times_net():
    """The runner's second defect was summing gross against a net comparator.
    $2,186bn / $652.75bn = 3.35x; the printed reconciliation is meaningless
    if that returns."""
    e = BMR["expectations"]
    ratio = e["gross_declines_b"] / e["E4_implied_realized_total_b"]
    assert 3.3 < ratio < 3.4
    assert "reinvestment settlement" in e["gross_note"]


def test_a_gross_that_is_not_gross_fails():
    bmr = copy.deepcopy(BMR)
    bmr["expectations"]["gross_declines_b"] = 700.0
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]


# --- E4 / E5 --------------------------------------------------------------
def test_the_settling_test_reconciles_far_inside_its_own_tolerance():
    """E4's 1% bar was fixed in the spec before the run. It came in at 7e-11
    bn, which is why the benchmark is not in play."""
    e = BMR["expectations"]
    diff = abs(e["E4_reconstructed_window_total_b"]
               - e["E4_implied_realized_total_b"])
    assert diff == e["E4_abs_diff_b"]
    assert diff < e["E4_tol_frac"] * e["E4_implied_realized_total_b"]
    assert diff < 1e-9
    assert e["E4_pass"] is True and e["E4_month_end_reproduces_exactly"] is True


def test_a_reconstruction_outside_the_tolerance_fails():
    """Branch B: outside 1% the benchmark IS in play, which is Eugene's call.
    The gate must not certify a disclosure in that world."""
    bmr = copy.deepcopy(BMR)
    bmr["expectations"]["E4_reconstructed_window_total_b"] = 700.0
    bmr["expectations"]["E4_abs_diff_b"] = abs(
        700.0 - bmr["expectations"]["E4_implied_realized_total_b"])
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]


def test_the_reconstruction_does_not_retire_the_zeros():
    """E5. Every clip month stays far under the window median, which is what
    'the zeros survive it' means."""
    e = BMR["expectations"]
    assert e["E5_reconstruction_still_shows_low_months"] is True
    for m in CLIP:
        assert abs(e["E5_clip_month_paydowns_b"][m]) < 0.5 * e[
            "E5_window_median_paydown_b"], m


def test_a_reconstruction_that_retires_the_zeros_fails():
    """Branch C: if the CUSIP route DID retire them, R2's objection is
    sustained and this is a claim change, not a wording note."""
    bmr = copy.deepcopy(BMR)
    bmr["expectations"]["E5_clip_month_paydowns_b"]["2024-04"] = 17.0
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]


# --- sourceability --------------------------------------------------------
def test_neither_route_r2_named_is_available():
    src = BMR["sourceability"]
    assert src["monthly_principal_payment_series_available"] is False
    assert src["summary_has_paydown_field"] is False
    assert set(src["monthly_endpoints"]) == {
        "mbs/get/monthly.json", "agency/get/monthly.json"}
    assert all(v == "400" for v in src["monthly_endpoints"].values())
    assert "paydown" not in [f.lower() for f in src["summary_fields"]]


@pytest.mark.parametrize("key,value", [
    ("monthly_principal_payment_series_available", True),
    ("summary_has_paydown_field", True),
])
def test_a_suddenly_available_monthly_series_fails(key, value):
    """If the endpoint appeared, "neither route is usable" would be false."""
    bmr = copy.deepcopy(BMR)
    bmr["sourceability"][key] = value
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]


def test_a_200_on_a_monthly_endpoint_fails():
    bmr = copy.deepcopy(BMR)
    bmr["sourceability"]["monthly_endpoints"]["mbs/get/monthly.json"] = "200"
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]


def test_a_partial_fetch_fails():
    """P4: network failure is non-fatal but explicit, and a run that lost
    weeks cannot back a staleness count over 192 of them."""
    bmr = copy.deepcopy(BMR)
    bmr["parity"]["P4_fetch_failures"] = ["2024-04-03"]
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["artifact_ok"]


def test_a_touched_cap_side_or_an_engine_run_fails():
    for key, value in (("cap_side_untouched", False), ("no_engine_runs", False),
                       ("window_months", 41)):
        bmr = copy.deepcopy(BMR)
        bmr["spec"][key] = value
        ok, info = check(TEX, bmr=bmr)
        assert not ok and not info["artifact_ok"], key


# --- prose spans ----------------------------------------------------------
@pytest.mark.parametrize("key", sorted(BMR_SPANS))
def test_each_static_span_removal_fails(key):
    span = BMR_SPANS[key]
    assert span in TEX, f"vacuous mutation: span {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #122 survived removal of {key!r}")


@pytest.mark.parametrize("key", sorted(DERIVED))
def test_each_derived_span_removal_fails(key):
    span = DERIVED[key]
    assert span in TEX, f"vacuous mutation: {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #122 survived removal of {key!r}")


def test_the_runindex_row_is_undeletable():
    row = BMR_SPANS["runindex_row"]
    assert TEX.count(row) == 1, "vacuous mutation"
    assert TEX.count(BMR_SPANS["run_tag"]) == 2, (
        "expected the tag in the prose citation AND the runindex row")
    ok, info = check(TEX.replace(row, ""))
    assert not ok and "runindex_row" in info["missing"]
    assert "run_tag" not in info["missing"]


@pytest.mark.parametrize("path,delta", [
    (("expectations", "gross_declines_b"), 100.0),
    (("expectations", "E4_reconstructed_window_total_b"), 0.001),
    (("expectations", "E5_window_median_paydown_b"), 2.0),
])
def test_each_derived_figure_drift_fails(path, delta):
    """Trace, by row: gross breaks the gross-vs-net literal; the
    reconstructed total breaks the 4-decimal reconciliation AND the E4 diff
    identity; the median breaks the low-months literal."""
    bmr = copy.deepcopy(BMR)
    node = bmr
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] += delta
    ok, _ = check(TEX, bmr=bmr)
    assert not ok, f"a drifted {'.'.join(path)} must fail against unmoved tex"


@pytest.mark.parametrize("month", CLIP)
def test_a_drifted_clip_month_paydown_breaks_the_printed_row(month):
    bmr = copy.deepcopy(BMR)
    bmr["expectations"]["E5_clip_month_paydowns_b"][month] += 1.0
    ok, info = check(TEX, bmr=bmr)
    assert not ok and "low_months" in info["missing"]


# --- the two variants -----------------------------------------------------
def test_the_two_variants_carry_the_same_paragraphs():
    for span in (DERIVED["reconciles"], DERIVED["stale_counts"],
                 BMR_SPANS["three_of_four"], BMR_SPANS["runindex_row"]):
        assert TEX.count(span) == VARIANT.count(span) == 1, span
    assert len(TEX.split("\n")) == len(VARIANT.split("\n"))


def test_the_landing_did_not_disturb_the_existing_zero_months_account():
    """The clip mechanism, the unclipped values and the h1 run tag all sit in
    the same paragraph with zero headroom; this disclosure is appended to
    that account, not a restatement of it."""
    for span in ("a month-boundary allocation artifact of the reporting "
                 "series, not a behavioral observation",
                 "unclipped values $-1.59$/$-0.49$/$-0.84$/$-0.84$ points",
                 "\\texttt{h1\\_zero\\_months\\_diagnosis}"):
        assert TEX.count(span) == VARIANT.count(span), span
    assert TEX.count("four exact-zero months (June 2022, February 2023, "
                     "April 2024, September 2025)") == 1
