"""
Agent-Based Model: The Mortgage "Lock-In Effect"
=================================================
Simulates how rational households decide to move or stay when subjected to
an interest-rate shock, comparing two institutional regimes:

  * U.S. system     -- mortgages are prepaid at PAR (outstanding principal),
                       so a below-market mortgage is a golden handcuff.
  * Danish system   -- borrowers may buy back their mortgage at MARKET PRICE
                       (the PV of remaining cash flows discounted at the
                       current market rate, capped at par). When rates rise,
                       the debt can be retired at a discount, releasing the
                       lock-in.

Output: a CPR (Conditional Prepayment Rate) S-curve for both systems across
market rates from 2.0% to 8.0%.
"""

from typing import Optional

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from fredapi import Fred

from paths import (
    ABM_CPR_SURFACE_CSV,
    ABM_LOCKIN_RESULTS_CSV,
    ABM_LOCKIN_SCURVE_PNG,
)

# ---------------------------------------------------------------------------
# Global calibration constants
# ---------------------------------------------------------------------------
RNG_SEED = 42
N_HOUSEHOLDS = 10_000

# 3.0% is the empirical coupon of the 2020-2021 pandemic origination cohort:
# the Freddie Mac PMMS 30-year average hovered between 2.8% and 3.2% during
# that window, which is where the bulk of the Fed's trapped MBS originated.
ORIGINAL_RATE = 0.03
TERM_YEARS = 30
MONTHS_ELAPSED = 60           # 5 years into the mortgage at simulation start

EXPECTED_STAY_MONTHS = 60     # horizon over which payment penalties are felt
TRANSACTION_COST_MEAN = 0.07  # 7% mean (realtor commissions, origination, moving)
TRANSACTION_COST_STD = 0.015  # ~1.5% std dev → 68% of agents pay 5.5%-8.5%
TRANSACTION_COST_FLOOR = 0.02 # minimum 2% (discount broker / FSBO)
TRANSACTION_COST_CAP = 0.12   # maximum 12% (high-cost markets + relocation)
MOBILITY_DESIRE_SCALE = 12_500  # default scale; recalibrated at runtime

# --- Behavioral extensions (literature-grounded, not tuned to any target) ---
# DTI hard wall: CFPB QM/ATR threshold, 12 CFR 1026.43(e)(2)(vi).
# Front-end only (mortgage payment / gross income); no other-debt data.
DTI_MAX = 0.43

# Loss aversion: Kahneman & Tversky (1979, 1992) prospect-theory coefficient.
# Payment *increases* (losses) are perceived at lambda x their dollar value;
# payment *decreases* (gains) are unscaled.
LOSS_AVERSION_LAMBDA = 2.25

# Wait-and-see: when the 6-month rate change exceeds the threshold, a fixed
# fraction of the population freezes regardless of their cost-benefit result.
# These are stated assumptions, not empirically sourced — sensitivity-test later.
WAIT_AND_SEE_RATE_THRESHOLD = 0.015   # 150 bps over 6 months
WAIT_AND_SEE_PROB = 0.20              # 20% of cleared movers freeze

RATE_GRID = np.arange(0.02, 0.0801, 0.005)  # 2.0% -> 8.0% step 0.5%
# Friction grid for the 2D CPR surface — widened to 5%-17.5% so the sensitivity
# analysis (which sweeps base friction and penalty caps) can interpolate at
# extreme friction levels without clamping at a grid boundary.
FRICTION_GRID = np.arange(0.05, 0.18, 0.005)

# Rate-velocity grid for the 3D surface: 6-month change in the 30-year rate.
# Covers the observed 2021-2025 range (roughly -1pp to +3pp) plus buffer.
RATE_VELOCITY_GRID = np.arange(-0.01, 0.0351, 0.005)  # -1.0% to +3.5%, step 0.5%

# FRED settings (same key as fed_mbs_extension_risk.py)
import sys as _sys
from pathlib import Path as _Path
_REPO_ROOT = _Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_REPO_ROOT))
from common.fred_key import get_fred_api_key  # noqa: E402
FRED_API_KEY = get_fred_api_key()
FALLBACK_MEDIAN_INCOME = 80_000       # used if FRED is unreachable
FALLBACK_MEDIAN_HOME_VALUE = 420_000  # used if FRED is unreachable


def fetch_macro_from_fred(api_key: str = FRED_API_KEY) -> tuple:
    """
    Pull the latest empirical medians used to seed the household population:

      * MEHOINUSA672N -- Real Median Household Income (annual)
      * MSPUS         -- Median Sales Price of Houses Sold (quarterly)

    Falls back to hardcoded defaults if the API is unreachable so the
    simulation still runs offline.
    """
    try:
        fred = Fred(api_key=api_key)
        income = fred.get_series("MEHOINUSA672N").dropna().iloc[-1]
        home_value = fred.get_series("MSPUS").dropna().iloc[-1]
        print(f"FRED medians fetched: income ${income:,.0f}, "
              f"home price ${home_value:,.0f}")
        return float(income), float(home_value)
    except Exception as exc:
        print(f"FRED fetch failed ({exc}); using fallback medians.")
        return FALLBACK_MEDIAN_INCOME, FALLBACK_MEDIAN_HOME_VALUE


# ---------------------------------------------------------------------------
# Class 1: Mortgage
# ---------------------------------------------------------------------------
class Mortgage:
    """A fixed-rate, fully amortizing mortgage."""

    def __init__(self, principal: float, annual_rate: float,
                 term_years: int = TERM_YEARS,
                 months_elapsed: int = MONTHS_ELAPSED):
        self.principal = principal
        self.annual_rate = annual_rate
        self.term_years = term_years
        self.months_elapsed = months_elapsed

    # -- amortization mechanics --------------------------------------------
    def calculate_monthly_payment(self) -> float:
        """Standard fixed-rate annuity payment."""
        r = self.annual_rate / 12
        n = self.term_years * 12
        if r == 0:
            return self.principal / n
        return self.principal * r / (1 - (1 + r) ** -n)

    def remaining_term_months(self) -> int:
        return self.term_years * 12 - self.months_elapsed

    def outstanding_principal(self) -> float:
        """Closed-form remaining balance after months_elapsed payments."""
        r = self.annual_rate / 12
        n = self.term_years * 12
        k = self.months_elapsed
        if r == 0:
            return self.principal * (n - k) / n
        growth = (1 + r) ** k
        total = (1 + r) ** n
        return self.principal * (total - growth) / (total - 1)

    # -- payoff rules under the two institutional regimes -------------------
    def get_payoff_cost_us(self, current_market_rate: float) -> float:
        """U.S. rule: prepayment always settles at par (outstanding balance)."""
        return self.outstanding_principal()

    def get_payoff_cost_danish(self, current_market_rate: float) -> float:
        """
        Danish rule: the borrower can buy back their debt at market price --
        the PV of remaining scheduled payments discounted at the current
        market rate. Since Danish mortgages are also callable at par, the
        payoff is capped at the outstanding principal (relevant when market
        rates are BELOW the coupon).
        """
        r_mkt = current_market_rate / 12
        n_rem = self.remaining_term_months()
        pmt = self.calculate_monthly_payment()

        if r_mkt == 0:
            market_value = pmt * n_rem
        else:
            market_value = pmt * (1 - (1 + r_mkt) ** -n_rem) / r_mkt

        return min(market_value, self.outstanding_principal())


# ---------------------------------------------------------------------------
# Class 2: Household
# ---------------------------------------------------------------------------
class Household:
    """A rational household weighing financial penalty against desire to move."""

    def __init__(self, income: float, current_home_value: float,
                 mortgage: Mortgage, mobility_desire: float,
                 transaction_cost_rate: float,
                 patience_draw: float = 1.0):
        self.income = income
        self.current_home_value = current_home_value
        self.mortgage = mortgage
        self.mobility_desire = mobility_desire  # $-equivalent benefit of moving
        self.transaction_cost_rate = transaction_cost_rate
        self.patience_draw = patience_draw  # U[0,1]; used for wait-and-see gate

    def evaluate_move(self, current_market_rate: float,
                      system_type: str,
                      friction: float = TRANSACTION_COST_MEAN,
                      rate_velocity: float = 0.0) -> bool:
        """
        Decide whether to move under the given mortgage system.

        Three behavioral gates are applied in sequence:

        1. DTI hard wall — if the new mortgage payment exceeds 43% of gross
           monthly income, the bank rejects the loan (QM/ATR rule).
        2. Asymmetric loss aversion — payment *increases* are perceived at
           LOSS_AVERSION_LAMBDA times their dollar value (Kahneman & Tversky);
           payment decreases are unscaled.
        3. Wait-and-see — when recent rate velocity exceeds the threshold,
           a fixed share of otherwise-cleared movers freezes.

        `friction` is the macro base transaction-cost rate for the month
        (defaults to the static 7% mean). `rate_velocity` is the 6-month
        change in the 30-year rate (decimal, e.g. 0.02 = 200 bps).
        """
        if system_type == "US":
            payoff = self.mortgage.get_payoff_cost_us(current_market_rate)
        elif system_type == "Danish":
            payoff = self.mortgage.get_payoff_cost_danish(current_market_rate)
        else:
            raise ValueError(f"Unknown system_type: {system_type}")

        # Same-term replacement loan (see _new_payment_vec for why).
        new_loan = Mortgage(payoff, current_market_rate,
                            term_years=self.mortgage.term_years,
                            months_elapsed=0)
        new_payment = new_loan.calculate_monthly_payment()
        current_payment = self.mortgage.calculate_monthly_payment()

        # Gate 1: DTI hard wall (front-end ratio, mortgage payment only)
        monthly_income = self.income / 12
        if monthly_income > 0 and new_payment / monthly_income > DTI_MAX:
            return False

        # Gate 2: asymmetric loss aversion on the payment change
        monthly_penalty = new_payment - current_payment
        if monthly_penalty > 0:
            monthly_penalty *= LOSS_AVERSION_LAMBDA

        # Effective transaction cost = macro friction shifted by the agent's
        # idiosyncratic offset around the base mean, clipped to sane bounds.
        offset = self.transaction_cost_rate - TRANSACTION_COST_MEAN
        eff_rate = float(np.clip(friction + offset,
                                 TRANSACTION_COST_FLOOR, TRANSACTION_COST_CAP))
        transaction_cost = self.current_home_value * eff_rate
        total_penalty = monthly_penalty * EXPECTED_STAY_MONTHS + transaction_cost

        if self.mobility_desire <= total_penalty:
            return False

        # Gate 3: wait-and-see freeze under high rate velocity
        if (rate_velocity > WAIT_AND_SEE_RATE_THRESHOLD
                and self.patience_draw < WAIT_AND_SEE_PROB):
            return False

        return True


# ---------------------------------------------------------------------------
# Class 3: HousingMarketEngine
# ---------------------------------------------------------------------------
class HousingMarketEngine:
    """Generates the population and runs the rate-shock experiment."""

    def __init__(self, n_households: int = N_HOUSEHOLDS,
                 seed: int = RNG_SEED,
                 median_income: float = None,
                 median_home_value: float = None,
                 mobility_scale: float = MOBILITY_DESIRE_SCALE):
        if median_income is None or median_home_value is None:
            fred_income, fred_home = fetch_macro_from_fred()
            median_income = median_income or fred_income
            median_home_value = median_home_value or fred_home

        self.n_households = n_households
        self.median_income = median_income
        self.median_home_value = median_home_value
        self.mobility_scale = mobility_scale
        self.rng = np.random.default_rng(seed)
        self._cohort_rate = ORIGINAL_RATE
        self._cohort_months_elapsed = MONTHS_ELAPSED
        self._cohort_term_years = TERM_YEARS
        self.households = self._generate_population()
        self._attach_mortgages()
        self._precompute_arrays()

    def attach_cohort(self, original_rate: float,
                      months_elapsed: int = MONTHS_ELAPSED,
                      term_years: int = TERM_YEARS):
        """Rebind every household mortgage to a new coupon/seasoning/term cohort."""
        self._cohort_rate = original_rate
        self._cohort_months_elapsed = months_elapsed
        self._cohort_term_years = term_years
        self._attach_mortgages()
        self._precompute_arrays()

    def _generate_population(self) -> list:
        """Draw heterogeneous households (economics only; mortgages attached later)."""
        incomes = self.rng.lognormal(mean=np.log(self.median_income),
                                     sigma=0.45, size=self.n_households)
        home_values = self.rng.lognormal(mean=np.log(self.median_home_value),
                                         sigma=0.35, size=self.n_households)
        desires = self.rng.exponential(scale=self.mobility_scale,
                                       size=self.n_households)
        txn_rates = self.rng.normal(
            loc=TRANSACTION_COST_MEAN,
            scale=TRANSACTION_COST_STD,
            size=self.n_households,
        ).clip(TRANSACTION_COST_FLOOR, TRANSACTION_COST_CAP)
        patience_draws = self.rng.random(size=self.n_households)

        households = []
        for inc, hv, des, txn, pat in zip(incomes, home_values, desires,
                                           txn_rates, patience_draws):
            placeholder = Mortgage(0.80 * hv, self._cohort_rate,
                                   months_elapsed=self._cohort_months_elapsed)
            households.append(Household(inc, hv, placeholder, des, txn, pat))
        return households

    def _attach_mortgages(self):
        """Rebuild mortgages for the current cohort without redrawing economics."""
        for h in self.households:
            principal = 0.80 * h.current_home_value
            h.mortgage = Mortgage(principal, self._cohort_rate,
                                  term_years=self._cohort_term_years,
                                  months_elapsed=self._cohort_months_elapsed)

    def _precompute_arrays(self):
        """Cache population attributes as NumPy arrays for vectorized CPR."""
        n = self.n_households
        self._monthly_income = np.array([h.income / 12 for h in self.households])
        self._home_values = np.array([h.current_home_value
                                      for h in self.households])
        self._desires = np.array([h.mobility_desire for h in self.households])
        self._txn_offsets = np.array([h.transaction_cost_rate - TRANSACTION_COST_MEAN
                                      for h in self.households])
        self._patience = np.array([h.patience_draw for h in self.households])
        self._current_payment = np.array(
            [h.mortgage.calculate_monthly_payment() for h in self.households])
        self._outstanding_us = np.array(
            [h.mortgage.outstanding_principal() for h in self.households])

        # Danish payoff depends on market rate, so precompute partial values:
        # monthly coupon payment and remaining term. Derived per household
        # from the attached mortgages so heterogeneous populations
        # (--population=freddie) work; in cohort mode every entry is equal
        # and the arithmetic is identical to the former scalar.
        self._pmt = self._current_payment  # same as coupon payment
        self._n_rem = np.array(
            [h.mortgage.remaining_term_months() for h in self.households]
        )
        self._term_years_vec = np.array(
            [h.mortgage.term_years for h in self.households]
        )

    def _payoff_us(self, rate: float) -> np.ndarray:
        return self._outstanding_us

    def _payoff_danish(self, rate: float) -> np.ndarray:
        r_mkt = rate / 12
        if r_mkt == 0:
            market_value = self._pmt * self._n_rem
        else:
            market_value = self._pmt * (1 - (1 + r_mkt) ** -self._n_rem) / r_mkt
        return np.minimum(market_value, self._outstanding_us)

    def _new_payment_vec(self, payoff: np.ndarray, rate: float) -> np.ndarray:
        """
        Monthly payment on a new mortgage at `rate` for each household.

        Movers originate a fresh loan of the SAME term as their current
        cohort (term preference persistence). Comparing a seasoned 15-year
        payment against a fresh 30-year payment is not apples-to-apples:
        the amortization-schedule difference alone drops the new payment so
        far that the loss-aversion penalty turns negative and overwhelms
        transaction costs, unlocking ~90% of the 15-year cohort per month.
        """
        r = rate / 12
        n = self._term_years_vec * 12
        if r == 0:
            return payoff / n
        return payoff * r / (1 - (1 + r) ** -n)

    def _mobility_penalty(self, payoff: np.ndarray, new_pmt: np.ndarray,
                          rate: float) -> np.ndarray:
        """
        Per-household loss-aversion penalty ($/month), term-aware.

        30-year (legacy, frozen): payment delta of the new same-term loan vs
        the current payment; negative deltas ("gains") pass through unscaled.

        15-year (native gate, 3.3): the legacy delta is an artifact for
        seasoned short-amortization loans — the new loan is financed on the
        much-reduced payoff, so `new_pmt - current_payment` is large and
        *negative*, a spurious "gain" that unlocks ~all 15yr borrowers. The
        native rule isolates the pure rate-lock cost: the payment increase from
        financing the SAME payoff at the market rate vs the borrower's own
        coupon. It is ≥0 when locked in (market > coupon) and 0 otherwise — a
        golden-handcuff cost, never a false gain — so 15yr mobility is governed
        by desire vs transaction cost + genuine rate lock-in.
        """
        delta_legacy = new_pmt - self._current_payment
        pen_legacy = np.where(delta_legacy > 0,
                              delta_legacy * LOSS_AVERSION_LAMBDA, delta_legacy)
        pmt_at_coupon = self._new_payment_vec(payoff, self._cohort_rate)
        delta_rate = new_pmt - pmt_at_coupon
        pen_rate = np.where(delta_rate > 0,
                            delta_rate * LOSS_AVERSION_LAMBDA, 0.0)
        is_short = self._term_years_vec <= 20
        return np.where(is_short, pen_rate, pen_legacy)

    def _cpr_vec(self, rate: float, system_type: str,
                 friction: float, rate_velocity: float) -> float:
        """Fully vectorized CPR for one grid point."""
        return float(self._movers_mask(rate, system_type, friction,
                                        rate_velocity).sum()) / self.n_households

    def _movers_mask(self, rate: float, system_type: str,
                     friction: float, rate_velocity: float) -> np.ndarray:
        """Boolean mask of households that move at one grid point."""
        payoff = (self._payoff_us(rate) if system_type == "US"
                  else self._payoff_danish(rate))
        new_pmt = self._new_payment_vec(payoff, rate)
        dti = np.where(self._monthly_income > 0,
                       new_pmt / self._monthly_income, 0.0)
        passes_dti = dti <= DTI_MAX
        penalty = self._mobility_penalty(payoff, new_pmt, rate)
        eff_rate = np.clip(friction + self._txn_offsets,
                           TRANSACTION_COST_FLOOR, TRANSACTION_COST_CAP)
        txn_cost = self._home_values * eff_rate
        total_penalty = penalty * EXPECTED_STAY_MONTHS + txn_cost
        passes_cost = self._desires > total_penalty
        if rate_velocity > WAIT_AND_SEE_RATE_THRESHOLD:
            passes_wait = self._patience >= WAIT_AND_SEE_PROB
        else:
            passes_wait = np.ones(self.n_households, dtype=bool)
        return passes_dti & passes_cost & passes_wait

    def simulate_cohort_path(self,
                             month_index: pd.DatetimeIndex,
                             market_rates_pct: pd.Series,
                             frictions: pd.Series,
                             velocities: pd.Series) -> pd.DataFrame:
        """
        Vintage burnout via survivor selection (parameter-free).

        Walk the historical path from the cohort's seasoning anchor; each
        month evaluate move decisions on the *surviving* population, record
        CPR = movers / survivors, then permanently remove movers.  The
        involuntary tail (agents who never pass the mobility gates) remains
        and sets a natural CPR floor on the depleted pool.
        """
        alive_us = np.ones(self.n_households, dtype=bool)
        alive_dk = np.ones(self.n_households, dtype=bool)
        us_out, dk_out = [], []
        for ts in month_index:
            n_us = int(alive_us.sum())
            n_dk = int(alive_dk.sum())
            if n_us == 0 and n_dk == 0:
                us_out.append(0.0)
                dk_out.append(0.0)
                continue
            rate = float(market_rates_pct.loc[ts]) / 100.0
            fric = float(frictions.loc[ts])
            vel = float(velocities.loc[ts])
            if n_us > 0:
                movers_us = (
                    alive_us
                    & self._movers_mask(rate, "US", fric, vel)
                )
                us_out.append(float(movers_us.sum()) / n_us * 100.0)
                alive_us &= ~movers_us
            else:
                us_out.append(0.0)
            if n_dk > 0:
                movers_dk = (
                    alive_dk
                    & self._movers_mask(rate, "Danish", fric, vel)
                )
                dk_out.append(float(movers_dk.sum()) / n_dk * 100.0)
                alive_dk &= ~movers_dk
            else:
                dk_out.append(0.0)
        return pd.DataFrame(
            {"US_CPR_Pct": us_out, "Danish_CPR_Pct": dk_out},
            index=month_index,
        )

    def cpr_at(self, rate: float, system_type: str,
               friction: float = TRANSACTION_COST_MEAN,
               rate_velocity: float = 0.0) -> float:
        """CPR for a single (rate, friction, rate_velocity) point."""
        return self._cpr_vec(rate, system_type, friction, rate_velocity)

    def build_cpr_surface(self) -> pd.DataFrame:
        """
        Sweep the full rate x friction x rate_velocity grid to produce a 3D
        CPR surface.  Uses vectorized evaluation for speed.
        """
        records = []
        total = len(FRICTION_GRID) * len(RATE_VELOCITY_GRID) * len(RATE_GRID)
        done = 0
        for friction in FRICTION_GRID:
            for velocity in RATE_VELOCITY_GRID:
                for rate in RATE_GRID:
                    records.append({
                        "Market_Rate": rate,
                        "Friction": friction,
                        "Rate_Velocity": velocity,
                        "CPR_US": self._cpr_vec(rate, "US", friction, velocity),
                        "CPR_Danish": self._cpr_vec(rate, "Danish", friction,
                                                    velocity),
                    })
                    done += 1
                if done % 260 == 0 or done == total:
                    print(f"  Surface: {done}/{total} grid points …")
        return pd.DataFrame(records)

    def run_simulation(self) -> pd.DataFrame:
        """Sweep market rates and record CPR under both systems (velocity=0)."""
        records = []
        for rate in RATE_GRID:
            records.append({
                "Market_Rate": rate,
                "CPR_US": self.cpr_at(rate, "US"),
                "CPR_Danish": self.cpr_at(rate, "Danish"),
            })
        return pd.DataFrame(records)


def build_multi_cohort_surfaces(engine: HousingMarketEngine,
                                cohorts: list) -> pd.DataFrame:
    """Build one 3D CPR surface per cohort, keyed by Cohort_Coupon + Cohort_Term."""
    frames = []
    for i, cohort in enumerate(cohorts):
        term_months = int(cohort.get("term_months", TERM_YEARS * 12))
        print(f"  Cohort {i + 1}/{len(cohorts)}: "
              f"{term_months // 12}yr coupon={cohort['coupon']*100:.2f}%  "
              f"weight={cohort['weight']*100:.1f}%  "
              f"seasoning={cohort['months_elapsed']}mo")
        engine.attach_cohort(cohort["coupon"], cohort["months_elapsed"],
                             term_years=term_months // 12)
        surf = engine.build_cpr_surface()
        surf["Cohort_Coupon"] = cohort["coupon"]
        surf["Cohort_Term"] = term_months
        frames.append(surf)
    return pd.concat(frames, ignore_index=True)


def weighted_burnout_cpr_paths(
    df: pd.DataFrame,
    cohorts: list,
    mobility_scale: float,
    median_income: float,
    median_home_value: float,
    seed: int = RNG_SEED,
    rates_extended: Optional[pd.Series] = None,
    base_friction: float = None,
) -> tuple:
    """
    Build cohort-weighted US/Danish CPR paths via survivor-based burnout
    along each cohort's historical rate path from origination.
    """
    import fed_mbs_extension_risk as fed

    if base_friction is None:
        base_friction = fed.BASE_FRICTION
    if rates_extended is None:
        rates_extended = df.attrs.get("MORTGAGE30US_EXTENDED", df["MORTGAGE30US"])

    engine = HousingMarketEngine(
        seed=seed,
        median_income=median_income,
        median_home_value=median_home_value,
        mobility_scale=mobility_scale,
    )

    us_cpr = pd.Series(0.0, index=df.index)
    dk_cpr = pd.Series(0.0, index=df.index)
    fric_series = df["Dynamic_Friction"]
    vel_series = df["Rate_6M_Change"]

    for cohort in cohorts:
        engine.attach_cohort(cohort["coupon"], cohort["months_elapsed"])
        origin = pd.Timestamp(cohort["origin_date"])
        end = df.index[-1]
        if origin > end:
            continue
        path_index = pd.date_range(origin, end, freq="ME")
        rates_path = rates_extended.reindex(path_index).ffill().bfill()
        fric_path = fric_series.reindex(path_index).fillna(base_friction)
        vel_path = vel_series.reindex(path_index).fillna(0.0)
        path = engine.simulate_cohort_path(path_index, rates_path,
                                           fric_path, vel_path)
        w = cohort["weight"]
        us_cpr += w * path["US_CPR_Pct"].reindex(df.index).fillna(0.0)
        dk_cpr += w * path["Danish_CPR_Pct"].reindex(df.index).fillna(0.0)

    return us_cpr, dk_cpr


# ---------------------------------------------------------------------------
# Calibration: anchor the mobility-desire scale to the "Baseline Floor"
# ---------------------------------------------------------------------------
def reference_cohort(cohorts: list) -> dict:
    """
    Dominant 30-year coupon bucket (max SOMA weight).

    The mobility calibration anchor stays on the 30-year book so the 4-5%
    involuntary-turnover floor remains comparable across runs with and
    without the 15-year fold-in.
    """
    thirty_yr = [c for c in cohorts
                 if int(c.get("term_months", TERM_YEARS * 12)) == 360]
    return max(thirty_yr or cohorts, key=lambda c: c["weight"])


def calibrate_mobility_scale(median_income: float,
                             median_home_value: float,
                             cohort_rate: float = ORIGINAL_RATE,
                             cohort_months: int = MONTHS_ELAPSED,
                             target_low: float = 0.04,
                             target_high: float = 0.05,
                             max_iter: int = 30) -> float:
    """
    Binary-search the exponential mobility_desire scale so that, under
    maximum lock-in (8.0% market rate, U.S. par-payoff rule), the model
    reproduces the real-world involuntary turnover floor of 4-5% CPR
    (death, divorce, default).
    """
    target_mid = (target_low + target_high) / 2
    lo, hi = 1_000.0, 500_000.0
    scale = MOBILITY_DESIRE_SCALE

    for _ in range(max_iter):
        scale = (lo + hi) / 2
        engine = HousingMarketEngine(
            median_income=median_income,
            median_home_value=median_home_value,
            mobility_scale=scale,
        )
        engine.attach_cohort(cohort_rate, cohort_months)
        cpr = engine.cpr_at(0.08, "US")

        if target_low <= cpr <= target_high:
            break
        if cpr < target_mid:
            lo = scale   # too few movers -> raise desire scale
        else:
            hi = scale   # too many movers -> lower desire scale

    print(f"Calibrated MOBILITY_DESIRE_SCALE = {scale:,.0f} "
          f"(CPR floor at 8.0% US = {cpr:.2%})")
    return scale


# ---------------------------------------------------------------------------
# Visualization
# ---------------------------------------------------------------------------
def plot_s_curve(results: pd.DataFrame,
                 reference_coupon: float = ORIGINAL_RATE,
                 save_path=None):
    """Publication-quality S-curve comparing the two mortgage systems."""
    if save_path is None:
        save_path = ABM_LOCKIN_SCURVE_PNG
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(results["Market_Rate"] * 100, results["CPR_US"] * 100,
            color="#1f77b4", linewidth=2.5, marker="o", markersize=6,
            label="U.S. System (par payoff)")
    ax.plot(results["Market_Rate"] * 100, results["CPR_Danish"] * 100,
            color="#d62728", linewidth=2.5, marker="s", markersize=6,
            label="Danish System (market-price buyback)")

    # Reference line at the original mortgage coupon
    ax.axvline(x=reference_coupon * 100, color="grey", linestyle=":",
               linewidth=1.5, alpha=0.8)
    ax.text(reference_coupon * 100 + 0.05, 2,
            f"Reference coupon ({reference_coupon*100:.1f}%)",
            color="grey", fontsize=10)

    ax.set_xlabel("Current Market Interest Rate (%)", fontsize=12)
    ax.set_ylabel("Mobility Rate / CPR (%)", fontsize=12)
    ax.set_title(
        "The Lock-In Effect: Household Mobility vs. Rate Shocks\n"
        "U.S. Par-Payoff Rule vs. Danish Market-Price Buyback Rule",
        fontsize=14, fontweight="bold",
    )
    ax.set_xlim(1.8, 8.2)
    y_top = max(40, results[["CPR_US", "CPR_Danish"]].max().max() * 100 + 5)
    ax.set_ylim(0, y_top)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f"{y:.0f}%"))
    ax.grid(alpha=0.3)
    ax.legend(fontsize=11, loc="upper right")

    plt.tight_layout()
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nS-curve chart saved to {save_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main(population: str = "synthetic"):
    import fed_mbs_extension_risk as fed

    if population == "freddie":
        # Cross-design mode: real Freddie structural covariates, synthetic
        # behavioral draws, frozen production calibration. The full
        # two-variant diagnostic lives in cross_design_test.py.
        from freddie_population import (
            attach_freddie_covariates,
            load_freddie_structural_sample,
            population_summary,
        )

        print("Fetching SOMA MBS coupon cohorts from NY Fed …")
        cohorts = fed.fetch_soma_mbs_cohorts()
        print("Fetching empirical medians from FRED …")
        median_income, median_home_value = fetch_macro_from_fred()
        ref = reference_cohort(cohorts)
        mobility_scale = calibrate_mobility_scale(
            median_income, median_home_value,
            cohort_rate=ref["coupon"],
            cohort_months=ref["months_elapsed"],
        )
        loans = load_freddie_structural_sample(N_HOUSEHOLDS)
        print(population_summary(loans))
        engine = HousingMarketEngine(
            median_income=median_income,
            median_home_value=median_home_value,
            mobility_scale=mobility_scale,
        )
        attach_freddie_covariates(engine, loans)
        print("Building population-level 3D CPR surface (freddie, frozen "
              "calibration) …")
        surface = engine.build_cpr_surface()
        out_csv = ABM_CPR_SURFACE_CSV.with_name(
            "abm_cpr_surface_freddie_frozen.csv")
        surface.to_csv(out_csv, index=False)
        print(f"CPR surface saved to {out_csv}")
        return

    print("Fetching SOMA MBS coupon cohorts from NY Fed …")
    cohorts = fed.fetch_soma_mbs_cohorts()

    print("Fetching empirical medians from FRED …")
    median_income, median_home_value = fetch_macro_from_fred()

    ref = reference_cohort(cohorts)

    print("Calibrating mobility desire to the 4-5% involuntary-turnover "
          "floor …")
    mobility_scale = calibrate_mobility_scale(
        median_income, median_home_value,
        cohort_rate=ref["coupon"],
        cohort_months=ref["months_elapsed"],
    )

    print(f"\nInitializing {N_HOUSEHOLDS:,} households "
          f"(reference cohort {ref['coupon']*100:.2f}%, "
          f"{ref['months_elapsed']}mo seasoning) …")
    engine = HousingMarketEngine(
        median_income=median_income,
        median_home_value=median_home_value,
        mobility_scale=mobility_scale,
    )
    engine.attach_cohort(ref["coupon"], ref["months_elapsed"])

    print("Sweeping market rates 2.0% → 8.0% under US and Danish rules …")
    results = engine.run_simulation()

    # Summary table
    display = results.copy()
    display["Market_Rate"] = (display["Market_Rate"] * 100).map("{:.1f}%".format)
    display["CPR_US"] = (display["CPR_US"] * 100).map("{:.2f}%".format)
    display["CPR_Danish"] = (display["CPR_Danish"] * 100).map("{:.2f}%".format)
    print("\n" + display.to_string(index=False))

    results.to_csv(ABM_LOCKIN_RESULTS_CSV, index=False)
    print(f"\nResults table saved to {ABM_LOCKIN_RESULTS_CSV}")

    print(f"\nBuilding multi-cohort 3D CPR surfaces "
          f"({len(cohorts)} cohorts x {len(RATE_GRID)} rates x "
          f"{len(FRICTION_GRID)} frictions x {len(RATE_VELOCITY_GRID)} velocities) …")
    surface = build_multi_cohort_surfaces(engine, cohorts)
    surface.to_csv(ABM_CPR_SURFACE_CSV, index=False)
    print(f"CPR surface saved to {ABM_CPR_SURFACE_CSV}")

    plot_s_curve(results, reference_coupon=ref["coupon"])


if __name__ == "__main__":
    import argparse

    _parser = argparse.ArgumentParser(description=__doc__)
    _parser.add_argument(
        "--population",
        choices=["synthetic", "freddie"],
        default="synthetic",
        help="synthetic: production default (unchanged); freddie: real "
             "Freddie structural covariates (see cross_design_test.py)",
    )
    _args = _parser.parse_args()
    main(population=_args.population)
