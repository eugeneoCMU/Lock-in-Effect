"""Pure ex-post descriptions of linked HARP predecessor/successor contracts.

This module does not infer refinancing offers, program eligibility, transaction
costs, cash-out, household equity, or welfare. It reads no files and creates no
predictor values from later observations.
"""

import math
from numbers import Real
import re


def _month_index(value, name):
    if value is None:
        return None
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}", value):
        raise ValueError(name + " must be YYYY-MM or None")
    year, month = int(value[:4]), int(value[5:])
    if year < 1 or not 1 <= month <= 12:
        raise ValueError(name + " must be a valid calendar month")
    return year * 12 + month - 1


def _number(value, name, *, integer=False):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(name + " must be a finite nonnegative number or None")
    try:
        number = float(value)
    except (OverflowError, TypeError, ValueError):
        raise ValueError(name + " must be a finite nonnegative number or None") from None
    if not math.isfinite(number) or number < 0 or (integer and not number.is_integer()):
        raise ValueError(name + " must be finite, nonnegative" + (" and integral" if integer else ""))
    return number


def _finite(value, name):
    if not math.isfinite(value):
        raise ValueError(name + " overflowed")
    return value


def _payment(principal, coupon_percent, months, name):
    if principal is None or coupon_percent is None or months is None or months <= 0:
        return None
    monthly_rate = coupon_percent / 1200.0
    factor = 1.0 / months if monthly_rate == 0 else monthly_rate / (
        -math.expm1(-months * math.log1p(monthly_rate))
    )
    return _finite(principal * factor, name)


def describe_linked_contract(
    *,
    event_label,
    event_month,
    prior_month,
    prior_upb,
    prior_coupon_percent,
    prior_remaining_months,
    successor_first_report_month,
    successor_origination_month,
    successor_original_upb_rounded,
    successor_original_coupon_percent,
    successor_original_term_months,
):
    """Describe one linked contract pair using explicitly supplied source fields.

    Months must be ``YYYY-MM`` strings or ``None``; coupon units are annual
    percentage points (``6.0`` means six percent). Present numeric inputs must
    be finite and nonnegative; month counts must also be integral. Zero terms
    are retained as source values but cannot define a term comparison or payment.

    ``chronology_accepted`` requires ``linked_harp_payoff``, known successor
    origination no later than the event, and no observed first report before
    origination. A missing first report yields no lag and does not invalidate
    those two known dates. First-report lag is relative to origination.

    Paired differences additionally require origination in the event month,
    a prior observation in the month immediately preceding the event, and the
    relevant two source values. Earlier origination remains an accepted link
    with a timing note but no paired differences. A stale prior observation
    is retained, never carried forward. Standalone
    payment proxies retain their source timing and require accepted chronology.
    All comparisons and payment proxies are suppressed for unaccepted links.

    The returned dictionary retains every source argument at top level. The
    balance proxy subtracts prior current UPB from rounded successor original
    UPB; this mixes observation times and rounding conventions. Payment proxies
    are standard fully amortizing monthly principal-and-interest calculations,
    excluding fees, taxes, insurance, payment modifications, and realized cash
    flows. They do not measure observed payments or lifetime welfare. Future
    successor terms remain ex-post descriptions, never historical offers or
    backfilled predictors. Missing source values and unknown fees remain None.
    """
    if event_label is not None and not isinstance(event_label, str):
        raise ValueError("event_label must be a string or None")
    source = dict(
        event_label=event_label,
        event_month=event_month,
        prior_month=prior_month,
        prior_upb=prior_upb,
        prior_coupon_percent=prior_coupon_percent,
        prior_remaining_months=prior_remaining_months,
        successor_first_report_month=successor_first_report_month,
        successor_origination_month=successor_origination_month,
        successor_original_upb_rounded=successor_original_upb_rounded,
        successor_original_coupon_percent=successor_original_coupon_percent,
        successor_original_term_months=successor_original_term_months,
    )
    event = _month_index(event_month, "event_month")
    prior = _month_index(prior_month, "prior_month")
    first = _month_index(successor_first_report_month, "successor_first_report_month")
    origination = _month_index(successor_origination_month, "successor_origination_month")
    old_upb = _number(prior_upb, "prior_upb")
    old_coupon = _number(prior_coupon_percent, "prior_coupon_percent")
    old_term = _number(prior_remaining_months, "prior_remaining_months", integer=True)
    new_upb = _number(successor_original_upb_rounded, "successor_original_upb_rounded")
    new_coupon = _number(successor_original_coupon_percent, "successor_original_coupon_percent")
    new_term = _number(successor_original_term_months, "successor_original_term_months", integer=True)

    problems = []
    if event_label != "linked_harp_payoff":
        problems.append("event_label_not_accepted_link")
    if event is None or origination is None:
        problems.append("event_or_origination_month_missing")
    elif origination > event:
        problems.append("event_origination_month_conflict")
    if first is not None and origination is not None and first < origination:
        problems.append("first_report_precedes_origination")
    accepted = not problems
    adjacent = event is not None and prior is not None and event - prior == 1
    origination_lag = event - origination if event is not None and origination is not None else None
    same_month = origination_lag == 0
    comparable = accepted and adjacent and same_month
    result = {
        **source,
        "chronology_accepted": accepted,
        "chronology_problems": problems,
        "adjacent_prior_observed": adjacent,
        "event_minus_origination_months": origination_lag,
        "same_month_pair": same_month,
        "comparison_timing_aligned": comparable,
        "timing_note": (
            "Successor origination precedes predecessor payoff; standalone payment proxies retain their source dates and paired comparisons are withheld."
            if origination_lag is not None and origination_lag > 0 else None
        ),
        "prior_baseline_status": "missing" if prior is None else ("adjacent" if adjacent else "nonadjacent"),
        "successor_first_report_lag_months": first - origination if first is not None and origination is not None else None,
        "coupon_change_pp": None,
        "term_change_months": None,
        "new_rounded_to_prior_upb_ratio": None,
        "balance_change_proxy_dollars": None,
        "scheduled_PI_proxy_old": None,
        "scheduled_PI_proxy_new": None,
        "scheduled_PI_proxy_change": None,
        "fees_financed": None,
        "fees_observed": False,
        "eligibility_known": False,
        "offers_known": False,
        "evidence_timing": "ex_post",
        "balance_proxy_rounded": True,
        "payment_proxy_is_observed_payment": False,
        "balance_proxy_is_fee_or_cashout_or_household_equity": False,
        "payment_proxy_is_lifetime_welfare": False,
        "limitations": [
            "Successor terms are ex-post observations, not offers available before the event.",
            "Prior current UPB and successor original rounded UPB differ in timing and rounding.",
            "The balance-change proxy is not a fee, cash-out, or household-equity measure.",
            "Scheduled P&I proxies assume standard full amortization and are not observed payments or lifetime welfare.",
            "Actual fees, financed fees, eligibility, and unchosen offers are unknown.",
        ],
    }
    if not accepted:
        return result
    result["scheduled_PI_proxy_old"] = _payment(old_upb, old_coupon, old_term, "scheduled_PI_proxy_old")
    result["scheduled_PI_proxy_new"] = _payment(new_upb, new_coupon, new_term, "scheduled_PI_proxy_new")
    if not comparable:
        return result
    if old_coupon is not None and new_coupon is not None:
        result["coupon_change_pp"] = new_coupon - old_coupon
    if old_term is not None and old_term > 0 and new_term is not None and new_term > 0:
        result["term_change_months"] = int(new_term - old_term)
    if old_upb is not None and new_upb is not None:
        result["balance_change_proxy_dollars"] = _finite(new_upb - old_upb, "balance_change_proxy_dollars")
        if old_upb > 0:
            result["new_rounded_to_prior_upb_ratio"] = _finite(new_upb / old_upb, "new_rounded_to_prior_upb_ratio")
    old_payment, new_payment = result["scheduled_PI_proxy_old"], result["scheduled_PI_proxy_new"]
    if old_payment is not None and new_payment is not None:
        result["scheduled_PI_proxy_change"] = _finite(new_payment - old_payment, "scheduled_PI_proxy_change")
    return result
