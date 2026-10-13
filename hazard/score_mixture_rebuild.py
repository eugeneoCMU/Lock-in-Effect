"""Retrospective mixture scoring with the existing corrected-data support gates."""
import argparse
from contextlib import contextmanager
from pathlib import Path
import sys
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT/'hazard'):
    if str(path) not in sys.path: sys.path.insert(0, str(path))
from hazard import score_freddie_rebuild as scoring
from hazard import simulate_freddie_rebuild as pair
from hazard.cohort_history import prediction_initial_state
from hazard.mixture_hazard import mixture_probability, reference_probability, response_gamma


def predict_path(rows, pre, cov, rates, annual_floor, psa, beta, *,
                 sensitive_share, calibration, gap_mode):
    if rows.duplicated(['cell','period']).any():
        raise ValueError('Duplicate cell-month rows')
    d = rows[['cell','period','coupon']].copy()
    dates = pd.to_datetime(pre.period.unique())
    if len(dates) != 1 or not (d.period > dates[0]).all():
        raise ValueError('One strictly pre-prediction initialization month is required')
    if not set(d.cell).issubset(set(pre.index) & set(cov.index)):
        raise ValueError('Missing pre-period or covariate support')
    origin = dates[0]
    d['age'] = d.cell.map(pre.mean_loan_age) + (d.period.dt.year-origin.year)*12 + d.period.dt.month-origin.month
    d['rate'] = d.period.dt.to_period('M').map(rates)
    d['fz'], d['lz'] = d.cell.map(cov.fico_z), d.cell.map(cov.ltv_z)
    if not np.isfinite(d[['age','rate','fz','lz']].to_numpy()).all():
        raise ValueError('Missing or nonfinite conditioning covariates')
    burn, balance, original = prediction_initial_state(pre)
    for _, sub in d.groupby('period', sort=True):
        b = np.array([burn[x] for x in sub.cell])
        p0 = reference_probability(sub.age.to_numpy(), b, sub.fz.to_numpy(), sub.lz.to_numpy(), psa=psa)
        probability = mixture_probability(p0, (sub.coupon-sub.rate).to_numpy(),
            sensitive_share, response_gamma(beta, calibration), gap_mode=gap_mode)
        default = pair.lh.default_hazard(np.maximum(sub.rate-sub.coupon,0).to_numpy(), sub.fz.to_numpy(), sub.lz.to_numpy())
        h, _ = pair.lh.normalize_competing_hazards(probability, default)
        d.loc[sub.index,'hazard'] = h
        d.loc[sub.index,'voluntary_before_floor'] = probability
        d.loc[sub.index,'floor_bound'] = False
        d.loc[sub.index,'normalized'] = probability+default > 1
        d.loc[sub.index,'predicted_burnout'] = b
        d.loc[sub.index,'latent_balance'] = [balance[x] for x in sub.cell]
        for cell, hz in zip(sub.cell,h):
            amount = balance[cell]*hz
            balance[cell] -= amount
            burn[cell] = min(1., burn[cell]+amount/original[cell])
    d['floor_bound'] = d.floor_bound.astype(bool)
    d['normalized'] = d.normalized.astype(bool)
    return d.drop(columns=['cell','period','coupon'])


@contextmanager
def scoring_context(sensitive_share, calibration, gap_mode):
    mixture_probability(.02,0.,sensitive_share,response_gamma(0.,calibration),gap_mode=gap_mode)
    previous = (scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES, scoring.RESPONSE_BETA)
    def choices(*args, **kwargs):
        previous[1](*args, **kwargs)  # Validate the historical freeze; do not reuse selected floors.
        return {'mixture': dict(annual_floor=0., psa=100., sensitive_share=sensitive_share,
            calibration=calibration, gap_mode=gap_mode, reference_newly_calibrated=False,
            gamma_per_pp={'off': 0., 'on': float(response_gamma(previous[4],calibration))},
            coefficient_convention='response_coefficients stores negative gamma; gamma_per_pp is the positive intensity coefficient')}
    def predictor(*args, **kwargs):
        return predict_path(*args, **kwargs, sensitive_share=sensitive_share,
            calibration=calibration, gap_mode=gap_mode)
    scoring.predict_path, scoring.recorded_choices = predictor, choices
    scoring.RESPONSE_BETA = -float(response_gamma(previous[4], calibration))
    scoring.SPEC = ROOT/'specs/SPEC_2026-10-13_mixture_alternative.md'
    scoring.CODE_FILES = previous[3]+['score_mixture_rebuild.py','mixture_hazard.py']
    try:
        yield
    finally:
        scoring.predict_path, scoring.recorded_choices, scoring.SPEC, scoring.CODE_FILES, scoring.RESPONSE_BETA = previous


def run(*, sensitive_share, calibration='legacy_conversion', gap_mode='positive_only', **inputs):
    with scoring_context(sensitive_share,calibration,gap_mode):
        return scoring.run(**inputs)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('root','macro','parameter-freeze','recorded-result','output'):
        p.add_argument('--'+name,required=True,type=Path)
    p.add_argument('--sensitive-share',required=True,type=float)
    p.add_argument('--calibration',choices=['illustrative','legacy_conversion'],default='legacy_conversion')
    p.add_argument('--gap-mode',choices=['positive_only','preserve_refinancing'],default='positive_only')
    run(**vars(p.parse_args()))


if __name__ == '__main__': main()
