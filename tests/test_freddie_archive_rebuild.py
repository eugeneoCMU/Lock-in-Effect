"""Annual archive rebuild runs all real gates on small synthetic sources."""
import hashlib,json,zipfile
from pathlib import Path
import polars as pl
import pytest


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.write_text(json.dumps(d))


@pytest.fixture
def archive_inputs(tmp_path,monkeypatch):
    from hazard import freddie_archive_rebuild as stage
    quarter='2021Q2';rows=[]
    for lid,upb,first in [('F21Q20000001',100000,'202105'),('F20Q40000002',120000,'202105'),('F21Q20000003',80000,'202104')]:
        r=['']*31
        for i,v in {0:720,1:first,10:upb,11:80,12:3.,15:'FRM',16:'PA',19:lid,21:360}.items():r[i]=str(v)
        rows.append('|'.join(r))
    perf=[]
    for lid,date,balance,age in [('F21Q20000001','202204',95000,11),('F21Q20000001','202205',94000,12),('F21Q20000001','202510','POISON','POISON'),('F20Q40000002','202204',110000,11),('F20Q40000002','202205',109000,12),('F20Q40000002','202207',108000,14),('F21Q20000003','202208',79000,16)]:
        r=['']*35
        for i,v in {0:lid,1:date,2:balance,3:'00',4:age}.items():r[i]=str(v)
        perf.append('|'.join(r))
    qzip=tmp_path/'historical_data_2021Q2.zip'
    with zipfile.ZipFile(qzip,'w',compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('orig_2021Q2.txt','\n'.join(rows)+'\n');z.writestr('perf_2021Q2.txt','\n'.join(perf)+'\n')
    annual=tmp_path/'historical_data_2021.zip'
    with zipfile.ZipFile(annual,'w',compression=zipfile.ZIP_STORED) as z:z.write(qzip,qzip.name)
    previous=[]
    for year in range(2017,2022):
        for q in range(1,5):
            label=f'{year}Q{q}'
            if label>=quarter:break
            p=tmp_path/label;(p/'rebuilt').mkdir(parents=True)
            completed=p/'completed.json';dump(completed,dict(quarter=label))
            ids=p/'rebuilt/eligible_source_ids.parquet';pl.DataFrame({'loan_sequence_number':[f'F{year%100}Q{q}999999']}).write_parquet(ids)
            previous.append(dict(quarter=label,completed_path=str(completed),completed_sha256=digest(completed),eligible_ids_path=str(ids),eligible_ids_sha256=digest(ids)))
    prior=tmp_path/'prior.json';dump(prior,dict(quarters=previous))
    workbook=tmp_path/'layout.xlsx';workbook.write_bytes(b'synthetic-layout')
    monkeypatch.setattr(stage,'validate_source_completed',lambda path:json.loads((path/'completed.json').read_text()))
    return dict(annual_zip=annual,quarter=quarter,prior_manifest=prior,layout_workbook=workbook,output=tmp_path/'run')


def test_full_archive_rebuild_and_saved_completion(archive_inputs):
    from hazard.freddie_archive_rebuild import run,validate_archive_completed
    result=run(**archive_inputs)
    assert result['status']=='complete' and result['storage_policy']=='annual_archive_retained'
    report=json.loads((archive_inputs['output']/'rebuilt/report.json').read_text())
    assert report['counts']['eligible_original_ids']==3
    assert report['pre_snapshot_coverage']['missing_loans']==1
    assert report['pre_snapshot_coverage']['unknown_history_imputed'] is False
    assert report['cutoff_proof']['post_cutoff_outcomes_decoded']==0
    snap=pl.read_parquet(archive_inputs['output']/'rebuilt/snapshot.parquet')
    assert sorted(snap['vintage'].to_list())==[2020,2021]
    assert validate_archive_completed(archive_inputs['output'])['status']=='complete'
    assert not list(archive_inputs['output'].glob('*.txt'))
    assert archive_inputs['annual_zip'].exists()


def test_prior_overlap_is_fatal(archive_inputs,monkeypatch):
    from hazard import freddie_archive_rebuild as stage
    p=archive_inputs['prior_manifest'];d=json.loads(p.read_text());item=d['quarters'][-1];ids=Path(item['eligible_ids_path'])
    pl.DataFrame({'loan_sequence_number':['F21Q20000001']}).write_parquet(ids);item['eligible_ids_sha256']=digest(ids);dump(p,d)
    monkeypatch.setattr(stage,'build_quarter',lambda *a,**k:pytest.fail('Outcome rebuild despite overlap'))
    with pytest.raises(ValueError,match='overlap|Overlap'):stage.run(**archive_inputs)
    assert not (archive_inputs['output']/'completed.json').exists()


def test_resealed_later_window_is_rejected(archive_inputs):
    from hazard.freddie_archive_rebuild import run,validate_archive_completed
    run(**archive_inputs);out=archive_inputs['output'];p=out/'rebuilt/report.json';d=json.loads(p.read_text());d['cutoff']='202603';dump(p,d)
    r=json.loads((out/'completed.json').read_text());r['output_sha256']={str(p.relative_to(out)):digest(p) for p in out.rglob('*') if p.is_file() and p.name!='completed.json'};dump(out/'completed.json',r)
    with pytest.raises(ValueError,match='cutoff|identity'):validate_archive_completed(out)


def test_missing_archived_code_rejects(archive_inputs):
    from hazard.freddie_archive_rebuild import run,validate_archive_completed
    run(**archive_inputs);out=archive_inputs['output'];(out/'executed_code/schema.py').unlink()
    with pytest.raises((ValueError,FileNotFoundError)):validate_archive_completed(out)
