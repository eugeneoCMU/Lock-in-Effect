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
    opening_delinquent: Optional[np.ndarray] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """Apply Markov transitions to agents already in delinquency pipeline."""
    state_names = list(trans.columns)
    if (not trans.index.is_unique or not trans.columns.is_unique
            or set(trans.index) != set(MARKOV_STATES)
            or set(trans.columns) != set(MARKOV_STATES)):
        raise ValueError("Transition matrix must have unique, complete state labels")
    values = trans.to_numpy(dtype=float)
    if not np.all(np.isfinite(values) & (values >= 0)):
        raise ValueError("Transition probabilities must be finite and nonnegative")
    totals = values.sum(axis=1)
    if not np.all(np.isclose(totals, 1) | np.isclose(totals, 0)):
        raise ValueError("Transition rows must sum to one (or zero for legacy unsupported rows)")
    name_to_code = {s: STATE_TO_CODE[s] for s in MARKOV_STATES if s in STATE_TO_CODE}

    mask = np.isin(pool.state_code, list(DELINQUENT_CODES)) & pool.active_mask
    if opening_delinquent is not None:
        mask &= opening_delinquent
    idxs = np.where(mask)[0]
    if len(idxs) == 0:
        return np.array([], dtype=int), np.array([], dtype=float)

    paid_idxs, paid_amounts = [], []

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
            paid_idxs.append(i)
            paid_amounts.append(pool.balance[i])
            pool.balance[i] = 0.0
    return np.asarray(paid_idxs, dtype=int), np.asarray(paid_amounts, dtype=float)


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
) -> dict:
    """
    One monthly competing-risks step for all active agents.

    Returns month aggregates: prepay_upb, default_count, sched_amt, settled_b.
    """
    if trans is None:
        trans = load_transition_matrix()

    # Contractual maturity cash is scheduled principal, not voluntary payoff.
    mature = pool.active_mask & (pool.loan_age >= pool.loan_terms)
    maturity_cash = float(pool.balance[mature].sum())
    pool.balance[mature] = 0.0
    pool._update_active_mask()
    pool.broadcast_burnout()
    active = pool.active_mask.copy()
    opening_delinquent = active & np.isin(pool.state_code, list(DELINQUENT_CODES))
    # Round-15 Q3 amendment: beta1 may be a per-loan vector (full pool
    # length, aligned to loan-sample row order) for group-ablation runs.
    # A constant vector is elementwise bit-identical to the scalar path;
    # marginal_decomposition.py gates G1/G2 prove exact reproduction of the
    # committed central and null artifacts before any variant is read.
    if isinstance(beta1, np.ndarray):
        beta1 = beta1[active]
    n_active = int(active.sum())
    if n_active == 0:
        return {
            "prepay_upb": 0.0,
            "default_upb": 0.0,
            "sched_amt": maturity_cash,
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

    if pool.regime.upper() in ("DANISH", "DK"):
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
                regime="US", term_months=pool.loan_terms[active],
            )
            h_refi = _annual_to_monthly_cpr(refi_ann)
            # competing risks on the survival scale
            h_prep = 1.0 - (1.0 - h_move) * (1.0 - h_refi)
        else:
            cpr_ann = danish_cpr_annual(
                pool.coupon[active], market_rate, pool.loan_age[active],
                regime="US", term_months=pool.loan_terms[active],
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

    if PREPAY_MODE == "fractional":
        prepay_amts = bal_active * h_prep_n
        prepay_upb = float(prepay_amts.sum())
        pool.balance[active_idx] = np.maximum(bal_active - prepay_amts, 0.0)
        prepaid_indices = active_idx[prepay_amts > 0]

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
        prepaid_balances = pool.balance[prepay_idx].copy()

        prepay_upb = float(pool.balance[prepay_idx].sum()) if len(prepay_idx) else 0.0
        prepaid_indices = prepay_idx
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
            update_cohort_burnout_amounts(pool, prepay_idx, prepaid_balances)

    paid_idxs, paid_amounts = _markov_step_delinquent(pool, trans, pool.rng, opening_delinquent)
    prepay_upb += float(paid_amounts.sum())
    # A fractional payment and a subsequent Markov payoff are one borrower.
    prepay_count = int(len(np.union1d(prepaid_indices, paid_idxs)))
    update_cohort_burnout_amounts(pool, paid_idxs, paid_amounts)

    sched_amt = maturity_cash
    pool._update_active_mask()
    still_active = pool.active_mask
    for i in np.where(still_active)[0]:
        smm = scheduled_amortization_smm(
            float(pool.coupon[i]), int(pool.loan_terms[i]), int(pool.loan_age[i])
        )
        principal = pool.balance[i] * smm
        pool.balance[i] = max(pool.balance[i] - principal, 0.0)
        sched_amt += principal
        pool.loan_age[i] += 1

    pool._update_active_mask()

    # Voluntary prepayments reach SOMA immediately.
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
