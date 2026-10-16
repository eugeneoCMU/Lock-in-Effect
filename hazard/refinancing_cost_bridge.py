"""Explicit scenario bridge from new-loan cost ratios to incumbent-balance fees.

Let q = reported total loan costs / public rounded new loan amount and let
R = new loan amount / incumbent opening principal. The fee fraction consumed by
the refinancing solvers is k = q * R. Public HMDA does not identify the incumbent
balance or how fees were financed; the caller must select those assumptions.

This utility performs no acquisition, estimation, missing-value imputation, or
solver execution. Its outputs remain conditional cost scenarios.
"""

import math
from numbers import Integral, Real


def _finite_nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{name} must be an explicit finite numeric value")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be finite and nonnegative") from exc
    if not math.isfinite(result) or result < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return result


def bridge_cost_ratio(
    q, *, balance_rule, financing, new_to_existing_ratio=None, purpose_code,
):
    """Return a JSON-compatible record for one explicit fee-denominator scenario.

    ``q`` is a ratio, not a percent, with public rounded *new* loan amount in
    its denominator. ``cost_fraction`` instead uses existing opening principal.

    Supported balance rules:

    * ``supplied_balance_ratio`` requires a positive finite R and purpose 31 or
      32; k = q R. Either cash or financed settlement must be selected explicitly.
    * ``unchanged_balance`` assumes R = 1, cash settlement, and purpose 31.
    * ``all_fees_financed_no_other_balance_change`` assumes purpose 31, financed
      settlement, and q < 1. B_new = B_old + F yields R = 1/(1-q), k = q/(1-q).

    Purpose 31 means refinancing; purpose 32 means cash-out refinancing. Both
    identity rules reject a supplied R, including R = 1. All rules reject absent,
    nonnumeric, Boolean, nonfinite, or negative q; observed q = 0 is valid.

    The supplied-R rule only converts the fee denominator. It does not implement
    other changes to replacement debt or cash-out proceeds in a downstream solver.
    """
    q = _finite_nonnegative(q, "q")
    if (
        isinstance(purpose_code, bool)
        or not isinstance(purpose_code, Integral)
        or purpose_code not in (31, 32)
    ):
        raise ValueError("purpose_code must be the integer 31 or 32")
    purpose_code = int(purpose_code)
    if not isinstance(financing, str) or financing not in ("cash", "financed"):
        raise ValueError("financing must be explicitly cash or financed")
    rules = (
        "supplied_balance_ratio",
        "unchanged_balance",
        "all_fees_financed_no_other_balance_change",
    )
    if not isinstance(balance_rule, str) or balance_rule not in rules:
        raise ValueError("Unknown balance_rule")

    assumptions = [
        "The supplied ratio uses reported total loan costs divided by the public rounded new loan amount, without a rounding correction.",
        "Reported total loan costs are treated as the modeled fee; no missing or unreported cost components are imputed or added.",
        "The incumbent opening principal is not observed; the selected balance rule is a scenario assumption.",
        "Fee financing is not observed; the selected settlement method is a scenario assumption.",
    ]
    if balance_rule == "supplied_balance_ratio":
        ratio = _finite_nonnegative(new_to_existing_ratio, "new_to_existing_ratio")
        if ratio == 0:
            raise ValueError("new_to_existing_ratio must be positive")
        cost_fraction = q * ratio
        assumptions.append(
            "The caller-supplied new-to-existing balance ratio is assumed rather than inferred from public loan costs."
        )
    else:
        if new_to_existing_ratio is not None:
            raise ValueError("Identity balance rules do not accept a supplied balance ratio")
        if purpose_code != 31:
            raise ValueError("Identity balance rules require refinancing purpose 31")
        if balance_rule == "unchanged_balance":
            if financing != "cash":
                raise ValueError("unchanged_balance requires cash fee settlement")
            ratio = 1.0
            cost_fraction = q
            assumptions.append(
                "New loan principal equals incumbent opening principal, with no other balance change."
            )
        else:
            if financing != "financed":
                raise ValueError("The all-fees-financed identity requires financed settlement")
            if q >= 1:
                raise ValueError("The all-fees-financed identity requires q < 1")
            ratio = 1.0 / (1.0 - q)
            cost_fraction = q / (1.0 - q)
            assumptions.append(
                "All reported loan costs are financed, and new principal equals incumbent opening principal plus that fee, with no other balance change."
            )

    if not math.isfinite(ratio) or not math.isfinite(cost_fraction):
        raise ValueError("Computed balance ratio or cost fraction is not finite")
    if financing == "cash":
        assumptions.append(
            "The solver pays the modeled fee once in cash at refinancing, without adding it to replacement principal."
        )
    else:
        assumptions.append(
            "The solver adds the modeled fee once to replacement principal, with no simultaneous cash fee charge."
        )

    return {
        "cost_fraction": cost_fraction,
        "reported_cost_to_new_loan_ratio": q,
        "new_to_existing_ratio": ratio,
        "balance_rule": balance_rule,
        "financing": financing,
        "purpose_code": purpose_code,
        "evidence_class": "conditional_cost_scenario",
        "cost_component": "reported_loan_costs",
        "input_denominator": "public_rounded_new_loan_amount",
        "model_denominator": "existing_opening_principal",
        "incumbent_balance_observed": False,
        "fee_financing_observed": False,
        "assumptions": assumptions,
        "limitations": [
            "This conversion does not identify a borrower-specific refinancing cost or the complete economic cost of refinancing.",
            "Public loan-amount rounding is retained; the fee fraction is an approximate conditional proxy.",
            "The supplied balance ratio normalizes fees only; cash-out proceeds, paydowns, and other principal changes need separate modeling before a solver comparison.",
        ],
    }
