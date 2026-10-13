"""Replay the saved Freddie floor grid, then calculate it on verified inputs.

This offline stage has no parameter selection and no production-data defaults.
Every input and the new output directory must be supplied explicitly. It does
not start source reconstruction, retrieve rates, or update the paper/headline.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
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
os.environ.setdefault('FRED_API_KEY', 'offline-calibration-no-network')

from hazard.fannie_floor_read import prep
from hazard.fannie_age_rebuild_audit import grids, verify_grid_parity
from run_freddie_rebuild import QUARTERS, SPEC, digest, validate_completed, write_json

RATE_URL = ('https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US'
            '&cosd=2016-12-01&coed=2025-10-31')
COMBINED_OUTPUTS = {'cohort_month_panel.parquet', 'loan_sample.parquet',
                    'markov_transition_matrix.parquet', 'transition_diagnostics.json'}
KEYS = ['vintage', 'coupon', 'fico_bucket', 'ltv_bucket', 'reporting_period']
CODE_FILES = ['calibrate_freddie_rebuild.py', 'fannie_floor_read.py',
              'fannie_age_rebuild_audit.py', 'run_freddie_rebuild.py',
              'combine_freddie_rebuild.py', 'freddie_raw_quarter_audit.py']
POPULATION = 'known360FRM; original vintage2017–2021'
WINDOWS = {'out_of_window_2017_2019', 'in_window_2023_2024',
           'in_window_deep_OTM_validation'}


def read_json(path):
    return json.loads(Path(path).read_text())


def verify_hashes(hashes):
    for path, expected in hashes.items():
        if digest(path) != expected:
            raise ValueError('Frozen input or code changed: ' + path)


def validated_combined(root):
    """Validate local receipts and their links, without reopening any original."""
    missing = [q for q in QUARTERS if not (root / 'quarters' / q / 'completed.json').is_file()]
    if missing:
        raise FileNotFoundError('Missing verified quarter completions: ' + ', '.join(missing))
    hashes, reports = {}, {}
    for quarter in QUARTERS:
        path = root / 'quarters' / quarter
        receipt = validate_completed(path)
        hashes[str(path / 'completed.json')] = digest(path / 'completed.json')
        hashes.update({str(path / name): value for name, value in receipt['output_sha256'].items()})
        reports[quarter] = read_json(path / 'rebuilt/report.json')
    frozen_spec = root / 'spec_frozen.md'
    if digest(frozen_spec) != digest(SPEC):
        raise ValueError('Source specification differs from the frozen rebuild protocol')
    hashes[str(frozen_spec)] = digest(frozen_spec)
    combined = root / 'combined'
    report_path = combined / 'report.json'
    report = read_json(report_path)
    if (report.get('quarters') != QUARTERS or report.get('complete_freddie_manifest') is not True
            or report.get('population') != POPULATION or report.get('cutoff') != '202509'
            or report.get('transition_end') != '202205' or report.get('sample_month') != '202205'):
        raise ValueError('Combined report lacks the complete frozen population/cutoff manifest')
    cash_audits={q:reports[q].get('quarter_cash_ratio_audit') for q in QUARTERS}
    if (report.get('quarter_cash_ratio_audits_by_quarter')!=cash_audits
            or report.get('partial_cohort_overrun_count')!=sum((v or {}).get('overrun_cohort_count',0) for v in cash_audits.values())
            or report.get('complete_cohort_burnout_bounds_verified') is not True):
        raise ValueError('Combined source-partition audit or complete-cohort bound is missing')
    identity_audits = {q: reports[q].get('identity_exceptions') for q in QUARTERS}
    identity_totals = {k: sum((v or {}).get(k, 0) for v in identity_audits.values())
        for k in ['original_records', 'performance_rows', 'eligible_original_loans', 'eligible_original_upb']}
    if (report.get('identity_exceptions_by_quarter', dict.fromkeys(QUARTERS)) != identity_audits
            or report.get('identity_exception_totals', dict.fromkeys(identity_totals, 0)) != identity_totals):
        raise ValueError('Combined identity exception accounting disagrees with the source quarters')
    report.setdefault('identity_exceptions_by_quarter', identity_audits)
    report.setdefault('identity_exception_totals', identity_totals)
    if set(report.get('output_sha256', {})) != COMBINED_OUTPUTS:
        raise ValueError('Combined report lacks the complete output hash manifest')
    if report.get('source_report_sha256') != {
            q: hashes[str(root / 'quarters' / q / 'rebuilt/report.json')] for q in QUARTERS}:
        raise ValueError('Combined report source hashes do not match verified quarters')
    zero = {q: reports[q].get('zero_note_rate_exclusions',
            dict(enabled=False, known360_count=0, known360_upb=0.)) for q in QUARTERS}
    if (report.get('zero_note_rate_exclusions_by_quarter') != zero
            or report.get('zero_note_rate_excluded_loans') != sum(z['known360_count'] for z in zero.values())
            or report.get('zero_note_rate_excluded_original_upb') != sum(z['known360_upb'] for z in zero.values())):
        raise ValueError('Combined exclusion accounting disagrees with source quarters')
    assumptions = [dict(quarter=q, **reports[q]['payoff_assumptions']) for q in QUARTERS]
    if (report.get('original_loans') != sum(r['counts']['eligible_original_ids'] for r in reports.values())
            or report.get('original_payoff_assumptions') != assumptions
            or report.get('observed_source_survivors') != sum(r['artifacts']['snapshot.parquet']['rows'] for r in reports.values())):
        raise ValueError('Combined population or payoff accounting disagrees with source quarters')
    for name, expected in report['output_sha256'].items():
        hashes[str(combined / name)] = expected
    hashes[str(report_path)] = digest(report_path)
    verify_hashes(hashes)
    return report, hashes


def frozen_rates(rate_csv, rate_source):
    """Retain the saved weekly-to-within-month-mean convention, including gaps."""
    meta = read_json(rate_source)
    if meta.get('url') != RATE_URL or not meta.get('retrieved_utc'):
        raise ValueError('Frozen rate metadata must identify the saved official FRED response')
    if digest(rate_csv) != meta.get('sha256'):
        raise ValueError('Frozen mortgage-rate hash mismatch')
    data = pd.read_csv(io.BytesIO(rate_csv.read_bytes()))
    if (len(data.columns) != 2 or data.columns[0] not in ('DATE', 'observation_date')
            or data.columns[1] != 'MORTGAGE30US'):
        raise ValueError('Unexpected frozen mortgage-rate CSV schema')
    dates = pd.to_datetime(data.iloc[:, 0], errors='raise')
    if dates.isna().any() or dates.duplicated().any():
        raise ValueError('Missing or duplicate weekly mortgage-rate dates')
    values = pd.to_numeric(data.MORTGAGE30US, errors='coerce') / 100.
    if np.isinf(values).any() or (values.dropna() <= 0).any():
        raise ValueError('Nonfinite or nonpositive weekly mortgage rates')
    monthly = values.groupby(dates.dt.strftime('%Y%m')).mean().to_dict()
    required = {f'{year}{month:02}' for year in [2017, 2018, 2019, 2023, 2024]
                for month in range(1, 13)}
    if not all(k in monthly and np.isfinite(monthly[k]) and monthly[k] > 0 for k in required):
        raise ValueError('Missing/nonfinite evaluation rates')
    return monthly, meta


def saved_freddie_grid(path):
    """Accept only the two documented historical result schemas."""
    saved = read_json(path)
    if 'books' in saved:
        result = {name: saved['books']['freddie'][name] for name in WINDOWS}
        schema = 'fannie_floor_read.books.freddie'
    elif 'grids' in saved and 'in_window_deep_OTM_validation' in saved:
        result = dict(saved['grids'], in_window_deep_OTM_validation=saved['in_window_deep_OTM_validation'])
        schema = 'out_of_window_floor.grids_and_deep_validation'
    else:
        raise ValueError('Unrecognized saved Freddie floor-grid schema')
    if set(result) != WINDOWS:
        raise ValueError('Saved Freddie grid does not contain all three frozen windows')
    for name, cells in result.items():
        expected = ({f'gap<=-0.02_age>={age}' for age in [12, 24]} if 'deep_OTM' in name else
                    {f'gap<={gap:+.4f}_age>={age}' for gap in [0., -.0025, -.005] for age in [12, 24]})
        if set(cells) != expected:
            raise ValueError('Incomplete or altered saved floor-grid cells: ' + name)
        for key, row in cells.items():
            if not isinstance(row, dict) or not {'cpr_pct', 'exposure_upb', 'n_cohort_months'}.issubset(row):
                raise ValueError('Saved floor-grid numeric fields are missing: ' + name + '/' + key)
            count, exposure, cpr = row['n_cohort_months'], row['exposure_upb'], row['cpr_pct']
            number = lambda x: type(x) in (int, float) and np.isfinite(x)
            if (type(count) is not int or count < 0 or not number(exposure) or exposure < 0
                    or (count == 0 and (exposure != 0 or cpr is not None))
                    or (count > 0 and (exposure <= 0 or not number(cpr) or not 0 <= cpr <= 100))):
                # NaN defeats the legacy absolute-difference comparison. Check
                # its numeric contract before reading either panel's outcomes.
                raise ValueError('Saved floor-grid numeric values are invalid: ' + name + '/' + key)
    return result, schema


def validate_panel_identity(path, *, corrected=False, expected_rows=None):
    # Read identity/date columns first. Outcomes beyond the frozen boundary are
    # never passed into prep, including when an incorrect legacy path is supplied.
    keys = pd.read_parquet(path, columns=KEYS)
    periods = keys.reporting_period.astype(str)
    if (not periods.str.fullmatch(r'20\d{2}(0[1-9]|1[0-2])').all()
            or (periods > '202509').any() or keys.duplicated(KEYS).any()):
        raise ValueError('Invalid, duplicate, or post-cutoff panel cell identity')
    if corrected and (len(keys) != expected_rows or not keys.vintage.between(2017, 2021).all()):
        raise ValueError('Corrected panel identity disagrees with the combined population/row count')


def run(*, root, legacy_panel, saved_grid, rate_csv, rate_source, output):
    root, legacy_panel, saved_grid, rate_csv, rate_source, output = [Path(p).resolve() for p in
        (root, legacy_panel, saved_grid, rate_csv, rate_source, output)]
    if output.exists():
        raise FileExistsError('Preserve the existing attempt and choose a new output directory')
    for protected in (HERE / 'data', root / 'quarters', root / 'combined'):
        if output == protected or protected in output.parents:
            raise ValueError('Calibration output must be separate from protected inputs')
    corrected_panel = root / 'combined/cohort_month_panel.parquet'
    if legacy_panel == corrected_panel:
        raise ValueError('Legacy replay requires the explicit preserved historical panel')
    combined, hashes = validated_combined(root)
    for path in (legacy_panel, saved_grid, rate_csv, rate_source, SPEC):
        hashes[str(path)] = digest(path)
    code_hashes = {str(HERE / name): digest(HERE / name) for name in CODE_FILES}
    monthly, rate_meta = frozen_rates(rate_csv, rate_source)
    saved, saved_schema = saved_freddie_grid(saved_grid)
    verify_hashes(dict(hashes, **code_hashes))
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    manifest = dict(created_utc=datetime.now(timezone.utc).isoformat(),
        scope='Freddie floor-grid replay and corrected-input comparison; no parameter selection',
        input_sha256=hashes, code_sha256=code_hashes, spec_sha256=digest(SPEC),
        source_quarters=QUARTERS, saved_grid_schema=saved_schema,
        environment={'python': sys.version, 'pandas': pd.__version__, 'numpy': np.__version__},
        rate_convention='MORTGAGE30US weekly percent / 100, within-month arithmetic mean',
        frozen_grid={'windows': ['201701–201912', '202301–202412'], 'min_mean_age_months': [12, 24],
                     'maximum_gap_basis_points': [0, -25, -50], 'deep_validation_gap_basis_points': -200})
    write_json(output / 'input_manifest.json', manifest)
    try:
        validate_panel_identity(legacy_panel)
        old_frame = prep(legacy_panel, monthly)
        old_grid = grids(old_frame)
        parity = verify_grid_parity(old_grid, saved)
        replay = dict(parity=parity, saved_grid_schema=saved_schema, grid=old_grid,
                      legacy_rows_after_filter=len(old_frame))
        write_json(output / 'legacy_replay.json', replay)
        # No corrected outcome calculation takes place until the exact saved
        # legacy-grid count, exposure and CPR replay has passed in every cell.
        validate_panel_identity(corrected_panel, corrected=True, expected_rows=combined['panel_rows'])
        corrected = prep(corrected_panel, monthly)
        new_grid = grids(corrected)
        verify_hashes(dict(hashes, **code_hashes))
        result = dict(created_utc=datetime.now(timezone.utc).isoformat(),
            scope=manifest['scope'], input_manifest_sha256=digest(output / 'input_manifest.json'),
            legacy_replay_sha256=digest(output / 'legacy_replay.json'), legacy_replay=replay,
            corrected_grid=new_grid, corrected_rows_after_filter=len(corrected),
            source_inputs_unchanged=True, parameter_selection_performed=False,
            population_comparison={
                'legacy': 'Preserved historical all-term Freddie fixed-rate panel; original source accounting retained',
                'corrected': combined['population'],
                'interpretation': 'Differences jointly reflect source/accounting corrections and population changes; not an isolated software effect',
                'zero_note_rate_excluded_loans': combined['zero_note_rate_excluded_loans'],
                'zero_note_rate_excluded_original_upb': combined['zero_note_rate_excluded_original_upb'],
                'zero_note_rate_exclusions_by_quarter': combined['zero_note_rate_exclusions_by_quarter']},
            payoff_assumptions=combined['original_payoff_assumptions'], rate_source=rate_meta,
            quarter_cash_ratio_audits=combined['quarter_cash_ratio_audits_by_quarter'],
            identity_exceptions_by_quarter=combined['identity_exceptions_by_quarter'],
            identity_exception_totals=combined['identity_exception_totals'],
            complete_cohort_burnout_bounds_verified=True,
            limitations=[
                'Age thresholds apply to cohort mean ages, not individual loans.',
                'Unchanged CPR annualizes payoff/current-end-UPB; exposure totals are dollar-months.',
                'Original-UPB first-observed fallback and nonadjacent prior-balance assumptions remain explicit.',
                'Evaluation windows were previously examined; these are not new holdouts.',
                'No new floor choice, imported response, headline, paper result, Fannie validation or full-SOMA transport claim.'])
        write_json(output / 'results.json', result)
        return result
    except Exception as exc:
        write_json(output / 'failed.json', dict(error_type=type(exc).__name__, error=str(exc),
            failed_utc=datetime.now(timezone.utc).isoformat(), results_written=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root', 'legacy-panel', 'saved-grid', 'rate-csv', 'rate-source', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    result = run(**vars(args))
    print(json.dumps({'status': 'passed', 'output': str(args.output),
                      'replayed_cells': result['legacy_replay']['parity']['cells'],
                      'parameter_selection_performed': False}, indent=2))
