import numpy as np
import pandas as pd
import pytest
from hazard.pathb_cohort_validation import prepare_exposures, score, fit_baseline

def test_hand_calculated_errors():
    s=score(np.array([100.,300.]),np.array([10.,30.]),np.array([.2,.1]))
    assert s['observed_b']==pytest.approx(40/1e9)
    assert s['predicted_b']==pytest.approx(50/1e9)
    assert s['weighted_rmse_monthly_pp']==pytest.approx(5.)
    assert s['ratio']==pytest.approx(1.25)

def test_contiguous_lag_and_explicit_exclusions():
    d=pd.DataFrame({'cell':['a']*4,'period':pd.to_datetime(['2023-11-01','2023-12-01','2024-02-01','2024-03-01']),'exposure_upb':[100.,90.,0.,0.],'prepaid_upb':[0.,5.,1.,0.]})
    out,counts=prepare_exposures(d)
    assert len(out)==1 and out.iloc[0].opening_exposure==100.
    assert counts['missing_or_noncontiguous']==2 and counts['zero_exposure']==1
    assert counts['evaluation']=={'input_rows':2,'missing_or_noncontiguous':1,'zero_exposure':1,'invalid_numerator':0}

def test_baseline_uses_no_evaluation_outcome():
    d=pd.DataFrame({'cell':['a']*3,'period':pd.to_datetime(['2023-01-01','2023-12-01','2024-01-01']),'opening_exposure':[100.,100.,100.],'prepaid_upb':[5.,15.,90.]})
    assert fit_baseline(d)['a']==pytest.approx(.1)
