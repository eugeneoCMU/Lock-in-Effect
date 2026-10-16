"""Landmark-sample follow-up, as-of gaps and aggregation diagnostics only."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from empirical_readiness import month_ordinal,month_string,sha256

ROOT=Path(__file__).resolve().parents[1]


def followup_status(panel,*,cutoff='202509'):
    counts=dict(observed_active_at_cutoff=0,missing_followup_before_cutoff=0,
                recorded_payoff=0,recorded_credit_exit=0)
    details=[]
    for loan,group in panel.groupby('loan_id',sort=False):
        group=group.sort_values('reporting_period');last=group.iloc[-1]
        pay=int(group.recorded_payoff_event.sum());credit=int(group.recorded_credit_exit.sum())
        if pay+credit>1:raise ValueError('Multiple first exits in borrower follow-up')
        month=str(last.reporting_period)
        if month>cutoff:raise ValueError('Post-cutoff borrower record')
        if pay:status='recorded_payoff'
        elif credit:status='recorded_credit_exit'
        elif month==cutoff:status='observed_active_at_cutoff'
        else:status='missing_followup_before_cutoff'
        counts[status]+=1
        details.append(dict(loan_id=loan,status=status,last_observed_month=month,
            missing_tail_months=month_ordinal(cutoff)-month_ordinal(month) if status=='missing_followup_before_cutoff' else 0))
    return dict(loans=len(details),cutoff=cutoff,counts=counts,
        missing_tail_months=sum(r['missing_tail_months'] for r in details),
        last_observed_month_counts=pd.Series([r['last_observed_month'] for r in details]).value_counts().sort_index().to_dict(),
        private_details=details,
        qualification='Active at the accepted source cutoff is administrative censoring; earlier disappearance is missing follow-up, not an inferred exit.')


def add_asof_gaps(panel,benchmark):
    if benchmark.index.duplicated().any():raise ValueError('Duplicate benchmark month')
    for key,value in benchmark.items():
        month_ordinal(str(key))
        if not np.isfinite(value) or not 0<value<1:raise ValueError('Benchmark must be a positive decimal rate')
    d=panel.copy()
    d['benchmark_month']=d.reporting_period.astype(str).map(lambda m:month_string(month_ordinal(m)-1))
    d['benchmark_rate']=d.benchmark_month.map(benchmark)
    d['current_note_gap_pp']=100*(d.benchmark_rate-pd.to_numeric(d.lag_current_note_rate,errors='coerce'))
    d['original_note_gap_pp']=100*(d.benchmark_rate-d.coupon)
    d['original_coupon_bin_gap_pp']=100*(d.benchmark_rate-d.cohort_coupon)
    d.loc[~d.at_risk_adjacent,['current_note_gap_pp','original_note_gap_pp','original_coupon_bin_gap_pp']]=np.nan
    return d


def aggregation_comparison(panel):
    ok=(panel.at_risk_adjacent & np.isfinite(panel.lag_current_note_rate)
        & np.isfinite(panel.benchmark_rate) & np.isfinite(panel.adjacent_opening_upb)
        & (panel.adjacent_opening_upb>0))
    rows=[]
    for (month,stratum),group in panel[ok].groupby(['reporting_period','stratum_id']):
        if group.benchmark_rate.nunique()!=1 or group.cohort_coupon.nunique()!=1:
            raise ValueError('Inconsistent benchmark/coupon within source stratum-month')
        w=group.adjacent_opening_upb.to_numpy(float);w=w/w.sum()
        rates=group.lag_current_note_rate.to_numpy(float)
        market=float(group.benchmark_rate.iloc[0]);mean_rate=float(np.sum(w*rates))
        actual=float(np.sum(w*np.maximum((market-rates)*100,0)))
        at_mean=max((market-mean_rate)*100,0)
        rows.append(dict(reporting_period=str(month),stratum_id=stratum,loans=len(group),
            adjacent_opening_upb=float(group.adjacent_opening_upb.sum()),
            mean_current_note_rate=mean_rate,current_note_rate_sd_pp=float(np.sqrt(np.sum(w*(rates-mean_rate)**2)))*100,
            mean_original_note_rate=float(np.sum(w*group.coupon.to_numpy(float))),
            original_coupon_bin=float(group.cohort_coupon.iloc[0]),
            mean_borrower_positive_gap_pp=actual,positive_gap_at_mean_current_rate_pp=at_mean,
            hinge_aggregation_difference_pp=actual-at_mean,
            positive_gap_at_original_coupon_bin_pp=max((market-float(group.cohort_coupon.iloc[0]))*100,0)))
    return pd.DataFrame(rows)


def run(pilot,output):
    pilot=ROOT/pilot;output=ROOT/output;output.mkdir(parents=True,exist_ok=False);output.chmod(0o700)
    seal=json.loads((pilot/'output-sha256.json').read_text())
    source=pilot/'private-borrower-panel.parquet'
    if sha256(source)!=seal[source.name]:raise ValueError('Verified borrower panel changed')
    d=pd.read_parquet(source)
    status=followup_status(d)
    pd.DataFrame(status.pop('private_details')).to_parquet(output/'private-followup-status.parquet',index=False)
    (output/'private-followup-status.parquet').chmod(0o600)
    manifest=json.loads((ROOT/'output/research-next/2026-10-14/support/attempt-002/input_manifest.json').read_text())
    ratepath=next(Path(p) for p in manifest['input_sha256'] if p.endswith('MORTGAGE30US_201612_202510.csv'))
    if sha256(ratepath)!=manifest['input_sha256'][str(ratepath)]:raise ValueError('Frozen benchmark changed')
    rates=pd.read_csv(ratepath);months=pd.to_datetime(rates.observation_date).dt.strftime('%Y%m')
    benchmark=pd.to_numeric(rates.MORTGAGE30US,errors='coerce').groupby(months).mean().dropna()/100
    augmented=add_asof_gaps(d,benchmark)
    follow=augmented[augmented.reporting_period.between('202206','202509')].copy()
    follow['adjacent_payoff_event']=(follow.recorded_payoff_event.astype(bool)&follow.at_risk_adjacent).astype(int)
    follow['timing_unallocated_payoff_event']=(follow.recorded_payoff_event.astype(bool)&~follow.at_risk_adjacent&~follow.payoff_without_known_opening).astype(int)
    follow['unknown_opening_payoff_event']=(follow.recorded_payoff_event.astype(bool)&follow.payoff_without_known_opening).astype(int)
    assert int(follow.recorded_payoff_event.sum())==int(follow[['adjacent_payoff_event','timing_unallocated_payoff_event','unknown_opening_payoff_event']].sum().sum())
    monthly=follow.groupby('reporting_period').agg(adjacent_loan_months=('at_risk_adjacent','sum'),
        all_recorded_payoff_events=('recorded_payoff_event','sum'),adjacent_payoff_events=('adjacent_payoff_event','sum'),
        timing_unallocated_payoff_events=('timing_unallocated_payoff_event','sum'),unknown_opening_payoff_events=('unknown_opening_payoff_event','sum'),
        opening_upb=('adjacent_opening_upb','sum'),adjacent_payoff_upb=('adjacent_payoff_upb','sum'))
    monthly['adjacent_borrower_event_fraction']=monthly.adjacent_payoff_events/monthly.adjacent_loan_months.where(monthly.adjacent_loan_months>0)
    monthly['adjacent_amount_fraction']=monthly.adjacent_payoff_upb/monthly.opening_upb.where(monthly.opening_upb>0)
    monthly.to_csv(output/'monthly-event-and-dollar-denominators.csv')
    cells=aggregation_comparison(follow);cells.to_csv(output/'same-population-aggregation.csv',index=False)
    risk=follow[follow.at_risk_adjacent]
    available=risk.current_note_gap_pp.notna()
    positive=risk.current_note_gap_pp>0;near=risk.current_note_gap_pp.abs()<=.25
    summary=dict(population='3829 May2022 survivors; physical source2021Q1 only',followup_window=['202206','202509'],
        followup=status,adjacent_loan_months=len(risk),benchmark_lag_months=1,
        missing_benchmark_rows=int(risk.benchmark_rate.isna().sum()),missing_lag_current_rate_rows=int((~available).sum()),
        positive_current_note_gap_loan_months=int(positive.sum()),near_zero_current_note_gap_loan_months=int(near.sum()),
        positive_gap_exposure_share=float(risk.loc[positive,'adjacent_opening_upb'].sum()/risk.adjacent_opening_upb.sum()),
        near_zero_gap_exposure_share=float(risk.loc[near,'adjacent_opening_upb'].sum()/risk.adjacent_opening_upb.sum()),
        current_note_differs_from_original_loan_months=int((risk.lag_current_note_rate-risk.coupon).abs().gt(1e-10).sum()),
        gap_range_pp=[float(risk.current_note_gap_pp.min()),float(risk.current_note_gap_pp.max())],
        comparison_cells=len(cells),
        maximum_hinge_aggregation_difference_pp=float(cells.hinge_aggregation_difference_pp.max()),
        exposure_weighted_hinge_aggregation_difference_pp=float(np.average(cells.hinge_aggregation_difference_pp,weights=cells.adjacent_opening_upb)),
        exposure_weighted_current_note_rate_sd_pp=float(np.average(cells.current_note_rate_sd_pp,weights=cells.adjacent_opening_upb)),
        reference_estimated=False,response_parameters_estimated=False,
        qualification='Observed landmark-sample support and deterministic rate aggregation; no causal reference, offers, mechanism labels or portfolio inference')
    (output/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    follow.to_parquet(output/'private-followup-with-asof-gaps.parquet',index=False);(output/'private-followup-with-asof-gaps.parquet').chmod(0o600)
    (output/'REPORT.md').write_text('# Borrower follow-up and rate support\n\n'+
        f'For the {status["loans"]:,}-loan May2022 landmark sample: {status["counts"]["recorded_payoff"]:,} '
        f'recorded payoff exits; {status["counts"]["recorded_credit_exit"]} credit exit; '
        f'{status["counts"]["observed_active_at_cutoff"]:,} active at September2025 administrative censoring; '
        f'{status["counts"]["missing_followup_before_cutoff"]} missing earlier follow-up. '
        'Per-loan last dates and missing tails are in the private status artifact.\n\n'+
        f'The adjacent riskset has {len(risk):,} actual borrower-months. Event counts use matching adjacent '
        'borrower denominators; payoff dollars use adjacent opening principal. All-event, gap-timed and unknown-opening counts '
        'are separate. No aggregate cohort loan_count is used as a trial count.\n\n'+
        f'Positive lagged-current-note gaps occur in {summary["positive_current_note_gap_loan_months"]:,} borrower-months; '
        f'near-zero gaps (±0.25pp) in {summary["near_zero_current_note_gap_loan_months"]:,}. '
        f'The lagged current note rate differs from origination note rate in '
        f'{summary["current_note_differs_from_original_loan_months"]:,} borrower-months. '
        'Benchmark is the frozen prior-month weekly-rate mean, not a feasible borrower offer or verified real-time data vintage.\n\n'+
        f'Within {len(cells):,} selected-population stratum-month cells, the maximum difference between the '
        f'mean individual positive gap and positive gap at the mean current note rate is '
        f'{summary["maximum_hinge_aggregation_difference_pp"]:.8f}pp. '
        'This measures the positive-gap hinge, not a nonlinear hazard probability or estimated response. '
        'The comparison uses exactly the extracted sample, not the full origination-cohort panel.\n\n'+
        'The May-survivor selection prevents an unconditional pre-May reference. This restricted2021 sample '
        'does not establish earlier-vintage or SOMA coverage. Ordinary payoff cause, borrower offers/qualification, '
        'causal reference and response parameters remain unavailable. No parameter estimation was performed.\n')
    inputs={str(source):sha256(source),str(ratepath):sha256(ratepath),str(Path(__file__)):sha256(__file__),
            str(ROOT/'tests/test_borrower_panel_diagnostics.py'):sha256(ROOT/'tests/test_borrower_panel_diagnostics.py')}
    (output/'source-sha256.json').write_text(json.dumps(inputs,indent=2)+'\n')
    (output/'output-sha256.json').write_text(json.dumps({p.name:sha256(p) for p in sorted(output.iterdir())
        if p.is_file() and p.name!='output-sha256.json'},indent=2)+'\n')
    print(json.dumps(summary),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--pilot',type=Path,default=Path('output/empirical-grounding/2026-10-16/attempt-005-borrower-pilot'))
    parser.add_argument('--output',type=Path,default=Path('output/empirical-grounding/2026-10-16/attempt-005-borrower-pilot/diagnostics'))
    args=parser.parse_args();run(args.pilot,args.output)
