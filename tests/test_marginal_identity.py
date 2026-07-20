"""
End-to-end invariants for the lock-in marginal, plus the convexity property
the dispersion-vs-structure diagnosis rests on.

Two gaps this file closes.

1. NOTHING in the repo asserted the defining property of the marginal:
   the marginal is the difference between the production leg and the
   no-lock-in null leg, and at beta1 = 0 that difference must be EXACTLY
   zero because the rate-gap channel is switched off.  No test imported
   competing_risks, microsim_engine, markov or agents at all, so the whole
   forward walk — pool -> monthly_step -> roll-off series ->
   score_extension_risk — was unexercised.

   The test here is a 200-loan, 6-month microsim on a synthetic pool and a
   synthetic rate path (no FRED, no Freddie sample, no cached parquet), run
   through the real `_simulate_regime` and the real `score_extension_risk`.
   Rate paths are chosen so every loan is at or in the money, which pins the
   competing default hazard's `rate_stress` at exactly 0 in every leg; the
   ONLY thing that differs across the paths is the rate gap.  Therefore at
   beta1 = 0 the three legs must be bit-identical, and the beta1 != 0 control
   must separate them — otherwise the elasticity is inert, which is precisely
   the class of bug TECHNICAL.md section 15 Fix 3 was about.

2. `cpr_annual_to_monthly_hazard` must be STRICTLY convex.  The
   dispersion-vs-structure reading depends on Jensen running one way:
   averaging a dispersed CPR path before converting understates the mean
   monthly hazard.  Nothing asserted it.

Run:  python3 -m pytest tests/test_marginal_identity.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl
import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))
sys.path.insert(0, str(_ROOT / "hazard"))

from common.qt_window import QT_TARGET_FULL_B, QT_TARGET_RAMP_B  # noqa: E402
from config import MARKOV_STATES  # noqa: E402
from extension_risk import score_extension_risk  # noqa: E402
from literature_hazard import (  # noqa: E402
    BETA1_PREPAY_MID,
    cpr_annual_to_monthly_hazard,
    rothstein_beta1,
)
from microsim_engine import _simulate_regime  # noqa: E402


N_LOANS_TEST = 200
SIM_MONTHS = pd.date_range("2022-06-01", periods=6, freq="MS")
COUPON_PCT = 4.0          # every loan; MicrosimPool converts to 0.04 decimal
HOLDINGS_B = 2_600.0
SEED = 20260719

# Every path is at or below the 4.0% coupon, so rate_stress = max(0, mkt -
# coupon) is exactly 0 in all of them and the competing default hazard is
# identical across legs.  Only the refi gap moves.
PATH_ZERO_GAP = 4.0       # gap 0 by construction: the no-lock-in baseline
PATH_SMALL_GAP = 3.5      # +50bp in the money
PATH_LARGE_GAP = 3.0      # +100bp in the money


def _loan_sample(n: int = N_LOANS_TEST) -> pl.DataFrame:
    """Deterministic synthetic pool: no Freddie/Fannie data, no cache."""
    rng = np.random.default_rng(SEED)
    return pl.DataFrame(
        {
            "loan_id": [f"T{i:06d}" for i in range(n)],
            "stratum_id": [f"S{i % 4}" for i in range(n)],
            "fico": rng.integers(640, 800, n).astype(np.int64),
            "property_state": [["CA", "TX", "NY", "OH"][i % 4] for i in range(n)],
            "orig_ltv": rng.integers(60, 95, n).astype(np.float64),
            "coupon": np.full(n, COUPON_PCT),
            "orig_upb": np.full(n, 300_000.0),
            "balance": np.full(n, 250_000.0),
            "loan_age": np.full(n, 48, dtype=np.int64),
            "state": ["Current"] * n,
        }
    )


def _macro(market_rate_pct: float) -> pd.DataFrame:
    """Flat synthetic rate path over the six simulated QT months."""
    return pd.DataFrame(
        {
            "MORTGAGE30US": np.full(len(SIM_MONTHS), market_rate_pct),
            "WSHOMCB": np.full(len(SIM_MONTHS), HOLDINGS_B * 1_000.0),
        },
        index=SIM_MONTHS,
    )


def _identity_transitions() -> pd.DataFrame:
    """
    Delinquency transitions held fixed, so the Markov leg contributes no
    randomness of its own and any difference between legs is attributable
    to the prepay hazard.
    """
    return pd.DataFrame(
        np.eye(len(MARKOV_STATES)),
        index=MARKOV_STATES,
        columns=MARKOV_STATES,
    )


def _run(market_rate_pct: float, beta1) -> pd.DataFrame:
    return _simulate_regime(
        _loan_sample(),
        _macro(market_rate_pct),
        regime="US",
        holdings_scale_b=HOLDINGS_B,
        trans=_identity_transitions(),
        seed=SEED,
        beta1=beta1,
    )


def _empirical_benchmark() -> pd.DataFrame:
    """
    Synthetic empirical frame over the same six months, in the shape
    score_extension_risk consumes.  Its levels are arbitrary — it is the
    common denominator against which both legs are scored, so it cancels
    out of the marginal.
    """
    targets = np.array(
        [QT_TARGET_RAMP_B] * 3 + [QT_TARGET_FULL_B] * 3, dtype=float
    )
    return pd.DataFrame(
        {
            "Extension_Delta_Billions": np.full(len(SIM_MONTHS), -20.0),
            "QT_Target_Billions": targets,
            "Empirical_CPR_Pct": np.array([6.0, 5.4, 5.0, 4.7, 4.9, 5.6]),
        },
        index=SIM_MONTHS,
    )


class TestNullLegIsExactlyNoLockIn:
    """beta1 = 0 must switch the rate-gap channel off exactly."""

    def test_zero_shock_is_exactly_zero_beta1(self):
        """Precondition for everything below (also asserted in no_lockin_null)."""
        assert rothstein_beta1(0.0) == 0.0

    def test_null_leg_is_invariant_to_the_rate_gap(self):
        """
        At beta1 = 0 the simulated roll-off and CPR paths must be IDENTICAL
        across rate paths that differ only in the refi gap.  A hard-coded
        elasticity, a beta1 that leaks in from a module default, or a rate
        gap wired into the hazard outside the beta1 term all break this.
        """
        base = _run(PATH_ZERO_GAP, beta1=0.0)
        small = _run(PATH_SMALL_GAP, beta1=0.0)
        large = _run(PATH_LARGE_GAP, beta1=0.0)

        for other in (small, large):
            np.testing.assert_array_equal(
                other["simulated_rolloff_b"].to_numpy(),
                base["simulated_rolloff_b"].to_numpy(),
            )
            np.testing.assert_array_equal(
                other["hazard_cpr_pct"].to_numpy(),
                base["hazard_cpr_pct"].to_numpy(),
            )

    def test_control_the_production_elasticity_does_separate_the_paths(self):
        """
        The mirror of the test above: with the production beta1 the same two
        rate paths MUST diverge, and deeper in the money must prepay faster.
        Without this control, the invariance test could pass on a model in
        which the rate gap never does anything.
        """
        small = _run(PATH_SMALL_GAP, beta1=BETA1_PREPAY_MID)
        large = _run(PATH_LARGE_GAP, beta1=BETA1_PREPAY_MID)

        assert not np.allclose(
            small["hazard_cpr_pct"].to_numpy(),
            large["hazard_cpr_pct"].to_numpy(),
        )
        # +100bp in the money prepays faster than +50bp, every month.
        assert (
            large["hazard_cpr_pct"].to_numpy()
            > small["hazard_cpr_pct"].to_numpy()
        ).all()

    def test_marginal_is_exactly_zero_at_beta1_zero(self):
        """
        THE identity.  The lock-in marginal is
            score(production leg) - score(null leg)
        (hazard/no_lockin_null.py).  Score the beta1 = 0 leg against the
        zero-gap no-lock-in baseline and the marginal must be exactly 0.0 in
        both dollars and percentage points — not approximately, exactly.
        """
        empirical = _empirical_benchmark()

        null = score_extension_risk(_run(PATH_ZERO_GAP, beta1=0.0), empirical)
        leg = score_extension_risk(_run(PATH_LARGE_GAP, beta1=0.0), empirical)

        marginal_b = leg["hazard_trapped_b"] - null["hazard_trapped_b"]
        marginal_pp = leg["share_explained_pct"] - null["share_explained_pct"]

        assert marginal_b == 0.0
        assert marginal_pp == 0.0

    def test_marginal_is_nonzero_and_positive_at_the_production_elasticity(self):
        """
        Control for the identity: at the production beta1 the same comparison
        must produce a strictly nonzero marginal, and in the money faster
        prepayment means MORE roll-off, i.e. less trapped than the null.
        """
        empirical = _empirical_benchmark()

        null = score_extension_risk(
            _run(PATH_LARGE_GAP, beta1=0.0), empirical
        )
        prod = score_extension_risk(
            _run(PATH_LARGE_GAP, beta1=BETA1_PREPAY_MID), empirical
        )

        marginal_b = prod["hazard_trapped_b"] - null["hazard_trapped_b"]
        assert marginal_b != 0.0
        assert prod["hazard_trapped_b"] < null["hazard_trapped_b"]

    def test_constant_beta1_vector_matches_the_scalar_path(self):
        """
        competing_risks.monthly_step documents that a per-loan beta1 vector
        of constant value is elementwise bit-identical to the scalar path
        (round-15 Q3 group-ablation amendment).  The group-ablation runs read
        off that promise; nothing tested it.
        """
        scalar = _run(PATH_LARGE_GAP, beta1=BETA1_PREPAY_MID)
        vector = _run(
            PATH_LARGE_GAP,
            beta1=np.full(N_LOANS_TEST, BETA1_PREPAY_MID, dtype=np.float64),
        )

        np.testing.assert_array_equal(
            vector["simulated_rolloff_b"].to_numpy(),
            scalar["simulated_rolloff_b"].to_numpy(),
        )
        np.testing.assert_array_equal(
            vector["hazard_cpr_pct"].to_numpy(),
            scalar["hazard_cpr_pct"].to_numpy(),
        )

    def test_simulation_is_seed_deterministic(self):
        """Reruns at the same seed must reproduce exactly, or no identity above means anything."""
        a = _run(PATH_LARGE_GAP, beta1=BETA1_PREPAY_MID)
        b = _run(PATH_LARGE_GAP, beta1=BETA1_PREPAY_MID)
        pd.testing.assert_frame_equal(a, b)


class TestCprTransformConvexity:
    """
    cpr_annual_to_monthly_hazard(x) = 1 - (1 - x)^(1/12) is strictly convex on
    [0, 1).  Averaging a dispersed CPR path BEFORE converting therefore
    understates the mean monthly hazard — the whole dispersion-vs-structure
    diagnosis depends on that inequality running this way.
    """

    PATHS = [
        np.array([0.02, 0.10]),
        np.array([0.01, 0.05, 0.20]),
        np.array([0.001, 0.30]),
        np.array([0.04, 0.06, 0.08, 0.12, 0.25]),
        np.array([0.05, 0.05, 0.05, 0.40]),
    ]

    @pytest.mark.parametrize("path", PATHS)
    def test_jensen_gap_is_strictly_positive(self, path):
        """mean(f(path)) > f(mean(path)) strictly, for any non-degenerate path."""
        mean_of_f = float(cpr_annual_to_monthly_hazard(path).mean())
        f_of_mean = float(
            cpr_annual_to_monthly_hazard(np.array([path.mean()]))[0]
        )
        assert mean_of_f > f_of_mean
        assert mean_of_f - f_of_mean > 0.0

    def test_degenerate_path_has_no_gap(self):
        """A constant path is the equality case — Jensen is tight, not broken."""
        flat = np.full(8, 0.08)
        mean_of_f = float(cpr_annual_to_monthly_hazard(flat).mean())
        f_of_mean = float(
            cpr_annual_to_monthly_hazard(np.array([flat.mean()]))[0]
        )
        assert mean_of_f == pytest.approx(f_of_mean, rel=1e-12)

    def test_random_paths_never_violate_convexity(self):
        """
        Property check over many random non-degenerate paths inside the
        unclipped domain.  A concave or linearised replacement transform
        (e.g. dividing the annual CPR by 12) fails immediately.
        """
        rng = np.random.default_rng(SEED)
        for _ in range(200):
            path = rng.uniform(0.001, 0.45, size=rng.integers(2, 9))
            if np.allclose(path, path[0]):
                continue
            mean_of_f = float(cpr_annual_to_monthly_hazard(path).mean())
            f_of_mean = float(
                cpr_annual_to_monthly_hazard(np.array([path.mean()]))[0]
            )
            assert mean_of_f > f_of_mean, path

    def test_linear_transform_would_fail_this_test(self):
        """
        Documents what the property is worth: the naive CPR/12 transform is
        linear, so it has a zero Jensen gap and could not distinguish
        dispersion from structure.  Kept as a live comparison, not a comment.
        """
        path = np.array([0.02, 0.10, 0.30])
        linear_gap = float((path / 12).mean() - path.mean() / 12)
        real_gap = float(
            cpr_annual_to_monthly_hazard(path).mean()
            - cpr_annual_to_monthly_hazard(np.array([path.mean()]))[0]
        )
        assert linear_gap == pytest.approx(0.0, abs=1e-15)
        assert real_gap > 1e-6

    def test_transform_is_monotone_increasing(self):
        """Convexity without monotonicity would not be the intended transform."""
        grid = np.linspace(0.0, 0.9, 50)
        out = cpr_annual_to_monthly_hazard(grid)
        assert (np.diff(out) > 0).all()


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
