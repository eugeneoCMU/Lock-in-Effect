"""Source-bound exception for explicitly unknown pre-snapshot history."""
from collections import Counter,defaultdict
import hashlib
import json
import math
from pathlib import Path

POLICY='known_pre_snapshot_history_v1'
BOUND_ASSUMPTION='Unknown pre-May cumulative principal payoff lies between zero and original principal; assumption-dependent cash-ratio interval, not a guaranteed observed-cash bound'


def apply_exception(record,quarter,source_hashes,missing,loans,source_history):
    if not record or record.get('policy')!=POLICY or record.get('quarter')!=quarter:
        raise ValueError('Unapproved pre-snapshot coverage exception')
    if record.get('source_sha256')!=source_hashes:
        raise ValueError('Coverage exception source hashes differ')
    first=lambda n:f'{n//12:04d}{n%12+1:02d}'
    original_dates=Counter(first(loans[lid][6]) for lid in missing)
    observed_dates=Counter(first(month) for month in missing.values())
    total=sum(loans[lid][1] for lid in missing)
    if (record.get('expected_missing_loans')!=len(missing)
        or record.get('expected_missing_original_upb')!=total
        or record.get('expected_original_first_payment')!=dict(original_dates)
        or record.get('expected_first_valid_performance')!=dict(observed_dates)):
        raise ValueError('Coverage exception missing-history pattern differs')
    unknown=defaultdict(float);n=Counter()
    for lid in missing:
        key,upb=loans[lid][:2];unknown[key]+=upb;n[key]+=1
    cohorts=[]
    for key,amount in sorted(unknown.items()):
        original,paid,surviving,first_count,gap_count=source_history[key]
        known=original-amount
        if known<0 or paid>known or surviving>known:
            raise ValueError('Unknown-history removal contradicts known cohort totals')
        cohorts.append(dict(cohort=list(key),unknown_loans=n[key],unknown_original_upb=amount,
            full_original_upb=original,known_history_original_upb=known,known_prepaid_upb=paid,
            known_history_burnout=paid/known if known else None,
            full_cohort_burnout_lower=paid/original,
            full_cohort_burnout_upper=(paid+amount)/original,
            maximum_unknown_burnout_width=amount/original))
        if known:
            source_history[key][0]=known
        else:
            del source_history[key]
    return dict(enabled=True,policy=POLICY,missing_loans=len(missing),unknown_original_upb=total,
        missing_id_sha256=sorted(hashlib.sha256(lid).hexdigest() for lid in missing),
        original_first_payment=dict(original_dates),first_valid_performance=dict(observed_dates),
        affected_cohorts=cohorts,unknown_history_imputed=False,burnout_bound_assumption=BOUND_ASSUMPTION,
        initial_burnout_population='Eligible originals with valid pre-May history; unknown originals excluded only from this history denominator',
        panel_population='Full eligible source; later observed records retained; fixed panel original-UPB denominator unchanged',
        may_snapshot_unknown_loans=0)


def frozen_record(destination,freeze,digest):
    expected=freeze.get('coverage_exception_sha256')
    if not expected:return None
    path=Path(destination)/'coverage_exception.json'
    if digest(path)!=expected:raise ValueError('Frozen coverage exception changed')
    record=json.loads(path.read_text())
    if record.get('quarter')!=Path(destination).name or record.get('policy')!=POLICY:
        raise ValueError('Frozen coverage exception identity differs')
    for name,sha in record.get('evidence_sha256',{}).items():
        if Path(name).name!=name or digest(Path(destination)/name)!=sha:
            raise ValueError('Frozen coverage evidence changed')
    if not record.get('evidence_sha256'):
        raise ValueError('Coverage exception requires frozen authorization and diagnostic evidence')
    return record


def validate_audit(record,report,destination):
    audit=report.get('pre_snapshot_coverage',{})
    counts=report['counts']
    missing=counts.get('history_eligible_original_ids',0)-counts.get('loans_with_pre_snapshot_history',0)
    if record is None:
        if audit.get('enabled') or missing:
            raise ValueError('Missing frozen pre-snapshot coverage authorization')
        return
    if (not audit.get('enabled') or audit.get('policy')!=POLICY
        or report['source_sha256']!=record['source_sha256']
        or audit.get('missing_loans')!=record['expected_missing_loans'] or missing!=audit['missing_loans']
        or audit.get('unknown_original_upb')!=record['expected_missing_original_upb']
        or audit.get('original_first_payment')!=record['expected_original_first_payment']
        or audit.get('first_valid_performance')!=record['expected_first_valid_performance']
        or audit.get('burnout_bound_assumption')!=BOUND_ASSUMPTION
        or audit.get('unknown_history_imputed') is not False or audit.get('may_snapshot_unknown_loans')!=0
        or len(set(audit.get('missing_id_sha256',[])))!=missing):
        raise ValueError('Coverage audit differs from its source-bound frozen exception')
    rows=audit['affected_cohorts']
    if (sum(r['unknown_loans'] for r in rows)!=missing
        or sum(r['unknown_original_upb'] for r in rows)!=audit['unknown_original_upb']):
        raise ValueError('Coverage cohort totals differ')
    import polars as pl
    history=pl.read_parquet(Path(destination)/'rebuilt/cohort_history.parquet')
    keys=['vintage','cohort_coupon','fico_bucket','ltv_bucket']
    for row in rows:
        full,known,unknown,paid=[row[k] for k in ('full_original_upb','known_history_original_upb','unknown_original_upb','known_prepaid_upb')]
        if (not all(math.isfinite(v) for v in (full,known,unknown,paid))
            or full<=0 or known<0 or unknown<=0 or not math.isclose(full,known+unknown)
            or not 0<=paid<=known
            or not math.isclose(row['full_cohort_burnout_lower'],paid/full)
            or not math.isclose(row['full_cohort_burnout_upper'],(paid+unknown)/full)
            or not math.isclose(row['maximum_unknown_burnout_width'],unknown/full)
            or (known and not math.isclose(row['known_history_burnout'],paid/known))):
            raise ValueError('Invalid unknown-history burnout audit')
        frame=history.filter(pl.all_horizontal([pl.col(k)==v for k,v in zip(keys,row['cohort'])]))
        if (known and (frame.height!=1 or not math.isclose(frame['cohort_original_upb'].item(),known)
                       or not math.isclose(frame['historical_prepaid_upb'].item(),paid))) or (not known and frame.height):
            raise ValueError('Coverage audit differs from saved known-history denominator')
    snap=pl.read_parquet(Path(destination)/'rebuilt/snapshot.parquet')
    unknown_ids=set(audit['missing_id_sha256'])
    if any(hashlib.sha256(lid.encode()).hexdigest() in unknown_ids for lid in snap['loan_id']):
        raise ValueError('Unknown-history loan entered the May snapshot')


def combined_audit(reports,histories):
    """Aggregate unknown principal and burnout bounds across source partitions."""
    known=defaultdict(lambda:[0.,0.]);unknown=defaultdict(float)
    for frame in histories:
        for r in frame.iter_rows(named=True):
            key=tuple(r[k] for k in ('vintage','cohort_coupon','fico_bucket','ltv_bucket'))
            known[key][0]+=r['cohort_original_upb'];known[key][1]+=r['historical_prepaid_upb']
    by_quarter={r['quarter']:r.get('pre_snapshot_coverage',dict(enabled=False,missing_loans=0,unknown_original_upb=0.)) for r in reports}
    for audit in by_quarter.values():
        for r in audit.get('affected_cohorts',[]):unknown[tuple(r['cohort'])]+=r['unknown_original_upb']
    rows=[]
    for key,u in sorted(unknown.items()):
        k,p=known[key];full=k+u
        rows.append(dict(cohort=list(key),known_history_original_upb=k,unknown_original_upb=u,
            known_prepaid_upb=p,known_history_burnout=p/k if k else None,
            full_cohort_burnout_lower=p/full,full_cohort_burnout_upper=(p+u)/full,
            maximum_unknown_burnout_width=u/full))
    return dict(policy=POLICY if rows else 'strict_complete_history',by_quarter=by_quarter,
        burnout_bound_assumption=BOUND_ASSUMPTION if rows else None,
        missing_loans=sum(a.get('missing_loans',0) for a in by_quarter.values()),
        unknown_original_upb=sum(unknown.values()),affected_cohorts=rows,
        maximum_combined_cohort_burnout_width=max((r['maximum_unknown_burnout_width'] for r in rows),default=0.),
        initial_burnout_population='Known pre-May history only; unknown balances not treated as zero prepayment',
        panel_burnout_qualification='Observed-cash ratio on full fixed original denominator; unobserved early payoffs remain unknown')
