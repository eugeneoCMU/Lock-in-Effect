"""Calendar concentration and absolute-rate overlap diagnostics, not reference identification."""
import json
from pathlib import Path
import hashlib
import datetime
import shutil
import pandas as pd
import numpy as np

SCREENS=[('presence',1,1,0),('10loans_3months_1event',10,3,1),('30loans_6months_5events',30,6,5)]
KEYS=['age_bin_6m','fico_bucket','ltv_bucket','property_state']


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def audit_time_environment(panel):
    cols=['loan_id','reporting_period','at_risk_adjacent','current_note_gap_pp','lag_loan_age',
          'fico_bucket','ltv_bucket','property_state','adjacent_opening_upb','benchmark_rate']
    d=panel[cols].copy()
    if d.duplicated(['loan_id','reporting_period']).any():raise ValueError('Duplicate loan-month')
    if not np.isfinite(d.adjacent_opening_upb).all() or (d.adjacent_opening_upb<0).any():raise ValueError('Invalid exposure')
    d=d[d.at_risk_adjacent & (d.adjacent_opening_upb>0)].copy()
    age=pd.to_numeric(d.lag_loan_age,errors='coerce')
    d['age_bin_6m']=np.floor(age/6).where(np.isfinite(age)&(age>=0))
    d['year']=d.reporting_period.str[:4]
    d['quarter']=d.year+'Q'+(((d.reporting_period.str[4:6].astype(int)-1)//3)+1).astype(str)
    target=d[d.reporting_period.between('202206','202509')]
    target_keys=list(target[KEYS].itertuples(index=False,name=None))
    complete=target[KEYS].notna().all(axis=1)
    total=float(target.adjacent_opening_upb.sum());cells=[];coverage=[];periods=[];global_rates=[]
    for width in [.25,.5]:
        train=d[d.reporting_period.between('201801','202112') & (d.current_note_gap_pp.abs()<=width)].copy()
        events=panel.loc[train.index,'recorded_payoff_event']
        if not events.isin([0,1]).all():raise ValueError('Nonbinary training event')
        train['payoff']=events.astype(int)
        lo=float(train.lag_loan_age.min()) if len(train) else None
        hi=float(train.lag_loan_age.max()) if len(train) else None
        age_ok=target.lag_loan_age.between(lo,hi) if lo is not None else pd.Series(False,index=target.index)
        mapped={}
        for key,g in train.dropna(subset=KEYS).groupby(KEYS,sort=True):
            quarter=g.groupby('quarter').adjacent_opening_upb.sum();year=g.groupby('year').adjacent_opening_upb.sum()
            w=float(g.adjacent_opening_upb.sum());rates=g.loc[np.isfinite(g.benchmark_rate),'benchmark_rate']*100
            cell=dict(half_width_pp=width,age_bin_6m=int(key[0]),fico_bucket=key[1],ltv_bucket=key[2],property_state=key[3],
                training_loans=int(g.loan_id.nunique()),training_calendar_months=int(g.reporting_period.nunique()),
                training_payoff_events=int(g.payoff.sum()),training_years=int(g.year.nunique()),training_quarters=int(g.quarter.nunique()),
                largest_quarter_exposure_fraction=float(quarter.max()/w),largest_year_exposure_fraction=float(year.max()/w),
                benchmark_min_pct=float(rates.min()) if len(rates) else None,benchmark_max_pct=float(rates.max()) if len(rates) else None)
            cells.append(cell);mapped[key]=cell
        for name,l,m,e in SCREENS:
            eligible={k:v for k,v in mapped.items() if v['training_loans']>=l and v['training_calendar_months']>=m and v['training_payoff_events']>=e}
            base=complete & age_ok & pd.Series([k in eligible for k in target_keys],index=target.index)
            two=base & pd.Series([eligible.get(k,{}).get('training_years',0)>=2 for k in target_keys],index=target.index)
            quarter_ok=base & pd.Series([eligible.get(k,{}).get('largest_quarter_exposure_fraction',1.)<=.5 for k in target_keys],index=target.index)
            low=pd.Series([eligible.get(k,{}).get('benchmark_min_pct') for k in target_keys],index=target.index,dtype=float)
            high=pd.Series([eligible.get(k,{}).get('benchmark_max_pct') for k in target_keys],index=target.index,dtype=float)
            rate_ok=base & (target.benchmark_rate*100).between(low,high)
            masks={'base_supported':base,'two_training_years':two,'quarter_concentration_le_half':quarter_ok,
                   'rate_range_supported':rate_ok,'all_three_additional':two&quarter_ok&rate_ok}
            row=dict(half_width_pp=width,screen=name,evaluation_rows=len(target),evaluation_opening_upb=total)
            for label,mask in masks.items():
                exposure=float(target.loc[mask,'adjacent_opening_upb'].sum())
                row[label+'_rows']=int(mask.sum());row[label+'_opening_upb']=exposure
                row[label+'_exposure_fraction']=exposure/total if total else None
            coverage.append(row)
        for year,g in train.groupby('year'):
            periods.append(dict(half_width_pp=width,year=year,rows=len(g),loans=int(g.loan_id.nunique()),
                calendar_months=int(g.reporting_period.nunique()),opening_upb=float(g.adjacent_opening_upb.sum()),payoff_events=int(g.payoff.sum())))
        for label,frame in [('training',train),('evaluation',target)]:
            rates=frame.loc[np.isfinite(frame.benchmark_rate),'benchmark_rate']*100
            global_rates.append(dict(half_width_pp=width,view=label,benchmark_min_pct=float(rates.min()) if len(rates) else None,
                benchmark_max_pct=float(rates.max()) if len(rates) else None))
    return dict(coverage=coverage,cells=cells,training_years=periods,benchmark_ranges=global_rates,causal_reference_estimated=False,
        design=dict(training=['201801','202112'],evaluation=['202206','202509'],development_excluded=['202201','202205'],
            fixed_bands_pp=[.25,.5],screens=SCREENS,controls=KEYS,benchmark='Prior-month national mortgage benchmark, decimal input; percent output',
            additional_checks=['At least two distinct training calendar years','No one training quarter exceeds half of training cell opening-UPB exposure','Target absolute benchmark lies within observed training-cell benchmark min/max'],
            qualification='Separate retrospective diagnostics, not causal acceptance rules. Absolute-rate range ignores within-range density and other omitted market conditions. Zero overlap is not proof that every parametric extrapolation is invalid.',
            denominator='Opening principal summed across adjacent target loan-months; unsupported observations stay in denominator'))


def run(drive_root):
    root=Path(drive_root)/'Lock-in-Effect cloud results'
    paths=[(root/'origination-reference-20261016T151834Z','private-origination-borrower-panel.parquet'),
           (root/'older-2018Q1-n20000-20261016T154805Z','private-older-borrower-panel.parquet')]
    frames=[];receipts=[]
    for folder,name in paths:
        seal=json.loads((folder/'output-sha256.json').read_text())
        if name not in seal:raise ValueError('Required panel absent from seal')
        for n,h in seal.items():
            if Path(n).name!=n or sha(folder/n)!=h:raise ValueError('Prior seal mismatch')
        frame=pd.read_parquet(folder/name)
        if name.startswith('private-older'):frame=frame[frame.reporting_period<='202112']
        frames.append(frame);receipts.append(dict(folder=str(folder),panel_sha256=sha(folder/name),seal_sha256=sha(folder/'output-sha256.json')))
    result=audit_time_environment(pd.concat(frames,ignore_index=True))
    if any(r['evaluation_rows']!=172640 for r in result['coverage']):raise ValueError('Target riskset changed')
    prior=root/'nested-20000-cell-adequacy-v2-20261016T155316Z'
    seal=json.loads((prior/'output-sha256.json').read_text())
    if sha(prior/'adequacy.json')!=seal['adequacy.json']:raise ValueError('Prior adequacy mismatch')
    baseline=json.loads((prior/'adequacy.json').read_text())['coverage']
    for r in result['coverage']:
        old=next(x for x in baseline if x['half_width_pp']==r['half_width_pp'] and x['screen']==r['screen'])
        if old['supported_rows']!=r['base_supported_rows'] or not np.isclose(old['supported_opening_upb'],r['base_supported_opening_upb'],rtol=1e-13,atol=.01):
            raise ValueError('Fixed baseline coverage changed')
    output=root/('reference-time-environment-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(exist_ok=False);output.chmod(0o700)
    (output/'time-environment.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(result['coverage']).to_csv(output/'coverage.csv',index=False)
    pd.DataFrame(result['cells']).to_csv(output/'training-cells.csv',index=False)
    pd.DataFrame(result['training_years']).to_csv(output/'training-year-exposure.csv',index=False)
    (output/'input-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    shutil.copyfile(__file__,output/'executed_reference_time_environment.py')
    report='Calendar and absolute-rate environment diagnostic\n\nFixed2021Q1target riskset172640months. Training2018-2021 from saved2018Q1n20000 and2021Q1n5000 panels. Baseline cell screens verified unchanged.\n\n'
    for r in result['coverage']:
        report+=f"±{r['half_width_pp']}pp, {r['screen']}: base {r['base_supported_exposure_fraction']:.8%}; two training years {r['two_training_years_exposure_fraction']:.8%}; largest quarter ≤50% {r['quarter_concentration_le_half_exposure_fraction']:.8%}; absolute-rate range {r['rate_range_supported_exposure_fraction']:.8%}; all three {r['all_three_additional_exposure_fraction']:.8%}.\n"
    report+='\nAdditional percentages retain the full target opening-UPB denominator and apply each condition on top of its baseline screen. Calendar and absolute-rate checks are descriptive, not sufficient causal identification. No p0/share/gamma fit or portfolio effect.\n'
    (output/'REPORT.md').write_text(report)
    final={p.name:sha(p) for p in output.iterdir() if p.is_file()}
    (output/'output-sha256.json').write_text(json.dumps(final,indent=2)+'\n')
    assert all(sha(output/n)==h for n,h in final.items())
    print(report);print(json.dumps(result['benchmark_ranges']));print('COMPLETE: all time/environment output hashes verified:',output)
    return output
