"""Battery for gate #121 (R32 C-128: the realized-side boundary allocation).

Four failure modes drive what these tests bind hardest on.

A SENSITIVITY READING AS THE COMMITTED NUMBER. The production convention is
calendar and the committed settlement variant is the CAP-side one at
$-42.0$bn. The both-aligned $-25.4$bn is a rider on it. One test moves the
new clause ahead of the cap-only account and asserts ONLY `cap_only_leads`
flips -- every span still present, every artifact identity intact.

AN ASSERTED OFFSET. "Gives back $16.6bn" is only auditable because
mass_in - mass_out equals both_aligned - cap_only exactly, for every kernel.
The identity is re-derived here rather than read off the artifact's own
summary flag, and breaking it in a single kernel is tested.

REWRITING THE PRE-COMMITMENT. E3 fixed the DIRECTION before the run and
deliberately left the residual's SIGN open. An artifact claiming the sign was
predicted must turn the gate red, or the run's ex-ante record is decorative.

OUTRUNNING THE ARTIFACT. Every printed figure is derived from the run, and
the two committed benchmarks it had to reproduce are tied to
settlement_months_benchmark -- a run this one did not write. Each derived
figure has a drift test; each tie has a mutation test.

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
    RBA_SPANS,
    realized_boundary_allocation_check,
)

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
GATES_SRC = (ROOT / "tools" / "liveness_gates.py").read_text()
RBA = json.loads((ROOT / "hazard" / "data"
                  / "realized_boundary_allocation_results.json").read_text())
SMB = json.loads((ROOT / "hazard" / "data"
                  / "settlement_months_benchmark_results.json").read_text())

# The literals the gate BUILDS from the artifact, written out here so a silent
# artifact change breaks this file as well as the gate.
DERIVED = {
    "pre_window": "seventeen pre-QT months of realized roll-off",
    "boundary_decomp": "the realized leg gains \\$4.5 billion there against "
                       "\\$21.2 billion leaving at the end",
    "gives_back": "giving back \\$16.6 billion of the cap-side \\$42.0 billion",
    "both_aligned": "lands the benchmark at \\$739.4 billion",
    "shift": "a shift of $-\\$25.4$ billion or $-3.3$\\%",
    "bracket": "bracket at $-\\$19.0$ and $-\\$29.2$ billion",
    "threshold_share": "at 3.3\\% of the committed benchmark the boundary "
                       "treatment",
}

# the committed cap-side account this landing must sit BEHIND
CAP_ONLY_LIT = "the benchmark moves by exactly that \\$42.0 billion"


def check(tex, rba=None, smb=None):
    return realized_boundary_allocation_check(tex, rba or RBA, smb or SMB)


def test_gate_passes_on_the_manuscript():
    ok, info = check(TEX)
    assert ok, f"gate #121 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = check(VARIANT)
    assert ok, f"gate #121 fails on the long-abstract variant: {info}"


def test_the_gate_is_wired_into_the_suite():
    """An unwired gate is a green suite that checks nothing. Trace: both
    artifact constants, the call site with its cross-tie argument, and the
    gate number must all exist in the gate source."""
    assert "RBA_RESULTS = " in GATES_SRC
    assert "SMB_RESULTS = " in GATES_SRC
    assert ("realized_boundary_allocation_check(tex, _rba, _smb121)"
            in GATES_SRC)
    assert "#121" in GATES_SRC


# --- (a) the committed cap-side account must still lead -------------------
def test_the_cap_only_account_must_come_first():
    """The committed convention is the cap-side one; $-25.4$bn is a rider.

    Trace: the new clause is moved AHEAD of the cap-only sentence and nothing
    else changes -- both spans survive, so `missing` stays empty and every
    artifact identity holds. ONLY `cap_only_leads` may flip."""
    direction = RBA_SPANS["direction"]
    assert 0 <= TEX.find(CAP_ONLY_LIT) < TEX.find(direction), (
        "vacuous: the cap-only account does not already lead")
    # lift the whole new sentence and re-seat it before the cap-only account
    moved = TEX.replace(f" Aligning the realized leg as well {direction}.", "", 1)
    assert moved != TEX, "vacuous mutation: the new sentence was not found"
    moved = moved.replace(
        CAP_ONLY_LIT, f"aligning the realized leg as well {direction}, and "
                      f"{CAP_ONLY_LIT}", 1)
    ok, info = check(moved)
    assert not ok
    assert not info["cap_only_leads"]
    assert info["missing"] == [], info["missing"]
    assert info["artifact_ok"] and info["cross_artifact_tie"]


# --- prose spans ----------------------------------------------------------
@pytest.mark.parametrize("key", sorted(RBA_SPANS))
def test_each_static_span_removal_fails(key):
    span = RBA_SPANS[key]
    assert span in TEX, f"vacuous mutation: span {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #121 survived removal of {key!r}")


@pytest.mark.parametrize("key", sorted(DERIVED))
def test_each_derived_span_removal_fails(key):
    span = DERIVED[key]
    assert span in TEX, f"vacuous mutation: {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #121 survived removal of {key!r}")


def test_the_runindex_row_is_undeletable():
    """The tag alone cannot carry the row: it also sits in the prose citation,
    so the row is pinned by its description."""
    row = RBA_SPANS["runindex_row"]
    assert TEX.count(row) == 1, "vacuous mutation"
    assert TEX.count(RBA_SPANS["run_tag"]) == 2, (
        "expected the tag in the prose citation AND the runindex row")
    ok, info = check(TEX.replace(row, ""))
    assert not ok and "runindex_row" in info["missing"]
    assert "run_tag" not in info["missing"], (
        "deleting the row must not be masked by the prose citation")


# --- derived literals must track the artifact -----------------------------
@pytest.mark.parametrize("leg,key,delta", [
    ("production", "benchmark_both_aligned_b", 1.0),
    ("production", "shift_both_b", 1.0),
    ("production", "shift_both_pct_of_committed", 0.5),
    ("production", "realized_boundary_mass_in_b", 1.0),
    ("production", "realized_boundary_mass_out_b", 1.0),
    ("production", "cap_edge_loss_b", 1.0),
    ("production", "shift_cap_only_b", 1.0),
    ("faster", "shift_both_b", 1.0),
    ("slower", "shift_both_b", 1.0),
])
def test_each_derived_figure_drift_fails(leg, key, delta):
    """Trace, by row: both_aligned and shift_both break their printed
    literals; the pct breaks the shift and threshold spans AND the E4
    share identity; the two mass rows break the decomposition literal and
    the mass_in - mass_out identity; cap_edge and shift_cap_only break the
    gives-back arithmetic; the two off-kernel shifts break the bracket."""
    rba = copy.deepcopy(RBA)
    rba["legs"][leg][key] += delta
    ok, _ = check(TEX, rba=rba)
    assert not ok, f"a drifted {leg}.{key} must fail against unmoved tex"


@pytest.mark.parametrize("path", [
    ("calendar_benchmark_b",),
    ("legs", "production", "benchmark_b"),
    ("n_qt_active_months",),
    ("window_edge_cap_mass_lost_b",),
])
def test_the_settlement_benchmark_tie_mutations_fail(path):
    """The two committed benchmarks, the QT month count and the cap edge loss
    belong to settlement_months_benchmark -- a run this one did not write.
    Trace: moving any of them breaks cross_artifact_tie without a single
    printed literal having to move."""
    smb = copy.deepcopy(SMB)
    node = smb
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] = node[path[-1]] + 1
    ok, info = check(TEX, smb=smb)
    assert not ok and not info["cross_artifact_tie"]


def test_a_moved_kernel_breaks_the_tie():
    smb = copy.deepcopy(SMB)
    smb["kernel_production"] = [0.2, 0.5, 0.3]
    ok, info = check(TEX, smb=smb)
    assert not ok and not info["cross_artifact_tie"]


# --- (b) the offset is decomposed, not asserted ---------------------------
def test_the_boundary_decomposition_identity_holds_for_every_kernel():
    """P5, re-derived here rather than read off the artifact's own flag:
    mass_in - mass_out must equal both_aligned - cap_only."""
    for name, lg in RBA["legs"].items():
        lhs = (lg["realized_boundary_mass_in_b"]
               - lg["realized_boundary_mass_out_b"])
        rhs = lg["benchmark_both_aligned_b"] - lg["benchmark_cap_only_b"]
        assert abs(lhs - rhs) < 1e-6, name


@pytest.mark.parametrize("leg", ["production", "slower", "faster"])
def test_breaking_the_decomposition_in_any_single_kernel_fails(leg):
    """Trace: shifting one leg's mass_out alone breaks that leg's identity.
    The artifact's own P5 flag stays True, which is the point -- the gate
    re-derives rather than trusting it."""
    rba = copy.deepcopy(RBA)
    rba["legs"][leg]["realized_boundary_mass_out_b"] += 5.0
    assert rba["parity"]["P5_boundary_decomposition_sums"] is True
    ok, info = check(TEX, rba=rba)
    assert not ok and not info["decomposition_ok"]


def test_a_lying_p5_flag_cannot_rescue_a_broken_decomposition():
    """The converse: the flag alone must not be able to carry the gate."""
    rba = copy.deepcopy(RBA)
    rba["legs"]["slower"]["benchmark_both_aligned_b"] += 7.0
    ok, info = check(TEX, rba=rba)
    assert not ok and not info["decomposition_ok"]


def test_the_gives_back_figure_is_the_difference_of_the_two_shifts():
    p = RBA["legs"]["production"]
    give_back = abs(p["shift_cap_only_b"]) - abs(p["shift_both_b"])
    assert abs(give_back - 16.616017783) < 1e-6
    assert f"\\${give_back:.1f} billion of the cap-side" in TEX


# --- (c) the pre-commitment split -----------------------------------------
def test_claiming_the_sign_was_predicted_fails():
    """E3 fixed the direction and deliberately left the residual's SIGN open.
    Trace: flipping the artifact's own honesty flag turns the gate red, so the
    ex-ante record cannot be quietly upgraded after the fact."""
    rba = copy.deepcopy(RBA)
    rba["expectations"]["E3_sign_deliberately_not_predicted"] = False
    ok, info = check(TEX, rba=rba)
    assert not ok and not info["artifact_ok"]


def test_e3_must_hold_for_every_kernel_not_just_the_production_one():
    """The claim is that aligning BOTH legs moves less than aligning the cap
    alone. Trace: making one off-kernel violate it breaks decomposition_ok."""
    for leg in ("production", "slower", "faster"):
        assert abs(RBA["legs"][leg]["shift_both_b"]) < abs(
            RBA["legs"][leg]["shift_cap_only_b"]), leg
    rba = copy.deepcopy(RBA)
    rba["legs"]["faster"]["shift_both_b"] = -99.0
    ok, info = check(TEX, rba=rba)
    assert not ok and not info["decomposition_ok"]


def test_a_failed_e3_flag_fails():
    rba = copy.deepcopy(RBA)
    rba["expectations"]["E3_both_moves_less_than_cap_only"] = False
    ok, info = check(TEX, rba=rba)
    assert not ok and not info["artifact_ok"]


# --- (d) the disclosure threshold is the artifact's own -------------------
def test_the_ten_percent_bar_is_read_from_the_run_not_typed_here():
    assert RBA["expectations"]["E4_max_share"] == 0.1
    assert "E4_max_share" not in GATES_SRC.split("def main")[0].replace(
        'exp["E4_max_share"]', ""), "the bar must not be re-typed as a literal"
    share = RBA["expectations"]["E4_shift_share_of_committed"]
    assert share < RBA["expectations"]["E4_max_share"]
    assert abs(share - abs(RBA["legs"]["production"]["shift_both_b"])
               / SMB["calendar_benchmark_b"]) < 1e-12


def test_a_shift_past_the_threshold_fails():
    """Branch C: a boundary treatment moving the benchmark >=10% is not a
    disclosure and is Eugene's call, not a coordinator's. Trace: the gate must
    not certify a manuscript that still calls it a disclosed sensitivity."""
    rba = copy.deepcopy(RBA)
    rba["expectations"]["E4_shift_share_of_committed"] = 0.15
    rba["expectations"]["E4_pass"] = False
    ok, info = check(TEX, rba=rba)
    assert not ok and not info["artifact_ok"]


def test_too_few_pre_window_months_fails():
    """P4: a length-3 kernel needs 3 pre-window months, or the run convolved
    against zeros and fabricated the very asymmetry it is measuring."""
    rba = copy.deepcopy(RBA)
    rba["parity"]["P4_pre_window_months"] = 2
    ok, info = check(TEX, rba=rba)
    assert not ok and not info["artifact_ok"]


def test_a_changed_pre_window_count_breaks_the_spelled_out_word():
    """The prose spells the count. Trace: an unmapped count falls through to
    digits, so the span stops matching rather than silently disagreeing."""
    rba = copy.deepcopy(RBA)
    rba["parity"]["P4_pre_window_months"] = 18
    ok, info = check(TEX, rba=rba)
    assert not ok and "pre_window" in info["missing"]


def test_an_engine_run_or_a_rebased_convention_fails():
    for key, value in (("no_engine_runs", False),
                       ("production_convention_stays_calendar", False),
                       ("kernel_imported_not_estimated", False)):
        rba = copy.deepcopy(RBA)
        rba["spec"][key] = value
        ok, info = check(TEX, rba=rba)
        assert not ok and not info["artifact_ok"], key


# --- the two variants -----------------------------------------------------
def test_the_two_variants_carry_the_same_paragraphs():
    for span in (DERIVED["both_aligned"], DERIVED["shift"],
                 RBA_SPANS["direction"], RBA_SPANS["runindex_row"]):
        assert TEX.count(span) == VARIANT.count(span) == 1, span
    assert len(TEX.split("\n")) == len(VARIANT.split("\n"))


def test_the_landing_did_not_disturb_the_committed_cap_side_account():
    """The cap-side variant keeps its own figures with zero headroom: the
    landing adds a leg, it does not restate the committed one."""
    assert TEX.count(CAP_ONLY_LIT) == VARIANT.count(CAP_ONLY_LIT) == 1
    assert TEX.count("a settlement-aligned benchmark of \\$722.7 billion") == 1
    assert TEX.count("$-\\$28.0$ and $-\\$52.5$ billion") == 1
    assert TEX.count("\\texttt{settlement\\_months\\_benchmark}") == 1
