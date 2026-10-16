import numpy as np
import pytest
from paired_scenario_uncertainty import summarize_monte_carlo

def test_mc_precision_is_not_sampling_inference():
    r=summarize_monte_carlo([1.,2.,3.])
    assert r['mean']==2.
    assert r['mcse']==pytest.approx(1/np.sqrt(3))
    assert r['sampling_interval_estimated'] is False

def test_single_seed_does_not_estimate_precision():
    r=summarize_monte_carlo([2.])
    assert r['mcse'] is None
    assert r['precision_goal_met'] is False

@pytest.mark.parametrize('values',[[],[float('nan')],[float('inf')]])
def test_invalid_effects(values):
    with pytest.raises(ValueError):summarize_monte_carlo(values)
