import numpy as np
import pytest
from hazard.coupon_bridge_sensitivity import bridge_buckets, target_weights

def test_bridge_enters_assignment():
    assert bridge_buckets(np.array([.03]),60)[0]!=bridge_buckets(np.array([.03]),100)[0]

def test_support_failure_preserves_missing_mass():
    r=target_weights(np.array([100.,100.]),np.array([.025,.025]),np.array(['2020','2020']),{(.025,'2020'):.6,(.02,'2021'):.4})
    assert r['status']=='unsupported' and r['missing_target_share']==pytest.approx(.4)
    assert 'weights' not in r

def test_exact_weighted_cell_shares():
    r=target_weights(np.array([100.,300.,50.]),np.array([.025,.025,.02]),np.array(['2020','2020','2021']),{(.025,'2020'):.6,(.02,'2021'):.4})
    b=np.array([100.,300.,50.])*r['weights']
    np.testing.assert_allclose([b[:2].sum()/b.sum(),b[2]/b.sum()],[.6,.4],atol=1e-8)
