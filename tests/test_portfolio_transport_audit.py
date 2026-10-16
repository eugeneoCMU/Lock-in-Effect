import pytest
from hazard.portfolio_transport_audit import audit_transport


def test_unsupported_target_mass_is_not_renormalized_away():
    r=audit_transport([{'cell':'A'}],[{'cell':'A','weight':.6},{'cell':'B','weight':.4}],coupon_basis='security_pass_through',as_of_date='2022-05-31')
    assert r['supported_target_share']==.6
    assert r['unsupported_target_share']==.4
    assert r['full_portfolio_verified'] is False


def test_unknown_target_and_receipts_not_certified():
    r=audit_transport([],[],coupon_basis='security_pass_through',as_of_date='2022-05-31')
    assert r['supported_target_share'] is None
    assert r['unsupported_target_share'] is None
    assert r['receipt_mapping_verified'] is False


def test_partial_weights_preserve_residual():
    r=audit_transport([{'cell':'A'}],[{'cell':'A','weight':.6}],coupon_basis='security_pass_through',as_of_date='2022-05-31')
    assert r['unmapped_residual_share']==pytest.approx(.4)
    assert r['unsupported_target_share']==pytest.approx(.4)


@pytest.mark.parametrize('weight',[-.1,float('nan'),1.1])
def test_invalid_target_mass_rejected(weight):
    with pytest.raises(ValueError):
        audit_transport([], [{'cell':'A','weight':weight}],coupon_basis='security_pass_through',as_of_date='2022-05-31')
