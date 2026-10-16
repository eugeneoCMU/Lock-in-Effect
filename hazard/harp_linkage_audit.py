"""Audit a selected HARP linkage pilot; never estimate a general refinance rate.

Inputs are compact normalized loan summaries and the provider's ID mapping.
Mapping orientation/width must be supplied after inspecting the actual file.
No original-payoff cause, HARP eligibility, closing cost or complete monthly
risk set is inferred from mapping absence, balance changes or successor terms.
Loan-level output is for local internal use; do not package provider records.
"""
import csv
import math
import re

# Removal categories are retained as source codes, not promoted to sale causes.
REMOVAL_CODES={'01','02','03','06','09','15','16'}


def _identifier(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9]{12}',value):
        raise ValueError('Loan identifier must be a 12-character provider string')
    return value


def _month(value):
    if not isinstance(value,str) or not re.fullmatch(r'[0-9]{4}-(0[1-9]|1[0-2])',value) or value[:4]=='0000':
        raise ValueError('Normalized month must be YYYY-MM')
    return value


def _number(value,*,integer=False):
    if isinstance(value,bool):raise ValueError('Boolean is not a balance or term')
    if not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
        raise ValueError('A finite nonnegative numeric balance/term is required')
    if integer and value!=int(value):raise ValueError('Term must be integer months')
    return int(value) if integer else float(value)


def _optional(value,*,integer=False):
    return None if value is None else _number(value,integer=integer)


def read_mapping(stream,*,original_column,successor_column,field_count,header,delimiter='|'):
    """Yield normalized links with explicit, inspected layout; no format guessing.

    Inputs are zero-based column positions. IDs remain strings with leading
    zeros. Header presence is supplied; a malformed first row is never silently
    treated as a header. This parser itself does not authenticate provider data.
    """
    if not isinstance(header,bool) or not isinstance(delimiter,str) or len(delimiter)!=1:
        raise ValueError('Explicit boolean header and one-character delimiter required')
    args=(field_count,original_column,successor_column)
    if any(isinstance(v,bool) or not isinstance(v,int) for v in args):
        raise ValueError('Integer layout positions required')
    if field_count<2 or not (0<=original_column<field_count and 0<=successor_column<field_count) or original_column==successor_column:
        raise ValueError('Distinct column positions within declared width required')
    reader=csv.reader(stream,delimiter=delimiter)
    if header:
        names=next(reader,None)
        if names is None or len(names)!=field_count:raise ValueError('Header width mismatch')
    for fields in reader:
        if len(fields)!=field_count:raise ValueError('Mapping record width mismatch')
        yield dict(original_loan_id=_identifier(fields[original_column].strip()),
                   successor_loan_id=_identifier(fields[successor_column].strip()))


def _index(rows,*,original):
    index={}
    for row in rows:
        loan_id=_identifier(row['loan_id'])
        if loan_id in index:raise ValueError('One normalized summary per loan required')
        if original:
            report=_month(row['reporting_month'])
            code=row['zero_balance_code'];event=row['zero_balance_month']
            if code not in REMOVAL_CODES|{''}:raise ValueError('Unsupported removal code; audit its source semantics')
            if bool(code)!=bool(event):raise ValueError('Removal code/date must be jointly present')
            if event and _month(event)>report:raise ValueError('Removal effective date exceeds latest reporting date')
            copied=dict(loan_id=loan_id,reporting_month=report,zero_balance_code=code,
                zero_balance_month=event,prior_balance=_optional(row.get('prior_balance')),
                prior_remaining_months=_optional(row.get('prior_remaining_months'),integer=True))
        else:
            copied=dict(loan_id=loan_id,origination_month=_month(row['origination_month']),
                original_balance=_optional(row.get('original_balance')),
                original_term_months=_optional(row.get('original_term_months'),integer=True))
        index[loan_id]=copied
    return index


def audit_linked_refinances(primary_rows,mapping_rows,successor_rows,*,balance_tolerance,
                           term_tolerance_months,selection_definition):
    """Classify linkage evidence without converting the selected sample to hazards.

    Selection must be described explicitly; software cannot prove it preceded
    outcomes. Original effective payoff month is the event month. Successor
    origination after it is a conflict, not a timing assumption to be repaired.
    Old prior_balance/prior_remaining_months must refer to a documented adjacent
    observation; their provenance is still the importer/caller's responsibility.
    Matching balance/term is descriptive and does not establish rate-term
    purpose, eligibility, transaction costs or compatibility with the whole
    supplied-quote borrower objective. All other payoff causes remain unknown.
    """
    if not isinstance(selection_definition,str) or not selection_definition.strip():
        raise ValueError('Define pilot selection and denominator before reading event outcomes')
    money_tol=_number(balance_tolerance)
    term_tol=_number(term_tolerance_months,integer=True)
    primary=_index(primary_rows,original=True)
    successors=_index(successor_rows,original=False)
    if not primary:raise ValueError('A nonempty primary-loan pilot is required')
    links={};reverse={}
    for row in mapping_rows:
        old=_identifier(row['original_loan_id']);new=_identifier(row['successor_loan_id'])
        if old==new or old in links or new in reverse:raise ValueError('Mapping must have unique distinct original/successor IDs')
        links[old]=new;reverse[new]=old
    if set(links)&set(reverse):raise ValueError('Primary/HARP mapping roles overlap; possible orientation error or chain')
    if set(primary)&set(successors):raise ValueError('Primary and HARP successor summary roles overlap')
    if set(primary)&set(reverse) or set(successors)&set(links):
        raise ValueError('Mapping roles contradict primary/successor summaries; inspect orientation')
    counts={};rows=[]
    for old,p in sorted(primary.items()):
        new=links.get(old);child=successors.get(new)
        code=p['zero_balance_code'];event=p['zero_balance_month']
        known=None;balance_change=None;term_change=None;match=None
        if new and code!='01':label='linked_original_not_paid_off'
        elif new and child is None:label='linked_payoff_successor_unobserved'
        elif new and child['origination_month']>event:label='linked_date_conflict'
        elif new:
            label='linked_harp_payoff';known=True
            if p['prior_balance'] is not None and child['original_balance'] is not None:
                balance_change=child['original_balance']-p['prior_balance']
            if p['prior_remaining_months'] is not None and child['original_term_months'] is not None:
                term_change=child['original_term_months']-p['prior_remaining_months']
            if balance_change is not None and term_change is not None:
                match=abs(balance_change)<=money_tol and abs(term_change)<=term_tol
        elif code=='01':label='unmapped_payoff_or_maturity'
        elif code:label='other_source_removal'
        else:label='observed_nonterminal'
        counts[label]=counts.get(label,0)+1
        rows.append(dict(original_loan_id=old,successor_loan_id=new,event_label=label,
            event_month=event or None,source_removal_code=code or None,refinancing_known=known,
            harp_eligible=None,observed_balance_term_match=match,balance_change=balance_change,
            term_change_months=term_change,transaction_cost=None))
    return dict(status='selected_program_linkage_audit_only',primary_loans=len(primary),
        mapping_links=len(links),mapping_outside_primary_pilot=len(set(links)-set(primary)),
        counts=counts,loan_audit=rows,selection_definition=selection_definition,
        balance_tolerance=money_tol,term_tolerance_months=term_tol,
        ready_for_general_refinancing_fit=False,eligibility_inferred=False,
        limitations=['Selected HARP program positives do not identify all refinancing',
                    'Unmapped code01 retains unknown payoff/maturity and sale/refinance cause',
                    'Normalized loan summaries do not construct a full monthly risk set',
                    'Source mapping authenticity and adjacent prior-observation provenance require inspection',
                    'Matching observed balance/term does not verify eligibility, purpose or cost',
                    'Historical program data do not establish transportability to 2017–2021 loans'])



def select_opening_stock(rows,*,sample_size=1000,observation_month='2009-03'):
    """Choose a local pilot without reading future payoff or mapping information.

    Input normalized monthly records; only the declared observation month's
    ID, balance, term, amortization and removal code are inspected. Delinquency
    is deliberately not a qualifier. Missing/zero balances are not imputed.
    Return local IDs only; this selection does not establish HARP eligibility.
    """
    import hashlib
    import json
    month=_month(observation_month)
    if isinstance(sample_size,bool) or not isinstance(sample_size,int) or sample_size<=0:
        raise ValueError('A positive integer sample size is required')
    seen=set();snapshot=[];candidates=[];missing=0;exclusions={}
    for row in rows:
        if _month(row['reporting_month'])!=month:continue
        loan_id=_identifier(row['loan_id'])
        if loan_id in seen:raise ValueError('Duplicate opening-stock loan observation')
        seen.add(loan_id)
        balance=_optional(row.get('current_upb'))
        term=_optional(row.get('original_term_months'),integer=True)
        amortization=row.get('amortization_type')
        code=row.get('zero_balance_code')
        if amortization not in ('FRM','ARM','',None) or code not in REMOVAL_CODES|{''}:
            raise ValueError('Unknown source amortization/removal semantics')
        snapshot.append(dict(loan_id=loan_id,current_upb=balance,original_term_months=term,
                             amortization_type=amortization,zero_balance_code=code))
        if balance is None:
            missing+=1;reason='missing_balance'
        elif balance<=0:reason='zero_or_masked_balance'
        elif code:reason='source_removal'
        elif term!=360:reason='term_not_360_or_unknown'
        elif amortization!='FRM':reason='not_FRM_or_unknown'
        else:
            candidates.append(loan_id);continue
        exclusions[reason]=exclusions.get(reason,0)+1
    chosen=sorted(candidates,key=lambda x:hashlib.sha256(x.encode()).hexdigest())[:sample_size]
    payload=dict(observation_month=month,sample_size=sample_size,
                 snapshot=sorted(snapshot,key=lambda r:r['loan_id']))
    digest=hashlib.sha256(json.dumps(payload,sort_keys=True,allow_nan=False).encode()).hexdigest()
    return dict(observation_month=month,snapshot_loans=len(snapshot),opening_stock_loans=len(candidates),
                selected_loan_ids=chosen,selected_loans=len(chosen),missing_balance_loans=missing,
                exclusions=exclusions,selection_sha256=digest,eligibility_inferred=False,
                selection_rule='lowest SHA256(provider loan ID) among positive-balance unremoved360FRM opening loans')


def run_local_pilot(input_path,output_path):
    """Audit a compact normalized JSON pilot into a fresh, local-only directory.

    This does not ingest an uninspected raw provider format. Loan-level outputs
    remain private local records. Package source/tests/docs, not provider data.
    """
    import hashlib
    import json
    from pathlib import Path
    source=Path(input_path);output=Path(output_path)
    output.mkdir(parents=True,exist_ok=False,mode=0o700)
    with source.open('rb') as f:raw=f.read(20_000_001)
    if len(raw)>20_000_000:raise ValueError('Compact normalized pilot exceeds 20MB; select a smaller documented pilot')
    digest=hashlib.sha256(raw).hexdigest()
    data=json.loads(raw)
    if data.get('evidence_class') not in ('synthetic','observational'):
        raise ValueError('Explicit synthetic/observational evidence class required')
    provenance={k:data.get(k) for k in ('mapping_provenance','primary_provenance','successor_provenance')}
    if any(not isinstance(v,str) or not v.strip() for v in provenance.values()):
        raise ValueError('Document each normalized source before auditing')
    result=audit_linked_refinances(data['primary'],data['mapping'],data['successors'],
        balance_tolerance=data['balance_tolerance'],term_tolerance_months=data['term_tolerance_months'],
        selection_definition=data['selection_definition'])
    result['evidence_class']=data['evidence_class'];result['provenance']=provenance
    after=hashlib.sha256(source.read_bytes()).hexdigest()
    if after!=digest:raise ValueError('Input changed during audit; retain this failed attempt')
    (output/'local-loan-audit.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    aggregate={k:v for k,v in result.items() if k!='loan_audit'}
    (output/'summary.json').write_text(json.dumps(aggregate,indent=2,allow_nan=False)+'\n')
    receipt=dict(status='completed_local_audit',input_path=str(source.resolve()),
        input_sha256_before=digest,input_sha256_after=after,
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        output_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.json')},
        provider_records_for_redistribution=False,empirical_parameters_estimated=0)
    (output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    return aggregate


if __name__=='__main__':
    import argparse
    import json
    parser=argparse.ArgumentParser(description='Local selected-HARP linkage audit; no empirical refinance fit')
    parser.add_argument('--input-json',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    print(json.dumps(run_local_pilot(args.input_json,args.output)))
