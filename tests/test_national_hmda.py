"""National ingestion must not narrow raw activity or leak holdout data."""
import csv
import hashlib
import importlib
import json
import zipfile
import pytest
from hazard.hmda_cost_profiles import REQUIRED, build_profiles


def api():
    try:
        return importlib.import_module('hazard.national_hmda')
    except ModuleNotFoundError:
        pytest.fail('National snapshot workflow is missing')


def row(**changes):
    r=dict(zip(REQUIRED,['2023','PA','42003','1','1','2','2','C','1','1','1','1','31','100000','100','6','','','L1']))
    r.update(changes)
    return r


def source(tmp_path, rows):
    p=tmp_path/'source.csv'
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=[*REQUIRED,'extra']);w.writeheader()
        w.writerows(dict(r,extra='001') for r in rows)
    return p


def ingest(tmp_path, rows, **kwargs):
    p=source(tmp_path,rows)
    return api().ingest_snapshot(p,tmp_path/'snapshot',year=2023,source_url='https://example.org/snapshot',publication_version='test-frozen',batch_rows=2,reserve_bytes=0,**kwargs)


def test_raw_retains_all_actions_purposes_jurisdictions_and_codes(tmp_path):
    m=ingest(tmp_path,[row(),row(state_code='PR',action_taken='6',loan_purpose='1'),row(state_code='',county_code='',action_taken='8',total_loan_costs='Exempt')])
    assert m['record_count']==3
    assert m['state_counts']=={'':1,'PA':1,'PR':1}
    assert m['action_counts']=={'1':1,'6':1,'8':1}
    assert m['source_sha256']==hashlib.sha256((tmp_path/'source.csv').read_bytes()).hexdigest()
    import duckdb
    rows=duckdb.sql(f"select state_code,total_loan_costs,extra from read_parquet('{tmp_path}/snapshot/part-*.parquet') order by state_code").fetchall()
    assert rows==[('', 'Exempt','001'),('PA','100','001'),('PR','100','001')]
    assert len(m['parquet_files'])==2


def test_zip_streaming_and_exact_profiles_match_legacy(tmp_path):
    rows=[row(total_loan_costs=x) for x in ('0','100','300','NA','','Exempt')]+[row(action_taken='3'),row(loan_purpose='32',loan_amount='333333',total_loan_costs='222.22')]
    p=source(tmp_path,rows)
    z=tmp_path/'snapshot.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:f.write(p,'nested/lar.csv')
    api().ingest_snapshot(z,tmp_path/'snapshot',year=2023,source_url='https://example.org/zip',publication_version='test',reserve_bytes=0,batch_rows=2)
    actual=api().profile_snapshot(tmp_path/'snapshot',state='PA')
    assert actual==build_profiles(rows,expected_year=2023,expected_state='PA')
    assert api().profile_snapshot(tmp_path/'snapshot')['raw_application_records']==8


@pytest.mark.parametrize('changes',[{'activity_year':'2022'}])
def test_wrong_year_never_publishes_manifest(tmp_path,changes):
    with pytest.raises(ValueError,match='year'):ingest(tmp_path,[row(**changes)])
    assert not (tmp_path/'snapshot/manifest.json').exists()


def test_schema_disk_and_immutable_destination_guards(tmp_path):
    p=source(tmp_path,[row()])
    with pytest.raises(ValueError,match='schema'):
        api().ingest_snapshot(p,tmp_path/'bad',year=2023,source_url='u',publication_version='v',expected_header=['bad'],reserve_bytes=0)
    with pytest.raises(OSError,match='Disk'):
        api().ingest_snapshot(p,tmp_path/'full',year=2023,source_url='u',publication_version='v',reserve_bytes=10**30)
    ingest(tmp_path,[row()])
    with pytest.raises(FileExistsError):ingest(tmp_path,[row()])


def test_holdout_requires_frozen_artifact_hash_and_final_requires_validation(tmp_path):
    p=source(tmp_path,[row(activity_year='2024')])
    with pytest.raises(ValueError,match='freeze'):
        api().ingest_snapshot(p,tmp_path/'blocked',year=2024,source_url='u',publication_version='v',reserve_bytes=0)
    frozen=tmp_path/'frozen.json';frozen.write_text('{"model":"frozen"}')
    gate=tmp_path/'gate.json';gate.write_text(json.dumps({'development_years':list(range(2018,2024)), 'validation_year':2024,'final_evaluation_year':2025,'frozen_artifact':str(frozen),'frozen_sha256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'allowed_years':[2024]}))
    api().ingest_snapshot(p,tmp_path/'allowed',year=2024,source_url='u',publication_version='v',freeze_gate=gate,reserve_bytes=0)
    with pytest.raises(ValueError,match='freeze'):api().profile_snapshot(tmp_path/'allowed')
    assert api().profile_snapshot(tmp_path/'allowed',freeze_gate=gate)['year']==2024
    frozen.write_text('changed')
    with pytest.raises(ValueError,match='hash'):api().profile_snapshot(tmp_path/'allowed',freeze_gate=gate)


def test_profile_filters_broad_raw_and_rejects_corrupted_parts(tmp_path):
    ingest(tmp_path,[row(),row(state_code='OH'),row(state_code='PR',loan_purpose='1'),row(action_taken='6'),row(state_code='')])
    assert api().profile_snapshot(tmp_path/'snapshot',state='PA')['raw_application_records']==1
    assert api().profile_snapshot(tmp_path/'snapshot')['raw_application_records']==3
    part=next((tmp_path/'snapshot').glob('part-*.parquet'));part.write_bytes(b'corrupt')
    with pytest.raises(ValueError,match='integrity'):api().profile_snapshot(tmp_path/'snapshot')


@pytest.mark.parametrize('value',['oops','nan','Infinity','-1','0.0000000000001'])
def test_numeric_profile_validation_never_silently_rounds_or_accepts_bad_values(tmp_path,value):
    ingest(tmp_path,[row(total_loan_costs=value)])
    with pytest.raises(ValueError,match='numeric'):api().profile_snapshot(tmp_path/'snapshot')


def test_2025_no_data_read_without_completed_validation_gate(tmp_path):
    frozen=tmp_path/'frozen';frozen.write_text('frozen')
    gate=tmp_path/'gate';g={'development_years':list(range(2018,2024)),'validation_year':2024,'final_evaluation_year':2025,'frozen_artifact':str(frozen),'frozen_sha256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'allowed_years':[2025]};gate.write_text(json.dumps(g))
    with pytest.raises(ValueError,match='validation'):api().ingest_snapshot(tmp_path/'does-not-exist.zip',tmp_path/'final',year=2025,source_url='u',publication_version='v',freeze_gate=gate)


def test_official_snapshot_underscore_header_is_preserved_and_aliased_for_analysis(tmp_path):
    p=source(tmp_path,[row()]);p.write_text(p.read_text().replace('open-end_line_of_credit','open_end_line_of_credit'))
    m=api().ingest_snapshot(p,tmp_path/'official',year=2023,source_url='u',publication_version='v',reserve_bytes=0)
    assert 'open_end_line_of_credit' in m['header']
    assert 'open-end_line_of_credit' not in m['header']
    assert api().profile_snapshot(tmp_path/'official',state='PA')==build_profiles([row()],expected_year=2023,expected_state='PA')
    both=p.read_text().replace('open_end_line_of_credit','open_end_line_of_credit,open-end_line_of_credit');p.write_text(both)
    with pytest.raises(ValueError,match='schema'):api().ingest_snapshot(p,tmp_path/'ambiguous',year=2023,source_url='u',publication_version='v',reserve_bytes=0)


def test_fast_zip_retains_raw_and_reproduces_profile_without_full_csv_expansion(tmp_path):
    rows=[row(),row(state_code='PR',action_taken='8',loan_purpose='1',total_loan_costs='Exempt')]
    p=source(tmp_path,rows);z=tmp_path/'source.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:f.write(p,'lar.csv')
    m=api().ingest_snapshot(z,tmp_path/'fast',year=2023,source_url='u',publication_version='v',reserve_bytes=0,fast_zip=True)
    assert m['record_count']==2 and m['state_counts']=={'PA':1,'PR':1}
    assert m['ingest_engine']=='native_duckdb_gzip'
    assert api().profile_snapshot(tmp_path/'fast',state='PA')==build_profiles(rows[:1],expected_year=2023,expected_state='PA')
    assert not list((tmp_path/'fast').rglob('*.gz'))
    with pytest.raises(OSError,match='Disk'):api().ingest_snapshot(z,tmp_path/'limited',year=2023,source_url='u',publication_version='v',reserve_bytes=0,max_output_bytes=1,fast_zip=True)


def test_native_zip_optional_threads_preserve_all_record_values(tmp_path):
    rows=[row(),row(state_code='PR',loan_purpose='32',total_loan_costs='0'),row(state_code='',action_taken='8')]
    p=source(tmp_path,rows);z=tmp_path/'source.zip'
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as f:f.write(p,'lar.csv')
    one=api().ingest_snapshot(z,tmp_path/'one',year=2023,source_url='u',publication_version='v',reserve_bytes=0,fast_zip=True)
    four=api().ingest_snapshot(z,tmp_path/'four',year=2023,source_url='u',publication_version='v',reserve_bytes=0,fast_zip=True,threads=4,memory_limit='1GB')
    assert one['record_count']==four['record_count']==3
    assert four['resources']['threads']==4 and one['resources']['threads']==1
    import duckdb
    con=duckdb.connect()
    try:
        left=con.execute(f"select * from read_parquet('{tmp_path}/one/part-000000.parquet')").fetchall()
        right=con.execute(f"select * from read_parquet('{tmp_path}/four/part-000000.parquet')").fetchall()
        assert sorted(left)==sorted(right)
    finally:con.close()


@pytest.mark.parametrize('threads',[True,0,-1,1.5,'4'])
def test_ingest_threads_must_be_explicit_positive_integers(tmp_path,threads):
    with pytest.raises(ValueError,match='threads'):
        api().ingest_snapshot(tmp_path/'unread.csv',tmp_path/'unwritten',year=2023,source_url='u',publication_version='v',threads=threads)
