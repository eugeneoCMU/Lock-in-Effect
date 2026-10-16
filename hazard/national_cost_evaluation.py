"""Transport frozen national development cost cutoffs to 2024/2025 costs.

This is an external component-distribution comparison, not behavioral or causal
validation. Prior Pennsylvania 2024 costs were examined; national 2024 must not
be described as an untouched year across the whole research project. No new
cutoffs are fitted, selected or promoted. No empirical pass/fail rule is added.
"""
import argparse
from copy import deepcopy
from decimal import Decimal
import json
import math
from numbers import Real
from pathlib import Path
import shutil
import tempfile

from hazard.hmda_cost_profiles import MISSING, REQUIRED, number
from hazard.national_cost_tables import _num, _quartiles
from hazard.national_hmda import ALIASES, NARROW, NUMERIC, _connection, _gate, _ident, _lit, _sha

YEARS=tuple(range(2018,2024))
PURPOSES=('31','32')
QUANTILES=('p25','p50','p75')


def _frozen(path,gate_path,year):
    if gate_path is None:raise ValueError('Evaluation requires a freeze gate')
    _gate(year,gate_path)
    gate=json.loads(Path(gate_path).read_text());frozen=json.loads(Path(path).read_text())
    if _sha(path)!=gate['frozen_sha256']:raise ValueError('Actual frozen cost artifact hash differs from gate')
    if (frozen.get('status')!='frozen_national_conditional_cost_scenarios' or frozen.get('evidence_class')!='conditional_cost_scenario' or frozen.get('development_years')!=list(YEARS) or frozen.get('validation_year')!=2024 or frozen.get('final_evaluation_year')!=2025 or frozen.get('scenario_count')!=252 or any(frozen.get(k)!=0 for k in ('model_parameters_changed','behavioral_parameters_fitted','new_portfolio_estimates'))):raise ValueError('Frozen costs have incorrect split, scope or fitted parameters')
    if year==2025 and 'protocol_sha256' not in gate:
        # _gate has verified the original gate and exact validation bytes.
        validation=Path(gate['validation_artifact'])
        if not validation.is_absolute():validation=Path(gate_path).parent/validation
        prior=json.loads(validation.read_text())
        if (prior.get('status')!='held_out_national_cost_distribution_comparison' or
            prior.get('evaluation_year')!=2024 or
            prior.get('frozen_costs_sha256')!=gate['frozen_sha256']):
            raise ValueError('Final protocol binding requires matching completed validation')
        gate['protocol_sha256']=prior.get('protocol_sha256')
        gate['protocol_binding']='hash_verified_2024_validation'
    if frozen.get('protocol_sha256')!=gate.get('protocol_sha256'):raise ValueError('Frozen protocol and gate hashes disagree')
    cutoffs=frozen.get('frozen_cutoffs')
    if not isinstance(cutoffs,dict) or set(cutoffs)!={str(y) for y in YEARS}:raise ValueError('Incomplete frozen development years')
    checked={}
    for development_year in YEARS:
        groups=cutoffs[str(development_year)]
        if not isinstance(groups,dict) or set(groups)!=set(PURPOSES):raise ValueError('Incomplete frozen purpose groups')
        checked[development_year]={}
        for purpose in PURPOSES:
            values=groups[purpose]
            if not isinstance(values,dict) or set(values)!=set(QUANTILES):raise ValueError('Incomplete frozen cutoff quartiles')
            previous=Decimal(-1);q={}
            for name in QUANTILES:
                value=values[name]
                if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(value):raise ValueError('Invalid frozen numeric cutoff')
                value=Decimal(str(value))
                if value<0 or value<previous:raise ValueError('Frozen cutoff quartiles must be nonnegative and ordered')
                q[name]=value;previous=value
            checked[development_year][purpose]=q
    return frozen,gate,checked


def compare_national_costs(snapshot,frozen_costs,freeze_gate,*,memory_limit='512MB',max_spill_bytes=2*1024**3,reserve_bytes=4*1024**3):
    """Apply all 12 frozen year/purpose cutoffs with inclusive ties.

    Ratios use reported costs/public rounded new principal. Counts compare
    original Decimal ratios to frozen ratio fractions, rather than binary64
    approximate comparisons. Quartile ordering retains the documented binary64
    ratio-rank limitation of the development table workflow. Empty pair samples
    yield null shares, never fabricated coverage or imputed missing values.
    """
    root=Path(snapshot).resolve();manifest=root/'manifest.json';m=json.loads(manifest.read_text());year=m.get('year')
    if isinstance(year,bool) or year not in (2024,2025):raise ValueError('Evaluation only permits held-out years 2024/2025')
    if m.get('split')!=('validation' if year==2024 else 'final_evaluation'):raise ValueError('Manifest evaluation split mismatch')
    frozen,gate,cutoffs=_frozen(frozen_costs,freeze_gate,year)
    frozen_hash=_sha(frozen_costs);manifest_hash=_sha(manifest);gate_hash=_sha(freeze_gate)
    ingestion_gate=m.get('freeze_gate')
    if not isinstance(ingestion_gate,dict):raise ValueError('Missing ingestion freeze gate receipt')
    if ingestion_gate.get('frozen_sha256')!=gate['frozen_sha256']:raise ValueError('Snapshot ingestion freeze does not match supplied frozen costs')
    if ingestion_gate.get('gate_sha256')!=gate_hash:raise ValueError('Snapshot ingestion gate does not match the actual supplied gate file')
    if reserve_bytes<0 or max_spill_bytes<=0:raise ValueError('Invalid disk budget')
    if shutil.disk_usage(root).free<reserve_bytes+max_spill_bytes:raise OSError('Disk reserve unavailable for cost evaluation')
    paths=[]
    for part in m['parquet_files']:
        path=(root/part['path']).resolve()
        if path.parent!=root or path.stat().st_size!=part['bytes'] or _sha(path)!=part['sha256']:raise ValueError('Parquet integrity mismatch')
        paths.append(str(path))
    if not paths:raise ValueError('Snapshot has no accepted Parquet parts')
    comparisons={(development_year,purpose):{'counts':dict.fromkeys(QUANTILES,0),'band':0} for development_year in YEARS for purpose in PURPOSES}
    with tempfile.TemporaryDirectory(prefix='.cost-evaluation-',dir=root) as work:
        con=_connection(memory_limit,work)
        try:
            con.execute('SET max_temp_directory_size='+_lit(str(max_spill_bytes)+'B'))
            projection=','.join(_ident(ALIASES[k])+' AS '+_ident(k) if k not in m['header'] and k in ALIASES else _ident(k) for k in REQUIRED)
            con.execute('CREATE VIEW raw AS SELECT '+projection+' FROM read_parquet(['+','.join(map(_lit,paths))+'])')
            raw_count,bad_year=con.execute('SELECT count(*),count(*) FILTER(WHERE activity_year IS NULL OR activity_year<>'+_lit(year)+') FROM raw').fetchone()
            if raw_count!=m['record_count'] or bad_year:raise ValueError('Manifest record count or year mismatch')
            origin="loan_purpose IN ('31','32') AND action_taken='1'"
            broad,narrow=con.execute('SELECT count(*) FILTER(WHERE '+origin+'),count(*) FILTER(WHERE '+origin+' AND '+NARROW+') FROM raw').fetchone()
            con.execute('CREATE TEMP TABLE eligible AS SELECT * FROM raw WHERE '+origin+' AND '+NARROW)
            for field in NUMERIC:
                q=_ident(field)
                cursor=con.execute('SELECT '+q+' FROM eligible WHERE '+q+" NOT IN ('','NA','Exempt') AND (NOT regexp_full_match("+q+", '[+]?[0-9]+([.][0-9]{0,12})?') OR TRY_CAST("+q+' AS DECIMAL(38,12)) IS NULL)')
                while True:
                    batch=cursor.fetchmany(10000)
                    if not batch:break
                    for (raw,) in batch:
                        value=number(raw)
                        if value is None or value<0 or value>=Decimal('1e26') or (field in ('loan_amount','total_loan_costs') and value.normalize().as_tuple().exponent < -12):raise ValueError('Invalid numeric disclosure or unsupported numeric precision: '+field)
            con.execute('CREATE TEMP TABLE sample AS SELECT state_code,loan_purpose,total_loan_costs,loan_amount,'+_num('total_loan_costs')+' AS cost,'+_num('loan_amount')+' AS principal,'+_num('discount_points')+' AS points,'+_num('lender_credits')+' AS credits,'+_num('interest_rate')+' AS rate FROM eligible')
            con.execute('DROP TABLE eligible')
            cost_quartiles=_quartiles(con,('loan_purpose',),'cost');ratio_quartiles=_quartiles(con,('loan_purpose',),'ratio')
            summaries=[]
            for purpose in PURPOSES:
                where='loan_purpose='+_lit(purpose)
                row=con.execute('SELECT count(*),count(cost),count(*) FILTER(WHERE cost=0),count(*) FILTER(WHERE cost>0),count(*) FILTER(WHERE cost IS NOT NULL AND principal>0),count(*) FILTER(WHERE cost IS NOT NULL AND (principal IS NULL OR principal<=0)),count(*) FILTER(WHERE cost IS NOT NULL AND points IS NOT NULL),count(*) FILTER(WHERE cost IS NOT NULL AND credits IS NOT NULL),count(*) FILTER(WHERE cost IS NOT NULL AND rate IS NOT NULL) FROM sample WHERE '+where).fetchone()
                names=('originated_records','numeric_loan_cost_records','reported_zero_cost_records','positive_cost_records','fee_new_rounded_principal_pair_records','missing_or_nonpositive_new_principal_among_known_cost','numeric_points_among_known_cost','numeric_lender_credits_among_known_cost','joint_numeric_rate_and_cost_records')
                missing=con.execute('SELECT total_loan_costs,count(*) FROM sample WHERE '+where+' AND cost IS NULL GROUP BY 1').fetchall()
                summaries.append(dict(purpose_code=purpose,**dict(zip(names,row)),cost_missing_by_code={MISSING[code]:count for code,count in missing},dollar_cost_quantiles=cost_quartiles.get((purpose,)),new_principal_cost_ratio_percent_quantiles=ratio_quartiles.get((purpose,))))
            missing_state_by_code=dict(con.execute('SELECT state_code,count(*) FROM sample WHERE state_code IN ('+','.join(map(_lit,MISSING))+') GROUP BY 1').fetchall())
            unknown=sum(missing_state_by_code.values())
            cursor=con.execute('SELECT loan_purpose,total_loan_costs,loan_amount FROM sample WHERE cost IS NOT NULL AND principal>0')
            while True:
                batch=cursor.fetchmany(10000)
                if not batch:break
                for purpose,cost,principal in batch:
                    ratio=number(cost)/number(principal)
                    for development_year in YEARS:
                        bounds=cutoffs[development_year][purpose];entry=comparisons[development_year,purpose]
                        for name in QUANTILES:entry['counts'][name]+=int(ratio<=bounds[name])
                        entry['band']+=int(bounds['p25']<=ratio<=bounds['p75'])
            rows=[];summary_by_purpose={g['purpose_code']:g for g in summaries}
            for development_year in YEARS:
                for purpose in PURPOSES:
                    entry=comparisons[development_year,purpose];denominator=summary_by_purpose[purpose]['fee_new_rounded_principal_pair_records']
                    rows.append(dict(development_year=development_year,purpose_code=purpose,evaluation_year=year,frozen_cutoffs_ratio_fraction={name:float(value) for name,value in cutoffs[development_year][purpose].items()},held_out_cost_principal_pair_records=denominator,counts_at_or_below_frozen_cutoffs=entry['counts'],shares_at_or_below_frozen_cutoffs={name:count/denominator if denominator else None for name,count in entry['counts'].items()},closed_p25_p75_band_records=entry['band'],closed_p25_p75_band_share=entry['band']/denominator if denominator else None))
        finally:con.close()
    if _sha(frozen_costs)!=frozen_hash or _sha(manifest)!=manifest_hash or _sha(freeze_gate)!=gate_hash:raise ValueError('Bound input changed during evaluation')
    _gate(year,freeze_gate)  # Recheck validation artifact binding after the read.
    result=dict(status='held_out_national_cost_distribution_comparison',evaluation_year=year,test_scope='temporal_cost_distribution_transport_only',frozen_costs_sha256=frozen_hash,freeze_gate_sha256=gate_hash,source_manifest_sha256=manifest_hash,source_sha256=m['source_sha256'],protocol_sha256=frozen['protocol_sha256'],publication_version=m['publication_version'],source_completeness=m.get('source_completeness','not independently verified'),workflow_sha256=_sha(__file__),denominators=dict(raw_snapshot_application_records=raw_count,all_refinance_originations=broad,narrower_refinance_originations=narrow,refinance_originations_outside_narrower=broad-narrow,narrower_originations_missing_state=unknown,narrower_originations_missing_state_by_code=missing_state_by_code),held_out_purpose_summaries=summaries,comparisons=rows,source_quality_qualifications=deepcopy(frozen.get('source_quality_qualifications',{})),development_source_acceptance={development_year:{key:deepcopy(value) for key,value in receipt.items() if key in ('year','source_status','every_TS_institution_count_matches','source_quality_status','source_sha256','acceptance_sha256','manifest_sha256','source_quality_qualification')} for development_year,receipt in frozen.get('input_receipts',{}).items()},tie_policy='Ratios at a cutoff are included; central coverage includes both p25 and p75 boundaries. Counts compare original Decimal ratios to frozen ratio fractions.',interpretation='External reported-cost component distribution transport only; not refinancing behavior, model probabilities, causal effects, observed joint offers or an incumbent-balance fee estimate. No empirical pass/fail criterion is imposed and frozen cutoffs are never refitted.',temporal_scope='Prior Pennsylvania 2024 cost evidence was examined. This national comparison does not make all 2024 evidence untouched. Modern transaction costs are not contemporaneous information for historical HARP borrowers.',quartile_method='Unweighted linear p(n-1) with Decimal interpolation. Held-out quartiles describe this evaluation sample and do not replace frozen cutoffs. Ratio rank ordering uses binary64, so extremely close ratios can tie.',resources=dict(memory_limit=memory_limit,max_spill_bytes=max_spill_bytes,reserve_bytes=reserve_bytes,stream_batch_records=10000),model_parameters_changed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0)
    if result['source_quality_qualifications']:result['interpretation']+=' Development cutoffs retain the 2018 unresolved public LAR/TS source-count and coverage discrepancy; evaluating held-out cost transport does not resolve that discrepancy or establish complete reported-loan coverage, behavioral validity or SOMA transport.'
    if year==2025:result['validation_artifact_sha256']=gate['validation_sha256']
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('snapshot');parser.add_argument('frozen_costs');parser.add_argument('--freeze-gate',required=True);parser.add_argument('--output',required=True);parser.add_argument('--memory-limit',default='512MB');parser.add_argument('--max-spill-gib',type=float,default=2);parser.add_argument('--reserve-gib',type=float,default=4)
    args=vars(parser.parse_args(argv));output=Path(args.pop('output'))
    if output.exists():raise FileExistsError('Evaluation output already exists')
    args['max_spill_bytes']=int(args.pop('max_spill_gib')*1024**3);args['reserve_bytes']=int(args.pop('reserve_gib')*1024**3)
    result=compare_national_costs(**args);output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(str(output))


if __name__=='__main__':main()
