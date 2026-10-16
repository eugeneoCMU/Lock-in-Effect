"""Payment scenarios conserve principal without inferring deferred collections."""
import math
import pytest
from hazard.observed_payment_rule import payment_scenario


def args(**overrides):
    out=dict(total_principal=120.,interest_bearing=100.,deferred=20.,
        current_rate_decimal=.06,remaining_legal_months=12,
        payment_rule='level_payment_to_legal_maturity')
    out.update(overrides)
    return out


def test_annuity_uses_interest_bearing_balance_only():
    r=payment_scenario(**args())
    pmt=100*.005/(1-1.005**-12)
    assert r.scheduled_principal==pytest.approx(pmt-.5)
    assert r.interest==pytest.approx(.5)
    assert r.ending_deferred==20
    assert r.ending_total+r.scheduled_principal==pytest.approx(120)
    assert not r.actual_payment_verified
    assert r.deferred_maturity_cash is None


def test_zero_rate_and_last_month_do_not_collect_deferred_principal():
    r=payment_scenario(**args(current_rate_decimal=0,remaining_legal_months=1))
    assert r.scheduled_principal==100
    assert r.ending_total==r.ending_deferred==20
    assert r.ending_interest_bearing==0
    assert r.remaining_legal_months_after==0
    assert r.deferred_maturity_cash is None


def test_tiny_rate_is_numerically_stable():
    r=payment_scenario(**args(current_rate_decimal=1e-15))
    assert r.scheduled_principal==pytest.approx(100/12,rel=1e-10)


@pytest.mark.parametrize('update',[
    dict(total_principal=121),dict(interest_bearing=-1),dict(deferred=float('nan')),
    dict(current_rate_decimal=6),dict(current_rate_decimal=-.01),
    dict(remaining_legal_months=0),dict(remaining_legal_months=1.5),
    dict(remaining_legal_months=True),dict(payment_rule=None),
    dict(payment_rule='observed_actual_payment'),dict(total_principal=True)])
def test_invalid_or_unstated_rules_fail_closed(update):
    with pytest.raises((ValueError,TypeError)):payment_scenario(**args(**update))


def test_small_component_roundoff_is_retained_as_explicit_residual():
    r=payment_scenario(**args(total_principal=120.005))
    assert r.component_residual==pytest.approx(.005)
    assert r.ending_total+r.scheduled_principal==pytest.approx(120.005)
