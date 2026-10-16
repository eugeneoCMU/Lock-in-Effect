"""Historical cell means carried forward only as an explicit rate/calendar-invariance scenario."""
import json
from pathlib import Path
import hashlib
import datetime
import shutil
import pandas as pd
import numpy as np

KEYS=['age_bin_6m','fico_bucket','ltv_bucket','property_state']
SCREENS=[('10loans_3months',10,3),('30loans_6months',30,6)]


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def historical_reference_scenario(panel):
    x=panel[['loan_id','reporting_period','at_risk_adjacent','current_note_gap_pp','lag_loan_age','fico_bucket','ltv_bucket','property_state','adjacent_opening_upb','benchmark_rate']].copy()
    if x.duplicated(['loan_id','reporting_period']).any():raise ValueError('Duplicate loan-month')
    if not np.isfinite(x.adjacent_opening_upb).all() or (x.adjacent_opening_upb<0).any():raise ValueError('Invalid exposure')
    x=x[x.at_risk_adjacent & (x.adjacent_opening_upb>0)].copy()
    age=pd.to_numeric(x.lag_loan_age,errors='coerce')
    x['age_bin_6m']=np.floor(age/6).where(np.isfinite(age)&(age>=0))
    cells=[];predictions=[];evaluation=[]
    for width in [.25,.5]:
        train=x[x.reporting_period.between('201801','202112') & (x.current_note_gap_pp.abs()<=width)].copy()
        y=panel.loc[train.index,'adjacent_payoff_upb']
        if not np.isfinite(y).all() or ((y<0)|(y>train.adjacent_opening_upb)).any():raise ValueError('Invalid training payoff')
        train['payoff']=y
        mapped={}
        for key,g in train.dropna(subset=KEYS).groupby(KEYS,sort=True):
            exposure=float(g.adjacent_opening_upb.sum());paid=float(g.payoff.sum())
            rates=g.loc[np.isfinite(g.benchmark_rate),'benchmark_rate']
            cell=dict(half_width_pp=width,age_bin_6m=int(key[0]),fico_bucket=key[1],ltv_bucket=key[2],property_state=key[3],
                training_loans=int(g.loan_id.nunique()),training_months=int(g.reporting_period.nunique()),
                training_opening_upb=exposure,training_payoff_upb=paid,historical_fraction=paid/exposure,
                age_min=float(g.lag_loan_age.min()),age_max=float(g.lag_loan_age.max()),
                rate_min=float(rates.min()) if len(rates) else None,rate_max=float(rates.max()) if len(rates) else None)
            cells.append(cell);mapped[key]=cell
        for name,minimum_loans,minimum_months in SCREENS:
            eligible={k:c for k,c in mapped.items() if c['training_loans']>=minimum_loans and c['training_months']>=minimum_months}
            for view,start,end in [('development','202201','202205'),('evaluation','202206','202509')]:
                t=x[x.reporting_period.between(start,end)].copy();keys=list(t[KEYS].itertuples(index=False,name=None))
                valid=t[KEYS].notna().all(axis=1)
                low=pd.Series([eligible.get(k,{}).get('age_min') for k in keys],index=t.index,dtype=float)
                high=pd.Series([eligible.get(k,{}).get('age_max') for k in keys],index=t.index,dtype=float)
                match=valid & t.lag_loan_age.between(low,high)
                p=pd.Series([eligible.get(k,{}).get('historical_fraction') for k in keys],index=t.index,dtype=float).where(match)
                ratelow=pd.Series([eligible.get(k,{}).get('rate_min') for k in keys],index=t.index,dtype=float)
                ratehigh=pd.Series([eligible.get(k,{}).get('rate_max') for k in keys],index=t.index,dtype=float)
                extrap=match & ~t.benchmark_rate.between(ratelow,ratehigh)
                total=float(t.adjacent_opening_upb.sum());matched=float(t.loc[match,'adjacent_opening_upb'].sum())
                predicted=float((p[match]*t.loc[match,'adjacent_opening_upb']).sum())
                month_errors=[];month_weights=[]
                # Outcomes are read only here, after cell means and matching are fixed.
                ty=panel.loc[t.index,'adjacent_payoff_upb']
                if not np.isfinite(ty).all() or ((ty<0)|(ty>t.adjacent_opening_upb)).any():raise ValueError('Invalid validation payoff')
                observed=float(ty[match].sum())
                for month,g in t.groupby('reporting_period'):
                    idx=g.index;mi=idx[match.loc[idx]];mw=float(t.loc[mi,'adjacent_opening_upb'].sum());mt=float(g.adjacent_opening_upb.sum())
                    mp=float((p.loc[mi]*t.loc[mi,'adjacent_opening_upb']).sum())
                    predictions.append(dict(half_width_pp=width,screen=name,view=view,reporting_period=str(month),
                        total_opening_upb=mt,matched_opening_upb=mw,scenario_predicted_payoff_amount=mp,
                        matched_scenario_fraction=mp/mw if mw else None))
                    if mw:
                        month_errors.append(abs(mp/mw-float(ty.loc[mi].sum())/mw));month_weights.append(mw)
                evaluation.append(dict(half_width_pp=width,screen=name,view=view,risk_rows=len(t),matched_rows=int(match.sum()),
                    total_opening_upb=total,matched_opening_upb=matched,unmatched_opening_upb=total-matched,
                    matched_exposure_fraction=matched/total if total else None,
                    matched_scenario_fraction=predicted/matched if matched else None,
                    matched_observed_fraction=observed/matched if matched else None,
                    matched_monthly_fraction_weighted_mae=float(np.average(month_errors,weights=month_weights)) if month_weights else None,
                    matched_rate_environment_extrapolation_exposure_fraction=float(t.loc[extrap,'adjacent_opening_upb'].sum())/matched if matched else None,
                    conditional_full_fraction_lower=predicted/total if total else None,
                    conditional_full_fraction_upper=(predicted+total-matched)/total if total else None))
    return dict(cells=cells,predictions=predictions,evaluation=evaluation,causal_reference_estimated=False,
        designated_reference_status='reference_not_estimated',scenario_status='conditional_historical_cell_mean_only',
        assumptions=dict(training=['201801','202112'],development=['202201','202205'],evaluation=['202206','202509'],
            bands_pp=[.25,.5],controls=KEYS,screens=SCREENS,
            matching='Complete covariates plus exact target age inside each eligible cell observed training min/max; no age extrapolation',
            new_screen_rule='Distinct loan/month screens only; no payoff-event minimum, because outcome-selected training groups would distort a historical-rate scenario',
            transport='Imposed calendar and absolute-rate invariance within matched cells, despite observed rate support failure',
            estimator='Opening-principal-weighted training recorded payoff fraction; no binomial trial-count inference',
            full_target_envelope='Matched historical fractions treated as fixed scenario values; unmatched fractions allowed[0,1]. Conditional envelope excludes sampling and model error; not a causal or confidence interval',
            riskset='Observed monthly risksets held fixed; no dynamic portfolio projection, no cause-specific labels',
            evaluation_use='Development/evaluation payoff outcomes enter validation scores only; no fitting, tuning, flooring or monotonicity enforcement'))


def run(drive_root):
    root=Path(drive_root)/'Lock-in-Effect cloud results';frames=[];receipts=[]
    for folder,name in [(root/'origination-reference-20261016T151834Z','private-origination-borrower-panel.parquet'),(root/'older-2018Q1-n20000-20261016T154805Z','private-older-borrower-panel.parquet')]:
        seal=json.loads((folder/'output-sha256.json').read_text())
        if name not in seal:raise ValueError('Panel absent from seal')
        for n,h in seal.items():
            if Path(n).name!=n or sha(folder/n)!=h:raise ValueError('Source output mismatch')
        frame=pd.read_parquet(folder/name)
        if name.startswith('private-older'):frame=frame[frame.reporting_period<='202112']
        frames.append(frame);receipts.append(dict(folder=str(folder),panel_sha256=sha(folder/name),seal_sha256=sha(folder/'output-sha256.json')))
    result=historical_reference_scenario(pd.concat(frames,ignore_index=True))
    if any(x['risk_rows']!=172640 for x in result['evaluation'] if x['view']=='evaluation'):raise ValueError('Target riskset changed')
    output=root/('historical-reference-scenario-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(exist_ok=False);output.chmod(0o700)
    for key in ['cells','predictions','evaluation']:pd.DataFrame(result[key]).to_csv(output/(key+'.csv'),index=False)
    (output/'scenario.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    (output/'input-receipts.json').write_text(json.dumps(receipts,indent=2)+'\n')
    shutil.copyfile(__file__,output/'executed_historical_reference_scenario.py')
    report='Historical-reference scenario validation\n\nMeasured pre-QT cell fractions carried forward under an imposed rate/calendar invariance assumption. No structural no-lockin reference is estimated. Each matched target age must lie inside its own trainingcell observed range. No event-count screening or hidden floor.\n\n'
    for x in result['evaluation']:
        if x['view']!='evaluation':continue
        def pct(v):return 'unavailable' if v is None else f'{v:.8%}'
        report+=f"±{x['half_width_pp']}pp, {x['screen']}: matched exposure {pct(x['matched_exposure_fraction'])}; matched historical scenario {pct(x['matched_scenario_fraction'])}; matched observed {pct(x['matched_observed_fraction'])}; matched monthly fraction MAE {pct(x['matched_monthly_fraction_weighted_mae'])}; rate-extrapolated matched exposure {pct(x['matched_rate_environment_extrapolation_exposure_fraction'])}; full-target conditional envelope [{pct(x['conditional_full_fraction_lower'])},{pct(x['conditional_full_fraction_upper'])}].\n"
    report+='\nFractions use opening principal summed across observed loan-months. Historical point fractions are fixed assumptions when forwarded; the full-target envelope permits unknown[0,1] fractions for unmatched exposure, ignores sampling/model error, and is not a causal/confidence interval. Development/evaluation outcomes are used only for scoring, never adjustment. No share/gamma calibration or population dollar projection.\n'
    (output/'REPORT.md').write_text(report)
    final={p.name:sha(p) for p in output.iterdir() if p.is_file()};(output/'output-sha256.json').write_text(json.dumps(final,indent=2)+'\n')
    assert all(sha(output/n)==h for n,h in final.items())
    print(report);print('COMPLETE: historical scenario output hashes verified:',output)
    return output
