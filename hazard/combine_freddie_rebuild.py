"""Combine only verified quarterly source rebuilds into separate model inputs."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('FRED_API_KEY','offline-source-rebuild-no-network')
import numpy as np
import pandas as pd
import polars as pl

from config import MARKOV_STATES, N_LOANS, RNG_SEED
from schema import SOURCE_SEMANTICS_VERSION
from loan_sample import _attach_history, _stratified_sample
from run_freddie_rebuild import OUTPUT, QUARTERS, digest, validate_completed, write_json

KEYS=['vintage','coupon','fico_bucket','ltv_bucket']
SUMS=['exposure_upb','orig_upb_sum','prepaid_upb','finite_age_sum','finite_age_count','loan_count',
      'opening_upb','adjacent_opening_upb','first_observed_opening_upb','gap_opening_upb',
      'first_observed_payoff_upb','gap_payoff_upb','first_observed_payoff_count','gap_payoff_count']


def combine_panel(frames):
    """Fixed denominators are summed once per source cohort, never per month."""
    denominators=[]
    for frame in frames:
        if frame.select(pl.struct(KEYS+['reporting_period']).is_duplicated().any()).item():
            raise ValueError('Duplicate quarterly cohort-month')
        fixed=frame.group_by(KEYS).agg(pl.col('cohort_original_upb').n_unique().alias('n'),
                                        pl.col('cohort_original_upb').first())
        if fixed.filter((pl.col('n')!=1)|~pl.col('cohort_original_upb').is_finite()|
                        (pl.col('cohort_original_upb')<=0)).height:
            raise ValueError('Invalid fixed quarterly cohort denominator')
        denominators.append(fixed.drop('n'))
    fixed=pl.concat(denominators).group_by(KEYS).agg(pl.col('cohort_original_upb').sum())
    combined=pl.concat(frames).group_by(KEYS+['reporting_period']).agg([
        *[pl.col(c).sum() for c in SUMS],pl.col('mode_state').first()])
    combined=combined.join(fixed,on=KEYS).sort(KEYS+['reporting_period']).with_columns([
        (pl.col('finite_age_sum')/pl.col('finite_age_count')).alias('mean_loan_age'),
        (pl.col('prepaid_upb')/pl.col('exposure_upb').clip(lower_bound=1)).alias('monthly_prepay_rate'),
        (pl.col('prepaid_upb').cum_sum().over(KEYS)/pl.col('cohort_original_upb')).alias('burnout'),
        pl.col('reporting_period').str.to_datetime('%Y%m').alias('period')])
    if combined.filter(~pl.col('burnout').is_finite()|(pl.col('burnout')<0)|(pl.col('burnout')>1+1e-10)).height:
        raise ValueError('Combined payoff history exceeds fixed original balance')
    for col in SUMS:
        if not np.isclose(combined[col].sum(),sum(f[col].sum() for f in frames),rtol=1e-10,atol=1e-5):
            raise AssertionError('Quarter conservation failed: '+col)
    return combined


def combine_transitions(frames):
    counts=pl.concat(frames).group_by(['from_state','to_state']).agg(
        pl.col('opening_upb').sum(),pl.col('count').sum()).to_pandas()
    weighted=counts.pivot(index='from_state',columns='to_state',values='opening_upb').reindex(
        index=MARKOV_STATES,columns=MARKOV_STATES,fill_value=0.)
    if not np.isfinite(weighted.to_numpy()).all() or (weighted.to_numpy()<0).any():
        raise ValueError('Invalid opening-weight transition totals')
    totals=weighted.sum(axis=1)
    matrix=weighted.div(totals.replace(0,1),axis=0)
    for state in totals[totals==0].index:
        matrix.loc[state,state]=1.
    matrix.index.name='from_state'
    matrix.attrs.update(estimator='identified_monthly_loan_transitions',estimation_end='202205',weighting='balance')
    diagnostics=dict(estimation_end='202205',weighting='balance',used_pairs=int(counts['count'].sum()),
        unsupported_states=totals[totals==0].index.tolist(),opening_weight_by_state=totals.to_dict())
    return matrix,diagnostics


def combine(root=OUTPUT, output=None, *, quarters=QUARTERS, n_loans=N_LOANS, seed=RNG_SEED):
    root=Path(root);output=Path(output) if output else root/'combined'
    if output.exists():
        raise FileExistsError('Combined inputs already exist; preserve them and choose a new output')
    if len(set(quarters))!=len(quarters) or not quarters:
        raise ValueError('Unique nonempty source-quarter manifest required')
    missing=[q for q in quarters if not (root/'quarters'/q/'completed.json').exists()]
    if missing:
        raise FileNotFoundError('Missing verified quarter completions: '+','.join(missing))
    paths=[root/'quarters'/q for q in quarters]
    receipts=[validate_completed(p) for p in paths]
    reports=[json.loads((p/'rebuilt/report.json').read_text()) for p in paths]
    for q,report in zip(quarters,reports):
        if report.get('source_semantics_version') != SOURCE_SEMANTICS_VERSION:
            raise ValueError('Source semantics require a fresh corrected quarterly extraction')
        if report['quarter']!=q or report['cutoff']!='202509' or report['snapshot_month']!='202205' or report['transition_end']!='202205':
            raise ValueError('Quarter or cutoff mismatch in rebuilt report')
    ids=pl.concat([pl.scan_parquet(p/'rebuilt/eligible_source_ids.parquet') for p in paths])
    if ids.group_by('loan_sequence_number').len().filter(pl.col('len')>1).limit(1).collect().height:
        raise ValueError('Cross-quarter original loan ID overlap')
    panel=combine_panel([pl.read_parquet(p/'rebuilt/panel.parquet') for p in paths])
    matrix,transition_diag=combine_transitions([pl.read_parquet(p/'rebuilt/transition_counts.parquet') for p in paths])
    per_file=max(1000,n_loans*4//len(paths))
    pieces=[]
    for i,p in enumerate(paths):
        snap=pl.read_parquet(p/'rebuilt/snapshot.parquet')
        if snap.filter((pl.col('reporting_period')!='202205')|(pl.col('original_loan_term')!=360)|
                       (pl.col('balance')<=0)|pl.col('state').is_in(['Prepaid','Defaulted','Liquidated'])).height:
            raise ValueError('Invalid active pre-QT snapshot')
        if snap.height:
            pieces.append(snap.sample(n=min(per_file,snap.height),seed=seed+i))
    if not pieces:
        raise ValueError('No surviving loans to sample')
    histories=[pl.read_parquet(p/'rebuilt/cohort_history.parquet') for p in paths]
    from coverage_exception import combined_audit
    coverage=combined_audit(reports,histories)
    pool=_attach_history(pl.concat(pieces),histories)
    sample=_stratified_sample(pool,n_loans,seed).with_columns(pl.lit(1.).alias('weight'))
    output.mkdir(parents=True,mode=0o700)
    panel.write_parquet(output/'cohort_month_panel.parquet')
    sample.write_parquet(output/'loan_sample.parquet')
    (output/'loan_sample.parquet').chmod(0o600)
    matrix.to_parquet(output/'markov_transition_matrix.parquet')
    write_json(output/'transition_diagnostics.json',transition_diag)
    result=dict(quarters=list(quarters),complete_freddie_manifest=list(quarters)==QUARTERS,
        source_semantics_version=SOURCE_SEMANTICS_VERSION,
        pre_snapshot_coverage=coverage,
        population='known360FRM; original vintage2017–2021',cutoff='202509',transition_end='202205',
        sample_month='202205',sample_n=sample.height,sample_unique_ids=sample['loan_id'].n_unique(),
        sample_seed=seed,pool_per_source_quarter=per_file,panel_rows=panel.height,
        original_loans=sum(r['counts']['eligible_original_ids'] for r in reports),
        zero_note_rate_excluded_loans=sum(r.get('zero_note_rate_exclusions',{}).get('known360_count',0) for r in reports),
        zero_note_rate_excluded_original_upb=sum(r.get('zero_note_rate_exclusions',{}).get('known360_upb',0.) for r in reports),
        zero_note_rate_exclusions_by_quarter={q:r.get('zero_note_rate_exclusions',dict(enabled=False,known360_count=0,known360_upb=0.)) for q,r in zip(quarters,reports)},
        quarter_cash_ratio_audits_by_quarter={q:r.get('quarter_cash_ratio_audit') for q,r in zip(quarters,reports)},
        identity_exceptions_by_quarter={q:r.get('identity_exceptions') for q,r in zip(quarters,reports)},
        identity_exception_totals={k:sum((r.get('identity_exceptions') or {}).get(k,0) for r in reports)
            for k in ['original_records','performance_rows','eligible_original_loans','eligible_original_upb']},
        partial_cohort_overrun_count=sum(r.get('quarter_cash_ratio_audit',{}).get('overrun_cohort_count',0) for r in reports),
        complete_cohort_burnout_bounds_verified=True,
        observed_source_survivors=sum(r['artifacts']['snapshot.parquet']['rows'] for r in reports),
        original_payoff_assumptions=[dict(quarter=q,**r['payoff_assumptions']) for q,r in zip(quarters,reports)],
        source_report_sha256={q:digest(p/'rebuilt/report.json') for q,p in zip(quarters,paths)},
        mode_state='First source diagnostic only; transition model uses identified-loan counts',
        output_sha256={p.name:digest(p) for p in output.iterdir() if p.is_file()})
    write_json(output/'report.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=OUTPUT)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    print(json.dumps(combine(args.root,args.output),indent=2))
