"""Public HMDA transaction-cost component profiles, never a behavioral fit.

Preserves reported zeros, missing codes, source purpose and joint term
availability. The cost/new-amount ratio is not an incumbent-balance fee rate.
"""
from collections import Counter
from decimal import Decimal, InvalidOperation
from pathlib import Path
import csv
import hashlib

MISSING={'':'blank','NA':'not_applicable_or_unavailable','Exempt':'exempt'}
BINS=(('<=100000',None,100000),('(100000,200000]',100000,200000),
      ('(200000,300000]',200000,300000),('(300000,500000]',300000,500000),
      ('>500000',500000,None))
REQUIRED=('activity_year','state_code','county_code','loan_type','lien_status',
          'open-end_line_of_credit','reverse_mortgage','conforming_loan_limit',
          'construction_method','total_units','occupancy_type','action_taken',
          'loan_purpose','loan_amount','total_loan_costs','interest_rate',
          'discount_points','lender_credits','lei')

def number(raw):
    if raw in MISSING:return None
    try:value=Decimal(raw)
    except (InvalidOperation,TypeError,ValueError):raise ValueError('Invalid numeric disclosure')
    if not value.is_finite():raise ValueError('Nonfinite numeric disclosure')
    return value

def quantiles(values):
    a=sorted(values)
    if not a:return None
    result={}
    for name,p in (('p25',Decimal('.25')),('p50',Decimal('.5')),('p75',Decimal('.75'))):
        position=p*(len(a)-1);lo=int(position);hi=min(lo+1,len(a)-1)
        result[name]=float(a[lo]+(position-lo)*(a[hi]-a[lo]))
    return result

def is_base(row):
    return all(row[k]==v for k,v in (('loan_type','1'),('lien_status','1'),
        ('open-end_line_of_credit','2'),('reverse_mortgage','2')))

def is_narrower(row):
    return is_base(row) and row['conforming_loan_limit']=='C' and row['construction_method']=='1' and row['total_units'] in ('1','2','3','4') and row['occupancy_type']=='1'

def summary(rows):
    costs=[];ratios=[];rates=[];missing=Counter();principal_missing=points=credits=0
    zero_purpose=Counter();zero_lenders=Counter();zeros=0
    for row in rows:
        cost=number(row['total_loan_costs'])
        if cost is None:missing[MISSING[row['total_loan_costs']]]+=1;continue
        costs.append(cost)
        principal=number(row['loan_amount'])
        if principal is None or principal<=0:principal_missing+=1
        else:ratios.append(100*cost/principal)
        rate=number(row['interest_rate'])
        if rate is not None:rates.append(rate)
        points+=int(number(row['discount_points']) is not None)
        credits+=int(number(row['lender_credits']) is not None)
        if cost==0:
            zeros+=1;zero_purpose[row['loan_purpose']]+=1;zero_lenders[row['lei']]+=1
    return dict(originated_records=len(rows),numeric_loan_cost_records=len(costs),
        cost_missing_by_code=dict(missing),dollar_cost_quantiles=quantiles(costs),
        fee_new_rounded_principal_pair_records=len(ratios),
        missing_or_nonpositive_new_principal_among_known_cost=principal_missing,
        new_principal_cost_ratio_percent_quantiles=quantiles(ratios),
        joint_numeric_rate_and_cost_records=len(rates),rate_percent_quantiles_among_known_cost=quantiles(rates),
        numeric_points_among_known_cost=points,numeric_lender_credits_among_known_cost=credits,
        reported_zero_cost_records=zeros,positive_cost_records=len(costs)-zeros,
        zero_cost_purpose_counts=dict(zero_purpose),zero_cost_reporting_lender_count=len(zero_lenders),
        zero_cost_counts_by_lender_descending=sorted(zero_lenders.values(),reverse=True))

def _view(rows):
    originations=[r for r in rows if r['action_taken']=='1']
    purposes=[];amounts=[]
    for code,label in (('31','refinancing'),('32','cash_out_refinancing')):
        selected=[r for r in originations if r['loan_purpose']==code]
        purposes.append(dict(purpose_code=code,label=label,**summary(selected)))
        for name,low,high in BINS:
            group=[r for r in selected if number(r['loan_amount']) is not None and
                   (low is None or number(r['loan_amount'])>low) and
                   (high is None or number(r['loan_amount'])<=high)]
            amounts.append(dict(purpose_code=code,label=label,new_public_loan_amount_bin_usd=name,**summary(group)))
    return dict(all_application_records=len(rows),application_outcomes=dict(Counter(r['action_taken'] for r in rows)),
        overall_originations=summary(originations),by_purpose=purposes,by_purpose_and_new_amount=amounts,
        originations_with_unclassified_amount=sum(number(r['loan_amount']) is None for r in originations))

def _checked_rows(rows,year,state):
    if isinstance(year,bool) or not isinstance(year,int):raise ValueError('Expected year must be integral')
    if not isinstance(state,str) or len(state)!=2 or not state.isalpha() or state!=state.upper():raise ValueError('Expected state abbreviation')
    result=[]
    for row in rows:
        if any(k not in row or row[k] is None for k in REQUIRED):raise ValueError('Missing required disclosure')
        if row['activity_year']!=str(year) or row['state_code']!=state or row['action_taken'] not in ('1','2','3','4','5') or row['loan_purpose'] not in ('31','32'):raise ValueError('Record outside frozen query')
        for field in ('loan_amount','total_loan_costs','interest_rate','discount_points','lender_credits'):
            x=number(row[field])
            if x is not None and x<0:raise ValueError('Negative disclosure: '+field)
        result.append({k:row[k] for k in REQUIRED})
    return result

def build_profiles(rows,*,expected_year,expected_state):
    rows=_checked_rows(rows,expected_year,expected_state)
    return dict(status='descriptive_external_cost_profiles',year=expected_year,state=expected_state,
        raw_application_records=len(rows),raw_application_outcomes=dict(Counter(r['action_taken'] for r in rows)),
        raw_county_records=dict(Counter(r['county_code'] for r in rows)),
        base=_view([r for r in rows if is_base(r)]),
        conforming_sitebuilt_principal_residence=_view([r for r in rows if is_narrower(r)]),
        evidence_class='observed_reported_loan_cost_component',
        model_parameters_changed=0,behavioral_parameters_fitted=0,new_portfolio_estimates=0)

def profile_csv(path,*,expected_year,expected_state,aggregation,expected_header=None):
    """Require complete schema and exact independent action/purpose aggregates."""
    path=Path(path);count=Counter();sums=Counter();rows=[]
    with path.open(newline='') as f:
        reader=csv.DictReader(f);header=reader.fieldnames
        if not header or len(header)!=len(set(header)) or not set(REQUIRED).issubset(header):raise ValueError('Invalid CSV header')
        if expected_header is not None and header!=list(expected_header):raise ValueError('Frozen source schema mismatch')
        for r in reader:
            if None in r or None in r.values():raise ValueError('Malformed CSV row')
            r={k:r[k] for k in REQUIRED}
            amount=number(r['loan_amount'])
            if amount is None:raise ValueError('Cannot reconcile missing aggregate loan amount')
            key=(r['action_taken'],r['loan_purpose']);count[key]+=1;sums[key]+=amount;rows.append(r)
    expected_count={};expected_sum={}
    for cell in aggregation['aggregations']:
        key=(str(cell['actions_taken']),str(cell['loan_purposes']))
        if key in expected_count or key[0] not in ('1','2','3','4','5') or key[1] not in ('31','32'):raise ValueError('Invalid aggregation cell')
        n=cell['count']
        if isinstance(n,bool) or not isinstance(n,int) or n<0:raise ValueError('Invalid aggregation count')
        expected_count[key]=n;expected_sum[key]=number(str(cell['sum']))
    keys=set(count)|set(expected_count)
    if not rows or any(count[k]!=expected_count.get(k,0) or sums[k]!=expected_sum.get(k,Decimal(0)) for k in keys):raise ValueError('Official aggregation mismatch')
    result=build_profiles(rows,expected_year=expected_year,expected_state=expected_state)
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    result['source_validation']=dict(source_sha256=h.hexdigest(),source_bytes=path.stat().st_size,
        csv_columns=len(header),frozen_source_schema_matched=expected_header is not None,all_query_cells_match=True,
        cells=[dict(action_taken=k[0],loan_purpose=k[1],count=count[k],loan_amount_sum=str(sums[k])) for k in sorted(keys)])
    return result
