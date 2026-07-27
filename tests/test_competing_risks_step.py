"""
Coverage for hazard/competing_risks.py — the monthly prepay-vs-default step
(audit: 0/1 mutants killed).

Nothing in the suite reached this module's own arithmetic. The existing
end-to-end test (tests/test_marginal_identity.py) drives monthly_step but
asserts a beta1 = 0 IDENTITY, which is invariant to almost everything here: the
identity holds whether burnout accumulates correctly, whether scheduled
amortization is applied, whether exposure counts prepaid balance, and whether
the Danish branch routes to the right anchor — because those all cancel between
the central and null legs.

This file asserts the step's own conservation and accounting properties on
small hand-built pools, where every number can be recomputed in the test.

Run with: python3 -m pytest tests/test_competing_risks_step.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import polars as pl
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "hazard"))

os.environ.setdefault("FRED_API_KEY", "test-dummy-key")


def _pool(n=6, n_strata=2, balance=250_000.0, coupon=3.0, regime="US", seed=0):
    from agents import MicrosimPool

    df = pl.DataFrame({
        "loan_id": [f"L{i:04d}" for i in range(n)],
        "stratum_id": [f"s{i % n_strata}" for i in range(n)],
        "fico": [700.0 + 10 * (i % 3) for i in range(n)],
        "property_state": ["CA"] * n,
        "orig_ltv": [80.0 + (i % 2) for i in range(n)],
        "coupon": [coupon] * n,
        "orig_upb": [balance] * n,
        "balance": [balance] * n,
        "loan_age": [36] * n,
        "state": ["Current"] * n,
    })
    return MicrosimPool(df, regime=regime, rng=np.random.default_rng(seed))


# ---------------------------------------------------------------------------
# State taxonomy
# ---------------------------------------------------------------------------
def test_delinquent_codes_are_exactly_the_pipeline_states():
    """The delinquency pipeline is D30/D60/D90+/Forbearance. Current must NOT be
    in it (a Markov step would then be applied to performing loans) and the
    absorbing states must not be either (they would resurrect)."""
    from agents import STATE_TO_CODE
    from competing_risks import DELINQUENT_CODES

    expected = {STATE_TO_CODE[s] for s in ("D30", "D60", "D90+", "Forbearance")}
    assert DELINQUENT_CODES == expected
    for excluded in ("Current", "Prepaid", "Defaulted"):
        assert STATE_TO_CODE[excluded] not in DELINQUENT_CODES


# ---------------------------------------------------------------------------
# update_cohort_burnout_amounts
# ---------------------------------------------------------------------------
def test_burnout_accumulates_prepaid_over_stratum_original_upb():
    """burnout_s += prepaid_s / orig_upb_s, per stratum, from the ORIGINAL
    balance not the current one. Hand-computed on the right."""
    from competing_risks import update_cohort_burnout_amounts

    pool = _pool(n=4, n_strata=2, balance=100_000.0)
    idxs = np.arange(4)
    # strata alternate s0,s1,s0,s1 -> each has orig_upb 200,000
    amts = np.array([10_000.0, 0.0, 5_000.0, 20_000.0])
    update_cohort_burnout_amounts(pool, idxs, amts)

    s0 = pool._stratum_to_code["s0"]
    s1 = pool._stratum_to_code["s1"]
    assert pool.cohort_burnout[s0] == pytest.approx(15_000.0 / 200_000.0)
    assert pool.cohort_burnout[s1] == pytest.approx(20_000.0 / 200_000.0)


def test_burnout_is_cumulative_across_months():
    from competing_risks import update_cohort_burnout_amounts

    pool = _pool(n=2, n_strata=1, balance=100_000.0)
    idxs = np.arange(2)
    for _ in range(3):
        update_cohort_burnout_amounts(pool, idxs, np.array([1_000.0, 1_000.0]))
    # 3 months x $2,000 over $200,000 original
    assert pool.cohort_burnout[0] == pytest.approx(6_000.0 / 200_000.0)


def test_burnout_is_capped_at_one():
    """Burnout is a share; above 1.0 it would drive the hazard multiplier
    negative. The cap must bind and hold."""
    from competing_risks import update_cohort_burnout_amounts

    pool = _pool(n=2, n_strata=1, balance=100_000.0)
    for _ in range(5):
        update_cohort_burnout_amounts(
            pool, np.arange(2), np.array([90_000.0, 90_000.0])
        )
    assert pool.cohort_burnout[0] == 1.0


def test_burnout_does_not_leak_across_strata():
    """A stratum with zero prepayment must stay at zero. Dropping the
    per-stratum mask would smear one cohort's burnout over all of them."""
    from competing_risks import update_cohort_burnout_amounts

    pool = _pool(n=4, n_strata=2, balance=100_000.0)
    amts = np.array([50_000.0, 0.0, 50_000.0, 0.0])  # only s0 prepays
    update_cohort_burnout_amounts(pool, np.arange(4), amts)
    s0, s1 = pool._stratum_to_code["s0"], pool._stratum_to_code["s1"]
    assert pool.cohort_burnout[s0] > 0.0
    assert pool.cohort_burnout[s1] == 0.0


def test_burnout_ignores_zero_prepayment_and_zero_denominator():
    from competing_risks import update_cohort_burnout_amounts

    pool = _pool(n=2, n_strata=1, balance=100_000.0)
    update_cohort_burnout_amounts(pool, np.arange(2), np.zeros(2))
    assert pool.cohort_burnout[0] == 0.0

    pool.stratum_orig_upb[0] = 0.0  # degenerate stratum must not divide by zero
    update_cohort_burnout_amounts(pool, np.arange(2), np.array([1.0, 1.0]))
    assert pool.cohort_burnout[0] == 0.0


# ---------------------------------------------------------------------------
# monthly_step — accounting identities
# ---------------------------------------------------------------------------
def _trans():
    """Identity transition matrix: isolates the competing-risks arithmetic from
    the Markov delinquency pipeline."""
    import pandas as pd
    from config import MARKOV_STATES

    return pd.DataFrame(
        np.eye(len(MARKOV_STATES)), index=MARKOV_STATES, columns=MARKOV_STATES
    )


def test_fractional_prepay_equals_balance_times_normalized_hazard():
    """PREPAY_MODE == 'fractional': prepay_upb must be exactly the sum of
    balance * h_prep_n, recomputed here from the hazard functions directly."""
    from config import PREPAY_MODE
    from competing_risks import monthly_step
    from literature_hazard import (
        default_hazard, normalize_competing_hazards, prepay_hazard,
    )
    from rate_gap import compute_rate_gap, rate_stress

    assert PREPAY_MODE == "fractional"
    pool = _pool(n=6)
    market_rate = 0.07
    bal0 = pool.balance.copy()

    pool.broadcast_burnout()
    gap = compute_rate_gap(pool.regime, pool.coupon, market_rate,
                           pool.balance, pool.loan_age)
    h_prep = prepay_hazard(pool.loan_age, gap, pool.burnout,
                           pool.fico_z, pool.ltv_z)
    h_def = default_hazard(rate_stress(pool.coupon, market_rate),
                           pool.fico_z, pool.ltv_z)
    h_prep_n, _ = normalize_competing_hazards(h_prep, h_def)
    expected = float((bal0 * h_prep_n).sum())

    out = monthly_step(pool, market_rate, trans=_trans())
    assert out["prepay_upb"] == pytest.approx(expected, rel=1e-12)
    assert expected > 0.0


def test_step_uses_the_NORMALIZED_prepay_hazard_when_the_risks_compete():
    """On a realistic pool h_prepay + h_default < 1, so the normalization is
    the identity and dropping it changes nothing — which is exactly why the
    test above cannot see it. Force the constraint to bind: with h_prep = 0.8
    and h_def = 0.6 the normalized prepay hazard is 0.8/1.4, and using the RAW
    0.8 would prepay 40% more UPB than the competing-risks step permits."""
    import competing_risks as cr

    pool = _pool(n=4, balance=100_000.0)
    opening = float(pool.balance.sum())

    monkeypatch_prepay = lambda *a, **k: np.full(int(pool.active_mask.sum()), 0.8)
    monkeypatch_default = lambda *a, **k: np.full(int(pool.active_mask.sum()), 0.6)
    orig_p, orig_d = cr.prepay_hazard, cr.default_hazard
    cr.prepay_hazard, cr.default_hazard = monkeypatch_prepay, monkeypatch_default
    try:
        out = cr.monthly_step(pool, 0.07, trans=_trans())
    finally:
        cr.prepay_hazard, cr.default_hazard = orig_p, orig_d

    assert out["prepay_upb"] == pytest.approx(opening * (0.8 / 1.4), rel=1e-12)
    # and the raw-hazard value it must NOT be
    assert out["prepay_upb"] != pytest.approx(opening * 0.8, rel=1e-6)


def _forced_hazards(h_prep_val, h_def_val):
    """Context manager replacing the two hazard functions competing_risks
    imported, so the bound can be probed where it actually BINDS."""
    import contextlib

    import competing_risks as cr

    @contextlib.contextmanager
    def _cm(pool):
        n = int(pool.active_mask.sum())
        orig_p, orig_d = cr.prepay_hazard, cr.default_hazard
        cr.prepay_hazard = lambda *a, **k: np.full(n, h_prep_val)
        cr.default_hazard = lambda *a, **k: np.full(n, h_def_val)
        try:
            yield cr
        finally:
            cr.prepay_hazard, cr.default_hazard = orig_p, orig_d

    return _cm


def test_prepayment_can_never_exceed_the_balance_at_risk():
    """The normalization's purpose, stated as an invariant that holds on any
    pool: the month's prepayment is bounded by the month's opening balance.

    On realistic hazards this bound is slack by two orders of magnitude and
    nothing can violate it, which is why the plain sweep below fires under no
    defect at all. The second leg forces the bound to BIND — an unnormalized
    hazard of 5.0 would prepay five times the pool — so the invariant is
    exercised where it is actually load-bearing.
    """
    import competing_risks as cr

    for coupon, rate in ((3.0, 0.09), (12.0, 0.005), (6.0, 0.06)):
        pool = _pool(n=6, coupon=coupon)
        opening = float(pool.balance.sum())
        out = cr.monthly_step(pool, rate, trans=_trans())
        assert 0.0 <= out["prepay_upb"] <= opening
        assert np.all(pool.balance >= 0.0)

    # Forced-binding leg: raw hazard 5.0, competing default 0.6.
    pool = _pool(n=6, balance=100_000.0)
    opening = float(pool.balance.sum())
    with _forced_hazards(5.0, 0.6)(pool) as cr_mod:
        out = cr_mod.monthly_step(pool, 0.07, trans=_trans())
    assert out["prepay_upb"] <= opening
    assert out["prepay_upb"] == pytest.approx(opening * (5.0 / 5.6), rel=1e-12)
    assert np.all(pool.balance >= 0.0)


def test_default_hits_escalate_current_to_d30_and_delinquent_to_defaulted():
    """The step's own delinquency state machine, asserted on states.

    HOLE (adversarial mutation pass). Nothing in this file observed
    `pool.state_code` after a default hit: every assertion reads the returned
    aggregates, and `default_upb` is 0.0 by construction while `default_count`
    is just `len(default_idx)`. Deleting BOTH escalation branches outright, or
    sending delinquent loans to "Current" instead of "Defaulted", changed no
    reported number and the whole file still passed. Force every loan to
    default, then read the states.
    """
    from agents import CODE_TO_STATE, STATE_TO_CODE
    import competing_risks as cr

    # Half the pool starts Current, half already in the delinquency pipeline.
    pool = _pool(n=6, seed=11)
    for i in (3, 4, 5):
        pool.state_code[i] = STATE_TO_CODE["D60"]
    before = [CODE_TO_STATE[int(c)] for c in pool.state_code]
    assert before == ["Current"] * 3 + ["D60"] * 3

    # h_def = 1.0 makes `u < h_def_n` true for every draw, so every loan is a
    # default hit; h_prep = 0.0 keeps normalization from rescaling it away.
    with _forced_hazards(0.0, 1.0)(pool) as cr_mod:
        out = cr_mod.monthly_step(pool, 0.07, trans=_trans())

    assert out["default_count"] == 6
    after = [CODE_TO_STATE[int(c)] for c in pool.state_code]
    # Current escalates exactly one step, into the pipeline — not to Defaulted.
    assert after[:3] == ["D30"] * 3
    # Already-delinquent loans are absorbed.
    assert after[3:] == ["Defaulted"] * 3


def test_step_conserves_balance_prepay_plus_scheduled_plus_remaining():
    """Opening balance = prepaid + scheduled principal + closing balance.
    Any double-count or dropped term in the step breaks this exactly."""
    from competing_risks import monthly_step

    pool = _pool(n=8)
    opening = float(pool.balance.sum())
    out = monthly_step(pool, 0.07, trans=_trans())
    closing = float(pool.balance.sum())
    assert opening == pytest.approx(
        out["prepay_upb"] + out["sched_amt"] + closing, rel=1e-10
    )


def test_step_advances_loan_age_by_exactly_one_month():
    from competing_risks import monthly_step

    pool = _pool(n=5)
    before = pool.loan_age.copy()
    monthly_step(pool, 0.07, trans=_trans())
    assert np.array_equal(pool.loan_age, before + 1)


def test_settled_equals_prepay_upb():
    """Voluntary prepayments reach SOMA immediately — settled_b IS prepay_upb,
    with no lag and no scheduled principal folded in."""
    from competing_risks import monthly_step

    pool = _pool(n=5)
    out = monthly_step(pool, 0.07, trans=_trans())
    assert out["settled_b"] == out["prepay_upb"]
    assert out["settled_b"] != pytest.approx(
        out["prepay_upb"] + out["sched_amt"]
    )


def test_exposure_adds_prepaid_balance_back_to_the_closing_balance():
    """exposure is the balance at RISK this month = closing balance + prepaid.
    Dropping the `+ prepay_upb` would shrink the denominator of every CPR by
    exactly the numerator, biasing every reported prepayment rate upward."""
    from competing_risks import monthly_step

    pool = _pool(n=6)
    opening = float(pool.balance.sum())
    out = monthly_step(pool, 0.07, trans=_trans())
    closing = float(pool.balance.sum())

    assert out["prepay_upb"] > 0.0
    assert out["exposure"] == pytest.approx(closing + out["prepay_upb"], rel=1e-10)
    # equivalently: opening balance net of scheduled principal only
    assert out["exposure"] == pytest.approx(opening - out["sched_amt"], rel=1e-10)
    assert out["exposure"] > closing


def test_empty_pool_returns_a_zeroed_month_not_a_crash():
    """All-absorbed pool: every aggregate zero, exposure floored at 1 so
    downstream CPR divisions stay finite."""
    from agents import STATE_TO_CODE
    from competing_risks import monthly_step

    pool = _pool(n=4)
    pool.state_code[:] = STATE_TO_CODE["Prepaid"]
    pool._update_active_mask()
    out = monthly_step(pool, 0.07, trans=_trans())
    assert out["prepay_upb"] == 0.0
    assert out["sched_amt"] == 0.0
    assert out["prepay_count"] == 0 and out["default_count"] == 0
    assert out["exposure"] == 0.0


def test_exposure_is_floored_at_one_on_a_live_but_zero_balance_pool():
    """max(exposure, 1.0): a fully paid-down but still-active pool must not
    hand a zero denominator downstream."""
    from competing_risks import monthly_step

    pool = _pool(n=3)
    pool.balance[:] = 0.0
    out = monthly_step(pool, 0.07, trans=_trans())
    assert out["exposure"] == 1.0


def test_default_upb_is_reported_as_zero_by_construction():
    """Defaults move loans through the delinquency pipeline; they do not
    retire UPB in this step. A nonzero default_upb would double-count."""
    from competing_risks import monthly_step

    pool = _pool(n=6)
    out = monthly_step(pool, 0.07, trans=_trans())
    assert out["default_upb"] == 0.0


def test_balances_never_go_negative_under_an_extreme_rate_gap():
    """The `np.maximum(bal - prepay, 0.0)` guard, probed where it BINDS.

    A 12% coupon against a 0.5% market is 'extreme' in economic terms but the
    resulting monthly hazard is still far below 1, so the guard never engages
    and the assertion fires under no defect. The second leg drives the
    normalized prepay hazard to essentially 1.0, which is the only regime in
    which a dropped clamp produces a negative balance.
    """
    from competing_risks import monthly_step

    pool = _pool(n=6, coupon=12.0)
    monthly_step(pool, 0.005, trans=_trans())  # enormous refi incentive
    assert np.all(pool.balance >= 0.0)

    pool = _pool(n=6, balance=100_000.0)
    with _forced_hazards(1.0, 0.0)(pool) as cr_mod:
        out = cr_mod.monthly_step(pool, 0.07, trans=_trans())
    assert out["prepay_upb"] == pytest.approx(600_000.0, rel=1e-12)
    assert np.all(pool.balance >= 0.0)
    assert np.all(pool.balance == 0.0)  # fully retired, not overshot negative


def test_step_is_deterministic_under_a_fixed_seed_and_actually_draws():
    """Reproducibility, plus the thing reproducibility alone cannot state.

    Same-seed equality is satisfied trivially by a step that never touches the
    RNG at all — so on its own it fires under no defect, including one that
    replaces the default draw with a constant. Assert additionally that the
    pool's generator STATE advanced, which is exactly the property a dropped
    or short-circuited draw destroys, and that a different seed moves the
    stochastic (default) leg while leaving the deterministic (fractional
    prepay) leg bit-identical.
    """
    from competing_risks import monthly_step

    a = monthly_step(_pool(n=8, seed=3), 0.07, trans=_trans())
    b = monthly_step(_pool(n=8, seed=3), 0.07, trans=_trans())
    assert a == b

    pool = _pool(n=8, seed=3)
    before = pool.rng.bit_generator.state
    monthly_step(pool, 0.07, trans=_trans())
    assert pool.rng.bit_generator.state != before, "the step consumed no draws"

    # Fractional prepay is deterministic given the pool, so it must NOT move
    # with the seed; only the default draw may.
    c = monthly_step(_pool(n=8, seed=99), 0.07, trans=_trans())
    assert c["prepay_upb"] == pytest.approx(a["prepay_upb"], rel=1e-12)


def test_prepay_count_counts_only_the_loans_that_actually_prepaid():
    """prepay_count is a COUNT of positive prepayments, not the active
    headcount. On a pool where every loan prepays a little the two coincide,
    so the distinction only becomes visible when some loans cannot prepay."""
    from competing_risks import monthly_step

    pool = _pool(n=6)
    pool.balance[:3] = 0.0  # zero balance -> zero prepay amount
    out = monthly_step(pool, 0.07, trans=_trans())
    assert out["prepay_count"] == 3
    assert out["prepay_count"] < int(pool.n)

    full = _pool(n=6)
    out_full = monthly_step(full, 0.07, trans=_trans())
    assert out_full["prepay_count"] == 6


def test_burnout_from_one_month_is_broadcast_into_the_next_months_hazard():
    """The step must re-broadcast stratum burnout onto the per-loan vector at
    the TOP of each month. Dropping that call is invisible in a single step
    (burnout starts at zero either way) and silently freezes the burnout
    channel at zero for the whole simulation."""
    from competing_risks import monthly_step

    pool = _pool(n=6, n_strata=1)
    assert np.all(pool.burnout == 0.0)
    monthly_step(pool, 0.07, trans=_trans())
    assert np.all(pool.cohort_burnout > 0.0)
    after_month_1 = pool.cohort_burnout.copy()

    monthly_step(pool, 0.07, trans=_trans())
    # The broadcast runs at the TOP of month 2, so the per-loan vector must
    # carry month 1's cohort burnout exactly (month 2's own prepayment is
    # folded into cohort_burnout only afterwards).
    assert np.all(pool.burnout > 0.0)
    assert pool.burnout.max() == pytest.approx(after_month_1.max(), rel=1e-12)
    assert pool.cohort_burnout.max() > after_month_1.max()


# ---------------------------------------------------------------------------
# Rate-gap responsiveness — the sign the paper reports
# ---------------------------------------------------------------------------
def test_prepayment_falls_when_rates_rise_above_the_coupon():
    """Lock-in, in one line: same pool, higher market rate, less prepayment.
    A beta1 sign flip inverts this while leaving every conservation identity
    above intact."""
    from competing_risks import monthly_step

    low = monthly_step(_pool(n=8, coupon=6.0, seed=1), 0.03, trans=_trans())
    high = monthly_step(_pool(n=8, coupon=6.0, seed=1), 0.09, trans=_trans())
    assert low["prepay_upb"] > high["prepay_upb"]


def test_burnout_rises_after_a_step_that_prepaid():
    """The step must feed its own prepayment back into cohort burnout; if it
    did not, the hazard would never burn out over the simulation."""
    from competing_risks import monthly_step

    pool = _pool(n=6)
    assert np.all(pool.cohort_burnout == 0.0)
    out = monthly_step(pool, 0.07, trans=_trans())
    assert out["prepay_upb"] > 0.0
    assert np.all(pool.cohort_burnout > 0.0)


# ---------------------------------------------------------------------------
# Danish branch routing
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("regime", ["Danish", "DK", "danish", "dk"])
def test_danish_regime_labels_all_take_the_berger_branch(regime):
    """All four spellings must route to the Berger calibration. A regime label
    that silently falls through to the U.S. hazard would report the U.S.
    counterfactual as the Danish one."""
    from competing_risks import monthly_step

    us = monthly_step(_pool(n=8, coupon=3.0, regime="US", seed=5), 0.07,
                      trans=_trans())
    dk = monthly_step(_pool(n=8, coupon=3.0, regime=regime, seed=5), 0.07,
                      trans=_trans())
    assert dk["prepay_upb"] != pytest.approx(us["prepay_upb"], rel=1e-9)


def test_danish_branch_is_near_flat_in_the_rate_gap():
    """Berger's identified fact: under market-value payoff, moving does not
    respond to the coupon gap. The Danish leg's prepayment must be nearly
    unchanged across a 600bp swing, where the U.S. leg moves a lot."""
    from competing_risks import monthly_step

    dk_lo = monthly_step(_pool(n=8, coupon=6.0, regime="Danish", seed=2), 0.03,
                         trans=_trans())["prepay_upb"]
    dk_hi = monthly_step(_pool(n=8, coupon=6.0, regime="Danish", seed=2), 0.09,
                         trans=_trans())["prepay_upb"]
    us_lo = monthly_step(_pool(n=8, coupon=6.0, regime="US", seed=2), 0.03,
                         trans=_trans())["prepay_upb"]
    us_hi = monthly_step(_pool(n=8, coupon=6.0, regime="US", seed=2), 0.09,
                         trans=_trans())["prepay_upb"]

    dk_swing = abs(dk_hi - dk_lo) / dk_lo
    us_swing = abs(us_hi - us_lo) / us_lo
    assert dk_swing < 0.10
    assert us_swing > dk_swing


def test_danish_leg_is_a_MONTHLY_hazard_not_the_annual_cpr():
    """The Danish branch's LEVEL, recomputed here from berger_calibration.

    Everything else in this file about the Danish leg is directional (flat in
    the gap, different from the U.S. leg, moves with the anchor), and all of
    it survives feeding the ANNUAL CPR straight into the step as if it were a
    monthly hazard — a ~12x overstatement of the Danish counterfactual, which
    is the denominator of the institutional-gap comparison the paper reports.
    Only pinning the level catches it.
    """
    from common.berger_calibration import (
        _annual_to_monthly_cpr, danish_cpr_annual,
    )
    from competing_risks import monthly_step
    from literature_hazard import default_hazard, normalize_competing_hazards
    from rate_gap import rate_stress

    market_rate = 0.07
    pool = _pool(n=6, coupon=3.0, regime="Danish", seed=7)
    bal0 = pool.balance.copy()

    cpr_ann = danish_cpr_annual(
        pool.coupon, market_rate, pool.loan_age, regime="US",
        term_months=pool.term_months,
    )
    h_prep = _annual_to_monthly_cpr(cpr_ann)
    h_def = default_hazard(rate_stress(pool.coupon, market_rate),
                           pool.fico_z, pool.ltv_z)
    h_prep_n, _ = normalize_competing_hazards(h_prep, h_def)
    expected = float((bal0 * h_prep_n).sum())

    out = monthly_step(pool, market_rate, trans=_trans())
    assert out["prepay_upb"] == pytest.approx(expected, rel=1e-12)

    # and the annual figure it must NOT be: ~12x larger, same sign, same
    # flatness, so no directional test can separate them.
    annual_n, _ = normalize_competing_hazards(cpr_ann, h_def)
    wrong = float((bal0 * annual_n).sum())
    assert wrong > 5.0 * expected
    assert out["prepay_upb"] != pytest.approx(wrong, rel=1e-3)


def test_us_intercept_combines_move_and_refi_on_the_survival_scale():
    """1 - (1-move)(1-refi), not move + refi.

    At the production anchor the transplant refi channel is exactly 0, so the
    two rules agree identically and the difference is untestable. Sweeping the
    refi global (the documented refi_sweep.py path) makes the second-order
    term real, which is the regime in which the sweep's answers are read.
    """
    from common import berger_calibration as bc
    from common.berger_calibration import _annual_to_monthly_cpr
    from competing_risks import monthly_step
    from literature_hazard import (
        default_hazard, normalize_competing_hazards, prepay_hazard,
    )
    from rate_gap import rate_stress

    market_rate = 0.07
    bc.set_danish_moving_anchor("us_intercept")
    bc.set_us_transplant_refi(0.60)  # large enough that the cross term bites
    try:
        pool = _pool(n=6, coupon=3.0, regime="Danish", seed=11)
        bal0 = pool.balance.copy()
        pool_ref = _pool(n=6, coupon=3.0, regime="Danish", seed=11)
        pool_ref.broadcast_burnout()

        h_move = prepay_hazard(
            pool_ref.loan_age, np.zeros_like(pool_ref.coupon),
            pool_ref.burnout, pool_ref.fico_z, pool_ref.ltv_z,
        )
        h_refi = _annual_to_monthly_cpr(np.full(pool_ref.n, 0.60))
        survival = 1.0 - (1.0 - h_move) * (1.0 - h_refi)
        naive_sum = h_move + h_refi
        h_def = default_hazard(rate_stress(pool_ref.coupon, market_rate),
                               pool_ref.fico_z, pool_ref.ltv_z)

        want, _ = normalize_competing_hazards(survival, h_def)
        wrong, _ = normalize_competing_hazards(naive_sum, h_def)
        out = monthly_step(pool, market_rate, trans=_trans())

        assert float((bal0 * want).sum()) != pytest.approx(
            float((bal0 * wrong).sum()), rel=1e-6
        ), "fixture failed to separate the two combination rules"
        assert out["prepay_upb"] == pytest.approx(
            float((bal0 * want).sum()), rel=1e-12
        )
    finally:
        bc.set_us_transplant_refi(bc.US_TRANSPLANT_REFI_BEST_ESTIMATE)
        bc.set_danish_moving_anchor("dk_level")


def test_danish_us_intercept_anchor_changes_the_step(monkeypatch):
    """The two Danish moving anchors are different counterfactuals; if the step
    ignored the selector both would score identically and the manuscript's
    rule-only vs rule+country distinction would be vacuous."""
    from common import berger_calibration as bc
    from competing_risks import monthly_step

    bc.set_danish_moving_anchor("dk_level")
    try:
        dk_level = monthly_step(_pool(n=8, regime="Danish", seed=9), 0.07,
                                trans=_trans())["prepay_upb"]
        bc.set_danish_moving_anchor("us_intercept")
        us_intercept = monthly_step(_pool(n=8, regime="Danish", seed=9), 0.07,
                                    trans=_trans())["prepay_upb"]
    finally:
        bc.set_danish_moving_anchor("dk_level")
    assert dk_level != pytest.approx(us_intercept, rel=1e-9)


def test_us_intercept_anchor_switches_off_the_rate_gap_term(monkeypatch):
    """'Rule-only': Berger's flatness at the U.S. zero-gap intercept. The
    us_intercept leg must be flat in the market rate too — if the rate-gap term
    were still live it would inherit U.S. lock-in and stop being rule-only."""
    from common import berger_calibration as bc
    from competing_risks import monthly_step

    bc.set_danish_moving_anchor("us_intercept")
    try:
        lo = monthly_step(_pool(n=8, coupon=6.0, regime="Danish", seed=4), 0.03,
                          trans=_trans())["prepay_upb"]
        hi = monthly_step(_pool(n=8, coupon=6.0, regime="Danish", seed=4), 0.09,
                          trans=_trans())["prepay_upb"]
    finally:
        bc.set_danish_moving_anchor("dk_level")
    assert lo == pytest.approx(hi, rel=1e-9)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
