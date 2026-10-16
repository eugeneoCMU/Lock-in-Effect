"""Small fixtures guard against double counting and denominator leakage."""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))
from older_vintage_floor_support import (
    combine_cells, prepare_source_rows, summarize_support, monthly_rates,
)


def cell(quarter="FNMA2017Q1", month="201801", count=1, age=24,
         exposure=100.0, prepaid=1.0, coupon=0.04):
    return dict(source_quarter=quarter, vintage=2015, coupon=coupon,
                fico_bucket="high", ltv_bucket="low", reporting_period=month,
                exposure_upb=exposure, orig_upb_sum=exposure * 2,
                prepaid_upb=prepaid, mean_loan_age=age, mode_state="Current",
                loan_count=count)


def test_combine_adds_disjoint_quarters_and_weights_age_by_loan_count():
    rows = pd.DataFrame([cell(count=1, age=12),
                         cell("FNMA2017Q2", count=9, age=32, exposure=900)])
    combined = combine_cells(rows, age_convention="loan_count_weighted")
    assert len(combined) == 1
    assert combined.iloc[0].mean_loan_age == 30
    assert combined.iloc[0].exposure_upb == 1000
    assert combined.iloc[0].loan_count == 10
    assert combined.iloc[0].prepaid_upb == 2
    assert combine_cells(rows, age_convention="legacy").iloc[0].mean_loan_age == 22


def test_duplicate_rows_within_one_quarter_are_rejected_not_summed():
    with pytest.raises(ValueError, match="Duplicate"):
        combine_cells(pd.DataFrame([cell(), cell()]))


def test_unknown_age_is_excluded_and_audited_before_age_based_support():
    rows = pd.DataFrame([cell(age=float('nan'), exposure=100),
                         cell(month='201802', age=25, exposure=90)])
    prepared, audit = prepare_source_rows(rows)
    assert len(prepared) == 1
    assert audit['missing_age_rows'] == 1
    assert audit['missing_age_2018_exposure'] == 100
    assert prepared.opening_exposure_upb.iloc[0] == 100


def test_opening_balance_is_lagged_within_quarter_and_requires_adjacent_month():
    rows = pd.DataFrame([
        cell(month="201712", exposure=110), cell(exposure=100),
        cell("FNMA2017Q2", exposure=900, prepaid=9),
        cell(month="201803", exposure=90),
        cell("FNMA2019Q1", exposure=20),  # future acquisition history
    ])
    prepared, audit = prepare_source_rows(rows)
    assert audit["performance_before_acquisition_rows"] == 1
    combined = combine_cells(prepared)
    jan = combined.loc[combined.reporting_period == "201801"].iloc[0]
    assert jan.opening_exposure_upb == 110  # not 110+900
    assert jan.opening_prepaid_upb == 1  # Q2 event has no matching opening risk set
    assert jan.opening_end_exposure_upb == 100
    march = combined.loc[combined.reporting_period == "201803"].iloc[0]
    assert march.opening_exposure_upb == 0  # January is not February


def test_support_uses_dollar_months_and_concentration_at_both_levels():
    rows = pd.DataFrame([cell(month="201801", exposure=100, prepaid=1),
                         cell(month="201802", exposure=100, prepaid=1),
                         cell(month="201801", coupon=.035, exposure=200, prepaid=2)])
    combined = combine_cells(rows)
    result = summarize_support(combined, min_outcome_cells=1, min_outcome_strata=1)
    assert result["cohort_months"] == 3
    assert result["strata"] == 2
    assert result["months"] == 2
    assert result["exposure_dollar_months"] == 400
    assert result["effective_cohort_months"] == pytest.approx(8 / 3)
    assert result["effective_strata"] == 2
    assert result["annualized_end_exposure_cpr_pct"] == pytest.approx(11.36151282838708)
    assert summarize_support(combined)["annualized_end_exposure_cpr_pct"] is None


def test_rate_parser_keeps_only_2018_and_averages_weekly_values_in_percent():
    payload = b"observation_date,MORTGAGE30US\n2017-12-28,3.99\n2018-01-04,4\n2018-01-11,5\n2018-02-01,.\n"
    rates = monthly_rates(payload, require_complete=False)
    assert rates == {"201801": .045}
    with pytest.raises(ValueError, match="twelve"):
        monthly_rates(payload)
