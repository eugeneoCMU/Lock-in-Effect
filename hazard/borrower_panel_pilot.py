"""Bounded source-bound borrower measurement; no reference or response fitting."""
import argparse
import ast
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import time
import types
import zipfile

import numpy as np
import pandas as pd

from empirical_readiness import month_ordinal, sha256

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'output/research-rerun/2026-10-14-archive'
TERMINAL={'Prepaid','Defaulted','Liquidated'}


def require_headroom(free_bytes,*,minimum=4*1024**3):
    if minimum<1024**3:
        raise ValueError('Local-only reserve cannot be below 1 GiB')
    if free_bytes < minimum:
        raise RuntimeError(f'Borrower pilot requires at least {minimum/1024**3:g} GiB free')


def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


class FrozenDecoder:
    """Load original schema and exact helper definitions, without legacy imports."""
    def __init__(self,directory):
        directory=Path(directory)
        receipt=json.loads((directory.parent/'completed.json').read_text())['output_sha256']
        names=['schema.py','freddie_rebuild_stream.py','freddie_raw_quarter_audit.py','config.py']
        self.source_hashes={}
        for name in names:
            actual=sha256(directory/name)
            if actual!=receipt['executed_code/'+name]:
                raise ValueError('Frozen parser source hash mismatch')
            self.source_hashes[name]=actual
        self.schema=types.ModuleType('borrower_frozen_freddie_schema')
        exec(compile((directory/'schema.py').read_text(),str(directory/'schema.py'),'exec'),self.schema.__dict__)
        def helper(file,name):
            tree=ast.parse((directory/file).read_text())
            node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
            scope={'math':math}
            exec(compile(ast.Module(body=[node],type_ignores=[]),str(directory/file),'exec'),scope)
            return scope[name]
        self.state=helper('freddie_rebuild_stream.py','_state')
        self.finite=helper('freddie_raw_quarter_audit.py','finite')
        config=ast.parse((directory/'config.py').read_text())
        assignment=next(n for n in config.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='COUPON_STEP' for t in n.targets))
        self.coupon_step=ast.literal_eval(assignment.value)

    def origination(self,raw):
        r=self.schema.normalize_origination(raw.rstrip(b'\r\n').split(b'|'),'release47')
        f=self.finite;loan=r[19].decode();fico=f(r[0]);ltv=f(r[11]);rate=f(r[12]);term=f(r[21]);upb=f(r[10])
        if not (r[15]==b'FRM' and term==360 and upb and upb>0 and rate and rate>0 and fico is not None and ltv is not None):
            raise ValueError('Selected origination fails saved eligibility')
        vintage=int('20'+loan[1:3]);coupon=rate/100
        bucket=round(coupon/self.coupon_step)*self.coupon_step
        fico_bucket='<680' if fico<680 else '680-740' if fico<740 else '740+'
        ltv_bucket='≤80' if ltv<=80 else '>80'
        return dict(loan_id=loan,fico=fico,orig_ltv=ltv,coupon=coupon,orig_upb=upb,
            property_state=r[16].decode() or None,original_loan_term=term,vintage=vintage,
            cohort_coupon=bucket,fico_bucket=fico_bucket,ltv_bucket=ltv_bucket,
            stratum_id=f'{vintage}_{round(bucket*10000)}_{fico_bucket}_{ltv_bucket}')

    def performance(self,raw):
        r=raw.rstrip(b'\r\n').split(b'|')
        self.schema.validate_performance_semantics(r,'release47')
        r=self.schema.normalize_performance(r,'release47');f=self.finite
        rate=f(r[10]);balance=f(r[2])
        return dict(loan_id=r[0].decode(),reporting_period=r[1].decode(),balance=balance,
            loan_age=f(r[4]),state=self.state(r[3],r[29],r[8]),remaining_months=f(r[5]),
            current_note_rate=rate/100 if rate is not None else None,
            modification_flag=r[7].decode() or None,current_non_ib_upb=f(r[11]),
            interest_bearing_upb=f(r[31]),payment_deferral_flag=r[24].decode() or None,
            zero_balance_code=r[8].decode() or None)


def stream_selected(archive,selected_ids,decoder,*,expected_hashes,cutoff='202509',
                    start='202204',resource_check=None):
    selected={i.encode() for i in selected_ids};originals={};records=[];counts=Counter()
    hashes={};began=time.monotonic();last_group=None;groups=set()
    with zipfile.ZipFile(archive) as z:
        for kind,filename in [('origination','orig_2021Q1.txt'),('performance','perf_2021Q1.txt')]:
            if resource_check:resource_check()
            h=hashlib.sha256()
            with z.open(filename) as stream:
                for raw in stream:
                    h.update(raw);counts[kind+'_source_rows']+=1
                    if kind=='origination':
                        prefix=raw.split(b'|',20)
                        if len(prefix)<20:raise ValueError('Source origination identity missing')
                        loan=prefix[19]
                    else:
                        loan=raw.partition(b'|')[0]
                    if loan in selected:
                        if kind=='origination':
                            if loan in originals:raise ValueError('Duplicate selected origination')
                            originals[loan]=decoder.origination(raw)
                        else:
                            if loan!=last_group:
                                if loan in groups:raise ValueError('Selected source loan group reentry')
                                groups.add(loan);last_group=loan
                            pieces=raw.split(b'|',2)
                            month=pieces[1].decode();month_ordinal(month)
                            if month>cutoff:
                                counts['post_cutoff_selected_rows']+=1
                            elif month<start:
                                counts['before_start_selected_rows']+=1
                            else:
                                row=decoder.performance(raw)
                                if loan not in originals:raise ValueError('Selected performance has no origination')
                                row.update(originals[loan]);records.append(row)
                                counts['decoded_selected_rows']+=1
                    if counts[kind+'_source_rows']%2000000==0:
                        if resource_check:resource_check()
                        print(json.dumps(dict(phase=kind,scanned_rows=counts[kind+'_source_rows'],
                            retained_rows=len(records),elapsed_seconds=round(time.monotonic()-began,1))),flush=True)
            hashes[kind]=h.hexdigest()
            if hashes[kind]!=expected_hashes[kind]:raise ValueError(kind+' source hash mismatch')
    if set(originals)!=selected:raise ValueError('Selected originations missing')
    d=pd.DataFrame(records)
    if set(d.loan_id)!=set(selected_ids):raise ValueError('Selected follow-up missing')
    return d,dict(counts,source_hashes_verified=True,source_sha256=hashes,
        elapsed_seconds=time.monotonic()-began,cutoff=cutoff,earliest_retained=start,
        max_decoded_month=str(d.reporting_period.max()),selected_loans=len(selected),
        parser_source_sha256=decoder.source_hashes)


def prepare_followup(data):
    d=data.copy();d['reporting_period']=d.reporting_period.astype(str)
    if d.duplicated(['loan_id','reporting_period']).any():raise ValueError('Duplicate loan-month')
    rows=[];audit=Counter()
    for _,group in d.groupby('loan_id',sort=False):
        previous=None;ever_terminal=False
        months=group.reporting_period.map(month_ordinal).to_numpy()
        if len(months)>1 and np.any(np.diff(months)<=0):raise ValueError('Backward loan-months')
        for row in group.to_dict('records'):
            month=month_ordinal(row['reporting_period']);terminal=row['state'] in TERMINAL
            if ever_terminal and not terminal:raise ValueError('Terminal revival in selected history')
            adjacent=previous is not None and month-previous['_month']==1
            if previous is not None:audit['missing_calendar_months']+=max(0,month-previous['_month']-1)
            prior_balance=previous['balance'] if previous else None
            valid_balance=prior_balance is not None and np.isfinite(prior_balance) and prior_balance>0
            active_prior=previous is not None and previous['state'] not in TERMINAL and valid_balance
            payoff=row['state']=='Prepaid' and not ever_terminal
            credit=row['state'] in {'Defaulted','Liquidated'} and not ever_terminal
            at_risk=bool(adjacent and active_prior)
            new=dict(row,adjacent_prior=adjacent,at_risk_adjacent=at_risk,
                adjacent_opening_upb=float(prior_balance) if at_risk else 0.,
                recorded_payoff_event=int(payoff),recorded_credit_exit=int(credit),
                adjacent_payoff_upb=float(prior_balance) if payoff and at_risk else 0.,
                timing_unallocated_payoff_upb=float(prior_balance) if payoff and active_prior and not adjacent else 0.,
                payoff_without_known_opening=bool(payoff and not active_prior),
                lag_current_note_rate=previous.get('current_note_rate') if adjacent and active_prior else None,
                lag_loan_age=previous.get('loan_age') if adjacent and active_prior else None,
                repeated_terminal_row=bool(terminal and ever_terminal))
            rows.append(new);previous=dict(row,_month=month);ever_terminal|=terminal
            audit['repeated_terminal_rows']+=int(new['repeated_terminal_row'])
    out=pd.DataFrame(rows)
    audit.update(rows=len(out),loans=int(out.loan_id.nunique()),duplicate_rows=0,terminal_revivals=0)
    return out,dict(audit)


def reconcile_landmark(panel,saved,month='202205'):
    observed=panel[panel.reporting_period.astype(str)==month].copy()
    if observed.loan_id.duplicated().any() or saved.loan_id.duplicated().any():
        raise ValueError('Duplicate snapshot identities')
    columns=[c for c in saved if c in observed and c not in {'loan_id'}]
    joined=saved.merge(observed,on='loan_id',how='outer',suffixes=('_saved','_extracted'),indicator=True)
    mismatches={};bad=joined['_merge'].ne('both').to_numpy()
    for c in columns:
        a=joined[c+'_saved'];b=joined[c+'_extracted']
        if pd.api.types.is_numeric_dtype(a):
            same=np.isclose(pd.to_numeric(a).to_numpy(float),pd.to_numeric(b).to_numpy(float),
                rtol=1e-12,atol=.01 if c in {'balance','orig_upb','interest_bearing_upb','current_non_ib_upb'} else 1e-9,equal_nan=True)
        else:same=(a.fillna('<NULL>').astype(str)==b.fillna('<NULL>').astype(str)).to_numpy()
        mismatches[c]=int((~same).sum());bad|=~same
    return dict(all_matched=not bool(bad.any()),matched_loans=int((~bad).sum()),mismatch_rows=int(bad.sum()),
        saved_loans=len(saved),observed_loans=len(observed),compared_fields=columns,
        absent_saved_fields=[c for c in saved if c not in observed],field_mismatches=mismatches)


def run(output,*,local_stream_reserve_gib=4):
    output=ROOT/output
    minimum=local_stream_reserve_gib*1024**3
    require_headroom(shutil.disk_usage(ROOT).free,minimum=minimum)
    output.mkdir(parents=True,exist_ok=False);output.chmod(0o700)
    quarter=BASE/'quarters/2021Q1';qreport=json.loads((quarter/'rebuilt/report.json').read_text())
    sample_path=BASE/'combined/loan_sample.parquet';source_ids=quarter/'rebuilt/eligible_source_ids.parquet'
    sample=pd.read_parquet(sample_path);ids=set(pd.read_parquet(source_ids).loan_sequence_number)
    selected=sample[sample.loan_id.isin(ids)].copy()
    if len(selected)!=3829:raise ValueError('Frozen pilot membership changed')
    decoder=FrozenDecoder(quarter/'executed_code')
    archive=ROOT/'output/2021Q1-redownload-2026-10-13/historical_data_2021Q1.zip'
    inputs=[sample_path,source_ids,quarter/'rebuilt/report.json',quarter/'completed.json',
            quarter/'rebuilt/snapshot.parquet',ROOT/'hazard/borrower_panel_pilot.py',ROOT/'tests/test_borrower_panel_pilot.py']
    freeze={str(p.relative_to(ROOT)):sha256(p) for p in inputs}
    write_json(output/'input-manifest.json',dict(input_sha256=freeze,archive=str(archive),archive_bytes=archive.stat().st_size,
        expected_uncompressed_source_sha256=qreport['source_sha256'],selected_loans=len(selected),
        population='2021Q1 source members of May2022 survivor-selected75k sample',cutoff='202509',
        status='running',minimum_free_bytes=minimum,
        resource_ruling='Explicit local-only reserve; no download or unpacking. User directed continuation with available space; 4GiB remains default for acquisition/unpacking.'))
    data,scan=stream_selected(archive,set(selected.loan_id),decoder,expected_hashes=qreport['source_sha256'],
        resource_check=lambda:require_headroom(shutil.disk_usage(ROOT).free,minimum=minimum))
    write_json(output/'source-scan.json',scan)
    snapshot_fields=pd.read_parquet(quarter/'rebuilt/snapshot.parquet').columns.tolist()
    reconciliation=reconcile_landmark(data,selected[snapshot_fields])
    write_json(output/'snapshot-reconciliation.json',reconciliation)
    data.to_parquet(output/'private-extracted-records.parquet',index=False);(output/'private-extracted-records.parquet').chmod(0o600)
    if not reconciliation['all_matched'] or reconciliation['absent_saved_fields']:
        raise ValueError('May snapshot reconciliation failed; private extracted evidence retained')
    panel,temporal=prepare_followup(data)
    panel.to_parquet(output/'private-borrower-panel.parquet',index=False);(output/'private-borrower-panel.parquet').chmod(0o600)
    follow=panel[panel.reporting_period.between('202206','202509')].copy()
    summary=dict(status='source_bound_borrower_measurement_complete',population='3829 selected May2022 survivors from physical source2021Q1',
        cutoff='202509',retained_records=len(panel),followup_records=len(follow),temporal=temporal,
        adjacent_loan_months=int(follow.at_risk_adjacent.sum()),recorded_payoff_events=int(follow.recorded_payoff_event.sum()),
        recorded_credit_exits=int(follow.recorded_credit_exit.sum()),
        adjacent_opening_upb=float(follow.adjacent_opening_upb.sum()),adjacent_payoff_upb=float(follow.adjacent_payoff_upb.sum()),
        timing_unallocated_payoff_upb=float(follow.timing_unallocated_payoff_upb.sum()),
        payoff_without_known_opening=int(follow.payoff_without_known_opening.sum()),
        missing_lag_note_rate_at_risk=int(follow.loc[follow.at_risk_adjacent,'lag_current_note_rate'].isna().sum()),
        missing_lag_age_at_risk=int(follow.loc[follow.at_risk_adjacent,'lag_loan_age'].isna().sum()),
        unchanged_inputs=all(sha256(ROOT/p)==h for p,h in freeze.items()),
        reference_estimated=False,sensitive_share_estimated=False,gamma_estimated=False,security_receipts_verified=False,
        qualification='Landmark survivor sample; retrospective recorded payoff measurement, ordinary payoff cause unknown')
    if not summary['unchanged_inputs']:raise ValueError('Inputs changed during pilot')
    monthly=follow.groupby('reporting_period').agg(adjacent_loan_months=('at_risk_adjacent','sum'),
        payoff_events=('recorded_payoff_event','sum'),credit_exits=('recorded_credit_exit','sum'),
        opening_upb=('adjacent_opening_upb','sum'),payoff_upb=('adjacent_payoff_upb','sum'),
        unallocated_payoff_upb=('timing_unallocated_payoff_upb','sum'))
    monthly['amount_weighted_fraction']=monthly.payoff_upb/monthly.opening_upb.where(monthly.opening_upb>0)
    monthly.to_csv(output/'monthly-measurement.csv')
    write_json(output/'summary.json',summary)
    (output/'REPORT.md').write_text('# Bounded Q1 borrower measurement\n\n'+
        f'Accepted source hashes and all May snapshot fields match for {len(selected):,} selected loans. '
        f'The panel retains {len(panel):,} records, with {len(follow):,} follow-up records through September2025. '
        f'Adjacent at-risk loan-months: {summary["adjacent_loan_months"]:,}; '
        f'recorded payoff events: {summary["recorded_payoff_events"]:,}; source credit exits: {summary["recorded_credit_exits"]:,}.\n\n'+
        'This is a May2022 survivor-selected subset of one physical source quarter. It is not an unconditional '
        'origination-cohort reference, borrower causal elasticity, sale/refinance decomposition or SOMA receipt result. '
        'Individual covariates use the preceding adjacent active observation; unknown gaps remain unallocated. '
        'Repeated terminal rows never create additional payoffs. October–November2025 remains outside the cutoff.\n\n'+
        'The complete compressed members were streamed and their uncompressed hashes checked. No raw text was '
        'unpacked or downloaded. The private artifacts contain loan identifiers and have owner-only permissions. '
        'The original files and manuscripts were not changed.\n')
    write_json(output/'output-sha256.json',{p.name:sha256(p) for p in sorted(output.iterdir()) if p.is_file() and p.name!='output-sha256.json'})
    print(json.dumps(summary),flush=True)
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('output/empirical-grounding/2026-10-16/attempt-005-borrower-pilot'))
    parser.add_argument('--local-stream-reserve-gib',type=int,default=4)
    args=parser.parse_args()
    run(args.output,local_stream_reserve_gib=args.local_stream_reserve_gib)
