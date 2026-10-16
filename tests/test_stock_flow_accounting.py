import numpy as np
import pandas as pd
import pytest
from hazard.stock_flow_accounting_comparison import reconcile_step, cap_cashflows, simulate_accounting

def test_cash_and_transfer_reconcile_without_double_count():
    x=reconcile_step(100.,90.,3.,5.,2.,0.)
    assert x['active_residual']==0
    assert x['cash_principal']==8
    assert x['default_transfer']==2

def test_inconsistent_identity_fails():
    with pytest.raises(ValueError):reconcile_step(100.,89.,3.,5.,2.,0.)

def test_cap_binding_distinguishes_cash_runoff_and_reinvestment():
    runoff,reinvestment=cap_cashflows(np.array([20.,40.]),np.array([17.5,35.]))
    np.testing.assert_allclose(runoff,[17.5,35.]);np.testing.assert_allclose(reinvestment,[2.5,5.])

def test_zero_response_paths_are_identical():
    import polars as pl
    loans=pl.read_parquet('hazard/data/loan_sample.parquet').head(100)
    macro=pd.DataFrame({'MORTGAGE30US':[6.,7.],'WSHOMCB':[2700000.,2680000.]},index=pd.to_datetime(['2022-06-30','2022-07-31']))
    a=simulate_accounting(loans,macro,0.);b=simulate_accounting(loans,macro,0.)
    pd.testing.assert_frame_equal(a,b)
    assert (a.closing_active_b>=0).all()
    np.testing.assert_allclose(a.opening_total_b-a.cash_principal_b,a.closing_total_b,atol=1e-10)
