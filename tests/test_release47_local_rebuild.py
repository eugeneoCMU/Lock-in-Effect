"""Local archive receipts bind release, identity, cutoffs and preserved sources."""
import hashlib,json,zipfile
from pathlib import Path
import polars as pl
import pytest


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d))


@pytest.fixture
def local_inputs(tmp_path,monkeypatch):
    from hazard import release47_local_rebuild as stage
    source=tmp_path/'source';source.mkdir()
    lid='F20Q40000001';key=hashlib.sha256(lid.encode()).hexdigest()
    row=['']*31
    for i,v in {0:720,1:'202103',10:100000,11:80,12:2.625,15:'FRM',16:'PA',19:lid,21:360}.items():row[i]=str(v)
    orig=source/'orig_2021Q1.txt';orig.write_text('|'.join(row)+'\n')
    perf=source/'perf_2021Q1.txt';lines=[]
    for date,balance,age in [('202102','100000','0'),('202205','90000','15'),('202510','POISON','POISON')]:
        row=['']*35
        for i,v in {0:lid,1:date,2:balance,3:'00',4:age}.items():row[i]=v
        lines.append('|'.join(row))
    perf.write_text('\n'.join(lines)+'\n')
    quarter_zip=tmp_path/'historical_data_2021Q1.zip'
    with zipfile.ZipFile(quarter_zip,'w') as z:
        for p in (orig,perf):z.write(p,p.name)
    inventory=tmp_path/'archive.json';dump(inventory,dict(quarter_archive=str(quarter_zip),quarter_archive_sha256=digest(quarter_zip)))
    extracted=tmp_path/'extracted.json';dump(extracted,dict(files={k:dict(filename=p.name,bytes=p.stat().st_size,sha256=digest(p),zip_crc_verified=True) for k,p in [('origination',orig),('performance',perf)]}))
    identity=tmp_path/'identity.json';dump(identity,dict(quarter='2021Q1',allowed_id_sha256=[key],
        source_sha256=dict(origination=digest(orig),performance=digest(perf)),
        expected=dict(original_records=1,performance_rows=3,eligible_original_loans=1,eligible_original_upb=100000),
        allowed_id_prefixes={key:'F20Q4'},cohort_vintage_by_id_sha256={key:2020}))
    previous=[]
    for year in range(2017,2021):
        for quarter in range(1,5):
            q=f'{year}Q{quarter}';base=tmp_path/q;(base/'rebuilt').mkdir(parents=True);p=base/'rebuilt/eligible_source_ids.parquet';pl.DataFrame({'loan_sequence_number':[f'F{year%100}Q{quarter}999999']}).write_parquet(p)
            completed=base/'completed.json';dump(completed,{'test':True})
            previous.append(dict(quarter=q,completed_path=str(completed),completed_sha256=digest(completed),eligible_ids_path=str(p),eligible_ids_sha256=digest(p)))
    overlap=tmp_path/'overlap.json';dump(overlap,dict(quarters=previous))
    workbook=tmp_path/'official-layout.xlsx';workbook.write_bytes(b'synthetic-layout-reference')
    monkeypatch.setattr(stage,'validate_completed',lambda p:{'quarter':p.name})
    return dict(source=source,quarter_zip=quarter_zip,archive_inventory=inventory,extraction_review=extracted,
        identity_record=identity,overlap_manifest=overlap,layout_workbook=workbook,output=tmp_path/'run')


def test_real_stream_local_archive_receipt_and_vintage(local_inputs):
    from hazard.release47_local_rebuild import run,validate_local_completed
    result=run(**local_inputs)
    assert result['status']=='complete'
    assert result['storage_policy']=='local_archive_retained'
    assert result['cutoff']=='202509'
    assert result['source_layout']=='release47'
    report=json.loads((local_inputs['output']/'rebuilt/report.json').read_text())
    assert report['counts']['post_cutoff_date_rows']==1
    assert report['cutoff_proof']['post_cutoff_outcomes_decoded']==0
    snap=pl.read_parquet(local_inputs['output']/'rebuilt/snapshot.parquet')
    assert snap['vintage'].to_list()==[2020]
    assert validate_local_completed(local_inputs['output'])['status']=='complete'
    assert (local_inputs['source']/'perf_2021Q1.txt').exists()
    assert not (local_inputs['output']/'cleanup.json').exists()


def test_failed_schema_does_not_publish_completion(local_inputs):
    from hazard.release47_local_rebuild import run
    d=json.loads(local_inputs['identity_record'].read_text());d['expected']['performance_rows']=4;dump(local_inputs['identity_record'],d)
    with pytest.raises(ValueError):run(**local_inputs)
    assert not (local_inputs['output']/'completed.json').exists()
    assert (local_inputs['output']/'failed.json').exists()


def test_changed_extracted_file_rejects_before_schema(local_inputs):
    from hazard.release47_local_rebuild import run
    p=local_inputs['source']/'orig_2021Q1.txt';p.write_bytes(p.read_bytes()+b'bad\n')
    with pytest.raises(ValueError,match='source|Source|size|Size'):run(**local_inputs)
    assert not (local_inputs['output']/'completed.json').exists()


def test_exception_overlap_blocks_before_outcomes(local_inputs,monkeypatch):
    from hazard import release47_local_rebuild as stage
    m=json.loads(local_inputs['overlap_manifest'].read_text());item=m['quarters'][-1];p=Path(item['eligible_ids_path'])
    pl.DataFrame({'loan_sequence_number':['F20Q40000001']}).write_parquet(p);item['eligible_ids_sha256']=digest(p);dump(local_inputs['overlap_manifest'],m)
    monkeypatch.setattr(stage,'build_quarter',lambda *a,**kw:pytest.fail('Outcome processing reached despite overlap'))
    with pytest.raises(ValueError,match='overlap|Overlap'):stage.run(**local_inputs)


def test_tampered_output_cannot_validate(local_inputs):
    from hazard.release47_local_rebuild import run,validate_local_completed
    run(**local_inputs)
    with (local_inputs['output']/'rebuilt/snapshot.parquet').open('ab') as f:f.write(b'bad')
    with pytest.raises(ValueError,match='hash|Hash|artifact'):validate_local_completed(local_inputs['output'])


def reseal(output):
    p=output/'completed.json';r=json.loads(p.read_text())
    r['output_sha256']={str(x.relative_to(output)):digest(x) for x in output.rglob('*') if x.is_file() and x.name!='completed.json'}
    dump(p,r)


def test_mislabeled_prior_quarter_is_rejected(local_inputs):
    from hazard.release47_local_rebuild import run
    p=local_inputs['overlap_manifest'];m=json.loads(p.read_text());m['quarters'][1].update({k:m['quarters'][0][k] for k in ('completed_path','completed_sha256','eligible_ids_path','eligible_ids_sha256')});dump(p,m)
    with pytest.raises(ValueError,match='quarter|Quarter|duplicate|Duplicate'):run(**local_inputs)


def test_resealed_later_cutoff_is_rejected(local_inputs):
    from hazard.release47_local_rebuild import run,validate_local_completed
    run(**local_inputs);p=local_inputs['output']/'rebuilt/report.json';r=json.loads(p.read_text());r['cutoff']='202603';dump(p,r);reseal(local_inputs['output'])
    with pytest.raises(ValueError,match='cutoff|Cutoff|identity|Identity'):validate_local_completed(local_inputs['output'])


def test_missing_code_freeze_is_rejected(local_inputs):
    from hazard.release47_local_rebuild import run,validate_local_completed
    run(**local_inputs);p=local_inputs['output']/'input_manifest.json';r=json.loads(p.read_text());r['code_sha256']={};dump(p,r);reseal(local_inputs['output'])
    with pytest.raises(ValueError,match='code|Code'):validate_local_completed(local_inputs['output'])


def add_unknown_history_loan(inputs):
    source=inputs['source'];orig=source/'orig_2021Q1.txt';perf=source/'perf_2021Q1.txt'
    r=['']*31
    for i,v in {0:720,1:'202104',10:100000,11:80,12:2.625,15:'FRM',16:'PA',19:'F21Q10000002',21:360}.items():r[i]=str(v)
    with orig.open('a') as f:f.write('|'.join(r)+'\n')
    r=['']*35
    for i,v in {0:'F21Q10000002',1:'202207',2:'90000',3:'00',4:'15'}.items():r[i]=v
    with perf.open('a') as f:f.write('|'.join(r)+'\n')
    with zipfile.ZipFile(inputs['quarter_zip'],'w') as z:
        for p in (orig,perf):z.write(p,p.name)
    d=json.loads(inputs['archive_inventory'].read_text());d['quarter_archive_sha256']=digest(inputs['quarter_zip']);dump(inputs['archive_inventory'],d)
    d=json.loads(inputs['extraction_review'].read_text())
    for k,p in [('origination',orig),('performance',perf)]:d['files'][k].update(bytes=p.stat().st_size,sha256=digest(p))
    dump(inputs['extraction_review'],d)
    identity=json.loads(inputs['identity_record'].read_text());identity['source_sha256']={k:d['files'][k]['sha256'] for k in d['files']};dump(inputs['identity_record'],identity)
    evidence=orig.parent/'coverage-evidence.json';dump(evidence,{'synthetic_fixture':True})
    record=orig.parent/'coverage-record.json';dump(record,dict(policy='known_pre_snapshot_history_v1',quarter='2021Q1',
        source_sha256=identity['source_sha256'],expected_missing_loans=1,expected_missing_original_upb=100000,
        expected_original_first_payment={'202104':1},expected_first_valid_performance={'202207':1},
        evidence_sha256={str(evidence):digest(evidence)}))
    return record


def test_documented_unknown_history_stays_out_of_may_snapshot(local_inputs):
    from hazard.release47_local_rebuild import run,validate_local_completed
    coverage=add_unknown_history_loan(local_inputs)
    run(**local_inputs,coverage_record=coverage)
    report=json.loads((local_inputs['output']/'rebuilt/report.json').read_text())
    audit=report['pre_snapshot_coverage']
    assert audit['missing_loans']==1 and audit['unknown_original_upb']==100000
    assert audit['unknown_history_imputed'] is False
    assert audit['may_snapshot_unknown_loans']==0
    assert report['counts']['eligible_original_ids']==2
    assert pl.read_parquet(local_inputs['output']/'rebuilt/snapshot.parquet').height==1
    assert validate_local_completed(local_inputs['output'])['status']=='complete'


def test_missing_unknown_history_record_keeps_gate_strict(local_inputs):
    from hazard.release47_local_rebuild import run
    add_unknown_history_loan(local_inputs)
    with pytest.raises(ValueError,match='pre-snapshot'):run(**local_inputs)
    assert not (local_inputs['output']/'completed.json').exists()
