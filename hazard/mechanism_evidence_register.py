"""Conservative adapter for dated, source-accepted selected-program events."""
from datetime import datetime
import re


def _month(value):
    if not isinstance(value, str) or re.fullmatch(r'[0-9]{4}-?[0-9]{2}',value) is None:
        raise ValueError('month must be YYYYMM or YYYY-MM')
    normalized=value.replace('-', '')
    if len(normalized)!=6 or not normalized.isdigit():
        raise ValueError('month must be YYYYMM or YYYY-MM')
    datetime.strptime(normalized,'%Y%m')
    return normalized


def summarize_causes(events, *, population_id, coverage_start, coverage_end):
    start,end=_month(coverage_start),_month(coverage_end)
    if start>end:
        raise ValueError('coverage start after end')
    out=dict(population_id=population_id,coverage_start=start,coverage_end=end,
             unknown_payoff_cause=0,verified_sales=0,verified_nonrefinances=0,
             verified_selected_refinances=0,credit_or_other_source_removals=0,
             missing_follow_up=0,date_conflicts=0,no_recorded_exit=0,
             outside_coverage=0,unrecognized_records=0,input_records=len(events))
    for row in events:
        month=_month(row['month'])
        if not start<=month<=end:
            out['outside_coverage']+=1
            continue
        event=row['event']
        if event=='linked_harp_payoff':
            out['verified_selected_refinances']+=1
        elif event in ('unmatched_payoff','unmapped_payoff_or_maturity','linked_date_conflict'):
            out['unknown_payoff_cause']+=1
            out['date_conflicts']+=int(event=='linked_date_conflict')
        elif event in ('verified_sale','verified_nonrefinance'):
            if row.get('source_verified') is True and row.get('evidence_id'):
                out['verified_sales' if event=='verified_sale' else 'verified_nonrefinances']+=1
            else:
                out['unknown_payoff_cause']+=1
        elif event in ('other_source_removal','credit_exit'):
            out['credit_or_other_source_removals']+=1
        elif event in ('unknown_missing_report','missing_follow_up'):
            out['missing_follow_up']+=1
        elif event in ('observed_nonterminal','observed_no_recorded_exit'):
            out['no_recorded_exit']+=1
        else:
            out['unrecognized_records']+=1
    n=out['verified_selected_refinances']
    out['refinance_classification_count_bounds']=[n,n+out['unknown_payoff_cause']]
    out['bounds_kind']='classification_scenario_bounds_not_sampling_interval'
    out['sensitive_intensity_share_estimated']=False
    out['interpretation']='Accepted source-linked selected-program events only; absence of a link is not a sale or non-refinance. Verified sales and other nonrefinances are disjoint categories.'
    return out
