"""Offline, gated response-off/on simulation on the corrected Freddie inputs.

Uses the existing engine with an explicit audited matrix and full frozen macro.
No source, network, calibration, or production-result write is performed here.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import polars as pl

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for directory in (ROOT, HERE):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
os.environ.setdefault('FRED_API_KEY', 'offline-corrected-pair-no-network')

from hazard.calibrate_freddie_rebuild import validated_combined, verify_hashes
from run_freddie_rebuild import digest, write_json
from agents import STATE_TO_CODE
import competing_risks as cr
import literature_hazard as lh
import microsim_engine as engine
from macro import build_empirical_metrics
from config import MARKOV_STATES

SPEC = ROOT / 'specs/SPEC_2026-10-12_corrected_pair_wrapper.md'
BENCHMARK_B = 764.7482532227002
INITIAL_HOLDINGS_B = 2707.446
QT_INDEX = pd.date_range('2022-06-30', '2025-11-30', freq='ME')
PARAMETERS = dict(annual_floor=.04991, psa=100., floor_form='max',
                  prepay_mode='fractional', moving_share='full', regime='US',
                  seed=42, response_off_pct=0., response_on_pct=6.5,
                  allow_legacy_inputs=False, soma_reweighting=False)
CODE_FILES = [Path(__file__), HERE / 'calibrate_freddie_rebuild.py',
              HERE / 'run_freddie_rebuild.py', HERE / 'microsim_engine.py',
              HERE / 'competing_risks.py', HERE / 'agents.py',
              HERE / 'literature_hazard.py', HERE / 'macro.py', HERE / 'config.py',
              HERE / 'rate_gap.py', HERE / 'markov.py', HERE / 'loan_sample.py',
              HERE / 'freddie_raw_quarter_audit.py',
              ROOT / 'common/qt_window.py']


def read_json(path):
    return json.loads(Path(path).read_text())


def validate_conventions():
    """Do not silently inherit an interactive sensitivity's patched behavior."""
    coefficients = {'beta_burnout': -.5, 'beta_fico': -.15, 'beta_ltv': .10,
                    'h0_default_monthly': .0003, 'gamma_rate_stress': 2.,
                    'gamma_fico': -.20, 'gamma_ltv': .25}
    if (lh.FLOOR_MODE != 'max' or cr.PREPAY_MODE != 'fractional'
            or lh.h0_psa.__defaults__ != (100.,)
            or lh.baseline_hazard.__defaults__ != ('psa',)
            or lh.rothstein_beta1.__defaults__ != (.06,)
            or lh.LITERATURE_COEFS != coefficients
            or cr.prepay_hazard is not lh.prepay_hazard
            or engine.monthly_step is not cr.monthly_step
            or engine.QT_START != pd.Timestamp('2022-06-01')
            or engine.QT_END != pd.Timestamp('2025-12-01')):
        raise ValueError('Active hazard convention differs from the frozen main pair')


def validate_recorded_inputs(macro_path, parameter_freeze, empirical_csv,
                             input_inventory, benchmark_reference):
    inventory = read_json(input_inventory)
    comparator = inventory['archived_empirical_comparator']
    references = [(macro_path, inventory['frozen_macro']),
                  (parameter_freeze, inventory['recorded_selection']),
                  (empirical_csv, comparator),
                  (benchmark_reference, comparator['monthly_rebuild_reference'])]
    for path, record in references:
        if Path(record['path']).resolve() != path or digest(path) != record['sha256']:
            raise ValueError('Recorded downstream inventory path/hash mismatch: ' + str(path))
    freeze = read_json(parameter_freeze)
    recorded_macro = {str((ROOT / key).resolve()): value for key, value in freeze['input_sha256'].items()}
    if recorded_macro.get(str(macro_path)) != digest(macro_path):
        raise ValueError('Frozen macro is not bound to the recorded parameter freeze')
    if (freeze.get('annual_floor_grid') != [0., .02, .035, .04991]
            or freeze.get('psa_grid') != [50., 75., 100.]
            or freeze.get('selection_start') != '2023-01-01'
            or freeze.get('selection_end') != '2023-12-01'
            or set(freeze.get('selected', {})) != {'floor_only', 'floor_psa'}
            or any(row.get('annual_floor') != .035 or row.get('psa') != 100.
                   for row in freeze['selected'].values())):
        raise ValueError('Recorded candidate/selection boundaries changed')
    return freeze


def load_macro(path):
    macro = pd.read_parquet(path)
    if (not isinstance(macro.index, pd.DatetimeIndex) or macro.index.tz is not None
            or macro.index.has_duplicates or not macro.index.is_monotonic_increasing
            or not macro.index.is_month_end.all()):
        raise ValueError('Frozen macro requires unique, ordered, timezone-free month ends')
    fields = ['WSHOMCB', 'MORTGAGE30US', 'ACTLISCOUUS', 'UMCSENT']
    if not set(fields).issubset(macro.columns) or not QT_INDEX.isin(macro.index).all():
        raise ValueError('Frozen macro lacks the full 42-month QT window or required columns')
    if not np.isfinite(macro[fields].to_numpy(dtype=float)).all():
        raise ValueError('Frozen macro contains nonfinite conditioning inputs')
    if (macro.WSHOMCB <= 0).any() or (macro.MORTGAGE30US <= 0).any():
        raise ValueError('Frozen macro holdings and mortgage rates must be positive')
    nearest = macro.index.get_indexer([pd.Timestamp('2022-06-01')], method='nearest')[0]
    date = macro.index[nearest]
    holdings = float(macro.iloc[nearest].WSHOMCB) / 1000.
    if date != pd.Timestamp('2022-05-31') or not np.isclose(holdings, INITIAL_HOLDINGS_B, rtol=0, atol=1e-9):
        raise ValueError('Frozen macro changes the May-31 engine initialization')
    return macro, dict(date=date.strftime('%Y-%m-%d'), holdings_b=holdings)


def empirical_replay(macro, csv_path, benchmark_reference):
    archive = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    fields = ['MORTGAGE30US', 'Actual_Monthly_Rolloff_Billions',
              'QT_Target_Billions', 'Extension_Delta_Billions']
    if (not isinstance(archive.index, pd.DatetimeIndex) or not archive.index.equals(QT_INDEX)
            or not set(fields).issubset(archive.columns)
            or not np.isfinite(archive[fields].to_numpy(dtype=float)).all()):
        raise ValueError('Archived empirical comparator requires all 42 finite monthly rows')
    reference = read_json(benchmark_reference)
    expected_keys = {date.strftime('%Y-%m') for date in QT_INDEX}
    monthly = reference.get('committed_method_monthly_diff_b', {})
    if reference.get('status') != 'OK' or not expected_keys.issubset(monthly):
        raise ValueError('Saved monthly benchmark lacks the complete verified QT window')
    reference_values = np.array([monthly[date.strftime('%Y-%m')] for date in QT_INDEX], dtype=float)
    if (not np.isfinite(reference_values).all() or not np.allclose(reference_values,
            archive.Actual_Monthly_Rolloff_Billions, rtol=0, atol=1e-8)):
        raise ValueError('Archived monthly runoff disagrees with the saved monthly benchmark')
    # Explicit SOMA rolloff prevents the function's WSHOMCB difference fallback.
    full = build_empirical_metrics(macro, soma_rolloff=archive.Actual_Monthly_Rolloff_Billions)
    replay = full.loc[QT_INDEX].copy()
    for field in fields:
        tolerance = 1e-10 if field == 'MORTGAGE30US' else 1e-8
        if not np.allclose(replay[field], archive[field], rtol=0, atol=tolerance):
            raise ValueError('Monthly empirical benchmark replay differs: ' + field)
    denominator = float(replay.Extension_Delta_Billions.sum())
    if not np.isclose(denominator, BENCHMARK_B, rtol=0, atol=1e-8):
        raise ValueError('Empirical denominator differs from the frozen 764.7482532227002 billion')
    return replay, dict(denominator_b=denominator, months=len(replay),
        first_date='2022-06-30', last_date='2025-11-30', monthly_equality_passed=True,
        excluded_reference_months=sorted(set(monthly) - expected_keys),
        runoff_source='archived SOMA series supplied explicitly',
        cpr_convention='hazard scheduled amortization; archived ABM CPR not used',
        max_monthly_reference_difference_b=float(np.max(np.abs(reference_values - archive.Actual_Monthly_Rolloff_Billions))))


class AccountingRecorder:
    """Observe an existing step; never alter its arguments, results or pool."""
    def __init__(self, step):
        self.step = step
        self.rows = []

    def __call__(self, pool, *args, **kwargs):
        active = pool.active_mask.copy()
        opening, total = pool.total_exposure(), float(pool.balance.sum())
        result = self.step(pool, *args, **kwargs)
        closing, closing_total = pool.total_exposure(), float(pool.balance.sum())
        terminal = active & ~pool.active_mask
        default = terminal & np.isin(pool.state_code, [STATE_TO_CODE['Defaulted'], STATE_TO_CODE['Liquidated']])
        default_transfer = float(pool.balance[default].sum())
        other_transfer = float(pool.balance[terminal & ~default].sum())
        voluntary, scheduled = float(result['prepay_upb']), float(result['sched_amt'])
        residual = opening - closing - voluntary - scheduled - default_transfer - other_transfer
        total_residual = total - closing_total - voluntary - scheduled
        values = [opening, closing, total, closing_total, voluntary, scheduled, default_transfer, other_transfer]
        if (not np.isfinite(values).all() or min(values) < -1e-5
                or abs(residual) > max(1e-5, abs(opening) * 1e-12)
                or abs(total_residual) > max(1e-5, abs(total) * 1e-12)
                or not np.isclose(result['settled_b'], voluntary, rtol=1e-12, atol=1e-5)):
            raise ValueError('Monthly active/total principal accounting does not reconcile')
        self.rows.append(dict(opening_active_b=opening / 1e9, closing_active_b=closing / 1e9,
            opening_total_b=total / 1e9, closing_total_b=closing_total / 1e9,
            voluntary_b=voluntary / 1e9, scheduled_b=scheduled / 1e9,
            default_transfer_b=default_transfer / 1e9, other_terminal_transfer_b=other_transfer / 1e9,
            cash_principal_b=(voluntary + scheduled) / 1e9,
            default_cash_b=0., curtailment_b=0., additions_b=0.,
            active_residual_b=residual / 1e9, total_residual_b=total_residual / 1e9))
        return result


@contextmanager
def recorded_leg():
    previous_floor, previous_step = lh.INVOLUNTARY_CPR_ANNUAL, engine.monthly_step
    recorder = AccountingRecorder(previous_step)
    lh.INVOLUNTARY_CPR_ANNUAL = PARAMETERS['annual_floor']
    engine.monthly_step = recorder
    try:
        yield recorder
    finally:
        engine.monthly_step = previous_step
        lh.INVOLUNTARY_CPR_ANNUAL = previous_floor


def validate_model_inputs(loans, matrix, combined):
    required = {'loan_id', 'original_loan_term', 'reporting_period', 'balance', 'state'}
    if (not required.issubset(loans.columns) or len(loans) != combined['sample_n']
            or loans['loan_id'].n_unique() != combined['sample_unique_ids'] or loans['loan_id'].null_count()
            or loans.filter((pl.col('original_loan_term') != 360) | (pl.col('reporting_period') != '202205')
                | (pl.col('balance') <= 0) | (~pl.col('state').is_in(MARKOV_STATES))).height
            or loans.select(pl.any_horizontal(pl.col(c).is_null() for c in required)).to_series().any()):
        raise ValueError('Combined loan sample violates the known-360 May-2022 input contract')
    unique_ids = loans['loan_id'].n_unique()
    if loans.unique().height != unique_ids:
        raise ValueError('Conflicting complete records for repeated loan IDs in the sample')
    if (matrix.attrs.get('estimator') != 'identified_monthly_loan_transitions'
            or matrix.attrs.get('estimation_end') != '202205'
            or not matrix.index.is_unique or not matrix.columns.is_unique
            or set(matrix.index) != set(MARKOV_STATES) or set(matrix.columns) != set(MARKOV_STATES)
            or not np.isfinite(matrix.to_numpy(dtype=float)).all()
            or (matrix.to_numpy(dtype=float) < 0).any()
            or not np.allclose(matrix.sum(axis=1), 1., rtol=1e-12, atol=1e-12)):
        raise ValueError('Combined transition matrix lacks valid identified pre-QT probabilities')
    return dict(sample_rows=len(loans), unique_loan_ids=unique_ids,
                repeated_draw_rows=len(loans) - unique_ids,
                maximum_id_multiplicity=int(loans.group_by('loan_id').len()['len'].max()))


def run(*, root, macro_path, parameter_freeze, empirical_csv, input_inventory,
        benchmark_reference, output):
    root, macro_path, parameter_freeze, empirical_csv, input_inventory, benchmark_reference, output = [
        Path(p).resolve() for p in (root, macro_path, parameter_freeze, empirical_csv,
                                   input_inventory, benchmark_reference, output)]
    if output.exists():
        raise FileExistsError('Preserve prior outputs and choose a new paired-run directory')
    for protected in (HERE / 'data', root / 'quarters', root / 'combined'):
        if output == protected or protected in output.parents:
            raise ValueError('New paired outputs must be separate from protected inputs')
    validate_conventions()
    combined, hashes = validated_combined(root)
    for path in (macro_path, parameter_freeze, empirical_csv, input_inventory, benchmark_reference, SPEC):
        hashes[str(path)] = digest(path)
    code_hashes = {str(path): digest(path) for path in CODE_FILES}
    freeze = validate_recorded_inputs(macro_path, parameter_freeze, empirical_csv,
                                     input_inventory, benchmark_reference)
    macro, initialization = load_macro(macro_path)
    verify_hashes(dict(hashes, **code_hashes))
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    (output / 'spec_frozen.md').write_bytes(SPEC.read_bytes())
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        input_sha256=hashes, code_sha256=code_hashes, spec_sha256=digest(SPEC),
        parameters=PARAMETERS, initialization=initialization,
        recorded_retrospective_selection=freeze['selected'],
        recorded_selection_applied=False,
        environment={'python': sys.version, 'numpy': np.__version__, 'pandas': pd.__version__, 'polars': pl.__version__})
    write_json(output / 'input_manifest.json', manifest)
    try:
        empirical, benchmark = empirical_replay(macro, empirical_csv, benchmark_reference)
        empirical.to_parquet(output / 'empirical_replay.parquet')
        loans = pl.read_parquet(root / 'combined/loan_sample.parquet')
        matrix = pd.read_parquet(root / 'combined/markov_transition_matrix.parquet')
        multiplicity = validate_model_inputs(loans, matrix, combined)
        paths, accounts, legs = {}, {}, {}
        for name, response in [('off', 0.), ('on', 6.5)]:
            validate_conventions()
            with recorded_leg() as recorder:
                results = engine.run_qt_microsim(loan_sample=loans, macro=macro,
                    transition_matrix=matrix, regimes=('US',), seed=42, p_q_shock_pct=response,
                    output=output / f'{name}_simulation.parquet', allow_legacy_inputs=False)
            sim = results['US']
            if not sim.index.equals(QT_INDEX) or len(recorder.rows) != len(QT_INDEX):
                raise ValueError('Simulation and accounting must cover exactly 42 QT months')
            account = pd.DataFrame(recorder.rows, index=QT_INDEX)
            scale = np.where(account.closing_active_b > 0,
                macro.loc[QT_INDEX].WSHOMCB.to_numpy() / 1000. / np.maximum(account.closing_active_b, 1e-6), 1.)
            account['reporting_scale'] = scale
            account['production_principal_b'] = account.cash_principal_b * scale
            account['production_voluntary_b'] = account.voluntary_b * scale
            account['production_scheduled_b'] = account.scheduled_b * scale
            if (not np.isfinite(sim.select_dtypes('number').to_numpy()).all()
                    or not np.isfinite(account.to_numpy()).all()
                    or not np.allclose(-sim.simulated_rolloff_b, account.production_principal_b, rtol=1e-12, atol=1e-8)
                    or not np.allclose(sim.weighted_settled_b, account.production_voluntary_b, rtol=1e-12, atol=1e-8)
                    or not np.allclose(sim.weighted_sched_b, account.production_scheduled_b, rtol=1e-12, atol=1e-8)):
                raise ValueError('Engine reporting and captured principal accounting disagree')
            account.to_parquet(output / f'{name}_accounting.parquet')
            paths[name], accounts[name] = sim, account
            legs[name] = dict(response_pct=response,
                reported_extension_b=float((sim.simulated_rolloff_b - empirical.QT_Target_Billions).sum()),
                production_principal_b=float(account.production_principal_b.sum()),
                closed_pool_cash_principal_b=float(account.cash_principal_b.sum()),
                voluntary_b=float(account.voluntary_b.sum()), scheduled_b=float(account.scheduled_b.sum()),
                default_transfer_b=float(account.default_transfer_b.sum()),
                other_terminal_transfer_b=float(account.other_terminal_transfer_b.sum()), default_cash_b=0.,
                max_active_identity_error_b=float(account.active_residual_b.abs().max()),
                max_total_identity_error_b=float(account.total_residual_b.abs().max()))
        verify_hashes(dict(hashes, **code_hashes))
        marginal = legs['off']['production_principal_b'] - legs['on']['production_principal_b']
        result = dict(created_utc=datetime.now(timezone.utc).isoformat(),
            scope='Conditional corrected-input Freddie main pair; unchanged imported response and floor',
            initialization=initialization, parameters=PARAMETERS, empirical_benchmark=benchmark,
            legs=legs, reported_marginal_b=marginal, reported_marginal_pp=marginal / benchmark['denominator_b'] * 100.,
            closed_pool_cash_marginal_b=legs['off']['closed_pool_cash_principal_b'] - legs['on']['closed_pool_cash_principal_b'],
            parameter_selection_performed=False, source_inputs_unchanged=True,
            sampling_multiplicity=multiplicity,
            population=combined['population'], original_payoff_assumptions=combined['original_payoff_assumptions'],
            zero_note_rate_excluded_loans=combined['zero_note_rate_excluded_loans'],
            zero_note_rate_excluded_original_upb=combined['zero_note_rate_excluded_original_upb'],
            quarter_cash_ratio_audits_by_quarter=combined['quarter_cash_ratio_audits_by_quarter'],
            identity_exceptions_by_quarter=combined['identity_exceptions_by_quarter'],
            identity_exception_totals=combined['identity_exception_totals'],
            limitations=[
                'Original note rates and original 360-month terms do not validate modified contracts.',
                'Observed-holdings monthly reporting scale is distinct from closed-pool cash accounting.',
                'Default/other transfers retain claims; no recovery cash, curtailment or additions are modeled.',
                'Source/accounting corrections and population changes are not an isolated software effect.',
                'Ordinary Freddie sample; no SOMA reweighting, causal estimate or full-SOMA representativeness.',
                'No new parameter selection, headline promotion, paper replacement or Fannie original-source validation.'],
            output_sha256={p.name: digest(p) for p in output.iterdir() if p.is_file()})
        write_json(output / 'results.json', result)
        return result
    except BaseException as exc:
        write_json(output / 'failed.json', dict(error_type=type(exc).__name__, error=str(exc),
            failed_utc=datetime.now(timezone.utc).isoformat(), results_written=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'macro-path', 'parameter-freeze', 'empirical-csv',
                 'input-inventory', 'benchmark-reference', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = run(**vars(args))
    print(json.dumps({'status': 'passed', 'output': str(args.output),
                      'reported_marginal_b': result['reported_marginal_b'],
                      'headline_updated': False}, indent=2))
