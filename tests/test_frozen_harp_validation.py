import math
import pytest
from hazard.frozen_harp_validation import frozen_logits, score_rows


def summaries():
    reference={'fit_parameters':dict(frequency_logit=-2.,time_mean_training_months_since_april2009=10.,time_scale_training=2.,linear_time_coefficients=[-3.,.5])}
    incentive={'fit_parameters':{
        'gap_only':dict(feature_mean=[1.],feature_scale=[2.],coefficients_standardized=[-2.,.4]),
        'gap_and_time':dict(feature_mean=[1.,10.],feature_scale=[2.,2.],coefficients_standardized=[-3.,.4,.5])}}
    return reference,incentive


def test_exact_frozen_formulas_and_signed_gap():
    r,i=summaries()
    assert frozen_logits(r,i,'frequency','2010-04')==-2
    assert frozen_logits(r,i,'linear_time','2010-04')==-2.5
    assert frozen_logits(r,i,'gap_only','2010-04',-1)==pytest.approx(-2.4)
    assert frozen_logits(r,i,'gap_and_time','2010-04',-1)==pytest.approx(-2.9)


def test_missing_accounting_and_simple_models_ignore_missing_gap():
    r,i=summaries();rows=[dict(month='2010-04',gap_pp=-1,recorded_link_event=1),dict(month='2010-05',gap_pp=None,recorded_link_event=0),dict(month='2010-06',gap_pp=None,recorded_link_event=None)]
    s=score_rows(r,i,'gap_only',rows)
    assert (s['exposure_rows'],s['scored_rows'],s['excluded_unknown_outcomes'],s['excluded_missing_feature'],s['recorded_events'])==(3,1,1,1,1)
    assert score_rows(r,i,'frequency',rows)['scored_rows']==2
    assert score_rows(r,i,'linear_time',rows)['scored_rows']==2
    assert frozen_logits(r,i,'gap_only','2010-04') is None


def test_adding_cohort_rows_does_not_rescale():
    r,i=summaries();a=dict(month='2010-04',gap_pp=-1,recorded_link_event=1)
    before=frozen_logits(r,i,'gap_and_time',a['month'],a['gap_pp'])
    score_rows(r,i,'gap_and_time',[a,dict(month='2020-01',gap_pp=100,recorded_link_event=0)])
    assert frozen_logits(r,i,'gap_and_time',a['month'],a['gap_pp'])==before


def test_stable_extremes_and_empty_scores():
    r,i=summaries();r['fit_parameters']['frequency_logit']=1000
    s=score_rows(r,i,'frequency',[dict(month='2010-04',recorded_link_event=0)])
    assert s['log_loss']==1000 and s['brier']==1 and s['predicted_events']==1
    r['fit_parameters']['frequency_logit']=-1000
    s=score_rows(r,i,'frequency',[dict(month='2010-04',recorded_link_event=1)])
    assert s['log_loss']==1000 and s['brier']==1
    s=score_rows(r,i,'gap_only',[dict(month='2010-04',recorded_link_event=1)])
    assert s['scored_rows']==0 and s['log_loss'] is None and s['brier'] is None and s['predicted_events']==0


def test_invalid_inputs_never_fallback():
    r,i=summaries()
    for model,month,gap in [('bad','2010-04',1),('frequency','2010-13',None),('gap_only','2010-04',float('nan')),('gap_only','2010-04',True)]:
        with pytest.raises(ValueError):frozen_logits(r,i,model,month,gap)
    for label in [2,1.,'1']:
        with pytest.raises(ValueError):score_rows(r,i,'frequency',[dict(month='2010-04',recorded_link_event=label)])
    i['fit_parameters']['gap_only']['feature_scale']=[0]
    with pytest.raises(ValueError):frozen_logits(r,i,'gap_only','2010-04',1)
    r['fit_parameters']['frequency_logit']=float('inf')
    with pytest.raises(ValueError):frozen_logits(r,i,'frequency','2010-04')


def test_manual_probability_loss_and_denominator_accounting():
    r,i=summaries();p=1/(1+math.exp(2.4))
    s=score_rows(r,i,'gap_only',[
        dict(month='2010-04',gap_pp=-1,recorded_link_event=1),
        dict(month='2010-04',gap_pp=-1,recorded_link_event=0),
        dict(month='2010-04',gap_pp='ignored for unknown label',recorded_link_event=None),
        dict(month='2010-04',recorded_link_event=1)])
    assert s['predicted_events']==pytest.approx(2*p)
    assert s['log_loss']==pytest.approx((-math.log(p)-math.log1p(-p))/2)
    assert s['brier']==pytest.approx(((1-p)**2+p*p)/2)
    assert s['exposure_rows']==s['scored_rows']+s['excluded_unknown_outcomes']+s['excluded_missing_feature']
    assert s['recorded_events']==1


def test_parameters_validate_even_with_no_scores_and_dates_always_validate():
    r,i=summaries()
    i['fit_parameters']['gap_only']['coefficients_standardized']=[1]
    with pytest.raises(ValueError):score_rows(r,i,'gap_only',[])
    r,i=summaries();i['fit_parameters']['gap_only']['feature_scale']=[float('nan')]
    with pytest.raises(ValueError):frozen_logits(r,i,'gap_only','2010-04')
    with pytest.raises(ValueError):score_rows(r,i,'frequency',[dict(month='2010-00',recorded_link_event=None)])
    r['fit_parameters']['time_scale_training']=-1
    with pytest.raises(ValueError):frozen_logits(r,i,'linear_time','2010-04')
