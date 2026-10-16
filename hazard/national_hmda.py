"""Immutable, bounded national HMDA snapshots and descriptive cost views.

Raw Parquet columns are verbatim strings, including blank, NA and Exempt.
No jurisdiction, purpose or outcome filter is applied at ingestion. Analysis
uses the existing PA scope (purposes 31/32 and actions 1..5) explicitly.
DuckDB is optional until this workflow is called; install duckdb>=1.4.
"""
import argparse
from collections import Counter
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import gzip
import threading
import io
import json
from pathlib import Path
import shutil
import tempfile
import zipfile

from hazard.hmda_cost_profiles import BINS, MISSING, REQUIRED, number

VERSION='national-hmda-v1'
NUMERIC=('loan_amount','total_loan_costs','interest_rate','discount_points','lender_credits')
BASE="loan_type='1' AND lien_status='1' AND \"open-end_line_of_credit\"='2' AND reverse_mortgage='2'"
ALIASES={'open-end_line_of_credit':'open_end_line_of_credit'}
NARROW=BASE+" AND conforming_loan_limit='C' AND construction_method='1' AND total_units IN ('1','2','3','4') AND occupancy_type='1'"


def _sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def _lit(value):
    return "'"+str(value).replace("'","''")+"'"


def _ident(value):
    return '"'+value.replace('"','""')+'"'


def _gate(year, freeze_gate):
    if isinstance(year,bool) or not isinstance(year,int) or year not in range(2018,2026):
        raise ValueError('Expected integral year 2018..2025')
    if year<=2023:return None
    if not freeze_gate:raise ValueError('Held-out data require a freeze gate')
    p=Path(freeze_gate);g=json.loads(p.read_text())
    if (g.get('development_years')!=list(range(2018,2024)) or g.get('validation_year')!=2024 or
        g.get('final_evaluation_year')!=2025 or year not in g.get('allowed_years',[])):
        raise ValueError('Invalid freeze gate split or allowed years')
    artifact=Path(g.get('frozen_artifact',''))
    if not artifact.is_absolute():artifact=p.parent/artifact
    if not artifact.is_file() or _sha(artifact)!=g.get('frozen_sha256'):
        raise ValueError('Frozen artifact hash mismatch')
    if year==2025:
        validation=Path(g.get('validation_artifact',''))
        if not validation.is_absolute():validation=p.parent/validation
        if not validation.is_file() or _sha(validation)!=g.get('validation_sha256'):
            raise ValueError('Final evaluation requires hashed validation artifact')
    return {'gate_sha256':_sha(p),'frozen_sha256':g['frozen_sha256']}


def _connection(memory_limit='512MB',temp_directory=None,threads=1):
    if isinstance(threads,bool) or not isinstance(threads,int) or threads<1:raise ValueError('threads must be a positive integer')
    try:import duckdb
    except ImportError as e:raise RuntimeError('Install duckdb>=1.4 to use national HMDA snapshots') from e
    con=duckdb.connect()
    con.execute('SET memory_limit='+_lit(memory_limit))
    con.execute('SET threads='+str(threads))
    con.execute('SET preserve_insertion_order=false')
    if temp_directory:con.execute('SET temp_directory='+_lit(temp_directory))
    return con


@contextmanager
def _source(path,member):
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as z:
            names=[n for n in z.namelist() if n.lower().endswith('.csv') and not n.endswith('/')]
            if member is None:
                if len(names)!=1:raise ValueError('ZIP needs one CSV or explicit zip_member')
                member=names[0]
            if member not in names:raise ValueError('ZIP CSV member missing')
            with z.open(member) as f:
                with io.TextIOWrapper(f,encoding='utf-8-sig',newline='') as t:
                    yield t,member,z.getinfo(member).file_size
    else:
        if member:raise ValueError('zip_member supplied for non-ZIP source')
        with path.open(encoding='utf-8-sig',newline='') as f:yield f,None,path.stat().st_size


def ingest_snapshot(source, output_dir, *, year, source_url, publication_version,
                    expected_header=None, zip_member=None, freeze_gate=None,
                    batch_rows=50000, reserve_bytes=4*1024**3,
                    max_output_bytes=8*1024**3, memory_limit='512MB', fast_zip=False, threads=1):
    """Read one local year at a time; original source is never removed.

    Each bounded CSV batch becomes a Parquet part. A complete manifest is
    published only after every record has passed structural/year checks.
    Failed attempts retain parts plus failure.json and cannot be overwritten.
    """
    gate=_gate(year,freeze_gate)
    if isinstance(threads,bool) or not isinstance(threads,int) or threads<1:raise ValueError('threads must be a positive integer')
    if not source_url or not publication_version:raise ValueError('Source URL and publication version required')
    if batch_rows<=0 or reserve_bytes<0 or max_output_bytes<=0:raise ValueError('Invalid resource budget')
    source=Path(source);out=Path(output_dir)
    if out.exists():raise FileExistsError('Snapshot destination already exists')
    out.parent.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(out.parent).free<reserve_bytes:raise OSError('Disk reserve unavailable')
    out.mkdir();con=None
    try:
        if fast_zip:
            return _ingest_fast_zip(source,out,year=year,source_url=source_url,publication_version=publication_version,expected_header=expected_header,zip_member=zip_member,gate=gate,reserve_bytes=reserve_bytes,max_output_bytes=max_output_bytes,memory_limit=memory_limit,threads=threads)
        source_hash=_sha(source);initial=source.stat();states=Counter();actions=Counter();purposes=Counter();n=0;parts=[];written=0
        with _source(source,zip_member) as (stream,member,uncompressed):
            reader=csv.reader(stream,strict=True);header=next(reader,None)
            if (not header or len(header)!=len(set(header)) or any((k not in header and ALIASES.get(k) not in header) or (k in header and ALIASES.get(k) in header) for k in REQUIRED) or
                (expected_header is not None and header!=list(expected_header))):raise ValueError('Invalid or frozen source schema mismatch')
            indices={name:header.index(name) for name in ('activity_year','state_code','action_taken','loan_purpose')}
            with tempfile.TemporaryDirectory(prefix='.work-',dir=out) as work:
                con=_connection(memory_limit,work,threads=threads)
                chunk=Path(work)/'batch.csv';batch=[]
                def flush():
                    nonlocal written
                    free=shutil.disk_usage(out).free
                    estimated=sum(sum(len(v.encode('utf-8')) for v in r)+len(r)*3 for r in batch)+sum(map(len,header))+len(header)*3
                    # Bound simultaneous CSV plus Parquet/spill allowance before materializing.
                    if free<reserve_bytes+estimated*4:raise OSError('Disk reserve would be crossed by batch')
                    if written+estimated*2>max_output_bytes:raise OSError('Disk output budget would be crossed by batch')
                    with chunk.open('w',newline='') as f:
                        writer=csv.writer(f);writer.writerow(header);writer.writerows(batch)
                    dest=out/f'part-{len(parts):06d}.parquet'
                    schema='{'+','.join(_lit(k)+": 'VARCHAR'" for k in header)+'}'
                    con.execute('COPY (SELECT * FROM read_csv('+_lit(chunk)+', header=true, columns='+schema+", force_not_null=["+','.join(map(_lit,header))+"], strict_mode=true)) TO "+_lit(dest)+" (FORMAT PARQUET, COMPRESSION ZSTD)")
                    size=dest.stat().st_size;written+=size
                    if written>max_output_bytes or shutil.disk_usage(out).free<reserve_bytes:raise OSError('Disk budget exceeded')
                    parts.append({'path':dest.name,'bytes':size,'sha256':_sha(dest),'records':len(batch)})
                    chunk.unlink();batch.clear()
                for values in reader:
                    if len(values)!=len(header):raise ValueError('Malformed CSV row')
                    if values[indices['activity_year']]!=str(year):raise ValueError('Record year mismatch')
                    states[values[indices['state_code']]]+=1;actions[values[indices['action_taken']]]+=1;purposes[values[indices['loan_purpose']]]+=1
                    batch.append(values);n+=1
                    if len(batch)>=batch_rows:flush()
                if batch:flush()
                if not n:raise ValueError('Empty snapshot')
        if source.stat().st_size!=initial.st_size or source.stat().st_mtime_ns!=initial.st_mtime_ns or _sha(source)!=source_hash:
            raise ValueError('Source changed during ingest')
        m=dict(workflow_version=VERSION,workflow_sha256=_sha(__file__),year=year,split='development' if year<=2023 else ('validation' if year==2024 else 'final_evaluation'),source_url=source_url,publication_version=publication_version,source_path=str(source.resolve()),source_sha256=source_hash,source_bytes=initial.st_size,zip_member=member,uncompressed_bytes=uncompressed,record_count=n,header=header,analysis_aliases={k:v for k,v in ALIASES.items() if v in header},schema_sha256=hashlib.sha256(json.dumps(header,separators=(',',':')).encode()).hexdigest(),state_counts=dict(sorted(states.items())),action_counts=dict(sorted(actions.items())),purpose_counts=dict(sorted(purposes.items())),parquet_files=parts,parquet_bytes=written,raw_scope='all source records; jurisdiction/purpose/action unrestricted',source_completeness='local source integrity only; national completeness requires independent official counts',null_policy={'storage':'all VARCHAR; blank is empty string, no SQL NULL conversion','analysis_missing_codes':MISSING},freeze_gate=gate,resources=dict(batch_rows=batch_rows,threads=threads,memory_limit=memory_limit,reserve_bytes=reserve_bytes,max_output_bytes=max_output_bytes),created_utc=datetime.now(timezone.utc).isoformat(),model_parameters_changed=0)
        (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');return m
    except Exception as e:
        (out/'failure.json').write_text(json.dumps({'status':'incomplete_not_accepted','error':str(e)},indent=2)+'\n');raise
    finally:
        if con is not None:con.close()


def _ingest_fast_zip(source,out,*,year,source_url,publication_version,expected_header,zip_member,gate,reserve_bytes,max_output_bytes,memory_limit,threads):
    """Native CSV parsing; temporary gzip avoids a full uncompressed copy."""
    if not zipfile.is_zipfile(source):raise ValueError('fast_zip requires a ZIP source')
    source_hash=_sha(source);initial=source.stat()
    with zipfile.ZipFile(source) as z:
        names=[n for n in z.namelist() if n.lower().endswith('.csv') and not n.endswith('/')]
        if zip_member is None:
            if len(names)!=1:raise ValueError('ZIP needs one CSV or explicit zip_member')
            zip_member=names[0]
        if zip_member not in names:raise ValueError('ZIP CSV member missing')
        uncompressed=z.getinfo(zip_member).file_size
        with z.open(zip_member) as raw:
            with io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:header=next(csv.reader(text,strict=True),None)
        if (not header or len(header)!=len(set(header)) or any((k not in header and ALIASES.get(k) not in header) or (k in header and ALIASES.get(k) in header) for k in REQUIRED) or (expected_header is not None and header!=list(expected_header))):
            raise ValueError('Invalid or frozen source schema mismatch')
        with tempfile.TemporaryDirectory(prefix='.work-',dir=out) as work:
            compressed=Path(work)/'source.csv.gz'
            with z.open(zip_member) as raw, gzip.open(compressed,'wb',compresslevel=1) as target:
                for chunk in iter(lambda:raw.read(1024**2),b''):
                    if shutil.disk_usage(out).free<reserve_bytes+16*1024**2:raise OSError('Disk reserve unavailable during ZIP streaming')
                    if compressed.stat().st_size+len(chunk)>max_output_bytes:raise OSError('Disk staging budget exceeded')
                    target.write(chunk)
            con=_connection(memory_limit,work,threads=threads);done=threading.Event();disk_failure=[];dest=out/'part-000000.parquet'
            con.execute('SET max_temp_directory_size='+_lit(str(min(max_output_bytes,2*1024**3))+'B'))
            def monitor():
                while not done.wait(.1):
                    size=dest.stat().st_size if dest.exists() else 0
                    if size>max_output_bytes or shutil.disk_usage(out).free<reserve_bytes+16*1024**2:
                        disk_failure.append('Disk budget exceeded during native conversion');con.interrupt();return
            watcher=threading.Thread(target=monitor,daemon=True);watcher.start()
            try:
                schema='{'+','.join(_lit(k)+": 'VARCHAR'" for k in header)+'}'
                try:
                    con.execute('COPY (SELECT * FROM read_csv('+_lit(compressed)+', header=true, columns='+schema+", force_not_null=["+','.join(map(_lit,header))+"], delim=',', strict_mode=true)) TO "+_lit(dest)+" (FORMAT PARQUET, COMPRESSION ZSTD)")
                except Exception:
                    if disk_failure:raise OSError(disk_failure[0])
                    raise
                size=dest.stat().st_size
                if size>max_output_bytes or shutil.disk_usage(out).free<reserve_bytes:raise OSError('Disk budget exceeded')
                con.execute('CREATE VIEW raw AS SELECT * FROM read_parquet('+_lit(dest)+')')
                n,bad=con.execute('SELECT count(*),count(*) FILTER (WHERE activity_year IS NULL OR activity_year<>'+_lit(year)+') FROM raw').fetchone()
                if not n:raise ValueError('Empty snapshot')
                if bad:raise ValueError('Record year mismatch')
                def counts(field):return dict(con.execute('SELECT '+_ident(field)+',count(*) FROM raw GROUP BY 1 ORDER BY 1').fetchall())
                states=counts('state_code');actions=counts('action_taken');purposes=counts('loan_purpose')
            finally:
                done.set();watcher.join();con.close()
    if source.stat().st_size!=initial.st_size or source.stat().st_mtime_ns!=initial.st_mtime_ns or _sha(source)!=source_hash:raise ValueError('Source changed during ingest')
    m=dict(workflow_version=VERSION,workflow_sha256=_sha(__file__),ingest_engine='native_duckdb_gzip',year=year,split='development' if year<=2023 else ('validation' if year==2024 else 'final_evaluation'),source_url=source_url,publication_version=publication_version,source_path=str(source.resolve()),source_sha256=source_hash,source_bytes=initial.st_size,zip_member=zip_member,uncompressed_bytes=uncompressed,record_count=n,header=header,analysis_aliases={k:v for k,v in ALIASES.items() if v in header},schema_sha256=hashlib.sha256(json.dumps(header,separators=(',',':')).encode()).hexdigest(),state_counts=states,action_counts=actions,purpose_counts=purposes,parquet_files=[dict(path=dest.name,bytes=size,sha256=_sha(dest),records=n)],parquet_bytes=size,raw_scope='all source records; jurisdiction/purpose/action unrestricted',source_completeness='local source integrity only; national completeness requires independent official counts',null_policy={'storage':'all VARCHAR; blank is empty string, no SQL NULL conversion','analysis_missing_codes':MISSING},freeze_gate=gate,resources=dict(threads=threads,memory_limit=memory_limit,reserve_bytes=reserve_bytes,max_output_bytes=max_output_bytes,disk_monitor_interval_seconds=.1),created_utc=datetime.now(timezone.utc).isoformat(),model_parameters_changed=0)
    (out/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');return m


def _numeric(field):
    return 'CAST(NULLIF(NULLIF(NULLIF('+_ident(field)+",''),'NA'),'Exempt') AS DECIMAL(38,12))"


def _counts(con,field,where):
    return dict(con.execute('SELECT '+_ident(field)+',count(*) FROM selected WHERE '+where+' GROUP BY 1 ORDER BY 1').fetchall())


def _quantiles(con,kind,where):
    field={'cost':'total_loan_costs','rate':'interest_rate','ratio':'total_loan_costs'}[kind]
    criterion=where+' AND '+_numeric(field)+' IS NOT NULL'
    if kind=='ratio':criterion+=' AND '+_numeric('loan_amount')+'>0'
    n=con.execute('SELECT count(*) FROM selected WHERE '+criterion).fetchone()[0]
    if not n:return None
    order=_numeric(field)
    if kind=='ratio':order+=' / '+_numeric('loan_amount')
    # One external sort supplies all six rank operands.
    ranks=set()
    positions={name:p*(n-1) for name,p in (('p25',Decimal('.25')),('p50',Decimal('.5')),('p75',Decimal('.75')))}
    for position in positions.values():
        ranks.update((int(position)+1,min(int(position)+2,n)))
    rows=con.execute('SELECT value,principal,rn FROM (SELECT '+_ident(field)+' AS value,loan_amount AS principal,row_number() OVER (ORDER BY '+order+') AS rn FROM selected WHERE '+criterion+') WHERE rn IN ('+','.join(map(str,sorted(ranks)))+')').fetchall()
    ranked={rank:(100*number(value)/number(principal) if kind=='ratio' else number(value)) for value,principal,rank in rows}
    result={}
    for name,position in positions.items():
        lo=int(position);left=ranked[lo+1];right=ranked[min(lo+2,n)]
        result[name]=float(left+(position-lo)*(right-left))
    return result


def _summary(con,where):
    cost=_numeric('total_loan_costs');amount=_numeric('loan_amount');known=where+' AND '+cost+' IS NOT NULL';zero=known+' AND '+cost+'=0'
    count_cache={}
    predicates=[where,known,known+' AND '+amount+'>0',known+' AND ('+amount+' IS NULL OR '+amount+'<=0)',known+' AND '+_numeric('interest_rate')+' IS NOT NULL',known+' AND '+_numeric('discount_points')+' IS NOT NULL',known+' AND '+_numeric('lender_credits')+' IS NOT NULL',zero]
    counts=con.execute('SELECT '+','.join('count(*) FILTER (WHERE '+predicate+')' for predicate in predicates)+' FROM selected').fetchone()
    count_cache.update(zip(predicates,counts))
    def count(w):return count_cache[w]
    missing=_counts(con,'total_loan_costs',where+' AND '+cost+' IS NULL')
    lenders=list(_counts(con,'lei',zero).values())
    return dict(originated_records=count(where),numeric_loan_cost_records=count(known),cost_missing_by_code={MISSING[k]:v for k,v in missing.items()},dollar_cost_quantiles=_quantiles(con,'cost',known),fee_new_rounded_principal_pair_records=count(known+' AND '+amount+'>0'),missing_or_nonpositive_new_principal_among_known_cost=count(known+' AND ('+amount+' IS NULL OR '+amount+'<=0)'),new_principal_cost_ratio_percent_quantiles=_quantiles(con,'ratio',known),joint_numeric_rate_and_cost_records=count(known+' AND '+_numeric('interest_rate')+' IS NOT NULL'),rate_percent_quantiles_among_known_cost=_quantiles(con,'rate',known),numeric_points_among_known_cost=count(known+' AND '+_numeric('discount_points')+' IS NOT NULL'),numeric_lender_credits_among_known_cost=count(known+' AND '+_numeric('lender_credits')+' IS NOT NULL'),reported_zero_cost_records=count(zero),positive_cost_records=count(known)-count(zero),zero_cost_purpose_counts=_counts(con,'loan_purpose',zero),zero_cost_reporting_lender_count=len(lenders),zero_cost_counts_by_lender_descending=sorted(lenders,reverse=True))


def _view(con,where):
    originated=where+" AND action_taken='1'";purposes=[];bins=[]
    for code,label in (('31','refinancing'),('32','cash_out_refinancing')):
        group=originated+' AND loan_purpose='+_lit(code)
        purposes.append(dict(purpose_code=code,label=label,**_summary(con,group)))
        for name,low,high in BINS:
            subset=group+' AND '+_numeric('loan_amount')+' IS NOT NULL'
            if low is not None:subset+=' AND '+_numeric('loan_amount')+'>'+str(low)
            if high is not None:subset+=' AND '+_numeric('loan_amount')+'<='+str(high)
            bins.append(dict(purpose_code=code,label=label,new_public_loan_amount_bin_usd=name,**_summary(con,subset)))
    return dict(all_application_records=con.execute('SELECT count(*) FROM selected WHERE '+where).fetchone()[0],application_outcomes=_counts(con,'action_taken',where),overall_originations=_summary(con,originated),by_purpose=purposes,by_purpose_and_new_amount=bins,originations_with_unclassified_amount=con.execute('SELECT count(*) FROM selected WHERE '+originated+' AND '+_numeric('loan_amount')+' IS NULL').fetchone()[0])


def profile_snapshot(snapshot, *, state=None, freeze_gate=None, memory_limit='512MB',reserve_bytes=4*1024**3,max_spill_bytes=2*1024**3):
    """National or state profile over the explicit legacy PA analysis scope.

    Profiles include no behavioral fit. National HMDA is reportable activity,
    not a census of every mortgage transaction. Frozen holdouts fail closed.
    """
    out=Path(snapshot);m=json.loads((out/'manifest.json').read_text());_gate(m['year'],freeze_gate)
    if state is not None and (len(state)!=2 or not state.isalpha() or state!=state.upper()):raise ValueError('Expected state abbreviation')
    if shutil.disk_usage(out).free<reserve_bytes+max_spill_bytes:raise OSError('Disk reserve unavailable for profile spill')
    paths=[]
    for part in m['parquet_files']:
        path=out/part['path']
        if path.parent!=out or path.stat().st_size!=part['bytes'] or _sha(path)!=part['sha256']:raise ValueError('Parquet integrity mismatch')
        paths.append(str(path))
    with tempfile.TemporaryDirectory(prefix='.profile-',dir=out) as work:
        con=_connection(memory_limit,work)
        try:
            con.execute('SET max_temp_directory_size='+_lit(str(max_spill_bytes)+'B'))
            clause="loan_purpose IN ('31','32') AND action_taken IN ('1','2','3','4','5')"
            if state is not None:clause+=' AND state_code='+_lit(state)
            con.execute('CREATE TEMP TABLE selected AS SELECT '+','.join(_ident(ALIASES[k])+' AS '+_ident(k) if k not in m['header'] and k in ALIASES else _ident(k) for k in REQUIRED)+' FROM read_parquet(['+','.join(map(_lit,paths))+']) WHERE '+clause)
            # Bounded validation preserves Decimal semantics and rejects precision
            # beyond the exact DECIMAL storage used for external ordering.
            cursor=con.execute('SELECT '+','.join(map(_ident,NUMERIC))+' FROM selected')
            while True:
                batch=cursor.fetchmany(10000)
                if not batch:break
                for row in batch:
                    for field,raw in zip(NUMERIC,row):
                        x=number(raw)
                        if x is not None and (x<0 or x>=Decimal('1e26') or x.normalize().as_tuple().exponent < -12):
                            raise ValueError('Invalid numeric disclosure or unsupported numeric precision: '+field)
            return dict(status='descriptive_external_cost_profiles',year=m['year'],state=state if state is not None else 'ALL',raw_application_records=con.execute('SELECT count(*) FROM selected').fetchone()[0],raw_application_outcomes=_counts(con,'action_taken','true'),raw_county_records=_counts(con,'county_code','true'),base=_view(con,BASE),conforming_sitebuilt_principal_residence=_view(con,NARROW),evidence_class='observed_reported_loan_cost_component',model_parameters_changed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0)
        finally:con.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    ingest=sub.add_parser('ingest');ingest.add_argument('source');ingest.add_argument('output_dir');ingest.add_argument('--year',type=int,required=True);ingest.add_argument('--source-url',required=True);ingest.add_argument('--publication-version',required=True);ingest.add_argument('--expected-header',help='JSON file containing exact ordered source column names');ingest.add_argument('--zip-member');ingest.add_argument('--batch-rows',type=int,default=50000);ingest.add_argument('--max-output-gib',type=float,default=8);ingest.add_argument('--threads',type=int,default=1,help='Native ingestion worker count; default1 preserves prior resource use');ingest.add_argument('--fast-zip',action='store_true',help='Native DuckDB ingestion through bounded temporary gzip; recommended for national ZIPs')
    profile=sub.add_parser('profile');profile.add_argument('snapshot');profile.add_argument('--state');profile.add_argument('--output',required=True);profile.add_argument('--max-spill-gib',type=float,default=2)
    for p in (ingest,profile):p.add_argument('--freeze-gate');p.add_argument('--reserve-gib',type=float,default=4);p.add_argument('--memory-limit',default='512MB')
    args=vars(parser.parse_args(argv));command=args.pop('command');args['reserve_bytes']=int(args.pop('reserve_gib')*1024**3)
    if command=='ingest':
        args['max_output_bytes']=int(args.pop('max_output_gib')*1024**3)
        if args['expected_header']:args['expected_header']=json.loads(Path(args['expected_header']).read_text())
        result=ingest_snapshot(**args);print(json.dumps(result,indent=2))
    else:
        output=Path(args.pop('output'))
        if output.exists():raise FileExistsError('Profile output already exists')
        args['max_spill_bytes']=int(args.pop('max_spill_gib')*1024**3)
        result=profile_snapshot(**args);output.write_text(json.dumps(result,indent=2)+'\n');print(str(output))


if __name__=='__main__':main()
