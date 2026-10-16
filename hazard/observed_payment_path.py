"""Opt-in payment components for the existing monthly simulation.

Current rates affect scheduling only; hazard coupons remain unchanged. Partial
prepayment is allocated proportionally, payments are recast after that allocation,
and deferred maturity collections are unknown. No future modification is inferred.
"""
import numpy as np
from hazard.observed_payment_rule import payment_scenario

PAYMENT_RULE='level_payment_to_legal_maturity_proportional_prepayment'


class ObservedPaymentState:
    def __init__(self, loans, pool, *, payment_rule):
        if payment_rule != PAYMENT_RULE:
            raise ValueError('Unsupported explicit payment path rule')
        fields={'loan_id','balance','interest_bearing_upb','current_non_ib_upb',
                'current_note_rate','remaining_months'}
        if not fields.issubset(loans.columns):
            raise ValueError('Missing observed payment components, rate or term')
        if tuple(loans['loan_id']) != tuple(pool.loan_ids):
            raise ValueError('Payment rows must align exactly with the pool')
        self.pool=pool
        self.payment_rule=payment_rule
        for row in loans.select(sorted(fields)).iter_rows(named=True):
            payment_scenario(total_principal=row['balance'],
                interest_bearing=row['interest_bearing_upb'],deferred=row['current_non_ib_upb'],
                current_rate_decimal=row['current_note_rate'],remaining_legal_months=row['remaining_months'],
                payment_rule='level_payment_to_legal_maturity')
        source=loans['balance'].to_numpy().astype(float)
        if np.any((source==0)&(pool.balance!=0)):
            raise ValueError('Cannot allocate a positive pool balance from zero source balance')
        scale=np.divide(pool.balance,source,out=np.zeros_like(source),where=source>0)
        if np.any(~np.isfinite(scale)) or np.any(scale<0):
            raise ValueError('Invalid payment component scaling')
        self.interest_bearing=loans['interest_bearing_upb'].to_numpy().astype(float)*scale
        self.deferred=loans['current_non_ib_upb'].to_numpy().astype(float)*scale
        self.rate=loans['current_note_rate'].to_numpy().astype(float)
        self.months=loans['remaining_months'].to_numpy().astype(float)
        self.residual=(source-loans['interest_bearing_upb'].to_numpy()-
                       loans['current_non_ib_upb'].to_numpy())*scale
        self.total=pool.balance.copy()
        self.completed_months=0
        self._check(pool)

    def _check(self,pool):
        if pool is not self.pool:
            raise ValueError('Payment components belong to a different pool')
        if not np.allclose(self.total,pool.balance,rtol=1e-12,atol=1e-8):
            raise ValueError('Payment component state does not match pool balance')
        if not np.allclose(self.total,self.interest_bearing+self.deferred+self.residual,
                           rtol=1e-12,atol=1e-8):
            raise ValueError('Payment components do not reconcile')

    def before_month(self,pool):
        self._check(pool)
        if np.any(pool.active_mask & (self.months<=0) & (self.interest_bearing>1e-8)):
            raise ValueError('Unknown amortization beyond legal maturity')

    def after_exits(self,pool):
        if pool is not self.pool:
            raise ValueError('Payment components belong to a different pool')
        if np.any(pool.balance>self.total+1e-8):
            raise ValueError('Unspecified balance addition in payment scenario')
        ratio=np.divide(pool.balance,self.total,out=np.zeros_like(self.total),where=self.total>0)
        self.interest_bearing*=ratio
        self.deferred*=ratio
        self.residual*=ratio
        self.total=pool.balance.copy()
        self._check(pool)

    def scheduled_principal(self,pool,i):
        if self.months[i]<=0:
            # Deferred principal remains debt; collection is not inferred.
            return 0.
        # Components were validated before scaling. Use their exact scaled sum
        # here so a permissible source rounding residual is not reclassified.
        value=payment_scenario(total_principal=self.interest_bearing[i]+self.deferred[i],
            interest_bearing=self.interest_bearing[i],deferred=self.deferred[i],
            current_rate_decimal=self.rate[i],remaining_legal_months=self.months[i],
            payment_rule='level_payment_to_legal_maturity')
        amount=min(value.scheduled_principal,float(pool.balance[i]))
        self.interest_bearing[i]-=amount
        return amount

    def finish_month(self,pool):
        self.months=np.maximum(self.months-1,0)
        self.total=pool.balance.copy()
        self.completed_months+=1
        self._check(pool)

    def summary(self):
        return dict(payment_rule=self.payment_rule,completed_months=self.completed_months,
            total_principal=float(self.total.sum()),interest_bearing=float(self.interest_bearing.sum()),
            deferred=float(self.deferred.sum()),component_residual=float(self.residual.sum()),
            matured_unresolved_principal=float(self.total[self.months==0].sum()),
            deferred_maturity_cash=None,actual_payment_verified=False,
            hazard_rate_basis='existing_pool_coupon',payment_rate_basis='fixed_current_note_rate')
