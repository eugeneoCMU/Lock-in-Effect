"""
Berger, Jeong, Marx, Olesen & Tourre — Danish-counterfactual calibration.

Source: "A Danish fix for U.S. mortgage lock-in?" (SSRN abstract 6150766, draft
January 2026), cited as berger2026 in the manuscript. NOTE: this header
previously read "Berger, Milbradt, Tourre & Vavra", which is the author list of
Berger, Milbradt, Tourre & Vavra (2021 AER, "Mortgage prepayment and
path-dependent effects of monetary policy") — a different, non-Danish paper. The
transcribed parameters below are Danish (DK/US structural pairs, Danish tax
shield), so the attribution, not the manuscript citation, was the error.

Single source of truth for the Danish (and U.S.-transplant) prepayment
elasticities used to recalibrate BOTH frameworks' Danish counterfactual, so we
stop extrapolating a U.S.-calibrated response function to a Danish rate gap and
instead import estimated elasticities for this exact counterfactual.

All numbers below are transcribed from the paper as supplied (Table 3 structural
parameters; §3.3.1 and §4.9.1 empirical elasticities and tax parameters). None
are invented here. Two prepayment channels are modeled separately:

  * MOVING channel — households that sell/move. Danish moving is essentially
    insensitive to the coupon gap (no lock-in on the moving margin).
  * REFINANCE-IN-PLACE channel — discount buyback while staying put, driven in
    Denmark by a tax shield that is attenuated under U.S. tax law.
"""

from __future__ import annotations

import numpy as np

# --- Table 3: structural parameters (annual opportunity hazards + cost draws) --
PSI = {"DK": 0.055, "US": 0.13}          # moving opportunity hazard
KAPPA_PSI = {"DK": 0.0, "US": 0.0}       # mean net moving cost
SIGMA_PSI = {"DK": 0.10, "US": 0.15}     # sd of net moving costs
LAMBDA = {"DK": 0.33, "US": 0.30}        # refinancing opportunity hazard
KAPPA_LAMBDA = {"DK": 0.008, "US": 0.02}  # mean refinancing cost (frac of balance)
SIGMA_LAMBDA = {"DK": 0.005, "US": 0.02}  # sd of refinancing cost

# --- §3.3.1: realized moving elasticities ------------------------------------
DK_UNCOND_MOVE_ANNUAL = 0.032            # 3.2%/yr Danish unconditional moving rate
# Danish moving-hazard slope, %/yr per 100bp of (negative) coupon gap: the CI
# spans zero (−0.198 .. +0.12), i.e. statistically flat / no lock-in.
DK_MOVE_SLOPE_LO_PP = -0.198
DK_MOVE_SLOPE_HI_PP = +0.12
DK_MOVE_SLOPE_MID_PP = 0.5 * (DK_MOVE_SLOPE_LO_PP + DK_MOVE_SLOPE_HI_PP)  # -0.039
# U.S. moving-hazard slope, %/yr per 100bp (Fonseca & Liu 2024): 0.57 .. 1.20.
US_MOVE_SLOPE_LO_PP = 0.57
US_MOVE_SLOPE_HI_PP = 1.20
US_MOVE_SLOPE_MID_PP = 0.5 * (US_MOVE_SLOPE_LO_PP + US_MOVE_SLOPE_HI_PP)   # 0.885

# Moving attenuation = |Danish slope| / |U.S. slope|. ~0.044 → essentially flat.
MOVE_ATTENUATION = abs(DK_MOVE_SLOPE_MID_PP) / US_MOVE_SLOPE_MID_PP

# --- §4.9.1: U.S.-counterfactual tax parameters (footnote 24) -----------------
THETA_I_US = 0.22    # U.S. mortgage-interest deduction rate
THETA_G_US = 0.15    # U.S. capital-gains tax rate (taxes the buyback discount)
THETA_DK = 0.33      # Danish interest deduction; capital gains tax-exempt
THETA_G_DK = 0.0
# Equilibrium mortgage-rate shift under realistic U.S. buyback-with-taxable-gains.
US_BUYBACK_EQUIL_RATE_SHIFT_BP = 1.0
# Berger §4.9.1: that ~1bp equilibrium shift means the U.S.-transplant buyback
# adds essentially no incremental refinancing. Best estimate is therefore ≈0
# annual CPR (a partial-equilibrium reduced form over-predicts because it omits
# the rate adjustment). The value is a module global so it can be SWEPT (see
# refi_sweep.py) to test how far the institutional-gap sign is from breakeven.
US_TRANSPLANT_REFI_BEST_ESTIMATE = 0.0  # Berger realistic-tax GE anchor
_US_TRANSPLANT_REFI_ANNUAL = US_TRANSPLANT_REFI_BEST_ESTIMATE

# --- Moving-channel transplant anchor ------------------------------------
# "dk_level"     — import the Danish descriptive level (3.2%/yr unconditional
#                  moving) with the near-flat Danish slope. This transplants
#                  Denmark's LEVEL onto U.S. households, i.e. a rule+country
#                  bundle: it assumes U.S. households adopt Danish baseline
#                  mobility along with the Danish payoff rule.
# "us_intercept" — rule-only counterfactual: keep Berger's identified SLOPE
#                  fact (moving is flat in the coupon gap under market-value
#                  payoff) but anchor the level at the U.S. zero-gap intercept
#                  (each framework's own U.S. hazard evaluated at zero rate
#                  gap, involuntary floor retained). U.S. life-event turnover
#                  (death, divorce, forced relocation) cannot fall because the
#                  payoff rule changed, so this anchor respects the U.S.
#                  involuntary-turnover floor by construction. Consumed by the
#                  frameworks' Danish branches, not here.
_DANISH_MOVING_ANCHOR = "dk_level"


def set_danish_moving_anchor(mode: str) -> None:
    """Select the Danish moving-channel anchor: 'dk_level' | 'us_intercept'."""
    global _DANISH_MOVING_ANCHOR
    if mode not in ("dk_level", "us_intercept"):
        raise ValueError(f"unknown Danish moving anchor: {mode!r}")
    _DANISH_MOVING_ANCHOR = mode


def get_danish_moving_anchor() -> str:
    return _DANISH_MOVING_ANCHOR


def set_us_transplant_refi(value: float) -> None:
    """Override the U.S.-transplant refi-in-place annual CPR (for sweeps)."""
    global _US_TRANSPLANT_REFI_ANNUAL
    _US_TRANSPLANT_REFI_ANNUAL = float(value)


def get_us_transplant_refi() -> float:
    return _US_TRANSPLANT_REFI_ANNUAL


def us_transplant_refi_reduced_form(coupon, market_rate, loan_age,
                                    term_months: int = 360):
    """
    The partial-equilibrium reduced form rejected in §20 as over-predicting
    (retained here only to ground the sweep ceiling). Tax-arbitrage take-up of
    the buyback discount under U.S. taxes (θi − θg), λ_US opportunity hazard.
    """
    from math import erf, sqrt
    disc = _buyback_discount_frac(coupon, market_rate, loan_age, term_months)
    benefit = disc * (THETA_I_US - THETA_G_US)
    z = (benefit - KAPPA_LAMBDA["US"]) / max(SIGMA_LAMBDA["US"], 1e-9)
    take = np.where(disc > 0.0,
                    0.5 * (1.0 + np.vectorize(lambda x: erf(x / sqrt(2.0)))(z)),
                    0.0)
    return np.clip(LAMBDA["US"] * take, 0.0, 1.0)


def _annual_to_monthly_cpr(cpr_annual: np.ndarray) -> np.ndarray:
    """Constant-hazard: monthly SMM from annual CPR."""
    cpr = np.clip(np.asarray(cpr_annual, dtype=np.float64), 0.0, 0.99)
    return 1.0 - (1.0 - cpr) ** (1.0 / 12.0)


def danish_moving_cpr_annual(coupon_gap: np.ndarray) -> np.ndarray:
    """
    Danish MOVING channel, annual CPR. Anchored to the 3.2%/yr unconditional
    rate with the (near-flat) Danish slope. `coupon_gap` = coupon − market
    (decimal; negative when rates have risen above the coupon).
    """
    gap_100bp = np.asarray(coupon_gap, dtype=np.float64) * 100.0  # decimal→(×100bp)
    slope = DK_MOVE_SLOPE_MID_PP / 100.0  # %/yr per 100bp → fraction/yr per 100bp
    return np.clip(DK_UNCOND_MOVE_ANNUAL + slope * gap_100bp, 0.0, 1.0)


def _buyback_discount_frac(coupon: np.ndarray, market_rate: float,
                           loan_age: np.ndarray, term_months: int = 360
                           ) -> np.ndarray:
    """
    Fraction of balance recoverable as a buyback discount: 1 − PV(remaining
    payments at market)/balance. Positive only when market > coupon (rates
    risen), i.e. the debt trades below par.
    """
    coupon = np.asarray(coupon, dtype=np.float64)
    n_rem = np.maximum(term_months - np.asarray(loan_age), 1).astype(np.float64)
    rc = coupon / 12.0
    rm = market_rate / 12.0
    # payment per unit balance at the coupon; PV of those payments at market.
    with np.errstate(divide="ignore", invalid="ignore"):
        pmt = np.where(rc > 0, rc / (1.0 - (1.0 + rc) ** (-n_rem)), 1.0 / n_rem)
        pv = np.where(rm > 0, pmt * (1.0 - (1.0 + rm) ** (-n_rem)) / rm,
                      pmt * n_rem)
    return np.clip(1.0 - pv, 0.0, 1.0)  # >0 when market>coupon


def danish_refi_in_place_cpr_annual(coupon: np.ndarray, market_rate: float,
                                    loan_age: np.ndarray, regime: str = "US",
                                    term_months: int = 360) -> np.ndarray:
    """
    Discount-buyback-while-staying-put channel, annual CPR (reduced form).

    The buyback of below-par debt is NPV-neutral on the financing itself (that
    is the identity Path B previously used); its real value is the TAX treatment
    of the realized discount. Denmark: tax-exempt → full discount is a net gain.
    U.S. transplant: the discount is a taxable capital gain (θg) and the interest
    deduction is smaller (θi vs Danish θ), so the net after-tax benefit is
    attenuated. A refinance opportunity arrives at hazard λ; it is taken when the
    after-tax benefit exceeds a refinancing-cost draw N(κλ, σλ).

    U.S. transplant is anchored to Berger's ~1bp GE result (≈0 incremental refi;
    the tax shield is absent). The Danish-home case uses a reduced-form take-up
    of the tax-free discount for the institutional contrast — its magnitude is a
    derivation from Berger's structural inputs, not a rate the paper reports.
    """
    disc = _buyback_discount_frac(coupon, market_rate, loan_age, term_months)
    if not (regime.upper().startswith("DK") or regime.upper() == "DANISH"):
        # U.S. transplant: taxable capital gain removes the buyback tax shield →
        # negligible incremental refi (Berger §4.9.1, ~1bp equilibrium). Value is
        # the sweepable module global (best estimate ≈0); see refi_sweep.py.
        return np.full(np.shape(disc), _US_TRANSPLANT_REFI_ANNUAL,
                       dtype=np.float64)
    # Danish home: tax-free discount (θ_dk − θg_dk = 0.33) drives take-up.
    from math import sqrt
    tax_adv = THETA_DK - THETA_G_DK
    benefit = disc * tax_adv
    z = (benefit - KAPPA_LAMBDA["DK"]) / max(SIGMA_LAMBDA["DK"], 1e-9)
    take = np.where(disc > 0.0,
                    0.5 * (1.0 + np.vectorize(lambda x: _erf(x / sqrt(2.0)))(z)),
                    0.0)
    return np.clip(LAMBDA["DK"] * take, 0.0, 1.0)


def _erf(x: float) -> float:
    from math import erf
    return erf(x)


def danish_cpr_annual(coupon: np.ndarray, market_rate: float,
                      loan_age: np.ndarray, regime: str = "US",
                      term_months: int = 360) -> np.ndarray:
    """Total Danish counterfactual CPR = moving + refinance-in-place (annual)."""
    gap = np.asarray(coupon, dtype=np.float64) - market_rate
    move = danish_moving_cpr_annual(gap)
    refi = danish_refi_in_place_cpr_annual(coupon, market_rate, loan_age,
                                           regime, term_months)
    # competing risks on the survival scale: 1 − (1−move)(1−refi)
    return np.clip(1.0 - (1.0 - move) * (1.0 - refi), 0.0, 1.0)


if __name__ == "__main__":
    print(f"MOVE_ATTENUATION = {MOVE_ATTENUATION:.4f}  "
          f"(DK slope {DK_MOVE_SLOPE_MID_PP:+.3f} / US {US_MOVE_SLOPE_MID_PP:.3f} %/yr per 100bp)")
    print("Danish counterfactual CPR (annual %) for a 2.5% coupon, age 36mo:")
    print(f"  {'market':>7} {'move':>7} {'refi(US)':>9} {'refi(DK)':>9} "
          f"{'tot(US)':>8} {'tot(DK)':>8}")
    for m in (0.02, 0.03, 0.045, 0.06, 0.07, 0.08):
        c = np.array([0.025]); age = np.array([36])
        move = danish_moving_cpr_annual(c - m)[0] * 100
        rus = danish_refi_in_place_cpr_annual(c, m, age, "US")[0] * 100
        rdk = danish_refi_in_place_cpr_annual(c, m, age, "DK")[0] * 100
        tus = danish_cpr_annual(c, m, age, "US")[0] * 100
        tdk = danish_cpr_annual(c, m, age, "DK")[0] * 100
        print(f"  {m*100:>6.1f}% {move:>6.2f}% {rus:>8.2f}% {rdk:>8.2f}% "
              f"{tus:>7.2f}% {tdk:>7.2f}%")
