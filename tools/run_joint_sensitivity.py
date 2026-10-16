"""Exact floor/response factorial scenarios, never a total confidence interval."""
from pathlib import Path
import sys,os,json
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'hazard'):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
os.environ.setdefault('FRED_API_KEY','offline-joint-sensitivity')
import numpy as np
import pandas as pd
import polars as pl
from hazard.post_rerun_diagnostics import floor_recorded_leg
from hazard import simulate_freddie_rebuild as pair
from hazard.run_freddie_rebuild import digest,write_json
BASE_GAMMA=-float(pair.lh.rothstein_beta1(.065))

def response_percent(multiplier):
    if not np.isfinite(multiplier) or multiplier<0:raise ValueError('Finite nonnegative response multiplier required')
    hbase=pair.lh.quarterly_to_monthly_hazard(pair.lh.P_Q_BASELINE)
    hshock=hbase*np.exp(-BASE_GAMMA*multiplier)
    shocked=1-(1-hshock)**3
    return float(100*(1-shocked/pair.lh.P_Q_BASELINE))

def run_exact_pair(loans,matrix,macro,output,*,floor,response_multiplier):
    if not np.isfinite(floor) or not 0<=floor<1:raise ValueError('Valid annual floor required')
    pct=response_percent(response_multiplier);effective=-float(pair.lh.rothstein_beta1(pct/100))
    if not np.isclose(effective,BASE_GAMMA*response_multiplier,rtol=1e-11,atol=1e-13):raise ValueError('Effective response conversion differs')
    if pair.lh.FLOOR_MODE!='max' or pair.lh.PSA_SPEED!=100:raise ValueError('Joint sensitivity requires inherited max100PSA')
    output=Path(output);output.mkdir();legs={}
    for name,response in [('off',0.),('on',pct)]:
        with floor_recorded_leg(floor) as recorder:
            pair.engine.run_qt_microsim(loan_sample=loans,macro=macro,transition_matrix=matrix,regimes=('US',),seed=42,p_q_shock_pct=response,output=output/(name+'.parquet'),allow_legacy_inputs=False)
        a=pd.DataFrame(recorder.rows,index=pair.QT_INDEX)
        if len(a)!=42 or max(a.active_residual_b.abs().max(),a.total_residual_b.abs().max())>1e-8:raise ValueError('Monthly principal accounting failed')
        scale=np.where(a.closing_active_b>0,macro.loc[pair.QT_INDEX].WSHOMCB.to_numpy()/1000/np.maximum(a.closing_active_b,1e-6),1.)
        a['reporting_scale']=scale;a.to_parquet(output/(name+'-accounting.parquet'))
        legs[name]=dict(reported_principal_b=float((a.cash_principal_b*scale).sum()),cash_principal_b=float(a.cash_principal_b.sum()))
    result=dict(floor_annual=float(floor),response_multiplier=float(response_multiplier),engine_response_decline_percent=pct,effective_gamma_per_pp=effective,legs=legs,
        reported_marginal_b=legs['off']['reported_principal_b']-legs['on']['reported_principal_b'],cash_marginal_b=legs['off']['cash_principal_b']-legs['on']['cash_principal_b'],accounting_identity_tolerance_b=1e-8)
    write_json(output/'results.json',result);return result

def run(root,macro_path,floor_inference,output,*,combined):
    root,macro_path,floor_inference,output=map(Path,(root,macro_path,floor_inference,output))
    if output.exists():raise FileExistsError('Preserve existing attempt')
    inference=json.loads(floor_inference.read_text())['stratum'];floors=[inference['floor_cpr_ci95_pct'][0]/100,inference['point_cpr_pct']/100,inference['floor_cpr_ci95_pct'][1]/100]
    multipliers=[.5,1.,1.5];paths=[root/'combined/loan_sample.parquet',root/'combined/markov_transition_matrix.parquet',macro_path,floor_inference,Path(__file__),ROOT/'hazard/post_rerun_diagnostics.py',ROOT/'hazard/literature_hazard.py',ROOT/'hazard/config.py',ROOT/'docs/superpowers/specs/2026-10-14-research-next-design.md']
    hashes={str(p):digest(p) for p in paths};output.mkdir()
    write_json(output/'input_manifest.json',dict(input_sha256=hashes,floors=floors,response_multipliers=multipliers,base_gamma=BASE_GAMMA,scope='Nine exact structural scenarios conditional on all other inputs, not joint statistical uncertainty'))
    try:
        loans=pl.read_parquet(root/'combined/loan_sample.parquet');matrix=pd.read_parquet(root/'combined/markov_transition_matrix.parquet');macro,_=pair.load_macro(macro_path)
        pair.validate_conventions();pair.validate_model_inputs(loans,matrix,combined)
        rows=[]
        for i,f in enumerate(floors):
            for j,m in enumerate(multipliers):
                print('Exact floor/response scenario:',i+1,j+1,flush=True)
                rows.append(run_exact_pair(loans,matrix,macro,output/f'floor-{i}-response-{j}',floor=f,response_multiplier=m))
            off=[x['legs']['off'] for x in rows[-3:]]
            if off[0]!=off[1] or off[0]!=off[2]:raise ValueError('OFF path differs within floor')
        if np.ptp([x['legs']['off']['reported_principal_b'] for x in rows])<1e-8:raise ValueError('Floor change never exercised')
        for p,h in hashes.items():
            if digest(Path(p))!=h:raise ValueError('Frozen scenario inputs changed')
        report=dict(rows=rows,reported_envelope_b=[min(x['reported_marginal_b'] for x in rows),max(x['reported_marginal_b'] for x in rows)],cash_envelope_b=[min(x['cash_marginal_b'] for x in rows),max(x['cash_marginal_b'] for x in rows)],off_invariants_passed=True,
            interpretation='Finite assumption grid; no probability distribution for response or joint coverage, mixture/seasoning/transport uncertainty not exhausted')
        write_json(output/'results.json',report);write_json(output/'completed.json',dict(status='complete',output_sha256={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()}));return report
    except BaseException as exc:write_json(output/'failed.json',dict(error=repr(exc)));raise
