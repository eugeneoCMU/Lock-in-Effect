"""
Monthly competing-risks step: prepay vs default with hazard normalization.

Cohort burnout updated after stratum-level CPR aggregation (not per-loan).
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

from agents import CODE_TO_STATE, STATE_TO_CODE, MicrosimPool
from config import MARKOV_STATES, PREPAY_MODE, TERM_MONTHS
from literature_hazard import (
    BETA1_PREPAY_MID,
    default_hazard,
    normalize_competing_hazards,
    prepay_hazard,
)
from macro import scheduled_amortization_smm
from markov import load_transition_matrix
from rate_gap import compute_rate_gap, rate_stress


DELINQUENT_CODES = {
    STATE_TO_CODE["D30"],
    STATE_TO_CODE["D60"],
    STATE_TO_CODE["D90+"],
    STATE_TO_CODE["Forbearance"],
}


def _markov_step_delinquent(
    pool: MicrosimPool,
    trans: pd.DataFrame,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply delinquency transitions and return full-payoff indices and cash.

    Prepaid closes the remaining debt; default/liquidation transitions retain
    balances under the existing unresolved-credit convention. Returned cash is
    loan principal, with no new claim about security receipt timing.
    """
    T = trans.to_numpy()
    state_names = list(trans.index)
    name_to_code = {s: STATE_TO_CODE[s] for s in MARKOV_STATES if s in STATE_TO_CODE}

    mask = np.isin(pool.state_code, list(DELINQUENT_CODES)) & pool.active_mask
    idxs = np.where(mask)[0]
    if len(idxs) == 0:
        return np.array([], dtype=int), np.array([], dtype=float)

    payoff_idxs = []
    payoff_amounts = []
    for i in idxs:
        state_name = CODE_TO_STATE[int(pool.state_code[i])]
        if state_name not in trans.index:
            continue
        row = trans.loc[state_name].to_numpy()
        u = rng.uniform()
        cum = np.cumsum(row)
        if cum[-1] <= 0:
            continue
        cum = cum / cum[-1]
        j = min(int(np.searchsorted(cum, u)), len(state_names) - 1)
        new_state = state_names[j]
        pool.state_code[i] = name_to_code.get(new_state, pool.state_code[i])
        if new_state == "Prepaid":
            payoff_idxs.append(i)
            payoff_amounts.append(float(pool.balance[i]))
            pool.balance[i] = 0.0
    return np.asarray(payoff_idxs, dtype=int), np.asarray(payoff_amounts, dtype=float)


def update_cohort_burnout_amounts(
    pool: MicrosimPool,
    agent_idxs: np.ndarray,
    prepay_amts: np.ndarray,
) -> None:
    """Accumulate stratum burnout from fractional or full prepay UPB."""
    for s in range(pool.n_strata):
        in_stratum = pool.stratum_id_code[agent_idxs] == s
        prepaid_s = prepay_amts[in_stratum].sum()
        denom = pool.stratum_orig_upb[s]
        if denom > 0 and prepaid_s > 0:
            pool.cohort_burnout[s] = min(
                1.0,
                pool.cohort_burnout[s] + prepaid_s / denom,
            )


def monthly_step(
    pool: MicrosimPool,
    market_rate: float,
    trans: Optional[pd.DataFrame] = None,
    beta1: float = BETA1_PREPAY_MID,
    *, payment_state=None,prepayment_model=None,
) -> dict:
    """
    One monthly competing-risks step for all active agents.

    Returns month aggregates: prepay_upb, default_count, sched_amt, settled_b.
    Optional payment_state tracks separate principal components under an
    explicit scenario. It must be bound to this pool after initial weighting.
    """
    if prepayment_model is not None:
        from hazard.positive_gap_mixture import PositiveGapMixture
        from hazard.floor_clamped_mixture import FloorClampedMixture
        if not isinstance(prepayment_model,(PositiveGapMixture,FloorClampedMixture)) or pool.regime.upper()!='US':
            raise ValueError('Positive-gap mixture requires its explicit configuration and US regime')
    if trans is None:
        trans = load_transition_matrix()

    if payment_state is not None:
        payment_state.before_month(pool)

    pool.broadcast_burnout()
    active = pool.active_mask
    # Round-15 Q3 amendment: beta1 may be a per-loan vector (full pool
    # length, aligned to loan-sample row order) for group-ablation runs.
    # A constant vector is elementwise bit-identical to the scalar path;
    # marginal_decomposition.py gates G1/G2 prove exact reproduction of the
    # committed central and null artifacts before any variant is read.
    if isinstance(beta1, np.ndarray):
        beta1 = beta1[active]
    n_active = int(active.sum())
    if n_active == 0:
        if payment_state is not None:
            payment_state.after_exits(pool)
            payment_state.finish_month(pool)
        return {
            "prepay_upb": 0.0,
            "default_upb": 0.0,
            "sched_amt": 0.0,
            "settled_b": 0.0,
            "exposure": 0.0,
            "prepay_count": 0,
            "default_count": 0,
        }

    active_idx = np.where(active)[0]
    bal_active = pool.balance[active_idx]

    pool.rate_gap[active] = compute_rate_gap(
        pool.regime,
        pool.coupon[active],
        market_rate,
        pool.balance[active],
        pool.loan_age[active],
    )
    stress = rate_stress(pool.coupon[active], market_rate)

    if prepayment_model is not None:
        reference=prepay_hazard(pool.loan_age[active],np.zeros(n_active),
            pool.burnout[active],pool.fico_z[active],pool.ltv_z[active],beta1=0.)
        h_prep=prepayment_model.probability(reference,(market_rate-pool.coupon[active])*100.)
    elif pool.regime.upper() in ("DANISH", "DK"):
        # Berger et al. Danish counterfactual (§20): import the estimated
        # U.S.-transplant elasticities directly instead of the NPV-reset
        # heuristic. Same population, only the prepay hazard swaps. Two
        # moving-channel anchors (common.berger_calibration):
        #   dk_level     — Danish descriptive level: flat 3.2%/yr moving +
        #                  refi-in-place (≈0 under U.S. tax).
        #   us_intercept — rule-only transplant: Berger's flatness fact at
        #                  the U.S. zero-gap intercept (production U.S.
        #                  hazard with the rate-gap term switched off;
        #                  involuntary floor retained) + the same refi
        #                  channel.
        from common.berger_calibration import (
            _annual_to_monthly_cpr,
            danish_cpr_annual,
            danish_refi_in_place_cpr_annual,
            get_danish_moving_anchor,
        )
        if get_danish_moving_anchor() == "us_intercept":
            h_move = prepay_hazard(
                pool.loan_age[active],
                np.zeros_like(pool.rate_gap[active]),
                pool.burnout[active],
                pool.fico_z[active],
                pool.ltv_z[active],
                beta1=beta1,
            )
            refi_ann = danish_refi_in_place_cpr_annual(
                pool.coupon[active], market_rate, pool.loan_age[active],
                regime="US", term_months=pool.term_months,
            )
            h_refi = _annual_to_monthly_cpr(refi_ann)
            # competing risks on the survival scale
            h_prep = 1.0 - (1.0 - h_move) * (1.0 - h_refi)
        else:
            cpr_ann = danish_cpr_annual(
                pool.coupon[active], market_rate, pool.loan_age[active],
                regime="US", term_months=pool.term_months,
            )
            h_prep = _annual_to_monthly_cpr(cpr_ann)
    else:
        h_prep = prepay_hazard(
            pool.loan_age[active],
            pool.rate_gap[active],
            pool.burnout[active],
            pool.fico_z[active],
            pool.ltv_z[active],
            beta1=beta1,
        )
    h_def = default_hazard(stress, pool.fico_z[active], pool.ltv_z[active])
    h_prep_n, h_def_n = normalize_competing_hazards(h_prep, h_def)

    prepay_upb = 0.0
    prepay_count = 0
    default_count = 0
    prepaid_this_month = np.zeros(pool.n, dtype=bool)

    if PREPAY_MODE == "fractional":
        prepay_amts = bal_active * h_prep_n
        prepay_upb = float(prepay_amts.sum())
        pool.balance[active_idx] = np.maximum(bal_active - prepay_amts, 0.0)
        prepay_count = int(np.sum(prepay_amts > 0))
        prepaid_this_month[active_idx[prepay_amts > 0]] = True

        u = pool.rng.uniform(size=n_active)
        default_hits = u < h_def_n
        default_idx = active_idx[default_hits]
        default_count = int(len(default_idx))
        for i in default_idx:
            if pool.state_code[i] == STATE_TO_CODE["Current"]:
                pool.state_code[i] = STATE_TO_CODE["D30"]
            elif pool.state_code[i] in DELINQUENT_CODES:
                pool.state_code[i] = STATE_TO_CODE["Defaulted"]

        update_cohort_burnout_amounts(pool, active_idx, prepay_amts)
    else:
        u = pool.rng.uniform(size=n_active)
        prepay_hits = u < h_prep_n
        default_hits = (u >= h_prep_n) & (u < h_prep_n + h_def_n)

        prepay_idx = active_idx[prepay_hits]
        default_idx = active_idx[default_hits]

        prepay_upb = float(pool.balance[prepay_idx].sum()) if len(prepay_idx) else 0.0
        prepay_count = int(len(prepay_idx))
        prepaid_this_month[prepay_idx] = True
        default_count = int(len(default_idx))

        for i in prepay_idx:
            pool.state_code[i] = STATE_TO_CODE["Prepaid"]
            pool.balance[i] = 0.0

        for i in default_idx:
            if pool.state_code[i] == STATE_TO_CODE["Current"]:
                pool.state_code[i] = STATE_TO_CODE["D30"]
            elif pool.state_code[i] in DELINQUENT_CODES:
                pool.state_code[i] = STATE_TO_CODE["Defaulted"]

        if len(prepay_idx):
            prepaid_mask = np.zeros(pool.n, dtype=bool)
            prepaid_mask[prepay_idx] = True
            prepaid_bal = np.where(prepaid_mask, pool.balance, 0.0)
            for s in range(pool.n_strata):
                in_stratum = pool.stratum_id_code == s
                prepaid_s = prepaid_bal[in_stratum].sum()
                denom = pool.stratum_orig_upb[s]
                if denom > 0 and prepaid_s > 0:
                    pool.cohort_burnout[s] = min(
                        1.0,
                        pool.cohort_burnout[s] + prepaid_s / denom,
                    )

    payoff_idxs, payoff_amounts = _markov_step_delinquent(pool, trans, pool.rng)
    if len(payoff_idxs):
        prepay_upb += float(payoff_amounts.sum())
        prepaid_this_month[payoff_idxs[payoff_amounts > 0]] = True
        prepay_count = int(prepaid_this_month.sum())
        update_cohort_burnout_amounts(pool, payoff_idxs, payoff_amounts)

    if payment_state is not None:
        payment_state.after_exits(pool)

    sched_amt = 0.0
    pool._update_active_mask()
    still_active = pool.active_mask
    for i in np.where(still_active)[0]:
        if payment_state is None:
            smm = scheduled_amortization_smm(
                float(pool.coupon[i]), int(pool.loan_terms[i]), int(pool.loan_age[i])
            )
            principal = pool.balance[i] * smm
        else:
            principal = payment_state.scheduled_principal(pool,i)
        pool.balance[i] = max(pool.balance[i] - principal, 0.0)
        sched_amt += principal
        pool.loan_age[i] += 1

    if payment_state is not None:
        payment_state.finish_month(pool)

    pool._update_active_mask()

    # Legacy loan-principal cash field; security receipt timing needs a separate mapping.
    settled_b = prepay_upb

    default_upb = 0.0
    exposure = float(pool.balance[active].sum()) + prepay_upb

    return {
        "prepay_upb": prepay_upb,
        "default_upb": default_upb,
        "sched_amt": sched_amt,
        "settled_b": settled_b,
        "exposure": max(exposure, 1.0),
        "prepay_count": prepay_count,
        "default_count": default_count,
    }
