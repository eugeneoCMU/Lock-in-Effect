"""Independent likelihood, chronology, gate and first-exit checks."""
import importlib
import math
import numpy as np
import pytest
from hazard.dynamic_refinancing import solve_dynamic_refinancing

pytestmark = pytest.mark.filterwarnings('error')


def bridge():
    return importlib.import_module('hazard.refinancing_exercise_bridge')


def contract(**changes):
    d=dict(complete_first_exit_labels=True, comparable_outstanding_risk_set=True,
           refinancing_scope='same_balance_remaining_term_rate_term',
           label_provenance='synthetic known causes', risk_set_definition='synthetic full-month opening loans',
           incentive_provenance='fixed supplied solver scenario', eligibility_provenance='known simulated binary status',
           competing_intensity_provenance='known synthetic intensities', evidence_class='synthetic')
    d.update(changes); return d


def cell(**changes):
    d=dict(cell_id='a', month='2023-01', exposure=1000, eligible=True,
           advantage_fraction=.02, tie_tolerance=1e-12,
           sale=0., other=0., default=0.,
           counts=dict(survive=900, refinancing=100, sale=0, other=0, default=0))
    d.update(changes);return d


def test_dynamic_wait_with_positive_static_savings_is_not_a_refinance_hazard():
    solution=solve_dynamic_refinancing(initial_coupon=.08, market_rates=[.06,.02],
        transition_matrix=[[0,1],[0,1]], remaining_months=120,discount_rate=.04,cost_fraction=.005)
    incentive=bridge().dynamic_incentive(solution,market_state=0)
    assert incentive['advantage_fraction'] < 0
    assert incentive['exercise_now'] is False
    p=bridge().bridge_probabilities(**{k:incentive[k] for k in ('advantage_fraction','tie_tolerance')},
                                    eligible=True,arrival_intensity=.2)
    assert p['refinancing']==0
    next_incentive=bridge().dynamic_incentive(solution,market_state=1,remaining_months=119)
    assert next_incentive['exercise_now'] is True


@pytest.mark.parametrize('advantage,eligible,expected',[(.01,True,.2),(.01,False,0),(-.01,True,0),(1e-12,True,0)])
def test_exact_first_exit_and_eligibility(advantage,eligible,expected):
    p=bridge().bridge_probabilities(advantage_fraction=advantage,eligible=eligible,
                                    arrival_intensity=.2,sale=.03,other=.01,default=.02)
    total=expected+.06
    assert p['refinancing']==pytest.approx(expected/total*(1-math.exp(-total)))
    assert p['survive']==pytest.approx(math.exp(-total))
    assert math.fsum(p.values())==pytest.approx(1)


def test_closed_form_no_competitor_mle_and_holdout_not_read():
    good=cell()
    # Only month is inspected on a held-out row; every outcome may be malformed.
    bad=dict(month='2024-01',counts='not a label',exposure=-900)
    fit=bridge().fit_exercise_rate([good,bad],training_end='2023-12',contract=contract())
    assert fit['arrival_intensity']==pytest.approx(-math.log(.9),rel=1e-7)
    assert fit['training_exposure']==1000
    assert fit['status']=='finite'
    assert fit['ignored_future_cells']==1
    assert fit['training_sha256']==bridge().fit_exercise_rate([good],training_end='2023-12',contract=contract())['training_sha256']


@pytest.mark.parametrize('change',[
    {'complete_first_exit_labels':False}, {'comparable_outstanding_risk_set':False},
    {'refinancing_scope':'all payoffs'}, {'label_provenance':''}, {'evidence_class':'unknown'}])
def test_label_contract_cannot_promote_unlabeled_payoffs(change):
    with pytest.raises(ValueError):
        bridge().fit_exercise_rate([cell()],training_end='2023-12',contract=contract(**change))


@pytest.mark.parametrize('change',[
    {'counts':dict(survive=899,refinancing=100,sale=0,other=0,default=0)},
    {'counts':dict(survive=900,refinancing=100,unknown_payoff=0,sale=0,other=0,default=0)},
    {'counts':dict(survive=900.5,refinancing=99.5,sale=0,other=0,default=0)},
    {'eligible':.75}, {'sale':-1}, {'advantage_fraction':np.nan}, {'month':'2023-13'},
])
def test_invalid_risk_cells_rejected(change):
    with pytest.raises(ValueError):
        bridge().fit_exercise_rate([cell(**change)],training_end='2023-12',contract=contract())


def test_duplicate_cells_and_unsupported_refinance_rejected():
    for rows in [[cell(),cell()],[cell(eligible=False)],[cell(advantage_fraction=-.1)]]:
        with pytest.raises(ValueError):
            bridge().fit_exercise_rate(rows,training_end='2023-12',contract=contract())


def test_no_exposure_zero_events_and_upper_boundary_are_distinct():
    counts=dict(survive=1000,refinancing=0,sale=0,other=0,default=0)
    none=bridge().fit_exercise_rate([cell(eligible=False,counts=counts)],training_end='2023-12',contract=contract())
    assert none['status']=='not_identified' and none['arrival_intensity'] is None
    zero=bridge().fit_exercise_rate([cell(counts=counts)],training_end='2023-12',contract=contract())
    assert zero['status']=='zero_boundary' and zero['arrival_intensity']==0
    infinite=bridge().fit_exercise_rate([cell(counts=dict(survive=0,refinancing=1000,sale=0,other=0,default=0))],training_end='2023-12',contract=contract())
    assert infinite['status']=='upper_boundary' and infinite['arrival_intensity'] is None


def test_competing_risk_mle_matches_independent_grid():
    row=cell(sale=.03,other=.01,default=.02,
             counts=dict(survive=800,refinancing=150,sale=25,other=10,default=15))
    fit=bridge().fit_exercise_rate([row],training_end='2023-12',contract=contract())
    def nll(alpha):
        total=alpha+.06
        scale=(1-math.exp(-total))/total
        return -(800*(-total)+150*math.log(alpha*scale)+25*math.log(.03*scale)
                 +10*math.log(.01*scale)+15*math.log(.02*scale))
    best=min(np.linspace(.14,.21,7001),key=nll)
    assert fit['arrival_intensity']==pytest.approx(best,abs=1.1e-5)
    assert fit['negative_log_likelihood']==pytest.approx(nll(fit['arrival_intensity']),rel=1e-10)


def test_heldout_zero_probability_events_are_reported_not_dropped():
    fit=bridge().fit_exercise_rate([cell()],training_end='2023-12',contract=contract())
    score=bridge().evaluate_exercise_rate([cell(month='2024-01',eligible=False)],fit=fit,contract=contract())
    assert score['exposure']==1000 and score['incompatible_event_count']==100
    assert score['mean_negative_log_likelihood'] is None
    assert score['status']=='incompatible_events'
    with pytest.raises(ValueError):
        bridge().evaluate_exercise_rate([cell()],fit=fit,contract=contract())


@pytest.mark.parametrize('change',[{'eligible':.5},{'arrival_intensity':np.inf},{'tie_tolerance':-1},{'advantage_fraction':np.nan}])
def test_probability_inputs_fail_closed(change):
    kwargs=dict(advantage_fraction=.01,eligible=True,arrival_intensity=.1);kwargs.update(change)
    with pytest.raises(ValueError):bridge().bridge_probabilities(**kwargs)


def test_survival_underflow_is_not_a_structurally_impossible_event():
    fit=bridge().fit_exercise_rate([cell()],training_end='2023-12',contract=contract())
    row=cell(month='2024-01',sale=1000.,counts=dict(survive=1,refinancing=0,sale=999,other=0,default=0))
    score=bridge().evaluate_exercise_rate([row],fit=fit,contract=contract())
    alpha=fit['arrival_intensity']; total=1000+alpha
    expected=(total-999*(math.log(1000)-math.log(total)))/1000
    assert score['status']=='scored'
    assert score['incompatible_event_count']==0
    assert score['mean_negative_log_likelihood']==pytest.approx(expected)


def test_tiny_positive_cause_intensity_keeps_finite_log_support():
    fit=bridge().fit_exercise_rate([cell()],training_end='2023-12',contract=contract())
    row=cell(month='2024-01',sale=np.nextafter(0.,1.),default=1000.,
             counts=dict(survive=0,refinancing=0,sale=1,other=0,default=999))
    score=bridge().evaluate_exercise_rate([row],fit=fit,contract=contract())
    assert score['status']=='scored'
    assert math.isfinite(score['mean_negative_log_likelihood'])


@pytest.mark.parametrize('retained_name',['synthetic-risk-cells.json','data-readiness.json','demonstration-receipt.json'])
def test_demo_never_overwrites_a_partial_prior_attempt(tmp_path,retained_name):
    from tools.run_refinancing_bridge_demo import run
    output=tmp_path/'prior-attempt';output.mkdir()
    retained=output/retained_name;retained.write_text('preserve exact bytes')
    with pytest.raises(FileExistsError):
        run(output)
    assert retained.read_text()=='preserve exact bytes'
