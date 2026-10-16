"""Source-bound support and linear gap/control diagnostics without fitting p0.

Residualizing a gap is a design diagnostic. It neither estimates the nonlinear
mixture nor establishes its local/global, statistical or causal identification.
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from empirical_readiness import sha256
from empirical_payoff_measurement import COHORT_KEYS

AGE_EDGES = [0, 12, 24, 36, 60, 120, np.inf]
AGE_LABELS = ['0–11', '12–23', '24–35', '36–59', '60–119', '120+']
GAP_EDGES = [-np.inf, 0, .25, .5, 1, 2, np.inf]
GAP_LABELS = ['nonpositive', '(0,0.25]', '(0.25,0.5]', '(0.5,1]', '(1,2]', '>2']
ALLOWED_CONTROLS = ['reporting_period','coupon','vintage','age_band','cohort']


def prepared(data):
    d = data.copy()
    d['reporting_period'] = d.reporting_period.astype(str)
    d['age_band'] = pd.cut(d.mean_loan_age, AGE_EDGES, labels=AGE_LABELS, right=False)
    valid = (d.measurement_valid & np.isfinite(d.gap_pp)
             & np.isfinite(d.adjacent_opening_upb) & (d.adjacent_opening_upb > 0))
    return d, valid


def audit_identifying_variation(data, *, controls):
    if not controls or len(set(controls)) != len(controls) or set(controls)-set(ALLOWED_CONTROLS):
        raise ValueError('Use distinct declared calendar/coupon/vintage/age/cohort controls')
    d, valid = prepared(data)
    if 'cohort' in controls:
        if not set(COHORT_KEYS).issubset(d):
            raise ValueError('Full source cohort keys required')
        valid &= d[COHORT_KEYS].notna().all(axis=1)
        d['cohort'] = d[COHORT_KEYS].astype(str).agg('|'.join,axis=1)
    for key in controls:
        valid &= d[key].notna()
    used = d[valid]
    result = dict(controls=controls,rows_used=len(used),excluded_rows=int((~valid).sum()),
        gap_basis='positive_market_minus_original_coupon_bin_pp',
        weight_basis='adjacent_opening_principal',parameter_identification_established=False,
        reference_estimated=False,diagnostic_kind='weighted_linear_positive_gap_residualization',
        interpretation='Linear design diagnostic only; does not fit or establish identification of the nonlinear intensity mixture.')
    if used.empty:
        return dict(result,status='no_usable_rows',gap_absorbed_by_controls=None,
                    residualized_variation_share=None,control_rank=None)
    parts = [np.ones((len(used),1))]
    names = ['intercept']
    for key in controls:
        dummy = pd.get_dummies(used[key].astype(str),prefix=key,drop_first=True,dtype=float)
        parts.append(dummy.to_numpy());names.extend(dummy.columns.tolist())
    x = np.column_stack(parts)
    weights = used.adjacent_opening_upb.to_numpy(float)
    weights /= weights.sum()
    y = np.maximum(used.gap_pp.to_numpy(float),0.)
    root_w = np.sqrt(weights)
    wx = x*root_w[:,None];wy=y*root_w
    coefficients,_,rank,singular = np.linalg.lstsq(wx,wy,rcond=1e-10)
    # Use explicit reductions for these moments. The local macOS BLAS matmul
    # path raises spurious floating exceptions on finite large dummy designs.
    # einsum avoids that path; the least-squares design and estimand are unchanged.
    residual = wy-np.einsum('ij,j->i',wx,coefficients)
    residual_ss = float(np.sum(residual*residual))
    mean = float(np.sum(weights*y))
    total_ss = float(np.sum(weights*(y-mean)**2))
    absorbed = np.sqrt(residual_ss) <= 1e-10*max(1.,float(np.linalg.norm(wy)))
    result.update(status='diagnostic_complete',control_columns=len(names),control_rank=int(rank),
        rank_deficient=bool(rank<len(names)),column_names=names,
        positive_gap_rows=int((y>0).sum()),positive_gap_weight_share=float(weights[y>0].sum()),
        positive_gap_weighted_sd_pp=float(np.sqrt(total_ss)),
        residualized_positive_gap_sd_pp=float(np.sqrt(residual_ss)),
        residualized_variation_share=residual_ss/total_ss if total_ss>1e-20 else None,
        gap_absorbed_by_controls=bool(absorbed),
        minimum_retained_singular_value=float(singular[rank-1]) if rank else None,
        rank_rcond=1e-10,weight_normalized=True)
    return result


def joint_support(data):
    d, valid = prepared(data)
    missing_age = valid & d.age_band.isna()
    valid &= d.age_band.notna()
    d['gap_band'] = pd.cut(d.gap_pp,GAP_EDGES,labels=GAP_LABELS,right=True)
    d['year'] = d.reporting_period.str[:4]
    selected = d[valid]
    group_keys = ['year','vintage','age_band','gap_band']
    strata = [k for k in COHORT_KEYS if k in selected]
    cells = []
    for keys, group in selected.groupby(group_keys,observed=True):
        months = sorted(group.reporting_period.unique().tolist())
        year = str(keys[0]); end_month = 9 if year=='2025' else 12
        opening = float(group.adjacent_opening_upb.sum())
        payoff = float(group.adjacent_payoff_upb.sum())
        cells.append(dict(zip(group_keys,[str(k) for k in keys]), rows=len(group),
            strata=len(group[strata].drop_duplicates()),observed_months=months,
            missing_calendar_months=[f'{year}{n:02d}' for n in range(1,end_month+1) if f'{year}{n:02d}' not in months],
            adjacent_opening_upb=opening,adjacent_payoff_upb=payoff,
            amount_weighted_fraction=payoff/opening,
            unknown_timing_payoff_upb=float(group.unallocated_timing_payoff_upb.sum())))
    return dict(cells=cells,missing_age_rows=int(missing_age.sum()),
        invalid_or_missing_gap_rows=int((~prepared(data)[1]).sum()),
        age_basis='concurrent_cohort_mean_not_borrower_decision_time_age',
        gap_basis='previous_month_mean_market_minus_original_coupon_bin_percentage_points',
        causal_reference_supported=False,inference_support_verdict_changed=False,
        interpretation='Joint descriptive support only. Cell counts and residual variation do not establish reference behavior or parameter identification.')


def main(output):
    root = Path(__file__).resolve().parents[1]
    previous = root/'output/empirical-grounding/2026-10-16/attempt-001'
    source = previous/'measurement/measurements.parquet'
    previous_seal = json.loads((previous/'delivery/output-sha256.json').read_text())
    assert sha256(source)==previous_seal['measurement/measurements.parquet']
    output = root/output
    output.mkdir(parents=True,exist_ok=False)
    specs = [
        dict(name='calendar',controls=['reporting_period']),
        dict(name='calendar_coupon',controls=['reporting_period','coupon']),
        dict(name='calendar_coupon_vintage_age',controls=['reporting_period','coupon','vintage','age_band']),
        dict(name='calendar_cohort',controls=['reporting_period','cohort'])]
    design = dict(source=str(source.relative_to(root)),source_sha256=sha256(source),
        frozen_before_computation=True,designs=specs,age_edges_months=['0','12','24','36','60','120','infinity'],
        gap_edges_pp=['-infinity','0','0.25','0.5','1','2','infinity'],
        views={'all_observed':['201701','202509'],'retrospective_evaluation':['202206','202509'],
               'retrospective_positive_gap_only':['202206','202509']},
        evidence_limit='No p0 fitting, no score surface, no confidence region, no revision of prior support verdict')
    (output/'design.json').write_text(json.dumps(design,indent=2)+'\n')
    d = pd.read_parquet(source)
    for name, controls in [(spec['name'],spec['controls']) for spec in specs]:
        # Results are emitted after each design for recoverable progress.
        for view,(start,end) in design['views'].items():
            subset = d[d.reporting_period.astype(str).between(start,end)]
            if view.endswith('positive_gap_only'):
                subset = subset[subset.gap_pp>0]
            result = audit_identifying_variation(subset,controls=controls)
            (output/f'{view}-{name}.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    support = joint_support(d)
    (output/'joint-support.json').write_text(json.dumps(support,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(support['cells']).to_csv(output/'joint-support.csv',index=False)
    return finalize_reports(output, source)


def finalize_reports(output, source):
    root=Path(__file__).resolve().parents[1]
    support=json.loads((output/'joint-support.json').read_text())
    rows=[]
    for file in sorted(output.glob('*calendar*.json')):
        result=json.loads(file.read_text())
        rows.append(dict(view=file.stem,rows=result['rows_used'],
            control_columns=result['control_columns'],control_rank=result['control_rank'],
            residualized_variation_share=result['residualized_variation_share'],
            residualized_gap_sd_pp=result['residualized_positive_gap_sd_pp'],
            gap_absorbed_by_controls=result['gap_absorbed_by_controls']))
    pd.DataFrame(rows).to_csv(output/'variation-summary.csv',index=False)
    selected=json.loads((output/'retrospective_evaluation-calendar_coupon.json').read_text())
    positive=json.loads((output/'retrospective_positive_gap_only-calendar_coupon.json').read_text())
    retained=selected['residualized_variation_share']
    report=(
        '# Positive-gap variation and joint support\n\n'
        'This follow-up fills the source-bound calendar/coupon diagnostic left unavailable in attempt-001. '
        'It uses the sealed measured panel only; it fits no reference payoff rate or mixture response and changes no prior result.\n\n'
        f'In the retrospective June2022–September2025 view, {selected["rows_used"]:,} usable cohort-month rows '
        'enter a weighted linear residualization of positive market-minus-original-coupon gap. '
        f'Calendar-month and coupon-bin controls leave {100*retained:.6f}% of its weighted centered variation '
        f'and absorb {100*(1-retained):.6f}%. The residual gap standard deviation is '
        f'{selected["residualized_positive_gap_sd_pp"]:.8f} percentage points.\n\n'
        f'Among the {positive["rows_used"]:,} retrospective rows with a strictly positive gap, calendar and coupon '
        'controls absorb the linear gap to numerical precision. This follows the construction: '
        'within the positive region the gap equals the month-specific benchmark minus the fixed coupon-bin rate. '
        'The hinge at zero leaves a small amount of nonadditive variation in the full evaluation view.\n\n'
        'This diagnostic does not residualize the complete nonlinear intensity model. It does not prove that '
        'every nonlinear model is unidentified, quantify a parameter ridge, or supply a confidence region. '
        'It shows how little independent linear gap variation survives these controls in this grouped measurement. '
        'A supported reference, within-bin borrower heterogeneity, decision-time covariates, and justified inference remain unavailable.\n\n'
        f'Joint support is reported in {len(support["cells"]):,} descriptive cells crossing calendar year, origination vintage, '
        'concurrent cohort-mean-age band and gap band. Each includes observed/missing calendar months, cohort strata, '
        'matching exposure/payoff dollars and unknown-timing principal. Missing months in a vintage-year can reflect '
        'origination timing or the requested age/gap selection; they are not imputed or automatically called source gaps. '
        f'Missing/unclassifiable mean-age rows among otherwise usable measurements: {support["missing_age_rows"]}. '
        'Count thresholds are not used to rename a cell inferentially supported.\n\n'
        'The prior designated insufficient_support verdict is unchanged. The source-bound reference, share and gamma '
        'remain unestimated; no new simulation, SOMA transport, manuscript change or provider contact was performed. '
        'The earlier Path B package remains sealed and unchanged.\n\n'
        'Reproduce from the repository root with '
        '`PYTHONPATH=/private/tmp/hmda-system-python39:hazard:. /usr/bin/python3 hazard/empirical_identification_support.py '
        '--output output/empirical-grounding/2026-10-16/attempt-NEW-support-diagnostics`. '
        'The output directory must be new.\n')
    (output/'REPORT.md').write_text(report)
    claims=[]
    for object_,value in [('linear_positive_gap_retained_variation_share',retained),
        ('linear_positive_gap_absorbed_variation_share',1-retained),
        ('linear_positive_gap_residual_sd_pp',selected['residualized_positive_gap_sd_pp'])]:
        claims.append(dict(object=object_,value=value,population='rebuilt known360FRM Freddie 2017–2021 vintages; usable cohort-months',
            denominator='adjacent-opening-principal-weighted centered positive-gap variance; SD in percentage points',
            period='202206–202509',evidence_class='observed',
            source_receipt='retrospective_evaluation-calendar_coupon.json',
            assumptions=['positive gap from previous-month benchmark and rounded original coupon bins',
                         'linear dummy controls and normalized adjacent-dollar weights', 'lstsq rcond=1e-10'],
            unsupported_extensions=['identification of full nonlinear mixture','borrower elasticity','causal no-lock-in reference','confidence region']))
    (output/'claim-register.json').write_text(json.dumps(claims,indent=2)+'\n')
    final_sources={str(p.relative_to(root)):sha256(p) for p in [source,Path(__file__),root/'tests/test_empirical_identification_support.py']}
    (output/'source-sha256.json').write_text(json.dumps(final_sources,indent=2)+'\n')
    (output/'output-sha256.json').write_text(json.dumps({str(p.relative_to(output)):sha256(p)
        for p in sorted(output.iterdir()) if p.is_file() and p.name!='output-sha256.json'},indent=2)+'\n')
    return output


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=Path('output/empirical-grounding/2026-10-16/attempt-002-support-diagnostics'))
    main(parser.parse_args().output)
