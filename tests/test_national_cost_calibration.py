"""National freeze must bind all six accepted development years before holdouts."""
import csv
import hashlib
import importlib
import json
from pathlib import Path
import pytest
from hazard.hmda_cost_profiles import REQUIRED
from hazard.national_cost_tables import build_cost_tables
from hazard.national_hmda import ingest_snapshot, _gate


def api():
    try:return importlib.import_module('hazard.national_cost_calibration')
    except ModuleNotFoundError:pytest.fail('National development cost freeze is missing')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path,value):path.write_text(json.dumps(value,indent=2)+'\n');return path


@pytest.fixture
def panel(tmp_path):
    inputs={}
    for year in range(2018,2024):
        root=tmp_path/str(year);root.mkdir();source=root/'source.csv';rows=[]
        for purpose,cost,state in [('31','0','PA'),('31','100','PA'),('32','200','PR'),('32','400','PR')]:
            cost='0' if year==2018 and purpose=='31' else str(int(cost)*(year-2017))
            rows.append(dict(zip(REQUIRED,[str(year),state,'42003','1','1','2','2','C','1','1','1','1',purpose,'100000',cost,'6','','','L1'])))
        with source.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=REQUIRED);w.writeheader();w.writerows(rows)
        snapshot=root/'snapshot';m=ingest_snapshot(source,snapshot,year=year,source_url=f'https://official.example/{year}_public_lar_csv.zip',publication_version='synthetic accepted fixture',reserve_bytes=0)
        tables=dump(root/'tables.json',build_cost_tables(snapshot,reserve_bytes=0))
        acceptance=dump(root/'acceptance.json',dict(year=year,status='accepted_source_bound_national_snapshot',raw_records=4,institutions=1,every_TS_institution_count_matches=True,source_sha256=m['source_sha256'],manifest_sha256=digest(snapshot/'manifest.json')))
        inputs[year]={'tables':tables,'acceptance':acceptance,'manifest':snapshot/'manifest.json'}
    protocol=dump(tmp_path/'protocol.json',dict(development_years=list(range(2018,2024)),validation_year=2024,final_holdout_year=2025,holdout_data_opened=False))
    return inputs,protocol


def test_freeze_binds_files_and_creates_252_separate_conditional_scenarios(panel,tmp_path):
    inputs,protocol=panel;out=tmp_path/'freeze'
    frozen=api().freeze_national_costs(inputs,out,protocol_path=protocol)
    assert frozen['scenario_count']==252 and len(frozen['scenarios'])==252
    assert frozen['frozen_cutoffs']['2018']['31']=={'p25':0.,'p50':0.,'p75':0.}
    assert frozen['frozen_cutoffs']['2019']['31']=={'p25':.0005,'p50':.001,'p75':.0015}
    assert frozen['frozen_cutoffs']['2023']['31']=={'p25':.0015,'p50':.003,'p75':.0045}
    zeros=[s for s in frozen['scenarios'] if s['development_year']==2018 and s['purpose_code']==31]
    assert len(zeros)==24 and all(s['cost_fraction']==0 for s in zeros)
    assert len({s['development_year'] for s in frozen['scenarios']})==6
    example=next(s for s in frozen['scenarios'] if s['development_year']==2019 and s['purpose_code']==31 and s['quantile']=='p50' and s['balance_rule']=='supplied_balance_ratio' and s['new_to_existing_ratio']==1.1 and s['financing']=='cash')
    assert example['cost_fraction']==pytest.approx(.0011)
    financed=next(s for s in frozen['scenarios'] if s['development_year']==2019 and s['purpose_code']==31 and s['quantile']=='p50' and s['balance_rule']=='all_fees_financed_no_other_balance_change')
    assert financed['cost_fraction']==pytest.approx(.001/.999)
    output_manifest=json.loads((out/'manifest.json').read_text())
    assert output_manifest['files']['frozen-national-costs.json']==digest(out/'frozen-national-costs.json')
    assert all(s['evidence_class']=='conditional_cost_scenario' for s in frozen['scenarios'])
    assert frozen['input_receipts']['2018']['tables_sha256']==digest(inputs[2018]['tables'])
    assert frozen['protocol_sha256']==digest(protocol)
    gate=json.loads((out/'validation-gate.json').read_text())
    assert gate['allowed_years']==[2024]
    assert _gate(2024,out/'validation-gate.json')['frozen_sha256']==digest(out/'frozen-national-costs.json')
    with pytest.raises(ValueError):_gate(2025,out/'validation-gate.json')
    with pytest.raises(FileExistsError):api().freeze_national_costs(inputs,out,protocol_path=protocol)


@pytest.mark.parametrize('mutation',['table_hash','acceptance_hash','source_hash','raw_count','TS_flag','restricted_PA','missing_purpose','missing_year','holdout_year','protocol_split'])
def test_mutated_hash_scope_or_holdout_cannot_publish_freeze(panel,tmp_path,mutation):
    inputs,protocol=panel;entry=inputs[2018]
    table=json.loads(entry['tables'].read_text());acceptance=json.loads(entry['acceptance'].read_text());manifest=json.loads(entry['manifest'].read_text())
    if mutation=='table_hash':table['source_manifest_sha256']='0'*64;dump(entry['tables'],table)
    if mutation=='acceptance_hash':acceptance['manifest_sha256']='0'*64;dump(entry['acceptance'],acceptance)
    if mutation=='source_hash':table['source_sha256']='0'*64;dump(entry['tables'],table)
    if mutation=='raw_count':acceptance['raw_records']=5;dump(entry['acceptance'],acceptance)
    if mutation=='TS_flag':acceptance['every_TS_institution_count_matches']=False;dump(entry['acceptance'],acceptance)
    if mutation=='restricted_PA':
        manifest['raw_scope']='PA only, purposes31/32';dump(entry['manifest'],manifest);acceptance['manifest_sha256']=digest(entry['manifest']);dump(entry['acceptance'],acceptance);table['source_manifest_sha256']=digest(entry['manifest']);dump(entry['tables'],table)
    if mutation=='missing_purpose':table['groups']=[g for g in table['groups'] if not (g['level']=='national_purpose' and g['purpose_code']=='32')];dump(entry['tables'],table)
    if mutation=='missing_year':inputs.pop(2023)
    if mutation=='holdout_year':inputs[2024]=inputs.pop(2023)
    if mutation=='protocol_split':dump(protocol,dict(development_years=[2022,2023],validation_year=2024,final_holdout_year=2025))
    out=tmp_path/'failed-freeze'
    with pytest.raises(ValueError):api().freeze_national_costs(inputs,out,protocol_path=protocol)
    assert not (out/'manifest.json').exists()


def exception_receipt(inputs,year=2018):
    entry=inputs[year];root=Path(entry['acceptance']).parent;manifest=json.loads(entry['manifest'].read_text());acceptance=json.loads(entry['acceptance'].read_text())
    policy=dump(root/'quality-policy.json',dict(status='explicit_cost_only_source_quality_exception_before_2018_cost_inspection',year=2018,permitted_source_sha256=manifest['source_sha256'],published_LAR_records=4,published_TS_sum=6,net_count_discrepancy=-2,remaining_mismatches=1,missing_TS_only_institutions=1,TS_only_record_count=2,other_18_count_net_difference=0,allowed_use=['Descriptive reported-cost distributions conditional on current published public LAR records','Predeclared year/purpose cost scenarios with source-quality qualification','Cost-distribution transport checks with frozen cutoffs'],raw_record_policy='Keep all published source rows; no deletion, imputation, synthetic rows or forced TS match.',not_established=['Every institution-declared row appears in public LAR','Behavioral validity or SOMA transport']))
    audit=dump(root/'raw-audit.json',dict(status='independent_raw_byte_audit_not_TS_acceptance',year=2018,source_sha256=manifest['source_sha256'],source_bytes=manifest['source_bytes'],physical_data_records=4,raw_institutions=1,raw_vs_parquet_all_institution_counts_match=True,raw_vs_parquet_differences=[],completed_ZIP_member_CRC_verified=True,declared_uncompressed_bytes=manifest['uncompressed_bytes'],observed_uncompressed_bytes=manifest['uncompressed_bytes'],TS_sha256='b'*64,TS_count_sum=6,TS_records=2,diagnostic_uppercase_mismatch_count=1,raw_minus_TS_records=-2))
    acceptance.update(status='accepted_published_lar_with_unresolved_ts_discrepancy',every_TS_institution_count_matches=False,official_TS_sum=6,official_TS_sha256='b'*64,raw_minus_TS_records=-2,independent_raw_audit_path=str(audit),independent_raw_audit_sha256=digest(audit),source_quality_policy_path=str(policy),source_quality_policy_sha256=digest(policy),scope='Conditional published reported-cost evidence only; unresolved TS coverage, no behavior or SOMA fit.')
    dump(entry['acceptance'],acceptance);return acceptance,audit,policy


def test_explicit_2018_audited_exception_propagates_false_TS_and_scope(panel,tmp_path):
    inputs,protocol=panel;acceptance,audit,policy=exception_receipt(inputs)
    frozen=api().freeze_national_costs(inputs,tmp_path/'qualified-freeze',protocol_path=protocol)
    receipt=frozen['input_receipts']['2018'];quality=frozen['source_quality_qualifications']['2018']
    assert receipt['every_TS_institution_count_matches'] is False
    assert receipt['source_status']=='accepted_published_lar_with_unresolved_ts_discrepancy'
    assert quality['TS_reconciliation_established'] is False and quality['raw_minus_TS_records']==-2
    assert quality['independent_raw_audit_sha256']==digest(audit)
    assert quality['source_quality_policy_sha256']==digest(policy)
    assert all(s['source_quality_status']=='published_LAR_with_unresolved_TS_discrepancy' for s in frozen['scenarios'] if s['development_year']==2018)
    assert all(frozen['input_receipts'][str(year)]['every_TS_institution_count_matches'] is True for year in range(2019,2024))
    assert 'unresolved' in frozen['interpretation']


@pytest.mark.parametrize('mutation',['missing_policy','policy_changed','audit_changed','wrong_year','wrong_source','audit_counts','CRC_false','TS_arithmetic','policy_scope'])
def test_exception_is_source_bound_2018_only_and_never_an_unaudited_false_TS(panel,tmp_path,mutation):
    inputs,protocol=panel;year=2019 if mutation=='wrong_year' else 2018;acceptance,audit,policy=exception_receipt(inputs,year)
    if mutation=='missing_policy':acceptance.pop('source_quality_policy_path')
    if mutation=='policy_changed':policy.write_text(policy.read_text()+' ')
    if mutation=='audit_changed':audit.write_text(audit.read_text()+' ')
    if mutation=='wrong_source':
        p=json.loads(policy.read_text());p['permitted_source_sha256']='0'*64;dump(policy,p);acceptance['source_quality_policy_sha256']=digest(policy)
    if mutation in ('audit_counts','CRC_false','TS_arithmetic'):
        a=json.loads(audit.read_text())
        if mutation=='audit_counts':a['physical_data_records']=3
        if mutation=='CRC_false':a['completed_ZIP_member_CRC_verified']=False
        if mutation=='TS_arithmetic':a['raw_minus_TS_records']=-1
        dump(audit,a);acceptance['independent_raw_audit_sha256']=digest(audit)
    if mutation=='policy_scope':
        p=json.loads(policy.read_text());p['allowed_use'].append('Behavioral estimation');dump(policy,p);acceptance['source_quality_policy_sha256']=digest(policy)
    dump(inputs[year]['acceptance'],acceptance)
    with pytest.raises(ValueError):api().freeze_national_costs(inputs,tmp_path/'rejected-quality-freeze',protocol_path=protocol)
