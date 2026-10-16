"""Serial, resumable local-source rebuild with verified cloud-safe eviction.

Only the exact declared pair is materialized. Workers never modify originals;
the parent verifies output/source hashes and evicts through FileManager before
another quarter can start. A failed gate stops the sequence.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from schema import SOURCE_SEMANTICS_VERSION, ARCHIVE_SOURCE_SEMANTICS_VERSIONS

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/Users/eugene/Library/CloudStorage/GoogleDrive-eugeneo@andrew.cmu.edu/My Drive/Fannie and Freddie MAC')
SPEC = ROOT/'specs/SPEC_2026-10-11_source_rebuild.md'
ELIGIBILITY_CLARIFICATION = ROOT/'specs/SPEC_2026-10-11_source_rebuild_zero_rate_clarification.md'
CASH_RATIO_CLARIFICATION = ROOT/'specs/SPEC_2026-10-12_quarter_cash_ratio.md'
IDENTITY_CLARIFICATION = ROOT/'specs/SPEC_2026-10-12_source_identity_clarification.md'
OUTPUT = ROOT/'output/research-rebuild/2026-10-11'
QUARTERS = [f'{y}Q{q}' for y in range(2017,2022) for q in range(1,5)]
GIB = 1024**3
CORE_CODE_FILES = ['run_freddie_rebuild.py', 'freddie_rebuild_stream.py',
                   'freddie_raw_quarter_audit.py', 'ingest.py', 'loan_sample.py', 'markov.py']
REBUILT_ARTIFACTS = ['panel.parquet', 'cohort_history.parquet', 'snapshot.parquet',
                     'eligible_source_ids.parquet', 'transition_counts.parquet']
COMPARISON_COLUMNS = ['exposure_upb', 'orig_upb_sum', 'prepaid_upb', 'finite_age_sum',
                      'finite_age_count', 'loan_count', 'cohort_original_upb',
                      'mean_loan_age', 'burnout', 'monthly_prepay_rate']
AUDIT_FILES = ['schema.json', 'source_hashes_after.json', 'execution_freeze.json',
               'worker_passed.json', 'cleanup.json', 'source_metadata_at_worker_start.json',
               'resources.json', 'spec_frozen.md', 'rebuilt/report.json']


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):
            h.update(block)
    return h.hexdigest()


def file_info(path):
    s=path.stat()
    return dict(path=str(path),size=s.st_size,mtime_ns=s.st_mtime_ns,
                allocated_bytes=s.st_blocks*512,flags=getattr(s,'st_flags',0))


def provider_flags(text):
    names=['isDownloaded','isTrashed','isUploaded']
    out={}
    for name in names:
        values=re.findall(r'\b'+name+r'\s*=\s*([01])\b',text)
        if len(values)!=1:
            raise ValueError('Missing or ambiguous File Provider state: '+name)
        out[name]=int(values[0])
    return out


def verify_cleanup_receipt(receipt):
    if len(receipt.get('files',[])) != 2:
        raise ValueError('Cleanup needs both original source files')
    for f in receipt['files']:
        if (f.get('isDownloaded') != 0 or f.get('isTrashed') != 0 or f.get('isUploaded') != 1
                or f.get('allocated_bytes') != 0 or not f.get('exists')):
            raise ValueError('Cloud-safe cleanup is not verified')


def cleanup(paths, destination):
    swift='''import Foundation
for path in CommandLine.arguments.dropFirst() {
  try FileManager.default.evictUbiquitousItem(at: URL(fileURLWithPath: path))
  print("Eviction requested")
}
'''
    helper=destination/'evict.swift'
    helper.write_text(swift)
    r=subprocess.run(['/usr/bin/swift',str(helper),*[str(p) for p in paths]],
                     capture_output=True,text=True,timeout=60)
    (destination/'eviction.log').write_text(r.stdout+r.stderr)
    if r.returncode:
        raise RuntimeError('FileManager eviction failed; see local eviction.log')
    deadline=time.monotonic()+90
    while True:
        records=[]
        for p in paths:
            state=subprocess.run(['/usr/bin/fileproviderctl','evaluate',str(p)],
                                 capture_output=True,text=True,timeout=45)
            (destination/(p.stem+'_provider.txt')).write_text(state.stdout+state.stderr)
            if state.returncode:
                raise RuntimeError('File Provider state check failed')
            records.append(dict(file_info(p),exists=p.exists(),**provider_flags(state.stdout)))
        receipt=dict(method='FileManager.evictUbiquitousItem; no deletion',files=records,
                     verified_utc=datetime.now(timezone.utc).isoformat())
        try:
            verify_cleanup_receipt(receipt)
            write_json(destination/'cleanup.json',receipt)
            return receipt
        except ValueError:
            if time.monotonic()>=deadline:
                write_json(destination/'cleanup_unverified.json',receipt)
                raise
            time.sleep(3)


def load_identity_record(root, quarter):
    """Validate only local frozen identity evidence; never reopen a source."""
    root = Path(root)
    manifest = root/'identity_exceptions_frozen.json'
    if not manifest.exists():
        return None
    record = json.loads(manifest.read_text()).get(quarter)
    if record is None:
        return None
    from freddie_raw_quarter_audit import IdentityExceptions
    IdentityExceptions(quarter, record)
    clarification = root/'identity_clarification_frozen.md'
    if (clarification.read_bytes() != IDENTITY_CLARIFICATION.read_bytes()
            or digest(clarification) != record.get('clarification_sha256')):
        raise ValueError('Frozen identity clarification differs')
    evidence = record.get('evidence_sha256', {})
    if not isinstance(evidence, dict) or not evidence:
        raise ValueError('Frozen identity exception requires diagnostic evidence')
    for name, expected in evidence.items():
        path = (root/name).resolve()
        if root.resolve() not in path.parents or digest(path) != expected:
            raise ValueError('Frozen identity diagnostic evidence differs')
    return record


def freeze_identity_record(root, destination, quarter, record):
    if record is None:
        return {}
    if record != load_identity_record(root, quarter):
        raise ValueError('Identity record changed before freeze')
    shutil.copy2(root/'identity_exceptions_frozen.json', destination/'identity_manifest.json')
    shutil.copy2(root/'identity_clarification_frozen.md', destination/'identity_clarification.md')
    write_json(destination/'identity_exception.json', record)
    archive = destination/'identity_evidence'
    archive.mkdir()
    hashes = {}
    for index, (name, expected) in enumerate(sorted(record['evidence_sha256'].items())):
        target = archive/f'{index:02d}.json'
        shutil.copy2(root/name, target)
        hashes[str(target.relative_to(destination))] = expected
    return dict(identity_manifest_sha256=digest(destination/'identity_manifest.json'),
        identity_exception_sha256=digest(destination/'identity_exception.json'),
        identity_clarification_sha256=digest(destination/'identity_clarification.md'),
        identity_evidence_sha256=hashes)


def validate_identity_freeze(destination, freeze):
    if not freeze.get('identity_exception_sha256'):
        return None
    root = destination.parent.parent
    record = load_identity_record(root, destination.name)
    if record is None:
        raise ValueError('Frozen identity exception disappeared')
    names = {'identity_manifest.json': 'identity_manifest_sha256',
             'identity_exception.json': 'identity_exception_sha256',
             'identity_clarification.md': 'identity_clarification_sha256'}
    for name, key in names.items():
        if digest(destination/name) != freeze.get(key):
            raise ValueError('Frozen identity copy changed: '+name)
    expected_evidence = {f'identity_evidence/{i:02d}.json': value
                        for i, (_, value) in enumerate(sorted(record['evidence_sha256'].items()))}
    if (digest(root/'identity_exceptions_frozen.json') != freeze['identity_manifest_sha256']
            or json.loads((destination/'identity_exception.json').read_text()) != record
            or freeze.get('identity_evidence_sha256') != expected_evidence
            or digest(root/'identity_clarification_frozen.md') != freeze['identity_clarification_sha256']):
        raise ValueError('Frozen identity manifest or evidence binding changed')
    for name, expected in expected_evidence.items():
        if digest(destination/name) != expected:
            raise ValueError('Frozen identity evidence copy changed')
    return record


def expected_identity_audit(record):
    if record is None:
        return None
    return dict(enabled=True, quarter=record['quarter'], allowed_id_sha256=record['allowed_id_sha256'],
                source_sha256=record['source_sha256'], **record['expected'])


def freeze_coverage_record(root, destination, quarter):
    path=Path(root)/'coverage_exceptions_frozen.json'
    if not path.exists(): return {}
    record=json.loads(path.read_text()).get(quarter)
    if record is None: return {}
    if record.get('quarter')!=quarter:
        raise ValueError('Coverage record quarter mismatch')
    for name,expected in record.get('evidence_sha256',{}).items():
        if Path(name).name!=name or digest(Path(root)/name)!=expected:
            raise ValueError('Coverage evidence must be frozen before source access')
        shutil.copy2(Path(root)/name,Path(destination)/name)
    write_json(Path(destination)/'coverage_exception.json',record)
    return {'coverage_exception_sha256':digest(Path(destination)/'coverage_exception.json')}


def worker(quarter, source, destination):
    from freddie_raw_quarter_audit import schema_audit, check_resources
    from freddie_rebuild_stream import build_quarter
    orig,perf=[source/f'{kind}_{quarter}.txt' for kind in ['orig','perf']]
    freeze=json.loads((destination/'execution_freeze.json').read_text())
    identity = validate_identity_freeze(destination, freeze)
    from coverage_exception import frozen_record
    coverage=frozen_record(destination,freeze,digest)
    clarified=freeze.get('eligibility_clarification_sha256')
    if clarified and digest(destination/'eligibility_clarification.md')!=clarified:
        raise ValueError('Eligibility clarification must be frozen before source access')
    cash_clarified=freeze.get('cash_ratio_clarification_sha256')
    if cash_clarified and digest(destination/'cash_ratio_clarification.md')!=cash_clarified:
        raise ValueError('Cash-ratio clarification must be frozen before source access')
    schema_path=destination/'schema.json'
    if schema_path.exists():
        schema=json.loads(schema_path.read_text())
    else:
        schema,_=schema_audit(orig,perf,quarter=quarter,exclude_zero_note_rate=bool(clarified),
                              identity_exceptions=identity)
        write_json(schema_path,schema)
    if not schema['passed']:
        raise ValueError('Schema/identity gate failed before outcome processing')
    if schema.get('source_semantics_version') != SOURCE_SEMANTICS_VERSION:
        raise ValueError('Fresh native source semantics gate required before outcome processing')
    if schema.get('identity_exceptions') != expected_identity_audit(identity):
        raise ValueError('Schema identity exception does not match the frozen record')
    check_resources(destination)
    report=build_quarter(orig,perf,destination/'rebuilt',quarter=quarter,exclude_zero_note_rate=bool(clarified),
        allow_partial_cohort_overrun=bool(cash_clarified),identity_exceptions=identity,coverage_exception=coverage)
    if quarter == '2017Q1':
        # Independent vectorized implementation over the same declared 360-month
        # population. This first-quarter check is bounded by the parent watchdog.
        import numpy as np
        import polars as pl
        from ingest import build_panel_from_files
        production=build_panel_from_files([(orig,perf)],destination/'production_cells_360.parquet',
                                          term_months=360,reporting_end='202509')
        keys=['vintage','coupon','fico_bucket','ltv_bucket','reporting_period']
        reference=pl.read_parquet(destination/'rebuilt/panel.parquet').sort(keys)
        production=production.sort(keys)
        if not reference.select(keys).equals(production.select(keys)):
            raise ValueError('Streaming/production cohort membership differs')
        checks={}
        for name in COMPARISON_COLUMNS:
            a,b=reference[name].to_numpy(),production[name].to_numpy()
            ok=bool(np.allclose(a,b,rtol=1e-10,atol=1e-5,equal_nan=True))
            checks[name]=dict(passed=ok,max_absolute_difference=float(np.nanmax(abs(a-b))))
            if not ok:
                write_json(destination/'production_comparison.json',checks)
                raise ValueError('Streaming/production mismatch: '+name)
        write_json(destination/'production_comparison.json',dict(passed=True,rows=reference.height,checks=checks,
            mode_state_excluded='Tie-breaking is a declared diagnostic; identified transitions do not use cohort modes'))
    after={kind:digest(p) for kind,p in [('origination',orig),('performance',perf)]}
    write_json(destination/'source_hashes_after.json',after)
    if any(after[k]!=schema[k]['sha256'] for k in after):
        raise ValueError('Source bytes changed between schema and rebuilt outputs')
    write_json(destination/'worker_passed.json',dict(source_hashes=after,report=report))


def stop_worker(proc):
    """Reap before source eviction, including monitoring failures/interrupts."""
    if proc is None or proc.poll() is not None:
        return
    try:
        proc.terminate()
        proc.wait(timeout=20)
    except (subprocess.TimeoutExpired, OSError):
        try:
            proc.kill()
            proc.wait(timeout=20)
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise RuntimeError('Cannot reap worker; source eviction is prohibited') from exc
    if proc.poll() is None:
        raise RuntimeError('Cannot reap worker; source eviction is prohibited')


def required_evidence(destination):
    freeze=json.loads((destination/'execution_freeze.json').read_text())
    code=freeze.get('code_sha256',{})
    if not set(CORE_CODE_FILES).issubset(code) or any(Path(n).name!=n for n in code):
        raise ValueError('Incomplete or invalid executed-code manifest')
    names=AUDIT_FILES+['rebuilt/'+n for n in REBUILT_ARTIFACTS]+['executed_code/'+n for n in code]
    if freeze.get('eligibility_clarification_sha256'):
        names+=['eligibility_clarification.md']
    if freeze.get('cash_ratio_clarification_sha256'):
        names+=['cash_ratio_clarification.md']
    if freeze.get('identity_exception_sha256'):
        names+=['identity_manifest.json','identity_exception.json','identity_clarification.md']
        names+=list(freeze.get('identity_evidence_sha256',{}))
    if freeze.get('coverage_exception_sha256'):
        from coverage_exception import frozen_record
        coverage=frozen_record(destination,freeze,digest)
        names+=['coverage_exception.json']+list(coverage['evidence_sha256'])
    if destination.name=='2017Q1':
        names+=['production_comparison.json','production_cells_360.parquet']
    return names


def validate_evidence(destination):
    """Cross-check saved evidence without reopening a cloud source."""
    read=lambda name:json.loads((destination/name).read_text())
    quarter=destination.name
    if quarter not in QUARTERS:
        raise ValueError('Unexpected completed source quarter')
    freeze=read('execution_freeze.json'); schema=read('schema.json')
    identity = validate_identity_freeze(destination, freeze)
    report=read('rebuilt/report.json'); worker_record=read('worker_passed.json')
    after=read('source_hashes_after.json'); receipt=read('cleanup.json')
    resources=read('resources.json')
    if (freeze.get('quarter')!=quarter or report.get('quarter')!=quarter
            or freeze.get('cutoff')!='202509' or report.get('cutoff')!='202509'
            or freeze.get('transition_end')!='202205' or report.get('transition_end')!='202205'
            or report.get('snapshot_month')!='202205'):
        raise ValueError('Quarter/cutoff identity mismatch')
    spec_sha=digest(destination/'spec_frozen.md')
    if freeze.get('spec_sha256')!=spec_sha or digest(destination.parent.parent/'spec_frozen.md')!=spec_sha:
        raise ValueError('Frozen specification mismatch')
    clarification=freeze.get('eligibility_clarification_sha256')
    if clarification and (digest(destination/'eligibility_clarification.md')!=clarification
            or digest(destination.parent.parent/'eligibility_clarification_frozen.md')!=clarification):
        raise ValueError('Frozen eligibility clarification mismatch')
    cash_clarification=freeze.get('cash_ratio_clarification_sha256')
    if cash_clarification and (digest(destination/'cash_ratio_clarification.md')!=cash_clarification
            or digest(destination.parent.parent/'cash_ratio_clarification_frozen.md')!=cash_clarification):
        raise ValueError('Frozen cash-ratio clarification mismatch')
    if schema.get('passed') is not True:
        raise ValueError('Schema audit did not pass')
    semantics = report.get('source_semantics_version')
    if semantics is not None and (semantics not in ARCHIVE_SOURCE_SEMANTICS_VERSIONS
            or schema.get('source_semantics_version') != semantics
            or report['counts'].get('semantic_rows_validated') != report['counts'].get('eligible_pre_cutoff_rows')
            or report['counts'].get('semantic_rows_validated') is None):
        raise ValueError('Native source semantics evidence is missing or inconsistent')
    before_hashes={k:schema[k]['sha256'] for k in ['origination','performance']}
    from coverage_exception import frozen_record, validate_audit
    coverage=frozen_record(destination,freeze,digest)
    validate_audit(coverage,report,destination)
    expected_identity = expected_identity_audit(identity)
    if (schema.get('identity_exceptions') != expected_identity
            or report.get('identity_exceptions') != expected_identity
            or (identity and before_hashes != identity['source_sha256'])):
        raise ValueError('Schema/stream identity exception accounting disagrees with its freeze')
    if (after!=before_hashes or report.get('source_sha256')!=after
            or worker_record.get('source_hashes')!=after or worker_record.get('report')!=report
            or any(not re.fullmatch('[0-9a-f]{64}',h) for h in after.values())):
        raise ValueError('Before/streamed/after source evidence disagrees')
    for key,source_key in [('origination_rows','origination'),('performance_rows','performance')]:
        if report['counts'][key]!=schema[source_key]['rows']:
            raise ValueError('Schema/stream row counts disagree')
    if report['counts']['eligible_original_ids']!=schema['origination']['eligible_360_month_ids']:
        raise ValueError('Schema/stream eligible population disagrees')
    zero_rates=report.get('zero_note_rate_exclusions')
    if zero_rates!=schema['origination'].get('zero_note_rate_exclusions'):
        raise ValueError('Schema/stream zero-rate exclusion accounting disagrees')
    if zero_rates and zero_rates.get('enabled')!=bool(clarification):
        raise ValueError('Zero-rate exclusions require the frozen eligibility clarification')
    if clarification and not zero_rates:
        raise ValueError('Missing zero-rate exclusion accounting')
    cash_audit=report.get('quarter_cash_ratio_audit')
    if cash_audit and cash_audit.get('partial_cohort_overrun_enabled')!=bool(cash_clarification):
        raise ValueError('Partial-cohort exceptions require their frozen clarification')
    if cash_clarification and not cash_audit:
        raise ValueError('Missing partial-cohort cash-ratio audit')
    if cash_audit:
        overruns=cash_audit.get('overruns',[])
        if cash_audit.get('overrun_cohort_count')!=len(overruns) or (overruns and not cash_clarification):
            raise ValueError('Inconsistent partial-cohort cash-ratio accounting')
        for item in overruns:
            original=item.get('original_upb',0);paid=item.get('cumulative_prepaid_upb',0);ratio=item.get('peak_ratio',0)
            if (not all(math.isfinite(v) for v in [original,paid,ratio]) or original<=0 or ratio<=1
                    or not math.isclose(paid/original,ratio,rel_tol=1e-10,abs_tol=1e-10)
                    or item.get('multiple_positive_payoff_loans')!=0 or item.get('terminal_revival_loans')!=0):
                raise ValueError('Unresolved partial-cohort cash-ratio evidence')
    proof=report.get('cutoff_proof',{})
    if (proof.get('post_cutoff_outcomes_decoded')!=0 or proof.get('outcome_filter_precedes_decode') is not True
            or not re.fullmatch(r'20\d{2}(0[1-9]|1[0-2])',proof.get('latest_decoded_month',''))
            or proof['latest_decoded_month']>'202509'):
        raise ValueError('Outcome cutoff proof failed')
    if set(report.get('artifacts',{}))!=set(REBUILT_ARTIFACTS):
        raise ValueError('Incomplete rebuilt artifact manifest')
    for name,artifact in report['artifacts'].items():
        if digest(destination/'rebuilt'/name)!=artifact['sha256']:
            raise ValueError('Rebuilt artifact changed: '+name)
    for name,expected in freeze['code_sha256'].items():
        if digest(destination/'executed_code'/name)!=expected:
            raise ValueError('Executed code changed: '+name)
    verify_cleanup_receipt(receipt)
    expected_paths={f'{kind}_{quarter}.txt' for kind in ['orig','perf']}
    initial=read('source_metadata_at_worker_start.json')
    if (len(initial)!=2 or {Path(f['path']).name for f in receipt['files']}!=expected_paths
            or {f['path'] for f in initial}!={f['path'] for f in receipt['files']}):
        raise ValueError('Cleanup source identity mismatch')
    initial_by_path={f['path']:f for f in initial}
    if any(f[k]!=initial_by_path[f['path']][k] for f in receipt['files'] for k in ['size','mtime_ns']):
        raise ValueError('Source metadata changed')
    if (resources.get('worker_reaped') is not True or not 0<resources.get('peak_rss_bytes',0)<=8*GIB
            or resources.get('free_disk_bytes_after',0)<12*GIB):
        raise ValueError('Resource/worker completion evidence failed')
    if quarter=='2017Q1':
        comparison=read('production_comparison.json')
        if (comparison.get('passed') is not True or set(comparison.get('checks',{}))!=set(COMPARISON_COLUMNS)
                or not all(v.get('passed') is True for v in comparison['checks'].values())
                or comparison.get('rows')!=report['artifacts']['panel.parquet']['rows']):
            raise ValueError('First-quarter independent comparison failed')
    return receipt,resources


def seal_completion(destination):
    destination=Path(destination)
    if (destination/'completed.json').exists():
        raise FileExistsError('Preserve the existing completion before resealing')
    names=required_evidence(destination)
    hashes={name:digest(destination/name) for name in names}
    receipt,resources=validate_evidence(destination)
    record=dict(manifest_version=2,quarter=destination.name,status='completed',
        peak_rss_bytes=resources['peak_rss_bytes'],cleanup=receipt,
        spec_sha256=digest(destination/'spec_frozen.md'),
        completed_utc=datetime.now(timezone.utc).isoformat(),output_sha256=hashes)
    write_json(destination/'completed.json',record)
    return record


def validate_completed(destination):
    destination=Path(destination)
    record=json.loads((destination/'completed.json').read_text())
    if (record.get('manifest_version')!=2 or record.get('status')!='completed'
            or record.get('quarter')!=destination.name):
        raise ValueError('Incomplete completion manifest or quarter mismatch')
    names=required_evidence(destination)
    if set(record.get('output_sha256',{}))!=set(names):
        raise ValueError('Incomplete required output/audit evidence')
    for name,expected in record['output_sha256'].items():
        if digest(destination/name)!=expected:
            raise ValueError('Completed output or audit evidence changed: '+name)
    receipt,resources=validate_evidence(destination)
    if (record.get('cleanup')!=receipt or record.get('peak_rss_bytes')!=resources['peak_rss_bytes']
            or record.get('spec_sha256')!=digest(destination/'spec_frozen.md')):
        raise ValueError('Completion record disagrees with audit evidence')
    return record


def run_quarter(quarter, source=SOURCE, output=OUTPUT):
    if quarter not in QUARTERS:
        raise ValueError('Quarter must be in the frozen 2017–2021 source manifest')
    source=Path(source);output=Path(output)
    destination=output/'quarters'/quarter
    destination.mkdir(parents=True,exist_ok=True)
    if (destination/'completed.json').exists():
        result = validate_completed(destination)
        if json.loads((destination/'rebuilt/report.json').read_text()).get('source_semantics_version') != SOURCE_SEMANTICS_VERSION:
            raise ValueError('Earlier source semantics are archive-only; rebuild in a separate root')
        return result
    # A prior failed extraction must be inspected, not overwritten on resume.
    if (destination/'rebuilt').exists() or (destination/'failed.json').exists():
        raise FileExistsError('Prior attempt requires audit; use a separate output root')
    frozen=output/'spec_frozen.md'
    if not frozen.exists() or frozen.read_bytes()!=SPEC.read_bytes():
        raise ValueError('Current specification must match pre-access frozen copy')
    clarification=output/'eligibility_clarification_frozen.md'
    if not clarification.exists() or clarification.read_bytes()!=ELIGIBILITY_CLARIFICATION.read_bytes():
        raise ValueError('Eligibility clarification must match its pre-access frozen copy')
    cash_clarification=output/'cash_ratio_clarification_frozen.md'
    if not cash_clarification.exists() or cash_clarification.read_bytes()!=CASH_RATIO_CLARIFICATION.read_bytes():
        raise ValueError('Cash-ratio clarification must match its pre-access frozen copy')
    identity = load_identity_record(output, quarter)
    paths=[source/f'{kind}_{quarter}.txt' for kind in ['orig','perf']]
    if shutil.disk_usage(output).free < 12*GIB + sum(p.stat().st_size for p in paths):
        raise RuntimeError('Insufficient headroom for the declared pair plus 12 GiB reserve')
    # Metadata-only: never materialize another quarter before this one is closed.
    others=[p for p in source.glob('*.txt') if p not in paths and p.stat().st_blocks>0]
    if others:
        raise RuntimeError('Another source pair is materialized; verify its cleanup first')
    before=[file_info(p) for p in paths]
    write_json(destination/'source_metadata_at_worker_start.json',before)
    code_files=CORE_CODE_FILES+['config.py','schema.py','coverage_exception.py']
    code_archive=destination/'executed_code';code_archive.mkdir()
    for name in code_files:
        shutil.copy2(ROOT/'hazard'/name,code_archive/name)
    shutil.copy2(frozen,destination/'spec_frozen.md')
    shutil.copy2(clarification,destination/'eligibility_clarification.md')
    shutil.copy2(cash_clarification,destination/'cash_ratio_clarification.md')
    write_json(destination/'execution_freeze.json',dict(
        started_utc=datetime.now(timezone.utc).isoformat(),quarter=quarter,cutoff='202509',
        transition_end='202205',spec_sha256=digest(SPEC),python=sys.version,
        eligibility_clarification_sha256=digest(clarification),
        cash_ratio_clarification_sha256=digest(cash_clarification),
        **freeze_identity_record(output,destination,quarter,identity),
        **freeze_coverage_record(output,destination,quarter),
        code_sha256={n:digest(code_archive/n) for n in code_files}))
    error=None;peak_rss=0;proc=None
    try:
        env=dict(os.environ,POLARS_MAX_THREADS='2')
        with (destination/'worker.log').open('w') as log:
            proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--worker','--quarter',quarter,
                '--source',str(source),'--output',str(output)],stdout=log,stderr=subprocess.STDOUT,env=env)
            while proc.poll() is None:
                rss=subprocess.run(['ps','-o','rss=','-p',str(proc.pid)],capture_output=True,text=True).stdout.strip()
                peak_rss=max(peak_rss,int(rss or 0)*1024)
                if peak_rss>8*GIB or shutil.disk_usage(output).free<12*GIB:
                    raise RuntimeError('Resource stopping threshold reached')
                time.sleep(2)
            if proc.returncode:
                raise RuntimeError('Quarter worker failed; inspect worker.log before proceeding')
        after=[file_info(p) for p in paths]
        if any(a[k]!=b[k] for a,b in zip(after,before) for k in ['size','mtime_ns']):
            raise RuntimeError('Source metadata changed during rebuild')
        if any(digest(ROOT/'hazard'/n)!=digest(code_archive/n) for n in code_files):
            raise RuntimeError('Code changed during source processing; inspect the executed archive')
    except BaseException as exc:
        error=exc
    try:
        stop_worker(proc)
    except BaseException as exc:
        write_json(destination/'failed.json',dict(error=repr(error),worker_shutdown_error=repr(exc),
            cleanup='NOT ATTEMPTED: worker was not successfully reaped'))
        raise
    try:
        receipt=cleanup(paths,destination)
    except Exception as exc:
        write_json(destination/'failed.json',dict(error=str(error) if error else None,cleanup_error=str(exc)))
        raise
    if error:
        write_json(destination/'failed.json',dict(error=str(error),cleanup=receipt))
        raise error
    write_json(destination/'resources.json',dict(peak_rss_bytes=peak_rss,worker_reaped=True,
        free_disk_bytes_after=shutil.disk_usage(output).free))
    return seal_completion(destination)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--quarter',choices=QUARTERS)
    parser.add_argument('--source',type=Path,default=SOURCE)
    parser.add_argument('--output',type=Path,default=OUTPUT)
    parser.add_argument('--worker',action='store_true')
    args=parser.parse_args()
    if args.worker:
        worker(args.quarter,args.source,args.output/'quarters'/args.quarter)
    else:
        for quarter in ([args.quarter] if args.quarter else QUARTERS):
            print('Starting '+quarter,flush=True)
            result=run_quarter(quarter,args.source,args.output)
            print(quarter+': '+result['status']+'; cloud-only cleanup verified',flush=True)


if __name__=='__main__':
    main()
