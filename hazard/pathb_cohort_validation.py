"""Frozen retrospective, conditional cohort-principal predictions (not a holdout)."""
from __future__ import annotations
import json
import numpy as np
import pandas as pd
from hazard.stock_flow_accounting_comparison import ROOT,CHECKS,sha,lh
from hazard.cohort_history import prediction_initial_state
KEYS=['vintage','coupon','fico_bucket','ltv_bucket']
START=pd.Timestamp('2024-01-01');END=pd.Timestamp('2025-09-01')

def prepare_exposures(panel):
    d=panel.sort_values(['cell','period']).copy();g=d.groupby('cell')
    d['opening_exposure']=g.exposure_upb.shift(1)
    last=g.period.shift(1);contiguous=(d.period.dt.to_period('M').astype('int64')-last.dt.to_period('M').astype('int64'))==1
    missing=d.opening_exposure.isna()|~contiguous
    zero=~missing&(d.opening_exposure<=0)
    bad=~missing&~zero&((d.prepaid_upb<0)|(d.prepaid_upb>d.opening_exposure)|~np.isfinite(d.prepaid_upb))
    counts = {'missing_or_noncontiguous':int(missing.sum()),'zero_exposure':int(zero.sum()),'invalid_numerator':int(bad.sum())}
    window=(d.period>=START)&(d.period<=END)
    counts['evaluation']={'input_rows':int(window.sum()),'missing_or_noncontiguous':int((missing&window).sum()),'zero_exposure':int((zero&window).sum()),'invalid_numerator':int((bad&window).sum())}
    return d[~missing&~zero&~bad].copy(),counts

def fit_baseline(d):
    train=d[(d.period>=pd.Timestamp('2023-01-01'))&(d.period<START)]
    g=train.groupby('cell')[['prepaid_upb','opening_exposure']].sum()
    return (g.prepaid_upb/g.opening_exposure).to_dict()

def score(exposure,events,hazard):
    exposure=np.asarray(exposure,float);events=np.asarray(events,float);hazard=np.asarray(hazard,float)
    if len(exposure)==0 or np.any(exposure<=0):raise ValueError('Positive nonempty exposure required')
    pred=exposure*hazard;error=hazard-events/exposure
    return dict(n=int(len(exposure)),exposure_b_months=float(exposure.sum()/1e9),observed_b=float(events.sum()/1e9),predicted_b=float(pred.sum()/1e9),ratio=float(pred.sum()/events.sum()) if events.sum()>0 else None,weighted_rmse_monthly_pp=float(np.sqrt(np.average(error**2,weights=exposure))*100),weighted_mae_monthly_pp=float(np.average(abs(error),weights=exposure)*100))

def main():
    pp=ROOT/'hazard/data/cohort_month_panel.parquet';sp=ROOT/'hazard/data/loan_sample.parquet'
    panel=pd.read_parquet(pp);panel['cell']=panel[KEYS].astype(str).agg('|'.join,axis=1)
    d,exclusions=prepare_exposures(panel);base=fit_baseline(d)
    loans=pd.read_parquet(sp);loans['coupon']=np.round(np.round(loans.coupon/.005)*.005,4)
    for col,orig in [('fico_z','fico'),('ltv_z','orig_ltv')]:loans[col]=(loans[orig]-loans[orig].mean())/max(loans[orig].std(ddof=0),1.)
    loans['cell']=loans[KEYS].astype(str).agg('|'.join,axis=1)
    cov=loans.groupby('cell')[['fico_z','ltv_z']].mean()
    pre=panel[panel.period==pd.Timestamp('2023-12-01')].set_index('cell')
    eligible=set(base)&set(cov.index)&set(pre.index)
    raw=d[(d.period>=START)&(d.period<=END)].copy();exclusions['no_training_or_covariate_or_december_support']=int((~raw.cell.isin(eligible)).sum())
    ev=raw[raw.cell.isin(eligible)].copy()
    exclusions['evaluation']['no_training_or_covariate_or_december_support']=exclusions['no_training_or_covariate_or_december_support']
    coverage={'denominator':'Usable evaluation rows after lag/exposure/numerator exclusions, before support restrictions','usable_rows':int(len(raw)),'retained_rows':int(len(ev)),'usable_exposure_b_months':float(raw.opening_exposure.sum()/1e9),'retained_exposure_b_months':float(ev.opening_exposure.sum()/1e9),'usable_observed_b':float(raw.prepaid_upb.sum()/1e9),'retained_observed_b':float(ev.prepaid_upb.sum()/1e9),'exposure_retained_fraction':float(ev.opening_exposure.sum()/raw.opening_exposure.sum()),'observed_principal_retained_fraction':float(ev.prepaid_upb.sum()/raw.prepaid_upb.sum())}
    # Hold all state/covariate initialization to pre-evaluation rows.
    ev['base']=ev.cell.map(base)
    ev['fz']=ev.cell.map(cov.fico_z);ev['lz']=ev.cell.map(cov.ltv_z)
    age0=pre.mean_loan_age.to_dict()
    # This frozen replay retains the recorded legacy convention; corrected
    # prediction entry points require audited fixed-cohort history instead.
    burn0,balance0,orig0=prediction_initial_state(pre,allow_legacy=True)
    macro=pd.read_parquet(CHECKS/'macro_frozen.parquet');rate=macro.MORTGAGE30US.groupby(macro.index.to_period('M')).last()/100
    ev['rate']=ev.period.dt.to_period('M').map(rate)
    if ev.rate.isna().any():raise ValueError('Missing conditioning mortgage rates')
    ev['age']=ev.cell.map(age0)+(ev.period.dt.year-2023)*12+ev.period.dt.month-12
    old=lh.INVOLUNTARY_CPR_ANNUAL;lh.INVOLUNTARY_CPR_ANNUAL=.04991
    try:
        for name,beta in [('off',0.),('on',lh.rothstein_beta1(.065))]:
            burn=dict(burn0);balance=dict(balance0)
            for dt,sub in ev.groupby('period',sort=True):
                b=np.array([burn[c] for c in sub.cell]);h=lh.prepay_hazard(sub.age.to_numpy(),(sub.coupon-sub.rate).to_numpy(),b,sub.fz.to_numpy(),sub.lz.to_numpy(),beta1=beta)
                default=lh.default_hazard(np.maximum(sub.rate-sub.coupon,0).to_numpy(),sub.fz.to_numpy(),sub.lz.to_numpy())
                h,_=lh.normalize_competing_hazards(h,default);ev.loc[sub.index,name]=h
                for cell,hz in zip(sub.cell,h):
                    amount=balance[cell]*hz;balance[cell]-=amount
                    burn[cell]=min(1.,burn[cell]+amount/max(orig0[cell],1.))
    finally:lh.INVOLUNTARY_CPR_ANNUAL=old
    ev['coupon_vintage']=ev[['vintage','coupon']].astype(str).agg('|'.join,axis=1)
    ev['halfyear']=ev.period.dt.year.astype(str)+'H'+np.where(ev.period.dt.month<=6,'1','2')
    def metrics(group):return {n:score(group.opening_exposure,group.prepaid_upb,group[n]) for n in ['base','off','on']}
    result={'design':'frozen retrospective conditional cohort check','spec':'specs/SPEC_2026-10-07_pathb_validation.md','evaluation_start':str(START.date()),'evaluation_end':str(END.date()),'training_end':'2023-12-31','n_cells':int(ev.cell.nunique()),'months':int(ev.period.nunique()),'exclusions':exclusions,'evaluation_coverage':coverage,'aggregate':metrics(ev),'coupon_vintage':{str(k):metrics(g) for k,g in ev.groupby('coupon_vintage')},'subperiods':{str(k):metrics(g) for k,g in ev.groupby('halfyear')},'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [pp,sp,CHECKS/'macro_frozen.parquet']},'limitations':['Previously examined outcomes, no untouched holdout','Cohort-level aggregation and frozen covariate proxies','Conditional on realized opening exposure and rates, not a forward full-book forecast','No realized separate scheduled/default/curtailment fields or loan-ID histories','No claim to validate imported elasticity or causal marginal']}
    for name in ['base','off','on']:
        assert np.isclose(sum(v[name]['predicted_b'] for v in result['coupon_vintage'].values()),result['aggregate'][name]['predicted_b'])
    (ROOT/'hazard/data/pathb_validation_2026-10-07_results.json').write_text(json.dumps(result,indent=2)+'\n')
    ev.to_csv(CHECKS/'validation_cell_month_scores.csv',index=False)
    print(json.dumps({k:v for k,v in result.items() if k not in ['coupon_vintage','input_sha256']},indent=2))
if __name__=='__main__':main()
