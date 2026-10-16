import importlib.util
import numpy as np
import pandas as pd
import pytest

@pytest.fixture
def api():
    assert importlib.util.find_spec('hazard.corrected_chronological_calibration') is not None, 'Chronological calibration implementation required'
    from hazard import corrected_chronological_calibration
    return corrected_chronological_calibration

@pytest.fixture
def inputs():
    rows=[]
    for cell,coupon in [('a',.03),('b',.05)]:
        for p in pd.date_range('2022-12-01','2025-09-01',freq='MS'):
            rows.append(dict(cell=cell,period=p,coupon=coupon,vintage=2020,exposure_upb=1000.,prepaid_upb=2.,mean_loan_age=30.,burnout=.1,cohort_original_upb=2000.))
    panel=pd.DataFrame(rows);cov=pd.DataFrame({'fico_z':[0.,.2],'ltv_z':[0.,-.2]},index=['a','b'])
    rates=pd.Series(.06,index=pd.period_range('2022-12','2025-09',freq='M'))
    return panel,cov,rates

def test_training_selection_and_baseline_ignore_future_outcomes(api,inputs):
    panel,cov,rates=inputs;candidates=[api.Candidate('low','max',psa=25.,annual_floor=0.),api.Candidate('high','max',psa=100.,annual_floor=.04991)]
    a=api.calibrate(panel,cov,rates,'2023-01-01','2023-12-01',candidates)
    corrupted=panel.copy();corrupted.loc[corrupted.period>pd.Timestamp('2023-12-01'),'prepaid_upb']=999999.
    b=api.calibrate(corrupted,cov,rates,'2023-01-01','2023-12-01',candidates)
    assert a['selected']==b['selected'] and a['grid']==b['grid'] and a['baseline']==b['baseline']
    assert a['baseline']=={'a':.002,'b':.002}

def test_predictions_never_read_evaluation_outcomes(api,inputs):
    panel,cov,rates=inputs;state=panel[panel.period==pd.Timestamp('2023-12-01')].set_index('cell')
    calendar=api.calendar(state,'2024-01-01','2024-03-01');c=api.Candidate('x','mixture',psa=50.,share=.75,gamma=.07)
    a=api.forecast(calendar,state,cov,rates,c)
    changed=calendar.assign(prepaid_upb=1e99,burnout=1.,exposure_upb=0.)
    b=api.forecast(changed,state,cov,rates,c)
    np.testing.assert_array_equal(a.hazard,b.hazard)
    assert len(a)==6 and (a.predicted_burnout>=.1).all()

def test_max_predictor_matches_existing_fixed_history_engine(api,inputs):
    from hazard.pathb_prediction_diagnostics import predict_path,RESPONSE_BETA
    panel,cov,rates=inputs;state=panel[panel.period==pd.Timestamp('2023-12-01')].set_index('cell');cal=api.calendar(state,'2024-01-01','2024-03-01')
    got=api.forecast(cal,state,cov,rates,api.Candidate('x','max',psa=75.,annual_floor=.035))
    expected=predict_path(cal,state,cov,rates,.035,75.,RESPONSE_BETA)
    np.testing.assert_allclose(got.hazard,expected.hazard,rtol=1e-13)

def test_missing_observed_scoring_month_does_not_skip_latent_calendar(api,inputs):
    panel,cov,rates=inputs;train=api.calibrate(panel,cov,rates,'2023-01-01','2023-12-01',[api.Candidate('x','max',psa=50.,annual_floor=0.)])
    allscore,pred,a=api.evaluate_selected(panel,cov,rates,train,'2024-01-01','2024-03-01')
    missing=panel[~((panel.cell=='a')&(panel.period==pd.Timestamp('2024-02-01')))]
    sparse,pred2,b=api.evaluate_selected(missing,cov,rates,train,'2024-01-01','2024-03-01')
    pd.testing.assert_frame_equal(pred,pred2)
    assert len(pred2)==6 and len(sparse)<len(allscore)
    assert b['support']['calendar_rows']==6

def test_fixed_grid_counts_and_unique_ids(api):
    grid=api.candidate_grid();assert len(grid)==112 and len({c.id for c in grid})==112
    assert sum(c.family=='mixture' for c in grid)==80

def test_missing_rates_and_duplicate_state_rejected(api,inputs):
    panel,cov,rates=inputs;state=panel[panel.period==pd.Timestamp('2023-12-01')].set_index('cell');cal=api.calendar(state,'2024-01-01','2024-03-01')
    with pytest.raises(ValueError,match='rate'):api.forecast(cal,state,cov,rates.drop(pd.Period('2024-02','M')),api.Candidate('x','max'))
    with pytest.raises(ValueError,match='Duplicate'):api.calendar(pd.concat([state,state]),'2024-01-01','2024-03-01')

def test_chronological_window_and_candidate_validation(api,inputs):
    panel,cov,rates=inputs
    with pytest.raises(ValueError):api.Candidate('x','mixture',share=1.01)
    with pytest.raises(ValueError):api.Candidate('x','max',annual_floor=np.nan)
    with pytest.raises(ValueError):api.calibrate(panel,cov,rates,'2024-01-01','2023-12-01',[api.Candidate('x','max')])

def test_exclusion_counts_follow_requested_window_not_legacy_dates(api,inputs):
    panel,cov,rates=inputs;trained=api.calibrate(panel,cov,rates,'2023-01-01','2024-12-01',[api.Candidate('x','max')])
    scored,pred,result=api.evaluate_selected(panel,cov,rates,trained,'2025-01-01','2025-09-01')
    counts=result['support']['exclusions']['evaluation']
    assert counts['input_rows']==18
    assert counts['missing_or_noncontiguous']==0
    assert counts['zero_exposure']==0 and counts['invalid_numerator']==0
    assert trained['support']['exclusions']['evaluation']['input_rows']==48

def test_forecast_rejects_calendar_that_skips_first_latent_month(api,inputs):
    panel,cov,rates=inputs;state=panel[panel.period==pd.Timestamp('2023-12-01')].set_index('cell')
    skipped=api.calendar(state,'2024-02-01','2024-03-01')
    with pytest.raises(ValueError,match='month'):api.forecast(skipped,state,cov,rates,api.Candidate('x','mixture'))
    state=state.copy();state['period']=pd.Timestamp('2023-12-15')
    with pytest.raises(ValueError,match='month'):api.forecast(api.calendar(state,'2024-01-01','2024-03-01'),state,cov,rates,api.Candidate('x','max'))
