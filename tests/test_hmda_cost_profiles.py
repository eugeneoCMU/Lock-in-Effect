"""Cost distributions must preserve zero/missing disclosures and denominators."""
import csv
import importlib
from decimal import Decimal
from pathlib import Path
import pytest

def api():
    try:
        return importlib.import_module('hazard.hmda_cost_profiles')
    except ModuleNotFoundError:
        pytest.fail('The reusable HMDA cost-profile workflow is not implemented')

def row(**changes):
    result=dict(activity_year='2023',state_code='PA',county_code='42003',
        loan_type='1',lien_status='1',reverse_mortgage='2',
        **{'open-end_line_of_credit':'2'},conforming_loan_limit='C',
        construction_method='1',total_units='1',occupancy_type='1',
        action_taken='1',loan_purpose='31',loan_amount='1000',
        total_loan_costs='100',interest_rate='6',discount_points='',lender_credits='',lei='L1')
    result.update(changes)
    return result

def test_zero_missing_and_joint_disclosures_are_kept_separate():
    rows=[row(total_loan_costs=x) for x in ('0','100','300','NA','','Exempt')]
    rows.append(row(action_taken='3',total_loan_costs='NA'))
    p=api().build_profiles(rows,expected_year=2023,expected_state='PA')
    s=p['conforming_sitebuilt_principal_residence']['overall_originations']
    assert p['raw_application_records']==7
    assert s['originated_records']==6 and s['numeric_loan_cost_records']==3
    assert s['cost_missing_by_code']=={'not_applicable_or_unavailable':1,'blank':1,'exempt':1}
    assert s['dollar_cost_quantiles']=={'p25':50.,'p50':100.,'p75':200.}
    assert s['new_principal_cost_ratio_percent_quantiles']=={'p25':5.,'p50':10.,'p75':20.}
    assert s['reported_zero_cost_records']==1 and s['numeric_points_among_known_cost']==0
    assert s['joint_numeric_rate_and_cost_records']==3

def test_purpose_amount_and_missing_principal_partitions():
    p=api().build_profiles([row(loan_amount='100000'),row(loan_amount='100001',loan_purpose='32'),row(loan_amount='NA')],expected_year=2023,expected_state='PA')
    view=p['base'];s=view['overall_originations']
    assert s['missing_or_nonpositive_new_principal_among_known_cost']==1
    assert s['fee_new_rounded_principal_pair_records']==2
    assert view['originations_with_unclassified_amount']==1
    bins=view['by_purpose_and_new_amount']
    assert sum(g['originated_records'] for g in bins)==2
    assert next(g for g in bins if g['purpose_code']=='31' and g['new_public_loan_amount_bin_usd']=='<=100000')['originated_records']==1
    assert next(g for g in bins if g['purpose_code']=='32' and g['new_public_loan_amount_bin_usd']=='(100000,200000]')['originated_records']==1

@pytest.mark.parametrize('change',[{'activity_year':'2022'},{'state_code':'OH'},{'loan_purpose':'1'},{'action_taken':'6'},{'total_loan_costs':'nan'},{'total_loan_costs':'-1'},{'interest_rate':'Infinity'},{'loan_amount':'oops'}])
def test_wrong_query_scope_and_invalid_numerics_fail_closed(change):
    with pytest.raises(ValueError):api().build_profiles([row(**change)],expected_year=2023,expected_state='PA')

def test_complete_csv_reconciles_every_official_cell_and_sum(tmp_path):
    rows=[row(),row(action_taken='3',loan_purpose='32',loan_amount='2000')]
    source=tmp_path/'source.csv'
    with source.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    aggregation={'aggregations':[{'actions_taken':'1','loan_purposes':'31','count':1,'sum':1000},{'actions_taken':'3','loan_purposes':'32','count':1,'sum':2000}]}
    p=api().profile_csv(source,expected_year=2023,expected_state='PA',aggregation=aggregation)
    assert p['source_validation']['all_query_cells_match'] is True
    aggregation['aggregations'][1]['sum']=1999
    with pytest.raises(ValueError,match='aggregation'):api().profile_csv(source,expected_year=2023,expected_state='PA',aggregation=aggregation)

def test_malformed_csv_and_duplicate_aggregation_are_rejected(tmp_path):
    source=tmp_path/'bad.csv';source.write_text('activity_year,activity_year\n2023,2023\n')
    with pytest.raises(ValueError):api().profile_csv(source,expected_year=2023,expected_state='PA',aggregation={'aggregations':[]})

def test_frozen_source_schema_detects_a_projection(tmp_path):
    source=tmp_path/'projection.csv';r=row()
    with source.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(r));w.writeheader();w.writerow(r)
    aggregation={'aggregations':[{'actions_taken':'1','loan_purposes':'31','count':1,'sum':1000}]}
    with pytest.raises(ValueError,match='schema'):
        api().profile_csv(source,expected_year=2023,expected_state='PA',aggregation=aggregation,expected_header=list(r)+['unneeded_source_column'])

def test_sealed_county_quantile_regression():
    import json
    root=Path(__file__).resolve().parents[1]/'output/refinancing-pilot/2026-10-15'
    source=root/'missing-information-attempt-001/hmda-2023-allegheny-refinance.csv'
    if not source.exists():pytest.skip('Local sealed county fixture unavailable')
    old=json.loads((root/'cost-grounding-attempt-001/cost-profiles.json').read_text())
    with source.open(newline='') as f:rows=list(csv.DictReader(f))
    new=api().build_profiles(rows,expected_year=2023,expected_state='PA')
    for name in ('base','conforming_sitebuilt_principal_residence'):
        assert new[name]['all_application_records']==old[name]['all_application_records']
        assert new[name]['application_outcomes']==old[name]['application_outcomes']
        for group in ('overall_originations','by_purpose','by_purpose_and_new_amount'):
            left=new[name][group];right=old[name][group]
            for a,b in zip(left if isinstance(left,list) else [left],right if isinstance(right,list) else [right]):
                for key,value in b.items():assert a[key]==value,(name,group,key)
