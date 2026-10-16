"""Ex-post linked contracts retain source limits instead of imputing offers or fees."""

import copy

import pytest

from hazard.linked_refinancing_terms import describe_linked_contract


def describe(**changes):
    fields = dict(
        event_label="linked_harp_payoff",
        event_month="2011-01",
        prior_month="2010-12",
        prior_upb=100_000.0,
        prior_coupon_percent=6.0,
        prior_remaining_months=240,
        successor_first_report_month="2011-03",
        successor_origination_month="2011-01",
        successor_original_upb_rounded=101_000.0,
        successor_original_coupon_percent=4.0,
        successor_original_term_months=360,
    )
    fields.update(changes)
    return describe_linked_contract(**fields)


def test_adjacent_link_reports_observed_contract_changes_with_percent_units():
    result = describe()
    assert result["chronology_accepted"] is True
    assert result["adjacent_prior_observed"] is True
    assert result["event_minus_origination_months"] == 0
    assert result["same_month_pair"] is True
    assert result["comparison_timing_aligned"] is True
    assert result["prior_baseline_status"] == "adjacent"
    assert result["successor_first_report_lag_months"] == 2
    assert result["coupon_change_pp"] == -2.0
    assert result["term_change_months"] == 120
    assert result["new_rounded_to_prior_upb_ratio"] == pytest.approx(1.01)
    assert result["balance_change_proxy_dollars"] == 1_000.0
    # Independently hand-calculated standard fixed-rate amortization payments.
    assert result["scheduled_PI_proxy_old"] == pytest.approx(716.431058478173)
    assert result["scheduled_PI_proxy_new"] == pytest.approx(482.189448419109)
    assert result["scheduled_PI_proxy_change"] == pytest.approx(-234.241610059064)


@pytest.mark.parametrize(
    "origination_month, event_lag, report_lag",
    [("2010-12", 1, 3), ("2010-11", 2, 4)],
)
def test_prior_origination_remains_accepted_but_does_not_form_an_aligned_comparison(
    origination_month, event_lag, report_lag,
):
    result = describe(successor_origination_month=origination_month)
    assert result["chronology_accepted"] is True
    assert result["chronology_problems"] == []
    assert result["event_minus_origination_months"] == event_lag
    assert result["same_month_pair"] is False
    assert result["comparison_timing_aligned"] is False
    assert result["timing_note"]
    assert result["successor_first_report_lag_months"] == report_lag
    assert result["successor_origination_month"] == origination_month
    assert result["scheduled_PI_proxy_old"] == pytest.approx(716.431058478173)
    assert result["scheduled_PI_proxy_new"] == pytest.approx(482.189448419109)
    for field in (
        "coupon_change_pp", "term_change_months", "new_rounded_to_prior_upb_ratio",
        "balance_change_proxy_dollars", "scheduled_PI_proxy_change",
    ):
        assert result[field] is None


def test_zero_coupon_payment_is_principal_over_stated_months():
    result = describe(
        prior_coupon_percent=0,
        prior_remaining_months=100,
        successor_original_coupon_percent=0,
        successor_original_term_months=200,
    )
    assert result["scheduled_PI_proxy_old"] == 1_000
    assert result["scheduled_PI_proxy_new"] == 505
    assert result["scheduled_PI_proxy_change"] == -495


@pytest.mark.parametrize("prior_month", ["2010-11", "2009-12", "2011-01", None])
def test_stale_or_missing_prior_keeps_source_but_suppresses_comparisons(prior_month):
    result = describe(prior_month=prior_month)
    assert result["chronology_accepted"] is True
    assert result["adjacent_prior_observed"] is False
    assert result["comparison_timing_aligned"] is False
    assert result["prior_month"] == prior_month
    assert result["prior_upb"] == 100_000
    for field in (
        "coupon_change_pp", "term_change_months", "new_rounded_to_prior_upb_ratio",
        "balance_change_proxy_dollars", "scheduled_PI_proxy_change",
    ):
        assert result[field] is None
    assert result["prior_baseline_status"] == ("missing" if prior_month is None else "nonadjacent")


@pytest.mark.parametrize(
    "changes",
    [
        {"event_label": "paid_off_cause_unresolved"},
        {"event_label": "linked_harp_date_conflict"},
        {"event_label": None},
        {"successor_origination_month": "2011-02"},
        {"successor_first_report_month": "2010-12"},
        {"event_month": None},
        {"successor_origination_month": None},
    ],
)
def test_unaccepted_link_retains_payload_and_never_reports_contract_comparisons(changes):
    result = describe(**changes)
    assert result["chronology_accepted"] is False
    assert result["comparison_timing_aligned"] is False
    assert result["chronology_problems"]
    for field, value in changes.items():
        assert result[field] == value
    for field in (
        "coupon_change_pp", "term_change_months", "new_rounded_to_prior_upb_ratio",
        "balance_change_proxy_dollars", "scheduled_PI_proxy_old",
        "scheduled_PI_proxy_new", "scheduled_PI_proxy_change",
    ):
        assert result[field] is None


def test_missing_first_report_does_not_invent_lag_or_reject_matching_origination():
    result = describe(successor_first_report_month=None)
    assert result["chronology_accepted"] is True
    assert result["successor_first_report_lag_months"] is None
    assert result["coupon_change_pp"] == -2


def test_missing_source_fields_are_not_imputed_and_other_observed_pairs_survive():
    result = describe(prior_upb=None, successor_original_coupon_percent=None)
    assert result["prior_upb"] is None
    assert result["successor_original_coupon_percent"] is None
    assert result["coupon_change_pp"] is None
    assert result["term_change_months"] == 120
    assert result["new_rounded_to_prior_upb_ratio"] is None
    assert result["balance_change_proxy_dollars"] is None
    assert result["scheduled_PI_proxy_old"] is None
    assert result["scheduled_PI_proxy_new"] is None


def test_zero_remaining_term_is_retained_but_cannot_define_a_payment_proxy():
    result = describe(prior_remaining_months=0, successor_original_term_months=0)
    assert result["prior_remaining_months"] == 0
    assert result["term_change_months"] is None
    assert result["scheduled_PI_proxy_old"] is None
    assert result["scheduled_PI_proxy_new"] is None


def test_zero_prior_balance_does_not_define_a_balance_ratio():
    result = describe(prior_upb=0)
    assert result["new_rounded_to_prior_upb_ratio"] is None
    assert result["balance_change_proxy_dollars"] == 101_000
    assert result["scheduled_PI_proxy_old"] == 0


def test_contract_metadata_keeps_fees_offers_and_eligibility_unknown():
    result = describe()
    assert result["fees_financed"] is None
    assert result["fees_observed"] is False
    assert result["eligibility_known"] is False
    assert result["offers_known"] is False
    assert result["evidence_timing"] == "ex_post"
    assert result["balance_proxy_rounded"] is True
    assert result["payment_proxy_is_observed_payment"] is False
    assert result["balance_proxy_is_fee_or_cashout_or_household_equity"] is False
    assert result["payment_proxy_is_lifetime_welfare"] is False
    assert result["limitations"]


@pytest.mark.parametrize(
    "field",
    [
        "prior_upb", "prior_coupon_percent", "prior_remaining_months",
        "successor_original_upb_rounded", "successor_original_coupon_percent",
        "successor_original_term_months",
    ],
)
@pytest.mark.parametrize("value", [True, False, -1, float("nan"), float("inf"), "5"])
def test_bad_present_numeric_inputs_raise_instead_of_becoming_missing(field, value):
    with pytest.raises(ValueError, match=field):
        describe(**{field: value})


@pytest.mark.parametrize("field", ["prior_remaining_months", "successor_original_term_months"])
def test_fractional_month_counts_are_rejected(field):
    with pytest.raises(ValueError, match=field):
        describe(**{field: 12.5})


@pytest.mark.parametrize(
    "field",
    ["event_month", "prior_month", "successor_first_report_month", "successor_origination_month"],
)
@pytest.mark.parametrize("value", ["201101", "2011-1", "2011-13", "0000-01", 201101, True, ""])
def test_malformed_months_are_rejected(field, value):
    with pytest.raises(ValueError, match=field):
        describe(**{field: value})


def test_inputs_are_not_mutated_and_calls_do_not_share_mutable_metadata():
    fields = dict(
        event_label="linked_harp_payoff", event_month="2011-01", prior_month="2010-12",
        prior_upb=None, prior_coupon_percent=None, prior_remaining_months=None,
        successor_first_report_month="2011-03", successor_origination_month="2011-01",
        successor_original_upb_rounded=None, successor_original_coupon_percent=None,
        successor_original_term_months=None,
    )
    original = copy.deepcopy(fields)
    first = describe_linked_contract(**fields)
    first["limitations"].clear()
    second = describe_linked_contract(**fields)
    assert fields == original
    assert second["limitations"]
    assert second["coupon_change_pp"] is None
