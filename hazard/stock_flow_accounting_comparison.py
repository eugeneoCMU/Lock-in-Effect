"""Auditable reporting-convention comparison; frozen production files are read only."""
from __future__ import annotations
import os,sys,json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'hazard'):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
# This driver is offline: config's key is never used for a network call.
os.environ.setdefault('FRED_API_KEY','offline-unused')
from agents import MicrosimPool, STATE_TO_CODE
from competing_risks import monthly_step
import literature_hazard as lh
from markov import load_transition_matrix
from config import QT_START,QT_END
from common.qt_window import compute_qt_target_series
CHECKS=ROOT/'output/review-revision/2026-10-07-checks'
BENCHMARK=764.7482532227002

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def reconcile_step(opening,closing,voluntary,scheduled,default_transfer,other_transfer):
    residual=opening-closing-voluntary-scheduled-default_transfer-other_transfer
    if abs(residual)>max(1e-5,abs(opening)*1e-12):raise ValueError(f'Balance reconciliation failed: {residual}')
    return dict(active_residual=float(residual),cash_principal=float(voluntary+scheduled),default_transfer=float(default_transfer),other_transfer=float(other_transfer))

def cap_cashflows(principal,caps):
    principal=np.asarray(principal);caps=np.asarray(caps)
    if np.any(principal<0) or np.any(caps<0):raise ValueError('Nonnegative principal/caps required')
    return np.minimum(principal,caps),np.maximum(principal-caps,0.)

def simulate_accounting(loans,macro,beta1,reweight=None):
    macro=macro.loc[(macro.index>=QT_START)&(macro.index<QT_END)].copy()
    pool=MicrosimPool(loans,rng=np.random.default_rng(42))
    if reweight is not None:reweight(pool)
    pool.scale_to_holdings(float(macro.iloc[0].WSHOMCB)/1000)
    initial_active=pool.total_exposure()/1e9
    initial_total=pool.balance.sum()/1e9
    trans=load_transition_matrix(); rows=[]
    prior_floor=lh.INVOLUNTARY_CPR_ANNUAL;lh.INVOLUNTARY_CPR_ANNUAL=.04991
    try:
        for ts,row in macro.iterrows():
            active=pool.active_mask.copy();opening=pool.total_exposure();total=pool.balance.sum()
            result=monthly_step(pool,float(row.MORTGAGE30US)/100,trans=trans,beta1=beta1)
            closing=pool.total_exposure();terminal=active & ~pool.active_mask
            default=terminal & np.isin(pool.state_code,[STATE_TO_CODE['Defaulted'],STATE_TO_CODE['Liquidated']])
            dt=float(pool.balance[default].sum());ot=float(pool.balance[terminal & ~default].sum())
            rec=reconcile_step(opening,closing,result['prepay_upb'],result['sched_amt'],dt,ot)
            scale=(float(row.WSHOMCB)/1000)/max(closing/1e9,1e-6) if closing>0 else 1.
            rows.append(dict(period=ts,opening_active_b=opening/1e9,closing_active_b=closing/1e9,opening_total_b=total/1e9,closing_total_b=pool.balance.sum()/1e9,voluntary_b=result['prepay_upb']/1e9,scheduled_b=result['sched_amt']/1e9,default_transfer_b=dt/1e9,other_terminal_transfer_b=ot/1e9,default_cash_b=0.,curtailment_b=0.,additions_b=0.,cash_principal_b=rec['cash_principal']/1e9,production_principal_b=rec['cash_principal']*scale/1e9,production_voluntary_b=result['prepay_upb']*scale/1e9,production_scheduled_b=result['sched_amt']*scale/1e9,reporting_scale=scale,active_residual_b=rec['active_residual']/1e9,initial_active_b=initial_active,initial_total_b=initial_total))
    finally:lh.INVOLUNTARY_CPR_ANNUAL=prior_floor
    out=pd.DataFrame(rows).set_index('period')
    caps=-compute_qt_target_series(out.index).to_numpy()
    for name,col in [('production','production_principal_b'),('closed','cash_principal_b')]:
        out[name+'_allowed_runoff_b'],out[name+'_reinvestment_b']=cap_cashflows(out[col],caps)
    out['cap_b']=caps
    if not np.allclose(out.opening_total_b-out.cash_principal_b,out.closing_total_b,rtol=1e-12,atol=1e-8):raise ValueError('Total claims do not reconcile')
    return out

def summarize_pair(off,on):
    result={'initial_active_b':float(off.initial_active_b.iloc[0]),'initial_total_b':float(off.initial_total_b.iloc[0]),'paths':{}}
    for name,col in [('production','production_principal_b'),('closed','cash_principal_b')]:
        d=float(off[col].sum()-on[col].sum())
        result['paths'][name]={'off_principal_b':float(off[col].sum()),'on_principal_b':float(on[col].sum()),'marginal_b':d,'marginal_pp':d/BENCHMARK*100,'marginal_pct_initial_active':d/result['initial_active_b']*100,'off_allowed_runoff_b':float(off[name+'_allowed_runoff_b'].sum()),'on_allowed_runoff_b':float(on[name+'_allowed_runoff_b'].sum()),'capped_marginal_b':float(off[name+'_allowed_runoff_b'].sum()-on[name+'_allowed_runoff_b'].sum()),'off_reinvestment_b':float(off[name+'_reinvestment_b'].sum()),'on_reinvestment_b':float(on[name+'_reinvestment_b'].sum()),'off_cap_binding_months':int((off[name+'_reinvestment_b']>0).sum()),'on_cap_binding_months':int((on[name+'_reinvestment_b']>0).sum())}
    for leg,data in [('off',off),('on',on)]:
        result[leg+'_components_b']={k:float(data[k].sum()) for k in ['voluntary_b','scheduled_b','default_transfer_b','other_terminal_transfer_b','default_cash_b','curtailment_b','additions_b']}
        result[leg+'_max_active_identity_error_b']=float(data.active_residual_b.abs().max())
    d=result['paths']['closed']['marginal_b']-result['paths']['production']['marginal_b']
    result.update(change_b=d,change_pp=d/BENCHMARK*100,change_percent_production=d/result['paths']['production']['marginal_b']*100)
    return result

def main():
    macro=pd.read_parquet(CHECKS/'macro_frozen.parquet');loans=pl.read_parquet(ROOT/'hazard/data/loan_sample.parquet')
    off=simulate_accounting(loans,macro,0.);on=simulate_accounting(loans,macro,lh.rothstein_beta1(.065))
    off.to_csv(CHECKS/'stock_flow_off.csv');on.to_csv(CHECKS/'stock_flow_on.csv')
    result=summarize_pair(off,on);err=result['paths']['production']['marginal_b']-42.60839388108866
    result.update(spec='specs/SPEC_2026-10-07_stock_flow_accounting.md',benchmark_b=BENCHMARK,scope='Closed opening book; inactive claims retained, no recovery cash/additions/reinvestment-pool simulation. Production is a reporting convention, not a self-financing full-SOMA book.',production_parity_difference_b=err,production_parity_pass=abs(err)<1e-6,input_sha256={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'hazard/data/loan_sample.parquet',CHECKS/'macro_frozen.parquet',ROOT/'hazard/data/markov_transition_matrix.parquet']})
    (ROOT/'hazard/data/stock_flow_accounting_2026-10-07_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
