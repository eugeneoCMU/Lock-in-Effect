"""Separate retrospective predictive selection on corrected fixed-history cells.

No causal coefficient or termination cause is estimated. Selection consumes only
training outcomes. Full latent calendars remain independent of scoring omissions.
"""
from dataclasses import dataclass,asdict
from pathlib import Path
import sys,os,json
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'hazard'):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
os.environ.setdefault('FRED_API_KEY','offline-corrected-calibration')
import numpy as np
import pandas as pd
from hazard.pathb_prediction_diagnostics import strict_score,diagnose_groups,predict_path,RESPONSE_BETA
from hazard.pathb_cohort_validation import prepare_exposures,KEYS
from hazard.cohort_history import prediction_initial_state
from hazard.mixture_hazard import mixture_probability,reference_probability
from hazard import simulate_freddie_rebuild as pair
from hazard.run_freddie_rebuild import digest,write_json

LEGACY_GAMMA=-float(RESPONSE_BETA)

@dataclass(frozen=True)
class Candidate:
    id:str
    family:str
    psa:float=100.
    annual_floor:float=.04991
    share:float=1.
    gamma:float=LEGACY_GAMMA
    reference:str='inherited_psa'
    def __post_init__(self):
        v=np.array([self.psa,self.annual_floor,self.share,self.gamma])
        if (not self.id or self.family not in ('max','additive','mixture') or not np.isfinite(v).all()
                or self.psa<=0 or not 0<=self.annual_floor<1 or not 0<=self.share<=1 or self.gamma<0
                or self.reference not in ('inherited_psa','matched_max_off')):
            raise ValueError('Invalid explicit predictive candidate')
    @property
    def group(self):return self.family+(':'+self.reference if self.family=='mixture' else '')

def candidate_grid():
    out=[]
    for family in ('max','additive'):
        for floor in (0.,.02,.035,.04991):
            for psa in (25.,50.,75.,100.):out.append(Candidate(f'{family}:floor={floor}:psa={psa}',family,psa,floor))
    for reference in ('inherited_psa','matched_max_off'):
        for conversion,gamma in [('illustrative',-np.log(.935)),('legacy',LEGACY_GAMMA)]:
            for share in (0.,.25,.5,.75,1.):
                for psa in (25.,50.,75.,100.):
                    out.append(Candidate(f'mixture:{reference}:{conversion}:share={share}:psa={psa}','mixture',psa,.04991,share,float(gamma),reference))
    return out

def dates(start,end):
    start,end=pd.Timestamp(start),pd.Timestamp(end)
    if start>end or not start.is_month_start or not end.is_month_start:raise ValueError('Ordered month-start windows required')
    return start,end

def calendar(state,start,end):
    start,end=dates(start,end)
    if not state.index.is_unique:raise ValueError('Duplicate historical cell state')
    if state.empty:raise ValueError('No supported historical state')
    d=pd.MultiIndex.from_product([sorted(state.index),pd.date_range(start,end,freq='MS')],names=['cell','period']).to_frame(index=False)
    d['coupon']=d.cell.map(state.coupon)
    return d

def forecast(rows,state,cov,rates,candidate):
    # Only date, identity and coupon enter this predictor, even if callers carry outcomes.
    d=rows[['cell','period','coupon']].copy()
    origin=pd.to_datetime(state.period.unique())
    if len(origin)!=1 or not origin[0].is_month_start or d.empty or not d.period.dt.is_month_start.all():raise ValueError('Historical month-start initialization and calendar required')
    if d.period.min()!=origin[0]+pd.offsets.MonthBegin(1):raise ValueError('Calendar must start one month after initialization')
    if d.duplicated(['cell','period']).any():raise ValueError('Duplicate prediction calendar')
    cells=sorted(d.cell.unique())
    expected=pd.MultiIndex.from_product([cells,pd.date_range(d.period.min(),d.period.max(),freq='MS')],names=['cell','period'])
    if set(map(tuple,d[['cell','period']].to_numpy()))!=set(expected):raise ValueError('Complete monthly prediction calendar required')
    if not set(cells).issubset(set(state.index)&set(cov.index)):raise ValueError('Missing covariate/state support')
    r=d.period.dt.to_period('M').map(rates)
    if not np.isfinite(r).all() or (r<=0).any():raise ValueError('Missing or nonpositive conditioning rate')
    if candidate.family!='mixture':return predict_path(d,state,cov,rates,candidate.annual_floor,candidate.psa,-candidate.gamma,floor_form=candidate.family)
    d['age']=d.cell.map(state.mean_loan_age)+(d.period.dt.year-origin[0].year)*12+d.period.dt.month-origin[0].month
    d['rate']=r;d['fz']=d.cell.map(cov.fico_z);d['lz']=d.cell.map(cov.ltv_z)
    if not np.isfinite(d[['age','fz','lz']]).all().all():raise ValueError('Nonfinite conditioning covariates')
    burn,balance,original=prediction_initial_state(state)
    for _,sub in d.groupby('period',sort=True):
        b=np.array([burn[c] for c in sub.cell])
        p0=reference_probability(sub.age.to_numpy(),b,sub.fz.to_numpy(),sub.lz.to_numpy(),psa=candidate.psa,reference_mode=candidate.reference,annual_floor=candidate.annual_floor)
        vol=mixture_probability(p0,(sub.coupon-sub.rate).to_numpy(),candidate.share,candidate.gamma,gap_mode='positive_only')
        default=pair.lh.default_hazard(np.maximum(sub.rate-sub.coupon,0).to_numpy(),sub.fz.to_numpy(),sub.lz.to_numpy())
        h,_=pair.lh.normalize_competing_hazards(vol,default)
        d.loc[sub.index,'hazard']=h;d.loc[sub.index,'predicted_burnout']=b;d.loc[sub.index,'latent_balance']=[balance[c] for c in sub.cell]
        for cell,hz in zip(sub.cell,h):
            amount=balance[cell]*hz;balance[cell]-=amount;burn[cell]=min(1.,burn[cell]+amount/original[cell])
    return d.drop(columns=['cell','period','coupon'])

def _supported(panel,cov,start,end,*,baseline_cells=None):
    start,end=dates(start,end);pre=start-pd.offsets.MonthBegin(1)
    p=panel[panel.period.between(pre,end)].copy()
    if p.duplicated(['cell','period']).any():raise ValueError('Duplicate observed cohort month')
    usable,exclusions=prepare_exposures(p)
    # The legacy helper's counters pin a historical window. Recompute the
    # same exclusion rules on this experiment's requested dates.
    audit=p.sort_values(['cell','period']).copy();g=audit.groupby('cell')
    opening=g.exposure_upb.shift(1);last=g.period.shift(1)
    adjacent=(audit.period.dt.to_period('M').astype('int64')-last.dt.to_period('M').astype('int64'))==1
    missing=opening.isna()|~adjacent;zero=~missing&(opening<=0)
    bad=~missing&~zero&((audit.prepaid_upb<0)|(audit.prepaid_upb>opening)|~np.isfinite(audit.prepaid_upb))
    def counts(mask):return dict(input_rows=int(mask.sum()),missing_or_noncontiguous=int((mask&missing).sum()),zero_exposure=int((mask&zero).sum()),invalid_numerator=int((mask&bad).sum()))
    exclusions['evaluation']=counts(audit.period.between(start,end))
    exclusions['initialization']=counts(audit.period==pre)
    exclusions['window']=[str(start.date()),str(end.date())]
    raw=usable[usable.period.between(start,end)].copy()
    state=p[p.period==pre].set_index('cell')
    eligible=set(state.index)&set(cov.index)&set(raw.cell)
    if baseline_cells is not None:eligible &= set(baseline_cells)
    scored=raw[raw.cell.isin(eligible)].copy().sort_values(['cell','period']).reset_index(drop=True)
    if scored.empty:raise ValueError('No common positive-exposure scoring support')
    state=state.loc[sorted(eligible)].copy();prediction_initial_state(state)
    support=dict(usable_rows=len(raw),retained_rows=len(scored),retained_cells=len(eligible),retained_months=int(scored.period.nunique()),
        excluded_support_rows=len(raw)-len(scored),retained_exposure_b_months=float(scored.opening_exposure.sum()/1e9),
        usable_exposure_b_months=float(raw.opening_exposure.sum()/1e9),retained_observed_b=float(scored.prepaid_upb.sum()/1e9),
        usable_observed_b=float(raw.prepaid_upb.sum()/1e9),exposure_retained_fraction=float(scored.opening_exposure.sum()/raw.opening_exposure.sum()),
        exclusions=exclusions,initialization=pre.strftime('%Y-%m-%d'))
    return scored,state,support

def _aligned_prediction(scored,cal,pred):
    return scored[['cell','period']].merge(cal[['cell','period']].assign(hazard=pred.hazard.to_numpy()),on=['cell','period'],how='left',validate='one_to_one').hazard.to_numpy()

def calibrate(panel,cov,rates,start,end,candidates):
    start,end=dates(start,end)
    # Trim before any outcome processing. Even invalid future outcomes are invisible.
    training=panel[panel.period<=end].copy()
    scored,state,support=_supported(training,cov,start,end);cal=calendar(state,start,end)
    if len({c.id for c in candidates})!=len(candidates) or not candidates:raise ValueError('Nonempty unique candidate IDs required')
    totals=scored.groupby('cell')[['prepaid_upb','opening_exposure']].sum();baseline=(totals.prepaid_upb/totals.opening_exposure).to_dict()
    grid=[]
    for c in candidates:
        pred=forecast(cal,state,cov,rates,c);metrics=strict_score(scored.opening_exposure,scored.prepaid_upb,_aligned_prediction(scored,cal,pred))
        grid.append(dict(candidate=asdict(c),group=c.group,**metrics))
    groups=sorted({c.group for c in candidates});selected={}
    for group in groups+['overall']:
        eligible=[x for x in grid if group=='overall' or x['group']==group]
        best=min(eligible,key=lambda x:(x['weighted_rmse_monthly_pp'],x['candidate']['id']))
        selected[group]=best['candidate']
    return dict(training=[str(start.date()),str(end.date())],selected=selected,grid=grid,baseline=baseline,support=support,
        selection_metric='Training exposure-weighted monthly-rate RMSE; candidate-ID tie break',interpretation='Predictive calibration only; not identified cause share or causal response')

def evaluate_selected(panel,cov,rates,trained,start,end):
    start,end=dates(start,end)
    if start<=pd.Timestamp(trained['training'][1]):raise ValueError('Evaluation must follow training')
    scored,state,support=_supported(panel,cov,start,end,baseline_cells=trained['baseline'])
    cal=calendar(state,start,end);predictions=cal.copy();scored['baseline']=scored.cell.map(trained['baseline'])
    candidates={name:Candidate(**d) for name,d in trained['selected'].items()};candidates['inherited_benchmark']=Candidate('inherited_benchmark','max')
    for name,c in candidates.items():
        pred=forecast(cal,state,cov,rates,c);predictions[name]=pred.hazard.to_numpy();scored[name]=_aligned_prediction(scored,cal,pred)
    support['calendar_rows']=len(cal)
    names=['baseline']+list(candidates)
    agg={n:strict_score(scored.opening_exposure,scored.prepaid_upb,scored[n]) for n in names}
    scored['coupon_vintage']=scored[['vintage','coupon']].astype(str).agg('|'.join,axis=1)
    scored['halfyear']=scored.period.dt.year.astype(str)+'H'+np.where(scored.period.dt.month<=6,'1','2')
    groups={g:{n:diagnose_groups(scored,g,n) for n in names} for g in ('coupon_vintage','halfyear')}
    result=dict(evaluation=[str(start.date()),str(end.date())],aggregate=agg,groups=groups,support=support,
        parameters={n:asdict(c) for n,c in candidates.items()},previously_examined_outcomes=True,
        limitations=['Conditional on realized opening exposure/rates, not a forward balance forecast','Fixed May2022 sample covariates and advancing cohort mean age','No cause identification, causal coefficient, fitted dollar effect or full-SOMA validation'])
    return scored,predictions,result

def run(root,macro,output,*,combined):
    root,macro,output=Path(root),Path(macro),Path(output)
    if output.exists():raise FileExistsError('Preserve prior experiment')
    output.mkdir()
    panelpath=root/'combined/cohort_month_panel.parquet';samplepath=root/'combined/loan_sample.parquet'
    paths=[panelpath,samplepath,macro,ROOT/'docs/superpowers/specs/2026-10-14-research-next-design.md',Path(__file__),ROOT/'hazard/pathb_prediction_diagnostics.py',ROOT/'hazard/cohort_history.py',ROOT/'hazard/mixture_hazard.py']
    hashes={str(p):digest(p) for p in paths}
    grid=candidate_grid();windows=[('primary','2023-01-01','2023-12-01','2024-01-01','2025-09-01'),('expanding','2023-01-01','2024-12-01','2025-01-01','2025-09-01')]
    write_json(output/'input_manifest.json',dict(input_sha256=hashes,candidates=[asdict(c) for c in grid],windows=windows,population=combined['population'],source_semantics=combined['source_semantics_version'],retrospective=True))
    try:
        from hazard.score_freddie_rebuild import SAMPLE_COLUMNS,sample_covariates
        cov=sample_covariates(samplepath,combined)
        rateframe=pd.read_parquet(macro,columns=['MORTGAGE30US']);rates=rateframe.MORTGAGE30US.groupby(rateframe.index.to_period('M')).last()/100.
        results={}
        for name,ts,te,es,ee in windows:
            print('Chronological training:',name,flush=True)
            # Load only training outcome dates. Full file hash binds source without inspecting future payoff values.
            train=pd.read_parquet(panelpath,filters=[('period','>=',pd.Timestamp(ts)-pd.offsets.MonthBegin(1)),('period','<=',pd.Timestamp(te))])
            train['period']=pd.to_datetime(train.period);train['cell']=train[KEYS].astype(str).agg('|'.join,axis=1)
            learned=calibrate(train,cov,rates,ts,te,grid)
            freeze=output/(name+'-parameter-freeze.json');write_json(freeze,learned)
            # The selection receipt is sealed before evaluation outcome read.
            selection_digest=digest(freeze)
            ev=pd.read_parquet(panelpath,filters=[('period','>=',pd.Timestamp(es)-pd.offsets.MonthBegin(1)),('period','<=',pd.Timestamp(ee))])
            ev['period']=pd.to_datetime(ev.period);ev['cell']=ev[KEYS].astype(str).agg('|'.join,axis=1)
            scored,pred,metrics=evaluate_selected(ev,cov,rates,learned,es,ee)
            if digest(freeze)!=selection_digest:raise ValueError('Training selection changed during evaluation')
            metrics['parameter_freeze_sha256']=selection_digest;write_json(output/(name+'-results.json'),metrics)
            scored.to_parquet(output/(name+'-scores.parquet'),index=False);pred.to_parquet(output/(name+'-predictions.parquet'),index=False)
            results[name]=metrics
        for p,h in hashes.items():
            if digest(Path(p))!=h:raise ValueError('Frozen experiment input changed: '+p)
        write_json(output/'completed.json',dict(status='complete',selection_before_evaluation_read=True,source_inputs_unchanged=True,output_sha256={p.name:digest(p) for p in output.iterdir() if p.is_file()}))
        return results
    except BaseException as exc:
        write_json(output/'failed.json',dict(error=repr(exc)));raise
