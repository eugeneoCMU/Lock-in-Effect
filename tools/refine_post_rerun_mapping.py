"""Refine only numerical interpolation; preserve prior evidence and fixed tolerance."""
from pathlib import Path
import sys,os,argparse,json,shutil
ROOT=Path(__file__).resolve().parents[1]
for p in (ROOT,ROOT/'hazard'):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
os.environ.setdefault('FRED_API_KEY','offline-rerun')
import numpy as np
import pandas as pd
import polars as pl
from scipy.interpolate import PchipInterpolator
from hazard.post_rerun_diagnostics import run_pair_data,pair
from source_rebuild_receipts import receipt_validation_session
from run_freddie_rebuild import digest,write_json

def refine(source,root,output):
    source,root,output=[Path(p).resolve() for p in (source,root,output)]
    if output.exists():raise FileExistsError('Prior attempts are preserved')
    receipt=json.loads((source/'completed.json').read_text())
    for name,h in receipt['output_sha256'].items():
        if digest(source/name)!=h:raise ValueError('Prior evidence changed')
    manifest=json.loads((source/'input_manifest.json').read_text());frozen=dict(manifest['input_sha256'],**manifest['code_sha256'])
    frozen[str(source/'completed.json')]=digest(source/'completed.json');frozen[str(Path(__file__))]=digest(Path(__file__))
    pair.verify_hashes(frozen);shutil.copytree(source,output)
    (output/'completed.json').unlink()
    write_json(output/'refinement_manifest.json',dict(input_sha256=frozen,source=str(source),tolerance_b=.05,max_rounds=5,scope='Numerical refinement only; no structural selection'))
    prior=json.loads((source/'floor_mapping.json').read_text());nodes={r['floor_annual']:r for r in prior['grid']}
    cache=dict(nodes)
    for d in source.glob('floor-check-*'):
        r=json.loads((d/'results.json').read_text());cache[r['floor_annual']]=r
    curve=PchipInterpolator(sorted(nodes),[nodes[x]['reported_marginal_b'] for x in sorted(nodes)])
    for x,r in list(cache.items()):
        if abs(r['reported_marginal_b']-float(curve(x)))>.05:nodes[x]=r
    try:
        with receipt_validation_session() as session:
            pair.validated_combined(root)
            loans=pl.read_parquet(root/'combined/loan_sample.parquet');matrix=pd.read_parquet(root/'combined/markov_transition_matrix.parquet')
            macro_path=Path(next(p for p in frozen if p.endswith('/output/review-revision/2026-10-07-checks/macro_frozen.parquet')));macro,_=pair.load_macro(macro_path)
            new_runs=0;checks=[]
            def exact(x):
                nonlocal new_runs
                for k,r in cache.items():
                    if abs(k-x)<1e-14:return r
                new_runs+=1;print('Refinement simulation',new_runs,'floor',x,flush=True)
                r=run_pair_data(loans,matrix,macro,output/f'refine-{new_runs}',floor=float(x));cache[float(x)]=r;return r
            for round_id in range(5):
                xs=sorted(nodes);ys=[nodes[x]['reported_marginal_b'] for x in xs];curve=PchipInterpolator(xs,ys,extrapolate=False);checks=[];failed=[]
                for lo,hi in zip(xs[:-1],xs[1:]):
                    x=(lo+hi)/2;r=exact(x);estimated=float(curve(x));err=abs(r['reported_marginal_b']-estimated)
                    checks.append(dict(floor=x,exact=r['reported_marginal_b'],interpolated=estimated,error_b=err))
                    if err>.05:failed.append((x,r))
                write_json(output/'refinement_progress.json',dict(round=round_id+1,nodes=len(nodes),new_runs=new_runs,max_error_b=max(x['error_b'] for x in checks)))
                if not failed:break
                for x,r in failed:nodes[x]=r
            if failed:raise ValueError('Numerical tolerance not reached within five rounds; no accepted mapped band')
            xs=sorted(nodes);ys=np.array([nodes[x]['reported_marginal_b'] for x in xs]);curve=PchipInterpolator(xs,ys,extrapolate=False)
            monotone=bool((np.diff(ys)<=1e-8).all() or (np.diff(ys)>=-1e-8).all())
            if not monotone:raise ValueError('Nonmonotone checked grid; do not label endpoint image a bounded interval')
            inference=json.loads((output/'floor_inference.json').read_text());point=inference['stratum']['point_cpr_pct']/100;point_result=exact(point)
            if abs(point_result['reported_marginal_b']-float(curve(point)))>.05:raise ValueError('Point-read mapping exceeds numerical tolerance')
            mapping=dict(prior,grid=[nodes[x] for x in xs],holdout_checks=checks,grid_monotone=True,max_holdout_error_b=max(x['error_b'] for x in checks),
                accepted_approximation=True,point_mapped_marginal_b=point_result['reported_marginal_b'],point_exact_marginal_b=point_result['reported_marginal_b'],
                point_interpolated_marginal_b=float(curve(point)),point_error_b=abs(point_result['reported_marginal_b']-float(curve(point))),
                endpoint_marginals_b=[float(ys[0]),float(ys[-1])],mapped_measurement_band_b=[float(ys.min()),float(ys.max())],refinement_rounds=round_id+1,new_exact_runs=new_runs)
            write_json(output/'floor_mapping.json',mapping);session.verify_unchanged();pair.verify_hashes(frozen)
            write_json(output/'completed.json',dict(status='complete',source_inputs_unchanged=True,final_bridge_parity=True,common_fit_support=True,floor_mapping_accepted=True,
                output_sha256={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()}))
    except BaseException as exc:write_json(output/'failed.json',dict(error=repr(exc)));raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--root',required=True);p.add_argument('--output',required=True);a=p.parse_args();refine(a.source,a.root,a.output)
