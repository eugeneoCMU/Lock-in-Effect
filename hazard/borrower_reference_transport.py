"""Descriptive covariate coverage of a frozen near-zero-gap training candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import datetime

import numpy as np
import pandas as pd


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def audit_reference_transport(panel,*,training_start='202101'):
    required=['loan_id','reporting_period','at_risk_adjacent','current_note_gap_pp','lag_loan_age',
              'fico_bucket','ltv_bucket','property_state','adjacent_opening_upb']
    d=panel[required].copy()
    if d.duplicated(['loan_id','reporting_period']).any():raise ValueError('Duplicate loan-month')
    if not np.isfinite(d.adjacent_opening_upb).all() or (d.adjacent_opening_upb<0).any():
        raise ValueError('Invalid opening exposure')
    d=d[d.at_risk_adjacent].copy()
    age=pd.to_numeric(d.lag_loan_age,errors='coerce')
    d['age_bin_6m']=np.floor(age/6).where(np.isfinite(age)&(age>=0))
    evaluation=d[d.reporting_period.between('202206','202509')]
    views={'age':['age_bin_6m'],'age_fico_ltv':['age_bin_6m','fico_bucket','ltv_bucket'],
           'age_fico_ltv_state':['age_bin_6m','fico_bucket','ltv_bucket','property_state']}
    coverage=[]
    for width in [.25,.5]:
        train=d[d.reporting_period.between(training_start,'202112') & (d.current_note_gap_pp.abs()<=width)]
        lo=float(train.lag_loan_age.min()) if len(train) else None
        hi=float(train.lag_loan_age.max()) if len(train) else None
        for label,cols in views.items():
            validtrain=train.dropna(subset=cols)
            keys=set(validtrain[cols].itertuples(index=False,name=None))
            mask=evaluation[cols].notna().all(axis=1)
            mask &= pd.Series([k in keys for k in evaluation[cols].itertuples(index=False,name=None)],index=evaluation.index)
            mask &= evaluation.lag_loan_age.between(lo,hi) if lo is not None else False
            total=float(evaluation.adjacent_opening_upb.sum())
            supported=float(evaluation.loc[mask,'adjacent_opening_upb'].sum())
            coverage.append(dict(half_width_pp=width,controls=label,training_rows=len(train),
                training_complete_covariate_rows=len(validtrain),training_distinct_cells=len(keys),
                training_age_min=lo,training_age_max=hi,evaluation_rows=len(evaluation),
                supported_rows=int(mask.sum()),unsupported_rows=int((~mask).sum()),
                evaluation_opening_upb=total,supported_opening_upb=supported,unsupported_opening_upb=total-supported,
                supported_exposure_fraction=supported/total if total else None,
                supported_row_fraction=float(mask.mean()) if len(mask) else None))
    return dict(coverage=coverage,causal_reference_estimated=False,reference_predictions_generated=False,
        prior_designated_support_verdict='insufficient_support',
        interpretation='Descriptive coarse covariate overlap only; any training presence is not sample adequacy, exchangeability, offer feasibility, or causal transport. Target outcomes are not read.',
        design=dict(training=[training_start,'202112'],excluded_development=['202201','202205'],
            evaluation=['202206','202509'],near_zero_bands_pp=[.25,.5],age_bin_months=6,
            additional_age_rule='Target age must also lie within observed training age min/max',
            missing_covariates='Unsupported; missing values never match',minimum_training_presence_rows=1,
            denominator='Adjacent at-risk opening UPB loan-month exposure, not distinct portfolio principal',
            design_status='Retrospective diagnostic after original pilot; no causal estimator or parameter fit'))


def run(source,output):
    source=Path(source);output=Path(output)
    if source.resolve()==output.resolve():raise ValueError('New output directory required')
    seal=json.loads((source/'output-sha256.json').read_text())
    for name,expected in seal.items():
        if Path(name).name!=name or sha(source/name)!=expected:raise ValueError('Prior output seal mismatch: '+name)
    output.mkdir(parents=True,exist_ok=False);output.chmod(0o700)
    script=Path(__file__)
    shutil.copyfile(script,output/'executed_borrower_reference_transport.py')
    panelpath=source/'private-origination-borrower-panel.parquet'
    panel=pd.read_parquet(panelpath)
    result=audit_reference_transport(panel)
    (output/'coverage.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(result['coverage']).to_csv(output/'coverage.csv',index=False)
    receipt=dict(source_folder=str(source),source_output_seal_sha256=sha(source/'output-sha256.json'),
        source_panel_sha256=sha(panelpath),executed_code_sha256=sha(script),prior_output_hashes_verified=len(seal),
        created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    report='Reference candidate transport coverage\n\nTraining: Jan-Dec2021, fixed near-zero gap bands ±0.25 and ±0.5 percentage points. Evaluation: June2022-Sep2025. Development outcomes excluded.\n\n'
    for r in result['coverage']:
        report+=f"{r['half_width_pp']}pp, {r['controls']}: {r['supported_rows']}/{r['evaluation_rows']} target loan-months and {r['supported_exposure_fraction']:.8%} of opening-UPB exposure overlap this coarse training screen. Unsupported exposure remains in the denominator.\n"
    report+='\nThese are descriptive coverage measures. Any training presence does not demonstrate adequate sample size or causal reference support. Six-month age bins are a declared coarse screen, with an additional observed age-range check. No p0, share, gamma, or portfolio effect is fitted. Older cohorts with pre-QT observations at the target ages and rate gaps are the next source candidate, subject to their own inventory and support audit.\n'
    (output/'REPORT.md').write_text(report)
    final={p.name:sha(p) for p in output.iterdir() if p.is_file()}
    (output/'output-sha256.json').write_text(json.dumps(final,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    print('COMPLETE: transport audit hashes written to '+str(output),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();run(args.source,args.output)
