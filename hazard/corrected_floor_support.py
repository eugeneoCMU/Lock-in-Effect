"""Offline seasoning support and structural envelopes on accepted corrected outputs.

End exposure reproduces the inherited measured-speed convention. Adjacent
opening exposure comes from loan-level source bookkeeping and excludes the
first-observed and calendar-gap payoff dollars from its numerator. Neither
ratio identifies sale/refinance, an involuntary hazard, or a transport effect.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
from itertools import product
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
YEARS = (2018, 2019, 2023, 2024, 2025)
AGES = (12, 24, 36, 60)
GAPS_BP = (0, -25, -50, -100, -200)
KEYS = ['vintage', 'coupon', 'fico_bucket', 'ltv_bucket']
AXES = dict(reference_mode=('inherited_psa', 'matched_max_off'),
            calibration=('legacy_conversion', 'illustrative'),
            gap_mode=('positive_only', 'preserve_refinancing'),
            sensitive_share=(0., .25, .5, .75, 1.))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, data):
    Path(path).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def verify_hashes(hashes):
    for path, expected in hashes.items():
        if digest(path) != expected:
            raise ValueError(f'Input hash mismatch: {path}')


def prepare_support(panel, rates):
    """Validate matching dollars without filling missing observed mean ages."""
    d = panel.copy()
    if d.duplicated(KEYS + ['reporting_period']).any():
        raise ValueError('Duplicate cohort-month rows')
    d['month'] = d.reporting_period.astype(str)
    d['period'] = pd.to_datetime(d.month, format='%Y%m', errors='raise')
    d['stratum'] = d[KEYS].astype(str).agg('|'.join, axis=1)
    d['rate'] = d.month.map(rates)
    relevant = d.period.dt.year.isin(YEARS) & (d.period <= pd.Timestamp('2025-09-01'))
    if (~np.isfinite(d.loc[relevant, 'rate']) | (d.loc[relevant, 'rate'] <= 0)).any():
        raise ValueError('Missing or invalid frozen mortgage rate')
    columns = ['coupon', 'exposure_upb', 'prepaid_upb', 'loan_count', 'adjacent_opening_upb',
               'first_observed_opening_upb', 'gap_opening_upb', 'first_observed_payoff_upb',
               'gap_payoff_upb', 'first_observed_payoff_count', 'gap_payoff_count', 'finite_age_count']
    if not np.isfinite(d[columns].to_numpy(float)).all() or (d[columns] < 0).any().any():
        raise ValueError('Nonfinite or negative support/payoff bookkeeping')
    d['gap_bp'] = (d.coupon - d.rate) * 10000
    d['adjacent_payoff_upb'] = d.prepaid_upb - d.first_observed_payoff_upb - d.gap_payoff_upb
    tolerance = 1e-7 + 1e-12 * d.prepaid_upb
    if (d.adjacent_payoff_upb < -tolerance).any():
        raise ValueError('First/gap payoff exceeds total payoff')
    d['adjacent_payoff_upb'] = d.adjacent_payoff_upb.clip(lower=0)
    if (d.adjacent_payoff_upb > d.adjacent_opening_upb + tolerance).any():
        raise ValueError('Adjacent payoff exceeds matched opening exposure')
    if np.isinf(d.mean_loan_age).any() or (d.mean_loan_age.dropna() < 0).any():
        raise ValueError('Invalid observed mean age')
    if ((d.finite_age_count == 0) & d.mean_loan_age.notna()).any():
        raise ValueError('Mean age lacks observed age support')
    if ((d.finite_age_count > 0) & d.mean_loan_age.isna()).any() or (d.finite_age_count > d.loan_count).any():
        raise ValueError('Inconsistent finite age count')
    return d


def select_cell(d, *, year, min_age, max_gap_bp):
    end = 9 if year == 2025 else 12
    return d[(d.period.dt.year == year) & (d.period.dt.month <= end) &
             (d.mean_loan_age >= min_age) & (d.gap_bp <= max_gap_bp + 1e-9)].copy()


def ratio(events, exposure):
    denominator = float(exposure.sum())
    r = float(events.sum()) / denominator if denominator > 0 else None
    # End-exposure cash ratios need not lie in the probability range.
    cpr = (1 - (1 - r) ** 12) * 100 if r is not None and 0 <= r <= 1 else None
    return r, cpr


def summarize_cell(d, *, year, min_age, max_gap_bp):
    selected = select_cell(d, year=year, min_age=min_age, max_gap_bp=max_gap_bp)
    end = selected[selected.exposure_upb > 0]
    adjacent = selected[selected.adjacent_opening_upb > 0]
    smm, cpr = ratio(end.prepaid_upb, end.exposure_upb)
    adj_smm, adj_cpr = ratio(adjacent.adjacent_payoff_upb, adjacent.adjacent_opening_upb)
    expected_months = 9 if year == 2025 else 12
    raw = d[(d.period.dt.year == year) & (d.period.dt.month <= expected_months)]
    return dict(year=year, min_age_months=min_age, max_gap_bp=max_gap_bp,
        status='supported' if len(end) else 'no_support',
        end_status='supported' if len(end) else 'no_support',
        adjacent_status='supported' if len(adjacent) else 'no_support',
        end_missing_months=[f'{year}{n:02}' for n in range(1, expected_months+1) if f'{year}{n:02}' not in set(end.month)],
        adjacent_missing_months=[f'{year}{n:02}' for n in range(1, expected_months+1) if f'{year}{n:02}' not in set(adjacent.month)],
        rows=len(end), strata=int(end.stratum.nunique()),
        months=int(end.month.nunique()), expected_months=expected_months,
        selected_rows=len(selected), loan_count_months=int(end.loan_count.sum()),
        finite_age_count_months=int(end.finite_age_count.sum()),
        missing_mean_age_rows=int(raw.mean_loan_age.isna().sum()),
        selected_zero_end_exposure_rows=int((selected.exposure_upb <= 0).sum()),
        selected_zero_end_exposure_payoff_upb=float(selected.loc[selected.exposure_upb <= 0, 'prepaid_upb'].sum()),
        end_exposure_upb=float(end.exposure_upb.sum()), end_payoff_upb=float(end.prepaid_upb.sum()),
        end_smm=smm, end_cpr_pct=cpr, end_ratio_probability_valid=smm is not None and 0 <= smm <= 1,
        adjacent_rows=len(adjacent), adjacent_strata=int(adjacent.stratum.nunique()),
        adjacent_months=int(adjacent.month.nunique()), adjacent_loan_count_months=int(adjacent.loan_count.sum()),
        adjacent_opening_upb=float(adjacent.adjacent_opening_upb.sum()),
        adjacent_payoff_upb=float(adjacent.adjacent_payoff_upb.sum()), adjacent_smm=adj_smm,
        adjacent_cpr_pct=adj_cpr, excluded_first_payoff_upb=float(selected.first_observed_payoff_upb.sum()),
        excluded_gap_payoff_upb=float(selected.gap_payoff_upb.sum()),
        excluded_first_payoff_count=int(selected.first_observed_payoff_count.sum()),
        excluded_gap_payoff_count=int(selected.gap_payoff_count.sum()),
        excluded_first_opening_upb=float(selected.first_observed_opening_upb.sum()),
        excluded_gap_opening_upb=float(selected.gap_opening_upb.sum()),
        adjacent_loan_count_qualification='Loan count sums selected cohort-month counts; adjacent-only loan count unavailable',
        age_qualification='Observed count-weighted cohort mean age; no individual-age screen or imputation')


def support_grid(d):
    return [summarize_cell(d, year=y, min_age=a, max_gap_bp=g) for y, a, g in product(YEARS, AGES, GAPS_BP)]


def designated_inference(d, *, draws=9999, n_grid=401):
    selected = select_cell(d, year=2019, min_age=24, max_gap_bp=-25)
    selected = selected[selected.exposure_upb > 0]
    strata, months = int(selected.stratum.nunique()), int(selected.month.nunique())
    result = dict(diagnostic='mature2019age24gap25', year=2019, min_age_months=24, max_gap_bp=-25,
        rows=len(selected), strata=strata, months=months, required_strata=10, required_months=6,
        primary2018_unchanged=True, stratum=None, month=None,
        interpretation='Separate selected-payoff-speed measurement inference; no floor identification or transport claim')
    if strata < 10 or months < 6:
        return dict(result, status='insufficient_support')
    from hazard.post_rerun_diagnostics import infer_floor
    result.update(status='computed', stratum=infer_floor(selected, draws=draws, n_grid=n_grid, cluster='stratum'),
                  month=infer_floor(selected, draws=draws, n_grid=n_grid, cluster='month'))
    return result


def structural_envelope(scenarios):
    expected = set(product(*AXES.values()))
    actual = [tuple(s[k] for k in AXES) for s in scenarios]
    if len(actual) != 40 or len(set(actual)) != 40 or set(actual) != expected:
        raise ValueError('Incomplete or duplicate 40-scenario matrix')
    measures = ('reported_marginal_b', 'closed_pool_cash_marginal_b')
    if not np.isfinite([[s[k] for k in measures] for s in scenarios]).all():
        raise ValueError('Nonfinite matrix outcome')
    def bounds(rows):
        return {k:dict(min=min(s[k] for s in rows), max=max(s[k] for s in rows),
                       min_scenarios=[s['scenario'] for s in rows if s[k] == min(t[k] for t in rows)],
                       max_scenarios=[s['scenario'] for s in rows if s[k] == max(t[k] for t in rows)]) for k in measures}
    modes = []
    for s in scenarios:
        if s['sensitive_share'] != 0:
            continue
        identity = s['gap_mode'] == 'positive_only'
        if identity and any(abs(s[k]) > 1e-8 for k in measures):
            raise ValueError('Zero-share positive-only identity failed')
        modes.append({k:s[k] for k in ['scenario', 'reference_mode', 'calibration', 'gap_mode', *measures]} |
            dict(identity_required=identity, reason='ON equals OFF' if identity else 'Refinancing channel remains active at zero sensitive share'))
    grouped=[]
    for axis in AXES:
        for value in AXES[axis]:
            rows=[s for s in scenarios if s[axis] == value]
            grouped.append(dict(axis=axis, value=value, scenario_count=len(rows), **bounds(rows)))
    return dict(scenario_count=40, axes=AXES, **bounds(scenarios), by_axis=grouped,
        zero_share_identity_modes=modes, interpretation='Structural envelope over supplied assumptions; not a confidence interval or probability distribution',
        reported_measure='OFF minus ON production principal with inherited changing reporting scale, billion dollars',
        closed_pool_measure='OFF minus ON unreweighted closed-pool contractual cash principal, billion dollars')


def validate_matrix(matrix):
    """Gate saved top-level acceptance, then local outputs, then summary links."""
    from hazard.comparison_acceptance import validate_analysis
    matrix=Path(matrix)
    acceptance=json.loads((matrix/'acceptance.json').read_text())
    top=json.loads((matrix/'results.json').read_text())
    if acceptance.get('status') != 'passed' or top.get('status') != 'complete' or top.get('acceptance') != acceptance:
        raise ValueError('Matrix acceptance is absent or differs from results')
    # The gate reads only local outputs and never follows raw input source paths.
    checked=validate_analysis(matrix,top['scenarios'])
    for key in ('validated_receipts','scenario_count','validated_output_count','checks','tolerances'):
        if checked[key] != acceptance[key]:
            raise ValueError(f'Matrix accepted output evidence differs: {key}')
    for scenario in top['scenarios']:
        label=scenario['scenario']
        pair=json.loads((matrix/(label+'-pair')/'results.json').read_text())
        score=json.loads((matrix/(label+'-scoring')/'results.json').read_text())
        for measure in ('reported_marginal_b','closed_pool_cash_marginal_b'):
            if not np.isclose(scenario[measure],pair[measure],rtol=1e-12,atol=1e-8):
                raise ValueError('Matrix summary and pair outcome differ')
        if scenario['retrospective_scores'] != score['aggregate'] or scenario['support'] != score['support']:
            raise ValueError('Matrix summary and scoring outcome/support differ')
    return top, checked


def run(*, accepted_root, output):
    accepted_root,output=Path(accepted_root).resolve(),Path(output).resolve()
    if output.exists():
        raise FileExistsError('Preserve existing support attempt')
    output.mkdir(parents=True)
    try:
        calibration=accepted_root/'floor-calibration/input_manifest.json'
        cal=json.loads(calibration.read_text())['input_sha256']
        panel=accepted_root/'combined/cohort_month_panel.parquet'
        combined_report=accepted_root/'combined/report.json'
        rate_csv=Path(next(p for p in cal if p.endswith('/MORTGAGE30US_201612_202510.csv')))
        rate_meta=Path(next(p for p in cal if p.endswith('/rate_source.json')))
        required={str(p):cal[str(p)] for p in (panel,combined_report,rate_csv,rate_meta)}
        verify_hashes(required)
        matrix=accepted_root/'mixture-comparison-verified-session'
        inputs=dict(required)
        inputs[str(calibration)]=digest(calibration)
        # Hash only saved analysis outputs; do not follow input-manifest source paths.
        for p in matrix.rglob('*'):
            if p.is_file():inputs[str(p)]=digest(p)
        dependencies=[Path(__file__),ROOT/'hazard/post_rerun_diagnostics.py',
            ROOT/'hazard/floor_inference_correction_v2.py',ROOT/'hazard/calibrate_freddie_rebuild.py',
            ROOT/'hazard/comparison_acceptance.py',ROOT/'tests/test_corrected_floor_support.py',ROOT/'docs/2026-10-14-corrected-support-next.md',
            ROOT/'docs/superpowers/specs/2026-10-14-research-next-design.md']
        code={str(p):digest(p) for p in dependencies}
        write_json(output/'input_manifest.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),
            input_sha256=inputs,code_sha256=code,design=dict(years=YEARS,ages=AGES,gaps_bp=GAPS_BP,
            inference_diagnostic='mature2019age24gap25',minimum_strata=10,minimum_months=6,
            draws=9999,n_grid=401,seed=42),outcomes_read=False,rate_convention='Frozen weekly within-month means',
            source_receipt_validation='Parent performs separate retained-source fullcheck; worker opens saved outputs only'))
        verify_hashes(inputs)
        top,checked=validate_matrix(matrix)
        from hazard.calibrate_freddie_rebuild import frozen_rates
        rates,meta=frozen_rates(rate_csv,rate_meta)
        for year in YEARS:
            for month in range(1,10 if year==2025 else 13):
                if not np.isfinite(rates.get(f'{year}{month:02}',np.nan)):
                    raise ValueError('Missing required support-calendar frozen rate')
        prepared=prepare_support(pd.read_parquet(panel),rates)
        grid=support_grid(prepared)
        write_json(output/'support_grid.json',dict(cells=grid,cell_count=len(grid),
            end_denominator='Positive end-of-month UPB; same-row complete payoff numerator',
            adjacent_denominator='Positive source adjacent-opening UPB; complete payoff minus first/gap payoff numerator',
            observed_age_imputed=False,loan_count_measure='Sum of loan counts across cohort-months; not distinct people'))
        pd.DataFrame(grid).to_csv(output/'support_grid.csv',index=False)
        mature=designated_inference(prepared)
        write_json(output/'mature2019_measurement_inference.json',mature)
        envelope=structural_envelope(top['scenarios'])
        write_json(output/'structural_envelope.json',envelope)
        scenario_rows=[]
        for s in top['scenarios']:
            pair=json.loads((matrix/(s['scenario']+'-pair')/'results.json').read_text())
            scenario_rows.append({k:s[k] for k in ['scenario',*AXES,'reported_marginal_b','closed_pool_cash_marginal_b']} |
                dict(gamma_per_pp=pair['parameters']['gamma_per_pp']['on'],
                     reference_annual_floor=pair['parameters']['reference_annual_floor'],
                     off_reported_principal_b=pair['legs']['off']['production_principal_b'],
                     on_reported_principal_b=pair['legs']['on']['production_principal_b'],
                     off_pool_cash_principal_b=pair['legs']['off']['closed_pool_cash_principal_b'],
                     on_pool_cash_principal_b=pair['legs']['on']['closed_pool_cash_principal_b']))
        pd.DataFrame(scenario_rows).to_csv(output/'structural_scenarios.csv',index=False)
        write_json(output/'matrix_validation.json',checked)
        verify_hashes(inputs);verify_hashes(code)
        write_json(output/'completed.json',dict(status='complete',input_hashes_unchanged=True,code_hashes_unchanged=True,
            cell_count=100,supported_cells=sum(r['status']=='supported' for r in grid),
            designated_inference_status=mature['status'],matrix_scenarios=40,
            source_receipt_validation='Parent fullcheck is separate; not performed or certified by this worker',
            output_sha256={p.name:digest(p) for p in output.iterdir() if p.is_file()}))
    except BaseException as exc:
        write_json(output/'failed.json',dict(error=repr(exc)))
        raise


if __name__=='__main__':
    if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
    parser=argparse.ArgumentParser()
    parser.add_argument('--accepted-root',required=True)
    parser.add_argument('--output',required=True)
    run(**vars(parser.parse_args()))
