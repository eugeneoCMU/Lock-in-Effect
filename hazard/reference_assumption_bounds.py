"""Outer bounds for recorded payoff on fixed observed risksets, under named assumptions."""
import json
from pathlib import Path
import hashlib
import datetime
import shutil
import numpy as np
import pandas as pd

DEFAULT_CAPS=[.001,.0025,.005]


def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1048576),b''):h.update(b)
    return h.hexdigest()


def payoff_bounds(panel,*,caps=DEFAULT_CAPS):
    if not caps or any(isinstance(c,bool) or not np.isfinite(c) or not 0<=c<=1 for c in caps):raise ValueError('Caps must be finite probabilities in [0,1]')
    d=panel[['loan_id','reporting_period','at_risk_adjacent','current_note_gap_pp','adjacent_opening_upb','adjacent_payoff_upb']].copy()
    if d.duplicated(['loan_id','reporting_period']).any():raise ValueError('Duplicate loan-month')
    if not (np.isfinite(d.adjacent_opening_upb).all() and np.isfinite(d.adjacent_payoff_upb).all()):raise ValueError('Nonfinite denominator or payoff')
    if ((d.adjacent_opening_upb<0)|(d.adjacent_payoff_upb<0)|(d.adjacent_payoff_upb>d.adjacent_opening_upb)).any():raise ValueError('Payoff exceeds opening exposure')
    d=d[d.at_risk_adjacent & (d.adjacent_opening_upb>0) & d.reporting_period.between('202206','202509')]
    monthly=[]
    for month,g in d.groupby('reporting_period',sort=True):
        w=float(g.adjacent_opening_upb.sum());paid=float(g.adjacent_payoff_upb.sum())
        known=np.isfinite(g.current_note_gap_pp);positive=known & (g.current_note_gap_pp>0);nonpositive=known & ~positive;unknown=~known
        wp=float(g.loc[positive,'adjacent_opening_upb'].sum());pp=float(g.loc[positive,'adjacent_payoff_upb'].sum())
        wu=float(g.loc[unknown,'adjacent_opening_upb'].sum());pu=float(g.loc[unknown,'adjacent_payoff_upb'].sum())
        common=dict(reporting_period=str(month),risk_rows=len(g),opening_upb=w,observed_payoff_upb=paid,observed_fraction=paid/w,
            known_positive_opening_upb=wp,known_nonpositive_opening_upb=float(g.loc[nonpositive,'adjacent_opening_upb'].sum()),unknown_gap_opening_upb=wu)
        def add(name,lower,upper,cap=None):
            monthly.append(dict(common,scenario=name,monthly_positive_gap_cap_probability=cap,
                reference_fraction_lower=(paid+lower)/w,reference_fraction_upper=(paid+upper)/w,
                extra_payoff_lower=lower,extra_payoff_upper=upper,
                additional_fraction_lower=lower/w,additional_fraction_upper=upper/w))
        add('unrestricted',-paid,w-paid)
        add('monotone_recorded_payoff',0.,w-paid)
        for cap in caps:
            # Aggregate potential-outcome constraints on the observed positive-gap riskset.
            # Unknown-gap exposure remains monotone but uncapped; no missing support is renormalized away.
            upper=min(float(cap)*wp,max(0.,wp-pp))+max(0.,wu-pu)
            add('positive_gap_cap_'+str(cap),0.,upper,float(cap))
    summaries=[]
    for name in dict.fromkeys(x['scenario'] for x in monthly):
        rows=[x for x in monthly if x['scenario']==name];total=sum(x['opening_upb'] for x in rows)
        observed=sum(x['observed_payoff_upb'] for x in rows)/total
        summaries.append(dict(scenario=name,months=len(rows),risk_rows=sum(x['risk_rows'] for x in rows),
            observed_exposure_weighted_fraction=observed,
            reference_fraction_lower=sum(x['reference_fraction_lower']*x['opening_upb'] for x in rows)/total,
            reference_fraction_upper=sum(x['reference_fraction_upper']*x['opening_upb'] for x in rows)/total,
            additional_fraction_lower=sum(x['extra_payoff_lower'] for x in rows)/total,
            additional_fraction_upper=sum(x['extra_payoff_upper'] for x in rows)/total,
            unknown_gap_exposure_fraction=sum(x['unknown_gap_opening_upb'] for x in rows)/total))
    return dict(monthly=monthly,summary=summaries,causal_effect_estimated=False,reference_model_fitted=False,
        design=dict(population='Observed adjacent risksets of fixed2021Q1 n5000 origination sample, June2022-Sep2025',
            outcome='Recorded payoff of prior opening principal; sale/refinance cause unknown',
            unrestricted='Counterfactual payoff lies between zero and full opening exposure, without response restrictions',
            monotone='Removing lock-in weakly increases recorded payoff on this fixed observed riskset; imposed potential-outcome restriction',
            capped='Monotone; known nonpositive-gap outcomes fixed at observed values; average additional payoff fraction among known positive-gap exposures capped separately each month',
            unknown_gap='Retained in denominator; monotone but uncapped in capped scenarios',
            caps_probability=list(map(float,caps)),caps_pp_per_month=[100*float(c) for c in caps],
            caps_status='Illustrative retrospective sensitivity choices, not estimated limits or confidence bounds',
            bound_status='Outer bounds under imposed realized potential-outcome constraints; weighted binary outcomes can make interior values unattainable',
            normalization='Exposure-weighted average over observed loan-months; repeated principal exposures, no population scaling',
            dynamic_limit='Counterfactual riskset composition, survival, replacement loans and general-equilibrium rate response held outside this calculation; not a dynamic portfolio cash-flow counterfactual',
            identification='Neither sensitive share nor gamma is inferred; observational payoff fractions do not identify structural probabilities'))


def run(drive_root):
    root=Path(drive_root)/'Lock-in-Effect cloud results';source=root/'origination-reference-20261016T151834Z'
    name='private-origination-borrower-panel.parquet';seal=json.loads((source/'output-sha256.json').read_text())
    if name not in seal:raise ValueError('Panel absent from seal')
    for n,h in seal.items():
        if Path(n).name!=n or sha(source/n)!=h:raise ValueError('Prior output mismatch')
    output=root/('reference-assumption-bounds-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    output.mkdir(exist_ok=False);output.chmod(0o700)
    # Freeze assumptions before the new payoff calculation.
    (output/'declared-scenarios.json').write_text(json.dumps(dict(caps_probability=DEFAULT_CAPS,unrestricted=True,monotone=True,cap_application='positive-gap group monthly',no_dynamic_portfolio_claim=True),indent=2)+'\n')
    result=payoff_bounds(pd.read_parquet(source/name))
    if any(x['risk_rows']!=172640 for x in result['summary']):raise ValueError('Target riskset changed')
    (output/'bounds.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    pd.DataFrame(result['monthly']).to_csv(output/'monthly-bounds.csv',index=False)
    pd.DataFrame(result['summary']).to_csv(output/'summary.csv',index=False)
    shutil.copyfile(__file__,output/'executed_reference_assumption_bounds.py')
    (output/'input-receipts.json').write_text(json.dumps(dict(panel_sha256=sha(source/name),source_seal_sha256=sha(source/'output-sha256.json'),source_folder=str(source)),indent=2)+'\n')
    report='Assumption-dependent recorded-payoff bounds\n\nFixed observed2021Q1risksets June2022-Sep2025; sample5000loans,172640adjacent at-risk loan-months. Weighted fractions use repeated opening-principal exposures. No causal parameter is estimated.\n\n'
    for x in result['summary']:
        report+=f"{x['scenario']}: observed weighted payoff fraction {x['observed_exposure_weighted_fraction']:.8%}; reference outer range [{x['reference_fraction_lower']:.8%}, {x['reference_fraction_upper']:.8%}]; additional fraction [{x['additional_fraction_lower']*100:.8f}, {x['additional_fraction_upper']*100:.8f}] percentage points.\n"
    report+='\nMonotonicity and the positive-gap caps are imposed realized potential-outcome restrictions. Caps0.1/0.25/0.5percentage points apply monthly within known positive-gap exposures; missing gaps are retained monotone and uncapped. Bounds are outer bounds, not sampling or causal confidence intervals. The calculation holds observed risksets fixed and is not a dynamic portfolio projection or cumulative distinct principal effect. Share/gamma and causal reference remain unestimated.\n'
    (output/'REPORT.md').write_text(report)
    final={p.name:sha(p) for p in output.iterdir() if p.is_file()}
    (output/'output-sha256.json').write_text(json.dumps(final,indent=2)+'\n')
    assert all(sha(output/n)==h for n,h in final.items())
    print(report);print('COMPLETE: all assumption-bounds output hashes verified:',output)
    return output
