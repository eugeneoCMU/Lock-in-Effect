"""Battery for gate #113 (R32 C-76 + C-82: the marginal in transaction counts).

Three of these tests exist because of how this exhibit could go wrong quietly
rather than loudly: the denominator, the upper-bound framing, and the comparator
that was never sourced.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import marginal_transaction_counts_check  # noqa: E402

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
M = json.loads((ROOT / "hazard" / "data"
                / "marginal_transaction_counts_results.json").read_text())


def test_gate_passes_on_the_manuscript():
    ok, info = marginal_transaction_counts_check(TEX, M)
    assert ok, f"gate #113 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = marginal_transaction_counts_check(VARIANT, M)
    assert ok, f"gate #113 fails on the long-abstract variant: {info}"


@pytest.mark.parametrize("cell", ["s_1", "s_0.5", "s_0.25"])
def test_count_drift_fails(cell):
    m = copy.deepcopy(M)
    m["cells"][cell]["book_foregone_payoffs"] *= 1.10
    ok, _ = marginal_transaction_counts_check(TEX, m)
    assert not ok, f"a drifted {cell} count must fail against the unmoved tex"


def test_denominator_drift_fails():
    m = copy.deepcopy(M)
    m["spec"]["denominator_surviving_mean"] += 1000
    ok, _ = marginal_transaction_counts_check(TEX, m)
    assert not ok


def test_wrong_divisor_would_be_caught_by_the_run():
    """The all-loan mean is REJECTED and roughly doubles the count."""
    s = M["spec"]
    assert s["denominator_all_loan_mean_REJECTED"] < s["denominator_surviving_mean"]
    ratio = s["denominator_surviving_mean"] / s["denominator_all_loan_mean_REJECTED"]
    assert 1.7 < ratio < 2.1, "the 'roughly double' warning must stay true"


@pytest.mark.parametrize("phrase", [
    "upper bound",
    "would roughly double the count",
    "cannot be formed without assuming",
])
def test_each_disclosure_is_pinned(phrase):
    assert phrase in TEX, f"{phrase!r} missing (vacuous mutation)"
    ok, _ = marginal_transaction_counts_check(TEX.replace(phrase, ""), M)
    assert not ok, f"{phrase!r} is not pinned"


def test_bracket_is_ordered_and_s1_is_the_bound():
    c = M["cells"]
    assert (c["s_0.25"]["book_foregone_payoffs"]
            < c["s_0.5"]["book_foregone_payoffs"]
            < c["s_1"]["book_foregone_payoffs"])
    assert M["expectations"]["E1_counts_increase_in_s"] is True


def test_s1_reproduces_the_papers_headline():
    """The run is tied to the manuscript, not floating beside it."""
    c1 = M["cells"]["s_1"]
    assert round(c1["marginal_pp"], 1) == 5.6
    assert round(c1["marginal_b"], 1) == 42.6
    assert M["parity"]["s1_reproduces_headline_5p6pp_42p6b"] is True


def test_comparator_provenance_is_recorded():
    cmp_ = M["comparator"]
    assert cmp_["sourced"] is True
    assert cmp_["series_id"] == "EXHOSLUSM495S"
    assert cmp_["first_date"].startswith("2025"), (
        "the whole point is that this account has no pre-2025 history")


def test_the_uncomputed_statistic_is_named_not_dropped():
    nc = M["not_computed"]["share_of_2022_2024_decline"]
    assert "NOT COMPUTED" in nc and "fonseca2026" in nc
    assert "declines to make" in nc


def test_parity_flags_are_load_bearing():
    for key in M["parity"]:
        m = copy.deepcopy(M)
        m["parity"][key] = False
        ok, _ = marginal_transaction_counts_check(TEX, m)
        assert not ok, f"parity flag {key} must be load-bearing"
