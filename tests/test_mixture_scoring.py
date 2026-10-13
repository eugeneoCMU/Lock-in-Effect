import numpy as np
import pytest
from test_score_freddie_rebuild import inputs
from test_calibrate_freddie_rebuild import inputs as source_inputs
from hazard.score_mixture_rebuild import run


def test_scoring_zero_share_has_identical_legs(inputs):
    result = run(**inputs, sensitive_share=0.)
    assert result['parameters']['mixture']['sensitive_share'] == 0
    import pandas as pd
    prediction = pd.read_parquet(inputs['output'] / 'predictions.parquet')
    assert np.allclose(prediction.mixture_on, prediction.mixture_off)
    assert not prediction.mixture_on_floor_bound.any()
    assert result['parameter_selection_performed'] is False


def test_positive_share_predicts_lower_payoffs_and_restores_hooks(inputs):
    import hazard.score_freddie_rebuild as scoring
    original = scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES
    result = run(**inputs,sensitive_share=.75)
    assert result['aggregate']['mixture_on']['predicted_b'] < result['aggregate']['mixture_off']['predicted_b']
    assert original == (scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES)


def test_scoring_restores_after_gate_failure(inputs):
    import hazard.score_freddie_rebuild as scoring
    original = scoring.predict_path
    inputs['root'] = inputs['root']/'missing'
    with pytest.raises((ValueError,FileNotFoundError)):
        run(**inputs,sensitive_share=.75)
    assert scoring.predict_path is original
    assert not inputs['output'].exists()


def test_illustrative_receipt_records_actual_intensity_coefficient(inputs):
    import json
    run(**inputs,sensitive_share=.75,calibration='illustrative')
    manifest=json.loads((inputs['output']/'input_manifest.json').read_text())
    assert manifest['parameters']['mixture']['gamma_per_pp']['on'] == pytest.approx(-np.log(.935))
    assert manifest['response_coefficients']['on'] == pytest.approx(np.log(.935))
