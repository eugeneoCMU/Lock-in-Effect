"""Fixed-ID note-to-pass-through bridge experiment, with explicit support failures."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
import polars as pl
from hazard.stock_flow_accounting_comparison import ROOT,CHECKS,sha,simulate_accounting,summarize_pair,lh
from hazard.joint_soma_pair import targets

def bridge_buckets(coupon,bridge_bp):return np.round(np.round((np.asarray(coupon)-bridge_bp/10000)/.005)*.005,4)

def target_weights(balance,buckets,vintages,target):
    total=float(balance.sum());masks={k:np.isclose(buckets,k[0])&(vintages==k[1]) for k in target}
    missing=[k for k,m in masks.items() if balance[m].sum()<=0]
    report={'status':'unsupported' if missing else 'supported','missing_cells':[f'{k[0]:.4f}|{k[1]}' for k in missing],'missing_target_share':sum(target[k] for k in missing),'cell_counts':{f'{k[0]:.4f}|{k[1]}':int(m.sum()) for k,m in masks.items()}}
    if missing:return report
    weights=np.zeros(len(balance))
    for k,m in masks.items():weights[m]=total*target[k]/balance[m].sum()
    weighted=balance*weights
    report.update(weights=weights,candidate_loans=int(len(balance)),positive_weight_loans=int(np.count_nonzero(weights)),max_share_error=float(max(abs(weighted[m].sum()/weighted.sum()-target[k]) for k,m in masks.items())))
    return report

def main():
    sample=ROOT/'hazard/data/soma_fresh_umbs30_sample.parquet';loans=pl.read_parquet(sample);d=loans.to_pandas()
    target,mass=targets(json.loads((ROOT/'hazard/data/composition_shift_results.json').read_text()))
    vint=np.where(d.vintage<=2019,'2017-19',d.vintage.astype(str))
    macro=pd.read_parquet(CHECKS/'macro_frozen.parquet')
    out={'spec':'specs/SPEC_2026-10-07_coupon_bridge.md','fixed_sample_sha256':sha(sample),'unique_ids':int(d.loan_id.nunique()),'target_total_soma_face_share':mass,'bridges':{}}
    for bridge in [60,80,100]:
        report=target_weights(d.balance.to_numpy(),bridge_buckets(d.coupon.to_numpy(),bridge),vint,target)
        report['missing_total_soma_face_share']=report['missing_target_share']*mass
        if report['status']=='supported':
            weights=report.pop('weights');report['weights_sha256']=__import__('hashlib').sha256(weights.tobytes()).hexdigest()
            def rw(pool):
                pool.balance*=weights;pool.orig_upb*=weights
                pool.stratum_orig_upb=np.bincount(pool.stratum_id_code,weights=pool.orig_upb,minlength=pool.n_strata)
                pool._update_active_mask()
            off=simulate_accounting(loans,macro,0.,rw);on=simulate_accounting(loans,macro,lh.rothstein_beta1(.065),rw)
            report['paired_results']=summarize_pair(off,on)
            off.to_csv(CHECKS/f'bridge_{bridge}_off.csv');on.to_csv(CHECKS/f'bridge_{bridge}_on.csv')
        out['bridges'][str(bridge)]=report
        print(bridge,report['status'],report.get('paired_results',{}).get('paths',{}),flush=True)
    # Read compact snapshots only if a fixed-ID support failure exists.
    if any(r['status']=='unsupported' for r in out['bridges'].values()):
        root=Path('/Users/eugene/.codex/worktrees/6930/Lock-in-Effect/hazard/data/soma_stream_quarters')
        counts={b:{k:0 for k in target} for b in [60,80,100]}
        for path in sorted(root.glob('*.parquet')):
            s=pl.read_parquet(path).to_pandas();v=np.where(s.vintage<=2019,'2017-19',s.vintage.astype(str))
            for b in counts:
                cb=bridge_buckets(s.coupon.to_numpy(),b)
                for k in target:counts[b][k]+=int((np.isclose(cb,k[0])&(v==k[1])&(s.balance.to_numpy()>0)).sum())
        out['snapshot_support']={str(b):{f'{k[0]:.4f}|{k[1]}':n for k,n in c.items()} for b,c in counts.items()}
    old=json.loads((ROOT/'hazard/data/soma_fresh_pair_results.json').read_text())['pair']['marginal_b']
    out['bridge80_parity_difference_b']=out['bridges']['80']['paired_results']['paths']['production']['marginal_b']-old
    (ROOT/'hazard/data/coupon_bridge_2026-10-07_results.json').write_text(json.dumps(out,indent=2)+'\n')
if __name__=='__main__':main()
