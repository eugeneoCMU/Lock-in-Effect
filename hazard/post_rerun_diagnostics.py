"""Offline post-rerun bridge, common-support fit review and floor measurement inference."""
from pathlib import Path
import os,sys,json,argparse,shutil
from contextlib import contextmanager
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'hazard'):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
os.environ.setdefault('FRED_API_KEY','offline-rerun')
import numpy as np
import pandas as pd
import polars as pl
from scipy.interpolate import PchipInterpolator
from hazard import simulate_freddie_rebuild as pair
from run_freddie_rebuild import digest,write_json
from source_rebuild_receipts import receipt_validation_session
from hazard import floor_inference_correction_v2 as inference
from hazard.calibrate_freddie_rebuild import frozen_rates
from stratum import build_stratum_id


def bridge_samples(old,new):
    return [old.clone(),new.drop([c for c in ('initial_burnout','burnout_denominator_multiplier') if c in new.columns]),new.clone(),new.clone()]


def check_common_groups(groups):
    if not groups:return
    base=groups[0]
    for candidate in groups[1:]:
        if set(candidate)!=set(base):raise ValueError('Group support keys differ')
        for key in base:
            for field in ('n','observed_b','exposure_b_months'):
                if not np.isclose(candidate[key][field],base[key][field],rtol=1e-12,atol=1e-12):
                    raise ValueError('Group support or observed outcome differs')


def infer_floor(selected,*,draws=9999,n_grid=401,cluster='stratum'):
    groups=selected.groupby(cluster,sort=True)[['prepaid_upb','exposure_upb']].sum()
    A,W=groups.prepaid_upb.to_numpy(float),groups.exposure_upb.to_numpy(float)
    if len(A)<2 or not np.isfinite(A).all() or not np.isfinite(W).all() or (A<0).any() or (W<=0).any():
        raise ValueError('Finite nonnegative events and at least two positive exposure clusters required')
    c=inference.cr_ses(A,W);R=c['R_smm'];se=c['se_cr1'];h=c['_h']
    if not 0<=R<=1:raise ValueError('Selected exposure ratio lies outside monthly probability range')
    result=dict(point_smm=R,point_cpr_pct=inference.cpr_pct_of_smm(R),n_rows=len(selected),n_clusters=len(A),
        exposure_upb=float(W.sum()),prepaid_upb=float(A.sum()),cluster=cluster,max_leverage=float(h.max()),
        effective_clusters=float(1/(h*h).sum()),se_cr1_smm=se,draws=draws,seed=42,n_grid=n_grid,
        weights='Webb six-point',weights_reused_across_grid=True,
        studentizer='Unrestricted observed CR1 SE; restricted resample CR1 SE',
        denominator='End-of-month exposure; inherited floor measurement convention',
        interpretation='Measurement inference for selected payoff-speed ratio; not an identified involuntary floor or total uncertainty')
    if se<=np.finfo(float).eps:
        return dict(result,computable=False,reason='Degenerate observed variance; no fabricated interval')
    grid=np.linspace(R-5*se,R+5*se,n_grid)
    weights=inference.draw_weights(np.random.default_rng(42),'webb',len(A)) if draws==inference.B_WILD else np.random.default_rng(42).choice(inference.WEBB_POINTS,size=(draws,len(A)))
    kept=[];valid_counts=[];Wtot=W.sum();fac=len(A)/(len(A)-1)
    for i,R0 in enumerate(grid):
        if not 0<=R0<=1:continue
        Ast=R0*W[None,:]+weights*(A-R0*W)[None,:]
        Rst=Ast.sum(axis=1)/Wtot
        u=(Ast-Rst[:,None]*W[None,:])/Wtot
        sest=np.sqrt(fac*np.sum(u*u,axis=1))
        valid=np.isfinite(sest)&(sest>np.finfo(float).eps)
        valid_counts.append(int(valid.sum()))
        if valid.sum()<max(20,draws//2):raise ValueError('Insufficient finite null studentizers')
        tstar=(Rst[valid]-R0)/sest[valid];lo,hi=np.percentile(tstar,[2.5,97.5])
        if lo<=(R-R0)/se<=hi:kept.append(i)
    result.update(grid_smm=grid.tolist(),retained_indices=kept,minimum_valid_null_draws=min(valid_counts),
        excluded_nonphysical_candidates=int(np.sum((grid<0)|(grid>1))))
    if not kept:return dict(result,computable=False,reason='Empty retained candidate set')
    low,high=float(grid[kept[0]]),float(grid[kept[-1]])
    return dict(result,computable=True,retained_contiguous=kept[-1]-kept[0]+1==len(kept),
        open_at_grid_lo=kept[0]==0,open_at_grid_hi=kept[-1]==n_grid-1,
        smm_ci95=[low,high],floor_cpr_ci95_pct=[inference.cpr_pct_of_smm(low),inference.cpr_pct_of_smm(high)])


def select_floor(frame,rates):
    frame=frame.copy()
    frame['rp']=frame.reporting_period.astype(int)
    frame['gap']=frame.coupon-frame.reporting_period.astype(str).map(rates)
    frame['stratum']=[build_stratum_id(*row) for row in frame[['vintage','coupon','fico_bucket','ltv_bucket']].itertuples(index=False,name=None)]
    frame['month']=frame.reporting_period.astype(str)
    if frame.loc[frame.rp.between(201801,201812),'gap'].isna().any():raise ValueError('Missing primary floor rates')
    return frame[(frame.rp>=201801)&(frame.rp<=201812)&(frame.gap<=-.0025)&(frame.mean_loan_age>=12)&(frame.exposure_upb>0)]


def sample_summary(d):
    w=d['balance'].to_numpy().astype(float)*d['weight'].to_numpy().astype(float)
    return dict(rows=len(d),unique_ids=d['loan_id'].n_unique(),balance_weighted_coupon=float(np.average(d['coupon'],weights=w)),
        balance_weighted_age=float(np.average(d['loan_age'],weights=w)),balance_b=float(w.sum()/1e9),
        original_term_observed='original_loan_term' in d.columns,history_observed='initial_burnout' in d.columns)


def validate_bridge_matrix(m,*,legacy=False):
    values=m.to_numpy(float);totals=values.sum(axis=1)
    valid=np.isclose(totals,1) | (legacy & np.isclose(totals,0))
    if not np.isfinite(values).all() or (values<0).any() or not valid.all():raise ValueError('Invalid transition probabilities')


@contextmanager
def floor_recorded_leg(floor):
    previous_floor,previous_step=pair.lh.INVOLUNTARY_CPR_ANNUAL,pair.engine.monthly_step
    recorder=pair.AccountingRecorder(previous_step)
    pair.lh.INVOLUNTARY_CPR_ANNUAL=float(floor);pair.engine.monthly_step=recorder
    try:
        if pair.cr.prepay_hazard.__globals__['INVOLUNTARY_CPR_ANNUAL']!=float(floor):raise ValueError('Effective floor binding differs')
        yield recorder
    finally:
        pair.engine.monthly_step=previous_step;pair.lh.INVOLUNTARY_CPR_ANNUAL=previous_floor


def run_pair_data(loans,matrix,macro,output,*,floor=.04991,legacy=False):
    output.mkdir();prior=pair.lh.INVOLUNTARY_CPR_ANNUAL;pair.lh.INVOLUNTARY_CPR_ANNUAL=floor
    legs={}
    try:
        for leg,response in [('off',0.),('on',6.5)]:
            with floor_recorded_leg(floor) as recorder:
                pair.engine.run_qt_microsim(loan_sample=loans,macro=macro,transition_matrix=matrix,regimes=('US',),seed=42,
                    p_q_shock_pct=response,output=output/(leg+'.parquet'),allow_legacy_inputs=legacy)
            a=pd.DataFrame(recorder.rows,index=pair.QT_INDEX)
            if len(a)!=42:raise ValueError('Incomplete bridge accounting')
            scale=np.where(a.closing_active_b>0,macro.loc[pair.QT_INDEX].WSHOMCB.to_numpy()/1000/np.maximum(a.closing_active_b,1e-6),1.)
            a['reporting_scale']=scale;a.to_parquet(output/(leg+'-accounting.parquet'))
            if max(a.active_residual_b.abs().max(),a.total_residual_b.abs().max())>1e-8:raise ValueError('Bridge principal identity failed')
            legs[leg]=dict(reported_principal_b=float((a.cash_principal_b*scale).sum()),cash_principal_b=float(a.cash_principal_b.sum()))
        r=dict(floor_annual=floor,allow_legacy_inputs=legacy,legacy_initialization='initial_burnout' not in loans.columns,legs=legs,
            reported_marginal_b=legs['off']['reported_principal_b']-legs['on']['reported_principal_b'],
            cash_marginal_b=legs['off']['cash_principal_b']-legs['on']['cash_principal_b'])
        write_json(output/'results.json',r);return r
    finally:pair.lh.INVOLUNTARY_CPR_ANNUAL=prior


def run(*,accepted_root,legacy_root,output,reuse_analysis=None):
    accepted_root,legacy_root,output=[Path(p).resolve() for p in (accepted_root,legacy_root,output)]
    if output.exists():raise FileExistsError('Preserve existing analysis')
    pipeline=accepted_root/'pipeline-verified-session/pipeline.json'
    frozen=json.loads(pipeline.read_text())['frozen_sha256'];pair.verify_hashes(frozen)
    output.mkdir();inputs=dict(frozen)
    reuse_analysis=Path(reuse_analysis).resolve() if reuse_analysis else None
    if reuse_analysis:
        prior=json.loads((reuse_analysis/'completed.json').read_text())
        for name,h in prior['output_sha256'].items():
            if digest(reuse_analysis/name)!=h:raise ValueError('Reuse evidence changed')
        inputs[str(reuse_analysis/'completed.json')]=digest(reuse_analysis/'completed.json')
        for name in ('bridge.json','floor_inference.json'):
            inputs[str(reuse_analysis/name)]=digest(reuse_analysis/name)
        write_json(output/'reuse_record.json',dict(source=str(reuse_analysis),reused=['bridge stages','floor_inference.json'],rejected=['floor grid','floor mapping'],reason='Only recorded sensitivity floor was overridden; default-floor bridge and statistical inference unchanged'))
    for p in [legacy_root/'hazard/data/loan_sample.parquet',legacy_root/'hazard/data/markov_transition_matrix.parquet',
        legacy_root/'hazard/data/moving_share_bracket_offwindow_results.json',accepted_root/'paired-simulation/results.json',
        accepted_root/'floor-calibration/input_manifest.json',accepted_root/'mixture-comparison-verified-session/results.json']:
        inputs[str(p)]=digest(p)
    for p in (accepted_root/'mixture-comparison-verified-session').glob('*-scoring/results.json'):inputs[str(p)]=digest(p)
    code={str(p):digest(p) for p in [Path(__file__),ROOT/'hazard/floor_inference_correction_v2.py',ROOT/'hazard/stratum.py',ROOT/'specs/SPEC_2026-10-14_post_rerun.md']}
    write_json(output/'input_manifest.json',dict(created_utc=datetime.now(timezone.utc).isoformat(),input_sha256=inputs,code_sha256=code,parameter_selection_performed=False))
    try:
        with receipt_validation_session() as source_session:
            combined,_=pair.validated_combined(accepted_root)
            old=pl.read_parquet(legacy_root/'hazard/data/loan_sample.parquet');new=pl.read_parquet(accepted_root/'combined/loan_sample.parquet')
            oldmatrix=pd.read_parquet(legacy_root/'hazard/data/markov_transition_matrix.parquet');newmatrix=pd.read_parquet(accepted_root/'combined/markov_transition_matrix.parquet')
            validate_bridge_matrix(oldmatrix,legacy=True);validate_bridge_matrix(newmatrix)
            write_json(output/'sample_audit.json',dict(archived=sample_summary(old),corrected=sample_summary(new),common_loan_ids=old.select('loan_id').unique().join(new.select('loan_id').unique(),on='loan_id',how='inner').height,
                boundary='Archived terms/history absent; sample step jointly changes population, draw, covariates and observed balances'))
            matrix=accepted_root/'mixture-comparison-verified-session';models=[]
            for label,file,key in [('max',matrix/'benchmark-scoring/results.json','original_on'),('additive',matrix/'additive-benchmark-scoring/results.json','additive_on'),
                ('mixture-inherited-75',matrix/'inherited_psa-illustrative-positive_only-share-0.75-scoring/results.json','mixture_on'),
                ('mixture-matched-75',matrix/'matched_max_off-illustrative-positive_only-share-0.75-scoring/results.json','mixture_on')]:
                d=json.loads(file.read_text());inputs[str(file)]=digest(file);models.append((label,d,key))
            rows=[]
            for group in ('coupon_vintage','halfyear'):
                check_common_groups([d['groups'][group][key] for _,d,key in models])
                for label,d,key in models:
                    for cell,metrics in d['groups'][group][key].items():
                        base=d['groups'][group]['base'][cell]
                        rows.append(dict(model=label,group=group,cell=cell,**metrics,baseline_rmse=base['weighted_rmse_monthly_pp'],
                            rmse_change_from_baseline=metrics['weighted_rmse_monthly_pp']-base['weighted_rmse_monthly_pp']))
            write_json(output/'fit_review.json',dict(rows=rows,common_support_verified=True,selection_performed=False,scope='Previously examined conditional payoff outcomes; realized exposure and rates'))
            macro_path=Path(next(p for p in inputs if p.endswith('/output/review-revision/2026-10-07-checks/macro_frozen.parquet')))
            macro,_=pair.load_macro(macro_path);pair.validate_conventions()
            labels=['archived-current-engine','corrected-sample-legacy-history','corrected-history-archived-transitions','corrected-complete']
            results=[]
            for i,(label,loans) in enumerate(zip(labels,bridge_samples(old,new))):
                print('Bridge:',label,flush=True)
                if reuse_analysis:
                    shutil.copytree(reuse_analysis/label,output/label)
                    r=json.loads((output/label/'results.json').read_text())
                    if r['floor_annual']!=.04991:raise ValueError('Reuse bridge floor differs')
                else:r=run_pair_data(loans,newmatrix if i==3 else oldmatrix,macro,output/label,legacy=i<3)
                results.append(dict(stage=label,**r))
            accepted=json.loads((accepted_root/'paired-simulation/results.json').read_text())
            if not np.isclose(results[-1]['reported_marginal_b'],accepted['reported_marginal_b'],rtol=0,atol=1e-8):raise ValueError('Final bridge stage does not reproduce accepted benchmark')
            historical=42.60839388108866
            write_json(output/'bridge.json',dict(stages=results,historical_anchor_b=historical,current_engine_archived_residual_b=results[0]['reported_marginal_b']-historical,
                sequential_changes_b=[results[i]['reported_marginal_b']-results[i-1]['reported_marginal_b'] for i in range(1,4)],final_parity=True,
                interpretation='Order-dependent controlled input substitutions; sample/population/covariates jointly change. No causal or isolated parsing-effect attribution.'))
            cal=json.loads((accepted_root/'floor-calibration/input_manifest.json').read_text())
            paths=cal['input_sha256'];rate_csv=Path(next(p for p in paths if p.endswith('/MORTGAGE30US_201612_202510.csv')));rate_meta=Path(next(p for p in paths if p.endswith('/rate_source.json')))
            rates,_=frozen_rates(rate_csv,rate_meta)
            frame=pl.read_parquet(accepted_root/'combined/cohort_month_panel.parquet').to_pandas()
            selected=select_floor(frame,rates)
            infer=json.loads((reuse_analysis/'floor_inference.json').read_text()) if reuse_analysis else {c:infer_floor(selected,cluster=c) for c in ('stratum','month')}
            if infer['stratum']['n_rows']!=len(selected) or infer['stratum']['n_clusters']!=selected.stratum.nunique():raise ValueError('Reused floor support differs')
            write_json(output/'floor_inference.json',infer)
            primary=infer['stratum'];mapped={}
            if primary['computable'] and primary['retained_contiguous'] and not primary['open_at_grid_lo'] and not primary['open_at_grid_hi']:
                lo,hi=np.array(primary['floor_cpr_ci95_pct'])/100;grid=np.linspace(lo,hi,9);values=[]
                for i,floor in enumerate(grid):
                    print('Floor mapping grid:',i+1,'/9',floor,flush=True)
                    r=run_pair_data(new,newmatrix,macro,output/f'floor-grid-{i}',floor=float(floor));values.append(r)
                if np.ptp([r['legs']['off']['reported_principal_b'] for r in values])<1e-8:raise ValueError('Sensitivity floors did not change OFF principal; reject unexercised mapping')
                y=np.array([x['reported_marginal_b'] for x in values]);curve=PchipInterpolator(grid,y,extrapolate=False)
                checks=[]
                for i in (0,2,4,6):
                    f=float((grid[i]+grid[i+1])/2);r=run_pair_data(new,newmatrix,macro,output/f'floor-check-{i}',floor=f)
                    checks.append(dict(floor=f,exact=r['reported_marginal_b'],interpolated=float(curve(f)),error_b=abs(r['reported_marginal_b']-float(curve(f)))))
                monotone=bool((np.diff(y)<=1e-8).all() or (np.diff(y)>=-1e-8).all());err=max(c['error_b'] for c in checks)
                mapped=dict(grid=values,holdout_checks=checks,grid_monotone=monotone,max_holdout_error_b=err,
                    accepted_approximation=monotone and err<=.05,approximation_tolerance_b=.05,
                    point_floor=float(primary['point_cpr_pct']/100),point_mapped_marginal_b=float(curve(primary['point_cpr_pct']/100)),
                    endpoint_marginals_b=[float(y[0]),float(y[-1])],mapped_measurement_band_b=[float(y.min()),float(y.max())],
                    qualification='Conditional approximate image of stratum-cluster floor confidence set; measured-speed floor interpretation, imported response, sampling/initialization/transport and mixture shares held fixed. Numerical monotonicity/interpolation checks do not prove global exact coverage.')
                if not mapped['accepted_approximation']:mapped['mapped_measurement_band_b']=None
            else:mapped=dict(accepted_approximation=False,reason='Primary floor inversion is open, disconnected or noncomputable; no bounded mapped interval')
            write_json(output/'floor_mapping.json',mapped)
            source_session.verify_unchanged();pair.verify_hashes(dict(inputs,**code))
            write_json(output/'completed.json',dict(status='complete',source_inputs_unchanged=True,final_bridge_parity=True,common_fit_support=True,
                floor_mapping_accepted=mapped['accepted_approximation'],output_sha256={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()}))
    except BaseException as exc:
        write_json(output/'failed.json',dict(error=repr(exc)));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--accepted-root',required=True);p.add_argument('--legacy-root',required=True);p.add_argument('--output',required=True);p.add_argument('--reuse-analysis');run(**vars(p.parse_args()))
