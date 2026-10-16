"""An explicitly new, non-landmark-conditioned origination-cohort support pilot."""
import argparse
import hashlib
import heapq
import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd

from borrower_panel_pilot import FrozenDecoder,stream_selected,prepare_followup,reconcile_landmark,require_headroom
from borrower_panel_diagnostics import add_asof_gaps,followup_status
from empirical_readiness import sha256

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/research-rerun/2026-10-14-archive'


def select_origination_ids(ids,*,n,seed):
    ids=list(ids)
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate eligible source identities')
    if isinstance(n,bool) or not isinstance(n,int) or not 0<n<=len(ids):raise ValueError('Invalid sample size')
    return sorted(heapq.nsmallest(n,ids,key=lambda i:hashlib.sha256((seed+'|'+str(i)).encode()).digest()))


def describe_landmark_selection(panel,*,selected_loans):
    result=dict(selected_origination_loans=selected_loans,may_active_loans=0,pre_may_payoff_loans=0,
        pre_may_credit_exit_loans=0,may_terminal_exit_loans=0,first_observed_after_may_loans=0,
        other_or_missing_may_loans=0,population_conditioned_on_may_survival=False)
    if panel.loan_id.nunique()!=selected_loans:raise ValueError('Selected loan denominator changed')
    for _,g in panel.groupby('loan_id',sort=False):
        pre=g[g.reporting_period<'202205'];may=g[g.reporting_period=='202205']
        if pre.recorded_payoff_event.sum():result['pre_may_payoff_loans']+=1
        elif pre.recorded_credit_exit.sum():result['pre_may_credit_exit_loans']+=1
        elif (may.recorded_payoff_event.sum()+may.recorded_credit_exit.sum()):result['may_terminal_exit_loans']+=1
        elif len(may) and (may.balance>0).any() and (~may.state.isin(['Prepaid','Defaulted','Liquidated'])).any():result['may_active_loans']+=1
        elif g.reporting_period.min()>'202205':result['first_observed_after_may_loans']+=1
        else:result['other_or_missing_may_loans']+=1
    assert sum(result[k] for k in result if k.endswith('_loans') and k!='selected_origination_loans')==selected_loans
    return result


def reference_support(panel):
    d=panel[panel.at_risk_adjacent & panel.current_note_gap_pp.notna() & panel.lag_loan_age.notna()]
    windows={'training':('202101','202112'),'development':('202201','202205'),'retrospective_evaluation':('202206','202509')}
    cells=[];diagnostics=[]
    for width in [.25,.5]:
        training=d[d.reporting_period.between(*windows['training']) & (d.current_note_gap_pp.abs()<=width)]
        lower=float(training.lag_loan_age.min()) if len(training) else None
        upper=float(training.lag_loan_age.max()) if len(training) else None
        for view,(start,end) in windows.items():
            selected=d[d.reporting_period.between(start,end) & (d.current_note_gap_pp.abs()<=width)]
            opening=float(selected.adjacent_opening_upb.sum());payoff=float(selected.adjacent_payoff_upb.sum())
            cells.append(dict(view=view,half_width_pp=width,rows=len(selected),loans=int(selected.loan_id.nunique()),
                calendar_months=int(selected.reporting_period.nunique()),recorded_payoff_events=int(selected.recorded_payoff_event.sum()),
                adjacent_opening_upb=opening,adjacent_payoff_upb=payoff,
                observed_amount_fraction=payoff/opening if opening>0 else None,
                observed_event_fraction=float(selected.recorded_payoff_event.mean()) if len(selected) else None,
                lag_age_min=float(selected.lag_loan_age.min()) if len(selected) else None,
                lag_age_max=float(selected.lag_loan_age.max()) if len(selected) else None))
        evaluation=d[d.reporting_period.between(*windows['retrospective_evaluation'])]
        age_ok=evaluation.lag_loan_age.between(lower,upper) if lower is not None else pd.Series(False,index=evaluation.index)
        near=evaluation.current_note_gap_pp.abs()<=width
        diagnostics.append(dict(half_width_pp=width,training_near_zero_age_range=[lower,upper],
            evaluation_rows=len(evaluation),evaluation_rows_within_training_age_range=int(age_ok.sum()),
            evaluation_near_zero_rows=int(near.sum()),evaluation_rows_both_near_zero_and_age_supported=int((near&age_ok).sum()),
            qualification='Age-range overlap is necessary descriptive coverage only, not joint identification or transport support'))
    return dict(cells=cells,coverage_diagnostics=diagnostics,causal_reference_estimated=False,
        reference_predictions_generated=False,prior_designated_support_verdict='insufficient_support',
        interpretation='Source-bound observed fractions under declared benchmark bands; not fitted or causal no-lock-in p0. No evaluation outcomes enter training summaries.')


def write(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def run(output):
    output=ROOT/output;require_headroom(shutil.disk_usage(ROOT).free,minimum=1024**3)
    output.mkdir(parents=True,exist_ok=False);output.chmod(0o700)
    quarter=BASE/'quarters/2021Q1';idsfile=quarter/'rebuilt/eligible_source_ids.parquet'
    receipt=json.loads((quarter/'completed.json').read_text())
    expected_ids=receipt['output_sha256']['rebuilt/eligible_source_ids.parquet']
    if sha256(idsfile)!=expected_ids:raise ValueError('Eligible source ID receipt mismatch')
    ids=pd.read_parquet(idsfile).loan_sequence_number.tolist()
    eligible=[i for i in ids if i.startswith('F21Q1')]
    seed='20261016-Q1-origination-reference';selected=select_origination_ids(eligible,n=5000,seed=seed)
    qreport=json.loads((quarter/'rebuilt/report.json').read_text());decoder=FrozenDecoder(quarter/'executed_code')
    if sha256(quarter/'rebuilt/report.json')!=receipt['output_sha256']['rebuilt/report.json']:
        raise ValueError('Quarter report hash mismatch')
    design=dict(status='design_frozen_before_source_outcomes',new_estimand=True,
        reason='Retain early exits instead of conditioning the reference candidate on May2022 survival',
        population='Accepted known360FRM eligible2021Q1-ID originals in physical2021Q1 source; approved2020-ID exception outside this declared vintage',
        eligible_ids=len(eligible),excluded_other_vintage_ids=len(ids)-len(eligible),selected_loans=5000,
        selection='Smallest SHA256(seed|loan_id), without replacement; independent of May survival and source ordering',seed=seed,
        sample_interpretation='Deterministic hash sample; no sampling confidence interval or population expansion weights estimated',
        source_start='202101',observed_cutoff='202509',training=['202101','202112'],development=['202201','202205'],evaluation=['202206','202509'],
        near_zero_gap_bands_pp=[.25,.5],benchmark_lag_months=1,
        decision_time_covariates='Prior adjacent active borrower observation',
        old_designated_verdict='insufficient_support retained for its original population',
        retrospective=True,causal_reference_fitting_authorized_by_support=False,
        local_stream_reserve_bytes=1024**3,raw_download_or_unpacking=False)
    write(output/'design.json',design)
    pd.DataFrame({'loan_id':selected}).to_parquet(output/'private-selected-ids.parquet',index=False);(output/'private-selected-ids.parquet').chmod(0o600)
    inputs=[idsfile,quarter/'completed.json',quarter/'rebuilt/report.json',quarter/'rebuilt/snapshot.parquet',
        ROOT/'hazard/borrower_origination_reference.py',ROOT/'tests/test_borrower_origination_reference.py',
        ROOT/'hazard/borrower_panel_pilot.py',ROOT/'hazard/borrower_panel_diagnostics.py']
    frozen={str(p.relative_to(ROOT)):sha256(p) for p in inputs};write(output/'input-sha256.json',frozen)
    archive=ROOT/'output/2021Q1-redownload-2026-10-13/historical_data_2021Q1.zip'
    records,scan=stream_selected(archive,set(selected),decoder,expected_hashes=qreport['source_sha256'],
        start='202101',resource_check=lambda:require_headroom(shutil.disk_usage(ROOT).free,minimum=1024**3))
    write(output/'source-scan.json',scan)
    records.to_parquet(output/'private-extracted-records.parquet',index=False);(output/'private-extracted-records.parquet').chmod(0o600)
    saved=pd.read_parquet(quarter/'rebuilt/snapshot.parquet',filters=[('loan_id','in',selected)])
    observed=records[(records.reporting_period=='202205') & (records.balance>0) & ~records.state.isin(['Prepaid','Defaulted','Liquidated'])]
    landmark=reconcile_landmark(observed,saved);write(output/'may-snapshot-validation.json',landmark)
    if not landmark['all_matched'] or landmark['absent_saved_fields']:raise ValueError('Observed May subset mismatch')
    panel,temporal=prepare_followup(records)
    selection=describe_landmark_selection(panel,selected_loans=5000);write(output/'landmark-selection.json',selection)
    status=followup_status(panel);pd.DataFrame(status.pop('private_details')).to_parquet(output/'private-followup-status.parquet',index=False)
    (output/'private-followup-status.parquet').chmod(0o600);write(output/'followup-status.json',status)
    prior=json.loads((ROOT/'output/research-next/2026-10-14/support/attempt-002/input_manifest.json').read_text())
    ratepath=next(Path(p) for p in prior['input_sha256'] if p.endswith('MORTGAGE30US_201612_202510.csv'))
    if sha256(ratepath)!=prior['input_sha256'][str(ratepath)]:raise ValueError('Frozen benchmark hash mismatch')
    rates=pd.read_csv(ratepath);months=pd.to_datetime(rates.observation_date).dt.strftime('%Y%m')
    benchmark=pd.to_numeric(rates.MORTGAGE30US,errors='coerce').groupby(months).mean().dropna()/100
    panel=add_asof_gaps(panel,benchmark)
    panel.to_parquet(output/'private-origination-borrower-panel.parquet',index=False);(output/'private-origination-borrower-panel.parquet').chmod(0o600)
    support=reference_support(panel);write(output/'reference-candidate-support.json',support)
    pd.DataFrame(support['cells']).to_csv(output/'reference-candidate-cells.csv',index=False)
    write(output/'temporal-audit.json',temporal)
    if not all(sha256(ROOT/p)==h for p,h in frozen.items()):raise ValueError('Frozen inputs changed')
    write(output/'benchmark-source.json',dict(path=str(ratepath),sha256=sha256(ratepath),lag_months=1,units='decimal',real_time_vintage_verified=False))
    (output/'REPORT.md').write_text('# Origination-cohort reference-support pilot\n\n'+
        f'This is a new retrospective {len(selected):,}-loan hash-selected sample of accepted2021Q1 eligible original loans. '
        'It is not conditioned on being active in May2022. The design, selection seed and ±0.25/±0.5pp bands were frozen before the new scan.\n\n'+
        f'Included pre-May2022 exits: {selection["pre_may_payoff_loans"]:,} recorded payoff loans and '
        f'{selection["pre_may_credit_exit_loans"]:,} credit-exit loans. '
        f'May-active selected loans: {selection["may_active_loans"]:,}; every saved May snapshot field matches for that observed subset. '
        'These are a different population from the earlier3829-loan May-survivor pilot.\n\n'+
        'reference-candidate-cells.csv reports separately measured training, development and retrospective-evaluation '
        'payoff counts and dollar fractions within the fixed benchmark-gap bands. These are observed descriptive rates, '
        'not an estimated no-lock-in reference. First-observed or nonadjacent event timing does not enter adjacent numerators. '
        'Training summaries use no development or evaluation outcomes.\n\n'+
        'The age-range coverage diagnostic tests only one necessary support dimension; it does not establish joint '
        'transport, favorable-refinancing controls, feasible offers or causal identification. The original designated '
        'insufficient-support verdict remains unchanged. No p0, share or gamma is fitted or projected.\n\n'+
        'The full compressed Q1 source was streamed with complete uncompressed hashes checked. No raw file was '
        'unpacked or downloaded. Only selected borrower records were saved with owner-only permissions. '
        'The local-only1GiB reserve ruling continues from the earlier pilot; acquisition/unpacking retains its separate reserve requirement.\n')
    write(output/'output-sha256.json',{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='output-sha256.json'})
    print(json.dumps(dict(selection=selection,status=status['counts'],reference_support=support)),flush=True)
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('output/empirical-grounding/2026-10-16/attempt-006-origination-reference'))
    run(parser.parse_args().output)
