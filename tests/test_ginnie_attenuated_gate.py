"""Battery for gate #116 (R32 C-74: the Ginnie share's gap response, bracketed).

This exhibit's failure mode is an overclaim, in two directions, so the tests bind
hardest on the two honesty constraints rather than on the cells:

(a) the rise above the committed 0.797x scaling is FORCED for any positive
    response -- the share contributes exactly zero marginal under the committed
    overlay -- so it is arithmetic and not evidence, and the sentence saying so
    must be undeletable AND must come before the bracket verdict, not after it;
(b) a LEVEL differential does not identify a SLOPE, so the bracket is the result
    and no single cell may be quoted as the measured Ginnie marginal.

Same convention as the #107/#113/#114 batteries: every mutation is verified
non-vacuous before it is applied, and the artifact-side properties are re-derived
here rather than read off the run's own summary flags.

EVERY mutating test below carries a hand-trace of what the shipped check returns
on the mutated input, because a removal test that leaves some other pinned span
satisfying the gate does not bite.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    GINNIE_ATTENUATED_FILE_SPANS,
    GINNIE_ATTENUATED_SPANS,
    ginnie_attenuated_check,
)

# V20 closing-session rescope: app:ledger/app:verdicts live in the standalone
# replication_appendices.tex; the gated corpus is manuscript + that file.
TEX = ((ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
       + "\n" + (ROOT / "paper" / "final" / "replication_appendices.tex").read_text())
OPENER = "Pure conventional-share scaling is what a gap-inert Ginnie share gives."
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text() \
    + "\n" + (ROOT / "paper" / "final" / "replication_appendices.tex").read_text()  # V20 rescope
HAZ = ROOT / "hazard" / "data"
G = json.loads((HAZ / "ginnie_overlay_attenuated_results.json").read_text())
OV = json.loads((HAZ / "ginnie_cpr_overlay_results.json").read_text())
GOF = json.loads((HAZ / "ginnie_overlay_offwindow_results.json").read_text())

ORDER = ("M0_committed", "M2_primary_1_over_r", "M1_no_differential",
         "M3_amplification_r")
INS = [G["bracket_in_sample"][k]["marginal_pp"] for k in ORDER]
OFF = [G["bracket_off_window"][k]["marginal_pp"] for k in ORDER]
A = {k: G["bracket_in_sample"][k]["a"] for k in ORDER}
R = G["measurement"]["speed_ratio_r_freddie"]
MFULL = G["measurement"]["m_full_in_sample_pp"]
CONV_OFF = GOF["conventional_offwindow"]["marginal_pp"]
TAG = "\\texttt{ginnie\\_overlay\\_attenuated}"
ALL_SPANS = {**GINNIE_ATTENUATED_SPANS, **GINNIE_ATTENUATED_FILE_SPANS}


def _seq(v):
    return f"${v[0]:+.1f}$, ${v[1]:+.1f}$, ${v[2]:+.1f}$ and ${v[3]:+.1f}$"


def _bracket_line(tex):
    """The one line the gate reads: it carries the run tag and the 0.797 clause."""
    hits = [ln for ln in tex.split("\n") if TAG in ln and "0.797" in ln]
    assert len(hits) == 1, f"expected exactly one bracket line, got {len(hits)}"
    return hits[0]


def test_gate_passes_on_the_manuscript():
    ok, info = ginnie_attenuated_check(TEX, G, OV, GOF)
    assert ok, f"gate #116 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = ginnie_attenuated_check(VARIANT, G, OV, GOF)
    assert ok, f"gate #116 fails on the long-abstract variant: {info}"


@pytest.mark.parametrize("key", sorted(GINNIE_ATTENUATED_SPANS))
def test_each_line_pinned_span_removal_fails(key):
    """TRACE: each span occurs exactly once, inside the bracket sentence on the
    line that carries the run tag and 0.797. No span contains the tag or the
    string '0.797', so deleting one leaves len(lines) == 1 and the line is still
    found; the check then reports lits[key] False and returns ok False with
    missing == [key]. Nothing else in the file can satisfy it, because the span
    is looked up in `line`, not in the whole file."""
    span = GINNIE_ATTENUATED_SPANS[key]
    assert TEX.count(span) == 1, f"span {key!r} is not unique (vacuous mutation)"
    assert TAG not in span and "0.797" not in span, (
        f"span {key!r} would break the line-selection rule, not the span rule")
    ok, info = ginnie_attenuated_check(TEX.replace(span, ""), G, OV, GOF)
    assert not ok, f"gate #116 survives removal of span {key!r}"
    assert info["missing"] and key in info["missing"], (
        f"removal of {key!r} failed the gate for the wrong reason: {info}")


@pytest.mark.parametrize("key", sorted(GINNIE_ATTENUATED_SPANS))
def test_each_line_pinned_span_must_stay_on_the_bracket_line(key):
    """Relocating an honesty clause elsewhere in the file must not satisfy it.

    TRACE: the span is stripped from line 283 and re-appended as its own
    trailing line. The appended line carries neither the run tag nor '0.797', so
    the line-selection rule still returns exactly the (now shortened) line 283,
    and the span is absent from it. ok is False.

    File-scoped spans are deliberately excluded from this test -- they live at
    .tex:52 by design, and relocating them is not the failure this guards."""
    span = GINNIE_ATTENUATED_SPANS[key]
    moved = TEX.replace(span, "") + "\n" + span + "\n"
    ok, _ = ginnie_attenuated_check(moved, G, OV, GOF)
    assert not ok, f"span {key!r} is satisfied off the bracket's own line"


@pytest.mark.parametrize("key", sorted(GINNIE_ATTENUATED_FILE_SPANS))
def test_each_file_span_removal_fails(key):
    """The SS I cross-reference and its hedge.

    TRACE: both occur exactly once, at .tex:52, which carries neither the run
    tag nor '0.797'. Removing one therefore leaves the bracket line untouched
    (len(lines) == 1, every line-pinned span still present) and fails ONLY on
    the whole-file lookup -- so the assertion on missing below is what proves
    the bite is the intended one."""
    span = GINNIE_ATTENUATED_FILE_SPANS[key]
    assert TEX.count(span) == 1, f"span {key!r} is not unique (vacuous mutation)"
    ok, info = ginnie_attenuated_check(TEX.replace(span, ""), G, OV, GOF)
    assert not ok, f"gate #116 survives removal of file span {key!r}"
    assert info["missing"] == [key], (
        f"removal of {key!r} failed the gate for the wrong reason: {info}")


def test_the_assumability_link_precedes_its_hedge():
    """The cross-reference must sit immediately before 'ceilings, not sizes'.

    The spec's Branch A wording was 'so the carve-out is small', which this
    landing declined: nothing here sizes realized take-up (spec SS8.5), and that
    wording would contradict the next clause. The landed clause is only safe
    while the hedge follows it in the same sentence run."""
    i = TEX.find(GINNIE_ATTENUATED_FILE_SPANS["assumability_link"])
    j = TEX.find(GINNIE_ATTENUATED_FILE_SPANS["ceilings_not_sizes"])
    assert -1 < i < j, "the cross-reference must precede its hedge"
    assert j - i < 300, "the hedge drifted out of the clause it scopes"
    assert "the carve-out is small" not in TEX, (
        "the size claim the spec drafted was deliberately not landed")


@pytest.mark.parametrize("phrase", [
    "is arithmetic, not evidence",
    "none of the four is a measured Ginnie marginal",
])
def test_the_two_honesty_constraints_are_individually_pinned(phrase):
    """Named separately from the parametrized sweep: these are the constraints
    the spec makes non-negotiable, and a future refactor of the dict must not
    quietly drop either."""
    assert phrase in GINNIE_ATTENUATED_SPANS.values()
    assert TEX.count(phrase) == 1
    ok, _ = ginnie_attenuated_check(TEX.replace(phrase, ""), G, OV, GOF)
    assert not ok, f"{phrase!r} is not pinned"


@pytest.mark.parametrize("key", sorted(ALL_SPANS))
def test_every_pinned_span_occurs_exactly_once_in_both_variants(key):
    """A duplicated gate literal makes every removal test above vacuous."""
    span = ALL_SPANS[key]
    assert TEX.count(span) == 1, f"{key!r} occurs {TEX.count(span)}x in the canonical tex"
    assert VARIANT.count(span) == 1, f"{key!r} occurs {VARIANT.count(span)}x in the variant"


def test_the_run_tag_must_also_be_indexed():
    """TRACE, and this is the test the first draft got backwards.

    File order puts the PROSE citation at .tex:283 before the tab:runindex row
    at .tex:915, so removing the FIRST occurrence deletes the prose citation and
    fails on the len(lines) != 1 rule -- which proves nothing about the index.
    Removing the LAST occurrence leaves the bracket line intact (prose_lines 1,
    every span present) and trips run_tag_indexed alone. The assertion on
    missing is what makes this test bite the rule it names."""
    # V20 relocation: the prose citation moved WITH its paragraph to
    # Appendix app:params; V20 CLOSING RESCOPE: tab:runindex migrated to
    # replication_appendices.tex, which the gated corpus appends LAST, so
    # file order is now assembly row, prose, then the index row LAST.
    # Removing the LAST occurrence is what trips run_tag_indexed alone.
    assert TEX.count(TAG) == 3, "assembly + prose + tab:runindex expected"
    assert VARIANT.count(TAG) == 3
    i = TEX.rfind(TAG)
    mutated = TEX[:i] + TEX[i + len(TAG):]
    ok, info = ginnie_attenuated_check(mutated, G, OV, GOF)
    assert not ok, "the tab:runindex row is not required"
    assert info["prose_lines"] == 1 and info["missing"] == ["run_tag_indexed"], (
        f"the index rule is not what failed: {info}")


def test_removing_the_prose_citation_fails_on_the_prose_line_rule():
    """The complementary failure mode, documented so the two are not confused.

    TRACE (v20): the prose citation lives in Appendix app:params since the
    relocation; after the closing-session corpus rescope the runindex row
    (in replication_appendices.tex) sits LAST in the corpus, so the prose
    citation is the MIDDLE occurrence; removing it leaves no line carrying
    both the tag and '0.797', len(lines) == 0, and the check short-circuits
    with missing == ['prose_line']."""
    i = TEX.find(TAG, TEX.find(TAG) + 1)
    mutated = TEX[:i] + TEX[i + len(TAG):]
    ok, info = ginnie_attenuated_check(mutated, G, OV, GOF)
    assert not ok
    assert info["prose_lines"] == 0 and info["missing"] == ["prose_line"], info


@pytest.mark.parametrize("key", list(ORDER))
def test_each_in_sample_cell_drift_fails(key):
    """TRACE: +0.5pp moves every cell across a printed tenth (7.33->7.83,
    8.85->9.35, 9.20->9.70, 9.62->10.12), so the derived in_sample_sequence no
    longer matches the unmoved tex."""
    d = copy.deepcopy(G)
    d["bracket_in_sample"][key]["marginal_pp"] += 0.5
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, f"a drifted in-sample {key} must fail against the unmoved tex"


@pytest.mark.parametrize("key", list(ORDER))
def test_each_off_window_cell_drift_fails(key):
    """TRACE: +0.5pp moves every cell across a printed tenth (4.44->4.94,
    5.36->5.86, 5.57->6.07, 5.83->6.33), so the derived off_window_sequence no
    longer matches the unmoved tex."""
    d = copy.deepcopy(G)
    d["bracket_off_window"][key]["marginal_pp"] += 0.5
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, f"a drifted off-window {key} must fail against the unmoved tex"


def test_a_drifted_differential_or_ratio_fails():
    """TRACE: +0.10 takes 1.3541 -> 1.4541, printed '1.45' against the tex's
    '1.35'; +0.01 takes 1.22792 -> 1.23792, printed '1.238' against '1.228'.
    Both also break derived_ok against the recorded window means."""
    d = copy.deepcopy(G)
    d["measurement"]["crr_differential_ginnie_minus_freddie_pp"] += 0.10
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, "the printed 1.35 is not tied to the artifact"
    d = copy.deepcopy(G)
    d["measurement"]["speed_ratio_r_freddie"] += 0.01
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, "the printed 1.228 is not tied to the artifact"


def test_the_printed_sequences_are_the_artifact_rounded():
    assert _seq(INS) == "$+7.3$, $+8.9$, $+9.2$ and $+9.6$"
    assert _seq(OFF) == "$+4.4$, $+5.4$, $+5.6$ and $+5.8$"
    assert TEX.count(f"{_seq(INS)} points across those four") == 1
    assert TEX.count(_seq(OFF)) == 1


def test_the_printed_scaling_is_the_in_sample_ratio():
    """The prose compares a MULTIPLIER against a multiplier, not points against
    a multiplier, and the printed 0.797 is derived rather than typed.

    The in-sample scaling is 0.797226 -> '0.797'. The off-window scaling is
    0.797518, which would round to 0.798; the paper prints 0.797 at five sites
    and that pre-existing rendering is out of this landing's scope, so the gate
    derives the literal from the in-sample ratio and separately requires the two
    to agree to better than 5e-4 -- finer than the printed precision."""
    s_ins = INS[0] / MFULL
    s_off = OFF[0] / CONV_OFF
    assert f"{s_ins:.3f}" == "0.797"
    assert abs(s_off - GOF["marginal_scale_vs_conventional"]) < 1e-12
    assert abs(s_off - s_ins) < 5e-4
    assert TEX.count("rises above the committed $0.797\\times$ at every positive "
                     "response") == 1
    assert [round(x / MFULL, 4) for x in INS] == [0.7972, 0.9624, 1.0, 1.0462]


def test_the_a0_cell_is_the_committed_overlay_bit_for_bit():
    """P1, the parity anchor: a = 0 must BE the committed overlay, live.

    TRACE for the mutation: shifting the committed crr_only marginal by +0.5
    breaks anchor_ok (exact equality), so art_ok is False and the gate goes red
    even though the manuscript and the C-74 artifact are untouched."""
    assert INS[0] == OV["variants"]["crr_only"]["marginal_pp"]
    assert OFF[0] == GOF["overlay_offwindow"]["primary"]["marginal_pp"]
    assert (G["parity"]["P1_crr_only_marginal_b"]
            == OV["variants"]["crr_only"]["marginal_b"])
    d = copy.deepcopy(OV)
    d["variants"]["crr_only"]["marginal_pp"] += 0.5
    ok, _ = ginnie_attenuated_check(TEX, G, d, GOF)
    assert not ok, "the cross-artifact anchor is not live"


def test_the_identity_that_defines_the_fraction():
    """P3: a full response returns the un-overlaid marginal at BOTH calibrations.

    The off-window comparator is GOF['conventional_offwindow'], NOT a key under
    GOF['overlay_offwindow'] (which holds only primary/crr_only/gse_placebo).
    An earlier draft guarded that arm with a conditional that short-circuited to
    abs(0.0) and proved nothing; the real value is 5.57155818290974 and equals
    the a = 1 off-window cell exactly.

    TRACE for the mutation: +0.20 on one half of the P3 pair makes the pair
    differ by 0.20 against a pre-committed 0.05 tolerance, so identity_ok is
    False and the gate goes red."""
    tol = G["parity"]["P3_marginal_at_a1_vs_M_full"]["tol_pp"]
    assert tol == 0.05, "the tolerance was pre-committed at 0.05pp"
    assert abs(INS[2] - MFULL) <= tol
    assert OFF[2] == CONV_OFF
    assert abs(OFF[2] - CONV_OFF) <= tol
    d = copy.deepcopy(G)
    d["parity"]["P3_marginal_at_a1_vs_M_full"]["in_sample"][1] += 0.20
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, "a broken P3 identity must fail the gate"
    d = copy.deepcopy(GOF)
    d["conventional_offwindow"]["marginal_pp"] += 0.5
    ok, _ = ginnie_attenuated_check(TEX, G, OV, d)
    assert not ok, "the off-window arm of the identity is not live"


def test_the_rise_above_the_committed_cell_is_forced():
    """The claim the prose calls arithmetic, re-derived here.

    'FORCED' is in the artifact's KEY, not in its value; the value reads
    'the Ginnie share contributes EXACTLY ZERO marginal today, so for any a > 0
    the corrected marginal must exceed the committed 0.797x by arithmetic...'.
    An earlier draft asserted the wrong side of that pair and was a hard red."""
    assert all(x > INS[0] for x in INS[1:])
    assert all(x > OFF[0] for x in OFF[1:])
    assert INS == sorted(INS) and OFF == sorted(OFF)
    assert bool(G["expectations"]["E5_rise_is_forced_not_a_finding"])
    assert "rise_above_0797_is_FORCED" in G["honesty_constraints"]
    val = G["honesty_constraints"]["rise_above_0797_is_FORCED"]
    assert "EXACTLY ZERO" in val and "by arithmetic" in val


def test_the_bracket_is_the_result_not_a_cell():
    """The artifact must carry the level-does-not-identify-slope constraint."""
    hc = G["honesty_constraints"]["level_does_not_identify_slope"]
    assert "LEVEL" in hc and "SLOPE" in hc
    assert "the measured Ginnie marginal" in hc
    assert "full_universe_overstates" in G["honesty_constraints"]


def test_the_grid_is_zero_reciprocal_one_and_the_ratio():
    assert A["M0_committed"] == 0.0
    assert A["M1_no_differential"] == 1.0
    assert abs(A["M2_primary_1_over_r"] * R - 1.0) < 1e-9
    assert A["M3_amplification_r"] == R
    assert A["M2_primary_1_over_r"] < 1.0 < A["M3_amplification_r"], (
        "the bracket must straddle one: attenuation on one side, amplification "
        "on the other")
    d = copy.deepcopy(G)
    d["bracket_in_sample"]["M2_primary_1_over_r"]["a"] = 0.90
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, "a hard-coded grid point must fail a_grid_ok"


def test_the_grid_percentages_are_derived_not_typed():
    """The passage prints the grid as percentages of the conventional response.
    They must be the artifact's own fractions, formatted -- not round numbers."""
    a2, a1, a3 = (A["M2_primary_1_over_r"], A["M1_no_differential"],
                  A["M3_amplification_r"])
    assert f"${a2 * 100:.1f}$\\%" == "$81.4$\\%"
    assert f"${a1 * 100:.0f}$\\%" == "$100$\\%"
    assert f"${a3 * 100:.1f}$\\%" == "$122.8$\\%"
    line = _bracket_line(TEX)
    assert "$81.4$\\% of the conventional response" in line
    assert "$100$\\% (no differential)" in line
    assert "$122.8$\\% (proportional-hazard preservation" in line


def test_the_window_means_rederive_the_printed_differential_and_ratio():
    p = G["parity"]
    wm = p["P2_window_mean_crr_pct"]
    assert p["P2_window"] == ["2022-06", "2025-11"]
    assert p["P2_window_months"] == 42
    assert abs((wm["ginnie"] - wm["freddie"])
               - G["measurement"]["crr_differential_ginnie_minus_freddie_pp"]) < 1e-9
    assert abs(wm["ginnie"] / wm["freddie"] - R) < 1e-9
    assert f"{G['measurement']['crr_differential_ginnie_minus_freddie_pp']:.2f}" == "1.35"
    assert f"{R:.3f}" == "1.228"


def test_the_measurement_error_under_the_ratio_is_recorded():
    """P5: the ratio is not exact -- the extraction residual is ~1% of the
    differential it feeds, and the artifact must say so rather than presenting
    the ratio as exact."""
    res = G["parity"]["P5_series_extraction_residual_pp"]
    diff = G["measurement"]["crr_differential_ginnie_minus_freddie_pp"]
    worst = max(abs(v) for v in res.values())
    assert 0.0 < worst / diff < 0.05
    assert "NOT exact" in G["parity"]["P5_note"]


def test_the_comparator_choice_cannot_move_the_verdict():
    """P4: Freddie versus GSE-mean is a footnote, not a second bracket axis.

    TRACE for the mutation: 0.30 exceeds the pre-committed 0.05 tolerance, so
    art_ok is False."""
    p = G["parity"]
    assert abs(p["P4_comparator_shift_pp"]) < p["P4_tol_pp"]
    gse = G["bracket_in_sample_gse_comparator"]
    assert abs(gse["M2_primary_1_over_r"]["marginal_pp"] - INS[1]) < p["P4_tol_pp"]
    d = copy.deepcopy(G)
    d["parity"]["P4_comparator_shift_pp"] = 0.30
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, "a material comparator shift must fail the gate"


def test_no_engine_and_the_committed_artifacts_were_untouched():
    assert G["spec"]["no_engine_runs"] is True
    assert G["parity"]["P0b_artifacts_byte_identical"] is True
    assert "OUT OF SCOPE" in G["spec"]["engine_free"]
    assert "transplant" in G["spec"]["transplant_note"].lower()


def test_E3_held_but_is_not_advertised():
    """E3 passed, and the paper deliberately does not claim credit for it.

    Spec SS5 labels E3 a genuine prediction, but the construction is linear in
    the mapping fraction and spec SS3's DECLARED-NOT-PREDICTED table already
    fixes every input, so the realized cell is arithmetic on already-declared
    quantities. Quoting it as a prediction that held would be the overclaim
    SS2a exists to prevent. This test pins BOTH facts: the pass is real, and the
    band stays off the bracket line."""
    lo, hi = G["expectations"]["E3_band_pp"]
    assert (lo, hi) == (8.5, 9.2), "the band was pre-committed in the spec"
    assert lo <= G["expectations"]["E3_M2_in_sample_pp"] <= hi
    assert G["expectations"]["E3_M2_in_sample_pp"] == INS[1]
    assert G["expectations"]["E3_pass"] is True
    implied = INS[0] + A["M2_primary_1_over_r"] * (INS[2] - INS[0])
    assert implied == INS[1], (
        "E3's realized value is the linear interpolation of scoping-declared "
        "quantities; if that stops holding, the not-advertised decision must be "
        "revisited")
    # SCOPE FIX: _bracket_line returns the WHOLE of .tex:283, a ~5,900-char
    # paragraph that ALREADY contains "$+\\$38.5$ billion" and
    # "$\\$27.8 + \\$38.5 = \\$66.3$ billion" pre-edit -- both carry "8.5". An
    # absence check over the whole line is aimed at the wrong scope and fails on
    # the shipped manuscript. Scoped to the landed passage, where all three
    # literals are genuinely absent, so it still bites: adding "[8.5, 9.2]" or
    # "pre-committed band" to the bracket sentence turns it red.
    line = _bracket_line(TEX).split(OPENER)[-1]
    for lit in ("8.5", "pre-committed band", "prediction"):
        assert lit not in line, f"{lit!r} would advertise a forced result"


def test_the_two_honesty_clauses_must_stay_in_order():
    """Numbers, then the forced-rise disclaimer, then the bracket verdict.

    A rewrite that leads with the verdict and buries the disclaimer after it
    reads as a finding followed by a hedge. TRACE: the swap below leaves every
    span present and every artifact predicate true, so ONLY the ordering rule
    can catch it -- and the assertion on info['ordered'] proves that is what
    fired."""
    old = ("That the scaling rises above the committed $0.797\\times$ at every "
           "positive response is arithmetic, not evidence (a share contributing "
           "exactly zero must contribute more at any positive response), and I "
           "rest nothing on it. The bracket, not any cell in it, is the result: "
           "none of the four is a measured Ginnie marginal, and")
    new = ("The bracket, not any cell in it, is the result: none of the four is "
           "a measured Ginnie marginal. That the scaling rises above the "
           "committed $0.797\\times$ at every positive response is arithmetic, "
           "not evidence (a share contributing exactly zero must contribute "
           "more at any positive response), and I rest nothing on it, and")
    assert TEX.count(old) == 1, "the ordering mutation is vacuous"
    ok, info = ginnie_attenuated_check(TEX.replace(old, new), G, OV, GOF)
    assert not ok, "the clause order is not pinned"
    assert info["ordered"] is False and not info["missing"], (
        f"the order rule is not what failed: {info}")


@pytest.mark.parametrize("section,flag", [
    ("expectations", "E1_a0_reproduces_committed_overlay"),
    ("expectations", "E2_monotone_in_a"),
    ("expectations", "E5_rise_is_forced_not_a_finding"),
    ("parity", "P0b_artifacts_byte_identical"),
    ("spec", "no_engine_runs"),
])
def test_flags_are_load_bearing(section, flag):
    d = copy.deepcopy(G)
    d[section][flag] = False
    ok, _ = ginnie_attenuated_check(TEX, d, OV, GOF)
    assert not ok, f"{section}.{flag} must be load-bearing"
