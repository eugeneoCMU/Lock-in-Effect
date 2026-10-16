"""Reproducible, offline empirical-grounding evidence package (Tasks 0–2, 7).

Run with --attempt a fresh versioned output directory. Existing stage directories
are never overwritten by the measurement builder.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import sys

import numpy as np
import pandas as pd

from empirical_readiness import build_readiness, sha256, month_ordinal, month_string
from empirical_payoff_measurement import measure_payoffs, audit_gap_support, COHORT_KEYS
from reference_payoff_model import fit_reference

ROOT = Path(__file__).resolve().parents[1]
COMBINED = Path('output/research-rerun/2026-10-14-archive/combined')
PRIOR = Path('output/research-next/2026-10-14/support/attempt-002')
PLAN = Path('docs/superpowers/plans/2026-10-16-empirical-grounding.md')
DEFAULT_ATTEMPT = Path('output/empirical-grounding/2026-10-16/attempt-001')
CLAIM_FIELDS = ['object', 'population', 'denominator', 'period', 'evidence_class',
                'source_receipt', 'assumptions', 'unsupported_extensions']


def write_json(path, value):
    text = json.dumps(value, indent=2, allow_nan=False) + '\n'
    Path(path).write_text(text)


def validate_claim_register(claims):
    for claim in claims:
        for field in CLAIM_FIELDS:
            if field not in claim:
                raise ValueError(f'Claim missing {field}')
        if claim['evidence_class'] not in {'observed', 'conditional-estimated', 'externally imported', 'bounded', 'simulated'}:
            raise ValueError('Invalid evidence_class')
    return True


def load_json(path):
    return json.loads(Path(path).read_text())


def plan_file_references(text):
    return [p for p in re.findall(r'`([^`\n]+)`', text)
            if p.startswith(('output/', 'hazard/', 'tests/', 'docs/')) and len(p) < 240]


def verify_panel_receipt(path, completion):
    actual = sha256(path)
    expected = [value for key, value in completion.get('output_sha256', {}).items()
                if key == 'panel.parquet' or key.endswith('/panel.parquet')]
    if actual not in expected:
        raise ValueError(f'Quarter panel receipt mismatch: {path}')
    return actual


def freeze_inputs(attempt):
    readiness = attempt / 'readiness'
    readiness.mkdir(parents=True, exist_ok=False)
    # Hash small local derivatives/code. Never materialize the archived Drive raw text.
    sources = set()
    for name in plan_file_references((ROOT / PLAN).read_text()):
        p = ROOT / name
        if p.is_file():
            sources.add(p)
    sources.update((ROOT / 'hazard').glob('*.py'))
    sources.update((ROOT / 'tests').glob('test_*.py'))
    sources.update((ROOT / 'paper/final').glob('*.tex'))
    sources.update((ROOT / 'docs/superpowers/specs').glob('2026-10-16-empirical-grounding.md'))
    sources.update((ROOT / COMBINED).glob('*'))
    sources.update((ROOT / PRIOR).glob('*.json'))
    sources.update((ROOT / 'output/research-rerun/2026-10-14-archive/quarters').glob('*/executed_code/*.py'))
    sources.update((ROOT / 'output/research-rerun/2026-10-14-archive/quarters').glob('*/rebuilt/report.json'))
    manifest = {str(p.relative_to(ROOT)): sha256(p) for p in sorted(sources) if p.is_file()}
    write_json(readiness / 'initial-source-inventory.json', manifest)
    write_json(readiness / 'runtime.json', dict(executable=sys.executable, python=sys.version,
        pandas=pd.__version__, numpy=np.__version__, path_scope=str(ROOT),
        preservation='additive implementation; protected manuscripts and historical files never edited'))
    return manifest


def build_measurement(attempt):
    attempt = ROOT / attempt
    manifest = freeze_inputs(attempt)
    report = load_json(ROOT / COMBINED / 'report.json')
    prior = load_json(ROOT / PRIOR / 'completed.json')
    receipts = {name: dict(path=str(ROOT / COMBINED / name), sha256=digest)
                for name, digest in report['output_sha256'].items()}
    support_manifest = load_json(ROOT / PRIOR / 'input_manifest.json')
    for path, digest in support_manifest['input_sha256'].items():
        if Path(path).name in ['report.json', 'cohort_month_panel.parquet', 'MORTGAGE30US_201612_202510.csv', 'rate_source.json']:
            receipts[path] = dict(path=path, sha256=digest)
    for name, digest in prior['output_sha256'].items():
        receipts[f'prior/{name}'] = dict(path=str(ROOT / PRIOR / name), sha256=digest)
    ready = build_readiness(observed_cutoff=report['cutoff'], simulation_end='202511',
        prior_support=prior, input_receipts=receipts)
    write_json(attempt/'readiness/readiness.json', ready)
    failures = [k for k,v in ready['source_checks'].items() if v['status'] != 'matched_local_receipt']
    if failures:
        raise ValueError(f'Input receipt checks failed: {failures}')
    population = report['population']
    register = [dict(object=object_, population=population, denominator=denom,
        period=period, source_version=report['source_semantics_version'], status=status,
        current_limit=limit) for object_,denom,period,status,limit in [
            ('recorded_payoff','adjacent opening principal dollars','201701–202509','measurement_pending','Unknown payoff timing/cause preserved'),
            ('reference_p0','monthly adjacent payoff fraction','training through 202112','not_estimated','No verified neutral refinancing environment'),
            ('sensitive_intensity_share','reference intensity, not borrowers','202206–202511','assumed','Joint share/gamma identification missing'),
            ('gamma','per percentage point positive market-minus-original-coupon gap','202206–202511','assumed','No supported causal or conditional estimate'),
            ('mechanism_causes','selected HARP populations, separately 1000 and 5000 loans','200904–201609','selected_labels_only','Ordinary payoff causes unknown; different population from main panel'),
            ('portfolio_receipts','SOMA security principal','target 2022-05-31','unverified','Joint target support, coupon conversion and cash timing unresolved')]]
    write_json(attempt/'readiness/evidence-register.json', register)
    (attempt/'readiness/REPORT.md').write_text('# Evidence freeze\n\n'
        f'Population: {population}; {report["original_loans"]:,} original loans. '
        f'Source version: {report["source_semantics_version"]}. Observed cutoff: {report["cutoff"]}. '
        'October–November 2025 are simulation months only. Prior designated verdict: insufficient_support.\n\n'
        'Every local derivative and prior support receipt selected for reuse matched its saved hash. '
        'This is a local derivative check, not a new original-provider-source audit. '
        'See evidence-register.json for every object, population, denominator, window and limitation. '
        'Source coverage exceptions are retained verbatim in coverage-exceptions.json.\n')
    write_json(attempt/'readiness/coverage-exceptions.json', {k: report[k] for k in
        ['pre_snapshot_coverage','identity_exceptions_by_quarter','identity_exception_totals',
         'zero_note_rate_excluded_loans','partial_cohort_overrun_count','original_payoff_assumptions']})
    measurement = attempt / 'measurement'; measurement.mkdir(exist_ok=False)
    panel = pd.read_parquet(ROOT / COMBINED / 'cohort_month_panel.parquet')
    measured = measure_payoffs(panel, cutoff=report['cutoff'])
    # Reconcile each category against the frozen quarterly local derivatives.
    amounts = ['prepaid_upb','first_observed_payoff_upb','gap_payoff_upb','opening_upb',
               'adjacent_opening_upb','first_observed_opening_upb','gap_opening_upb','exposure_upb']
    quarterly_totals = pd.Series(0., index=amounts)
    quarter_checks = {}
    for quarter, expected in report['source_report_sha256'].items():
        qroot = ROOT / COMBINED.parent / 'quarters' / quarter / 'rebuilt'
        actual = sha256(qroot/'report.json')
        if actual != expected:
            raise ValueError(f'Quarter report mismatch: {quarter}')
        qreceipt = load_json(qroot.parent/'completed.json')
        panel_hash = verify_panel_receipt(qroot/'panel.parquet', qreceipt)
        quarter_checks[quarter] = dict(report_hash_verified=True, panel_sha256=panel_hash,
            panel_receipt_verified=True)
        quarterly_totals += pd.read_parquet(qroot/'panel.parquet')[amounts].sum()
    totals = measured[amounts].sum()
    if not np.allclose(totals, quarterly_totals, rtol=1e-12, atol=.01):
        raise ValueError('Quarterly payoff/denominator totals do not reconcile')
    audit = dict(population=population, original_loans=report['original_loans'], rows=len(measured),
        cutoff=report['cutoff'], totals={k: float(v) for k,v in totals.items()},
        quarterly_totals={k:float(v) for k,v in quarterly_totals.items()}, quarter_checks=quarter_checks,
        invalid_rows=int((~measured.measurement_valid).sum()),
        invalid_reasons=measured.loc[~measured.measurement_valid,'measurement_issue'].value_counts().to_dict(),
        adjacent_payoff_upb=float(measured.adjacent_payoff_upb.sum()),
        unknown_timing_payoff_upb=float(measured.unallocated_timing_payoff_upb.sum()),
        adjacent_fraction=float(measured.loc[measured.measurement_valid,'adjacent_payoff_upb'].sum() /
            measured.loc[measured.measurement_valid,'adjacent_opening_upb'].sum()),
        opening_partition_max_residual=float((measured.opening_upb - measured.adjacent_opening_upb -
            measured.first_observed_opening_upb - measured.gap_opening_upb).abs().max()),
        source_categories_disjoint=True,
        source_definition='executed_code/freddie_rebuild_stream.py: first=previous is None; adjacent=not first and month==previous+1; gap=elif not adjacent',
        clipping_performed=False, end_balance_ratio_above_one_rows=int((measured.end_balance_cash_ratio > 1).sum()),
        credit_removals='Not separately quantified by this combined cohort panel; source credit states remain in rebuilt report/transition receipts. Never counted as voluntary payoff.',
        interpretation='Pooled dollar-month recorded payoff fraction; not borrower hazard, payoff count or cause-specific outcome')
    write_json(measurement/'denominator-audit.json', audit)
    # Previous completed support search used monthly means; retain it verbatim,
    # and use a separate explicitly lagged as-of view for the new estimand.
    rate_path = next(Path(p) for p in support_manifest['input_sha256'] if p.endswith('MORTGAGE30US_201612_202510.csv'))
    rates = pd.read_csv(rate_path)
    dates = pd.to_datetime(rates.observation_date)
    benchmark = pd.to_numeric(rates.MORTGAGE30US, errors='coerce').groupby(dates.dt.strftime('%Y%m')).mean()/100
    benchmark = benchmark.dropna()
    gap_audit = audit_gap_support(measured, benchmark, gap_basis='original_coupon', lag_months=1)
    measured['benchmark_month'] = measured.reporting_period.map(lambda m: month_string(month_ordinal(m)-1))
    measured['benchmark_rate'] = measured.benchmark_month.map(benchmark)
    measured['gap_pp'] = 100*(measured.benchmark_rate-measured.coupon)
    measured.to_parquet(measurement/'measurements.parquet', index=False)
    write_json(measurement/'gap-support.json', gap_audit)
    designated = load_json(ROOT / PRIOR/'mature2019_measurement_inference.json')
    grid = load_json(ROOT / PRIOR/'support_grid.json')
    cells = [c for c in grid['cells'] if c['year']==2019 and c['min_age_months']==24 and c['max_gap_bp']==-25]
    write_json(measurement/'prior-support-reconciliation.json',dict(designated=designated,
        saved_cell=cells, preserved_status=prior['designated_inference_status'],
        old_gap_sign='contract_minus_market_bp', new_gap_sign='market_minus_original_coupon_pp',
        old_criterion='old gap <= -25 bp corresponds to market-minus-contract >= 0.25 pp',
        old_benchmark='contemporaneous whole-month mean; retained historical diagnostic',
        new_benchmark='previous-month mean available before reporting month',
        new_estimand=True, reason='decision-time as-of benchmark and adjacent-dollar numerator are explicit; no replacement verdict'))
    (measurement/'REPORT.md').write_text('# Recorded payoff measurement and support\n\n'
        f'{len(measured):,} cohort-months; {report["original_loans"]:,} original known-360-month Freddie loans, vintages 2017–2021. '
        f'Window {measured.reporting_period.min()}–{report["cutoff"]}. This is the full rebuilt panel, not the 75,000-loan forward sample.\n\n'
        f'Adjacent recorded payoff principal: ${audit["adjacent_payoff_upb"]:,.2f}; '
        f'first-observed plus reporting-gap timing-unallocated principal: ${audit["unknown_timing_payoff_upb"]:,.2f}. '
        f'Valid adjacent pooled dollar-month fraction: {audit["adjacent_fraction"]:.8f}. '
        f'Invalid/unusable rows: {audit["invalid_rows"]}; reasons in denominator-audit.json. '
        'No ratios were clipped. End-balance/opening views remain cash ratios; no fabricated loan counts.\n\n'
        'Category definitions are disjoint in the frozen executed rebuild source. Every amount category reconciles '
        'to the sum of twenty quarterly local panels, with report hashes checked.\n\n'
        'The new gap is previous-month mean market rate minus rounded original-coupon bin, in percentage points. '
        'This changes benchmark timing relative to the older support search; it is a distinct diagnostic. '
        'Coupon is not a borrower current note rate. Age is a concurrent count-weighted cohort mean, not a borrower eligibility screen. '
        'Support by year/vintage/coupon/mean-age threshold and missing benchmark months is in gap-support.json.\n\n'
        'The designated 2019, mean-age ≥24, old contract-minus-market gap ≤−25bp cell remains insufficient_support: '
        '32 rows, nine strata (ten required), eight months. No alternative band replaces this verdict. '
        'Credit removals are not identifiable as a separate dollar series here; their source state receipts are retained. '
        'Payoff cause, individual within-bin rates and missing timing are not recovered.\n')
    reference = attempt/'reference'; reference.mkdir(exist_ok=False)
    design = dict(evaluation_kind='retrospective', fit_end='202112', development_window=['202201','202205'],
        evaluation_start='202206', evaluation_end='202509', projection_months=['202510','202511'],
        near_zero_bands_pp=[.25,.5], mean_age_bands_months=[0,12,24,36,60,120],
        controls=['vintage','mean_age_band','favorable_refinancing_stratum'],
        reference_condition='market-minus-original-coupon within fixed near-zero bands; favorable refinancing separate',
        decision_time_covariates_verified=False, benchmark_lag_months=1,
        estimator_reuse='grouped_calibration.py scores a different frozen panel and denominator; not an estimator of this outcome',
        choice_timing='retrospective informed by prior exploration; no untouched holdout',
        prespecified_before_new_fit=True)
    write_json(reference/'reference-design.json', design)
    fit = fit_reference(measured, design=design, support={'target_status':prior['designated_inference_status']})
    write_json(reference/'fit.json', fit)
    write_json(reference/'evaluation.json',dict(status='no_reference_predictions',evaluation_kind='retrospective',
        reason=fit['reason'], outside_reference_support_rows=fit['unsupported_evaluation_rows'],
        predictive_performance=None, sampling_interval=None))
    pd.DataFrame(columns=['reporting_period','prediction','support_status']).to_parquet(reference/'reference-predictions.parquet', index=False)
    (reference/'REPORT.md').write_text('# Reference behavior decision\n\n'
        'Status: reference_not_estimated. The designated sample remains insufficiently supported. '
        'Logical monthly probability bounds are [0,1]; these are not useful empirical confidence limits. '
        'Near-zero original-coupon gaps do not establish a neutral refinancing environment. '
        'Loan-level decision-time age/current rate and within-cohort heterogeneity are unavailable in this grouped view.\n\n'
        'The design was written before any new fit. Pre-2022 observations are the initial training candidate; '
        'January–May 2022 has a development role; June 2022–September 2025 is already-explored retrospective evaluation. '
        'October–November 2025 has no observed performance here.\n\n'
        'fit.json reports training-only and fixed-band descriptive diagnostics. Evaluation outcomes never enter those summaries. '
        'No historical mean was assigned to structural p0 and no nonlinear individual hazard was evaluated at a cohort mean. '
        'The existing grouped-calibration scorer uses a different frozen panel, weights and outcome; duplicating or importing '
        'that estimator would not repair the missing reference interpretation. PSA and matched-OFF remain labeled scenario anchors.\n')
    return audit, fit


def build_delivery(attempt):
    attempt = ROOT / attempt
    delivery = attempt/'delivery'
    delivery.mkdir(exist_ok=False)
    audit = load_json(attempt/'measurement/denominator-audit.json')
    fit = load_json(attempt/'reference/fit.json')
    identified = load_json(attempt/'identification/identification.json')
    mc = load_json(attempt/'uncertainty/monte-carlo.json')
    run = load_json(attempt/'uncertainty/run-manifest.json')
    transport = load_json(attempt/'transport/transport-support.json')
    if run['status'] != 'complete_three_seed_pilot' or not run['source_inputs_unchanged']:
        raise ValueError('Pilot is incomplete or inputs changed')
    inventory = load_json(attempt/'readiness/initial-source-inventory.json')
    # New implementation files may evolve during review; protected pre-existing
    # code/manuscripts/data must still match the initial evidence freeze.
    new_stems = ['empirical_readiness','empirical_payoff_measurement','reference_payoff_model',
        'empirical_grounding_pipeline','mixture_identification','paired_scenario_uncertainty',
        'mechanism_evidence_register','portfolio_transport_audit']
    protected = {p:h for p,h in inventory.items()
        if not any(Path(p).stem in [n, 'test_'+n] for n in new_stems)}
    changed = [p for p,h in protected.items() if not (ROOT/p).is_file() or sha256(ROOT/p) != h]
    if changed:
        raise ValueError(f'Protected input changes: {changed}')
    write_json(delivery/'preservation-verification.json', dict(protected_files=len(protected),
        all_unchanged=True, original_raw_sources_rehashed=False,
        source_scope='local derivatives, frozen reports, source code and both dirty manuscripts'))
    claims = []
    def add(object_, value, population, denominator, period, evidence, receipt, assumptions, unsupported):
        claims.append(dict(object=object_,value=value,population=population,denominator=denominator,
            period=period,evidence_class=evidence,source_receipt=receipt,assumptions=assumptions,
            unsupported_extensions=unsupported))
    common_limits = ['borrower hazard','sale/refinance cause','causal no-lock-in effect','SOMA receipt']
    population = 'rebuilt Freddie known360FRM original vintages 2017–2021'
    for object_, value, denominator in [
        ('original_loan_count',audit['original_loans'],'original eligible loans'),
        ('cohort_month_rows',audit['rows'],'cohort-month cells'),
        ('usable_adjacent_rows',audit['rows']-audit['invalid_rows'],'cohort-month cells'),
        ('unusable_adjacent_rows',audit['invalid_rows'],'cohort-month cells'),
        ('adjacent_payoff_principal',audit['adjacent_payoff_upb'],'USD recorded payoff principal'),
        ('timing_unallocated_payoff_principal',audit['unknown_timing_payoff_upb'],'USD recorded payoff principal'),
        ('pooled_adjacent_payoff_fraction',audit['adjacent_fraction'],'adjacent opening USD summed across months'),
        ('end_balance_ratios_above_one_rows',audit['end_balance_ratio_above_one_rows'],'cohort-month cells')]:
        add(object_,value,population,denominator,'201701–202509','observed',
            '../measurement/denominator-audit.json',['source-defined payoff and balance measurements; local derivatives matched'],common_limits)
    add('reference_probability_bounds',fit['supported_reference_bounds'],population,
        'monthly amount-weighted payoff fraction','reference condition unverified','bounded',
        '../reference/fit.json',['logical [0,1] bounds only; no empirical point reference'],
        ['informative empirical interval','estimated p0'])
    for label, summary in mc.items():
        add(label+'_paired_principal_effect',summary['mean'],
            '74,999 May-2022 forward sample records; one component-unresolved record excluded',
            'USD per USD1bn initial principal','202206–202511','simulated',
            '../uncertainty/monte-carlo.json',
            ['three paired seeds','assumed OFF reference','sensitive intensity share 0.75',
             'gamma=-log(0.935) per percentage point','observed-payment rule and supplied saved rate path',
             'October–November2025 are projections'],
            ['sampling confidence interval','estimated response parameters','full SOMA dollars','observed security receipts'])
        add(label+'_simulation_precision', {k:summary[k] for k in ['n_seeds','simulation_sd','mcse','precision_goal_met']},
            'same normalized forward scenario','USD per USD1bn initial principal','202206–202511','simulated',
            '../uncertainty/monte-carlo.json',['across-seed numerical variability only'],['observational sampling uncertainty'])
    causes = load_json(attempt/'mechanisms/cause-bounds.json')
    for p in causes['populations']:
        add('selected_program_refinance_classification_bounds',p['refinance_classification_count_bounds'],
            p['population_id'],'counts among separately specified starting cohort',
            str(p['coverage_start'])+'–'+str(p['coverage_end']),'bounded',
            '../mechanisms/cause-bounds.json',['verified selected-program labels; unknown ordinary payoffs can take either cause'],
            ['general payoff mechanism decomposition','sampling interval','sensitive intensity share'])
    add('historical_paper_result',42600000000.,'historical manuscript model population; not this forward rerun',
        'USD as reported by historical manuscript','historical paper window','simulated',
        str((ROOT/'paper/final/paper_final_v1.tex').relative_to(ROOT)),
        ['historical reported model comparison; not recalibrated or reproduced in this package'],
        ['new empirical estimate','calibration target','comparable normalization without reconciliation'])
    validate_claim_register(claims)
    write_json(delivery/'claim-register.json',claims)
    decision = dict(path='B',status='weak_identification_conditional_sensitivity_package',
        reference=fit['status'],identification=identified['status'],sampling='not_estimated',
        mechanism='selected_program_labels_and_classification_bounds',transport=transport['status'],
        portfolio_receipt_claim_permitted=False,manuscript_edits_performed=False)
    write_json(delivery/'research-decision.json',decision)
    (delivery/'methods.md').write_text('''# Methods and reproduction

The observed population is the full corrected Freddie panel of known 360-month fixed-rate loans, original vintages 2017–2021. It differs from the selected May-2022 forward sample. Reported monthly principal payoff is an amount-weighted cohort-cell cash object, not a loan Bernoulli event.

Measurement subtracts the disjoint first-observed and nonadjacent reporting-gap payoff categories from total recorded payoff. The matching denominator is adjacent prior reported principal. Invalid or zero denominators remain flagged; no clipping creates a probability. Opening and end-balance cash ratios are retained as alternate denominator diagnostics. Source credit removals are not reclassified as voluntary payoffs. One partial-cohort overrun and the known pre-May coverage exceptions remain in the frozen source report; measurement does not fix or hide them.

The behavioral gap is previous-month mean mortgage benchmark minus rounded original coupon bin, in percentage points. Original coupon bins differ from current borrower note rates and from pass-through security coupons. Previous-month means are available before the reporting month; favorable refinancing opportunities, qualification and offers remain unobserved. Concurrent mean age is count-weighted and does not implement an individual or decision-time borrower-age screen.

The old designated support cell is retained with its original contemporaneous monthly benchmark and original contract-minus-market gap sign. The new as-of view is a different diagnostic, not a relabeled replacement. The reference design declares pre-2022 training candidates, January–May2022 development, and June2022–September2025 retrospective evaluation. All were informed by earlier exploration. October–November2025 are projections. Near-zero bands are fixed at ±0.25 and ±0.5 percentage points before a new fit; no reference is fitted because support and reference interpretation fail.

The joint mixture profile API uses p=1-exp(-lambda0*((1-s)+s*exp(-gamma*gplus))), with lambda0=-log(1-p0). Tests cover endpoints, product ridges, missing support, narrow gaps and controls absorbing the gap. No empirical reference predictions means no empirical score surface, point estimate or confidence contour. A numerical optimizer cannot repair missing identification.

The forward pilot runs the same assumed reference, 75% mixture and matched-floor cases using seeds42,31415,271828. The source sample excludes one record whose balance components remain unresolved. All cases use the saved rate path, observed payment rule, full-book principal ledger and USD1bn initial normalization. Same seed pairs cases; endogenous exits may change subsequent random draw alignment. Across-seed standard deviation and MCSE measure numerical noise only. The declared precision goal is max(USD100,000 per USD1bn,5% of absolute mean effect). Separate sampling-status and assumption-envelope files contain no invented confidence coverage.

HARP pilot and expansion are different selected Fannie populations. Verified selected-program labels are preserved only within documented source coverage. Ordinary/unmatched payoff causes remain unknown. Classification bounds, executed HMDA cost distributions and sensitive intensity share refer to different objects. Saved holdings are derivatives, not a verified joint May31,2022 target. Coupon conversion and security cash timing remain unresolved. No normalized result is multiplied by total SOMA holdings.

Reproduce measurement with `PYTHONPATH=/private/tmp/hmda-system-python39:hazard:. /usr/bin/python3 hazard/empirical_grounding_pipeline.py --attempt output/empirical-grounding/2026-10-16/attempt-NEW` from the repository root. The runtime path is recorded in readiness/runtime.json and may need local resolution. The builder refuses existing stage directories. Mechanism/transport and pilot reproduction scripts are included in their stage directories; copy those scripts to a new attempt before running to preserve this delivery. To assemble a completed attempt, use the same command with `--delivery` after all stages exist. No network or raw-source rebuild is required.
''')
    effects = '\n'.join(f'- {name}: mean ${s["mean"]:,.0f}; simulation SD ${s["simulation_sd"]:,.0f}; MCSE ${s["mcse"]:,.0f}; precision goal met: {s["precision_goal_met"]}.' for name,s in mc.items())
    (delivery/'research-decision.md').write_text('# Research decision: Path B\n\n'
        'The package supports recorded-payoff measurement, selected-program mechanism bounds and conditional normalized scenarios. '
        'It does not establish an empirical no-lock-in reference, sensitive intensity share, gamma, observational sampling interval, '
        'joint SOMA transport or security receipts. These are completed negative/support-limited findings, not omitted estimates.\n\n'
        f'Observed panel: {audit["original_loans"]:,} original loans, {audit["rows"]:,} cohort-months through September2025. '
        f'{audit["rows"]-audit["invalid_rows"]:,} adjacent-denominator rows are usable; {audit["invalid_rows"]} are not. '
        f'First-observed/reporting-gap timing remains unallocated for ${audit["unknown_timing_payoff_upb"]:,.0f} '
        'of recorded principal. No sale/refinance cause was fabricated.\n\n'
        'Normalized paired loan-principal differences (reference cash minus scenario cash, June2022–November2025):\n\n'
        +effects+'\n\nThese are conditional simulations per USD1bn initial principal. MCSE is numerical precision; '
        'scenario envelopes are assumptions; neither is a sampling confidence interval. '
        'The historical USD42.6bn manuscript result remains a separate historical comparison.\n\n'
        'All required unsuccessful/unavailable conditions are recorded in claim-register.json and the stage reports. '
        'A future point-reference claim needs source-bound borrower decision-time covariates and a supported reference environment; '
        'joint parameter inference additionally needs residual identifying gap variation and a justified uncertainty design. '
        'A portfolio claim additionally needs joint target support, sourced coupon conversion and loan-to-security receipt mapping. '
        'No manuscript edits, provider contacts, licenses or account changes were made.\n')
    # Scientific figure, not an empirical parameter contour.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    d = pd.read_parquet(attempt/'measurement/measurements.parquet')
    valid = d[d.measurement_valid]
    monthly = valid.groupby('reporting_period')[['adjacent_payoff_upb','adjacent_opening_upb']].sum()
    fraction = monthly.adjacent_payoff_upb/monthly.adjacent_opening_upb
    fig, axes = plt.subplots(1,2,figsize=(12,4.5))
    axes[0].plot(pd.to_datetime(fraction.index,format='%Y%m'),fraction*100,color='#204e68')
    axes[0].set(title='Observed adjacent-month recorded payoff',xlabel='Reporting month',ylabel='Payoff / adjacent opening principal (%)')
    axes[0].axvline(pd.Timestamp('2022-06-01'),color='grey',ls='--',lw=1)
    labels=list(mc)
    axes[1].bar(labels,[mc[k]['mean']/1e6 for k in labels],color='#567887',
        yerr=[mc[k]['mcse']/1e6 for k in labels],capsize=5)
    axes[1].set(title='Conditional paired principal difference',xlabel='Assumed scenario',ylabel='USD million per USD1bn initial principal')
    fig.text(.02,.01,'Left: rebuilt Freddie panel Jan2017–Sep2025. Right: 74,999-record forward sample Jun2022–Nov2025; error bars = ±1 MCSE, 3 seeds; no sampling interval.',fontsize=8)
    fig.tight_layout(rect=[0,.05,1,1]);fig.savefig(delivery/'measurement-and-scenario-precision.png',dpi=160);plt.close(fig)
    workspace = ROOT/'.superpowers/sdd/2026-10-16-empirical-grounding'
    tests = delivery/'test-receipts';tests.mkdir()
    for p in workspace.glob('*.log'):
        shutil.copy2(p,tests/p.name)
    if (workspace/'progress.md').exists():
        shutil.copy2(workspace/'progress.md',delivery/'implementation-ledger.md')
    # Hash every stage output, excluding this final seal itself.
    outputs = {str(p.relative_to(attempt)):sha256(p) for p in sorted(attempt.rglob('*'))
               if p.is_file() and p.name != 'output-sha256.json'}
    write_json(delivery/'output-sha256.json',outputs)
    return decision


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', type=Path, default=DEFAULT_ATTEMPT)
    parser.add_argument('--delivery', action='store_true')
    args = parser.parse_args()
    if args.delivery:
        print(json.dumps(build_delivery(args.attempt)))
    else:
        audit, fit = build_measurement(args.attempt)
        print(json.dumps(dict(measurement_rows=audit['rows'], invalid_rows=audit['invalid_rows'], reference_status=fit['status'])))
