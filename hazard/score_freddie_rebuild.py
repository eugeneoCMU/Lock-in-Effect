"""Score fixed recorded prediction candidates on verified corrected Freddie inputs.

Offline only: this wrapper never selects parameters, fetches macro data, starts
source reconstruction or overwrites a previous attempt. All paths are explicit.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for directory in (ROOT, HERE):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
os.environ.setdefault('FRED_API_KEY', 'offline-retrospective-scoring-no-network')

from hazard.calibrate_freddie_rebuild import (
    validated_combined, validate_panel_identity, verify_hashes,
)
from hazard.cohort_history import prediction_initial_state
from hazard.pathb_cohort_validation import KEYS, START, END, fit_baseline, prepare_exposures
from hazard.pathb_prediction_diagnostics import (
    RESPONSE_BETA, diagnose_groups, make_covariates, predict_path, strict_score,
)
from run_freddie_rebuild import digest, write_json

SPEC = ROOT / 'specs/SPEC_2026-10-12_corrected_retrospective_scoring.md'
MACRO_REFERENCE = 'output/review-revision/2026-10-07-checks/macro_frozen.parquet'
PRE = pd.Timestamp('2023-12-01')
TRAIN_START = pd.Timestamp('2023-01-01')
LOAD_START = pd.Timestamp('2022-12-01')
CODE_FILES = ['score_freddie_rebuild.py', 'calibrate_freddie_rebuild.py',
    'pathb_prediction_diagnostics.py', 'pathb_cohort_validation.py',
    'cohort_history.py', 'literature_hazard.py', 'stock_flow_accounting_comparison.py',
    'config.py', 'run_freddie_rebuild.py', 'combine_freddie_rebuild.py',
    'freddie_raw_quarter_audit.py']
PANEL_COLUMNS = KEYS + ['period', 'reporting_period', 'mean_loan_age',
    'exposure_upb', 'orig_upb_sum', 'cohort_original_upb', 'burnout', 'prepaid_upb']
SAMPLE_COLUMNS = KEYS + ['loan_id', 'fico', 'orig_ltv', 'original_loan_term',
    'reporting_period', 'initial_burnout', 'burnout_denominator_multiplier']


def recorded_choices(parameter_freeze, recorded_result, macro):
    """Bind frozen choices to the saved scored result; no new selection."""
    freeze = json.loads(parameter_freeze.read_text())
    result = json.loads(recorded_result.read_text())
    if result.get('parameter_freeze_sha256') != digest(parameter_freeze):
        raise ValueError('Recorded result does not bind the supplied parameter freeze')
    if (freeze.get('selection_start') != '2023-01-01'
            or freeze.get('selection_end') != '2023-12-01'
            or freeze.get('annual_floor_grid') != [0., .02, .035, .04991]
            or freeze.get('psa_grid') != [50., 75., 100.]
            or result.get('evaluation_start') != str(START.date())
            or result.get('evaluation_end') != str(END.date())):
        raise ValueError('Recorded candidate grid or date window differs from the frozen comparison')
    selected = freeze.get('selected')
    if (not isinstance(selected, dict) or set(selected) != {'floor_only', 'floor_psa'}
            or result.get('selected_parameters') != selected
            or any(p.get('annual_floor') != .035 or p.get('psa') != 100.
                   for p in selected.values())):
        raise ValueError('Recorded selected parameters differ; do not retune corrected candidates')
    expected = freeze.get('input_sha256', {}).get(MACRO_REFERENCE)
    if (not expected or expected != result.get('input_sha256', {}).get(MACRO_REFERENCE)
            or digest(macro) != expected):
        raise ValueError('Frozen conditioning macro hash does not match recorded inputs')
    return {'original': {'annual_floor': .04991, 'psa': 100.},
            **{name: {'annual_floor': p['annual_floor'], 'psa': p['psa']}
               for name, p in selected.items()}}


def conditioning_rates(path):
    macro = pd.read_parquet(path, columns=['MORTGAGE30US'])
    if (not isinstance(macro.index, pd.DatetimeIndex) or macro.index.hasnans
            or macro.index.tz is not None or not macro.index.is_monotonic_increasing
            or macro.index.to_period('M').duplicated().any()):
        raise ValueError('Frozen macro requires unique ordered monthly dates')
    rates = macro.MORTGAGE30US.groupby(macro.index.to_period('M')).last() / 100.
    required = pd.period_range(START, END, freq='M')
    values = rates.reindex(required).to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError('Missing, nonfinite or nonpositive evaluation conditioning rate')
    return rates.reindex(required)


def panel_identity(path, expected_rows):
    validate_panel_identity(path, corrected=True, expected_rows=expected_rows)
    keys = pd.read_parquet(path, columns=KEYS + ['period', 'reporting_period'])
    if (keys.isna().any().any() or not pd.api.types.is_datetime64_any_dtype(keys.period)
            or not np.isfinite(keys.coupon).all() or (keys.coupon <= 0).any()
            or not np.equal(keys.vintage, np.floor(keys.vintage)).all()
            or not keys.period.dt.is_month_start.all()
            or not (keys.period.dt.strftime('%Y%m') == keys.reporting_period.astype(str)).all()):
        raise ValueError('Panel identity/date columns are missing, inconsistent or invalid')


def load_panel(path):
    """Only declared dates reach the outcome reader, after the identity gate."""
    data = pd.read_parquet(path, columns=PANEL_COLUMNS, filters=[
        ('period', '>=', LOAD_START.to_pydatetime()), ('period', '<=', END.to_pydatetime())])
    data['period'] = data.period.astype('datetime64[ns]')
    if (not np.isfinite(data.exposure_upb).all() or (data.exposure_upb < 0).any()
            or not data.period.between(LOAD_START, END).all()):
        raise ValueError('Invalid source exposure or outcome date')
    data['cell'] = data[KEYS].astype(str).agg('|'.join, axis=1)
    return data


def sample_covariates(path, combined):
    sample = pd.read_parquet(path, columns=SAMPLE_COLUMNS)
    required = sample[['coupon', 'fico', 'orig_ltv', 'initial_burnout',
                       'burnout_denominator_multiplier']].to_numpy(dtype=float)
    if (len(sample) != combined['sample_n']
            or sample.loan_id.nunique() != combined['sample_unique_ids']
            or sample.drop_duplicates().loan_id.duplicated().any()
            or sample.isna().any().any() or not np.isfinite(required).all()
            or not (sample.original_loan_term == 360).all()
            or not (sample.reporting_period.astype(str) == '202205').all()
            or not sample.fico.between(300, 850).all()
            or not sample.orig_ltv.between(1, 200).all()
            or not sample.initial_burnout.between(0, 1).all()
            or (sample.burnout_denominator_multiplier <= 0).any()
            or (sample.coupon <= 0).any()):
        raise ValueError('Corrected sample lacks valid exact-May terms, covariates or fixed history')
    return make_covariates(sample)


def evaluate(panel, covariates, rates, parameters):
    usable, exclusions = prepare_exposures(panel)
    baseline = fit_baseline(usable)
    pre = panel[panel.period == PRE].set_index('cell')
    eligible = set(baseline) & set(pre.index) & set(covariates.index)
    input_rows = panel[panel.period.between(START, END)]
    raw = usable[usable.period.between(START, END)].copy()
    scored = raw[raw.cell.isin(eligible)].copy()
    if scored.empty:
        raise ValueError('No common supported evaluation rows')
    cells = sorted(scored.cell.unique())
    state = pre.loc[cells].copy()
    if (not np.isfinite(state.mean_loan_age).all() or (state.mean_loan_age < 0).any()):
        raise ValueError('Historical mean age must be finite and nonnegative')
    prediction_initial_state(state)
    # A complete calendar makes latent updates independent of missing/invalid
    # observed scoring rows. It carries no evaluation outcome or exposure.
    calendar = pd.MultiIndex.from_product(
        [cells, pd.date_range(START, END, freq='MS')], names=['cell', 'period']).to_frame(index=False)
    calendar['coupon'] = calendar.cell.map(state.coupon)
    predictions = calendar.copy()
    scored['base'] = scored.cell.map(baseline)
    for family, p in parameters.items():
        for leg, beta in [('off', 0.), ('on', RESPONSE_BETA)]:
            name = family + '_' + leg
            path = predict_path(calendar, state, covariates.loc[cells], rates,
                p['annual_floor'], p['psa'], beta)
            predictions[name] = path.hazard
            predictions[name + '_floor_bound'] = path.floor_bound
            predictions[name + '_predicted_burnout'] = path.predicted_burnout
    scored = scored.merge(predictions.drop(columns='coupon'), on=['cell', 'period'],
                          how='left', validate='one_to_one')
    names = ['base'] + [name + '_' + leg for name in parameters for leg in ('off', 'on')]
    aggregate = {name: strict_score(scored.opening_exposure, scored.prepaid_upb, scored[name])
                 for name in names}
    scored['coupon_vintage'] = scored[['vintage', 'coupon']].astype(str).agg('|'.join, axis=1)
    scored['halfyear'] = scored.period.dt.year.astype(str) + 'H' + np.where(scored.period.dt.month <= 6, '1', '2')
    groups = {group: {name: diagnose_groups(scored, group, name) for name in names}
              for group in ('coupon_vintage', 'halfyear')}
    floor_groups = {name: diagnose_groups(scored, name + '_floor_bound', name)
                    for name in names if name != 'base'}
    raw_exposure, kept_exposure = raw.opening_exposure.sum(), scored.opening_exposure.sum()
    raw_events, kept_events = raw.prepaid_upb.sum(), scored.prepaid_upb.sum()
    support = dict(input_rows=len(input_rows), input_cells=int(input_rows.cell.nunique()),
        input_months=int(input_rows.period.nunique()), usable_rows=len(raw),
        usable_cells=int(raw.cell.nunique()), retained_rows=len(scored),
        retained_cells=len(cells), retained_months=int(scored.period.nunique()),
        no_training_rows=int((~raw.cell.isin(baseline)).sum()),
        no_december_state_rows=int((~raw.cell.isin(pre.index)).sum()),
        no_covariate_rows=int((~raw.cell.isin(covariates.index)).sum()),
        any_support_exclusion_rows=len(raw) - len(scored),
        usable_exposure_b_months=float(raw_exposure / 1e9),
        retained_exposure_b_months=float(kept_exposure / 1e9),
        usable_observed_b=float(raw_events / 1e9), retained_observed_b=float(kept_events / 1e9),
        exposure_retained_fraction=float(kept_exposure / raw_exposure),
        observed_principal_retained_fraction=float(kept_events / raw_events) if raw_events > 0 else None,
        denominator='Usable evaluation rows after lag/exposure/numerator exclusions and before support restrictions',
        qualification='Support-reason counts overlap. Missing/noncontiguous opening exposure is unknown, not zero exposure.')
    return dict(aggregate=aggregate, exclusions=exclusions, support=support,
        groups=groups, floor_diagnostics=floor_groups,
        prediction_calendar_rows=len(calendar)), scored, predictions


def run(*, root, macro, parameter_freeze, recorded_result, output):
    root, macro, parameter_freeze, recorded_result, output = [Path(p).resolve() for p in
        (root, macro, parameter_freeze, recorded_result, output)]
    if output.exists():
        raise FileExistsError('Preserve the existing attempt and choose a new scoring output directory')
    for protected in (HERE / 'data', root / 'quarters', root / 'combined'):
        if output == protected or protected in output.parents:
            raise ValueError('Scoring output must be separate from protected inputs')
    combined, hashes = validated_combined(root)
    for path in (macro, parameter_freeze, recorded_result, SPEC):
        hashes[str(path)] = digest(path)
    code_hashes = {str(HERE / name): digest(HERE / name) for name in CODE_FILES}
    code_hashes[str(ROOT / 'common/qt_window.py')] = digest(ROOT / 'common/qt_window.py')
    parameters = recorded_choices(parameter_freeze, recorded_result, macro)
    rates = conditioning_rates(macro)
    panel_path = root / 'combined/cohort_month_panel.parquet'
    panel_identity(panel_path, combined['panel_rows'])
    verify_hashes(dict(hashes, **code_hashes))
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        input_sha256=hashes, code_sha256=code_hashes, spec_sha256=digest(SPEC),
        environment=dict(python=sys.version, pandas=pd.__version__, numpy=np.__version__),
        parameters=parameters, parameter_selection_performed=False,
        response_coefficients={'off': 0., 'on': RESPONSE_BETA},
        baseline_training=['2023-01-01', '2023-12-01'], initialization='2023-12-01',
        evaluation_start=str(START.date()), evaluation_end=str(END.date()),
        rate_convention='Saved monthly MORTGAGE30US percent divided by 100; no weekly-rate replacement',
        population=combined['population'])
    write_json(output / 'input_manifest.json', manifest)
    try:
        panel = load_panel(panel_path)
        cov = sample_covariates(root / 'combined/loan_sample.parquet', combined)
        result, scored, predictions = evaluate(panel, cov, rates, parameters)
        verify_hashes(dict(hashes, **code_hashes))
        scored.to_parquet(output / 'scores.parquet', index=False)
        predictions.to_parquet(output / 'predictions.parquet', index=False)
        pd.DataFrame.from_dict(result['aggregate'], orient='index').rename_axis('candidate').to_csv(output / 'scorecard.csv')
        for path in output.iterdir():
            path.chmod(0o600)
        result.update(design='Corrected-input retrospective conditional comparison; previously examined outcomes',
            input_manifest_sha256=digest(output / 'input_manifest.json'),
            parameter_selection_performed=False, parameters=parameters,
            baseline_training=manifest['baseline_training'], initialization=manifest['initialization'],
            evaluation_start=manifest['evaluation_start'], evaluation_end=manifest['evaluation_end'],
            source_inputs_unchanged=True, population=combined['population'],
            sampling=dict(rows=combined['sample_n'], unique_source_ids=combined['sample_unique_ids'],
                replacement_rows=combined['sample_n'] - combined['sample_unique_ids'],
                convention='Preserve the verified combined draw, including declared sampling with replacement'),
            zero_note_rate_excluded_loans=combined['zero_note_rate_excluded_loans'],
            zero_note_rate_excluded_original_upb=combined['zero_note_rate_excluded_original_upb'],
            payoff_assumptions=combined['original_payoff_assumptions'],
            quarter_cash_ratio_audits=combined['quarter_cash_ratio_audits_by_quarter'],
            identity_exceptions_by_quarter=combined['identity_exceptions_by_quarter'],
            identity_exception_totals=combined['identity_exception_totals'],
            output_sha256={p.name: digest(p) for p in output.iterdir() if p.is_file()},
            limitations=[
                'Previously examined evaluation outcomes; not a new holdout.',
                'Conditional on realized opening exposure and mortgage rates, not a forward balance forecast.',
                'Voluntary payoff principal only; scheduled/default/curtailment cash flows are not scored.',
                'Fixed sample covariates and advancing pre-period mean ages are cohort approximations.',
                'Original note rates and terms do not validate the current contracts of modified loans.',
                'Missing or invalid observed rows are excluded from scores, not from latent monthly state updates.',
                'Source/accounting corrections and a known360FRM population change jointly affect comparisons.',
                'No new parameter choice, causal response identification, sale/refinance split, or full-SOMA transport claim.'])
        write_json(output / 'results.json', result)
        (output / 'results.json').chmod(0o600)
        return result
    except Exception as exc:
        write_json(output / 'failed.json', dict(error_type=type(exc).__name__, error=str(exc),
            failed_utc=datetime.now(timezone.utc).isoformat(), results_written=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'macro', 'parameter-freeze', 'recorded-result', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = run(**vars(args))
    print(json.dumps(dict(status='passed', output=str(args.output),
        rows=result['support']['retained_rows'], parameter_selection_performed=False), indent=2))
