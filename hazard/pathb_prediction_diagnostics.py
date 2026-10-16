"""Bounded retrospective prediction development; never changes production.

Run from the repository root: python3 -m hazard.pathb_prediction_diagnostics.
The protocol is frozen in specs/SPEC_2026-10-09_pathb_prediction_diagnostics.md.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

import numpy as np
import pandas as pd
import polars as pl

from hazard.pathb_cohort_validation import KEYS, START, END, fit_baseline, prepare_exposures, score
from hazard.cohort_history import prediction_initial_state
from hazard.stock_flow_accounting_comparison import ROOT, CHECKS, lh, sha

OUTPUT = ROOT / 'output/research-limits/2026-10-09/prediction'
SPEC = ROOT / 'specs/SPEC_2026-10-09_pathb_prediction_diagnostics.md'
ORIGINAL_FLOOR = .04991
FLOORS = (0., .02, .035, ORIGINAL_FLOOR)
PSAS = (50., 75., 100.)
RESPONSE_BETA = lh.rothstein_beta1(.065)


def annual_floor_monthly(annual_floor):
    return float(lh.cpr_annual_to_monthly_hazard(np.array([annual_floor]))[0])


def strict_score(exposure, events, hazard):
    exposure, events, hazard = [np.asarray(x, dtype=float) for x in (exposure, events, hazard)]
    if (not (exposure.shape == events.shape == hazard.shape) or exposure.ndim != 1
            or exposure.size == 0 or not all(np.isfinite(x).all() for x in (exposure, events, hazard))
            or (exposure <= 0).any() or (events < 0).any() or (events > exposure).any()
            or (hazard < 0).any() or (hazard > 1).any()):
        raise ValueError('Finite aligned positive exposure, valid principal and probabilities required')
    result = score(exposure, events, hazard)
    result['signed_error_b'] = result['predicted_b'] - result['observed_b']
    return result


def ordered_previous_upb(performance):
    """Isolated regression helper for the chronological production ingest repair.

    Explicit chronological ordering inside each loan avoids dependence on input
    row order or join order. Duplicate months and missing months require separate
    source-level validation before any rebuild.
    """
    return performance.with_columns(
        pl.col('current_upb').shift(1).over('loan_sequence_number', order_by='reporting_period').alias('prev_upb')
    )


def predict_path(rows, pre, cov, rates, annual_floor, psa, beta, *, allow_legacy_history=False, floor_form="max"):
    """Predict the cohort approximation from an explicit pre-period state.

    Reads only cell/date/coupon from rows; the observed outcomes, exposures and
    contemporaneous burnout never update the model's state. Observed opening
    exposure is used later solely for conditional scoring. Corrected histories
    require the fixed original cohort balance. Legacy clipping and survivor
    original-balance denominators are available only for historical replay.
    """
    if floor_form not in ('max', 'additive'):
        raise ValueError('Unknown floor form')
    if rows.duplicated(['cell', 'period']).any():
        raise ValueError('Duplicate cell-month rows')
    d = rows[['cell', 'period', 'coupon']].copy()
    dates = pd.to_datetime(pre.period.unique())
    if len(dates) != 1 or not (d.period > dates[0]).all():
        raise ValueError('One strictly pre-prediction initialization month is required')
    origin = dates[0]
    if not set(d.cell).issubset(set(pre.index) & set(cov.index)):
        raise ValueError('Missing pre-period or covariate support')
    d['age'] = d.cell.map(pre.mean_loan_age) + (d.period.dt.year-origin.year)*12 + d.period.dt.month-origin.month
    d['rate'] = d.period.dt.to_period('M').map(rates)
    d['fz'] = d.cell.map(cov.fico_z)
    d['lz'] = d.cell.map(cov.ltv_z)
    if not np.isfinite(d[['age', 'rate', 'fz', 'lz']].to_numpy()).all():
        raise ValueError('Missing or nonfinite conditioning covariates')
    burn, balance, original = prediction_initial_state(pre, allow_legacy=allow_legacy_history)
    c = lh.LITERATURE_COEFS
    floor = annual_floor_monthly(annual_floor)
    for _, sub in d.groupby('period', sort=True):
        b = np.array([burn[x] for x in sub.cell])
        vol = lh.h0_psa(sub.age.to_numpy(), psa_speed=psa) * np.exp(
            -beta * (sub.coupon-sub.rate).to_numpy()*100
            + c['beta_fico']*sub.fz.to_numpy() + c['beta_ltv']*sub.lz.to_numpy()
            + c['beta_burnout']*b)
        default = lh.default_hazard(np.maximum(sub.rate-sub.coupon, 0).to_numpy(), sub.fz.to_numpy(), sub.lz.to_numpy())
        if floor_form == "additive":
            before_normalization = 1. - (1. - floor) * (1. - np.clip(vol, 0., 1.))
        else:
            before_normalization = np.clip(np.maximum(floor, vol), 0, 1)
        h, _ = lh.normalize_competing_hazards(before_normalization, default)
        d.loc[sub.index, 'hazard'] = h
        d.loc[sub.index, 'voluntary_before_floor'] = vol
        d.loc[sub.index, 'floor_bound'] = (vol <= floor) if floor_form == 'max' else False
        d.loc[sub.index, 'normalized'] = before_normalization + default > 1
        d.loc[sub.index, 'predicted_burnout'] = b
        d.loc[sub.index, 'latent_balance'] = [balance[x] for x in sub.cell]
        for cell, hz in zip(sub.cell, h):
            amount = balance[cell] * hz
            balance[cell] -= amount
            denominator = max(original[cell], 1.) if allow_legacy_history else original[cell]
            burn[cell] = min(1., burn[cell] + amount/denominator)
    d['floor_bound'] = d.floor_bound.astype(bool)
    d['normalized'] = d.normalized.astype(bool)
    return d.drop(columns=['cell', 'period', 'coupon'])


def select_parameters(rows, pre, cov, rates, *, allow_legacy_history=False):
    if rows.empty or not rows.period.between('2023-01-01', '2023-12-01').all():
        raise ValueError('Parameter selection permits only January-December 2023 rows')
    grid = []
    for floor in FLOORS:
        for psa in PSAS:
            pred = predict_path(rows, pre, cov, rates, floor, psa, RESPONSE_BETA,
                                allow_legacy_history=allow_legacy_history)
            metrics = strict_score(rows.opening_exposure, rows.prepaid_upb, pred.hazard)
            grid.append(dict(annual_floor=floor, psa=psa, **metrics))
    def choose(candidates):
        best = min(candidates, key=lambda x: (
            x['weighted_rmse_monthly_pp'], abs(x['annual_floor']-ORIGINAL_FLOOR),
            abs(x['psa']-100), x['annual_floor'], x['psa']))
        return dict(annual_floor=best['annual_floor'], psa=best['psa'],
                    development_rmse_monthly_pp=best['weighted_rmse_monthly_pp'])
    return {'floor_only': choose([x for x in grid if x['psa'] == 100]),
            'floor_psa': choose(grid)}, grid


def diagnose_groups(rows, group, prediction):
    result = {str(k): strict_score(g.opening_exposure, g.prepaid_upb, g[prediction])
              for k, g in rows.groupby(group, observed=True)}
    aggregate = strict_score(rows.opening_exposure, rows.prepaid_upb, rows[prediction])
    for field in ('exposure_b_months', 'observed_b', 'predicted_b', 'signed_error_b'):
        if not np.isclose(sum(x[field] for x in result.values()), aggregate[field], rtol=1e-12, atol=1e-9):
            raise AssertionError(f'Group accounting failed: {group}/{field}')
    return result


def make_covariates(loans):
    loans = loans.copy()
    loans['coupon'] = np.round(np.round(loans.coupon/.005)*.005, 4)
    for col, source in [('fico_z', 'fico'), ('ltv_z', 'orig_ltv')]:
        loans[col] = (loans[source]-loans[source].mean())/max(loans[source].std(ddof=0), 1.)
    loans['cell'] = loans[KEYS].astype(str).agg('|'.join, axis=1)
    return loans.groupby('cell')[['fico_z', 'ltv_z']].mean()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def main(output=OUTPUT):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    panel_path = ROOT/'hazard/data/cohort_month_panel.parquet'
    sample_path = ROOT/'hazard/data/loan_sample.parquet'
    saved_path = CHECKS/'validation_cell_month_scores.csv'
    report_path = ROOT/'hazard/data/pathb_validation_2026-10-07_results.json'
    source_paths = [panel_path, sample_path, saved_path, report_path, CHECKS/'macro_frozen.parquet',
                    ROOT/'hazard/pathb_cohort_validation.py', ROOT/'hazard/literature_hazard.py',
                    ROOT/'hazard/ingest.py', ROOT/'hazard/config.py', SPEC, Path(__file__)]
    input_hashes = {str(p.relative_to(ROOT)): sha(p) for p in source_paths}
    # Predicate pushdown restricts source outcome access to the declared end.
    panel = pd.read_parquet(panel_path, filters=[('period', '<=', END.to_pydatetime())])
    # CSV uses nanoseconds and the Parquet uses microseconds. Canonicalize only
    # storage resolution so identical cell-months compare equal in the replay.
    panel['period'] = panel.period.astype('datetime64[ns]')
    panel['cell'] = panel[KEYS].astype(str).agg('|'.join, axis=1)
    if panel.duplicated(['cell', 'period']).any():
        raise ValueError('Duplicate panel cell-months')
    usable, exclusions = prepare_exposures(panel)
    cov = make_covariates(pd.read_parquet(sample_path))
    macro = pd.read_parquet(CHECKS/'macro_frozen.parquet')
    rates = macro.MORTGAGE30US.groupby(macro.index.to_period('M')).last()/100
    rates = rates[rates.index <= END.to_period('M')]
    pre_train = panel[panel.period == pd.Timestamp('2022-12-01')].set_index('cell')
    train = usable[usable.period.between('2023-01-01', '2023-12-01')].copy()
    train = train[train.cell.isin(set(pre_train.index) & set(cov.index))].copy()
    # Frozen retrospective replay intentionally retains its recorded legacy
    # history convention. Corrected development needs a separately audited run.
    selected, grid = select_parameters(train, pre_train, cov, rates, allow_legacy_history=True)
    freeze = dict(design='retrospective development; previously examined evaluation outcomes',
                  selection_start='2023-01-01', selection_end='2023-12-01',
                  selection_metric='exposure-weighted monthly-rate RMSE, response-on',
                  annual_floor_grid=list(FLOORS), psa_grid=list(PSAS), selected=selected,
                  development_rows=len(train), development_cells=int(train.cell.nunique()),
                  development_exposure_b_months=float(train.opening_exposure.sum()/1e9),
                  development_observed_b=float(train.prepaid_upb.sum()/1e9),
                  protocol_sha256=sha(SPEC), input_sha256=input_hashes)
    freeze_path = output/'parameter_freeze.json'
    if freeze_path.exists():
        previous = json.loads(freeze_path.read_text())
        previous.pop('frozen_at_utc', None)
        if previous != freeze:
            raise ValueError('Existing parameter freeze differs; do not overwrite a scored protocol')
    else:
        write_json(freeze_path, dict(freeze, frozen_at_utc=datetime.now(timezone.utc).isoformat()))
    pd.DataFrame(grid).to_csv(output/'development_grid.csv', index=False)

    # Evaluation is first accessed for candidate scoring only after freeze is saved.
    base = fit_baseline(usable)
    pre_eval = panel[panel.period == pd.Timestamp('2023-12-01')].set_index('cell')
    eligible = set(base) & set(cov.index) & set(pre_eval.index)
    raw = usable[usable.period.between(START, END)].copy()
    ev = raw[raw.cell.isin(eligible)].copy()
    ev['base'] = ev.cell.map(base)
    paths = {}
    parameters = {'original': {'annual_floor': ORIGINAL_FLOOR, 'psa': 100.}, **selected}
    for family, p in parameters.items():
        for leg, beta in [('off', 0.), ('on', RESPONSE_BETA)]:
            name = family+'_'+leg
            path = predict_path(ev, pre_eval, cov, rates, p['annual_floor'], p['psa'], beta,
                                allow_legacy_history=True)
            paths[name] = path
            ev[name] = path.hazard
            ev[name+'_floor_bound'] = path.floor_bound
    names = ['base'] + list(paths)
    aggregate = {n: strict_score(ev.opening_exposure, ev.prepaid_upb, ev[n]) for n in names}
    saved = pd.read_csv(saved_path, parse_dates=['period'])
    saved = saved.set_index(['cell', 'period']).sort_index()
    actual = ev.set_index(['cell', 'period']).sort_index()
    if not saved.index.equals(actual.index):
        raise AssertionError('Evaluation support differs from saved check')
    reported = json.loads(report_path.read_text())
    parity = {}
    for current, prior in [('base', 'base'), ('original_on', 'on'), ('original_off', 'off')]:
        diff = float(np.max(np.abs(actual[current]-saved[prior])))
        if diff > 2e-15:
            raise AssertionError(f'Original prediction parity failed: {current}, {diff}')
        metric_diffs = {k: float(aggregate[current][k]-v) for k, v in reported['aggregate'][prior].items()}
        if any(abs(v) > 1e-8 for v in metric_diffs.values()):
            raise AssertionError('Reported metric reconciliation failed')
        parity[current] = {'max_abs_row_hazard_difference': diff, 'reported_metric_differences': metric_diffs}
    for col in ('opening_exposure', 'prepaid_upb'):
        if not np.allclose(actual[col], saved[col], rtol=1e-14, atol=1e-6):
            raise AssertionError(f'Saved accounting mismatch: {col}')
    ev['coupon_vintage'] = ev[['vintage', 'coupon']].astype(str).agg('|'.join, axis=1)
    ev['halfyear'] = ev.period.dt.year.astype(str)+'H'+np.where(ev.period.dt.month <= 6, '1', '2')
    diagnostics = {
        group: {n: diagnose_groups(ev, group, n) for n in names}
        for group in ('coupon', 'vintage', 'coupon_vintage', 'halfyear')}
    floor_diagnostics = {n: diagnose_groups(ev, n+'_floor_bound', n) for n in paths}
    monthly_floor = annual_floor_monthly(ORIGINAL_FLOOR)
    original_path = paths['original_on']
    floor_exposure = float(ev.loc[original_path.floor_bound, 'opening_exposure'].sum())
    floor_amount = float((ev.opening_exposure*monthly_floor).sum()/1e9)
    latent_gap = original_path.latent_balance/ev.opening_exposure-1
    units = dict(annual_floor=ORIGINAL_FLOOR, monthly_floor=monthly_floor,
                 annual_back_conversion=1-(1-monthly_floor)**12,
                 minimum_coupon=float(ev.coupon.min()), maximum_coupon=float(ev.coupon.max()),
                 minimum_conditioning_rate=float(original_path.rate.min()), maximum_conditioning_rate=float(original_path.rate.max()),
                 floor_only_predicted_b=floor_amount,
                 floor_only_minus_observed_b=floor_amount-aggregate['original_on']['observed_b'],
                 original_on_bound_rows=int(original_path.floor_bound.sum()),
                 original_on_bound_exposure_fraction=floor_exposure/float(ev.opening_exposure.sum()),
                 original_on_competing_normalization_rows=int(original_path.normalized.sum()),
                 original_on_direct_floor_lift_b=float((ev.opening_exposure*(original_path.hazard-original_path.voluntary_before_floor)).sum()/1e9),
                 direct_floor_lift_interpretation='Holding original predicted burnout fixed, not a recursively recomputed zero-floor path',
                 weighted_latent_balance_minus_realized_exposure_fraction=float(np.average(latent_gap, weights=ev.opening_exposure)),
                 latent_balance_diagnostic_interpretation='Predicted-payoff-only state omits amortization and defaults; used only for burnout recursion',
                 exposure_units='USD opening UPB; summed exposure is USD-months',
                 outcome_units='USD voluntary payoff prior-UPB; not scheduled principal or all agency runoff',
                 hazard_units='monthly probability decimal; rate gap is annual note coupon minus mortgage rate decimal, multiplied by 100')
    result = dict(design=freeze['design'], evaluation_start=str(START.date()), evaluation_end=str(END.date()),
                  scored_at_utc=datetime.now(timezone.utc).isoformat(),
                  parameter_freeze_sha256=sha(freeze_path), spec=str(SPEC.relative_to(ROOT)),
                  n_cells=int(ev.cell.nunique()), rows=len(ev), months=int(ev.period.nunique()),
                  selected_parameters=selected, aggregate=aggregate, reconciliation=parity,
                  exclusions=exclusions, retained_exposure_fraction=float(ev.opening_exposure.sum()/raw.opening_exposure.sum()),
                  training_evaluation_cell_overlap=int(len(set(train.cell) & set(ev.cell))),
                  floor_diagnostics=floor_diagnostics, units_and_state_audit=units,
                  source_order_bug={'status': 'verified synthetic implementation defect; realized saved-panel effect unknown',
                                    'location': 'hazard/ingest.py:214-218',
                                    'mechanism': 'prev_upb shift is not ordered by reporting_period within loan; input or join reordering changes payoff numerator',
                                    'synthetic_legacy_payoff': 100., 'synthetic_ordered_payoff': 90.,
                                    'repair': 'Loan window now explicitly orders by reporting_period; regression fixture returns90 instead of100. Duplicate/gapped months and realized source order still need auditing before rebuilding.',
                                    'ingestion_code_changed': True, 'saved_panels_rebuilt': False},
                  limitations=[
                      'Evaluation outcomes previously examined; date-separated fitting does not create an untouched holdout',
                      'Source-order bug verified synthetically; no claim it explains the saved-panel overprediction',
                      'Candidates retain all cohort approximations including frozen proxy covariates and payoff-only burnout recursion',
                      'Conditional on realized exposure and rates; not a forward full-book forecast',
                      'The imported elasticity, moving share and economic meaning of the floor are not estimated',
                      'No direct loan-level risk-set reconstruction, scheduled/default/curtailment evaluation, or SOMA transport',
                      'No production promotion or new $42.6B conclusion from this comparison'],
                  input_sha256=input_hashes)
    write_json(output/'results.json', result)
    write_json(output/'group_diagnostics.json', diagnostics)
    columns = ['cell', 'period', *KEYS, 'opening_exposure', 'prepaid_upb', *names,
               *[n+'_floor_bound' for n in paths]]
    ev[columns].to_csv(output/'evaluation_cell_month_predictions.csv', index=False)
    pd.DataFrame.from_dict(aggregate, orient='index').rename_axis('candidate').to_csv(output/'scorecard.csv')
    # Hashes make accidental source mutations visible, including indirect imports.
    if any(sha(p) != input_hashes[str(p.relative_to(ROOT))] for p in source_paths):
        raise AssertionError('Read-only source changed during diagnostics')
    print(json.dumps({'selected': selected, 'aggregate': aggregate, 'audit': units}, indent=2))
    return result


if __name__ == '__main__':
    main()
