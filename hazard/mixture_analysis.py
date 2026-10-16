"""Run old-model benchmarks and the complete prespecified mixture matrix offline."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parent.parent
for path in (ROOT,ROOT/'hazard'):
    if str(path) not in sys.path: sys.path.insert(0,str(path))
from hazard import simulate_freddie_rebuild as pair, score_freddie_rebuild as scoring
from hazard.benchmark_forms import run_additive_pair, score_additive
from hazard.comparison_acceptance import validate_analysis
from hazard.run_mixture_rebuild import run_pair
from hazard.score_mixture_rebuild import run as score_mixture

SHARES=(0.,.25,.5,.75,1.)
CALIBRATIONS=('legacy_conversion','illustrative')
GAP_MODES=('positive_only','preserve_refinancing')
REFERENCE_MODES=('inherited_psa','matched_max_off')


def planned_inputs(pipeline):
    stages=json.loads(Path(pipeline).read_text())['stages']
    result={}
    for stage in stages:
        name=stage['name']
        if name not in ('paired-simulation','scoring'): continue
        c=stage['command']
        flags=c[3:]
        if len(flags)%2 or any(not x.startswith('--') for x in flags[::2]):
            raise ValueError('Expected explicit option/value pipeline arguments')
        result[name]={flags[i][2:].replace('-','_'):Path(flags[i+1]) for i in range(0,len(flags),2)
                      if flags[i]!='--output'}
    if set(result)!= {'paired-simulation','scoring'}:
        raise ValueError('Pipeline must supply both benchmark stages')
    return result


def run(*,pipeline,output):
    from source_rebuild_receipts import receipt_validation_session
    with receipt_validation_session() as source_session:
        return _run(pipeline=pipeline,output=output,source_session=source_session)


def _run(*,pipeline,output,source_session):
    pipeline,output=Path(pipeline).resolve(),Path(output).resolve()
    inputs=planned_inputs(pipeline)
    roots={x['root'].resolve() for x in inputs.values()}
    if len(roots)!=1: raise ValueError('Both stages must use the same corrected root')
    root=roots.pop()
    for protected in (ROOT/'hazard/data',root/'quarters',root/'combined'):
        if output==protected or protected in output.parents:
            raise ValueError('Analysis output overlaps protected inputs')
    if output.exists(): raise FileExistsError('Preserve prior analysis; choose a new output')
    frozen=json.loads(pipeline.read_text())['frozen_sha256']
    pair.verify_hashes(frozen)
    pair.validated_combined(root)
    output.mkdir(parents=True,exist_ok=False)
    files=[Path(__file__),ROOT/'hazard/mixture_hazard.py',ROOT/'hazard/run_mixture_rebuild.py',ROOT/'hazard/score_mixture_rebuild.py',ROOT/'specs/SPEC_2026-10-13_mixture_alternative.md',
        ROOT/'hazard/benchmark_forms.py',ROOT/'hazard/comparison_acceptance.py',
        ROOT/'hazard/source_rebuild_receipts.py',
        ROOT/'hazard/simulate_freddie_rebuild.py',ROOT/'hazard/pathb_prediction_diagnostics.py',
        ROOT/'specs/SPEC_2026-10-13_comparison_matrix_v2.md']
    code_hashes={str(p):pair.digest(p) for p in files}
    pair.write_json(output/'analysis_manifest.json',dict(pipeline=str(pipeline),pipeline_sha256=pair.digest(pipeline),
        code_sha256=code_hashes,shares=SHARES,
        calibrations=CALIBRATIONS,gap_modes=GAP_MODES,reference_modes=REFERENCE_MODES,
        benchmarks=('max','additive'),parameter_selection_performed=False))
    done=[]
    try:
        print('Running existing-model benchmarks',flush=True)
        old_pair=pair.run(**inputs['paired-simulation'],output=output/'benchmark-pair')
        old_scores=scoring.run(**inputs['scoring'],output=output/'benchmark-scoring')
        additive_pair=run_additive_pair(**inputs['paired-simulation'],output=output/'additive-benchmark-pair')
        additive_scores=score_additive(**inputs['scoring'],output=output/'additive-benchmark-scoring')
        for reference_mode in REFERENCE_MODES:
            for calibration in CALIBRATIONS:
                for gap_mode in GAP_MODES:
                    for share in SHARES:
                        label=f'{reference_mode}-{calibration}-{gap_mode}-share-{share}'
                        print('Running',label,flush=True)
                        candidate=run_pair(**inputs['paired-simulation'],output=output/(label+'-pair'),
                            sensitive_share=share,calibration=calibration,gap_mode=gap_mode,reference_mode=reference_mode)
                        score=score_mixture(**inputs['scoring'],output=output/(label+'-scoring'),
                            sensitive_share=share,calibration=calibration,gap_mode=gap_mode,reference_mode=reference_mode)
                        done.append(dict(scenario=label,sensitive_share=share,calibration=calibration,gap_mode=gap_mode,
                            reference_mode=reference_mode,
                            reported_marginal_b=candidate['reported_marginal_b'],
                            closed_pool_cash_marginal_b=candidate['closed_pool_cash_marginal_b'],
                            retrospective_scores=score['aggregate'],support=score['support']))
                        pair.write_json(output/'progress.json',dict(completed=done,status='running'))
        pair.verify_hashes(frozen)
        pair.verify_hashes(code_hashes)
        # Fresh compact validation plus distinct retained-source SHA checks
        # precede acceptance; provisional scenario outputs cannot bypass them.
        pair.validated_combined(root)
        source_session.verify_unchanged()
        acceptance=validate_analysis(output,done)
        pair.write_json(output/'acceptance.json',acceptance)
        result=dict(status='complete',acceptance=acceptance,benchmark_pair=old_pair,benchmark_scores=old_scores['aggregate'],
            additive_benchmark_pair=additive_pair,additive_benchmark_scores=additive_scores['aggregate'],
            scenarios=done,reference_newly_calibrated=False,sensitive_share_estimated=False,
            interpretation='Prespecified structural sensitivities; previously examined retrospective period')
        pair.write_json(output/'results.json',result)
        pair.write_json(output/'progress.json',dict(completed=done,status='complete'))
        return result
    except BaseException as exc:
        pair.write_json(output/'failed.json',dict(error=repr(exc),completed=done))
        pair.write_json(output/'progress.json',dict(completed=done,status='failed'))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pipeline',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path)
    run(**vars(p.parse_args()))
