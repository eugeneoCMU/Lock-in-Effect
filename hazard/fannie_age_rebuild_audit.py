"""Recombine existing Fannie cells; this is not a raw-source payoff rebuild.

Protocol: specs/SPEC_2026-10-09_audited_rebuild_continuation.md.
No production inputs or original result files are overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd

# Legacy research modules resolve their sibling configuration as a top-level
# import. Match the existing command-line entry points without touching config.
HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
# This driver retrieves public CSV bytes, never calls the keyed FRED API, and
# needs config only to import the existing local aggregation function.
os.environ.setdefault('FRED_API_KEY', 'offline-unused')

from hazard.fannie_replication import combine_quarter_cells
from hazard.fannie_floor_read import prep, grid_for, deep_otm
from hazard.older_vintage_floor_support import legacy_parity

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/eugene/somthing/Lock In effect/Lock-in-Effect/hazard/data')
OUTPUT = ROOT / 'output/research-limits/2026-10-09/rebuild/fannie'
SPEC = ROOT / 'specs/SPEC_2026-10-09_audited_rebuild_continuation.md'
KEYS = ['vintage', 'coupon', 'fico_bucket', 'ltv_bucket', 'reporting_period']
RATE_URL = ('https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US'
            '&cosd=2016-12-01&coed=2025-10-31')
RESULT = ROOT / 'hazard/data/fannie_age_rebuild_2026-10-09_results.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def compare_panels(before, after):
    if before.duplicated(KEYS).any() or after.duplicated(KEYS).any():
        raise ValueError('Duplicate cell-months')
    a, b = [d.set_index(KEYS).sort_index() for d in (before, after)]
    if not a.index.equals(b.index):
        raise ValueError('Panel keys changed')
    checks = {}
    for col in ['exposure_upb', 'orig_upb_sum', 'prepaid_upb', 'loan_count',
                'monthly_prepay_rate', 'burnout']:
        ok = bool(np.allclose(a[col], b[col], rtol=1e-12, atol=1e-7, equal_nan=True))
        checks[col] = dict(passed=ok, max_abs_difference=float((a[col]-b[col]).abs().max()))
        if not ok:
            raise ValueError(f'Age-only rebuild changed {col}')
    age_a, age_b = a.mean_loan_age.to_numpy(), b.mean_loan_age.to_numpy()
    finite = np.isfinite(age_a) & np.isfinite(age_b)
    if not np.array_equal(np.isfinite(age_a), np.isfinite(age_b)):
        raise ValueError('Finite-age support changed')
    delta = np.abs(age_b[finite]-age_a[finite])
    weights = a.exposure_upb.to_numpy()[finite]
    return dict(rows=len(a), keys_equal=True, unaffected_columns=checks,
                changed_age_rows=int((delta > 1e-10).sum()),
                nonfinite_age_rows=int((~finite).sum()),
                max_abs_age_change_months=float(delta.max()),
                weighted_abs_age_change_months=float(np.average(delta, weights=weights)),
                mode_state_differences=int((a.mode_state != b.mode_state).sum()))


def grids(frame):
    return dict(out_of_window_2017_2019=grid_for(frame, 201701, 201912),
                in_window_2023_2024=grid_for(frame, 202301, 202412),
                in_window_deep_OTM_validation=deep_otm(frame))


def verify_grid_parity(actual, saved):
    mismatches = []
    for window, cells in actual.items():
        for cell, row in cells.items():
            old = saved[window][cell]
            if row['n_cohort_months'] != old['n_cohort_months']:
                mismatches.append(f'{window}/{cell}: count')
            x, y = row['cpr_pct'], old['cpr_pct']
            if (x is None) != (y is None) or (x is not None and abs(x-y) > .00100000001):
                mismatches.append(f'{window}/{cell}: CPR')
            if not np.isclose(row['exposure_upb'], old['exposure_upb'], rtol=1e-12, atol=1e-5):
                mismatches.append(f'{window}/{cell}: exposure')
    if mismatches:
        raise ValueError('Prior floor-grid replay failed: ' + '; '.join(mismatches))
    return {'passed': True, 'cells': sum(map(len, actual.values())), 'cpr_tolerance_pp': .001}


def membership_changes(before, after):
    rows = []
    windows = [('out_of_window_2017_2019', 201701, 201912, [0., -.0025, -.005]),
               ('in_window_2023_2024', 202301, 202412, [0., -.0025, -.005]),
               ('in_window_deep_OTM_validation', 202301, 202412, [-.02])]
    for label, lo, hi, gaps in windows:
        for gap in gaps:
            for age in [12, 24]:
                selected = [d[d.rp.between(lo, hi) & d.gap.le(gap)
                              & d.mean_loan_age.ge(age)].set_index(KEYS)
                            for d in (before, after)]
                a, b = selected
                added, removed = b.index.difference(a.index), a.index.difference(b.index)
                rows.append(dict(window=label, max_gap=gap, min_mean_age=age,
                                 added_cells=len(added), removed_cells=len(removed),
                                 added_exposure_dollar_months=float(b.loc[added, 'exposure_upb'].sum()),
                                 removed_exposure_dollar_months=float(a.loc[removed, 'exposure_upb'].sum())))
    return rows


def run(source=SOURCE, output=OUTPUT, fetch_rates=False):
    output.mkdir(parents=True, exist_ok=True)
    if (output/'results.json').exists():
        raise ValueError('Completed audit exists: preserve it and choose a new output directory')
    paths = [source/'fannie_quarters'/f'cells_FNMA{y}Q{q}.parquet'
             for y in range(2017, 2023) for q in range(1, 5)]
    fannie_path = source/'cohort_month_panel_fannie.parquet'
    freddie_path = ROOT/'hazard/data/cohort_month_panel.parquet'
    prior_path = ROOT/'hazard/data/fannie_floor_read_results.json'
    inputs = paths + [source/'fannie_quarters/manifest.json', fannie_path,
                      freddie_path, prior_path, SPEC, Path(__file__),
                      ROOT/'hazard/fannie_replication.py', ROOT/'hazard/fannie_floor_read.py']
    hashes = {str(p): sha(p) for p in inputs}
    write_json(output/'input_manifest.json', dict(frozen_utc=datetime.now(timezone.utc).isoformat(),
                                                sha256=hashes))
    parity = legacy_parity(paths, fannie_path)
    if not parity['passed']:
        raise ValueError('Legacy Fannie panel parity failed')
    rate_path = output/'MORTGAGE30US_201612_202510.csv'
    if not rate_path.exists():
        if not fetch_rates:
            raise ValueError('Frozen rates absent: --fetch-rates required once')
        with urlopen(RATE_URL, timeout=45) as response:
            payload = response.read()
        rate_path.write_bytes(payload)
        write_json(output/'rate_source.json', dict(url=RATE_URL, sha256=sha(rate_path),
                   retrieved_utc=datetime.now(timezone.utc).isoformat()))
    rate_meta = json.loads((output/'rate_source.json').read_text())
    if sha(rate_path) != rate_meta['sha256']:
        raise ValueError('Rate hash mismatch')
    rates = pd.read_csv(io.BytesIO(rate_path.read_bytes()))
    rates['date'] = pd.to_datetime(rates.iloc[:, 0])
    rates['value'] = pd.to_numeric(rates.MORTGAGE30US, errors='coerce') / 100
    if rates.date.duplicated().any():
        raise ValueError('Duplicate weekly rate date')
    monthly = rates.groupby(rates.date.dt.strftime('%Y%m')).value.mean().to_dict()
    required = {f'{y}{m:02}' for y in list(range(2017, 2020))+[2023, 2024] for m in range(1,13)}
    if not all(k in monthly and np.isfinite(monthly[k]) and monthly[k] > 0 for k in required):
        raise ValueError('Missing/nonfinite evaluation rates')
    saved = json.loads(prior_path.read_text())['books']
    old_fannie = prep(fannie_path, monthly)
    old_grids = {book: grids(prep(path, monthly))
                 for book, path in [('freddie', freddie_path), ('fannie', fannie_path)]}
    grid_parity = {book: verify_grid_parity(g, saved[book]) for book, g in old_grids.items()}
    # New values are calculated only after all old-grid replay gates pass.
    rebuilt_path = output/'cohort_month_panel_fannie_age_recombined.parquet'
    combined = combine_quarter_cells(paths, rebuilt_path, allow_legacy_cells=True)
    comparison = compare_panels(pd.read_parquet(fannie_path), combined.to_pandas())
    rebuilt = prep(rebuilt_path, monthly)
    new_grid = grids(rebuilt)
    if any(sha(Path(path)) != h for path, h in hashes.items()):
        raise ValueError('Source input changed during audit')
    result = dict(created_utc=datetime.now(timezone.utc).isoformat(),
                  scope='Age-only recombination of preserved Fannie quarter cells; not a raw-source payoff rebuild',
                  spec_sha256=sha(SPEC), input_sha256=hashes, rate_source=rate_meta,
                  source_inputs_unchanged=True, legacy_panel_parity=parity,
                  saved_grid_parity=grid_parity, panel_comparison=comparison,
                  before=old_grids['fannie'], after=new_grid,
                  membership_changes=membership_changes(old_fannie, rebuilt),
                  rebuilt_panel_sha256=sha(rebuilt_path),
                  limitations=['Original quarter payoff numerators are unchanged and unaudited against raw loan histories.',
                               'Reported loan count is the age weight; within-quarter finite-age counts are unavailable.',
                               'Age thresholds apply to cohort means, not each individual loan.',
                               'CPR annualizes payoff/current-end-UPB; summed exposure is dollar-months.',
                               'No Freddie raw-source rebuild, new parameter selection or headline simulation update.'])
    write_json(output/'results.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-rates', action='store_true')
    args = parser.parse_args()
    result = run(fetch_rates=args.fetch_rates)
    if RESULT.exists():
        raise SystemExit('Refusing to overwrite versioned aggregate result')
    write_json(RESULT, result)
    print(json.dumps({'panel_comparison': result['panel_comparison'],
                      'before': result['before'], 'after': result['after']}, indent=2))
