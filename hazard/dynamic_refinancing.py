"""Proposed amortizing repeated-refinancing scenario, with no production hooks.

This is not a Dunn--Spatt replication, fitted hazard or lender pricing model.
All market quotes, Markov transitions, discount rates and cash cost fractions
are supplied. There is no sale, default, tax or qualification mechanism.

At the decision date, just after the previous payment, refinancing replaces the
coupon immediately with the current supplied market quote, keeping principal
and remaining term. Its unfinanced cash cost is fraction * opening principal.
Next month's payment and transition occur one month later. The replacement
mortgage retains future refinancing opportunities. A zero-month state has zero
debt. Positive debt may never be truncated at an artificial horizon.

Proportional costs give exact degree-one balance homogeneity: J(b,c,n,x) =
b*v[n,c,x]. No balance interpolation/grid is used. On a supplied rate grid the
backward recursion is exact up to floating arithmetic and a declared wait-tie
tolerance, measured per dollar of opening principal.
"""
from dataclasses import dataclass
import numpy as np


def _nonnegative_scalar(value, name):
    array = np.asarray(value, dtype=float)
    if array.ndim != 0 or not np.isfinite(array) or array < 0:
        raise ValueError(name + ' must be a finite nonnegative scalar')
    return float(array)


def _integer(value, name, maximum=None):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(name + ' must be an integer')
    number = _nonnegative_scalar(value, name)
    if number != int(number) or (maximum is not None and number >= maximum):
        raise ValueError(name + ' is out of range or noninteger')
    return int(number)


def _payment_fraction(coupon, months):
    monthly = coupon / 12.
    if monthly == 0:
        return 1. / months
    return monthly / (-np.expm1(-months*np.log1p(monthly)))


@dataclass(frozen=True)
class DynamicRefinancingSolution:
    initial_coupon: float
    market_rates: np.ndarray
    transition_matrix: np.ndarray
    coupons: np.ndarray
    remaining_months: int
    discount_rate: float
    cost_fraction: float
    tie_tolerance: float
    normalized_values: np.ndarray
    wait_values: np.ndarray
    exercise_values: np.ndarray
    refinance: np.ndarray

    def value(self, balance, *, market_state):
        """Expected optimal borrower cash costs in USD at the initial coupon."""
        balance = _nonnegative_scalar(balance, 'balance')
        state = _integer(market_state, 'market_state', len(self.market_rates))
        if self.remaining_months == 0 and balance != 0:
            raise ValueError('Zero remaining months require zero balance')
        index = int(np.searchsorted(self.coupons, self.initial_coupon))
        value = balance*self.normalized_values[self.remaining_months, index, state]
        if not np.isfinite(value):
            raise ValueError('Dollar value overflowed')
        return float(value)

    def trace(self, balance, *, market_states):
        """Trace a supplied possible path; realized cost is not expected value.

        Exactly one decision-date market state per contractual month is required.
        Later state transitions must have positive supplied Markov probability.
        Cash refinancing cost is paid at date t; payment at date t+1. A zero
        initial balance generates no refinancing costs or exercise events.
        """
        balance = _nonnegative_scalar(balance, 'balance')
        states = list(market_states)
        if len(states) != self.remaining_months:
            raise ValueError('One market state is required per contractual month')
        states = [_integer(x, 'market_state', len(self.market_rates)) for x in states]
        if any(self.transition_matrix[left, right] <= 0 for left, right in zip(states, states[1:])):
            raise ValueError('Path contains an impossible Markov transition')
        if not states and balance != 0:
            raise ValueError('Zero remaining months require zero balance')
        coupon = self.initial_coupon
        monthly_discount = 1. / (1.+self.discount_rate/12.)
        cash_value = 0.
        total_fees = 0.
        rows = []
        for month, state in enumerate(states):
            n = self.remaining_months-month
            ci = int(np.searchsorted(self.coupons, coupon))
            exercise = bool(balance > 0 and self.refinance[n, ci, state])
            old_coupon = coupon
            fee = self.cost_fraction*balance if exercise else 0.
            if exercise:
                coupon = float(self.market_rates[state])
            payment = balance*_payment_fraction(coupon, n)
            closing = 0. if n == 1 else max(balance*(1.+coupon/12.)-payment, 0.)
            cash_value += monthly_discount**month*fee + monthly_discount**(month+1)*payment
            total_fees += fee
            rows.append(dict(month=month, remaining_months=n, market_state=state,
                             opening_balance=balance, prior_coupon=old_coupon,
                             market_quote=float(self.market_rates[state]), coupon=coupon,
                             refinanced=exercise, cash_refinancing_cost=fee,
                             scheduled_payment=payment, closing_balance=closing))
            balance = closing
        if not np.isfinite(cash_value) or not np.isfinite(total_fees):
            raise ValueError('Traced dollar cash costs overflowed')
        return dict(months=rows, discounted_cash_cost=float(cash_value),
                    total_cash_refinancing_cost=float(total_fees), ending_balance=float(balance))


def solve_dynamic_refinancing(*, initial_coupon, market_rates, transition_matrix,
                             remaining_months, discount_rate, cost_fraction,
                             tie_tolerance=1e-12):
    """Solve the supplied finite-horizon scenario through contractual maturity.

    All rates are annual nominal decimals with monthly rate = annual / 12.
    Matrix rows give next month's market probabilities; rows must sum to one
    within 1e-12, and only numerical roundoff is normalized. Market states may
    share quotes (e.g. a deterministic clock). Coupons are the union of the
    initial coupon and supplied quotes; refinancing always picks today's quote.
    There is no fixed-dollar cost component. Equal branch costs select wait.
    """
    initial_coupon = _nonnegative_scalar(initial_coupon, 'initial_coupon')
    discount_rate = _nonnegative_scalar(discount_rate, 'discount_rate')
    cost_fraction = _nonnegative_scalar(cost_fraction, 'cost_fraction')
    tie_tolerance = _nonnegative_scalar(tie_tolerance, 'tie_tolerance')
    months = _integer(remaining_months, 'remaining_months')
    rates = np.array(market_rates, dtype=float, copy=True)
    if rates.ndim != 1 or not rates.size or not np.isfinite(rates).all() or np.any(rates < 0):
        raise ValueError('A nonempty finite nonnegative one-dimensional rate grid is required')
    matrix = np.array(transition_matrix, dtype=float, copy=True)
    if (matrix.shape != (rates.size, rates.size) or not np.isfinite(matrix).all()
            or np.any(matrix < 0) or np.any(matrix > 1)):
        raise ValueError('A square finite probability matrix aligned with rates is required')
    row_mass = matrix.sum(axis=1)
    if not np.allclose(row_mass, 1., rtol=0., atol=1e-12):
        raise ValueError('Every transition row must sum to one')
    matrix /= row_mass[:, None]
    coupons = np.unique(np.append(rates, initial_coupon))
    quote_indices = np.searchsorted(coupons, rates)
    shape = (months+1, coupons.size, rates.size)
    values = np.zeros(shape)
    waits = np.zeros(shape)
    exercises = np.zeros(shape)
    policy = np.zeros(shape, dtype=bool)
    discount = 1. / (1.+discount_rate/12.)
    for n in range(1, months+1):
        payment = np.array([_payment_fraction(c, n) for c in coupons])
        residual = np.zeros(coupons.size) if n == 1 else 1.+coupons/12.-payment
        if np.any(residual < -1e-12):
            raise ValueError('Computed amortization fraction is negative')
        residual = np.maximum(residual, 0.)
        waits[n] = discount*(payment[:, None]+residual[:, None]*(np.einsum('cj,xj->cx', values[n-1], matrix, optimize=False)))
        exercise_by_state = cost_fraction + waits[n, quote_indices, np.arange(rates.size)]
        exercises[n] = exercise_by_state[None, :]
        policy[n] = exercises[n] < waits[n]-tie_tolerance
        values[n] = np.where(policy[n], exercises[n], waits[n])
    if not all(np.isfinite(a).all() for a in (values, waits, exercises)):
        raise ValueError('Computed borrower costs are nonfinite')
    for array in (rates, matrix, coupons, values, waits, exercises, policy):
        array.setflags(write=False)
    return DynamicRefinancingSolution(initial_coupon, rates, matrix, coupons, months,
                                     discount_rate, cost_fraction, tie_tolerance,
                                     values, waits, exercises, policy)
