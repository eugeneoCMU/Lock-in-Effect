"""Separate, offline mixture analysis using the corrected-pair input gates.

No frozen existing-model code or source receipt is modified. Each pair is an
explicit scenario, not parameter selection or an empirically identified split.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
for path in (ROOT, ROOT / 'hazard'):
    if str(path) not in sys.path: sys.path.insert(0, str(path))
from hazard import simulate_freddie_rebuild as pair
from hazard.mixture_hazard import mixture_context, response_gamma

SPEC = ROOT / 'specs/SPEC_2026-10-13_mixture_alternative.md'


@contextmanager
def pair_metadata(sensitive_share, calibration, gap_mode, reference_mode='inherited_psa'):
    old_params, old_spec, old_files = pair.PARAMETERS, pair.SPEC, pair.CODE_FILES
    pair.PARAMETERS = dict(old_params, annual_floor=None, floor_form='mixture',
        sensitive_share=sensitive_share, response_calibration=calibration, gap_mode=gap_mode,
        reference_mode=reference_mode, reference_annual_floor=.04991 if reference_mode=='matched_max_off' else None,
        gamma_per_pp={'off': 0., 'on': float(response_gamma(pair.lh.BETA1_PREPAY_MID, calibration))},
        response_percentage_interpretation='Legacy quarterly mobility input to adapter; gamma_per_pp is the applied intensity coefficient',
        reference=('Existing zero-gap PSA100/covariate schedule' if reference_mode=='inherited_psa'
                   else 'Hard-max response-OFF schedule at annual floor .04991; no post-response floor'),
        moving_share='not a borrower moving-share estimate')
    pair.SPEC = SPEC
    pair.CODE_FILES = old_files + [Path(__file__), ROOT / 'hazard/mixture_hazard.py']
    try:
        yield
    finally:
        pair.PARAMETERS, pair.SPEC, pair.CODE_FILES = old_params, old_spec, old_files


def run_pair(*, sensitive_share, calibration='legacy_conversion', gap_mode='positive_only',
             reference_mode='inherited_psa', **inputs):
    output = Path(inputs['output'])
    with mixture_context(sensitive_share, calibration, gap_mode, reference_mode), pair_metadata(sensitive_share, calibration, gap_mode, reference_mode):
        result = pair.run(**inputs)
    # Keep the original adapter receipt intact; the authoritative mixture
    # receipt identifies the changed model rather than inheriting its scope text.
    (output / 'results.json').rename(output / 'adapter_results.json')
    for name, leg in result['legs'].items():
        leg['legacy_adapter_response_input_pct'] = leg.pop('response_pct')
        leg['gamma_per_pp'] = result['parameters']['gamma_per_pp'][name]
    result['scope'] = 'Conditional mixture alternative on verified corrected Freddie inputs'
    result['limitations'] += [
        'Sensitive share is assumed, not an identified move/refinance decomposition.',
        'Specified reference schedule retained for structural comparison; no new calibration.',
        'Legacy monthly-probability response reused on intensity scale is an assumption.',
        'Positive-only and refinancing-preserving variants change different structural channels.']
    result['output_sha256'] = {p.name: pair.digest(p) for p in output.iterdir() if p.is_file()}
    pair.write_json(output / 'results.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('root','macro-path','parameter-freeze','empirical-csv','input-inventory','benchmark-reference','output'):
        parser.add_argument('--'+name, required=True, type=Path)
    parser.add_argument('--shares', nargs='+', type=float, default=[0., .25, .5, .75, 1.])
    parser.add_argument('--calibration', choices=['illustrative','legacy_conversion'], default='legacy_conversion')
    parser.add_argument('--gap-mode', choices=['positive_only','preserve_refinancing'], default='positive_only')
    parser.add_argument('--reference-mode',choices=['inherited_psa','matched_max_off'],default='inherited_psa')
    args = vars(parser.parse_args())
    shares, calibration, gap_mode = args.pop('shares'), args.pop('calibration'), args.pop('gap_mode')
    output = args.pop('output').resolve()
    if any(not 0 <= s <= 1 for s in shares) or len(set(shares)) != len(shares):
        parser.error('Shares must be unique finite values in [0,1]')
    for protected in (ROOT/'hazard/data', args['root'].resolve()/'quarters', args['root'].resolve()/'combined'):
        if output == protected or protected in output.parents:
            parser.error('Mixture outputs must be separate from protected inputs')
    # Fail before creating analysis outputs when source completion is missing.
    pair.validated_combined(args['root'].resolve())
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    try:
        for share in shares:
            result = run_pair(**args, output=output / ('share_'+str(share)),
                sensitive_share=share, calibration=calibration, gap_mode=gap_mode)
            rows.append(dict(sensitive_share=share, reported_marginal_b=result['reported_marginal_b'],
                closed_pool_cash_marginal_b=result['closed_pool_cash_marginal_b']))
        pair.write_json(output/'summary.json', dict(scenarios=rows, calibration=calibration,
            gap_mode=gap_mode, reference_mode=args['reference_mode'], empirical_share_estimated=False))
    except BaseException as exc:
        pair.write_json(output/'failed.json', dict(error=str(exc), completed_scenarios=rows,
            failed_utc=datetime.now(timezone.utc).isoformat()))
        raise


if __name__ == '__main__': main()
