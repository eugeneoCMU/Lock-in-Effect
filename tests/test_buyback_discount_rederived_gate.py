"""Battery for gate #117 (R32 C-75: the buyback discount, re-derived).

Three failure modes drive what these tests bind hardest on.

REVERSION. The superseded range was live at five .tex sites, and one of them
printed a HYPHENATED variant that gate #103's pinned substring never matched --
so a green suite was compatible with a retired figure sitting in the
conclusion. Absence is tested in both spellings, and the two independent
constants that pinned it (gate #103's span, gate #101's letter literal) are
checked to have been UPDATED, not half-updated and not deleted.

DRESSING UP A POINT AS A NARROWED RANGE. The committed 32--38% span was a range
only because the asserted grid had four points; nothing about its width was
ever estimated.

OUTRUNNING THE ARTIFACT. Two claims in the paragraph are not findings of this
run. The committed grid's no-prepayment provenance is "plausible but not
exactly reproduced" (spec SS2.3, SS6/P4), and D_crit is gap_par/E on the
committed chain, declared in the spec before the run so E4 could fail. Each
has its own hedge/ownership span and its own test that rewrites the clause
into the unhedged form and confirms the gate goes red.

Every mutation is verified non-vacuous before it is applied, and each carries
the trace of what the check returns on the mutated input.
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
    BUYBACK_BRACKET_SPANS,
    BUYBACK_DISCOUNT_SPANS,
    LETTER_CURRENT_LITERALS,
    buyback_discount_rederived_check,
)

TEX = (ROOT / "paper" / "final" / "paper_final_v1.tex").read_text()
VARIANT = (ROOT / "paper" / "final"
           / "paper_final_v1_long_abstract.tex").read_text()
LETTER = (ROOT / "paper" / "final"
          / "response_to_referees_round22.tex").read_text()
GATES_SRC = (ROOT / "tools" / "liveness_gates.py").read_text()
D = json.loads((ROOT / "hazard" / "data"
                / "buyback_discount_rederived_results.json").read_text())
CB = json.loads((ROOT / "hazard" / "data"
                 / "buyback_credit_bracket_results.json").read_text())
DAN = json.loads((ROOT / "hazard" / "data"
                  / "danish_us_intercept_results.json").read_text())

# runtime spellings (one backslash), i.e. what the .tex would carry
RETIRED = ("$-\\$89.4$ to $-\\$117.7$ billion",
           "$-\\$89.4$-to-$-\\$117.7$ billion")
# source spellings (two backslashes), i.e. what liveness_gates.py carries
RETIRED_SRC = ("$-\\\\$89.4$ to $-\\\\$117.7$ billion",
               "$-\\\\$89.4$-to-$-\\\\$117.7$ billion")
POINT = "$-\\$51.0$ billion"

DERIVED_SPANS = {
    "dbar": "face-weighted mean of 23.8\\%",
    "haircut": "\\$112.2 billion haircut",
    "gap_cash": "cash gap of $-\\$51.0$ billion",
    "monthly_range": "from 18.4\\% to 28.1\\%",
    "grid_span": "the committed 32--38\\% span was a range only by virtue of "
                 "a four-point asserted grid",
    "provenance": "returns 35.3\\% at zero prepayment on a 3.0\\% coupon "
                  "against a 6.8\\% market rate",
    "own_state": "the leg itself prepays at 5.61\\% against a window "
                 "averaging 6.61\\%",
    "d_crit": "the verdict turns at a 13.0\\% discount",
    "gap_face_unmoved": ("the gap stands at $+\\$61.2$ billion under the "
                         "balance-adjustment reading"),
}


def check(tex, d=None, cb=None, dan=None):
    return buyback_discount_rederived_check(tex, d or D, cb or CB, dan or DAN)


def test_gate_passes_on_the_manuscript():
    ok, info = check(TEX)
    assert ok, f"gate #117 fails on the shipped manuscript: {info}"


def test_variant_carries_it():
    ok, info = check(VARIANT)
    assert ok, f"gate #117 fails on the long-abstract variant: {info}"


# --- (a) the reversion this gate exists for -------------------------------
@pytest.mark.parametrize("lit", RETIRED)
def test_restoring_the_superseded_range_fails(lit):
    """Trace: replacing the one 'cash gap of $-\\$51.0$ billion' site with a
    retired spelling puts that spelling into tex_nc, so `retired` is
    non-empty; the same replacement also removes the derived 'gap_cash'
    literal, so `missing` names it. Both halves are asserted, so the test
    cannot be satisfied by the range check alone."""
    mutated = TEX.replace(DERIVED_SPANS["gap_cash"],
                          f"cash gap of {lit}", 1)
    assert mutated != TEX, "vacuous mutation"
    ok, info = check(mutated)
    assert not ok
    assert lit in info["retired_range_present"]
    assert "gap_cash" in info["missing"]


def test_no_gate_constant_still_pins_the_retired_range():
    """The half-landing guard, read off the CONSTANTS rather than the file
    text (gate #117 must itself carry the retired literal, in the tuple whose
    whole purpose is to check for its absence).

    Trace before this landing: BUYBACK_BRACKET_SPANS['reversal_range'] IS
    RETIRED[0], so the first assertion fails. Trace on a half-landing that
    updates gate #103 but not gate #101: the last assertion fails because the
    new figure is absent from LETTER_CURRENT_LITERALS. Trace on the reverse
    half-landing: the first assertion fails again. Only both updates pass."""
    for lit in RETIRED:
        assert lit not in BUYBACK_BRACKET_SPANS.values(), (
            f"gate #103 still pins the retired literal {lit!r}")
        assert lit not in LETTER_CURRENT_LITERALS, (
            f"gate #101 still pins the retired literal {lit!r}")
    assert POINT in BUYBACK_BRACKET_SPANS.values(), (
        "gate #103's reversal span was deleted rather than updated")
    assert POINT in LETTER_CURRENT_LITERALS, (
        "gate #101's letter literal was deleted rather than updated")


def test_the_retired_literal_survives_only_inside_its_own_absence_check():
    """Second half of the same guard, at file scope, so a NEW constant that
    re-pins the retired literal is caught too.

    Trace: after this landing each source spelling occurs exactly once in
    liveness_gates.py, inside buyback_discount_rederived_check's `retired`
    tuple. A surviving pin at gate #103 or gate #101 makes the space spelling
    occur twice and the count assertion fails; moving the tuple out of the
    check makes the containment assertion fail."""
    i = GATES_SRC.index("def buyback_discount_rederived_check")
    j = GATES_SRC.index("\ndef ", i + 1)
    own = GATES_SRC[i:j]
    for lit in RETIRED_SRC:
        assert GATES_SRC.count(lit) == 1, (
            f"{lit!r} is pinned somewhere other than gate #117's own "
            f"absence check ({GATES_SRC.count(lit)} occurrences)")
        assert own.count(lit) == 1, (
            f"gate #117's own absence check no longer carries {lit!r}")


def test_the_letter_and_the_manuscript_agree_on_the_new_figure():
    """Gate #101's drift rule in miniature: the response letter's current
    section quotes this figure, so it has to exist in the manuscript, and no
    spelling of the retired one may survive in that section.

    Trace: leaving the letter unedited keeps RETIRED[0] inside `current` and
    leaves POINT out of it, so both the third and the second assertion fail."""
    i = LETTER.find("\\section{Changes since this response was drafted}")
    assert i != -1
    current = LETTER[i:]
    assert POINT in current
    assert POINT in TEX
    for lit in RETIRED:
        assert lit not in current, "the letter's current section rotted"


@pytest.mark.parametrize("phrase", [
    "at the committed proxy discounts",
    "at the paper's own proxy discounts",
    "across the committed 32--38\\% discount grid",
])
def test_the_operative_proxy_phrasings_are_gone(phrase):
    """The four-point grid is now history, not the operative basis. Trace:
    each of these read as the basis the printed figure stands on; all three
    are also carried in ZERO_COUNT, so the gate suite fails independently."""
    assert phrase not in TEX and phrase not in VARIANT


# --- prose spans ----------------------------------------------------------
@pytest.mark.parametrize("key", sorted(BUYBACK_DISCOUNT_SPANS))
def test_each_static_span_removal_fails(key):
    """Trace: TEX.replace(span, "") strips EVERY occurrence, so the check's
    `lit not in tex_nc` fires and `missing` names this key. Verified
    non-vacuous first. Note two_grains is the long phrase, not the bare
    'two populations' -- the manuscript's unrelated 'two populations at two
    grains' (SS VI.B) survives the mutation and does NOT satisfy the span."""
    span = BUYBACK_DISCOUNT_SPANS[key]
    assert span in TEX, f"vacuous mutation: span {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #117 survived removal of {key!r}")


@pytest.mark.parametrize("key", sorted(DERIVED_SPANS))
def test_each_derived_span_removal_fails(key):
    """Same shape, for the literals the gate builds from the artifact rather
    than writing out. Trace for gap_face_unmoved: the phrase now carries its
    clause and occurs exactly once, so stripping it models the realistic
    single-site edit -- changing only the face-accounting sentence -- rather
    than a global search-and-replace of a 19-site bare literal."""
    span = DERIVED_SPANS[key]
    assert span in TEX, f"vacuous mutation: {key!r} not in manuscript"
    ok, info = check(TEX.replace(span, ""))
    assert not ok and key in info["missing"], (
        f"gate #117 survived removal of {key!r}")


def test_the_provenance_claim_may_not_be_upgraded_to_a_finding():
    """Spec SS2.3: the no-prepayment reading of the committed grid is
    "plausible but not exactly reproduced"; SS6/P4 makes it a non-targeting
    band check. Three non-matching values exist for that state (34.2%
    scoping, 36.5% as reported, 35.33% from the run), which is why it is
    hedged.

    Trace: rewriting the clause into the flat assertion deletes the span
    'consistent with a no-prepayment annuity priced at a representative
    state', so `missing` names no_prepay_provenance -- while the separate
    hedge sentence still stands, which is why the assertion names the key
    rather than relying on the gate being red for some other reason."""
    for bad in ("the grid priced a no-prepayment annuity",
                "the committed grid priced a no-prepayment annuity"):
        assert bad not in TEX and bad not in VARIANT
    mutated = TEX.replace(
        "The committed grid is consistent with a no-prepayment annuity "
        "priced at a representative state",
        "The committed grid priced a no-prepayment annuity at a "
        "representative state")
    assert mutated != TEX, "vacuous mutation"
    ok, info = check(mutated)
    assert not ok and "no_prepay_provenance" in info["missing"]


def test_the_threshold_may_not_be_credited_to_the_re_derivation():
    """Spec SS2.2 lists D_crit under "already known -- DECLARED, NOT
    PREDICTED"; the artifact's D_crit_note says it was stated before the run
    so E4 is falsifiable rather than retrofitted.

    Trace: replacing the ownership clause with "produced by the
    re-derivation" leaves the derived literal 'the verdict turns at a 13.0\\%
    discount' in place -- so the gate can only catch this through
    d_crit_ownership, and `missing` names exactly that key."""
    span = BUYBACK_DISCOUNT_SPANS["d_crit_ownership"]
    mutated = TEX.replace(span, "produced by the re-derivation")
    assert mutated != TEX, "vacuous mutation"
    assert DERIVED_SPANS["d_crit"] in mutated, "the trace requires it to stay"
    ok, info = check(mutated)
    assert not ok and "d_crit_ownership" in info["missing"]
    assert "before the run" in D["rederived"]["D_crit_note"]


# --- derived literals must track the artifact -----------------------------
@pytest.mark.parametrize("path,delta", [
    (("rederived", "face_weighted_mean_discount"), 0.01),
    (("rederived", "haircut_b"), 1.0),
    (("rederived", "gap_cash_b"), 1.0),
    (("rederived", "monthly_D_min"), 0.01),
    (("rederived", "monthly_D_max"), 0.01),
    (("rederived", "D_crit"), 0.01),
    (("parity", "P4_provenance_anchor", "discount"), 0.01),
    (("parity", "P5_mean_danish_cpr_pct"), 0.5),
    (("parity", "P5_market_rate_pct", "mean"), 0.5),
])
def test_each_derived_figure_drift_fails(path, delta):
    """Trace, by row: dbar/haircut/gap_cash/D_crit drifts break both the
    printed literal and an arithmetic identity; the two monthly bounds and
    the P4 anchor break only the literal (0.3533 + 0.01 is still inside
    [0.32, 0.38], so the band check still passes -- the literal is what
    bites); the two P5 drifts break the literal and the danish_us_intercept
    tie."""
    d = copy.deepcopy(D)
    node = d
    for k in path[:-1]:
        node = node[k]
    node[path[-1]] += delta
    ok, _ = check(TEX, d=d)
    assert not ok, f"a drifted {'.'.join(path)} must fail against unmoved tex"


def test_moving_gap_face_fails_because_it_is_an_identity():
    """Trace: gap_face_b = 55.0 makes the printed '$+\\$61.2$ billion' pin
    missing AND breaks the tie to both other artifacts."""
    d = copy.deepcopy(D)
    d["rederived"]["gap_face_b"] = 55.0
    ok, info = check(TEX, d=d)
    assert not ok
    assert "gap_face_unmoved" in info["missing"]
    assert not info["cross_artifact_tie"]


def test_a_month_at_the_committed_floor_fails():
    """E3 is the claim that the grid was too deep EVERYWHERE, not on average.
    Trace: months_at_or_above_committed_floor = 1 and one row's flag flipped
    make artifact_ok False by three separate conjuncts."""
    d = copy.deepcopy(D)
    d["rederived"]["months_at_or_above_committed_floor"] = 1
    d["months"][17]["below_committed_grid_floor"] = False
    ok, info = check(TEX, d=d)
    assert not ok and not info["artifact_ok"]


def test_a_shorter_grid_fails():
    """Trace: a three-point grid makes the gate demand 'a three-point
    asserted grid', which the manuscript does not carry, and breaks
    len(grid) == 4 and the row-for-row tie to the committed artifact."""
    d = copy.deepcopy(D)
    d["committed_bracket"]["D_GRID"] = [0.32, 0.34, 0.36]
    ok, info = check(TEX, d=d)
    assert not ok
    assert "grid_span" in info["missing"]
    assert not info["cross_artifact_tie"]


@pytest.mark.parametrize("key", ["gap_face_b", "early_face_E_b"])
def test_committed_bracket_tie_mutations_fail(key):
    """The committed constants are read from the run that owns them, not
    typed into the gate. Trace: moving either one breaks tie_ok, and no
    printed literal has to move for the gate to notice."""
    cb = copy.deepcopy(CB)
    cb["verdict"][key] = 1.0
    ok, info = check(TEX, cb=cb)
    assert not ok and not info["cross_artifact_tie"]


def test_committed_cash_rows_tie_mutation_fails():
    """Trace: the committed D = 0.32 row no longer equals the re-derived
    run's P3 reproduction of it, so the bit-identity claim fails."""
    cb = copy.deepcopy(CB)
    cb["verdict"]["cash_rows"][0]["gap_cash_b"] = -90.0
    ok, info = check(TEX, cb=cb)
    assert not ok and not info["cross_artifact_tie"]


@pytest.mark.parametrize("key", [
    "institutional_gap_shared_b", "us_trapped_shared_b",
    "danish_trapped_shared_b", "mean_danish_cpr_pct",
])
def test_danish_anchor_tie_mutations_fail(key):
    """The printed $+\\$61.2$ billion and 5.61\\% are anchored to
    danish_us_intercept, a third artifact this run did not write. Trace:
    moving any of the four breaks tie_ok."""
    dan = copy.deepcopy(DAN)
    dan["point"][key] = dan["point"][key] + 1.0
    ok, info = check(TEX, dan=dan)
    assert not ok and not info["cross_artifact_tie"]


def test_the_artifact_pins_the_machinery_still_in_the_repo():
    """P0. The run recorded sha256 over the amortization module, the
    committed bracket script and its three input artifacts; if any has moved
    since, the re-derivation is stale and the printed figures are not the
    ones the repo would now produce."""
    pins = D["parity"]["P0_sha_pins"]
    assert len(pins) == 5
    for rel, pin in pins.items():
        p = ROOT / rel
        assert p.exists(), rel
        assert hashlib.sha256(p.read_bytes()).hexdigest() == pin, rel


# --- the arithmetic, re-derived here rather than read off the summary -----
def test_the_chain_is_the_committed_one_with_only_D_changed():
    gap_par = D["parity"]["P2_committed_constants"]["gap_par"]["got"]
    E = D["parity"]["P2_E_b"]
    dbar = D["rederived"]["face_weighted_mean_discount"]
    assert abs(D["rederived"]["gap_cash_b"] - (gap_par - dbar * E)) < 1e-9


def test_d_crit_is_gap_par_over_E_and_is_not_this_run_s_output():
    gap_par = D["parity"]["P2_committed_constants"]["gap_par"]["got"]
    assert abs(D["rederived"]["D_crit"]
               - gap_par / D["parity"]["P2_E_b"]) < 1e-12
    assert "before the run" in D["rederived"]["D_crit_note"]


def test_dbar_is_the_face_weighted_mean_of_the_monthly_discounts():
    E = D["parity"]["P2_E_b"]
    got = sum(m["discount_D"] * m["early_face_b"] for m in D["months"]) / E
    assert abs(got - D["rederived"]["face_weighted_mean_discount"]) < 1e-12
    assert abs(D["rederived"]["haircut_b"] / E
               - D["rederived"]["face_weighted_mean_discount"]) < 1e-12


def test_E1_the_monthly_decomposition_telescopes():
    E = D["parity"]["P2_E_b"]
    assert len(D["months"]) == D["spec"]["window_months"] == 42
    assert abs(sum(m["early_face_b"] for m in D["months"]) - E) < 1e-9
    assert min(m["early_face_b"] for m in D["months"]) > 0


def test_every_month_prices_below_the_committed_floor():
    floor = D["committed_bracket"]["D_GRID"][0]
    assert max(m["discount_D"] for m in D["months"]) < floor
    assert D["rederived"]["months_at_or_above_committed_floor"] == 0


def test_P3_the_committed_chain_still_reproduces_bit_identically():
    for k, v in D["parity"]["P3_chain_bit_identical"].items():
        assert v["exact"] is True and v["got"] == v["committed"], k


def test_P4_is_a_band_check_at_the_zero_prepayment_state():
    a = D["parity"]["P4_provenance_anchor"]
    lo, hi = a["committed_grid_span"]
    assert lo < a["discount"] < hi
    assert a["state"]["cpr"] == 0.0, "the anchor is the NO-prepay state"


def test_the_verdict_is_smaller_but_still_reverses():
    gc = D["rederived"]["gap_cash_b"]
    near_edge = D["committed_bracket"]["gap_cash_range_b"][1]
    assert D["rederived"]["verdict_code"] == "REVERSES"
    assert gc < 0 and abs(gc) < abs(near_edge)
    assert D["rederived"]["D_crit"] < min(m["discount_D"] for m in D["months"])


def test_no_engine_run_and_the_import_was_binding_only():
    assert D["spec"]["no_engine_runs"] is True
    assert D["parity"]["P0a_wal_table_import_safe"] is True
    assert D["parity"]["P0b_artifacts_byte_identical_after_import"] is True


def test_the_two_grain_seam_is_the_artifact_s_own_disclosure():
    assert "two populations" in D["spec"]["grain_note"]
    assert "2.49% WAC" in D["spec"]["method"]
    assert D["committed_bracket"]["provenance"].startswith(
        "asserted, never derived")


def test_all_five_expectations_hold():
    e = D["expectations"]
    for k in ("E1_monthly_face_positive_and_telescopes", "E2_pv_monotone",
              "E3_every_month_below_committed_grid_floor", "E4_pass",
              "E5_reverses_and_smaller"):
        assert e[k] is True, k
    lo, hi = e["E4_band"]
    assert lo <= e["E4_dbar"] < hi


def test_the_two_variants_carry_the_same_paragraph():
    span = BUYBACK_DISCOUNT_SPANS["prepay_consistent"]
    assert TEX.count(span) == VARIANT.count(span) == 1
    assert TEX.count(POINT) == 5
    assert VARIANT.count(POINT) == 5
    assert len(TEX.split("\n")) == len(VARIANT.split("\n"))
