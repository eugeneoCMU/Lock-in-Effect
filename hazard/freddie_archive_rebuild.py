"""Audited quarterly rebuilds streaming retained annual ZIP members."""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parent.parent
HERE=ROOT/'hazard'
if str(HERE) not in sys.path:sys.path.insert(0,str(HERE))
from freddie_archive_source import ArchiveMember
from freddie_raw_quarter_audit import schema_audit,check_resources,finite,IdentityExceptions
from freddie_rebuild_stream import build_quarter
from schema import source_semantics_version,source_layout_metadata
from run_freddie_rebuild import digest,write_json,QUARTERS
from release47_local_rebuild import check_overlap,ARTIFACTS,verify_hashes,require
from coverage_exception import validate_audit,POLICY
from source_rebuild_receipts import validate_source_completed
import polars as pl

SPEC=ROOT/'specs/SPEC_2026-10-14_archive_rerun.md'
CODE_FILES=('freddie_archive_rebuild.py','freddie_archive_source.py','freddie_raw_quarter_audit.py',
 'freddie_rebuild_stream.py','schema.py','coverage_exception.py','run_freddie_rebuild.py',
 'release47_local_rebuild.py','source_rebuild_receipts.py','config.py')


def validate_prior(path,quarter):
    entries=json.loads(path.read_text())['quarters'];expected=QUARTERS[:QUARTERS.index(quarter)]
    require([x['quarter'] for x in entries]==expected,'Exact preceding-quarter manifest required')
    require(len({str(Path(x['completed_path']).resolve()) for x in entries})==len(entries),'Duplicate prior quarter paths')
    for item in entries:
        p=Path(item['completed_path']);ids=Path(item['eligible_ids_path'])
        require(digest(p)==item['completed_sha256'],'Prior completion hash differs')
        receipt=validate_source_completed(p.parent)
        require(receipt['quarter']==item['quarter'],'Prior quarter identity differs')
        require(ids.resolve()==(p.parent/'rebuilt/eligible_source_ids.parquet').resolve()
                and digest(ids)==item['eligible_ids_sha256'],'Prior ID inventory binding differs')
    return entries


def origination_diagnostic(source,quarter):
    """Original attributes only; retain hashes for nonstandard IDs, not identifiers."""
    bad={};loans={};h=hashlib.sha256();rows=0
    pattern=('F'+quarter[2:]+r'\d+').encode()
    with source.open('rb') as stream:
        for raw in stream:
            h.update(raw);rows+=1;r=raw.rstrip(b'\r\n').split(b'|')
            require(len(r)==31,'Release47 origination width mismatch')
            lid=r[19];key=hashlib.sha256(lid).hexdigest()
            fico,upb,ltv,rate,term=[finite(r[i]) for i in (0,10,11,12,21)]
            eligible=(r[15]==b'FRM' and upb is not None and upb>0 and ltv is not None and 1<=ltv<=200
                      and fico is not None and 300<=fico<=850 and term==360 and rate is not None and 0<rate<30)
            if not re.fullmatch(pattern,lid):
                require(re.fullmatch(rb'F(17|18|19|20|21)Q[1-4]\d+',lid) is not None,'Malformed or out-of-scope origination identifier')
                require(key not in bad,'Duplicate exceptional original ID')
                bad[key]=dict(prefix=lid[:5].decode(),vintage=2000+int(lid[1:3]),eligible=bool(eligible),original_upb=upb if eligible else 0.)
            if eligible:
                require(lid not in loans,'Duplicate eligible original ID')
                loans[lid]=(upb,r[1].decode())
            if rows%200000==0:check_resources(source.parent)
    return dict(raw_sha256=h.hexdigest(),rows=rows,exceptions=bad),loans


def coverage_diagnostic(source,loans,source_hashes):
    """Decode balance validity only through cutoff, never future balances."""
    eligible={lid:data for lid,data in loans.items() if data[1]<='202205'}
    covered=set();minimum={};pre_cutoff=set();h=hashlib.sha256();rows=0
    with source.open('rb') as stream:
        for raw in stream:
            h.update(raw);rows+=1;r=raw.split(b'|',3);lid,month=r[:2]
            if month<=b'202509' and lid in loans:
                if lid not in pre_cutoff or (lid in eligible and lid not in covered):
                    old=minimum.get(lid)
                    if old is None or month<old:
                        balance=finite(r[2])
                        if balance is not None and balance>=0:
                            pre_cutoff.add(lid);minimum[lid]=month
                            if month<=b'202205':covered.add(lid)
            if rows%10000000==0:check_resources(source.parent);print('Coverage rows checked:',rows,flush=True)
    require(h.hexdigest()==source_hashes['performance'],'Coverage source hash differs')
    require(len(pre_cutoff)==len(loans),'Eligible original sources lack valid pre-cutoff performance coverage')
    missing=set(eligible)-covered
    first=Counter(loans[lid][1] for lid in missing);observed=Counter(minimum[lid].decode() for lid in missing)
    return dict(source_sha256=source_hashes,missing_loans=len(missing),unknown_original_upb=sum(loans[lid][0] for lid in missing),
        original_first_payment=dict(first),first_valid_performance=dict(observed),
        missing_id_sha256=sorted(hashlib.sha256(lid).hexdigest() for lid in missing),
        post_cutoff_balances_decoded=False,performance_rows=rows)


def validate_archive_completed(output,*,verify_inputs=True):
    output=Path(output);require(not (output/'failed.json').exists(),'Failed archive run cannot validate')
    receipt=json.loads((output/'completed.json').read_text());quarter=receipt.get('quarter')
    require(quarter in QUARTERS and receipt.get('status')=='complete'
            and receipt.get('storage_policy')=='annual_archive_retained'
            and receipt.get('source_layout')=='release47','Invalid annual archive completion identity')
    required={'diagnostic_freeze.json','input_manifest.json','origination_diagnostic.json','schema_strict.json','schema.json',
        'coverage_diagnostic.json','identity_record.json','coverage_record.json','source_hashes_after.json','resources.json',
        'spec_frozen.md','layout_workbook.xlsx','prior_manifest.json','rebuilt/report.json'}
    required|={'rebuilt/'+name for name in ARTIFACTS}|{'executed_code/'+name for name in CODE_FILES}
    actual={str(p.relative_to(output)) for p in output.rglob('*') if p.is_file() and p.name!='completed.json'}
    require(required.issubset(actual) and set(receipt['output_sha256'])==actual,'Incomplete archive evidence/code coverage')
    for name,expected in receipt['output_sha256'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts,'Unsafe output artifact path')
        require(digest(output/name)==expected,'Archive output artifact hash differs: '+name)
    m=json.loads((output/'input_manifest.json').read_text());s=json.loads((output/'schema.json').read_text());r=json.loads((output/'rebuilt/report.json').read_text())
    for obj in (m,r,receipt):
        require(obj.get('quarter')==quarter and obj.get('cutoff')=='202509','Archive quarter/cutoff identity differs')
    for obj in (m,r):
        require(obj.get('snapshot_month')=='202205' and obj.get('transition_end')=='202205','Archive snapshot/transition cutoff differs')
    require(m['source_layout']==r['source_layout']==s['source_layout']==source_layout_metadata('release47'),'Archive physical layout differs')
    require(r['source_semantics_version']==s['source_semantics_version']==receipt['source_semantics_version']==source_semantics_version('release47'),'Archive semantics differ')
    require(set(Path(p).name for p in m['code_sha256'])==set(CODE_FILES) and len(m['code_sha256'])==len(CODE_FILES),'Incomplete archive code freeze')
    for name,expected in m['code_sha256'].items():require(digest(output/'executed_code'/Path(name).name)==expected,'Archived code differs')
    if verify_inputs:verify_hashes(m['input_sha256'])
    for name,expected in m['evidence_sha256'].items():require(digest(output/name)==expected,'Frozen diagnostic evidence differs')
    hashes={k:s[k]['sha256'] for k in ('origination','performance')}
    require(s['passed'] is True and r['source_sha256']==hashes==json.loads((output/'source_hashes_after.json').read_text()),'Archive schema/stream source hash differs')
    require(set(r['artifacts'])==ARTIFACTS,'Incomplete archive rebuilt artifacts')
    for name,item in r['artifacts'].items():require(digest(output/'rebuilt'/name)==item['sha256'],'Rebuilt artifact hash differs')
    require(r['counts']['origination_rows']==s['origination']['rows'] and r['counts']['performance_rows']==s['performance']['rows']
        and r['counts']['eligible_original_ids']==s['origination']['eligible_360_month_ids'],'Schema/stream population differs')
    require(r['zero_note_rate_exclusions']==s['origination']['zero_note_rate_exclusions'],'Zero-rate exclusions differ')
    require(r['identity_exceptions']==s['identity_exceptions'],'Identity exception counts differ')
    proof=r['cutoff_proof'];require(proof['post_cutoff_outcomes_decoded']==0 and proof['outcome_filter_precedes_decode'] is True
        and (proof['latest_decoded_month'] is None or proof['latest_decoded_month']<='202509'),'Archive outcome cutoff failed')
    require(r['counts']['semantic_rows_validated']==r['counts']['eligible_pre_cutoff_rows'],'Incomplete source semantic validation')
    require(receipt.get('eligible_overlap_check_passed') is True,'Missing eligible overlap proof')
    previous=validate_prior(output/'prior_manifest.json',quarter)
    check_overlap(previous,set(),pl.read_parquet(output/'rebuilt/eligible_source_ids.parquet'))
    coverage=json.loads((output/'coverage_record.json').read_text()).get('record')
    validate_audit(coverage,r,output)
    resources=json.loads((output/'resources.json').read_text());require(resources['peak_rss_bytes']<8*1024**3 and resources['free_disk_bytes']>=12*1024**3,'Archive resource threshold failed')
    return receipt


def run(*,annual_zip,quarter,prior_manifest,layout_workbook,output):
    annual_zip,prior_manifest,layout_workbook,output=[Path(x).resolve() for x in (annual_zip,prior_manifest,layout_workbook,output)]
    require(quarter in ('2021Q2','2021Q3','2021Q4'),'Only remaining2021 quarters authorized')
    if output.exists():raise FileExistsError('Preserve previous attempt; select a new output')
    output.mkdir(parents=True,mode=0o700)
    try:
        initial=check_resources(output)
        inputs={str(p):digest(p) for p in (annual_zip,prior_manifest,layout_workbook,SPEC)}
        code={str(HERE/name):digest(HERE/name) for name in CODE_FILES}
        orig,perf=[ArchiveMember(annual_zip,quarter,kind) for kind in ('origination','performance')]
        meta={k:s.metadata() for k,s in [('origination',orig),('performance',perf)]}
        previous=validate_prior(prior_manifest,quarter)
        for item in previous:
            inputs[item['completed_path']]=item['completed_sha256'];inputs[item['eligible_ids_path']]=item['eligible_ids_sha256']
        (output/'executed_code').mkdir()
        for name in CODE_FILES:shutil.copy2(HERE/name,output/'executed_code'/name)
        shutil.copy2(SPEC,output/'spec_frozen.md');shutil.copy2(layout_workbook,output/'layout_workbook.xlsx');shutil.copy2(prior_manifest,output/'prior_manifest.json')
        write_json(output/'diagnostic_freeze.json',dict(quarter=quarter,cutoff='202509',input_sha256=inputs,code_sha256=code,archive_members=meta))
        print(quarter,'original attribute diagnostic starting',flush=True)
        diag,loans=origination_diagnostic(orig,quarter);write_json(output/'origination_diagnostic.json',diag)
        check_overlap(previous,set(),pl.DataFrame({'loan_sequence_number':[lid.decode() for lid in loans]}))
        strict,_=schema_audit(orig,perf,quarter=quarter,exclude_zero_note_rate=True,source_layout='release47')
        write_json(output/'schema_strict.json',strict)
        require(diag['raw_sha256']==strict['origination']['sha256'],'Original diagnostic source changed')
        hashes={k:strict[k]['sha256'] for k in ('origination','performance')};identity=None
        if diag['exceptions']:
            require(strict['origination']['invalid_id_positions']==len(diag['exceptions']),'Identity diagnostic count differs')
            identity=dict(quarter=quarter,allowed_id_sha256=sorted(diag['exceptions']),source_sha256=hashes,
                expected=dict(original_records=len(diag['exceptions']),performance_rows=strict['performance']['invalid_id_positions'],
                    eligible_original_loans=sum(x['eligible'] for x in diag['exceptions'].values()),eligible_original_upb=sum(x['original_upb'] for x in diag['exceptions'].values())),
                allowed_id_prefixes={h:v['prefix'] for h,v in diag['exceptions'].items()},cohort_vintage_by_id_sha256={h:v['vintage'] for h,v in diag['exceptions'].items()})
            IdentityExceptions(quarter,identity)
            schema,_=schema_audit(orig,perf,quarter=quarter,exclude_zero_note_rate=True,identity_exceptions=identity,source_layout='release47')
        else:schema=strict
        write_json(output/'identity_record.json',dict(record=identity));write_json(output/'schema.json',schema)
        require(schema['passed'],'Archive schema/identity/date gate failed')
        require({k:schema[k]['sha256'] for k in hashes}==hashes,'Source changed between schema passes')
        print(quarter,'schema passed; valid-balance coverage diagnostic starting',flush=True)
        coverage_diag=coverage_diagnostic(perf,loans,hashes);write_json(output/'coverage_diagnostic.json',coverage_diag)
        coverage=None
        if coverage_diag['missing_loans']:
            coverage=dict(policy=POLICY,quarter=quarter,source_sha256=hashes,
                expected_missing_loans=coverage_diag['missing_loans'],expected_missing_original_upb=coverage_diag['unknown_original_upb'],
                expected_original_first_payment=coverage_diag['original_first_payment'],expected_first_valid_performance=coverage_diag['first_valid_performance'])
        write_json(output/'coverage_record.json',dict(record=coverage))
        evidence={name:digest(output/name) for name in ('diagnostic_freeze.json','origination_diagnostic.json','schema_strict.json','schema.json','identity_record.json','coverage_diagnostic.json','coverage_record.json','spec_frozen.md','layout_workbook.xlsx','prior_manifest.json')}
        manifest=dict(quarter=quarter,cutoff='202509',snapshot_month='202205',transition_end='202205',storage_policy='annual_archive_retained',
            source_layout=source_layout_metadata('release47'),input_sha256=inputs,code_sha256=code,evidence_sha256=evidence,archive_members=meta,
            environment=dict(python=sys.version,polars=pl.__version__),parameter_selection_performed=False)
        write_json(output/'input_manifest.json',manifest);verify_hashes(dict(inputs,**code))
        for name,expected in evidence.items():require(digest(output/name)==expected,'Diagnostic evidence changed before outcomes')
        print(quarter,'bounded outcome reconstruction starting',flush=True)
        del loans
        report=build_quarter(orig,perf,output/'rebuilt',quarter,cutoff='202509',transition_end='202205',exclude_zero_note_rate=True,
            allow_partial_cohort_overrun=True,identity_exceptions=identity,coverage_exception=coverage,source_layout='release47')
        check_overlap(previous,set(),pl.read_parquet(output/'rebuilt/eligible_source_ids.parquet'))
        verify_hashes(dict(inputs,**code))
        require(report['source_sha256']==hashes,'Schema/stream source changed')
        write_json(output/'source_hashes_after.json',hashes)
        final=check_resources(output);write_json(output/'resources.json',dict(peak_rss_bytes=max(initial['peak_rss_bytes'],final['peak_rss_bytes']),free_disk_bytes=min(initial['free_disk_bytes'],final['free_disk_bytes'])))
        receipt=dict(status='complete',quarter=quarter,cutoff='202509',storage_policy='annual_archive_retained',source_layout='release47',
            source_semantics_version=source_semantics_version('release47'),source_inputs_unchanged=True,eligible_overlap_check_passed=True,
            created_utc=datetime.now(timezone.utc).isoformat(),output_sha256={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()})
        write_json(output/'completed.json',receipt);validate_archive_completed(output)
        print(quarter,'completed and verified',flush=True);return receipt
    except BaseException as exc:
        if (output/'completed.json').exists():(output/'completed.json').unlink()
        write_json(output/'failed.json',dict(error_type=type(exc).__name__,error=str(exc),quarter=quarter,status='failed',archive_retained=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('annual-zip','quarter','prior-manifest','layout-workbook','output'):p.add_argument('--'+key,required=True,type=Path if key!='quarter' else str)
    run(**vars(p.parse_args()))
