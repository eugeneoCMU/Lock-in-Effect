"""Reproducible synthetic validation; never an empirical borrower calibration."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from hazard.dynamic_refinancing import solve_dynamic_refinancing
from hazard.refinancing_exercise_bridge import dynamic_incentive, bridge_probabilities, fit_exercise_rate, evaluate_exercise_rate


def run(output):
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    target=output/'synthetic-demonstration.json'
    inputs=dict(initial_coupon=.08,market_rates=[.06,.02],transition_matrix=[[0,1],[0,1]],
                remaining_months=120,discount_rate=.04,cost_fraction=.005)
    solution=solve_dynamic_refinancing(**inputs)
    waiting=dynamic_incentive(solution,market_state=0)
    exercising=dynamic_incentive(solution,market_state=1,remaining_months=119)
    supplied_alpha=.12
    cases=[]
    for name,incentive,eligible in [('dynamic_wait',waiting,True),('eligible_exercise',exercising,True),
                                    ('ineligible_exercise',exercising,False)]:
        probabilities=bridge_probabilities(advantage_fraction=incentive['advantage_fraction'],
            tie_tolerance=incentive['tie_tolerance'],eligible=eligible,arrival_intensity=supplied_alpha,
            sale=.02,other=.005,default=.005)
        cases.append(dict(name=name,incentive=incentive,eligible=eligible,probabilities=probabilities))
    declared=dict(complete_first_exit_labels=True,comparable_outstanding_risk_set=True,
        refinancing_scope='same_balance_remaining_term_rate_term',evidence_class='synthetic',
        label_provenance='Fixed-seed simulated mutually exclusive causes; no imported payoff codes',
        risk_set_definition='Independent full-month opening synthetic risk cells; 10000 borrowers each',
        incentive_provenance='Supplied no-exit dynamic solver scenario in this manifest; fixed gate over month',
        eligibility_provenance='Binary status supplied in each synthetic cell',
        competing_intensity_provenance='Known synthetic sale .02, other .005, default .005 per month')
    rng=np.random.default_rng(20261014)
    rows=[]
    causes=('survive','refinancing','sale','other','default')
    for year in (2023,2024):
        for month in range(1,13):
            for case in cases:
                counts=rng.multinomial(10000,[case['probabilities'][k] for k in causes])
                rows.append(dict(cell_id=case['name'],month=f'{year}-{month:02}',exposure=10000,
                    eligible=case['eligible'],advantage_fraction=case['incentive']['advantage_fraction'],
                    tie_tolerance=case['incentive']['tie_tolerance'],sale=.02,other=.005,default=.005,
                    counts={k:int(v) for k,v in zip(causes,counts)}))
    fit=fit_exercise_rate(rows,training_end='2023-12',contract=declared)
    holdout=[r for r in rows if r['month']>'2023-12']
    evaluation=evaluate_exercise_rate(holdout,fit=fit,contract=declared)
    poisoned=[r if r['month']<='2023-12' else dict(month=r['month'],counts='unread',exposure=-1) for r in rows]
    parity=fit_exercise_rate(poisoned,training_end='2023-12',contract=declared)
    assert fit['training_sha256']==parity['training_sha256']
    assert fit['arrival_intensity']==parity['arrival_intensity']
    payload=dict(evidence_class='synthetic',seed=20261014,supplied_arrival_intensity=supplied_alpha,
                 solver_inputs=inputs,cases=cases,data_contract=declared,fit=fit,evaluation=evaluation,
                 chronological_poison_check=True,
                 limitations=['Not an empirical alpha estimate or causal decomposition',
                    'The dynamic gate assumes immediate future exercise availability and no forced exits; alpha/competing intensities do not enter its recursion',
                    'Gates and competing intensities held fixed during each month',
                    'Competing intensities and eligibility supplied, not separately estimated',
                    'Independent synthetic monthly cells are not a longitudinal borrower portfolio',
                    'No portfolio principal cash-flow mapping or production integration'])
    target.write_text(json.dumps(payload,indent=2,allow_nan=False)+'\n')
    (output/'synthetic-risk-cells.json').write_text(json.dumps(rows,indent=2)+'\n')
    readiness=dict(status='empirical_fit_unavailable_without_cause_labeled_risk_set',
        empirical_fitted_parameters=0,new_portfolio_estimates=0,
        required_inputs=['Complete exclusive survive/refinancing/sale/other/default counts on opening borrower exposure',
            'Verified rate-term refinance scope matching same balance and remaining term, or a revised objective',
            'Comparable eligibility/risk-set coverage, including non-events and competing exits',
            'Documented decision-date quotes, transition expectations, costs, discount rates and remaining terms',
            'Explicit known/estimated competing cause intensities and binary eligibility',
            'Training period frozen before any held-out outcome analysis'],
        source_disposition=dict(Freddie='Aggregate voluntary payoffs do not identify refinance versus sale',
            NSMO='Previously audited public termination timing does not identify causes or actual dollar closing costs',
            ASMB_2024='Previously audited questionnaire lacks claimed realized cause split; response access unverified',
            Fannie_HARP='Positive selected historical refinance links; complete comparable risk set and matching objective not established'),
        audited_evidence='output/research-next/2026-10-14/theory-source-audit/data-access-evidence.json',
        source_access_this_run='No external access or raw data acquisition attempted')
    (output/'data-readiness.json').write_text(json.dumps(readiness,indent=2)+'\n')
    paths=[Path(__file__),Path(__file__).parents[1]/'hazard/refinancing_exercise_bridge.py',
           Path(__file__).parents[1]/'hazard/dynamic_refinancing.py',
           Path(__file__).parents[1]/'hazard/structural_sale_extension.py']
    receipt=dict(code_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                 outcome_files_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (target, output/'synthetic-risk-cells.json', output/'data-readiness.json')})
    (output/'demonstration-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(dict(output=str(output),fit_status=fit['status'],
        synthetic_alpha=fit['arrival_intensity'],heldout_rmse=evaluation['refinancing_probability_rmse'],
        training_exposure=fit['training_exposure'],heldout_exposure=evaluation['exposure'],
        incompatible_events=evaluation['incompatible_event_count'])))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True)
    run(parser.parse_args().output)
