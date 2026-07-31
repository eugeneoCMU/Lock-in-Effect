"""Battery for the engine confirmation of the book-sched wedge (R33-B E1).

The landed wedge came from an accounting decomposition. With a FRED key and
the pinned cohort book available, the engine was asked directly. Spec and
runner were committed before the run; this battery locks the E1 outcome.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    book_sched_wedge_check,
    monte_carlo_figure_currency_check,
)

ENG = json.loads((ROOT / "abm" / "data"
                  / "r33b_engine_confirmation_results.json").read_text())
DECOMP = json.loads((ROOT / "abm" / "data"
                     / "r33b_book_sched_results.json").read_text())
CROSS = json.loads((ROOT / "abm" / "data"
                    / "cross_design_results.json").read_text())
TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()


def test_spec_was_committed_before_the_run():
    assert ENG["spec"] == "specs/SPEC_R33B_engine_confirmation.md"
    assert (ROOT / ENG["spec"]).exists()


def test_g0_parity_is_exact():
    """Live FRED reproduced the frozen figures to machine precision."""
    assert ENG["G0_parity"]["pass"] is True
    for name, c in ENG["G0_parity"]["checks"].items():
        assert c["pass"] is True, name
        assert abs(c["diff"]) == 0.0, (name, c["diff"])


def test_branch_is_e1():
    assert ENG["verdict"]["branch"] == "E1"
    assert ENG["wedge"]["direction_prediction_held"] is True
    assert ENG["t2_on_engine_wedge"]["branch_unchanged"] is True
    assert ENG["t2_on_engine_wedge"]["seeds_below"] == 16


def test_engine_wedge_within_e1_tolerance():
    """E1 is |engine - decomp| <= $3bn; the observed gap is ~$0.38bn."""
    gap = ENG["wedge"]["abs_gap_b"]
    assert gap <= 3.0
    assert abs(gap - abs(ENG["wedge"]["delta_engine_b"]
                         - DECOMP["delta"]["primary_b"])) < 1e-9


def test_engine_reproduces_committed_cross_design_share():
    """The PARITY leg is the committed cross-design, bit-exactly."""
    p = ENG["legs"]["parity_population_sched"]
    want = CROSS["variants"]["recalibrated"]
    assert abs(p["trapped_b"] - want["trapped_b"]) < 1e-9
    assert abs(p["share_pct"] - want["share_pct"]) < 1e-9


def test_book_leg_uses_the_pinned_cohort_book():
    """The BOOK leg's scheduled annualized rate must match the pinned book."""
    book = ENG["legs"]["book_sched"]
    # Manifest annualized is 3.116956; the engine reports it on the same series.
    assert abs(book["sched_annualized_pct"] - 3.116956) < 1e-4


def test_manuscript_carries_the_engine_corroboration():
    for tex, label in ((TEX, "main"), (VARIANT, "variant")):
        ok, info = book_sched_wedge_check(tex)
        assert ok, f"gate #127 fails on {label}: {info}"
        assert info["engine_ok"] is True
        assert info["engine_branch"] == "E1"


def test_intro_and_conclusion_cannot_restate_bare_unanimity():
    """Coherence pass: L59 / L740 must carry the book-basis hedge."""
    bare_intro = (
        "on all fifty seeds the real-covariate leg crossed the threshold, "
        "fixed before that run, at which that reading is undercut "
        "(Section~\\ref{sec:robustness-crossdesign})."
    )
    bare_conclusion = (
        "reaching 59.3\\% (76.3\\% at the book's composition), above the "
        "pre-committed threshold"
    )
    for tex, label in ((TEX, "main"), (VARIANT, "variant")):
        assert bare_intro not in tex, f"bare intro unanimity returned in {label}"
        assert bare_conclusion not in tex, f"bare conclusion returned in {label}"
        assert "fifty-of-fifty unanimity does not" in tex
        assert ("50.9\\% and 51.9\\% when re-scored on the book's own "
                "scheduled amortization") in tex


def test_long_abstract_carries_book_sched_hedge():
    assert ("50.9\\% and 51.9\\% on the book's own scheduled amortization, "
            "where sixteen of fifty seeds fall below the threshold") in VARIANT


def test_monte_carlo_figure_is_the_foldin_run():
    """The defect the FRED session exposed: the root figure was stale."""
    ok, info = monte_carlo_figure_currency_check(TEX)
    assert ok, info
    assert info["png_matches_frozen_run"] is True
    assert abs(info["root_csv_mean"] - 103.68) < 0.01
