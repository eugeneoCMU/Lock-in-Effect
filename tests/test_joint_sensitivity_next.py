import importlib.util
import numpy as np
import pytest
from test_simulate_freddie_rebuild import pair_inputs,floor_inputs

def api():
    assert importlib.util.find_spec('tools.run_joint_sensitivity') is not None,'Joint sensitivity implementation required'
    from tools import run_joint_sensitivity
    return run_joint_sensitivity

def test_response_multiplier_exercises_exact_imported_beta():
    a=api()
    for factor in [.5,1.,1.5]:
        pct=a.response_percent(factor)
        assert -a.pair.lh.rothstein_beta1(pct/100)==pytest.approx(a.BASE_GAMMA*factor,rel=1e-12)
    with pytest.raises(ValueError):a.response_percent(-1.)

def test_real_engine_joint_responses_keep_off_path_and_restore_floor(pair_inputs,tmp_path):
    import polars as pl
    import pandas as pd
    a=api();root=pair_inputs['root'];loans=pl.read_parquet(root/'combined/loan_sample.parquet');matrix=pd.read_parquet(root/'combined/markov_transition_matrix.parquet');macro=pd.read_parquet(pair_inputs['macro_path'])
    old=a.pair.lh.INVOLUNTARY_CPR_ANNUAL
    low=a.run_exact_pair(loans,matrix,macro,tmp_path/'low',floor=.035,response_multiplier=.5)
    high=a.run_exact_pair(loans,matrix,macro,tmp_path/'high',floor=.035,response_multiplier=1.5)
    assert low['legs']['off']==high['legs']['off']
    assert high['reported_marginal_b']>low['reported_marginal_b']
    assert a.pair.lh.INVOLUNTARY_CPR_ANNUAL==old
    assert high['effective_gamma_per_pp']==pytest.approx(a.BASE_GAMMA*1.5)
