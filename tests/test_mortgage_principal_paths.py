"""Full-horizon accounting restrictions; supplied scenarios, no fitted hazards."""
import math
import pytest
from hazard.mortgage_principal_paths import principal_path, paired_principal_paths


def test_survivor_mass_scales_second_month_schedule_instead_of_reusing_pool_payment():
    p=principal_path(100,[10,10],[{'sale':math.log(2)}]*2,cash_causes={'sale'})
    assert p.months[0].scheduled_principal==10
    assert p.months[1].scheduled_principal==5
    assert p.months[1].cause_principal['sale']==20
    assert p.ending_balance==20
    assert p.scheduled_principal==15
    assert p.cause_principal=={'sale':65}
    assert p.designated_cash_principal==80
    assert p.unclassified_removal_principal==0


def test_paired_path_accounts_for_different_scheduled_principal_after_exits():
    p=paired_principal_paths(100,[10,10],[{'sale':math.log(2)}]*2,[{'sale':0}]*2,cash_causes={'sale'})
    assert p.scheduled_difference==-5
    assert p.cause_differences=={'sale':65}
    assert p.designated_cash_difference==60
    assert p.ending_balance_difference==-60
    assert p.accounting_residual==pytest.approx(0,abs=1e-12)


def test_full_horizon_collapse_of_causes_reproduces_supplied_combined_intensity():
    n=36;split=[{'refinance':.04,'sale':.03,'other':.01}]*n
    labelled=principal_path(120,[2]*n,split,cash_causes={'refinance','sale','other'})
    collapsed=principal_path(120,[2]*n,[{'combined':.08}]*n,cash_causes={'combined'})
    assert labelled.ending_balance==pytest.approx(48*math.exp(-.08*n))
    assert labelled.ending_balance==pytest.approx(collapsed.ending_balance)
    assert labelled.designated_cash_principal==pytest.approx(collapsed.designated_cash_principal)
    assert labelled.scheduled_principal==pytest.approx(collapsed.scheduled_principal)
    assert sum(labelled.cause_principal.values())==pytest.approx(collapsed.cause_principal['combined'])


def test_credit_and_unknown_removals_are_not_automatically_cash():
    p=principal_path(100,[0],[{'sale':math.log(2)/2,'credit':math.log(2)/4,'unresolved':math.log(2)/4}],cash_causes={'sale'})
    assert p.designated_cash_principal==pytest.approx(25)
    assert p.unclassified_removal_principal==pytest.approx(25)
    assert p.ending_balance==pytest.approx(50)
    assert p.scheduled_principal+sum(p.cause_principal.values())+p.ending_balance==pytest.approx(100)


def test_unchanged_credit_intensity_does_not_imply_unchanged_credit_amount():
    p=paired_principal_paths(100,[2]*12,[{'sale':.2,'credit':.05}]*12,[{'sale':.01,'credit':.05}]*12,cash_causes={'sale'})
    assert p.cause_differences['credit']<0
    assert p.designated_cash_difference!=pytest.approx(sum(p.cause_differences.values())+p.scheduled_difference)
    assert p.accounting_residual==pytest.approx(0,abs=1e-11)


def test_identical_paths_have_zero_differences():
    p=paired_principal_paths(100,[3]*24,[{'sale':.03,'credit':.01}]*24,[{'sale':.03,'credit':.01}]*24,cash_causes={'sale'})
    assert p.designated_cash_difference==p.ending_balance_difference==p.scheduled_difference==0
    assert all(v==0 for v in p.cause_differences.values())


def test_maturity_leaves_no_principal_or_active_mass_and_no_double_count():
    p=principal_path(100,[50,50,0],[{'sale':.1}]*3,cash_causes={'sale'})
    assert p.months[1].ending_balance==0
    assert p.months[1].ending_active_fraction==0
    assert p.months[2].scheduled_principal==0
    assert p.designated_cash_principal==pytest.approx(100)


def test_time_varying_causes_and_cash_mapping_are_explicit():
    p=principal_path(100,[1,1],[{'sale':.1},{'credit':.2}],cash_causes={'sale'})
    assert set(p.cause_principal)=={'sale','credit'}
    assert p.months[0].cause_principal['credit']==0
    assert p.months[1].cause_principal['sale']==0
    assert p.accounting_residual==pytest.approx(0,abs=1e-12)


@pytest.mark.parametrize('value',[True,-1,float('nan'),float('inf'),'100'])
def test_invalid_starting_balance_is_rejected(value):
    with pytest.raises((ValueError,TypeError)):
        principal_path(value,[0],[{'sale':0}],cash_causes={'sale'})


@pytest.mark.parametrize('schedule,paths,cash',[
    ([101],[{'sale':0}],{'sale'}),([50,51],[{'sale':0}]*2,{'sale'}),
    ([10],[{'sale':0}]*2,{'sale'}),([],[],set()),
    ([True],[{'sale':0}],{'sale'}),([0],[{'sale':-1}],{'sale'}),
    ([0],[{}],set()),([0],[{'sale':0}],{'typo'}),([0],[{'sale':0}],'sale'),
    ([100,0],[{'sale':0},{'sale':float('nan')}],{'sale'}),
])
def test_invalid_paths_reject_before_simulation_including_after_maturity(schedule,paths,cash):
    with pytest.raises((ValueError,TypeError)):
        principal_path(100,schedule,paths,cash_causes=cash)


def test_paired_horizons_must_match():
    with pytest.raises(ValueError):
        paired_principal_paths(100,[0],[{'sale':0}],[{'sale':0}]*2,cash_causes={'sale'})


def test_empty_cash_mapping_still_records_scheduled_principal_only():
    p=principal_path(100,[10],[{'unresolved':math.log(2)}],cash_causes=set())
    assert p.designated_cash_principal==10
    assert p.unclassified_removal_principal==45


def test_zero_starting_balance_and_extreme_hazards_are_finite():
    p=principal_path(0,[0,0],[{'x':1e308,'y':1e308}]*2,cash_causes=set())
    assert p.ending_balance==p.designated_cash_principal==p.unclassified_removal_principal==0
    p=principal_path(100,[0,0],[{'x':1e308,'y':1e308}]*2,cash_causes={'x'})
    assert p.designated_cash_principal==50
    assert p.unclassified_removal_principal==50
    assert p.months[1].beginning_balance==0


def test_paired_cash_cause_absent_in_one_leg_is_explicit_zero_not_error():
    p=paired_principal_paths(100,[10],[{'sale':math.log(2)}],[{'credit':math.log(2)}],cash_causes={'sale'})
    assert p.designated_cash_difference==45
    assert p.unclassified_removal_difference==-45
    assert p.ending_balance_difference==0
    assert p.accounting_residual==0


@pytest.mark.parametrize('bad',[[],['sale'],None,True,'sale'])
def test_paired_invalid_month_mapping_fails_with_documented_validation(bad):
    with pytest.raises((ValueError,TypeError)):
        paired_principal_paths(100,[0],[bad],[{'sale':0}],cash_causes=set())


def test_accounting_results_cannot_be_mutated_after_residual_calculation():
    p=paired_principal_paths(100,[10],[{'sale':.1}],[{'sale':.2}],cash_causes={'sale'})
    for mapping in (p.first.months[0].cause_principal,p.first.cause_principal,p.cause_differences):
        with pytest.raises(TypeError):mapping['sale']=999
