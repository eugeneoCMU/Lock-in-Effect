"""Battery for gate #120 (R32 C-79: the Danish leg with an interest-only share).

Four failure modes drive what these tests bind hardest on.

REVERSION AT THE TWO SITES THIS LANDING CHANGES. .tex:629 carried an
unmeasured concession and .tex:660 carried an unconditional "gross
institutional relief under face accounting, not a net social gain". Both
spellings are tested by restoring them and confirming the gate goes red
through `retired_present`, not merely through a missing span.

LEADING WITH AN IMPORTED PARAMETER. The break-even needs no external input
and is the deliverable; the 45% is pre-window, deferred-amortisation and
whole-market. Two tests bite here: one moves the crossing clause after the
imported share and asserts ONLY the ordering conjunct fails, one adds a
second bare printing of the share and asserts the limits-travel conjunct
fails while `missing` stays empty.

THE FALSE NON-COMPOSITION ACCOUNT. An earlier draft said stacking C-75's
cash haircut and this face reversal "would charge the same dollars twice".
E = dk_total - sched already EXCLUDES the scheduled dollars an interest-only
share removes, so the pools are disjoint; they share a balance path, and the
deferred balance's own prepayment ADDS to the early face, so a naive sum
UNDERSTATES the haircut. The arithmetic is re-derived here, and the assertive
spelling is tested to turn the gate red.

OUTRUNNING THE ARTIFACT. Every printed figure is derived from the run, and
the three committed constants it rests on are tied to two artifacts this run
did not write. Each derived figure has a drift test; each tie has a mutation
test.

Every mutation is verified non-vacuous before it is applied.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    DANISH_IO_RETIRED,
    DANISH_IO_SHARE_SPANS,
    danish_interest_only_share_check,
)

# V20 closing-session rescope: app:ledger/app:verdicts live in the standalone
# replication_appendices.tex; the gated corpus is manuscript + that file.
TEX = ((ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
       + "\n" + (ROOT / "paper" / "v18" / "replication_appendices.tex").read_text())
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text() \
    + "\n" + (ROOT / "paper" / "v18" / "replication_appendices.tex").read_text()  # V20 rescope
BIB = (ROOT / "paper" / "v18" / "references.bib").read_text()
GATES_SRC = (ROOT / "tools" / "liveness_gates.py").read_text()
IO = json.loads((ROOT / "hazard" / "data"
                 / "danish_interest_only_share_results.json").read_text())
DAN = json.loads((ROOT / "hazard" / "data"
                  / "danish_us_intercept_results.json").read_text())
CB = json.loads((ROOT / "hazard" / "data"
                 / "buyback_credit_bracket_results.json").read_text())

# The literals the gate BUILDS from the artifact, written out here so a
# silent artifact change breaks this file as well as the gate.
DERIVED = {
    "sched_basis": "cuts the face gap by $\\sigma$ times \\$198.67 billion",
    "crossing_first": "crosses zero at an interest-only share of 30.8\\%",
    "crossing_second": "lifts the crossing to 34.3\\%",
    "danish_speed": "the Danish leg's own 5.61\\% speed returns \\$9.1 "
                    "billion of extra early roll-off at a 45\\% share",
    "gap_at_sourced": "the face gap is $-\\$19.2$ billion after that "
                      "feedback",
    "sourced_share": "interest-only loans at 45\\% of outstanding mortgage "
                     "volumes",
    "tablenote_crossing": "above a Danish interest-only share of 34.3\\% the "
                          "face gap reverses too",
    "conclusion_crossing": "the interest-only crossing above sits at 34.3\\%",
    "disjoint_pools": "the \\$470.7 billion of early face the buyback credit "
                      "haircuts is Danish roll-off net of the scheduled "
                      "component",
    "feedback_size": "the deferred balance's own prepayment (\\$9.1 billion "
                     "at a 45\\% share) adds to it",
}

SOURCED_LIT = "45\\% of outstanding mortgage volumes"
NEW_FACE_SENTENCE = (
    "So $+\\$61.2$ billion is gross institutional relief under face "
    "accounting and a held-fixed Danish product mix, not a net social gain.")
OLD_FACE_SENTENCE = (
    "So $+\\$61.2$ billion is gross institutional relief under face "
    "accounting, not a net social gain.")
NEW_CONCESSION = (
    "The large interest-only share cuts scheduled amortization, the null's "
    "largest component, and so moves the shortfall against the payoff rule;")
OLD_CONCESSION = (
    "The large interest-only share, which would cut scheduled amortization, "
    "the null's largest component, and so move the shortfall in the opposite "
    "direction from the payoff rule;")
UNDERSTATEMENT = (
    "Summing the two cells would therefore understate the haircut rather "
    "than charge the same dollars twice.")


def check(tex, io=None, dan=None, cb=None):
    return danish_interest_only_share_check(
        tex, io or IO, dan or DAN, cb or CB)


def test_gate_passes_on_the_manuscript():
    ok, info = check(TEX)
    assert ok, f"gate #120 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = check(VARIANT)
    assert ok, f"gate #120 fails on the long-abstract variant: {info}"


def test_the_gate_is_wired_into_the_suite():
    """An unwired gate is a green suite that checks nothing. Trace: the call
    site and the artifact constant must both exist, and the call must pass
    the two artifacts loaded for gate #117 rather than re-reading them."""
    assert "DIOS_RESULTS = " in GATES_SRC
    assert ("danish_interest_only_share_check(tex, _dios, _bdan, _bbcb)"
            in GATES_SRC)
    assert "#120" in GATES_SRC


# --- (a) the two reversions this gate exists for --------------------------
def test_restoring_the_unconditional_face_sentence_fails():
    """Trace: the retired spelling re-enters tex_nc so `retired_present` is
    non-empty, and the same replacement deletes the face_scope span so
    `missing` names it. Both halves asserted, so the test cannot be satisfied
    by the absence check alone."""
    assert NEW_FACE_SENTENCE in TEX, "vacuous mutation"
    mutated = TEX.replace(NEW_FACE_SENTENCE, OLD_FACE_SENTENCE, 1)
    ok, info = check(mutated)
    assert not ok
    assert DANISH_IO_RETIRED[1] in info["retired_present"]
    assert "face_scope" in info["missing"]


def test_restoring_the_unmeasured_concession_fails():
    """Trace: restoring the .tex:629 concession puts DANISH_IO_RETIRED[0]
    back into tex_nc. The rest of the paragraph is untouched, so this can
    only be caught through the absence check."""
    assert NEW_CONCESSION in TEX, "vacuous mutation"
    mutated = TEX.replace(NEW_CONCESSION, OLD_CONCESSION, 1)
    ok, info = check(mutated)
    assert not ok
    assert DANISH_IO_RETIRED[0] in info["retired_present"]


@pytest.mark.parametrize("lit", DANISH_IO_RETIRED)
def test_the_retired_spellings_are_absent_from_both_variants(lit):
    assert lit not in TEX and lit not in VARIANT


# --- (b) the break-even is primary ----------------------------------------
def test_the_break_even_must_be_stated_before_the_imported_share():
    """The crossing needs no external input; the 45% is pre-window,
    deferred-amortisation and whole-market. Trace: the crossing clause is
    moved to AFTER the imported share and nothing else changes -- both spans
    are still present, all four limits still sit on the share's line, so
    `missing` and `limits_travel` are unaffected and ONLY
    `breakeven_before_import` flips."""
    cross, src = DERIVED["crossing_first"], DERIVED["sourced_share"]
    assert 0 <= TEX.find(cross) < TEX.find(src), "vacuous: already ordered"
    mutated = TEX.replace(cross, "@@X@@", 1)
    mutated = mutated.replace(src, f"{src}, and it {cross}", 1)
    mutated = mutated.replace("@@X@@", "reverses the face gap")
    assert mutated.count(cross) == 1 and mutated != TEX
    ok, info = check(mutated)
    assert not ok
    assert not info["breakeven_before_import"]
    assert info["missing"] == [] and info["limits_travel"]


def test_a_second_bare_printing_of_the_imported_share_fails():
    """The three limits travel with the 45% WHEREVER it is read. Trace: a
    second line printing the share without them leaves every span present
    and every artifact identity intact, so `limits_travel` is the only
    conjunct that can catch it -- which is exactly the point."""
    mutated = TEX + ("\n\nA stray restatement: Denmark reports 45\\% of "
                     "outstanding mortgage volumes.\n")
    ok, info = check(mutated)
    assert not ok
    assert not info["limits_travel"]
    assert info["missing"] == [] and info["artifact_ok"]


@pytest.mark.parametrize("key", [
    "limit_prewindow", "limit_deferred", "limit_not_permanent",
    "limit_population",
])
def test_dropping_any_limit_breaks_both_presence_and_travel(key):
    span = DANISH_IO_SHARE_SPANS[key]
    assert span in TEX, f"vacuous mutation: {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok
    assert key in info["missing"] and not info["limits_travel"]


# --- (c) the double-counting account stays retracted ----------------------
def test_the_double_counting_claim_may_not_return():
    """The false account may not come back, in ANY form -- including negated.

    An earlier draft explained the non-composition as "would charge the same
    dollars twice". E = dk_total - sched already excludes the scheduled dollars
    an interest-only share removes, so the pools are disjoint and nothing is
    double-counted; the real relation is a shared balance path. Trace: the gate
    conjunct is a bare absence test, so re-inserting the phrase anywhere --
    negated or not -- turns it red, and the four spans carrying the true
    account are pinned separately, so deleting THEM turns it red too.
    """
    assert "the same dollars twice" not in TEX
    ok, _ = check(TEX)
    assert ok
    # re-inserting it, even negated, must fail
    ok2, info2 = check(TEX.replace(
        "understate the haircut, not double-count it",
        "understate the haircut rather than charge the same dollars twice", 1))
    assert not ok2, "a negated restatement of the false account must still fail"
    # and dropping the true account must fail
    ok3, info3 = check(TEX.replace("but they share a balance path", "", 1))
    assert not ok3
    assert "shared_balance_path" in info3["missing"]

def test_the_two_pools_really_are_disjoint_and_the_sum_understates():
    """The claim, re-derived rather than asserted. E is Danish roll-off NET
    of the scheduled component, so it contains none of the dollars an
    interest-only share removes; and the deferred balance's own prepayment
    ADDS to E, so charging the committed haircut on the unmoved E is the
    smaller number."""
    p = IO["parity"]
    E, sched = p["P1_buyback_identity_E_b"], p["P1_sched_total_b"]
    assert E == CB["verdict"]["early_face_E_b"]
    off = IO["at_sourced_share"]["second_order_offset_b"]
    assert off > 0, "the feedback must ADD early face, not remove it"
    dbar = CB["verdict"]["cash_rows"][0]["D"]
    assert dbar * (E + off) > dbar * E, "a naive sum understates the haircut"
    assert sched > 0 and E > sched


# --- prose spans ----------------------------------------------------------
@pytest.mark.parametrize("key", sorted(DANISH_IO_SHARE_SPANS))
def test_each_static_span_removal_fails(key):
    """Trace: TEX.replace(span, "") strips every occurrence, so the check's
    `lit not in tex_nc` fires and `missing` names this key."""
    span = DANISH_IO_SHARE_SPANS[key]
    assert span in TEX, f"vacuous mutation: span {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #120 survived removal of {key!r}")


@pytest.mark.parametrize("key", sorted(DERIVED))
def test_each_derived_span_removal_fails(key):
    """Same shape, for the literals the gate builds from the artifact.
    Trace for gap_at_sourced: the pin carries "after that feedback" because
    "$+\\$19.2$ billion" already exists at the moving-share bracket, so a
    bare-numeral pin would be ambiguous between two unrelated cells."""
    span = DERIVED[key]
    assert span in TEX, f"vacuous mutation: {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #120 survived removal of {key!r}")


def test_the_bib_entry_exists_in_the_bib_the_manuscript_resolves():
    """\\bibliography{references} sits in paper/v18/, so it resolves to
    paper/v18/references.bib -- not the stale paper/references.bib."""
    assert "\\citep{nationalbanken2020}" in TEX
    assert "@misc{nationalbanken2020," in BIB
    assert "{{Danmarks Nationalbank}}" in BIB
    assert "Expiring interest-only mortgages" in BIB


# --- derived literals must track the artifact -----------------------------
@pytest.mark.parametrize("path,delta", [
    (("break_even", "first_order"), 0.01),
    (("break_even", "second_order"), 0.01),
    (("parity", "P1_sched_total_b"), 1.0),
    (("parity", "P1_gap_par"), 1.0),
    (("parity", "P1_buyback_identity_E_b"), 1.0),
    (("parity", "P3_mean_danish_cpr_pct"), 0.5),
    (("at_sourced_share", "second_order_offset_b"), 1.0),
    (("at_sourced_share", "gap_second_order_b"), 1.0),
    (("at_sourced_share", "gap_first_order_b"), 1.0),
])
def test_each_derived_figure_drift_fails(path, delta):
    """Trace, by row: the two break-evens break their printed crossings and
    (for first_order) the be1*sched identity; sched and gap_par break the
    printed basis figure and the cell-by-cell chain; E and the mean CPR break
    the tie to the two artifacts this run did not write; the three
    at_sourced rows break their printed literals and the additivity
    identity."""
    io = copy.deepcopy(IO)
    node = io
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] += delta
    ok, _ = check(TEX, io=io)
    assert not ok, f"a drifted {'.'.join(path)} must fail against unmoved tex"


@pytest.mark.parametrize("key", [
    "institutional_gap_shared_b", "mean_danish_cpr_pct",
])
def test_danish_anchor_tie_mutations_fail(key):
    """gap_par and the 5.61% are anchored to danish_us_intercept, an artifact
    this run did not write. Trace: moving either breaks cross_artifact_tie."""
    dan = copy.deepcopy(DAN)
    dan["point"][key] = dan["point"][key] + 1.0
    ok, info = check(TEX, dan=dan)
    assert not ok and not info["cross_artifact_tie"]


@pytest.mark.parametrize("key", ["early_face_E_b", "gap_face_b"])
def test_committed_bracket_tie_mutations_fail(key):
    """The $470.7 billion of early face and the face gap belong to the
    committed bracket. Trace: moving either breaks cross_artifact_tie, and
    no printed literal has to move for the gate to notice."""
    cb = copy.deepcopy(CB)
    cb["verdict"][key] = 1.0
    ok, info = check(TEX, cb=cb)
    assert not ok and not info["cross_artifact_tie"]


def test_a_joint_cell_in_the_grid_fails():
    """(e) No joint cell is run and none may be quoted. Trace: adding a
    composed sigma to the grid makes the pinned set comparison fail, so
    artifact_ok goes False even though every printed literal survives."""
    io = copy.deepcopy(IO)
    io["cells"]["sigma_0.600000"] = dict(io["cells"]["sigma_0.500000"],
                                         io_share=0.60)
    ok, info = check(TEX, io=io)
    assert not ok and not info["grid_ok"] and not info["artifact_ok"]


def test_breaking_monotonicity_fails():
    """E2. Trace: raising the 50% cell above the 45% one breaks the strictly
    decreasing conjunct at both orders."""
    io = copy.deepcopy(IO)
    io["cells"]["sigma_0.500000"]["gap_first_order_b"] = 100.0
    io["cells"]["sigma_0.500000"]["gap_second_order_b"] = 110.0
    ok, info = check(TEX, io=io)
    assert not ok and not info["artifact_ok"]


def test_a_nonzero_offset_at_the_parity_anchor_fails():
    """E1. Trace: sigma = 0 must return gap_par exactly at BOTH orders, so a
    non-zero offset there means the feedback term is mis-wired."""
    io = copy.deepcopy(IO)
    io["cells"]["sigma_0.000000"]["second_order_offset_b"] = 0.5
    ok, info = check(TEX, io=io)
    assert not ok and not info["artifact_ok"]


def test_an_unsourced_artifact_may_not_support_the_printed_share():
    """Branch D lands the break-even alone. Trace: an artifact that failed
    P2 cannot back a manuscript that prints the 45%, so sourced=False turns
    the gate red while the crossing spans stay present."""
    io = copy.deepcopy(IO)
    io["source"]["sourced"] = False
    ok, info = check(TEX, io=io)
    assert not ok and not info["artifact_ok"]
    assert "crossing_first" not in info["missing"]


@pytest.mark.parametrize("key,value", [
    ("publication_date", "2021-02-04"),
    ("publisher", "Danmarks Nationalbanken"),
    ("verbatim", "about half of outstanding mortgage volumes"),
])
def test_source_provenance_mutations_fail(key, value):
    io = copy.deepcopy(IO)
    io["source"][key] = value
    ok, info = check(TEX, io=io)
    assert not ok and not info["artifact_ok"]


def test_dropping_a_limit_from_the_artifact_fails():
    """The three limits are the artifact's own, not this file's."""
    io = copy.deepcopy(IO)
    io["source"]["limits"] = io["source"]["limits"][:2]
    ok, info = check(TEX, io=io)
    assert not ok and not info["artifact_ok"]


def test_an_engine_run_or_a_wrong_window_fails():
    for key, value in (("no_engine_runs", False), ("window_months", 41)):
        io = copy.deepcopy(IO)
        io["spec"][key] = value
        ok, info = check(TEX, io=io)
        assert not ok and not info["artifact_ok"], key


# --- the arithmetic, re-derived here rather than read off the summary -----
def test_the_artifact_pins_the_inputs_it_read():
    """P0/P0b. Three sha pins over the microsim parquet and the two committed
    artifacts; if any has moved, the crossing is stale."""
    pins = IO["parity"]["P0_sha_pins"]
    assert len(pins) == 3
    for rel, pin in pins.items():
        p = ROOT / rel
        assert p.exists(), rel
        assert hashlib.sha256(p.read_bytes()).hexdigest() == pin, rel
    assert IO["parity"]["P0b_artifacts_byte_identical"] is True


def test_the_first_order_break_even_is_gap_par_over_sched():
    p = IO["parity"]
    assert abs(IO["break_even"]["first_order"] * p["P1_sched_total_b"]
               - p["P1_gap_par"]) < 1e-12


def test_the_chain_is_gap_par_minus_sigma_times_sched():
    p = IO["parity"]
    for k, c in IO["cells"].items():
        want = p["P1_gap_par"] - c["io_share"] * p["P1_sched_total_b"]
        assert abs(c["gap_first_order_b"] - want) < 1e-9, k


def test_the_second_order_is_reported_beside_the_first_never_folded_in():
    """P4: gap2 = gap1 + offset exactly, for every cell, so a reader can
    recover either order from the other."""
    assert IO["parity"]["P4_second_order_reported_separately"] is True
    for k, c in IO["cells"].items():
        assert abs(c["gap_second_order_b"]
                   - (c["gap_first_order_b"]
                      + c["second_order_offset_b"])) < 1e-12, k


def test_both_break_even_cells_return_zero_at_their_own_order():
    be = IO["break_even"]
    c1 = IO["cells"][f"sigma_{be['first_order']:.6f}"]
    c2 = IO["cells"][f"sigma_{be['second_order']:.6f}"]
    assert abs(c1["gap_first_order_b"]) < 1e-9
    assert abs(c2["gap_second_order_b"]) < 1e-9
    assert c1["gap_second_order_b"] > 0, "the offset must RAISE the bar"


def test_the_offset_only_raises_the_bar_and_the_import_clears_both():
    be, s45 = IO["break_even"], IO["at_sourced_share"]
    assert be["first_order"] < be["second_order"] < s45["io_share"]
    assert s45["gap_first_order_b"] < 0 and s45["gap_second_order_b"] < 0
    assert s45["reverses"] is True


def test_the_expectations_the_spec_fixed_before_the_run():
    e = IO["expectations"]
    for k in ("E1_anchor_exact", "E2_monotone_both_orders", "E3_pass",
              "E4_sourced_share_reverses_under_face_accounting"):
        assert e[k] is True, k
    lo, hi = e["E3_band"]
    assert lo < e["E3_sigma_star_second_order"] <= hi
    assert e["E3_sigma_star_second_order"] == IO["break_even"]["second_order"]


def test_the_io_share_is_carried_on_the_danish_leg_only():
    """C-74's defect, named in the artifact: a share scored in BOTH legs
    contributes exactly zero."""
    assert "Danish leg only" in IO["spec"]["danish_leg_only"]
    assert "neutralize it" in IO["spec"]["danish_leg_only"]
    assert "U.S. leg's scheduled path" in IO["spec"]["basis_note"]


def test_the_two_variants_carry_the_same_paragraphs():
    for span in (DERIVED["crossing_first"], DERIVED["sourced_share"],
                 DANISH_IO_SHARE_SPANS["face_scope"],
                 DANISH_IO_SHARE_SPANS["no_joint_cell"]):
        assert TEX.count(span) == VARIANT.count(span) == 1, span
    assert TEX.count(SOURCED_LIT) == VARIANT.count(SOURCED_LIT) == 1
    assert len(TEX.split("\n")) == len(VARIANT.split("\n"))


def test_the_landing_did_not_disturb_the_neighbouring_pins():
    """Gate #117's unique face-accounting pin and gate #66's completeness
    count both sit in this neighbourhood with zero headroom."""
    pin = ("the gap stands at $+\\$61.2$ billion under the "
           "balance-adjustment reading")
    assert TEX.count(pin) == VARIANT.count(pin) == 1
    assert TEX.count("positive at every") == 6
    assert TEX.count("trade off sharply under face accounting") == 1
