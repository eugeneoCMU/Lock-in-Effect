"""Grouped descriptive HMDA cost distributions from verified raw snapshots.

Six levels are produced independently: national, state, national-purpose,
state-purpose, national-purpose-amount and state-purpose-amount. They overlap;
rows across levels must not be summed. Numeric zeros are retained. These are
record-level cost components and ratios to public rounded new loan amounts,
never incumbent-balance fee rates, observed offer menus or behavioral fits.
"""
import argparse
from decimal import Decimal
import json
from pathlib import Path
import shutil
import tempfile

from hazard.hmda_cost_profiles import MISSING, REQUIRED, number
from hazard.national_hmda import ALIASES, NARROW, NUMERIC, _connection, _gate, _ident, _lit, _sha

LEVELS=(('national',()),('state',('state_code',)),('national_purpose',('loan_purpose',)),('state_purpose',('state_code','loan_purpose')),('national_purpose_amount',('loan_purpose','amount_bin')),('state_purpose_amount',('state_code','loan_purpose','amount_bin')))


def _num(field):
    return "CAST(NULLIF(NULLIF(NULLIF("+_ident(field)+",''),'NA'),'Exempt') AS DECIMAL(38,12))"


def _quartiles(con,fields,metric):
    """One external sort per metric and level; Decimal interpolation at ranks.

    Sorting ratios uses DuckDB DOUBLE division; final interpolation uses the
    legacy Decimal arithmetic on the original operands. Extremely close ratios
    indistinguishable in binary64 can tie in ordering. No quantiles are paired
    across fields as if they described a single observed contract.
    """
    partition='PARTITION BY '+','.join(map(_ident,fields))+' ' if fields else ''
    prefix=','.join(map(_ident,fields))+',' if fields else ''
    criterion='cost IS NOT NULL'
    order='cost'
    if metric=='ratio':criterion+=' AND principal>0';order='cost/principal'
    inner='SELECT '+prefix+'total_loan_costs,loan_amount,row_number() OVER ('+partition+'ORDER BY '+order+') AS rn,count(*) OVER ('+partition.rstrip()+') AS n FROM sample WHERE '+criterion
    rank_filter=' OR '.join('rn IN (CAST(floor('+p+'*(n-1)) AS BIGINT)+1,least(CAST(floor('+p+'*(n-1)) AS BIGINT)+2,n))' for p in ('.25','.5','.75'))
    rows=con.execute('SELECT * FROM ('+inner+') WHERE '+rank_filter).fetchall();ranked={};counts={}
    for r in rows:
        key=tuple(r[:len(fields)]);cost,principal,rank,n=r[len(fields):]
        ranked.setdefault(key,{})[rank]=100*number(cost)/number(principal) if metric=='ratio' else number(cost)
        counts[key]=n
    result={}
    for key,values in ranked.items():
        q={};n=counts[key]
        for name,p in (('p25',Decimal('.25')),('p50',Decimal('.5')),('p75',Decimal('.75'))):
            position=p*(n-1);lo=int(position);a=values[lo+1];b=values[min(lo+2,n)]
            q[name]=float(a+(position-lo)*(b-a))
        result[key]=q
    return result


def build_cost_tables(snapshot,*,freeze_gate=None,memory_limit='512MB',max_spill_bytes=2*1024**3,reserve_bytes=4*1024**3):
    """Return one year's national/state descriptive distributions, no fitting.

    Uses a narrow temporary table and processes grouping levels sequentially,
    avoiding expansion of each observation into six simultaneous copies.
    All jurisdiction codes are retained; missing disclosure codes remain separate explicit
    groups, rather than being silently dropped or attributed to a reported state.
    """
    root=Path(snapshot).resolve();manifest=root/'manifest.json';m=json.loads(manifest.read_text());gate=_gate(m['year'],freeze_gate)
    if reserve_bytes<0 or max_spill_bytes<=0:raise ValueError('Invalid disk budget')
    if shutil.disk_usage(root).free<reserve_bytes+max_spill_bytes:raise OSError('Disk reserve unavailable for grouped cost tables')
    paths=[]
    for part in m['parquet_files']:
        path=(root/part['path']).resolve()
        if path.parent!=root or path.stat().st_size!=part['bytes'] or _sha(path)!=part['sha256']:raise ValueError('Parquet integrity mismatch')
        paths.append(str(path))
    if not paths:raise ValueError('Snapshot has no accepted Parquet parts')
    with tempfile.TemporaryDirectory(prefix='.cost-tables-',dir=root) as work:
        con=_connection(memory_limit,work)
        try:
            con.execute('SET max_temp_directory_size='+_lit(str(max_spill_bytes)+'B'))
            projection=','.join(_ident(ALIASES[k])+' AS '+_ident(k) if k not in m['header'] and k in ALIASES else _ident(k) for k in REQUIRED)
            con.execute('CREATE VIEW raw AS SELECT '+projection+' FROM read_parquet(['+','.join(map(_lit,paths))+'])')
            raw_count,bad_year=con.execute('SELECT count(*),count(*) FILTER(WHERE activity_year IS NULL OR activity_year<>'+_lit(m['year'])+') FROM raw').fetchone()
            if raw_count!=m['record_count'] or bad_year:raise ValueError('Manifest record count or year mismatch')
            origin="loan_purpose IN ('31','32') AND action_taken='1'"
            broad,narrow=con.execute('SELECT count(*) FILTER(WHERE '+origin+'),count(*) FILTER(WHERE '+origin+' AND '+NARROW+') FROM raw').fetchone()
            con.execute('CREATE TEMP TABLE eligible AS SELECT * FROM raw WHERE '+origin+' AND '+NARROW)
            # Native screening keeps ordinary decimal values in DuckDB. Validate
            # exceptional representations (including scientific notation) with
            # the existing Decimal semantics in bounded batches, retaining them.
            for field in NUMERIC:
                q=_ident(field)
                cursor=con.execute('SELECT '+q+' FROM eligible WHERE '+q+" NOT IN ('','NA','Exempt') AND (NOT regexp_full_match("+q+", '[+]?[0-9]+([.][0-9]{0,12})?') OR TRY_CAST("+q+' AS DECIMAL(38,12)) IS NULL)')
                while True:
                    exceptional=cursor.fetchmany(10000)
                    if not exceptional:break
                    for (raw,) in exceptional:
                        value=number(raw)
                        if value is None or value<0 or value>=Decimal('1e26') or (field in ('loan_amount','total_loan_costs') and value.normalize().as_tuple().exponent < -12):
                            raise ValueError('Invalid numeric disclosure or unsupported numeric precision: '+field)
            amount=_num('loan_amount')
            bins="CASE WHEN "+amount+" IS NULL THEN 'unclassified_amount' WHEN "+amount+"<=100000 THEN '<=100000' WHEN "+amount+"<=200000 THEN '(100000,200000]' WHEN "+amount+"<=300000 THEN '(200000,300000]' WHEN "+amount+"<=500000 THEN '(300000,500000]' ELSE '>500000' END"
            con.execute('CREATE TEMP TABLE sample AS SELECT state_code,loan_purpose,total_loan_costs,loan_amount,'+_num('total_loan_costs')+' AS cost,'+amount+' AS principal,'+_num('discount_points')+' AS points,'+_num('lender_credits')+' AS credits,'+_num('interest_rate')+' AS rate,'+bins+' AS amount_bin FROM eligible')
            con.execute('DROP TABLE eligible')
            groups=[]
            measures=[('originated_records','count(*)'),('numeric_loan_cost_records','count(cost)'),('reported_zero_cost_records','count(*) FILTER(WHERE cost=0)'),('positive_cost_records','count(*) FILTER(WHERE cost>0)'),('fee_new_rounded_principal_pair_records','count(*) FILTER(WHERE cost IS NOT NULL AND principal>0)'),('missing_or_nonpositive_new_principal_among_known_cost','count(*) FILTER(WHERE cost IS NOT NULL AND (principal IS NULL OR principal<=0))'),('numeric_points_among_known_cost','count(*) FILTER(WHERE cost IS NOT NULL AND points IS NOT NULL)'),('numeric_lender_credits_among_known_cost','count(*) FILTER(WHERE cost IS NOT NULL AND credits IS NOT NULL)'),('joint_numeric_rate_and_cost_records','count(*) FILTER(WHERE cost IS NOT NULL AND rate IS NOT NULL)')]
            for level,fields in LEVELS:
                prefix=','.join(map(_ident,fields))+',' if fields else ''
                groupby=' GROUP BY '+','.join(map(_ident,fields)) if fields else ''
                expressions=[expr+' AS '+_ident(name) for name,expr in measures]
                expressions += ['count(*) FILTER(WHERE total_loan_costs='+_lit(code)+') AS missing_'+str(i) for i,code in enumerate(MISSING)]
                rows=con.execute('SELECT '+prefix+','.join(expressions)+' FROM sample'+groupby).fetchall()
                costs=_quartiles(con,fields,'cost');ratios=_quartiles(con,fields,'ratio')
                for row in rows:
                    key=tuple(row[:len(fields)]);dimensions=dict(zip(fields,key));counts=row[len(fields):];stats=dict(zip((name for name,expr in measures),counts[:len(measures)]))
                    stats['cost_missing_by_code']={label:count for label,count in zip(MISSING.values(),counts[len(measures):]) if count}
                    groups.append(dict(level=level,state_code=dimensions.get('state_code'),state_status=('missing_state' if dimensions['state_code'] in MISSING else 'reported_state') if 'state_code' in dimensions else 'all_jurisdictions_including_missing',purpose_code=dimensions.get('loan_purpose'),new_public_loan_amount_bin_usd=dimensions.get('amount_bin'),**stats,dollar_cost_quantiles=costs.get(key),new_principal_cost_ratio_percent_quantiles=ratios.get(key)))
            groups.sort(key=lambda g:(list(name for name,fields in LEVELS).index(g['level']),g['state_code'] or '',g['purpose_code'] or '',g['new_public_loan_amount_bin_usd'] or ''))
            return dict(status='descriptive_national_cost_distributions',year=m['year'],split=m['split'],source_manifest_sha256=_sha(manifest),source_sha256=m['source_sha256'],publication_version=m['publication_version'],source_url=m['source_url'],source_completeness=m.get('source_completeness','not independently verified'),group_presence_policy='Only observed dimensional groups are emitted; the national total is emitted even for an empty sample. National means all records in this supplied snapshot; nationwide source completeness requires separate official reconciliation.',workflow_sha256=_sha(__file__),freeze_gate=gate,denominators=dict(raw_snapshot_application_records=raw_count,all_refinance_originations=broad,narrower_refinance_originations=narrow,refinance_originations_outside_narrower=broad-narrow),sample_definition="Originated action1, purposes31/32; conventional first-lien closed-end non-reverse; conforming C, site-built,1..4units,principal residence. No fixed-rate or term restriction inferred.",denominator_policy='Each group counts originated records in the narrower sample. Cost statistics condition on numeric cost; ratio statistics additionally require positive numeric public rounded new principal. Levels overlap and must not be summed together.',quartile_method='Unweighted linear p(n-1), exact Decimal interpolation from original operands; ratio rank order uses binary64 DuckDB division with possible ties at machine precision.',evidence_class='observed_reported_loan_cost_component',offer_menu_interpretation='No marginal quantiles are combined into observed joint offers. Points are included in total loan costs; lender credits are separate, without netting.',geography_interpretation='All reporting jurisdictions retained; blank, NA and Exempt state codes explicitly grouped as missing while preserving their literal values. HMDA reportable activity is not every US mortgage transaction.',resources=dict(memory_limit=memory_limit,max_spill_bytes=max_spill_bytes,reserve_bytes=reserve_bytes),groups=groups,model_parameters_changed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0)
        finally:con.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('snapshot');parser.add_argument('--output',required=True);parser.add_argument('--freeze-gate');parser.add_argument('--memory-limit',default='512MB');parser.add_argument('--max-spill-gib',type=float,default=2);parser.add_argument('--reserve-gib',type=float,default=4)
    args=vars(parser.parse_args(argv));output=Path(args.pop('output'))
    if output.exists():raise FileExistsError('Cost-table output already exists')
    args['max_spill_bytes']=int(args.pop('max_spill_gib')*1024**3);args['reserve_bytes']=int(args.pop('reserve_gib')*1024**3)
    result=build_cost_tables(**args);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');print(str(output))


if __name__=='__main__':main()
