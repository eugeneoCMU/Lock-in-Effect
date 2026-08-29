"""Battery for gate #110 (R32 C-94: the note-rate-basis WAL row).

Same convention as the #105-#108 batteries: every mutation is verified
non-vacuous before it is applied. The artifact-perturbation tests exercise the
anti-drift direction (a moved artifact fails against the unmoved tex) and the
live cross-artifact tie to the coupon-convention run that owns the basis.

The BASIS EFFECT tests are the ones that matter most here. C-94 is about a
difference between two rows, and a difference is what drifts silently: either
row could move on a rerun and leave the tablenote's "0.5 years" arithmetically
wrong while both individual rows still looked sane.
"""
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import wal_note_rate_basis_check  # noqa: E402

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
WNRB = json.loads((ROOT / "hazard" / "data"
                   / "wal_note_rate_basis_results.json").read_text())
AMORT = json.loads((ROOT / "hazard" / "data"
                    / "coupon_convention_amortization_results.json").read_text())

ROW = "Empirical path, note-rate WAC basis (5.79\\%) & 8.9 & 8.1 \\\\"
ABM_ROW = "Empirical path, ABM-basis back-out (5.14\\%) & 9.4 & 8.5 \\\\"
EFFECT = ("shortens the empirical path by 0.5 years at the window's open "
          "and 0.4 at its close")
DISCLAIMER = "mix conventions inside one statistic"


def test_gate_passes_on_the_manuscript():
    ok, info = wal_note_rate_basis_check(TEX, WNRB, AMORT)
    assert ok, f"gate #110 fails on the shipped manuscript: {info}"


def test_variant_carries_the_row():
    ok, info = wal_note_rate_basis_check(VARIANT, WNRB, AMORT)
    assert ok, f"gate #110 fails on the long-abstract variant: {info}"


def test_row_removal_fails():
    assert ROW in TEX, "row not in the manuscript (vacuous mutation)"
    ok, _ = wal_note_rate_basis_check(TEX.replace(ROW, ""), WNRB, AMORT)
    assert not ok


def test_abm_basis_row_removal_fails():
    """Both rows must stand: one basis alone is the defect C-94 removes."""
    assert ABM_ROW in TEX, "ABM-basis row not in the manuscript (vacuous)"
    ok, _ = wal_note_rate_basis_check(TEX.replace(ABM_ROW, ""), WNRB, AMORT)
    assert not ok


def test_basis_effect_removal_fails():
    assert EFFECT in TEX, "effect sentence not present (vacuous mutation)"
    ok, _ = wal_note_rate_basis_check(TEX.replace(EFFECT, ""), WNRB, AMORT)
    assert not ok


def test_basis_effect_misstatement_fails():
    """The stated difference must be the arithmetic one, not a plausible one."""
    assert EFFECT in TEX
    wrong = EFFECT.replace("0.5 years", "0.9 years")
    assert wrong != EFFECT
    ok, _ = wal_note_rate_basis_check(TEX.replace(EFFECT, wrong), WNRB, AMORT)
    assert not ok


def test_effect_goes_stale_when_either_row_moves():
    """Move the NEW row only: the levels change, so the stated 0.5 must fail."""
    w = copy.deepcopy(WNRB)
    w["rows"]["empirical_note_rate_basis"]["wal_june_2022"] += 0.1
    ok, _ = wal_note_rate_basis_check(TEX, w, AMORT)
    assert not ok, "a drifted artifact must fail against the unmoved tex"


def test_committed_comparator_drift_fails():
    """Move the COMMITTED side: the difference is re-derived, so it must fail."""
    w = copy.deepcopy(WNRB)
    w["comparators"]["empirical_abm_basis_committed"]["wal_june_2022"] += 0.1
    ok, _ = wal_note_rate_basis_check(TEX, w, AMORT)
    assert not ok, "both sides of the comparison must be bound"


def test_cross_artifact_tie_is_live():
    a = copy.deepcopy(AMORT)
    a["hazard_legs"]["delta_080"]["mean_cpr_pct"] += 1e-9
    ok, _ = wal_note_rate_basis_check(TEX, WNRB, a)
    assert not ok, "the basis must stay tied to the coupon-convention run"


def test_wrong_leg_would_fail():
    """Pointing the tie at the hazard-basis leg must not pass."""
    a = copy.deepcopy(AMORT)
    a["hazard_legs"]["delta_080"]["mean_cpr_pct"] = (
        a["hazard_legs"]["committed_0250"]["mean_cpr_pct"])
    ok, _ = wal_note_rate_basis_check(TEX, WNRB, a)
    assert not ok


def test_parity_false_fails():
    w = copy.deepcopy(WNRB)
    w["parity"]["nine_rows_bit_identical"] = False
    ok, _ = wal_note_rate_basis_check(TEX, w, AMORT)
    assert not ok, "a landing may not survive its own parity failure"


def test_monotonicity_flag_false_fails():
    w = copy.deepcopy(WNRB)
    w["expectations"]["E3_strictly_shorter_than_5p14_row"] = False
    ok, _ = wal_note_rate_basis_check(TEX, w, AMORT)
    assert not ok


def test_precision_flag_false_fails():
    w = copy.deepcopy(WNRB)
    w["parity"]["printed_row_precision_insensitive"] = False
    ok, _ = wal_note_rate_basis_check(TEX, w, AMORT)
    assert not ok


def test_mixed_basis_disclaimer_required():
    """Dropping the disclaimer re-opens the mixed-basis extension trap."""
    assert DISCLAIMER in TEX
    ok, _ = wal_note_rate_basis_check(TEX.replace(DISCLAIMER, ""), WNRB, AMORT)
    assert not ok


def test_run_tag_indexed():
    assert TEX.count("\\texttt{wal\\_note\\_rate\\_basis}") >= 1
    assert VARIANT.count("\\texttt{wal\\_note\\_rate\\_basis}") >= 1


def test_note_rate_row_is_strictly_shorter_than_both_committed_bases():
    """The physical claim, re-derived rather than trusted."""
    nr = WNRB["rows"]["empirical_note_rate_basis"]
    hz = WNRB["rows"]["empirical_hazard_basis"]
    emp = WNRB["comparators"]["empirical_abm_basis_committed"]
    assert nr["mean_cpr_pct"] > hz["mean_cpr_pct"] > emp["mean_cpr_pct"]
    assert nr["wal_june_2022"] < hz["wal_june_2022"] < emp["wal_june_2022"]
    assert nr["wal_nov_2025"] < hz["wal_nov_2025"] < emp["wal_nov_2025"]
