"""Retrospective cell-size diagnostics; no reference fit or causal acceptance."""
import json
from pathlib import Path
import hashlib
import shutil
import datetime
import numpy as np
import pandas as pd

SCREENS=[('presence',1,1,0),('10loans_3months_1event',10,3,1),('30loans_6months_5events',30,6,5)]
CONTROLS=['age_bin_6m','fico_bucket','ltv_bucket','property_state']


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def audit_cell_adequacy(panel):
    # Evaluation outcomes never enter the working frame.
    cols=['loan_id','reporting_period','at_risk_adjacent','current_note_gap_pp','lag_loan_age',
          'fico_bucket','ltv_bucket','property_state','adjacent_opening_upb']
    d=panel[cols].copy()
    if d.duplicated(['loan_id','reporting_period']).any():raise ValueError('Duplicate loan-month')
    if not np.isfinite(d.adjacent_opening_upb).all() or (d.adjacent_opening_upb<0).any():raise ValueError('Invalid opening exposure')
    d=d[d.at_risk_adjacent & (d.adjacent_opening_upb>0)].copy()
    ages=pd.to_numeric(d.lag_loan_age,errors='coerce')
    d['age_bin_6m']=np.floor(ages/6).where(np.isfinite(ages)&(ages>=0))
    target=d[d.reporting_period.between('202206','202509')]
    total=float(target.adjacent_opening_upb.sum());coverage=[];cells=[]
    for width in [.25,.5]:
        train=d[d.reporting_period.between('201801','202112') & (d.current_note_gap_pp.abs()<=width)].copy()
        train['training_payoff']=panel.loc[train.index,'recorded_payoff_event'].astype(int)
        if not train.training_payoff.isin([0,1]).all():raise ValueError('Invalid training event')
        lo=float(train.lag_loan_age.min()) if len(train) else None
        hi=float(train.lag_loan_age.max()) if len(train) else None
        mapped={}
        for key,g in train.dropna(subset=CONTROLS).groupby(CONTROLS,sort=True):
            byloan=g.groupby('loan_id').adjacent_opening_upb.sum()
            bymonth=g.groupby('reporting_period').adjacent_opening_upb.sum()
            exposure=float(byloan.sum())
            cell=dict(half_width_pp=width,age_bin_6m=int(key[0]),fico_bucket=key[1],ltv_bucket=key[2],property_state=key[3],
                training_rows=len(g),training_loans=int(g.loan_id.nunique()),training_calendar_months=int(g.reporting_period.nunique()),
                training_payoff_events=int(g.training_payoff.sum()),training_opening_upb=exposure,
                concentration_equivalent_loans=float(exposure**2/(byloan**2).sum()),
                largest_month_exposure_fraction=float(bymonth.max()/exposure))
            cells.append(cell);mapped[key]=cell
        complete=target[CONTROLS].notna().all(axis=1)
        age_ok=target.lag_loan_age.between(lo,hi) if lo is not None else pd.Series(False,index=target.index)
        keys=list(target[CONTROLS].itertuples(index=False,name=None))
        for name,minloans,minmonths,minevents in SCREENS:
            ok={k for k,v in mapped.items() if v['training_loans']>=minloans and v['training_calendar_months']>=minmonths and v['training_payoff_events']>=minevents}
            mask=complete & age_ok & pd.Series([k in ok for k in keys],index=target.index)
            supported=float(target.loc[mask,'adjacent_opening_upb'].sum())
            coverage.append(dict(half_width_pp=width,screen=name,training_cells=len(mapped),cells_passing=len(ok),
                evaluation_rows=len(target),supported_rows=int(mask.sum()),unsupported_rows=int((~mask).sum()),
                evaluation_opening_upb=total,supported_opening_upb=supported,unsupported_opening_upb=total-supported,
                supported_exposure_fraction=supported/total if total else None))
    return dict(coverage=coverage,cells=cells,causal_reference_estimated=False,reference_predictions_generated=False,
        design=dict(training=['201801','202112'],development_excluded=['202201','202205'],evaluation=['202206','202509'],
            age_bin_months=6,controls=CONTROLS,near_zero_bands_pp=[.25,.5],
            screens=[dict(name=n,minimum_distinct_loans=l,minimum_calendar_months=m,minimum_training_payoff_events=e) for n,l,m,e in SCREENS],
            age_rule='Also require target age within global observed near-zero training age range',
            zero_exposure_rows='Excluded from training presence and riskset denominator',
            interpretation='Retrospective sensitivity screens chosen before this audit, not confidence criteria or causal adequacy. Presence does not establish within-cell age or calendar overlap.',
            concentration='Exposure-concentration equivalent loan count only, not an inferential effective sample size',
            event_screen='Uses training payoff events only; outcome-dependent descriptive screening, not a causal selection rule',
            denominator='Adjacent at-risk opening UPB summed across target loan-months, not distinct portfolio principal'))


def run(drive_root):
    root=Path(drive_root)/'Lock-in-Effect cloud results'
    sources=[(root/'origination-reference-20261016T151834Z','private-origination-borrower-panel.parquet'),
             (root/'older-2018Q1-20261016T153853Z','private-older-borrower-panel.parquet')]
    frames=[];receipts=[]
    for folder,name in sources:
        seal=json.loads((folder/'output-sha256.json').read_text())
        if name not in seal:raise ValueError('Required panel absent from seal')
        for n,h in seal.items():
            if Path(n).name!=n or sha(folder/n)!=h:raise ValueError('Prior output seal mismatch: '+n)
        frame=pd.read_parquet(folder/name)
        if name=='private-older-borrower-panel.parquet':frame=frame[frame.reporting_period<='202112']
        frames.append(frame)
        receipts.append(dict(folder=str(folder),panel=name,panel_sha256=sha(folder/name),seal_sha256=sha(folder/'output-sha256.json')))
    combined=pd.concat(frames,ignore_index=True)
    result=audit_cell_adequacy(combined)
    if any(r['evaluation_rows']!=172640 for r in result['coverage']):raise ValueError('Target denominator changed')
    output=root/('reference-cell-adequacy-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(exist_ok=False);output.chmod(0o700)
    (output/'adequacy.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(result['coverage']).to_csv(output/'coverage.csv',index=False)
    pd.DataFrame(result['cells']).to_csv(output/'training-cells.csv',index=False)
    shutil.copyfile(__file__,output/'executed_reference_cell_adequacy.py')
    (output/'input-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    report='Reference cell-size diagnostic\n\nFixed target: 5000 original2021Q1 loans, June2022-Sep2025 adjacent riskset. Training: eligible2018Q1 and2021Q1 samples, Jan2018-Dec2021 only. Six-month age/FICO/LTV/state cells, with global training age-range check.\n\n'
    for r in result['coverage']:
        report+=f"Band ±{r['half_width_pp']}pp, {r['screen']}: {r['supported_rows']}/{r['evaluation_rows']} target loan-months; {r['supported_exposure_fraction']:.8%} of opening-UPB exposure; {r['cells_passing']}/{r['training_cells']} training cells pass.\n"
    report+='\nThresholds are diagnostic sensitivity choices, not justified estimation or confidence criteria. Training event-count screens are outcome-dependent descriptions. No evaluation payoff outcome enters these calculations. No causal p0, sensitive share, gamma or portfolio dollar result is estimated. Unsupported exposure remains in the denominator.\n'
    (output/'REPORT.md').write_text(report)
    seal={p.name:sha(p) for p in output.iterdir() if p.is_file()}
    (output/'output-sha256.json').write_text(json.dumps(seal,indent=2)+'\n')
    for n,h in seal.items():
        if sha(output/n)!=h:raise ValueError('Final output mismatch')
    print(report,flush=True);print('COMPLETE: all adequacy output hashes verified: '+str(output),flush=True)
    return output
