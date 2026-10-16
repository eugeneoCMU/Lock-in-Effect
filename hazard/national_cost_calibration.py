"""Freeze separately dated national cost scenarios before held-out analysis.

The freeze binds actual development table, source-manifest, acceptance and
protocol files by SHA256. Source archive hashes are cross-checked between those
receipts; this function does not reread archived loan files or refit quantiles.
All balance and financing transformations remain conditional external cost
scenarios, not behavioral calibration, borrower offers or portfolio estimates.
"""
from collections.abc import Mapping
from copy import deepcopy
from decimal import Decimal
import argparse
import hashlib
import json
import math
from numbers import Real
from pathlib import Path
import re

from hazard.refinancing_cost_bridge import bridge_cost_ratio
from hazard.national_hmda import _sha

YEARS=tuple(range(2018,2024))
PURPOSES=('31','32')
QUANTILES=('p25','p50','p75')
RAW_SCOPE='all source records; jurisdiction/purpose/action unrestricted'


def _read(path):
    path=Path(path).resolve();raw=path.read_bytes()
    try:value=json.loads(raw)
    except (ValueError,UnicodeDecodeError) as exc:raise ValueError('Invalid JSON input: '+str(path)) from exc
    if not isinstance(value,dict):raise ValueError('Expected JSON object: '+str(path))
    return value,hashlib.sha256(raw).hexdigest(),path


def _count(value,name,minimum=0):
    if isinstance(value,bool) or not isinstance(value,int) or value<minimum:raise ValueError('Invalid count: '+name)
    return value


def _hash(value):
    if not isinstance(value,str) or re.fullmatch('[0-9a-f]{64}',value) is None:raise ValueError('Invalid SHA256 receipt')
    return value


def _groups(table):
    groups={}
    for group in table.get('groups',[]):
        if not isinstance(group,dict):raise ValueError('Invalid table group')
        if group.get('level')!='national_purpose':continue
        purpose=group.get('purpose_code')
        if purpose not in PURPOSES or purpose in groups or group.get('state_code') is not None or group.get('new_public_loan_amount_bin_usd') is not None:raise ValueError('Invalid or duplicate national purpose group')
        keys=('originated_records','numeric_loan_cost_records','reported_zero_cost_records','positive_cost_records','fee_new_rounded_principal_pair_records','missing_or_nonpositive_new_principal_among_known_cost','numeric_points_among_known_cost','numeric_lender_credits_among_known_cost','joint_numeric_rate_and_cost_records')
        counts={key:_count(group.get(key),key) for key in keys}
        if not counts['fee_new_rounded_principal_pair_records']:raise ValueError('Qualifying purpose lacks observed cost/principal pairs')
        n=counts['originated_records'];known=counts['numeric_loan_cost_records'];missing=group.get('cost_missing_by_code')
        if not isinstance(missing,dict) or set(missing)-{'blank','not_applicable_or_unavailable','exempt'}:raise ValueError('Invalid missing disclosure audit')
        missing={key:_count(value,'cost missing') for key,value in missing.items()}
        if (known>n or known+sum(missing.values())!=n or counts['reported_zero_cost_records']+counts['positive_cost_records']!=known or counts['fee_new_rounded_principal_pair_records']+counts['missing_or_nonpositive_new_principal_among_known_cost']!=known or any(counts[key]>known for key in keys[6:])):raise ValueError('Inconsistent purpose denominators')
        percent=group.get('new_principal_cost_ratio_percent_quantiles')
        if not isinstance(percent,dict) or set(percent)!=set(QUANTILES):raise ValueError('Missing purpose quartiles')
        previous=-1.;cutoffs={}
        for name in QUANTILES:
            value=percent[name]
            if isinstance(value,bool) or not isinstance(value,Real) or not math.isfinite(value) or value<0 or value<previous:raise ValueError('Invalid ordered cost quartiles')
            previous=value;cutoffs[name]=float(Decimal(str(value))/100)
        counts['cost_missing_by_code']=missing;groups[purpose]=(counts,cutoffs)
    if set(groups)!=set(PURPOSES):raise ValueError('Both separate national purpose groups are required; no imputation')
    return groups


def _source_quality_exception(year,acceptance,manifest,acceptance_path,checked_files):
    """A source-bound 2018 cost-only exception; never an invented TS match."""
    if year!=2018 or acceptance.get('status')!='accepted_published_lar_with_unresolved_ts_discrepancy' or acceptance.get('every_TS_institution_count_matches') is not False:
        raise ValueError('Only the explicitly audited 2018 cost-only source exception is supported')
    if not isinstance(acceptance.get('scope'),str) or not acceptance['scope'].strip():raise ValueError('Explicit unresolved source-quality scope is required')
    documents={};hashes={};paths={}
    for kind,path_key,hash_key in (('audit','independent_raw_audit_path','independent_raw_audit_sha256'),('policy','source_quality_policy_path','source_quality_policy_sha256')):
        path=acceptance.get(path_key)
        if not isinstance(path,str) or not path:raise ValueError('Missing source-quality evidence path')
        path=Path(path)
        if not path.is_absolute():path=acceptance_path.parent/path
        documents[kind],hashes[kind],paths[kind]=_read(path)
        if hashes[kind]!=_hash(acceptance.get(hash_key)):raise ValueError('Source-quality audit or policy hash mismatch')
        checked_files.append((paths[kind],hashes[kind]))
    audit=documents['audit'];policy=documents['policy'];source=manifest['source_sha256'];raw=manifest['record_count']
    allowed={'Descriptive reported-cost distributions conditional on current published public LAR records','Predeclared year/purpose cost scenarios with source-quality qualification','Cost-distribution transport checks with frozen cutoffs'}
    if (policy.get('status')!='explicit_cost_only_source_quality_exception_before_2018_cost_inspection' or policy.get('year')!=2018 or policy.get('permitted_source_sha256')!=source or not isinstance(policy.get('allowed_use'),list) or set(policy['allowed_use'])!=allowed or not isinstance(policy.get('raw_record_policy'),str) or not policy['raw_record_policy'].strip()):raise ValueError('Source-quality policy has incorrect source, year or cost-only scope')
    not_established=policy.get('not_established')
    if not isinstance(not_established,list) or not {'Every institution-declared row appears in public LAR','Behavioral validity or SOMA transport'}.issubset(not_established):raise ValueError('Policy must retain unresolved coverage and behavioral limitations')
    if (audit.get('status')!='independent_raw_byte_audit_not_TS_acceptance' or audit.get('year')!=2018 or audit.get('source_sha256')!=source or audit.get('raw_vs_parquet_all_institution_counts_match') is not True or audit.get('raw_vs_parquet_differences')!=[] or audit.get('completed_ZIP_member_CRC_verified') is not True):raise ValueError('Independent raw/Parquet count and ZIP CRC audit is required')
    if (_count(audit.get('physical_data_records'),'audit raw rows',1)!=raw or _count(policy.get('published_LAR_records'),'policy raw rows',1)!=raw or _count(audit.get('raw_institutions'),'audit institutions',1)!=acceptance['institutions'] or _count(audit.get('source_bytes'),'audit source bytes',1)!=manifest['source_bytes']):raise ValueError('Audit source size, records or institutions mismatch')
    if (_count(audit.get('observed_uncompressed_bytes'),'audit uncompressed bytes',1)!=manifest['uncompressed_bytes'] or audit['observed_uncompressed_bytes']!=_count(audit.get('declared_uncompressed_bytes'),'ZIP declared bytes',1)):raise ValueError('Audit ZIP byte totals mismatch')
    ts=_count(audit.get('TS_count_sum'),'audit TS sum',1)
    if ts!=_count(policy.get('published_TS_sum'),'policy TS sum',1) or ts!=_count(acceptance.get('official_TS_sum'),'accepted TS sum',1) or _hash(audit.get('TS_sha256'))!=_hash(acceptance.get('official_TS_sha256')):raise ValueError('TS source hash or total mismatch')
    difference=raw-ts
    for value in (audit.get('raw_minus_TS_records'),acceptance.get('raw_minus_TS_records'),policy.get('net_count_discrepancy')):
        if isinstance(value,bool) or not isinstance(value,int) or value!=difference or not difference:raise ValueError('Unresolved source discrepancy arithmetic mismatch')
    if (_count(audit.get('diagnostic_uppercase_mismatch_count'),'residual TS mismatches',1)!=_count(policy.get('remaining_mismatches'),'policy TS mismatches',1) or _count(audit.get('TS_records'),'TS institutions',1)-audit['raw_institutions']!=_count(policy.get('missing_TS_only_institutions'),'missing TS institutions',1)):raise ValueError('Institution discrepancy ledger totals mismatch')
    other=policy.get('other_18_count_net_difference')
    if isinstance(other,bool) or not isinstance(other,int) or -_count(policy.get('TS_only_record_count'),'TS-only record count',1)+other!=difference:raise ValueError('Missing/shared-institution residual arithmetic mismatch')
    return dict(source_quality_status='published_LAR_with_unresolved_TS_discrepancy',year=2018,scope=acceptance['scope'],TS_reconciliation_established=False,source_sha256=source,published_LAR_records=raw,published_TS_sum=ts,raw_minus_TS_records=difference,independent_raw_audit_path=str(paths['audit']),independent_raw_audit_sha256=hashes['audit'],source_quality_policy_path=str(paths['policy']),source_quality_policy_sha256=hashes['policy'],allowed_use=policy['allowed_use'],not_established=policy['not_established'],raw_record_policy=policy['raw_record_policy'],records_deleted_or_imputed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0)


def freeze_national_costs(inputs,output_dir,*,protocol_path):
    """Bind exactly 2018..2023, write 252 scenarios and a 2024-only gate.

    inputs maps each year to paths under keys tables, acceptance and manifest.
    Every input is read and checked before a new output directory is created.
    Existing output directories are rejected; no input is modified. No 2025
    gate is produced: a separate accepted validation artifact is required first.
    """
    out=Path(output_dir).resolve()
    if out.exists():raise FileExistsError('National cost freeze destination already exists')
    if not isinstance(inputs,Mapping):raise ValueError('Expected development-year mapping')
    normalized={}
    for year,entry in inputs.items():
        if isinstance(year,bool) or str(year) not in {str(y) for y in YEARS} or int(year) in normalized:raise ValueError('Only the six separate development years 2018..2023 are allowed')
        if not isinstance(entry,Mapping) or set(entry)!={'tables','acceptance','manifest'}:raise ValueError('Each year requires tables, acceptance and manifest paths')
        normalized[int(year)]=entry
    if set(normalized)!=set(YEARS):raise ValueError('All six development years are required')
    protocol,protocol_hash,protocol_file=_read(protocol_path)
    final=protocol.get('final_holdout_year',protocol.get('final_evaluation_year'))
    if (protocol.get('development_years')!=list(YEARS) or protocol.get('validation_year')!=2024 or final!=2025 or ('final_evaluation_year' in protocol and protocol['final_evaluation_year']!=2025) or protocol.get('holdout_data_opened') is not False):raise ValueError('Protocol split must freeze 2018..2023 development,2024 validation,2025 unopened final evaluation')
    receipts={};cutoffs={};scenarios=[];qualifications={};checked_files=[(protocol_file,protocol_hash)]
    for year in YEARS:
        documents={};hashes={};files={}
        for kind,path in normalized[year].items():
            documents[kind],hashes[kind],files[kind]=_read(path);checked_files.append((files[kind],hashes[kind]))
        table=documents['tables'];acceptance=documents['acceptance'];manifest=documents['manifest']
        if (table.get('year')!=year or acceptance.get('year')!=year or manifest.get('year')!=year or table.get('split')!='development' or manifest.get('split')!='development'):raise ValueError('Development year or split mismatch')
        if table.get('status')!='descriptive_national_cost_distributions' or table.get('behavioral_parameters_fitted')!=0 or table.get('model_parameters_changed')!=0:raise ValueError('Expected unfitted descriptive national cost tables')
        exact_TS=acceptance.get('status')=='accepted_source_bound_national_snapshot' and acceptance.get('every_TS_institution_count_matches') is True
        if not exact_TS and (year!=2018 or acceptance.get('status')!='accepted_published_lar_with_unresolved_ts_discrepancy'):raise ValueError('Accepted official TS reconciliation or the audited 2018 cost-only exception is required')
        if manifest.get('raw_scope')!=RAW_SCOPE:raise ValueError('Restricted raw population cannot supply national freeze')
        states=manifest.get('state_counts')
        if not isinstance(states,dict) or len([state for state in states if state and state not in ('NA','Exempt')])<2:raise ValueError('National source cannot be restricted to Pennsylvania or one jurisdiction')
        raw=_count(manifest.get('record_count'),'manifest record_count',1)
        if sum(_count(count,'state count') for count in states.values())!=raw:raise ValueError('State count partition mismatch')
        _count(acceptance.get('institutions'),'accepted institutions',1)
        if _count(acceptance.get('raw_records'),'accepted raw_records',1)!=raw:raise ValueError('Accepted source record count mismatch')
        if _hash(table.get('source_manifest_sha256'))!=hashes['manifest'] or _hash(acceptance.get('manifest_sha256'))!=hashes['manifest']:raise ValueError('Actual source manifest hash mismatch')
        source=_hash(manifest.get('source_sha256'))
        if _hash(table.get('source_sha256'))!=source or _hash(acceptance.get('source_sha256'))!=source:raise ValueError('Source archive hash relationships disagree')
        quality=None
        if not exact_TS:
            quality=_source_quality_exception(year,acceptance,manifest,files['acceptance'],checked_files)
            qualifications[str(year)]=quality
        denominators=table.get('denominators')
        if not isinstance(denominators,dict) or _count(denominators.get('raw_snapshot_application_records'),'table raw records',1)!=raw:raise ValueError('Table raw denominator mismatch')
        broad=_count(denominators.get('all_refinance_originations'),'broad originations');narrow=_count(denominators.get('narrower_refinance_originations'),'narrow originations')
        if narrow>broad or broad>raw or _count(denominators.get('refinance_originations_outside_narrower'),'outside narrower')!=broad-narrow:raise ValueError('Inconsistent table population denominators')
        groups=_groups(table)
        if sum(counts['originated_records'] for counts,q in groups.values())!=narrow:raise ValueError('Purpose groups do not partition narrow originations')
        receipts[str(year)]=dict(year=year,source_sha256=source,tables_sha256=hashes['tables'],acceptance_sha256=hashes['acceptance'],manifest_sha256=hashes['manifest'],tables_path=str(files['tables']),acceptance_path=str(files['acceptance']),manifest_path=str(files['manifest']),raw_records=raw,institutions=acceptance['institutions'],publication_version=manifest.get('publication_version'),source_url=manifest.get('source_url'),every_TS_institution_count_matches=acceptance['every_TS_institution_count_matches'],source_status=acceptance['status'],source_quality_status='exact_TS_reconciled' if exact_TS else quality['source_quality_status'])
        if quality is not None:receipts[str(year)]['source_quality_qualification']=deepcopy(quality)
        cutoffs[str(year)]={}
        for purpose in PURPOSES:
            counts,q=groups[purpose];cutoffs[str(year)][purpose]=q
            for quantile in QUANTILES:
                choices=[('supplied_balance_ratio',financing,ratio) for ratio in (.9,1.,1.1) for financing in ('cash','financed')]
                if purpose=='31':choices.extend([('unchanged_balance','cash',None),('all_fees_financed_no_other_balance_change','financed',None)])
                for rule,financing,ratio in choices:
                    scenario=bridge_cost_ratio(q[quantile],balance_rule=rule,financing=financing,new_to_existing_ratio=ratio,purpose_code=int(purpose))
                    scenario.update(development_year=year,quantile=quantile,group_denominators=deepcopy(counts),tables_sha256=hashes['tables'],acceptance_sha256=hashes['acceptance'],source_manifest_sha256=hashes['manifest'],source_sha256=source,protocol_sha256=protocol_hash,calibration_status='conditional_external_cost_scenario_not_behavioral_fit',source_quality_status=receipts[str(year)]['source_quality_status'])
                    scenarios.append(scenario)
    if len(scenarios)!=252:raise ValueError('Incomplete conditional scenario grid')
    frozen=dict(status='frozen_national_conditional_cost_scenarios',evidence_class='conditional_cost_scenario',development_years=list(YEARS),validation_year=2024,final_evaluation_year=2025,protocol_path=str(protocol_file),protocol_sha256=protocol_hash,workflow_sha256=_sha(__file__),bridge_workflow_sha256=_sha(Path(__file__).with_name('refinancing_cost_bridge.py')),input_receipts=receipts,source_quality_qualifications=qualifications,frozen_cutoffs=cutoffs,scenario_count=len(scenarios),scenarios=scenarios,interpretation='Separate year/purpose external cost distributions; no pooling, missing-group imputation, behavioral fit, causal effect, joint offer menu, or portfolio re-estimation. Incumbent balances and financing are unobserved assumptions. Transaction-year costs do not constitute information available to a historical HARP borrower.',ratio_quantile_method='Input tables preserve public rounded new-principal denominator; ratio ranks may tie at binary64 precision. Frozen quantiles are descriptive component cutoffs, not borrower offers.',model_parameters_changed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0)
    if qualifications:frozen['interpretation']+=' The 2018 published LAR has an unresolved TS count/coverage discrepancy; conditional cost use does not establish complete reported-loan coverage, behavioral validity, h0 or SOMA transport.'
    # Check the same file bytes immediately before publishing immutable outputs.
    if any(_sha(path)!=expected for path,expected in checked_files):raise ValueError('Input changed during freeze')
    out.mkdir(parents=True)
    artifact=out/'frozen-national-costs.json'
    artifact.write_text(json.dumps(frozen,indent=2,allow_nan=False)+'\n')
    gate=dict(development_years=list(YEARS),validation_year=2024,final_evaluation_year=2025,frozen_artifact=artifact.name,frozen_sha256=_sha(artifact),allowed_years=[2024],protocol_sha256=protocol_hash,source_quality_qualifications=qualifications,note='Opens only 2024 cost validation; a separate accepted validation artifact is required before any 2025 gate.')
    gate_path=out/'validation-gate.json';gate_path.write_text(json.dumps(gate,indent=2,allow_nan=False)+'\n')
    output_manifest=dict(status='immutable_national_development_cost_freeze',development_years=list(YEARS),validation_year=2024,final_evaluation_year=2025,protocol_sha256=protocol_hash,input_receipts=receipts,source_quality_qualifications=qualifications,files={artifact.name:_sha(artifact),gate_path.name:_sha(gate_path)},scenario_count=252,model_parameters_changed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0)
    (out/'manifest.json').write_text(json.dumps(output_manifest,indent=2,allow_nan=False)+'\n')
    return frozen


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('inputs',help='JSON mapping year to tables/acceptance/manifest paths; relative paths resolve beside this JSON');parser.add_argument('output_dir');parser.add_argument('--protocol',required=True)
    args=parser.parse_args(argv);input_path=Path(args.inputs).resolve();inputs=json.loads(input_path.read_text())
    if not isinstance(inputs,dict):raise ValueError('Expected input year mapping')
    for entry in inputs.values():
        if isinstance(entry,dict):
            for key,value in entry.items():
                p=Path(value)
                if not p.is_absolute():entry[key]=str(input_path.parent/p)
    result=freeze_national_costs(inputs,args.output_dir,protocol_path=args.protocol);print(json.dumps({'scenario_count':result['scenario_count'],'output_dir':str(Path(args.output_dir).resolve()),'validation_gate':'validation-gate.json'},indent=2))


if __name__=='__main__':main()
