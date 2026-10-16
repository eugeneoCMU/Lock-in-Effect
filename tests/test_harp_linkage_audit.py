"""Selected-program linkage checks; unknown payoffs never become sale labels."""
import importlib
import io
import pytest

pytestmark=pytest.mark.filterwarnings('error')


def model():return importlib.import_module('hazard.harp_linkage_audit')


def primary(**changes):
    d=dict(loan_id='000000000001',reporting_month='2012-04',zero_balance_code='01',
           zero_balance_month='2012-04',prior_balance=100000.,prior_remaining_months=280)
    d.update(changes);return d


def successor(**changes):
    d=dict(loan_id='000000000101',origination_month='2012-04',original_balance=100000.,original_term_months=280)
    d.update(changes);return d


def mapping(**changes):
    d=dict(original_loan_id='000000000001',successor_loan_id='000000000101')
    d.update(changes);return d


def audit(p=None,m=None,s=None):
    return model().audit_linked_refinances([primary()] if p is None else p,
        [mapping()] if m is None else m,[successor()] if s is None else s,
        balance_tolerance=0.,term_tolerance_months=0,selection_definition='synthetic opening cohort selected before outcomes')


def test_linked_harp_positive_and_matching_terms_do_not_make_complete_risk_set():
    d=audit();r=d['loan_audit'][0]
    assert r['event_label']=='linked_harp_payoff'
    assert r['observed_balance_term_match'] is True
    assert d['ready_for_general_refinancing_fit'] is False
    assert d['eligibility_inferred'] is False
    assert d['counts']['linked_harp_payoff']==1
    assert r['transaction_cost'] is None


def test_unmapped_voluntary_payoff_is_unknown_not_sale():
    d=audit(m=[]);r=d['loan_audit'][0]
    assert r['event_label']=='unmapped_payoff_or_maturity'
    assert r['refinancing_known'] is None
    assert 'sale' not in d['counts']


def test_survivors_are_included_without_inferred_eligibility():
    d=audit(p=[primary(zero_balance_code='',zero_balance_month='')],m=[],s=[])
    assert d['counts']['observed_nonterminal']==1
    assert d['loan_audit'][0]['harp_eligible'] is None


def test_unobserved_successor_and_conflicting_dates_visible():
    assert audit(s=[])['counts']['linked_payoff_successor_unobserved']==1
    assert audit(s=[successor(origination_month='2012-05')])['counts']['linked_date_conflict']==1
    assert audit(p=[primary(zero_balance_code='',zero_balance_month='')])['counts']['linked_original_not_paid_off']==1


def test_different_balance_or_term_not_closing_cost_estimate():
    r=audit(s=[successor(original_balance=102000.,original_term_months=360)])['loan_audit'][0]
    assert r['balance_change']==2000
    assert r['term_change_months']==80
    assert r['observed_balance_term_match'] is False
    assert r['transaction_cost'] is None
    missing=audit(p=[primary(prior_balance=None)])['loan_audit'][0]
    assert missing['observed_balance_term_match'] is None


@pytest.mark.parametrize('links',[
    [mapping(),mapping()],
    [mapping(),mapping(original_loan_id='000000000002')],
    [mapping(successor_loan_id='000000000001')],
    [mapping(),mapping(original_loan_id='000000000101',successor_loan_id='000000000201')],
])
def test_duplicate_colliding_and_chained_links_rejected(links):
    with pytest.raises(ValueError):audit(m=links)


@pytest.mark.parametrize('changes',[
    dict(loan_id=1),dict(zero_balance_code='99'),dict(zero_balance_month='2012-13'),
    dict(zero_balance_month='2012-05'),dict(zero_balance_code='',zero_balance_month='2012-04'),
    dict(prior_balance=-1),dict(prior_remaining_months=.5),
])
def test_invalid_original_summary_rejected(changes):
    with pytest.raises(ValueError):audit(p=[primary(**changes)])


def test_outside_pilot_mapping_is_counted_without_creating_exposure():
    d=audit(m=[mapping(),mapping(original_loan_id='000000000002',successor_loan_id='000000000102')])
    assert d['mapping_outside_primary_pilot']==1 and d['primary_loans']==1


def test_mapping_orientation_and_width_are_explicit_and_leading_zeros_survive():
    rows=list(model().read_mapping(io.StringIO('successor|original\n000000000101|000000000001\n'),
        original_column=1,successor_column=0,field_count=2,header=True))
    assert rows==[mapping()]
    with pytest.raises(ValueError):
        list(model().read_mapping(io.StringIO('000000000001|000000000101|extra\n'),
            original_column=0,successor_column=1,field_count=2,header=False))


def test_no_selection_definition_and_duplicate_primary_are_rejected():
    with pytest.raises(ValueError):
        model().audit_linked_refinances([primary()],[mapping()],[successor()],balance_tolerance=0.,
             term_tolerance_months=0,selection_definition='')
    with pytest.raises(ValueError):audit(p=[primary(),primary()])


def test_local_runner_preserves_prior_outputs_and_records_input_hash(tmp_path):
    import hashlib,json
    source=tmp_path/'pilot.json'
    source.write_text(json.dumps(dict(primary=[primary()],mapping=[mapping()],successors=[successor()],
        selection_definition='synthetic pre-event pilot',balance_tolerance=0.,term_tolerance_months=0,
        evidence_class='synthetic',mapping_provenance='synthetic links',primary_provenance='synthetic originals',
        successor_provenance='synthetic successors')))
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    output=tmp_path/'out'
    result=model().run_local_pilot(source,output)
    assert result['counts']['linked_harp_payoff']==1
    assert result['ready_for_general_refinancing_fit'] is False
    receipt=json.loads((output/'receipt.json').read_text())
    assert receipt['input_sha256_before']==before==receipt['input_sha256_after']
    with pytest.raises(FileExistsError):model().run_local_pilot(source,output)


@pytest.mark.parametrize('link',[
    mapping(original_loan_id='000000000101',successor_loan_id='000000000001'),
    mapping(original_loan_id='000000000101',successor_loan_id='000000000201'),
])
def test_mapping_roles_must_agree_with_normalized_summary_roles(link):
    with pytest.raises(ValueError):audit(m=[link])


def stock_row(**changes):
    d=dict(loan_id='000000000001',reporting_month='2009-03',current_upb=100000.,
           original_term_months=360,amortization_type='FRM',zero_balance_code='',delinquency_status='99')
    d.update(changes);return d


def test_stock_selection_ignores_future_outcomes_and_input_order():
    import hashlib
    rows=[stock_row(loan_id=f'{i:012}') for i in range(1,5)]
    poisoned=dict(reporting_month='2012-04',loan_id=None,current_upb='bad',zero_balance_code='01')
    a=model().select_opening_stock(rows+[poisoned],sample_size=2)
    b=model().select_opening_stock(list(reversed(rows)),sample_size=2)
    expected=sorted([r['loan_id'] for r in rows],key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:2]
    assert a['selected_loan_ids']==b['selected_loan_ids']==expected
    assert a['selection_sha256']==b['selection_sha256']
    assert a['opening_stock_loans']==4 and a['eligibility_inferred'] is False


def test_stock_selection_retains_delinquency_and_does_not_fill_missing_balances():
    rows=[stock_row(),stock_row(loan_id='000000000002',current_upb=None),
          stock_row(loan_id='000000000003',zero_balance_code='01',current_upb=0),
          stock_row(loan_id='000000000004',original_term_months=300),
          stock_row(loan_id='000000000005',amortization_type='ARM')]
    d=model().select_opening_stock(rows,sample_size=1000)
    assert d['selected_loan_ids']==['000000000001']
    assert d['missing_balance_loans']==1
    assert d['opening_stock_loans']==1


def test_stock_selection_rejects_duplicate_snapshot_and_invalid_sample_size():
    with pytest.raises(ValueError):model().select_opening_stock([stock_row(),stock_row()])
    with pytest.raises(ValueError):model().select_opening_stock([stock_row()],sample_size=0)
