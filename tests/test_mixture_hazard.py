import numpy as np
import pytest
from hazard.mixture_hazard import mixture_probability, reference_probability, mixture_context
from test_simulate_freddie_rebuild import pair_inputs
from test_calibrate_freddie_rebuild import inputs as floor_inputs


def test_example_and_nulls():
    expected = 0.0164933792309524
    assert mixture_probability(.02, -.04, .75, -np.log(.935)) == pytest.approx(expected)
    for share, gamma, gap in [(0, .1, -.04), (.75, 0, -.04), (.75, .1, 0), (.75, .1, .04)]:
        assert mixture_probability(.02, gap, share, gamma) == pytest.approx(.02)
    assert mixture_probability(.02, -.04, .75, .1, lock_in=False) == pytest.approx(.02)


@pytest.mark.parametrize('p,s,g,gap', [(1,.5,.1,0),(-.1,.5,.1,0),(.02,1.1,.1,0),(.02,.5,-1,0),(.02,.5,.1,np.nan)])
def test_reject_invalid(p,s,g,gap):
    with pytest.raises(ValueError): mixture_probability(p,gap,s,g)


def test_monotonic_and_asymptote():
    p = mixture_probability(.02, -np.array([0,.01,.04,100]), .75, .1)
    assert np.all(np.diff(p) < 0)
    assert p[-1] == pytest.approx(-np.expm1(np.log1p(-.02)*.25))


def test_context_restores_after_failure():
    import hazard.simulate_freddie_rebuild as pair
    original = pair.lh.prepay_hazard
    with pytest.raises(RuntimeError):
        with mixture_context(.75, 'illustrative', 'positive_only'):
            assert pair.cr.prepay_hazard is pair.lh.prepay_hazard
            assert pair.lh.prepay_hazard is not original
            pair.validate_conventions()
            raise RuntimeError('probe')
    assert pair.cr.prepay_hazard is pair.lh.prepay_hazard is original


def test_real_engine_pair_and_null_share(pair_inputs):
    from hazard.run_mixture_rebuild import run_pair
    import hazard.simulate_freddie_rebuild as pair
    original = pair.lh.prepay_hazard
    result = run_pair(**pair_inputs, sensitive_share=0., calibration='illustrative', gap_mode='positive_only')
    assert result['reported_marginal_b'] == pytest.approx(0, abs=1e-10)
    assert result['parameters']['floor_form'] == 'mixture'
    assert result['parameters']['annual_floor'] is None
    assert result['parameters']['sensitive_share'] == 0
    assert pair.lh.prepay_hazard is original
    assert result['closed_pool_cash_marginal_b'] == pytest.approx(0, abs=1e-10)


def test_refinancing_variant_and_legacy_conversion():
    from hazard.mixture_hazard import response_gamma
    import hazard.simulate_freddie_rebuild as pair
    gamma = response_gamma(pair.lh.rothstein_beta1(.065), 'legacy_conversion')
    assert gamma > 0
    assert mixture_probability(.02,.02,.75,gamma,gap_mode='preserve_refinancing') > .02
    assert mixture_probability(.02,.02,.75,gamma,gap_mode='preserve_refinancing',lock_in=False) == pytest.approx(.02)
    assert mixture_probability(0.,1000.,.75,gamma,gap_mode='preserve_refinancing') == 0
    assert mixture_probability(.02,1000.,.75,gamma,gap_mode='preserve_refinancing') == 1


def test_positive_share_real_engine_and_manifest(pair_inputs):
    import json
    from hazard.run_mixture_rebuild import run_pair
    result = run_pair(**pair_inputs,sensitive_share=.75,calibration='legacy_conversion',gap_mode='positive_only')
    assert result['closed_pool_cash_marginal_b'] > 0
    manifest = json.loads((pair_inputs['output']/'input_manifest.json').read_text())
    assert manifest['parameters']['sensitive_share'] == .75
    assert manifest['parameters']['annual_floor'] is None
    assert manifest['parameters']['gamma_per_pp']['off'] == 0
    assert manifest['parameters']['gamma_per_pp']['on'] > 0
    assert 'response_pct' not in result['legs']['on']
    assert any(k.endswith('mixture_hazard.py') for k in manifest['code_sha256'])
    assert (pair_inputs['output']/'adapter_results.json').exists()
    assert result['legs']['on']['max_total_identity_error_b'] < 1e-8


def test_invalid_reference_requires_recalibration():
    with pytest.raises(ValueError,match='Reference schedule'):
        reference_probability(np.array([60.]),np.array([-1000.]),np.array([0.]),np.array([0.]))


def test_cli_rejects_protected_parent_before_writing(pair_inputs, monkeypatch):
    from hazard.run_mixture_rebuild import main
    target = pair_inputs['root']/'combined'/'must-not-exist'
    args=['mixture']
    for name,value in dict(pair_inputs,output=target).items():
        args += ['--'+name.replace('_','-'),str(value)]
    monkeypatch.setattr('sys.argv',args)
    with pytest.raises(SystemExit): main()
    assert not target.exists()
