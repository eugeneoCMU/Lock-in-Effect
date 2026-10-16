"""Frozen cost cutoffs are transported to held-out costs without refitting."""
import csv
import hashlib
import importlib
import json
from pathlib import Path
import pytest
from hazard.hmda_cost_profiles import REQUIRED
from hazard.national_hmda import ingest_snapshot


def api():
    try:return importlib.import_module('hazard.national_cost_evaluation')
    except ModuleNotFoundError:pytest.fail('National held-out cost evaluation is missing')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n');return path


@pytest.fixture
def evaluation(tmp_path):
    frozen=dump(tmp_path/'frozen.json',dict(status='frozen_national_conditional_cost_scenarios',evidence_class='conditional_cost_scenario',development_years=list(range(2018,2024)),validation_year=2024,final_evaluation_year=2025,protocol_sha256='a'*64,scenario_count=252,model_parameters_changed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0,frozen_cutoffs={str(year):{'31':{'p25':.001,'p50':.002,'p75':.003},'32':{'p25':0.,'p50':.002,'p75':.004}} for year in range(2018,2024)}))
    gate=dump(tmp_path/'gate.json',dict(development_years=list(range(2018,2024)),validation_year=2024,final_evaluation_year=2025,frozen_artifact=frozen.name,frozen_sha256=digest(frozen),allowed_years=[2024],protocol_sha256='a'*64))
    rows=[]
    for purpose,cost,state in [('31','100','PA'),('31','200','PA'),('31','200',''),('31','300','PR'),('31','NA','PA'),('32','0','PR'),('32','400','PA'),('32','100','PA')]:
        rows.append(dict(zip(REQUIRED,['2024',state,'42003','1','1','2','2','C','1','1','1','1',purpose,'100000',cost,'6','','','L1'])))
    rows.append(dict(rows[0],loan_amount='NA',total_loan_costs='10'))
    source=tmp_path/'source.csv'
    with source.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=REQUIRED);writer.writeheader();writer.writerows(rows)
    snap=tmp_path/'snapshot';ingest_snapshot(source,snap,year=2024,source_url='synthetic fixture',publication_version='synthetic',freeze_gate=gate,reserve_bytes=0,batch_rows=2)
    return snap,frozen,gate


def test_inclusive_ties_and_closed_band_use_frozen_cutoffs_for_each_year_purpose(evaluation):
    snap,frozen,gate=evaluation
    result=api().compare_national_costs(snap,frozen,gate,reserve_bytes=0)
    assert result['evaluation_year']==2024 and len(result['comparisons'])==12
    g=next(g for g in result['comparisons'] if g['development_year']==2018 and g['purpose_code']=='31')
    assert g['held_out_cost_principal_pair_records']==4
    assert g['counts_at_or_below_frozen_cutoffs']=={'p25':1,'p50':3,'p75':4}
    assert g['shares_at_or_below_frozen_cutoffs']=={'p25':.25,'p50':.75,'p75':1.}
    assert g['closed_p25_p75_band_records']==4 and g['closed_p25_p75_band_share']==1
    sample=next(g for g in result['held_out_purpose_summaries'] if g['purpose_code']=='31')
    assert sample['originated_records']==6 and sample['numeric_loan_cost_records']==5
    assert sample['cost_missing_by_code']=={'not_applicable_or_unavailable':1}
    assert sample['missing_or_nonpositive_new_principal_among_known_cost']==1
    assert sample['new_principal_cost_ratio_percent_quantiles']=={'p25':.175,'p50':.2,'p75':.225}
    other=next(g for g in result['held_out_purpose_summaries'] if g['purpose_code']=='32')
    assert other['reported_zero_cost_records']==1
    assert result['behavioral_parameters_fitted']==result['new_portfolio_estimates']==0


@pytest.mark.parametrize('mutation',['frozen_changed','other_frozen','gate_missing','wrong_year','bad_part','bad_cutoffs','2025_no_validation'])
def test_hash_and_holdout_mutations_fail_closed(evaluation,mutation,tmp_path):
    snap,frozen,gate=evaluation
    if mutation=='frozen_changed':frozen.write_text(frozen.read_text()+' ')
    if mutation=='other_frozen':frozen=dump(tmp_path/'different.json',json.loads(frozen.read_text())|{'protocol_sha256':'b'*64})
    if mutation=='gate_missing':gate=None
    if mutation=='wrong_year':
        p=snap/'manifest.json';m=json.loads(p.read_text());m['year']=2023;dump(p,m)
    if mutation=='bad_part':next(snap.glob('part-*.parquet')).write_bytes(b'corrupt')
    if mutation=='bad_cutoffs':
        f=json.loads(frozen.read_text());f['frozen_cutoffs']['2018']['31']['p25']=-1;dump(frozen,f);g=json.loads(gate.read_text());g['frozen_sha256']=digest(frozen);dump(gate,g)
    if mutation=='2025_no_validation':
        p=snap/'manifest.json';m=json.loads(p.read_text());m['year']=2025;dump(p,m);g=json.loads(gate.read_text());g['allowed_years']=[2025];dump(gate,g)
    with pytest.raises(ValueError):api().compare_national_costs(snap,frozen,gate,reserve_bytes=0)


def test_all_missing_costs_keep_explicit_null_shares_and_unknown_geography(evaluation,tmp_path):
    snap,frozen,gate=evaluation
    with (tmp_path/'source.csv').open(newline='') as f:rows=list(csv.DictReader(f))
    rows=[dict(r,total_loan_costs='NA',state_code='') for r in rows if r['loan_purpose']=='31']
    source=tmp_path/'missing.csv'
    with source.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=REQUIRED);writer.writeheader();writer.writerows(rows)
    missing=tmp_path/'missing-snapshot';ingest_snapshot(source,missing,year=2024,source_url='synthetic missing sample',publication_version='synthetic',freeze_gate=gate,reserve_bytes=0)
    result=api().compare_national_costs(missing,frozen,gate,reserve_bytes=0)
    assert result['denominators']['narrower_originations_missing_state']==6
    assert all(g['held_out_cost_principal_pair_records']==0 and g['closed_p25_p75_band_share'] is None and g['shares_at_or_below_frozen_cutoffs']=={'p25':None,'p50':None,'p75':None} for g in result['comparisons'])
    assert all(g['new_principal_cost_ratio_percent_quantiles'] is None for g in result['held_out_purpose_summaries'])
    assert next(g for g in result['held_out_purpose_summaries'] if g['purpose_code']=='32')['originated_records']==0


def test_synthetic_2025_requires_and_records_unchanged_validation_hash(evaluation,tmp_path):
    snap,frozen,gate=evaluation
    validation=dump(tmp_path/'validation.json',{'status':'synthetic accepted cost comparison'})
    g=json.loads(gate.read_text());g.update(allowed_years=[2025],validation_artifact=validation.name,validation_sha256=digest(validation));final_gate=dump(tmp_path/'final-gate.json',g)
    with (tmp_path/'source.csv').open(newline='') as f:rows=[dict(r,activity_year='2025') for r in csv.DictReader(f)]
    source=tmp_path/'synthetic-2025.csv'
    with source.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=REQUIRED);writer.writeheader();writer.writerows(rows)
    final=tmp_path/'synthetic-final';ingest_snapshot(source,final,year=2025,source_url='synthetic test only',publication_version='synthetic',freeze_gate=final_gate,reserve_bytes=0)
    result=api().compare_national_costs(final,frozen,final_gate,reserve_bytes=0)
    assert result['evaluation_year']==2025 and result['validation_artifact_sha256']==digest(validation)
    validation.write_text('changed')
    with pytest.raises(ValueError,match='validation'):api().compare_national_costs(final,frozen,final_gate,reserve_bytes=0)


def test_manifest_split_must_match_evaluation_year(evaluation):
    snap,frozen,gate=evaluation
    path=snap/'manifest.json';m=json.loads(path.read_text());m['split']='development';dump(path,m)
    with pytest.raises(ValueError,match='split'):api().compare_national_costs(snap,frozen,gate,reserve_bytes=0)


def test_missing_geography_audit_counts_NA_Exempt_and_blank_without_dropping_rows(evaluation,tmp_path):
    snap,frozen,gate=evaluation
    with (tmp_path/'source.csv').open(newline='') as f:template=next(csv.DictReader(f))
    rows=[dict(template,state_code=code) for code in ('','NA','Exempt','PR')]
    source=tmp_path/'missing-geography.csv'
    with source.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=REQUIRED);w.writeheader();w.writerows(rows)
    target=tmp_path/'missing-geography-snapshot';ingest_snapshot(source,target,year=2024,source_url='synthetic',publication_version='test',freeze_gate=gate,reserve_bytes=0)
    result=api().compare_national_costs(target,frozen,gate,reserve_bytes=0)
    assert result['denominators']['narrower_originations_missing_state']==3
    assert result['denominators']['narrower_originations_missing_state_by_code']=={'':1,'NA':1,'Exempt':1}
    assert result['denominators']['narrower_refinance_originations']==4
    assert next(g for g in result['held_out_purpose_summaries'] if g['purpose_code']=='31')['fee_new_rounded_principal_pair_records']==4


def test_actual_qualified_freeze_metadata_survives_heldout_comparison(evaluation,tmp_path):
    from hazard.national_cost_calibration import freeze_national_costs
    from hazard.national_cost_tables import build_cost_tables
    snap,old_frozen,old_gate=evaluation;inputs={}
    with (tmp_path/'source.csv').open(newline='') as f:holdout_rows=list(csv.DictReader(f))
    for year in range(2018,2024):
        folder=tmp_path/f'development-{year}';folder.mkdir();src=folder/'source.csv'
        with src.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=REQUIRED);w.writeheader();w.writerows(dict(r,activity_year=str(year)) for r in holdout_rows)
        target=folder/'snapshot';manifest=ingest_snapshot(src,target,year=year,source_url='synthetic',publication_version='test',reserve_bytes=0)
        table=dump(folder/'tables.json',build_cost_tables(target,reserve_bytes=0));mp=target/'manifest.json'
        acceptance=dict(year=year,status='accepted_source_bound_national_snapshot',raw_records=9,institutions=1,every_TS_institution_count_matches=True,source_sha256=manifest['source_sha256'],manifest_sha256=digest(mp))
        if year==2018:
            allowed=['Descriptive reported-cost distributions conditional on current published public LAR records','Predeclared year/purpose cost scenarios with source-quality qualification','Cost-distribution transport checks with frozen cutoffs']
            policy=dump(folder/'policy.json',dict(status='explicit_cost_only_source_quality_exception_before_2018_cost_inspection',year=2018,permitted_source_sha256=manifest['source_sha256'],published_LAR_records=9,published_TS_sum=11,net_count_discrepancy=-2,remaining_mismatches=1,missing_TS_only_institutions=1,TS_only_record_count=2,other_18_count_net_difference=0,allowed_use=allowed,raw_record_policy='Preserve every published LAR row; no forced TS match.',not_established=['Every institution-declared row appears in public LAR','Behavioral validity or SOMA transport']))
            audit=dump(folder/'audit.json',dict(status='independent_raw_byte_audit_not_TS_acceptance',year=2018,source_sha256=manifest['source_sha256'],source_bytes=manifest['source_bytes'],physical_data_records=9,raw_institutions=1,raw_vs_parquet_all_institution_counts_match=True,raw_vs_parquet_differences=[],completed_ZIP_member_CRC_verified=True,declared_uncompressed_bytes=manifest['uncompressed_bytes'],observed_uncompressed_bytes=manifest['uncompressed_bytes'],TS_sha256='b'*64,TS_count_sum=11,TS_records=2,diagnostic_uppercase_mismatch_count=1,raw_minus_TS_records=-2))
            acceptance.update(status='accepted_published_lar_with_unresolved_ts_discrepancy',every_TS_institution_count_matches=False,official_TS_sum=11,official_TS_sha256='b'*64,raw_minus_TS_records=-2,independent_raw_audit_path=str(audit),independent_raw_audit_sha256=digest(audit),source_quality_policy_path=str(policy),source_quality_policy_sha256=digest(policy),scope='Synthetic source-bound conditional reported-cost use only.')
        inputs[year]={'tables':table,'manifest':mp,'acceptance':dump(folder/'acceptance.json',acceptance)}
    protocol=dump(tmp_path/'qualified-protocol.json',dict(development_years=list(range(2018,2024)),validation_year=2024,final_holdout_year=2025,holdout_data_opened=False))
    out=tmp_path/'qualified-freeze';frozen=freeze_national_costs(inputs,out,protocol_path=protocol)
    qualified_snapshot=tmp_path/'qualified-heldout-snapshot'
    ingest_snapshot(tmp_path/'source.csv',qualified_snapshot,year=2024,source_url='synthetic qualified-gate holdout',publication_version='test',freeze_gate=out/'validation-gate.json',reserve_bytes=0)
    result=api().compare_national_costs(qualified_snapshot,out/'frozen-national-costs.json',out/'validation-gate.json',reserve_bytes=0)
    assert result['source_quality_qualifications']==frozen['source_quality_qualifications']
    assert result['development_source_acceptance']['2018']['every_TS_institution_count_matches'] is False
    assert result['development_source_acceptance']['2018']['source_status']=='accepted_published_lar_with_unresolved_ts_discrepancy'
    assert 'unresolved' in result['interpretation'] and '2018' in result['interpretation']
    assert all(result['development_source_acceptance'][str(y)]['every_TS_institution_count_matches'] is True for y in range(2019,2024))
    assert result['behavioral_parameters_fitted']==0


def test_retroactive_self_consistent_replacement_freeze_cannot_reuse_read_snapshot(evaluation,tmp_path):
    snap,frozen,gate=evaluation
    replacement=json.loads(frozen.read_text());replacement['frozen_cutoffs']['2018']['31']['p50']=.0021
    new_frozen=dump(tmp_path/'later-freeze.json',replacement)
    new_gate_value=json.loads(gate.read_text());new_gate_value.update(frozen_artifact=new_frozen.name,frozen_sha256=digest(new_frozen))
    new_gate=dump(tmp_path/'later-gate.json',new_gate_value)
    with pytest.raises(ValueError,match='ingestion.*freeze'):
        api().compare_national_costs(snap,new_frozen,new_gate,reserve_bytes=0)


def test_changed_gate_file_cannot_reuse_snapshot_even_with_same_frozen_costs(evaluation,tmp_path):
    snap,frozen,gate=evaluation
    changed=json.loads(gate.read_text());changed['note']='later replacement gate with same frozen artifact'
    later_gate=dump(tmp_path/'changed-gate.json',changed)
    with pytest.raises(ValueError,match='ingestion.*gate'):
        api().compare_national_costs(snap,frozen,later_gate,reserve_bytes=0)


def test_missing_ingestion_gate_receipt_fails_closed(evaluation):
    snap,frozen,gate=evaluation
    path=snap/'manifest.json';m=json.loads(path.read_text());m.pop('freeze_gate');dump(path,m)
    with pytest.raises(ValueError,match='ingestion.*gate'):
        api().compare_national_costs(snap,frozen,gate,reserve_bytes=0)

@pytest.mark.parametrize('bad_protocol',[False,True])
def test_final_gate_can_bind_protocol_through_hash_verified_validation(evaluation,tmp_path,bad_protocol):
    _,frozen,gate=evaluation
    validation=dump(tmp_path/'complete-validation.json',dict(status='held_out_national_cost_distribution_comparison',evaluation_year=2024,frozen_costs_sha256=digest(frozen),protocol_sha256=('b' if bad_protocol else 'a')*64))
    g=json.loads(gate.read_text());g.pop('protocol_sha256');g.update(allowed_years=[2025],validation_artifact=validation.name,validation_sha256=digest(validation));final=dump(tmp_path/'final-with-validation.json',g)
    if bad_protocol:
        with pytest.raises(ValueError,match='protocol'):api()._frozen(frozen,final,2025)
    else:
        f,receipt,_=api()._frozen(frozen,final,2025)
        assert f['protocol_sha256']=='a'*64
        assert receipt['protocol_sha256']=='a'*64
        assert receipt['protocol_binding']=='hash_verified_2024_validation'
        assert 'protocol_sha256' not in json.loads(final.read_text())
