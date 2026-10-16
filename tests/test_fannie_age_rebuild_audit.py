"""Keep an age-only reconstruction from silently changing financial outcomes."""
import pandas as pd
import pytest

from hazard.fannie_age_rebuild_audit import compare_panels, membership_changes, verify_grid_parity


def panel():
    return pd.DataFrame({
        'vintage': [2017, 2017], 'coupon': [.03, .03],
        'fico_bucket': ['a', 'b'], 'ltv_bucket': ['low', 'low'],
        'reporting_period': ['201801', '201801'],
        'exposure_upb': [100., 300.], 'orig_upb_sum': [120., 320.],
        'prepaid_upb': [1., 3.], 'loan_count': [1, 3],
        'monthly_prepay_rate': [.01, .01], 'burnout': [.1, .2],
        'mean_loan_age': [11., 13.], 'mode_state': ['Current', 'Current'],
        'rp': [201801, 201801], 'gap': [-.004, -.004],
    })


def test_age_audit_conserves_amounts_and_reports_reclassification():
    old = panel()
    new = old.copy()
    new['mean_loan_age'] = [12., 11.]
    audit = compare_panels(old, new)
    assert audit['changed_age_rows'] == 2
    assert audit['weighted_abs_age_change_months'] == pytest.approx(1.75)
    entry = next(r for r in membership_changes(old, new)
                 if r['window'] == 'out_of_window_2017_2019'
                 and r['max_gap'] == -.0025 and r['min_mean_age'] == 12)
    assert entry['added_cells'] == entry['removed_cells'] == 1
    assert entry['added_exposure_dollar_months'] == 100.
    assert entry['removed_exposure_dollar_months'] == 300.


def test_age_only_label_rejects_a_changed_payoff_numerator():
    old = panel()
    new = old.copy()
    new.loc[0, 'prepaid_upb'] += 1.
    with pytest.raises(ValueError, match='prepaid_upb'):
        compare_panels(old, new)


def test_grid_replay_does_not_accept_equal_rates_on_different_support():
    actual = {'window': {'cell': {'cpr_pct': 5.522, 'exposure_upb': 100., 'n_cohort_months': 2}}}
    saved = {'window': {'cell': {'cpr_pct': 5.522, 'exposure_upb': 100., 'n_cohort_months': 3}}}
    with pytest.raises(ValueError, match='count'):
        verify_grid_parity(actual, saved)
