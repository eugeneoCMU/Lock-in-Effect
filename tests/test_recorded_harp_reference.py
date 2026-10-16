import numpy as np
import pytest
from hazard.recorded_harp_reference import fit_references,score_reference

def rows():return [dict(month=f'2009-{m:02}',recorded_link_event=y) for m in [4,5,6,7] for y in [0,1]]
def test_frequency_and_time_reference_on_balanced_data():
 f=fit_references(rows(),training_end='2009-07')
 assert f.training_rows==8 and f.training_events==4
 for model in ['frequency','linear_time']:
  s=score_reference(f,rows(),model=model)
  assert s['predicted_events']==pytest.approx(4)
  assert s['brier']==pytest.approx(.25)
  assert s['log_loss']==pytest.approx(np.log(2))
def test_future_labels_not_read_and_scaling_train_only():
 a=fit_references(rows(),training_end='2009-07')
 b=fit_references(rows()+[dict(month='2016-09',recorded_link_event='poison')],training_end='2009-07')
 np.testing.assert_array_equal(a.coefficients,b.coefficients)
 assert a.time_mean==b.time_mean and a.time_scale==b.time_scale

def test_unknown_training_label_excluded_only_from_likelihood():
 f=fit_references(rows()+[dict(month='2009-05',recorded_link_event=None)],training_end='2009-07')
 assert f.training_rows==8 and f.excluded_unknown_rows==1
 s=score_reference(f,[dict(month='2014-01',recorded_link_event=None),dict(month='2014-02',recorded_link_event=1)],model='frequency')
 assert s['rows']==1 and s['excluded_unknown_rows']==1 and s['recorded_events']==1

def test_invalid_training_labels_and_empty_score_reject():
 with pytest.raises(ValueError):fit_references(rows()+[dict(month='2009-05',recorded_link_event=2)],training_end='2009-07')
 with pytest.raises(ValueError):fit_references([dict(month='2009-04',recorded_link_event=0)],training_end='2009-07')
 f=fit_references(rows(),training_end='2009-07')
 with pytest.raises(ValueError):score_reference(f,[],model='frequency')

def test_large_fit_has_no_runtime_numeric_warnings():
 import warnings
 data=[dict(month=f'2009-{m:02}',recorded_link_event=int(j<m)) for m in range(4,13) for j in range(1000)]
 with warnings.catch_warnings():
  warnings.simplefilter('error',RuntimeWarning)
  fit=fit_references(data,training_end='2009-12')
  score=score_reference(fit,data,model='linear_time')
 assert score['predicted_events']==pytest.approx(sum(r['recorded_link_event'] for r in data),abs=1e-4)
