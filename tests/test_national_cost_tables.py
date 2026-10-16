"""Grouped distributions must preserve costs, denominators and missing geography."""
import csv
import importlib
from pathlib import Path
import pytest
from hazard.hmda_cost_profiles import REQUIRED
from hazard.national_hmda import ingest_snapshot


def api():
    try:return importlib.import_module('hazard.national_cost_tables')
    except ModuleNotFoundError:pytest.fail('Grouped national cost tables are missing')


def row(**changes):
    r=dict(zip(REQUIRED,['2023','PA','42003','1','1','2','2','C','1','1','1','1','31','100000','100','6','','','L1']))
    r.update(changes);return r


def snapshot(tmp_path,rows):
    p=tmp_path/'source.csv'
    with p.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=REQUIRED);writer.writeheader();writer.writerows(rows)
    dest=tmp_path/'snapshot'
    ingest_snapshot(p,dest,year=2023,source_url='synthetic fixture',publication_version='test',batch_rows=2,reserve_bytes=0)
    return dest


def test_national_state_purpose_bins_preserve_missing_and_literal_quantiles(tmp_path):
    rows=[row(total_loan_costs=x) for x in ('0','100','300','NA','','Exempt')]
    rows += [row(state_code='PR',loan_purpose='32',loan_amount='200000',total_loan_costs='400',discount_points='0',lender_credits='15'),row(state_code='',total_loan_costs='500'),row(loan_type='2'),row(action_taken='3'),row(loan_purpose='1')]
    result=api().build_cost_tables(snapshot(tmp_path,rows),reserve_bytes=0)
    assert result['denominators']=={'raw_snapshot_application_records':11,'all_refinance_originations':9,'narrower_refinance_originations':8,'refinance_originations_outside_narrower':1}
    groups=result['groups']
    national=next(g for g in groups if g['level']=='national')
    assert national['originated_records']==8 and national['numeric_loan_cost_records']==5
    assert national['cost_missing_by_code']=={'blank':1,'not_applicable_or_unavailable':1,'exempt':1}
    assert national['reported_zero_cost_records']==1
    assert national['new_principal_cost_ratio_percent_quantiles']=={'p25':.1,'p50':.2,'p75':.3}
    pa=next(g for g in groups if g['level']=='state' and g['state_code']=='PA')
    assert pa['originated_records']==6 and pa['dollar_cost_quantiles']=={'p25':50.,'p50':100.,'p75':200.}
    missing=next(g for g in groups if g['level']=='state' and g['state_code']=='')
    assert missing['state_status']=='missing_state' and missing['originated_records']==1
    pr=next(g for g in groups if g['level']=='state_purpose_amount' and g['state_code']=='PR')
    assert pr['purpose_code']=='32' and pr['new_public_loan_amount_bin_usd']=='(100000,200000]'
    assert pr['numeric_points_among_known_cost']==1 and pr['numeric_lender_credits_among_known_cost']==1
    assert sum(g['originated_records'] for g in groups if g['level']=='state')==8
    assert sum(g['originated_records'] for g in groups if g['level']=='state_purpose_amount')==8
    assert result['behavioral_parameters_fitted']==0


def test_unknown_amount_partition_and_raw_integrity_guard(tmp_path):
    p=snapshot(tmp_path,[row(loan_amount='NA'),row(loan_amount='0')])
    result=api().build_cost_tables(p,reserve_bytes=0)
    n=next(g for g in result['groups'] if g['level']=='national')
    assert n['numeric_loan_cost_records']==2 and n['fee_new_rounded_principal_pair_records']==0
    assert n['new_principal_cost_ratio_percent_quantiles'] is None
    assert any(g['new_public_loan_amount_bin_usd']=='unclassified_amount' for g in result['groups'])
    next(p.glob('part-*.parquet')).write_bytes(b'changed')
    with pytest.raises(ValueError,match='integrity'):api().build_cost_tables(p,reserve_bytes=0)


def test_holdout_gate_and_invalid_numeric_fail_closed(tmp_path):
    p=snapshot(tmp_path,[row(total_loan_costs='nan')])
    with pytest.raises(ValueError,match='numeric'):api().build_cost_tables(p,reserve_bytes=0)
    import json
    manifest=p/'manifest.json';m=json.loads(manifest.read_text());m['year']=2024;manifest.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='freeze'):api().build_cost_tables(p,reserve_bytes=0)


def test_valid_scientific_numeric_disclosures_are_not_discarded_or_imputed(tmp_path):
    p=snapshot(tmp_path,[row(discount_points='4.8E-4',lender_credits='2E1',total_loan_costs='3E2',loan_amount='1E5',interest_rate='6E0')])
    result=api().build_cost_tables(p,reserve_bytes=0)
    n=next(g for g in result['groups'] if g['level']=='national')
    assert n['originated_records']==1 and n['numeric_loan_cost_records']==1
    assert n['numeric_points_among_known_cost']==1 and n['numeric_lender_credits_among_known_cost']==1
    assert n['dollar_cost_quantiles']=={'p25':300.,'p50':300.,'p75':300.}
    assert n['new_principal_cost_ratio_percent_quantiles']=={'p25':.3,'p50':.3,'p75':.3}


@pytest.mark.parametrize('disclosure',['NaN','-1E-3','1E26'])
def test_nonfinite_negative_or_unsupported_scientific_precision_fails_closed(tmp_path,disclosure):
    p=snapshot(tmp_path,[row(discount_points=disclosure)])
    with pytest.raises(ValueError,match='numeric'):api().build_cost_tables(p,reserve_bytes=0)


@pytest.mark.parametrize('state_code',['','NA','Exempt'])
def test_each_missing_state_code_is_labelled_missing_without_altering_literal(tmp_path,state_code):
    p=snapshot(tmp_path,[row(state_code=state_code),row(state_code='PR')])
    result=api().build_cost_tables(p,reserve_bytes=0)
    unknown=next(g for g in result['groups'] if g['level']=='state' and g['state_code']==state_code)
    assert unknown['state_status']=='missing_state' and unknown['originated_records']==1
    assert next(g for g in result['groups'] if g['level']=='state' and g['state_code']=='PR')['state_status']=='reported_state'
    assert next(g for g in result['groups'] if g['level']=='national')['originated_records']==2

def test_long_decimal_points_availability_preserves_cost_statistics(tmp_path):
    p=snapshot(tmp_path,[row(discount_points='0.011800000000000001')])
    n=next(g for g in api().build_cost_tables(p,reserve_bytes=0)['groups'] if g['level']=='national')
    assert n['numeric_points_among_known_cost']==1
    assert n['dollar_cost_quantiles']['p50']==100.


def test_cost_precision_remains_strict(tmp_path):
    p=snapshot(tmp_path,[row(total_loan_costs="1E-13")])
    with pytest.raises(ValueError,match="numeric"):api().build_cost_tables(p,reserve_bytes=0)
