"""Two-stage supplied-quote incentive/exercise overlay; no production hooks.

alpha is one monthly conditional exercise intensity. It does not separately
identify attention/qualification/delay, nor enter the optimal-control recursion.
The gate retains immediate future exercise availability from the original
solver. Within-month gates and competing intensities are held constant. The
result is a reduced-form overlay, not optimal delayed exercise or loan pricing.

Fitting requires complete cause-labeled *borrower counts* and a documented
comparable opening-loan risk set. Contract metadata are declarations, not
software authentication of source labels. No generic payoff flag is a cause.
"""
import hashlib
import json
import math
import re

import numpy as np
from scipy.optimize import brentq

from .dynamic_refinancing import DynamicRefinancingSolution, _integer
from .structural_sale_extension import competing_probabilities

CAUSES = ('survive', 'refinancing', 'sale', 'other', 'default')
PROVENANCE = ('label_provenance', 'risk_set_definition', 'incentive_provenance',
              'eligibility_provenance', 'competing_intensity_provenance')


def _number(value, name, *, nonnegative=True):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(name + ' must be a finite number')
    a = np.asarray(value, dtype=float)
    if a.ndim != 0 or not np.isfinite(a) or (nonnegative and a < 0):
        raise ValueError(name + ' must be a finite valid scalar')
    return float(a)


def _boolean(value, name):
    if not isinstance(value, (bool, np.bool_)):
        raise ValueError(name + ' must be an explicit boolean')
    return bool(value)


def _month(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-(0[1-9]|1[0-2])', value) or value[:4] == '0000':
        raise ValueError('month must be YYYY-MM')
    return value


def _contract(contract):
    if not isinstance(contract, dict):
        raise ValueError('An explicit data contract is required')
    if (contract.get('complete_first_exit_labels') is not True
            or contract.get('comparable_outstanding_risk_set') is not True):
        raise ValueError('Complete first-exit labels and comparable risk set required')
    if contract.get('refinancing_scope') != 'same_balance_remaining_term_rate_term':
        raise ValueError('Refinance scope must match the supplied borrower objective')
    if any(not isinstance(contract.get(k), str) or not contract[k].strip() for k in PROVENANCE):
        raise ValueError('All five data provenance descriptions are required')
    if contract.get('evidence_class') not in ('synthetic', 'observational'):
        raise ValueError('Declare synthetic or observational evidence class')
    return {k: contract[k] for k in ('complete_first_exit_labels', 'comparable_outstanding_risk_set',
                                    'refinancing_scope', 'evidence_class') + PROVENANCE}


def dynamic_incentive(solution, *, market_state, remaining_months=None, coupon=None):
    """Signed branch difference per dollar of opening principal, including fees.

    Positive above tie_tolerance selects immediate exercise in the supplied
    solver. This is not static lifetime savings or an estimated hazard. States
    are decision dates, just after the prior payment. Zero remaining term has
    no exercise region. An optional coupon must be on the solved coupon grid.
    """
    if not isinstance(solution, DynamicRefinancingSolution):
        raise ValueError('A solved DynamicRefinancingSolution is required')
    n = solution.remaining_months if remaining_months is None else _integer(remaining_months, 'remaining_months')
    if n > solution.remaining_months:
        raise ValueError('Remaining term exceeds solved horizon')
    state = _integer(market_state, 'market_state', len(solution.market_rates))
    c = solution.initial_coupon if coupon is None else _number(coupon, 'coupon')
    matches = np.flatnonzero(solution.coupons == c)
    if len(matches) != 1:
        raise ValueError('Coupon must be on the solved grid')
    ci = int(matches[0])
    advantage = float(solution.wait_values[n, ci, state] - solution.exercise_values[n, ci, state])
    return dict(advantage_fraction=advantage, tie_tolerance=solution.tie_tolerance,
                exercise_now=bool(solution.refinance[n, ci, state]), remaining_months=n,
                coupon=float(c), market_quote=float(solution.market_rates[state]))


def bridge_probabilities(*, advantage_fraction, eligible, arrival_intensity,
                         sale=0., other=0., default=0., tie_tolerance=1e-12):
    """Full-month probabilities for mutually exclusive first loan exits.

    alpha has units per month. Eligibility and the strict exercise gate are
    binary; all rates/gates remain constant during the month. Supplied sale is
    loan termination on sale, not home-sale incidence. No quarter/month mobility
    parameter conversion or intensity-by-positive-savings formula is inferred.
    """
    advantage = _number(advantage_fraction, 'advantage_fraction', nonnegative=False)
    eligible = _boolean(eligible, 'eligible')
    alpha = _number(arrival_intensity, 'arrival_intensity')
    tolerance = _number(tie_tolerance, 'tie_tolerance')
    other_rates = {k: _number(v, k) for k, v in dict(sale=sale, other=other, default=default).items()}
    refi = alpha if eligible and advantage > tolerance else 0.
    p = competing_probabilities(refinancing=refi, **other_rates)
    result = {k: float(v) for k, v in p.items()}
    result['survive'] = float(np.exp(-(refi + sum(other_rates.values()))))
    return result


def _cells(rows):
    validated = []
    keys = set()
    for row in rows:
        month = _month(row['month'])
        cell_id = row.get('cell_id')
        if not isinstance(cell_id, str) or not cell_id.strip():
            raise ValueError('Nonempty risk cell identifier required')
        key = (month, cell_id)
        if key in keys:
            raise ValueError('Duplicate cell/month risks double-count exposure')
        keys.add(key)
        exposure = _integer(row.get('exposure'), 'exposure')
        if not exposure:
            raise ValueError('Positive opening borrower exposure required')
        counts = row.get('counts')
        if not isinstance(counts, dict) or set(counts) != set(CAUSES):
            raise ValueError('Exactly five complete first-exit causes required; unknown payoffs are not labels')
        counts = {k: _integer(counts[k], k) for k in CAUSES}
        if sum(counts.values()) != exposure:
            raise ValueError('Complete exclusive outcome counts must equal opening exposure')
        eligible = _boolean(row.get('eligible'), 'eligible')
        advantage = _number(row.get('advantage_fraction'), 'advantage_fraction', nonnegative=False)
        tolerance = _number(row.get('tie_tolerance'), 'tie_tolerance')
        rates = {k: _number(row.get(k), k) for k in ('sale', 'other', 'default')}
        if not np.isfinite(sum(rates.values())):
            raise ValueError('Total competing intensity must be finite')
        validated.append(dict(cell_id=cell_id, month=month, exposure=exposure, counts=counts,
                              eligible=eligible, advantage_fraction=advantage,
                              tie_tolerance=tolerance, **rates))
    return sorted(validated, key=lambda r: (r['month'], r['cell_id']))


def _probabilities(row, alpha):
    return bridge_probabilities(**{k: row[k] for k in ('advantage_fraction', 'eligible', 'tie_tolerance',
                                                      'sale', 'other', 'default')}, arrival_intensity=alpha)


def _intensities(row, alpha):
    active = row['eligible'] and row['advantage_fraction'] > row['tie_tolerance']
    return dict(refinancing=alpha if active else 0.,
                **{k: row[k] for k in ('sale', 'other', 'default')})


def _nll(cells, alpha):
    value = 0.
    for row in cells:
        rates = _intensities(row, alpha)
        total = sum(rates.values())
        # Survival log probability is -total even when exp(-total) underflows.
        value += row['counts']['survive'] * total
        if total == 0:
            if row['counts']['survive'] != row['exposure']:
                return float('inf')
            continue
        log_scale = math.log(-math.expm1(-total)) - math.log(total)
        for cause, rate in rates.items():
            count = row['counts'][cause]
            if not count:
                continue
            if rate == 0:
                return float('inf')
            value -= count * (math.log(rate) + log_scale)
    return float(value)


def _scale_derivative(total):
    # d log((1-exp(-total))/total) / d total. Stable near zero and at high rates.
    if total < 1e-4:
        return -.5 + total/12. - total**3/720.
    return (0. if total > 700 else 1./np.expm1(total)) - 1./total


def fit_exercise_rate(rows, *, training_end, contract, maximum_arrival=100.):
    """Conditional multinomial MLE for alpha on complete training risk cells.

    Supplied incentive, eligibility and other intensities are frozen, not fitted.
    Filter by calendar month BEFORE inspecting outcome fields. Post-training
    outcomes do not enter validation, likelihood or training hash. No empirical
    estimate can be inferred from synthetic inputs. Boundary/not-identified
    outputs must not silently become usable positive fitted intensities.
    """
    declared = _contract(contract)
    end = _month(training_end)
    upper = _number(maximum_arrival, 'maximum_arrival')
    if upper <= 0:
        raise ValueError('A positive numerical upper search bound is required')
    selected = []
    ignored = 0
    for row in rows:
        if _month(row['month']) <= end:
            selected.append(row)
        else:
            ignored += 1
    cells = _cells(selected)
    if not cells:
        raise ValueError('No training risk cells supplied')
    active = [r for r in cells if r['eligible'] and r['advantage_fraction'] > r['tie_tolerance']]
    # Validate model support for *all* observed causes, without dropping rows.
    if not np.isfinite(_nll(cells, 1.)):
        raise ValueError('Observed training cause has zero model probability; revise labels/scope/specification')
    events = sum(r['counts']['refinancing'] for r in active)
    exposure = sum(r['exposure'] for r in active)
    if not exposure:
        status, alpha = 'not_identified', None
    elif not events:
        status, alpha = 'zero_boundary', 0.
    else:
        def derivative(a):
            return sum(r['counts']['survive'] - r['counts']['refinancing']/a
                       - (r['exposure']-r['counts']['survive'])*_scale_derivative(
                           a+sum(r[k] for k in ('sale', 'other', 'default'))) for r in active)
        if derivative(upper) <= 0:
            status, alpha = 'upper_boundary', None
        else:
            # A negative derivative near zero follows from positive refi counts.
            lower = min(1e-12, upper*1e-6)
            if derivative(lower) >= 0:
                status, alpha = 'lower_numerical_boundary', None
            else:
                alpha = float(brentq(derivative, lower, upper, xtol=1e-13, rtol=1e-12))
                status = 'finite'
    payload = dict(contract=declared, training_end=end, cells=cells)
    training_hash = hashlib.sha256(json.dumps(payload, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return dict(status=status, arrival_intensity=alpha, unit='per_month', training_end=end,
                training_exposure=sum(r['exposure'] for r in cells), exercise_region_exposure=exposure,
                refinancing_events=events, training_cells=len(cells), ignored_future_cells=ignored,
                numerical_upper_bound=upper, evidence_class=declared['evidence_class'], contract=declared,
                training_sha256=training_hash,
                negative_log_likelihood=_nll(cells, alpha) if alpha is not None else None)


def evaluate_exercise_rate(rows, *, fit, contract):
    """Score later cells with frozen alpha; record every impossible held-out event.

    Scores are borrower-count weighted. No re-fitting, dropped incompatible
    cells, causal interpretation or interpretation of alpha as a mechanism share.
    """
    declared = _contract(contract)
    if declared != fit.get('contract'):
        raise ValueError('Training and evaluation data contracts must match')
    if fit.get('status') not in ('finite', 'zero_boundary'):
        raise ValueError('Cannot evaluate a nonidentified or numerical-boundary fit')
    alpha = _number(fit['arrival_intensity'], 'arrival_intensity')
    end = _month(fit['training_end'])
    cells = _cells(rows)
    if not cells or any(r['month'] <= end for r in cells):
        raise ValueError('Evaluation requires only nonempty later risk cells')
    incompatible = 0
    forecasts = []
    exposure = sum(r['exposure'] for r in cells)
    refi_squared_error = 0.
    for row in cells:
        p = _probabilities(row, alpha)
        rates = _intensities(row, alpha)
        impossible = sum(row['counts'][k] for k, rate in rates.items() if rate == 0)
        incompatible += impossible
        refi_squared_error += row['exposure'] * (p['refinancing'] - row['counts']['refinancing']/row['exposure'])**2
        forecasts.append(dict(month=row['month'], cell_id=row['cell_id'], exposure=row['exposure'],
                              probabilities=p, observed_counts=row['counts'], incompatible_event_count=impossible))
    return dict(status='incompatible_events' if incompatible else 'scored', exposure=exposure,
                incompatible_event_count=incompatible,
                mean_negative_log_likelihood=None if incompatible else _nll(cells, alpha)/exposure,
                refinancing_probability_rmse=float(np.sqrt(refi_squared_error/exposure)),
                arrival_intensity=alpha, training_sha256=fit['training_sha256'],
                evidence_class=declared['evidence_class'], forecasts=forecasts)
