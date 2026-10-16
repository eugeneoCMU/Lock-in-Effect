"""Bounded older-vintage cloud extraction; descriptive training coverage only."""
import json
from pathlib import Path
import hashlib
import datetime
import time
import shutil
from collections import Counter

import pandas as pd

from borrower_panel_pilot import FrozenDecoder,prepare_followup,reconcile_landmark
from borrower_origination_reference import select_origination_ids
from borrower_panel_diagnostics import add_asof_gaps,followup_status
from borrower_reference_transport import audit_reference_transport,sha
from empirical_readiness import month_ordinal


class Native32Decoder(FrozenDecoder):
    def origination(self,raw):
        r=raw.rstrip(b'\r\n').split(b'|')
        if len(r)!=32:raise ValueError('Expected native32 origination')
        f=self.finite;loan=r[19].decode();fico=f(r[0]);ltv=f(r[11]);rate=f(r[12]);term=f(r[21]);upb=f(r[10])
        if not(r[15]==b'FRM' and term==360 and upb and upb>0 and rate and rate>0 and fico is not None and ltv is not None):
            raise ValueError('Selected origination fails saved eligibility')
        vintage=int('20'+loan[1:3]);coupon=rate/100;bucket=round(coupon/self.coupon_step)*self.coupon_step
        fico_bucket='<680' if fico<680 else '680-740' if fico<740 else '740+'
        ltv_bucket='≤80' if ltv<=80 else '>80'
        return dict(loan_id=loan,fico=fico,orig_ltv=ltv,coupon=coupon,orig_upb=upb,
            property_state=r[16].decode() or None,original_loan_term=term,vintage=vintage,
            cohort_coupon=bucket,fico_bucket=fico_bucket,ltv_bucket=ltv_bucket,
            stratum_id=f'{vintage}_{round(bucket*10000)}_{fico_bucket}_{ltv_bucket}')

    def performance(self,raw):
        r=raw.rstrip(b'\r\n').split(b'|')
        if len(r)!=32:raise ValueError('Expected native32 performance')
        self.schema.validate_performance_semantics(r);f=self.finite;rate=f(r[10])
        return dict(loan_id=r[0].decode(),reporting_period=r[1].decode(),balance=f(r[2]),
            loan_age=f(r[4]),state=self.state(r[3],r[29],r[8]),remaining_months=f(r[5]),
            current_note_rate=rate/100 if rate is not None else None,
            modification_flag=r[7].decode() or None,current_non_ib_upb=f(r[11]),
            interest_bearing_upb=f(r[31]),payment_deferral_flag=r[24].decode() or None,
            zero_balance_code=r[8].decode() or None)


def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def run(root,drive_root,*,sample_size=5000):
    if isinstance(sample_size,bool) or not isinstance(sample_size,int) or not 0<sample_size<=50000:
        raise ValueError('Invalid bounded cloud sample size')
    root=Path(root);drive_root=Path(drive_root)
    quarter=root/'output/research-rerun/2026-10-14-archive/quarters/2018Q1'
    receipt=json.loads((quarter/'completed.json').read_text())['output_sha256']
    for name in ['rebuilt/eligible_source_ids.parquet','rebuilt/report.json','rebuilt/snapshot.parquet']:
        if sha(quarter/name)!=receipt[name]:raise ValueError('Prior receipt mismatch: '+name)
    report=json.loads((quarter/'rebuilt/report.json').read_text());decoder=Native32Decoder(quarter/'executed_code')
    ids=pd.read_parquet(quarter/'rebuilt/eligible_source_ids.parquet').loan_sequence_number.tolist()
    ids=[i for i in ids if i.startswith('F18Q1')]
    selected=select_origination_ids(ids,n=sample_size,seed='20261016-2018Q1-origination-support')
    target=drive_root/'Lock-in-Effect cloud results/origination-reference-20261016T151834Z'
    target_seal=json.loads((target/'output-sha256.json').read_text())
    panel_name='private-origination-borrower-panel.parquet'
    if sha(target/panel_name)!=target_seal[panel_name]:raise ValueError('Target panel hash mismatch')
    sources={kind:drive_root/'Fannie and Freddie MAC'/f'{prefix}_2018Q1.txt'
        for kind,prefix in [('origination','orig'),('performance','perf')]}
    for p in sources.values():
        if not p.is_file():raise ValueError('Drive source not mounted: '+str(p))
    if shutil.disk_usage('/content').free<4*1024**3:raise RuntimeError('Insufficient cloud storage')
    output=drive_root/'Lock-in-Effect cloud results'/(f'older-2018Q1-n{sample_size}-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(exist_ok=False);output.chmod(0o700)
    design=dict(selected_loans=sample_size,seed='20261016-2018Q1-origination-support',source_vintage='2018Q1',
        expansion_status='Exploratory nested hash expansion after 5000-loan cell-sparsity diagnostic; not an untouched confirmatory sample',
        population='Hash sample of accepted eligible F18Q1 origination IDs, independent of May survival',
        selection_frozen_before_outcomes=True,source_start='201801',cutoff='202509',
        training_views=[['202101','202112'],['201801','202112']],development_excluded=['202201','202205'],
        target_population='Existing 5000-loan 2021Q1 origination sample, June2022-Sep2025 riskset unchanged',
        bands_pp=[.25,.5],age_bins_months=6,causal_fitting=False,
        interpretation='Retrospective source-bound covariate coverage; no sampling expansion or causal identification')
    write(output/'design.json',design)
    pd.DataFrame({'loan_id':selected}).to_parquet(output/'private-selected-ids.parquet',index=False)
    selected_bytes={s.encode() for s in selected};originals={};records=[];counts=Counter();source_hashes={}
    started=time.monotonic()
    for kind,path in sources.items():
        h=hashlib.sha256();last=None;groups=set()
        with path.open('rb') as f:
            for raw in f:
                h.update(raw);counts[kind+'_rows']+=1
                fields=raw.split(b'|',20) if kind=='origination' else raw.split(b'|',2)
                loan=fields[19] if kind=='origination' else fields[0]
                if loan in selected_bytes:
                    if kind=='origination':
                        key=loan.decode()
                        if key in originals:raise ValueError('Duplicate selected origination')
                        originals[key]=decoder.origination(raw)
                    else:
                        if loan!=last:
                            if loan in groups:raise ValueError('Performance group reentry')
                            groups.add(loan);last=loan
                        month=fields[1].decode();month_ordinal(month)
                        if '201801'<=month<='202509':
                            row=decoder.performance(raw);row.update(originals[loan.decode()]);records.append(row)
                        else:counts['outside_cutoff_selected_rows']+=1
                if counts[kind+'_rows']%2000000==0:
                    print(json.dumps(dict(phase=kind,rows=counts[kind+'_rows'],retained=len(records))),flush=True)
        source_hashes[kind]=h.hexdigest()
        if source_hashes[kind]!=report['source_sha256'][kind]:raise ValueError('Full source hash mismatch')
    if set(originals)!=set(selected):raise ValueError('Selected originals missing')
    if counts['origination_rows']!=report['counts']['origination_rows'] or counts['performance_rows']!=report['counts']['performance_rows']:
        raise ValueError('Full source row count mismatch')
    records=pd.DataFrame(records)
    if set(records.loan_id)!=set(selected):raise ValueError('Selected histories missing')
    observed=records[(records.reporting_period=='202205') & (records.balance>0) & ~records.state.isin(['Prepaid','Defaulted','Liquidated'])]
    saved=pd.read_parquet(quarter/'rebuilt/snapshot.parquet',filters=[('loan_id','in',selected)])
    landmark=reconcile_landmark(observed,saved)
    if not landmark['all_matched'] or landmark['absent_saved_fields']:raise ValueError('Saved May fields mismatch')
    write(output/'may-snapshot-validation.json',landmark)
    panel,temporal=prepare_followup(records);write(output/'temporal-audit.json',temporal)
    rate_info=json.loads((root/'cloud-benchmark-location.json').read_text())
    ratepath=root/'cloud-benchmark.csv'
    if sha(ratepath)!=rate_info['sha256']:raise ValueError('Benchmark hash mismatch')
    rates=pd.read_csv(ratepath);months=pd.to_datetime(rates.observation_date).dt.strftime('%Y%m')
    benchmark=pd.to_numeric(rates.MORTGAGE30US,errors='coerce').groupby(months).mean().dropna()/100
    panel=add_asof_gaps(panel,benchmark)
    panel.to_parquet(output/'private-older-borrower-panel.parquet',index=False)
    status=followup_status(panel);private=pd.DataFrame(status.pop('private_details'))
    private.to_parquet(output/'private-followup-status.parquet',index=False);write(output/'followup-status.json',status)
    target_panel=pd.read_parquet(target/panel_name)
    # Older evaluation rows are excluded so the target denominator never expands.
    combined=pd.concat([target_panel,panel[panel.reporting_period<='202112']],ignore_index=True)
    result={start:audit_reference_transport(combined,training_start=start) for start in ['202101','201801']}
    for start,audit in result.items():
        if any(r['evaluation_rows']!=172640 for r in audit['coverage']):raise ValueError('Target denominator changed')
    write(output/'target-coverage.json',result)
    write(output/'source-scan.json',dict(counts,source_sha256=source_hashes,source_hashes_verified=True,
        selected_loans=sample_size,retained_rows=len(panel),elapsed_seconds=time.monotonic()-started,
        source_paths={k:str(v) for k,v in sources.items()},benchmark_sha256=sha(ratepath)))
    for p in (root/'hazard').glob('*.py'):
        if p.name!='older_borrower_cloud.py':shutil.copyfile(p,output/('executed_'+p.name))
    shutil.copyfile(__file__,output/'executed_older_borrower_cloud.py')
    for p in output.glob('private-*'):p.chmod(0o600)
    summary=f'2018Q1 cloud borrower extension\n\n{sample_size} loans sampled independently of May survival. Full original source hashes, row counts and saved May fields validated. No causal reference or response fitted.\n\n'
    for start,audit in result.items():
        for r in audit['coverage']:
            summary+=f"Training from {start}, band {r['half_width_pp']}pp, {r['controls']}: {r['supported_rows']}/{r['evaluation_rows']} target loan-months; {r['supported_exposure_fraction']:.8%} of opening-UPB exposure.\n"
    (output/'REPORT.md').write_text(summary)
    write(output/'output-sha256.json',{p.name:sha(p) for p in output.iterdir() if p.is_file()})
    print(json.dumps(dict(output=str(output),status=status,coverage=result)),flush=True)
    print('COMPLETE: older source pilot saved; no causal reference fitted.',flush=True)
    return output
