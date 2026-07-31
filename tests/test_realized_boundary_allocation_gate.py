"""Battery for gate #121 (R32 C-128: the realized-side boundary allocation).

Four failure modes drive what these tests bind hardest on.

A SENSITIVITY READING AS THE COMMITTED NUMBER. The production convention is
calendar and the committed settlement variant is the CAP-side one at
$-42.0$bn. The both-aligned $-25.4$bn is a rider on it. One test moves the
new clause ahead of the cap-only account and asserts ONLY `cap_only_leads`
flips -- every span still present, every artifact identity intact.

AN ASSERTED OFFSET -- AND THE IDENTITY THAT COULD NOT AUDIT IT. The first
version of this battery claimed "gives back $16.6bn" was auditable because
mass_in - mass_out equals both_aligned - cap_only for every kernel. That was
wrong, and it let a false pair of figures ship in bf31cd2. mass_out was
computed as the residual r_tot_cal + mass_in - r_tot_set, so the difference
collapsed to r_tot_set - r_tot_cal for ANY mass_in: the identity held no
matter how wrong mass_in was, and the run's own P5 gate was tautological for
the same reason. The manuscript carried $4.5bn/$21.2bn when the true masses
were $6.8bn/$23.4bn.

The identity is still tested, because it must still hold. But the check that
BITES is now the external anchor: mass_out re-derived from
benchmark_monthly_rebuild's monthly series, a run C-128 never reads. An
identity between two quantities cannot police either one when one is defined
from the other -- only an outside anchor can. See
test_a_correlated_shift_in_both_masses_is_caught_by_the_anchor, which
reproduces the exact shape of the shipped defect.

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
BMR = json.loads((ROOT / "hazard" / "data"
                  / "benchmark_monthly_rebuild_results.json").read_text())

# The literals the gate BUILDS from the artifact, written out here so a silent
# artifact change breaks this file as well as the gate.
DERIVED = {
    "pre_window": "the two months the kernel reaches back into settle into "
                  "its start",
    "boundary_decomp": "the realized leg gains \\$6.8 billion there against "
                       "\\$23.4 billion leaving at the end",
    "gives_back": "giving back \\$16.6 billion of the cap-side \\$42.0 billion",
    "both_aligned": "lands the benchmark at \\$739.4 billion",
    "shift": "a shift of $-\\$25.4$ billion or $-3.3$\\%",
    "bracket": "bracket at $-\\$19.0$ and $-\\$29.2$ billion",
    "threshold_share": "at 3.3\\% of the committed benchmark the boundary "
                       "treatment",
}

# the committed cap-side account this landing must sit BEHIND
CAP_ONLY_LIT = "the benchmark moves by exactly that \\$42.0 billion"


def check(tex, rba=None, smb=None, bmr=None):
    return realized_boundary_allocation_check(
        tex, rba or RBA, smb or SMB, bmr or BMR)


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
    assert ("realized_boundary_allocation_check(tex, _rba, _smb121, _bmr)"
            in GATES_SRC)
    assert "BMR_RESULTS = " in GATES_SRC
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


def test_the_prose_tracks_the_KERNEL_REACH_not_the_pre_window_count():
    """The manuscript briefly conflated these. 17 pre-window months exist, but
    a length-3 kernel sees only len(k)-1 = 2 of them; the other 15 contribute
    exactly zero to every artifact field. Trace: moving P4 must NOT disturb the
    span (it is not what the prose describes), while lengthening the kernel
    must, because the reach is then 3."""
    rba = copy.deepcopy(RBA)
    rba["parity"]["P4_pre_window_months"] = 25
    ok, info = check(TEX, rba=rba)
    assert ok, "the spelled-out word must not track P4"

    rba2 = copy.deepcopy(RBA)
    rba2["parity"]["P3_kernel"] = [0.1, 0.5, 0.3, 0.1]
    ok2, info2 = check(TEX, rba=rba2)
    assert not ok2 and "pre_window" in info2["missing"]


# --- THE REGRESSION: the defect that shipped in bf31cd2 -------------------
def test_a_correlated_shift_in_both_masses_is_caught_by_the_anchor():
    """This is the exact shape of the bug that shipped for eight hours.

    The runner weighted the last pre-window month by k[1] instead of
    k[1]+k[2], and mass_out was defined as the residual
    r_tot_cal + mass_in - r_tot_set -- so it absorbed the identical error and
    BOTH masses moved together. mass_in - mass_out was therefore unchanged,
    which is why the P5 gate, gate #121's clause (b) and this battery all
    stayed green over $4.5bn/$21.2bn when the truth was $6.8bn/$23.4bn.

    Trace: shift both masses by the same small amount, chosen so the PRINTED
    figures still round to 6.8 and 23.4. Then `missing` stays empty and
    `decomposition_ok` stays True -- proving the identity is structurally
    blind -- and ONLY `mass_out_anchored` can fail."""
    rba = copy.deepcopy(RBA)
    for leg in ("production", "slower", "faster"):
        rba["legs"][leg]["realized_boundary_mass_in_b"] -= 0.04
        rba["legs"][leg]["realized_boundary_mass_out_b"] -= 0.04
    for leg in ("production", "slower", "faster"):
        lg = rba["legs"][leg]
        assert abs((lg["realized_boundary_mass_in_b"]
                    - lg["realized_boundary_mass_out_b"])
                   - (lg["benchmark_both_aligned_b"]
                      - lg["benchmark_cap_only_b"])) < 1e-6, (
            "vacuous: the shift must preserve the identity")
    ok, info = check(TEX, rba=rba)
    assert not ok, "a correlated mass shift must not pass"
    assert info["missing"] == [], "the printed figures must still round the same"
    assert info["decomposition_ok"], (
        "the P5 identity cannot see a correlated shift -- that is the point")
    assert not info["mass_out_anchored"], "the anchor is what must catch it"


def test_mass_out_re_derives_from_the_rebuild_artifact_on_every_kernel():
    """The anchor, re-derived here. The month i places before the window end
    loses sum(k[i+1:]) past it, and benchmark_monthly_rebuild owns that
    monthly series -- a run C-128 never reads."""
    net = BMR["monthly_net_rolloff_b"]
    months = sorted(net)
    i0 = months.index(BMR["parity"]["P1_clip_months"][0])
    win = months[i0:i0 + BMR["spec"]["window_months"]]
    assert len(win) == 42 and win[0] == "2022-06" and win[-1] == "2025-11"
    for name, lg in RBA["legs"].items():
        k = lg["kernel"]
        derived = -sum(sum(k[i + 1:]) * net[win[-1 - i]] for i in range(len(k) - 1))
        assert abs(lg["realized_boundary_mass_out_b"] - derived) < 1e-6, name


def test_breaking_the_rebuild_series_breaks_the_anchor():
    """Trace: the anchor reads C-127's artifact, so moving the window's final
    month there turns gate #121 red without any C-128 field moving."""
    bmr = copy.deepcopy(BMR)
    bmr["monthly_net_rolloff_b"]["2025-11"] += 1.0
    ok, info = check(TEX, bmr=bmr)
    assert not ok and not info["mass_out_anchored"]
    assert info["missing"] == [] and info["decomposition_ok"]


def test_the_masses_are_no_longer_a_residual_of_each_other():
    """The structural repair. If mass_out were still back-solved, this
    difference would be exactly 0.0 on every kernel and the identity would be
    a tautology. Non-zero float noise is the evidence of independence."""
    slack = []
    for lg in RBA["legs"].values():
        resid = (lg["realized_total_calendar_b"]
                 + lg["realized_boundary_mass_in_b"]
                 - lg["realized_total_settled_b"])
        slack.append(abs(resid - lg["realized_boundary_mass_out_b"]))
        assert slack[-1] < 1e-6, "the identity must still HOLD"
    assert any(s > 0 for s in slack), (
        "every kernel closing to exactly 0.0 would mean mass_out is still "
        "the residual and P5 is still tautological")


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
