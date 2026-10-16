"""Offline fixed additive-floor benchmarks sharing the corrected-input gates."""
from contextlib import contextmanager
from pathlib import Path
from hazard import simulate_freddie_rebuild as pair
from hazard import score_freddie_rebuild as scoring

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / 'specs/SPEC_2026-10-13_comparison_matrix_v2.md'


@contextmanager
def additive_pair_context():
    """Explicitly declare additive composition and restore all adapter state."""
    previous = pair.PARAMETERS, pair.SPEC, pair.CODE_FILES, pair.lh.FLOOR_MODE
    pair.PARAMETERS = dict(pair.PARAMETERS, annual_floor=.04991, psa=100., floor_form='additive')
    pair.SPEC = SPEC
    pair.CODE_FILES = pair.CODE_FILES + [Path(__file__)]
    pair.lh.FLOOR_MODE = 'additive'
    try:
        yield
    finally:
        pair.PARAMETERS, pair.SPEC, pair.CODE_FILES, pair.lh.FLOOR_MODE = previous


def run_additive_pair(**inputs):
    """Run the fixed floor/PSA response pair with additive survival composition."""
    with additive_pair_context():
        result = pair.run(**inputs)
    output = Path(inputs['output'])
    (output/'results.json').rename(output/'adapter_results.json')
    result['scope'] = 'Conditional corrected-input Freddie additive-floor benchmark pair'
    result['limitations'] += ['Additive survival composition is a structural sensitivity; floor and PSA are fixed, not newly selected.']
    result['output_sha256'] = {p.name: pair.digest(p) for p in output.iterdir() if p.is_file()}
    pair.write_json(output/'results.json', result)
    return result


@contextmanager
def additive_scoring_context():
    previous = scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES
    def choices(*args, **kwargs):
        previous[1](*args, **kwargs)
        return {'additive': dict(annual_floor=.04991, psa=100., floor_form='additive')}
    def predictor(*args, **kwargs):
        return previous[0](*args, **kwargs, floor_form='additive')
    scoring.predict_path, scoring.recorded_choices = predictor, choices
    scoring.SPEC = SPEC
    scoring.CODE_FILES = scoring.CODE_FILES + ['benchmark_forms.py']
    try:
        yield
    finally:
        scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES = previous


def score_additive(**inputs):
    """Score a fixed additive family while validating the historical selection."""
    with additive_scoring_context():
        return scoring.run(**inputs)
