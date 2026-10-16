"""Audit target mass without renormalizing absent sample support away."""
from datetime import date
import math


def audit_transport(sample_cells, target_cells, *, coupon_basis, as_of_date):
    date.fromisoformat(as_of_date)
    if coupon_basis not in ('security_pass_through','borrower_note_rate'):
        raise ValueError('explicit coupon basis required')
    sample={r['cell'] for r in sample_cells}
    total=supported=0.0
    unmapped=[]
    for row in target_cells:
        value=row['weight']
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<0:
            raise ValueError('finite nonnegative target weights required')
        total+=value
        if row['cell'] in sample:
            supported+=value
        else:
            unmapped.append(dict(row))
    if total>1+1e-10:
        raise ValueError('target weights must use the full target denominator and sum to at most one')
    residual=max(0.,1.-total) if target_cells else None
    return dict(coupon_basis=coupon_basis,as_of_date=as_of_date,
        target_inventory_available=bool(target_cells),provided_target_share=total if target_cells else None,
        supported_target_share=supported if target_cells else None,
        unsupported_target_share=1.-supported if target_cells else None,
        unmapped_residual_share=residual,unmapped_target_cells=unmapped,
        support_dimensions='Caller must define cells jointly by issuer, vintage, coupon basis, age, term, credit state and balance population; label matching alone does not verify those dimensions.',
        full_portfolio_verified=False,receipt_mapping_verified=False,
        status='partial_cell_overlap_only' if target_cells else 'target_holdings_unverified',
        projection_authorized_by_audit=False)
