"""Battery for gate #119 (R32 C-78: the episode gradient with loan age held fixed).

This exhibit's failure mode is asymmetric. The run returned a result the paper
wants (the point survives age standardization) and a result it does not (the
age-augmented interval covers the model-implied value, where the committed
interval excluded it). Only the second is at risk of quietly going away, so the
tests bind hardest there: the sentence must be undeletable, the numbers must be
the artifact's, and the gate must fail if the artifact ever stops supporting the
claim -- not merely if the string disappears.

Same convention as the #105/#107/#113/#114 batteries: mutations remove ALL
occurrences of a span, and every mutation is checked non-vacuous first.

MUTATION TRACES. Every mutating test below was hand-traced through
episode_age_bands_check on the mutated input before it was written, and the
named key is the one that actually goes missing. The gate is a conjunction over
8 spans and 10 derived literals plus the artifact block, so no surviving pin can
hold it green -- but the traces are recorded because "some other span still
satisfies it" is exactly the way a battery stops biting.

  * span removal, all 8 keys: tex.replace(span, "") drops the span's only
    occurrence and `missing == ["span:<k>"]`. Checked individually for the two
    gate-#75 spans, which share digits with new text: removing
    "$+4.20$ CPR points" does NOT disturb "puts $+0.38$ of the raw $+4.20$",
    and removing "$[+3.59, +4.66]$" does NOT disturb "$[+0.60, +4.35]$". Each
    bites on its own key alone.
  * coverage-clause removal: the clause is a substring of the single derived
    literal `age_ci_and_coverage`; deleting it leaves
    `missing == ["age_ci_and_coverage"]`. No other pin carries the coverage
    claim.
  * limb_a.ci95_pp -> [implied+0.01, hi]: lo prints "+0.95", so
    `age_ci_and_coverage` misses AND `covers` is False. Both halves fail.
  * committed limb_a.ci95_pp -> [implied-0.01, whi]: wlo prints "+0.93", so
    `age_ci_and_coverage` misses AND `excluded` is False.
  * limb_a.standardized_gradient_pp += 0.20 -> "+3.57": `age_point` misses.
    art_ok stays True (3.57 is still above the implied and the bar), so this
    proves the PRINTED number is bound independently of the property checks.
  * limb_a.imputed_weight_share += 0.05 -> "5.5": `age_ci_and_coverage` misses.
  * limb_b.age_only.between_composition_pp += 0.20 -> "+0.58", share "13.8":
    `age_only_and_share` AND `runindex_row` both miss.
  * limb_b.age_augmented_full.between_composition_pp += 0.20 -> "+1.05":
    `composition_moves` misses.
  * limb_a.ci95_pp widened to [lo-0.2, hi+0.2]: prints "+0.40"/"+4.55" so
    `age_ci_and_coverage` misses while `covers` stays True -- the literal binds
    even where the property does not move.
  * committed limb_a.standardized_gradient_pp += 0.20 -> "+3.64":
    `committed_point` misses. The manuscript's pre-existing $+3.44$ is derived
    by this gate from the COMMITTED artifact, so the two runs cannot drift
    apart in print.
  * runindex-row literal removed: `runindex_row` misses.
  * prose "(run \\texttt{episode\\_gradient\\_age\\_bands})" removed: `run_tag`
    falls to 1 < 2. `band_width` and `age_point` survive that deletion on their
    own, so run_tag is the ONLY reason the gate reddens -- which is the point of
    a two-site citation rule.
"""
import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from liveness_gates import (  # noqa: E402
    EPISODE_AGE_BANDS_SPANS,
    episode_age_bands_check,
)

TEX = (ROOT / "paper" / "v18" / "revised_paper_v18.tex").read_text()
VARIANT = (ROOT / "paper" / "v18"
           / "revised_paper_v18_long_abstract.tex").read_text()
A = json.loads((ROOT / "hazard" / "data"
                / "episode_gradient_age_bands_results.json").read_text())
W = json.loads((ROOT / "hazard" / "data"
                / "episode_confrontation_within_results.json").read_text())

IMPLIED = A["committed_reference"]["model_implied_pp"]
LO, HI = A["limb_a"]["ci95_pp"]
WLO, WHI = W["limb_a"]["ci95_pp"]
TOTAL = A["limb_b"]["full_cell_committed"]["total_pp"]
AGE_B = A["limb_b"]["age_only"]["between_composition_pp"]
TAG = "\\texttt{episode\\_gradient\\_age\\_bands}"
ROW_LIT = (f"seasoning composition at ${AGE_B:+.2f}$ of ${TOTAL:+.2f}$, and an "
           f"age-augmented interval that covers the model-implied "
           f"${IMPLIED:+.2f}$")


def test_gate_passes_on_the_manuscript():
    ok, info = episode_age_bands_check(TEX, A, W)
    assert ok, f"gate #119 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = episode_age_bands_check(VARIANT, A, W)
    assert ok, f"gate #119 fails on the long-abstract variant: {info}"


@pytest.mark.parametrize("key", sorted(EPISODE_AGE_BANDS_SPANS))
def test_each_span_removal_fails(key):
    """Trace: the span's only occurrence goes, so missing == ['span:<key>'].

    The gate ANDs every span with every derived literal, so nothing else can
    keep it green. Verified for the two gate-#75 spans specifically: neither
    removal disturbs the new text's own '$+4.20$' or '$[+0.60, +4.35]$'.
    """
    span = EPISODE_AGE_BANDS_SPANS[key]
    assert span in TEX, f"span {key!r} not in the manuscript (vacuous mutation)"
    ok, info = episode_age_bands_check(TEX.replace(span, ""), A, W)
    assert not ok, f"gate #119 survives removal of span {key!r}"
    assert f"span:{key}" in info["missing"], (
        f"removal of {key!r} reddened the gate for some OTHER reason "
        f"({info['missing']}) -- the test does not bite where it claims to")


def test_the_coverage_clause_is_undeletable():
    """The one sentence that costs this paper. It may not be trimmed away.

    Trace: the clause is a substring of the derived literal
    `age_ci_and_coverage`, so deleting it leaves missing == ['age_ci_and_coverage'].
    No other pin carries the coverage claim.
    """
    clause = f"covering the implied ${IMPLIED:+.2f}$ where the committed"
    assert clause in TEX, "vacuous mutation: the coverage clause is not printed"
    ok, info = episode_age_bands_check(TEX.replace(clause, ""), A, W)
    assert not ok, "the CI-coverage claim is not pinned"
    assert info["missing"] == ["age_ci_and_coverage"]


def test_gate_fails_if_the_interval_stops_covering_the_implied():
    """The gate binds the FINDING, not just the string.

    If a rerun moved the interval back above the implied value the printed
    sentence would be false. The gate must fail on the UNMOVED tex and force the
    sentence to change. Trace: lo prints '+0.95' so the literal misses, and
    covers becomes False so art_ok fails -- both halves.
    """
    a = copy.deepcopy(A)
    a["limb_a"]["ci95_pp"] = [IMPLIED + 0.01, HI]
    ok, info = episode_age_bands_check(TEX, a, W)
    assert not ok
    assert info["covers_implied"] is False
    assert "age_ci_and_coverage" in info["missing"]


def test_gate_fails_if_the_committed_interval_no_longer_excluded_it():
    """The contrast pair is live: it is read from the COMMITTED artifact.

    Trace: wlo prints '+0.93' so the literal misses, and excluded becomes False
    so art_ok fails.
    """
    w = copy.deepcopy(W)
    w["limb_a"]["ci95_pp"] = [IMPLIED - 0.01, WHI]
    ok, info = episode_age_bands_check(TEX, A, w)
    assert not ok
    assert info["committed_excluded"] is False
    assert "age_ci_and_coverage" in info["missing"]


@pytest.mark.parametrize("path,bump,key", [
    # each trace is in the module docstring; `key` is the literal that must go
    (("limb_a", "standardized_gradient_pp"), 0.20, "age_point"),
    (("limb_a", "imputed_weight_share"), 0.05, "age_ci_and_coverage"),
    (("limb_b", "age_only", "between_composition_pp"), 0.20, "age_only_and_share"),
    (("limb_b", "age_augmented_full", "between_composition_pp"), 0.20,
     "composition_moves"),
])
def test_each_printed_quantity_drift_fails(path, bump, key):
    a = copy.deepcopy(A)
    node = a
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] += bump
    ok, info = episode_age_bands_check(TEX, a, W)
    assert not ok, f"a drifted {'.'.join(path)} must fail against the unmoved tex"
    assert key in info["missing"], (
        f"drifting {'.'.join(path)} reddened the gate via {info['missing']}, "
        f"not via {key!r} -- the mutation does not bite where it claims to")


def test_a_widened_age_interval_fails_even_though_it_still_covers():
    """The printed literal binds where the coverage property does not move."""
    a = copy.deepcopy(A)
    a["limb_a"]["ci95_pp"] = [LO - 0.20, HI + 0.20]
    ok, info = episode_age_bands_check(TEX, a, W)
    assert not ok, "a drifted age interval must fail against the unmoved tex"
    assert info["covers_implied"] is True
    assert info["missing"] == ["age_ci_and_coverage"]


def test_the_committed_contrast_number_is_the_committed_runs():
    """$+3.44$ is printed from W, not written by hand.

    That sentence predates this landing. Gate #119 re-derives it from the
    committed artifact so the two runs cannot drift apart in print.
    """
    w = copy.deepcopy(W)
    w["limb_a"]["standardized_gradient_pp"] += 0.20
    ok, info = episode_age_bands_check(TEX, A, w)
    assert not ok
    assert "committed_point" in info["missing"]


def test_the_runindex_row_is_undeletable():
    assert ROW_LIT in TEX, "vacuous mutation: the runindex row is not present"
    ok, info = episode_age_bands_check(TEX.replace(ROW_LIT, ""), A, W)
    assert not ok
    assert "runindex_row" in info["missing"]


def test_the_run_tag_is_cited_at_both_sites():
    """Prose and tab:runindex. Dropping either citation reddens the gate.

    Trace: removing the prose citation leaves band_width and age_point intact,
    so run_tag is the only key that goes -- which is what makes the two-site
    rule real rather than decorative.
    """
    assert TEX.count(TAG) == 2
    assert VARIANT.count(TAG) == 2
    prose_cite = f"(run {TAG})"
    assert prose_cite in TEX, "vacuous mutation: the prose citation is absent"
    ok, info = episode_age_bands_check(TEX.replace(prose_cite, ""), A, W)
    assert not ok
    assert info["missing"] == ["run_tag"]


def test_the_age_interval_is_printed_at_exactly_one_site():
    """Branch A prints the age-augmented interval in the .tex:331 prose ONLY.

    tab:assembly is deliberately untouched by this landing, so a second printed
    site would mean the assembly row had been re-scoped without a signature.
    """
    lit = f"$[{LO:+.2f}, {HI:+.2f}]$"
    assert TEX.count(lit) == 1, f"{lit} should appear at exactly one site"
    assert VARIANT.count(lit) == 1


def test_the_assembly_row_and_the_sixth_qualification_are_untouched():
    """Spec section 7 Branch A: 'No new tab:assembly row'; section 8.2: the
    committed status line is preserved verbatim in every branch. Both sentences
    stay TRUE under this landing -- the assembly row prints the committed run's
    point and carries no interval, and the sixth qualification attributes its
    $+3.44$ to that same run -- so this landing scopes its own claim instead of
    editing theirs. Re-scoping either is Branch C's disposition and Eugene's
    signature.
    """
    for tex in (TEX, VARIANT):
        assert tex.count(
            "directional; not a marginal re-estimate "
            "(run \\texttt{episode\\_confrontation\\_within})") == 1
        assert tex.count(
            "the second survives composition standardization ($+3.44$ against "
            "the implied $+0.94$, run \\texttt{episode\\_confrontation\\_within})"
        ) == 1


def test_the_identity_telescopes_on_every_axis():
    """E2, STOP-class: asserted on every axis reported, not just the new one."""
    for name, v in A["limb_b"].items():
        assert abs(v["identity_residual"]) < 1e-12, f"{name} does not telescope"
        assert abs(v["total_pp"] - TOTAL) < 1e-12, f"{name} splits a different total"


def test_g6_reproduces_the_committed_decomposition_live():
    """The age axis is cut by the committed machinery, not a re-implementation."""
    g6 = A["parity_gates"]["G6_axis_machinery_reproduces_committed"]
    assert all(v["exact"] for v in g6.values())
    assert abs(g6["total_pp"]["got"] - W["limb_b"]["total_pp"]) < 1e-12
    assert abs(g6["between_composition_pp"]["got"]
               - W["limb_b"]["between_composition_pp"]) < 1e-12
    assert abs(g6["vintage_only"]["got"]
               - W["limb_b"]["between_by_axis"]["vintage_only"][
                   "between_composition_pp"]) < 1e-12


def test_g7_selection_ties_to_the_committed_run():
    sel, wsel = A["parity_gates"]["G7_selection_parity"], W["selection"]
    for k in ("n_strata_total", "n_strata_bucketed", "n_strata_primary",
              "n_rows_primary"):
        assert sel[k] == wsel[k], f"{k} drifted from the committed selection"


def test_e3_missed_and_the_miss_is_recorded_not_hidden():
    """A favourable miss is still a miss, and the manuscript names it.

    The prose hedge matches the measurement: 60.6% of shallow exposure DOES sit
    in single-band vintages, so the claim is 'not MERELY a relabelling'.
    """
    e = A["expectations"]
    assert e["E3_pass"] is False
    assert e["E3_measured"] < e["E3_collinearity_min"]
    for tex in (TEX, VARIANT):
        assert f"the realized share is ${e['E3_measured'] * 100:.1f}\\%$" in tex
        assert (f"at least ${e['E3_collinearity_min'] * 100:.0f}\\%$ of the "
                f"primary selection's shallow exposure") in tex
        assert "age is not merely a relabelling of vintage in this book" in tex


def test_e4_and_e5_are_the_flags_the_branch_was_scored_on():
    e = A["expectations"]
    assert e["E4_pass"] is True
    assert e["E4_age_only_between_pp"] < e["E4_bar_pp"]
    assert e["E5_standardized_above_bar"] is True
    assert A["limb_a"]["standardized_gradient_pp"] > e["E4_bar_pp"]
    assert A["branch_landed"] == "A"


def test_no_widening_is_claimed_anywhere():
    """The percentile interval NARROWS while shifting down.

    An earlier draft printed 'noisier' beside it; the word was cut because the
    only inferential object printed at that site is the interval, and it got
    narrower. The se rise is still asserted by the gate, but purely as a drift
    tripwire -- no printed word depends on it, and this test exists so a later
    editor cannot 'fix' the prose into a widening or noise claim.
    """
    assert (HI - LO) < (WHI - WLO), "the interval narrowed; do not claim widening"
    assert LO < WLO, "the interval's lower end is what fell"
    assert A["limb_a"]["se_pp"] > W["limb_a"]["se_pp"]
    for tex in (TEX, VARIANT):
        assert "noisier" not in tex


@pytest.mark.parametrize("lit", [
    "$+4.20$ CPR points",
    "$[+3.59, +4.66]$",
    "$+0.94$ points at the central",
    "unusable as a measurement of its size",
    "monthly-timing nulls above stand unchanged",
])
def test_gate_75_raw_literals_survive_this_landing(lit):
    """C-78 EXTENDS gate #75; the raw exhibit stays raw under it.

    The first two are ALSO pinned in EPISODE_AGE_BANDS_SPANS. That double-pin is
    deliberate and recorded in TECHNICAL and the R32 ledger: a legitimate future
    change to the raw numbers fails two gates, not one.
    """
    assert lit in TEX, f"gate #75 literal {lit!r} lost from the manuscript"
    assert lit in VARIANT, f"gate #75 literal {lit!r} lost from the variant"


def test_both_readings_are_present_not_just_the_favourable_one():
    """The point-survives reading and the interval-covers reading must co-occur."""
    for tex in (TEX, VARIANT):
        assert EPISODE_AGE_BANDS_SPANS["point_survives_interval_does_not"] in tex
        assert EPISODE_AGE_BANDS_SPANS["branch_reclassified"] in tex
        assert EPISODE_AGE_BANDS_SPANS["no_longer_separated"] in tex


def test_the_within_stratum_limit_is_still_declared():
    """Adding age changes nothing about the structural wall; the artifact says so."""
    assert "NOT COMPUTABLE" in A["spec"]["not_within_stratum"]


def test_the_age_cut_disclosure_is_the_artifacts():
    """Spec section 8.3 is stated in the PROSE, not delegated to the artifact.

    C-92 (the floor's flatness in loan age) is still open, so a reader must not
    be able to over-read this run as having tested where the cut sits.
    """
    assert A["spec"]["age_cut_held"] == 24
    assert A["spec"]["bands_cut_on_one_date"] is True
    for tex in (TEX, VARIANT):
        assert "The age cut itself is held at production" in tex
        assert EPISODE_AGE_BANDS_SPANS["age_cut_held_disclosed"] in tex
