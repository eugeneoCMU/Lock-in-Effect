"""Source-bound Release 47 rebuild from retained local archives.

This separate receipt never claims File Provider eviction or cloud-runner
completion. Existing frozen runs and their source semantics remain untouched.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile
import zlib

ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'hazard'
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
from run_freddie_rebuild import digest,write_json,validate_completed
from freddie_raw_quarter_audit import schema_audit,check_resources,IdentityExceptions
from freddie_rebuild_stream import build_quarter
from schema import source_semantics_version,source_layout_metadata
from coverage_exception import validate_audit
import polars as pl

PRIOR_QUARTERS=[f'{year}Q{quarter}' for year in range(2017,2021) for quarter in range(1,5)]
CODE_FILES=('release47_local_rebuild.py','schema.py','freddie_raw_quarter_audit.py',
            'freddie_rebuild_stream.py','coverage_exception.py','run_freddie_rebuild.py','config.py')
ARTIFACTS={'panel.parquet','snapshot.parquet','cohort_history.parquet','eligible_source_ids.parquet','transition_counts.parquet'}
SPEC=ROOT/'specs/SPEC_2026-10-13_release47_local.md'


def require(ok,message):
    if not ok:raise ValueError(message)


def verify_hashes(hashes):
    for name,expected in hashes.items():
        require(digest(name)==expected,'Input/code hash changed: '+name)


def source_identity(path):
    h=hashlib.sha256();crc=0;size=0
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):
            h.update(block);crc=zlib.crc32(block,crc);size+=len(block)
    return dict(bytes=size,sha256=h.hexdigest(),crc32=crc)


def validate_overlap_manifest(path):
    entries=json.loads(path.read_text())['quarters']
    require([x['quarter'] for x in entries]==PRIOR_QUARTERS,'Exact prior-quarter manifest required')
    require(len({str(Path(x['completed_path']).resolve()) for x in entries})==len(entries),'Duplicate prior quarter paths')
    for item in entries:
        completed=Path(item['completed_path']);ids=Path(item['eligible_ids_path'])
        require(digest(completed)==item['completed_sha256'],'Prior completion hash differs')
        receipt=validate_completed(completed.parent)
        require(receipt.get('quarter')==item['quarter'],'Prior completion quarter differs')
        require(digest(ids)==item['eligible_ids_sha256'],'Prior eligible-ID inventory hash differs')
        # The validator above checks that the receipt seals this precise local artifact.
        require(ids.resolve()==(completed.parent/'rebuilt/eligible_source_ids.parquet').resolve()
,'Eligible-ID inventory is not bound to the completed quarter')
    return entries


def check_overlap(entries,allowed_hashes,new_ids=None):
    """Check exact exception hashes before outcomes and all eligible IDs afterward."""
    for item in entries:
        old=pl.read_parquet(item['eligible_ids_path'],columns=['loan_sequence_number'])
        if new_ids is None:
            overlap=any(hashlib.sha256(x.encode()).hexdigest() in allowed_hashes for x in old['loan_sequence_number'])
        else:
            overlap=old.join(new_ids,on='loan_sequence_number',how='inner').height>0
        require(not overlap,'Eligible source-ID overlap with '+item['quarter'])


def validate_local_completed(output,*,verify_inputs=True):
    output=Path(output)
    require(not (output/'failed.json').exists(),'Failed local rebuild cannot validate')
    receipt=json.loads((output/'completed.json').read_text())
    require(receipt.get('status')=='complete' and receipt.get('storage_policy')=='local_archive_retained'
            and receipt.get('source_layout')=='release47' and receipt.get('quarter')=='2021Q1'
            and receipt.get('cutoff')=='202509','Invalid local archive completion identity')
    required={'input_manifest.json','schema.json','source_hashes_after.json','resources.json','spec_frozen.md',
              'identity_record.json','overlap_manifest.json','extraction_review.json','archive_inventory.json','layout_workbook.xlsx',
              'rebuilt/report.json'} | {'rebuilt/'+name for name in ARTIFACTS} | {'executed_code/'+name for name in CODE_FILES}
    actual_files={str(p.relative_to(output)) for p in output.rglob('*') if p.is_file() and p.name!='completed.json'}
    require(required.issubset(actual_files),'Missing required archived evidence/code')
    require(set(receipt['output_sha256'])==actual_files,'Incomplete output artifact hash coverage')
    for name,expected in receipt['output_sha256'].items():
        require(Path(name).is_absolute() is False and '..' not in Path(name).parts,'Unsafe output artifact path')
        require(digest(output/name)==expected,'Output artifact hash differs: '+name)
    manifest=json.loads((output/'input_manifest.json').read_text())
    require(manifest['source_layout']==source_layout_metadata('release47'),'Local layout differs')
    require({Path(name).name for name in manifest['code_sha256']}==set(CODE_FILES)
            and len(manifest['code_sha256'])==len(CODE_FILES),'Incomplete code freeze')
    for name,expected in manifest['code_sha256'].items():
        require(digest(output/'executed_code'/Path(name).name)==expected,'Executed code archive hash differs')
    if verify_inputs:verify_hashes(manifest['input_sha256'])
    schema=json.loads((output/'schema.json').read_text())
    report=json.loads((output/'rebuilt/report.json').read_text())
    after=json.loads((output/'source_hashes_after.json').read_text())
    for obj in (manifest,report):
        require(all(obj.get(k)==v for k,v in {'quarter':'2021Q1','cutoff':'202509','snapshot_month':'202205','transition_end':'202205'}.items()),
                'Local quarter/cutoff identity differs')
    require(report['cutoff_proof']['latest_decoded_month'] is None or report['cutoff_proof']['latest_decoded_month']<='202509',
            'Decoded outcome exceeds cutoff')
    resources=json.loads((output/'resources.json').read_text())
    require(resources['peak_rss_bytes']<8*1024**3 and resources['free_disk_bytes']>=12*1024**3,'Resource thresholds not verified')
    require(schema['passed'] is True,'Local schema gate failed')
    require(report['source_semantics_version']==schema['source_semantics_version']==source_semantics_version('release47'),
            'Local source semantics differ')
    require(after==report['source_sha256']=={k:schema[k]['sha256'] for k in ('origination','performance')},'Local source hashes disagree')
    require(set(report['artifacts'])==ARTIFACTS,'Incomplete local rebuilt artifacts')
    for name,item in report['artifacts'].items():
        require(digest(output/'rebuilt'/name)==item['sha256'],'Rebuilt artifact hash differs: '+name)
    require(report['cutoff_proof']['post_cutoff_outcomes_decoded']==0
            and report['cutoff_proof']['outcome_filter_precedes_decode'] is True,'Local outcome cutoff failed')
    require(report['counts']['semantic_rows_validated']==report['counts']['eligible_pre_cutoff_rows'],'Local semantic validation incomplete')
    require(report['identity_exceptions']==schema['identity_exceptions'],'Local identity accounting differs')
    require(report['counts']['origination_rows']==schema['origination']['rows']
            and report['counts']['performance_rows']==schema['performance']['rows']
            and report['counts']['eligible_original_ids']==schema['origination']['eligible_360_month_ids'],
            'Local schema/stream population counts differ')
    coverage=None
    if manifest.get('coverage_exception_enabled'):
        require((output/'coverage_record.json').is_file(),'Missing frozen coverage record')
        coverage=json.loads((output/'coverage_record.json').read_text())
        require(bool(coverage.get('evidence_sha256')),'Missing frozen coverage evidence')
        for name,expected in coverage['evidence_sha256'].items():
            require(digest(output/'coverage_evidence'/Path(name).name)==expected,'Frozen coverage evidence differs')
    validate_audit(coverage,report,output)
    require(report['zero_note_rate_exclusions']==schema['origination']['zero_note_rate_exclusions'],
            'Local zero-rate exclusion counts differ')
    return receipt


def run(*,source,quarter_zip,archive_inventory,extraction_review,identity_record,
        overlap_manifest,layout_workbook,output,coverage_record=None):
    paths={k:Path(v).resolve() for k,v in locals().items() if v is not None}
    source=paths.pop('source');output=paths.pop('output')
    require(output!=source and source not in output.parents and output not in source.parents,'Output overlaps source directory')
    if output.exists():raise FileExistsError('Preserve prior attempts; choose a new local rebuild output')
    output.mkdir(parents=True,mode=0o700)
    try:
        initial_resources=check_resources(output)
        inputs={str(p):digest(p) for p in paths.values()}
        inputs[str(SPEC)]=digest(SPEC)
        code={str(HERE/name):digest(HERE/name) for name in CODE_FILES}
        archive=output/'executed_code';archive.mkdir()
        for name in CODE_FILES:shutil.copy2(HERE/name,archive/name)
        for key in ('identity_record','overlap_manifest','extraction_review','archive_inventory','layout_workbook'):
            shutil.copy2(paths[key],output/(key+paths[key].suffix))
        shutil.copy2(SPEC,output/'spec_frozen.md')
        inventory=json.loads(paths['archive_inventory'].read_text())
        require(digest(paths['quarter_zip'])==inventory['quarter_archive_sha256'],'Quarter archive hash differs')
        expected=json.loads(paths['extraction_review'].read_text())['files']
        actual={}
        with zipfile.ZipFile(paths['quarter_zip']) as z:
            members={i.filename:i for i in z.infolist()}
            require(set(members)=={'orig_2021Q1.txt','perf_2021Q1.txt'},'Unexpected quarter archive members')
            for kind,filename in [('origination','orig_2021Q1.txt'),('performance','perf_2021Q1.txt')]:
                p=source/filename;actual[kind]=source_identity(p);record=expected[kind]
                require(record['filename']==filename and record['zip_crc_verified'] is True
                        and actual[kind]['bytes']==record['bytes']==members[filename].file_size
                        and actual[kind]['sha256']==record['sha256']
                        and actual[kind]['crc32']==members[filename].CRC,'Extracted source size/hash/CRC mismatch: '+kind)
                inputs[str(p)]=actual[kind]['sha256']
        identity=json.loads(paths['identity_record'].read_text())
        IdentityExceptions('2021Q1',identity)
        require(identity['source_sha256']=={k:v['sha256'] for k,v in actual.items()},'Identity exception source differs')
        require(identity.get('allowed_id_prefixes') and identity.get('cohort_vintage_by_id_sha256'),'Explicit exception prefix/vintage required')
        coverage=None
        if 'coverage_record' in paths:
            coverage=json.loads(paths['coverage_record'].read_text())
            require(coverage.get('quarter')=='2021Q1' and coverage.get('policy')=='known_pre_snapshot_history_v1'
                    and coverage.get('source_sha256')==identity['source_sha256'],'Coverage exception source/policy differs')
            evidence=coverage.get('evidence_sha256',{})
            require(bool(evidence) and len({Path(p).name for p in evidence})==len(evidence),'Coverage evidence required')
            folder=output/'coverage_evidence';folder.mkdir()
            for name,expected_hash in evidence.items():
                require(digest(name)==expected_hash,'Coverage evidence hash differs')
                inputs[str(Path(name).resolve())]=expected_hash
                shutil.copy2(name,folder/Path(name).name)
            shutil.copy2(paths['coverage_record'],output/'coverage_record.json')
        previous=validate_overlap_manifest(paths['overlap_manifest'])
        for item in previous:
            inputs[item['completed_path']]=item['completed_sha256']
            inputs[item['eligible_ids_path']]=item['eligible_ids_sha256']
        manifest=dict(created_utc=datetime.now(timezone.utc).isoformat(),quarter='2021Q1',cutoff='202509',
            snapshot_month='202205',transition_end='202205',source_layout=source_layout_metadata('release47'),
            storage_policy='local_archive_retained',input_sha256=inputs,code_sha256=code,
            identity_policy='Exact source-bound prefix/vintage maps; no identifier rewriting',
            overlap_population='Previously completed eligible source-ID inventories; no all-excluded-record claim',
            parameter_selection_performed=False,coverage_exception_enabled=coverage is not None)
        write_json(output/'input_manifest.json',manifest)
        check_overlap(previous,set(identity['allowed_id_sha256']))
        print('Schema/identity/date gate starting',flush=True)
        schema,_=schema_audit(source/'orig_2021Q1.txt',source/'perf_2021Q1.txt',quarter='2021Q1',
            exclude_zero_note_rate=True,identity_exceptions=identity,source_layout='release47')
        write_json(output/'schema.json',schema)
        require(schema['passed'],'Release47 schema/identity/date gate failed')
        verify_hashes(dict(inputs,**code))
        print('Schema gate passed; bounded outcome rebuild starting',flush=True)
        report=build_quarter(source/'orig_2021Q1.txt',source/'perf_2021Q1.txt',output/'rebuilt','2021Q1',
            cutoff='202509',transition_end='202205',exclude_zero_note_rate=True,
            allow_partial_cohort_overrun=True,identity_exceptions=identity,source_layout='release47',coverage_exception=coverage)
        check_overlap(previous,set(),pl.read_parquet(output/'rebuilt/eligible_source_ids.parquet'))
        final_resources=check_resources(output)
        write_json(output/'resources.json',dict(peak_rss_bytes=max(initial_resources['peak_rss_bytes'],final_resources['peak_rss_bytes']),
            free_disk_bytes=min(initial_resources['free_disk_bytes'],final_resources['free_disk_bytes']),
            checks='Per-row worker checkpoints enforce 12GiB disk / 8GiB RSS; process high-water RSS retained'))
        verify_hashes(dict(inputs,**code))
        after={k:digest(source/name) for k,name in [('origination','orig_2021Q1.txt'),('performance','perf_2021Q1.txt')]}
        require(after==report['source_sha256']=={k:schema[k]['sha256'] for k in actual},'Source changed during local rebuild')
        write_json(output/'source_hashes_after.json',after)
        receipt=dict(status='complete',quarter='2021Q1',cutoff='202509',source_layout='release47',
            source_semantics_version=source_semantics_version('release47'),storage_policy='local_archive_retained',
            source_inputs_unchanged=True,overlap_check_passed=True,parameter_selection_performed=False,
            empirical_estimate_replaced=False,created_utc=datetime.now(timezone.utc).isoformat(),
            output_sha256={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()})
        write_json(output/'completed.json',receipt)
        validate_local_completed(output)
        print('Local quarter completed and verified',flush=True)
        return receipt
    except BaseException as exc:
        if (output/'completed.json').exists():(output/'completed.json').unlink()
        write_json(output/'failed.json',dict(error_type=type(exc).__name__,error=str(exc),status='failed',
            failed_utc=datetime.now(timezone.utc).isoformat(),source_files_retained=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('source','quarter-zip','archive-inventory','extraction-review','identity-record','overlap-manifest','layout-workbook','output'):
        p.add_argument('--'+key,required=True,type=Path)
    p.add_argument('--coverage-record',type=Path)
    run(**vars(p.parse_args()))
