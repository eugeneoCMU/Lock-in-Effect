import numpy as np
import pytest
from hazard.recorded_harp_incentive import fit_incentive,score_incentive

def rows():return [dict(month=f'2009-{m:02}',gap_pp=g,recorded_link_event=y) for m in [4,5,6,7] for g in [-1.,1.] for y in [0,1]]
@pytest.mark.parametrize('include_time',[False,True])
def test_balanced_reference_and_signed_features(include_time):
 f=fit_incentive(rows(),training_end='2009-07',include_time=include_time)
 s=score_incentive(f,rows())
 assert f.training_rows==16 and f.training_events==8
 assert f.feature_mean[0]==0 and f.feature_scale[0]==1
 assert s['predicted_events']==pytest.approx(8) and s['log_loss']==pytest.approx(np.log(2))

def test_future_poison_ignored_before_parsing_label_or_gap():
 a=fit_incentive(rows(),training_end='2009-07',include_time=True)
 b=fit_incentive(rows()+[dict(month='2016-09',gap_pp='poison',recorded_link_event='poison')],training_end='2009-07',include_time=True)
 np.testing.assert_array_equal(a.coefficients,b.coefficients)
 np.testing.assert_array_equal(a.feature_mean,b.feature_mean)

def test_unknown_outcome_does_not_require_predictors_for_likelihood():
 f=fit_incentive(rows()+[dict(month='2009-05',recorded_link_event=None)],training_end='2009-07',include_time=False)
 assert f.training_rows==16 and f.excluded_unknown_rows==1
 s=score_incentive(f,[dict(month='2014-01',recorded_link_event=None),dict(month='2014-02',gap_pp=-2,recorded_link_event=1)])
 assert s['rows']==1 and s['excluded_unknown_rows']==1

def test_bad_training_gap_and_nonbinary_label_rejected():
 for extra in [dict(month='2009-05',gap_pp=float('nan'),recorded_link_event=1),dict(month='2009-05',gap_pp=0,recorded_link_event=2)]:
  with pytest.raises(ValueError):fit_incentive(rows()+[extra],training_end='2009-07',include_time=False)
