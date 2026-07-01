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

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from fredapi import Fred

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

RATE_GRID = np.arange(0.02, 0.0801, 0.005)  # 2.0% -> 8.0% step 0.5%
# Friction grid for the 2D CPR surface — widened to 5%-17.5% so the sensitivity
# analysis (which sweeps base friction and penalty caps) can interpolate at
# extreme friction levels without clamping at a grid boundary.
FRICTION_GRID = np.arange(0.05, 0.18, 0.005)

# FRED settings (same key as fed_mbs_extension_risk.py)
FRED_API_KEY = "0da55cec06bcff18594e15cc9da17d2d"
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
                 transaction_cost_rate: float):
        self.income = income
        self.current_home_value = current_home_value
        self.mortgage = mortgage
        self.mobility_desire = mobility_desire  # $-equivalent benefit of moving
        self.transaction_cost_rate = transaction_cost_rate

    def evaluate_move(self, current_market_rate: float,
                      system_type: str,
                      friction: float = TRANSACTION_COST_MEAN) -> bool:
        """
        Decide whether to move under the given mortgage system.

        The household pays off its current mortgage (cost depends on the
        system), finances that payoff amount with a NEW mortgage at the
        current market rate, and compares the resulting change in monthly
        payment (over an expected-stay horizon, plus transaction costs)
        against its non-financial mobility desire.

        `friction` is the macro base transaction-cost rate for the month
        (defaults to the static 7% mean). The household's idiosyncratic
        deviation from the base mean is preserved as an offset, so when
        friction == TRANSACTION_COST_MEAN behavior is unchanged.
        """
        if system_type == "US":
            payoff = self.mortgage.get_payoff_cost_us(current_market_rate)
        elif system_type == "Danish":
            payoff = self.mortgage.get_payoff_cost_danish(current_market_rate)
        else:
            raise ValueError(f"Unknown system_type: {system_type}")

        # New mortgage finances the payoff amount at today's market rate
        new_loan = Mortgage(payoff, current_market_rate,
                            term_years=TERM_YEARS, months_elapsed=0)
        new_payment = new_loan.calculate_monthly_payment()
        current_payment = self.mortgage.calculate_monthly_payment()

        # Effective transaction cost = macro friction shifted by the agent's
        # idiosyncratic offset around the base mean, clipped to sane bounds.
        offset = self.transaction_cost_rate - TRANSACTION_COST_MEAN
        eff_rate = float(np.clip(friction + offset,
                                 TRANSACTION_COST_FLOOR, TRANSACTION_COST_CAP))
        transaction_cost = self.current_home_value * eff_rate
        monthly_penalty = new_payment - current_payment
        total_penalty = monthly_penalty * EXPECTED_STAY_MONTHS + transaction_cost

        # Move only if the non-financial desire outweighs the penalty
        return self.mobility_desire > total_penalty


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
        self.households = self._generate_population()

    def _generate_population(self) -> list:
        """10,000 heterogeneous households, all locked into 3.0% mortgages."""
        # Lognormal income centered on the FRED empirical median
        incomes = self.rng.lognormal(mean=np.log(self.median_income),
                                     sigma=0.45, size=self.n_households)
        # Lognormal home values centered on the FRED empirical median
        home_values = self.rng.lognormal(mean=np.log(self.median_home_value),
                                         sigma=0.35, size=self.n_households)
        # Non-financial desire to move (job change, family, schools...)
        desires = self.rng.exponential(scale=self.mobility_scale,
                                       size=self.n_households)

        # Per-agent transaction cost rate: N(7%, 1.5%), clipped to [2%, 12%]
        txn_rates = self.rng.normal(
            loc=TRANSACTION_COST_MEAN,
            scale=TRANSACTION_COST_STD,
            size=self.n_households,
        ).clip(TRANSACTION_COST_FLOOR, TRANSACTION_COST_CAP)

        households = []
        for inc, hv, des, txn in zip(incomes, home_values, desires, txn_rates):
            principal = 0.80 * hv  # 80% LTV at origination
            mortgage = Mortgage(principal, ORIGINAL_RATE)
            households.append(Household(inc, hv, mortgage, des, txn))
        return households

    def cpr_at(self, rate: float, system_type: str,
               friction: float = TRANSACTION_COST_MEAN) -> float:
        """CPR for a single market rate and friction level under one system."""
        movers = sum(
            h.evaluate_move(rate, system_type, friction)
            for h in self.households
        )
        return movers / self.n_households

    def build_cpr_surface(self) -> pd.DataFrame:
        """
        Sweep the full rate x friction grid to produce a 2D CPR surface.
        Used by the macro model to interpolate month-specific CPRs from each
        month's mortgage rate AND its Dynamic_Friction level.
        """
        records = []
        for friction in FRICTION_GRID:
            for rate in RATE_GRID:
                records.append({
                    "Market_Rate": rate,
                    "Friction": friction,
                    "CPR_US": self.cpr_at(rate, "US", friction),
                    "CPR_Danish": self.cpr_at(rate, "Danish", friction),
                })
        return pd.DataFrame(records)

    def run_simulation(self) -> pd.DataFrame:
        """Sweep market rates and record CPR under both systems."""
        records = []
        for rate in RATE_GRID:
            records.append({
                "Market_Rate": rate,
                "CPR_US": self.cpr_at(rate, "US"),
                "CPR_Danish": self.cpr_at(rate, "Danish"),
            })
        return pd.DataFrame(records)


# ---------------------------------------------------------------------------
# Calibration: anchor the mobility-desire scale to the "Baseline Floor"
# ---------------------------------------------------------------------------
def calibrate_mobility_scale(median_income: float,
                             median_home_value: float,
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
                 save_path: str = "abm_lockin_scurve.png"):
    """Publication-quality S-curve comparing the two mortgage systems."""
    fig, ax = plt.subplots(figsize=(12, 7))

    ax.plot(results["Market_Rate"] * 100, results["CPR_US"] * 100,
            color="#1f77b4", linewidth=2.5, marker="o", markersize=6,
            label="U.S. System (par payoff)")
    ax.plot(results["Market_Rate"] * 100, results["CPR_Danish"] * 100,
            color="#d62728", linewidth=2.5, marker="s", markersize=6,
            label="Danish System (market-price buyback)")

    # Reference line at the original mortgage coupon
    ax.axvline(x=ORIGINAL_RATE * 100, color="grey", linestyle=":",
               linewidth=1.5, alpha=0.8)
    ax.text(ORIGINAL_RATE * 100 + 0.05, 2, "Original coupon (3.0%)",
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
def main():
    print("Fetching empirical medians from FRED …")
    median_income, median_home_value = fetch_macro_from_fred()

    print("Calibrating mobility desire to the 4-5% involuntary-turnover "
          "floor …")
    mobility_scale = calibrate_mobility_scale(median_income,
                                              median_home_value)

    print(f"\nInitializing {N_HOUSEHOLDS:,} households at "
          f"{ORIGINAL_RATE:.1%} mortgages "
          f"(2020-21 pandemic origination cohort) …")
    engine = HousingMarketEngine(
        median_income=median_income,
        median_home_value=median_home_value,
        mobility_scale=mobility_scale,
    )

    print("Sweeping market rates 2.0% → 8.0% under US and Danish rules …")
    results = engine.run_simulation()

    # Summary table
    display = results.copy()
    display["Market_Rate"] = (display["Market_Rate"] * 100).map("{:.1f}%".format)
    display["CPR_US"] = (display["CPR_US"] * 100).map("{:.2f}%".format)
    display["CPR_Danish"] = (display["CPR_Danish"] * 100).map("{:.2f}%".format)
    print("\n" + display.to_string(index=False))

    results.to_csv("abm_lockin_results.csv", index=False)
    print("\nResults table saved to abm_lockin_results.csv")

    # Build the 2D CPR surface (rate x friction) for the macro model
    print(f"\nBuilding 2D CPR surface "
          f"({len(RATE_GRID)} rates x {len(FRICTION_GRID)} friction levels) …")
    surface = engine.build_cpr_surface()
    surface.to_csv("abm_cpr_surface.csv", index=False)
    print("CPR surface saved to abm_cpr_surface.csv")

    plot_s_curve(results)


if __name__ == "__main__":
    main()
