#!/usr/bin/env python3
"""
Round-17 R17-K (referee DC4): minimal two-parameter / two-moment
simulated-minimum-distance (SMD) diagnostic for the ABM.

SPEC (committed before execution; moments, distance, gates, and verdict
vocabulary fixed ex ante — same discipline as §25.3 external gates and
§26.3 ML comparator)
-----------------------------------------------------------------------
Reviewer ask (R17-K, DC4): a formal SMD calibration on an ABM subset —
does a JOINT fit of two parameters to two moments restore admissibility,
or does the structural family itself bind?  The committed record contains
the one-parameter version twice over: the production floor anchor (scale
36,085.9 hits CPR(8%) in [4,5]% but overshoots the zero-gap moving level)
and the external-gates anchor (scale 4,472.0 hits zero-gap CPR 0.0585 in
[5.5,6.3]% but drives CPR(8%) to 0.0%, recovery 150.6%).  The
one-parameter exponential mobility-desire family provably cannot hit both
external moments; this run tests whether TWO parameters can.

PARAMETERS (2)
--------------
1. Mobility-desire scale — the existing exponential-family parameter,
   searched over the same bracket as both committed calibrators
   [1,000, 500,000] (log10 internally).
2. pi0, a forced-move point mass — a fraction of households that moves
   each period regardless of rate gap, DTI, cost-benefit, or wait-and-see
   state, mixed into the exponential mobility-desire family as a fixed
   pre-committed subpopulation (union at the mover-mask level).
   STRUCTURAL-FAMILY FLAG (stated ex ante, per the roadmap): pi0 EXTENDS
   the structural family — it is not a re-anchoring of an existing
   production parameter.  That is the diagnostic's point: the production
   floor anchor smuggles the involuntary-turnover moment in through
   calibration; pi0 asks whether that moment's work is recoverable as an
   explicit structural term identified from external moments only.
   WHY NOT FREEZE SHARE: both moments below are evaluated at rate
   velocity 0, and the wait-and-see gate is inert unless the 6-month rate
   change exceeds 150bp — so WAIT_AND_SEE_PROB has exactly zero gradient
   on both moments and cannot serve as a second identifying parameter for
   this moment pair.

IMPLEMENTATION CONSTRAINT (production preserved bit-exactly)
------------------------------------------------------------
pi0 lives entirely in THIS script as an opt-in override: a context
manager (ForcedMoveOverride) that patches
HousingMarketEngine._movers_mask at class level for the duration of a
`with` block.  The wrapper calls the untouched production method and, iff
pi0 > 0, ORs in a fixed forced subset (first k = round(pi0*N) indices of
a permutation drawn once per engine from an independent RNG,
seed FORCED_SET_SEED — the production seed-42 draw stream is never
consumed or reordered; households are already constructed before the
wrapper can act).  At pi0 = 0 the wrapper returns the production
method's own ndarray untouched — bit-identical by construction, and
verified empirically by gate G2.  abm_lockin_simulation.py is NEVER
edited on disk.  Nested subsets (a single fixed permutation) make the
point mass monotone in pi0 with resolution 1/N = 0.01pp.
Danish column: the default Berger anchor is "dk_level", which never
consults _movers_mask, so pi0 enters the U.S. column only; the Danish
counterfactual stays anchored to external Danish levels (which already
embed actual Danish involuntary turnover).

MOMENTS (2, both EXTERNAL, fixed ex ante; both at velocity 0, default
friction TRANSACTION_COST_MEAN — identical conventions to the committed
runs)
---------------------------------------------------------------------
M1 zero-gap moving level: cpr_at(WAC, "US"), WAC = loans["coupon"].mean()
   — the exact convention of abm_external_gates.
   calibrate_mobility_scale_zero_gap.  Admissible band [5.5%, 6.3%]
   (imported from abm_external_gates.ANCHOR_BAND; Liebersohn-Rothstein
   zero-gap anchor, annualized 5.87%).
M2 deep-gap discount-cohort turnover: cpr_at(0.08, "US") — the exact
   floor-diagnostic convention.  Admissible band [4.0%, 5.0%] (the
   observed involuntary-turnover floor band the paper cites; identical to
   calibrate_mobility_scale_freddie's target and the external-gates
   floor_diagnostic band).
The wait-and-see freeze cannot affect either moment (velocity 0) — see
WHY NOT FREEZE SHARE above.

DISTANCE + FEASIBILITY RULE (ex ante)
-------------------------------------
D_edge(scale, pi0) = sum over moments of squared RELATIVE deviation from
the nearest band edge (exactly 0 inside the band); D_mid = the same with
deviations from band midpoints, REPORTED ALONGSIDE but not the criterion.
The FEASIBILITY verdict is band membership: feasible iff BOTH moments lie
inside their closed bands at the fitted point.  Fitted point = the
lexicographic (D_edge, then D_mid) minimum over every evaluated point
(coarse grid plus the Nelder-Mead trace); D_mid breaks ties on the
D_edge = 0 plateau so the fitted point is well defined.

SEARCH (cheap point evaluations only; NO surface build in the loop)
-------------------------------------------------------------------
Coarse grid: 25 log-spaced scales in [1,000, 500,000] x 13 pi0 values in
{0, 0.005, ..., 0.06} (pi0 > 0.05 forces M2 > 5% mechanically, so the
grid brackets the feasible region); one engine build per scale, moments
via cpr_at.  Refine: scipy Nelder-Mead on (log10 scale, pi0) from the
grid argmin, bounds [3, log10(5e5)] x [0, 0.10], maxfev 150.  Each
objective call is one engine build + two cpr_at calls — the same cost
class as the committed 30-iteration calibrators.

AFTER THE FIT: exactly ONE full surface build + scoring at the fitted
point through cross_design_test.run_variant (variant "smd_fitted"; real
Freddie structural covariates — the same harness and population as the
committed 59.3% variant and the external-gates run), under the pi0*
override, reporting recovery share and dollars.

GATES (all must PASS before the fit is interpreted; any failure writes
{"status": "GATE_FAILURE", ...} to the artifact and halts)
----------------------------------------------------------------------
G1 harness parity: with the override installed at pi0 = 0, run_variant
   ("recalibrated", committed scale 36,085.9375, cached committed
   surface) must replay the committed share 59.30299434493775 within
   +-0.05pp (tolerance imported from abm_external_gates.G1_TOL_PP).
   The cached surface is required to exist; it is never rebuilt here (a
   rebuild would not be the committed surface).  Note (stated ex ante):
   the cached path builds no engine, so G1 proves the patched class does
   not perturb the scoring harness; wrapped-ENGINE bit-preservation is
   G2's job — rebuilding the surface inside G1 would conflate FRED-macro
   drift with wrapper effects and cost a second full build.
G2 wrapper bit-parity: on an engine at the committed recalibrated scale,
   _cpr_vec outputs wrapped-at-pi0=0 vs unwrapped must be EXACTLY equal
   (tolerance 0.0 — bit-identical floats) at the pre-committed probe set
   rates {2%, 4.5%, 8%, WAC} x frictions {5%, 7%, 17.5%} x velocities
   {-1%, 0%, +2%, +3.5%} x systems {US, Danish} (96 points spanning the
   surface grid corners, the interior, and both moment points).
G2b wrapper liveness: at pi0 = 0.05 on the same engine, M2 must be
   >= 0.05 (union with a 500-household forced set makes this a
   mathematical certainty; a silently inert wrapper would fail).
G3 moment-convention parity: at the committed external-gates scale
   4,472.0458984375 and pi0 = 0, M1 must reproduce the committed
   zero-gap CPR 0.0585 within +-0.0010 (10bp CPR — absorbs small FRED
   median-revision drift in the engine build while remaining far tighter
   than the 40bp band half-width; any convention error, e.g. wrong
   friction, velocity, or WAC weighting, overshoots 10bp).

PRE-COMMITTED VERDICT VOCABULARY + READINGS
-------------------------------------------
joint_fit_infeasible — the achieved frontier (per-pi0 best D_edge) and
  the minimized distance are reported; reading: even one extra structural
  degree of freedom does not restore joint admissibility on the two
  external moments — this STRENGTHENS the external-gates conclusion that
  the structural family, not calibration effort, binds.
joint_fit_feasible — fitted (scale, pi0) reported and the surface-scored
  recovery evaluated against the pre-registered cross-design bands
  (cross_design_test.PREREGISTRATION: >50 / 10-35 / 35-50 / <10), with
  readings pre-committed per band in VERDICT_READINGS below.
INVARIANCE (pre-committed): the hazard-side headline quantities — the
  88.7% mechanical null and the +9.2pp lock-in marginal — are not
  functions of ABM calibration and cannot move under any outcome of this
  run.

OUTPUT:  abm/data/smd_two_moment_results.json  (headline stats only)
BYPRODUCT: abm/abm_cpr_surface_freddie_smd_fitted.csv (surface cache for
  the fitted variant, same pattern as the committed external variant)
NO-TOUCH: abm/abm_lockin_simulation.py, abm/cross_design_test.py,
  abm/abm_external_gates.py, abm/data/cross_design_results.json,
  abm/data/abm_external_gates_results.json,
  abm/abm_cpr_surface_freddie_recalibrated.csv,
  abm/abm_cpr_surface_freddie_frozen.csv, paper/, TECHNICAL.md.
RUNTIME: grid ~25 engine builds + 650 cpr_at calls, Nelder-Mead <=150
  further builds (minutes each side), then ONE 3,380-point surface build
  + scoring (the dominant cost; tens of minutes) — well under an hour
  end to end, plus FRED/SOMA fetch latency.
RUN:  cd abm && python3 smd_two_moment.py
"""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from scipy.optimize import minimize

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from abm_external_gates import (
    ANCHOR_BAND,
    G1_TOL_PP,
    RESULTS_JSON as EXTERNAL_GATES_JSON,
)
from cross_design_test import (
    PREREGISTRATION,
    RESULTS_JSON as CROSS_DESIGN_JSON,
    _build_engine,
    _surface_csv,
    run_variant,
)
from freddie_population import load_freddie_structural_sample
from paths import ABM_DIR

RESULTS_JSON = ABM_DIR / "data" / "smd_two_moment_results.json"

# --- Moments (ex ante) ------------------------------------------------------
M1_BAND = tuple(ANCHOR_BAND)          # zero-gap moving level, L&R anchor band
M2_BAND = (0.04, 0.05)                # observed involuntary-turnover floor
M2_RATE = 0.08                        # deep-gap market rate (floor convention)

# --- Parameter space (ex ante) ----------------------------------------------
SCALE_BRACKET = (1_000.0, 500_000.0)  # same bracket as both committed calibrators
LOG10_SCALE_BOUNDS = (math.log10(SCALE_BRACKET[0]), math.log10(SCALE_BRACKET[1]))
SCALE_GRID = np.geomspace(SCALE_BRACKET[0], SCALE_BRACKET[1], 25)
PI0_GRID = np.round(np.arange(0.0, 0.0601, 0.005), 6)   # 13 values
PI0_HARD_CAP = 0.10
FORCED_SET_SEED = 20260717            # independent of production RNG_SEED=42

# --- Nelder-Mead (ex ante) --------------------------------------------------
NM_MAXFEV = 150
NM_XATOL = 1e-3
NM_FATOL = 1e-15

# --- Gate tolerances (ex ante) ----------------------------------------------
G2_TOL = 0.0                          # bit-identical
G2B_FLOOR = 0.05                      # M2 >= 5% at pi0=0.05, mechanical
G3_TOL = 0.0010                       # +-10bp CPR on the 0.0585 replay

INVARIANCE_STATEMENT = (
    "Hazard-side headline quantities (the 88.7% mechanical null and the "
    "+9.2pp lock-in marginal) are not functions of ABM calibration and "
    "cannot move under any outcome of this run."
)

VERDICT_READINGS = {
    "joint_fit_infeasible": (
        "Even one extra structural degree of freedom (a forced-move point "
        "mass) does not restore joint admissibility on the two external "
        "moments; strengthens the external-gates conclusion that the "
        "structural family, not calibration effort, binds."
    ),
    "joint_fit_feasible_above_band": (
        "The extended two-parameter family is jointly admissible on both "
        "external moments and recovers >50% of the benchmark — under "
        "external-moments-only discipline this undercuts the paradigm "
        "reading and must be reported as such."
    ),
    "joint_fit_feasible_inside_band": (
        "The extended two-parameter family is jointly admissible on both "
        "external moments yet recovery stays inside the synthetic ABM's "
        "pre-registered 10-35% band — corroborates the paradigm-gap "
        "reading: joint admissibility does not buy recovery."
    ),
    "joint_fit_feasible_ambiguous": (
        "The extended two-parameter family is jointly admissible and "
        "recovery lands in the pre-registered 35-50% ambiguous zone — "
        "reported as ambiguous, per the standing pre-registration."
    ),
    "joint_fit_feasible_below_band": (
        "The extended two-parameter family is jointly admissible on both "
        "external moments and recovery falls below the synthetic 10% band "
        "edge — the paradigm gap survives, and the explicit involuntary "
        "mass yields even less recovery than the production floor anchor."
    ),
}

# ---------------------------------------------------------------------------
# pi0 override: opt-in, class-level, bit-exact at pi0=0 (gate G2)
# ---------------------------------------------------------------------------
_PROD_MOVERS_MASK = abm.HousingMarketEngine._movers_mask
_OVERRIDE_ACTIVE = False


def _forced_mask(engine, pi0: float) -> np.ndarray:
    """Fixed forced-move subpopulation: first k = round(pi0*N) entries of a
    per-engine permutation drawn from an independent RNG (nested subsets,
    monotone in pi0). Never touches the production RNG stream."""
    perm = getattr(engine, "_smd_forced_perm", None)
    if perm is None:
        perm = np.random.default_rng(FORCED_SET_SEED).permutation(
            engine.n_households)
        engine._smd_forced_perm = perm
    k = int(round(pi0 * engine.n_households))
    mask = np.zeros(engine.n_households, dtype=bool)
    if k > 0:
        mask[perm[:k]] = True
    return mask


class ForcedMoveOverride:
    """Patch HousingMarketEngine._movers_mask for the duration of a `with`
    block (class-level, so engines built inside run_variant/_build_engine
    are covered). pi0 <= 0 returns the production method's own ndarray —
    bit-identical by construction; verified by G2. Not re-entrant."""

    def __init__(self, pi0: float):
        if not (0.0 <= pi0 <= PI0_HARD_CAP):
            raise ValueError(f"pi0 out of range [0, {PI0_HARD_CAP}]: {pi0}")
        self.pi0 = float(pi0)

    def __enter__(self):
        global _OVERRIDE_ACTIVE
        if _OVERRIDE_ACTIVE:
            raise RuntimeError("ForcedMoveOverride is not re-entrant")
        _OVERRIDE_ACTIVE = True
        pi0 = self.pi0

        def _movers_mask_with_point_mass(engine_self, rate, system_type,
                                         friction, rate_velocity):
            base = _PROD_MOVERS_MASK(engine_self, rate, system_type,
                                     friction, rate_velocity)
            if pi0 <= 0.0:
                return base
            return base | _forced_mask(engine_self, pi0)

        abm.HousingMarketEngine._movers_mask = _movers_mask_with_point_mass
        return self

    def __exit__(self, exc_type, exc, tb):
        global _OVERRIDE_ACTIVE
        abm.HousingMarketEngine._movers_mask = _PROD_MOVERS_MASK
        _OVERRIDE_ACTIVE = False
        return False


# ---------------------------------------------------------------------------
# Distance (ex ante)
# ---------------------------------------------------------------------------
def _edge_dev(x: float, band: tuple) -> float:
    lo, hi = band
    if x < lo:
        return (lo - x) / lo
    if x > hi:
        return (x - hi) / hi
    return 0.0


def _mid_dev(x: float, band: tuple) -> float:
    mid = (band[0] + band[1]) / 2.0
    return (x - mid) / mid


def distance_edge(m1: float, m2: float) -> float:
    return _edge_dev(m1, M1_BAND) ** 2 + _edge_dev(m2, M2_BAND) ** 2


def distance_mid(m1: float, m2: float) -> float:
    return _mid_dev(m1, M1_BAND) ** 2 + _mid_dev(m2, M2_BAND) ** 2


def in_bands(m1: float, m2: float) -> tuple:
    return (M1_BAND[0] <= m1 <= M1_BAND[1], M2_BAND[0] <= m2 <= M2_BAND[1])


# ---------------------------------------------------------------------------
# Moment evaluation (cheap point evaluations; no surface build)
# ---------------------------------------------------------------------------
class MomentKit:
    def __init__(self, income: float, home_value: float, loans: pd.DataFrame):
        self.income = income
        self.home_value = home_value
        self.loans = loans
        self.wac = float(loans["coupon"].mean())   # external-gates convention
        self.n_engine_builds = 0
        self.trace = []

    def build_engine(self, scale: float):
        self.n_engine_builds += 1
        return _build_engine(float(scale), self.income, self.home_value,
                             self.loans)

    def moments(self, engine, pi0: float) -> tuple:
        with ForcedMoveOverride(pi0):
            m1 = float(engine.cpr_at(self.wac, "US"))     # velocity 0, mean friction
            m2 = float(engine.cpr_at(M2_RATE, "US"))
        return m1, m2

    def record(self, scale: float, pi0: float, m1: float, m2: float,
               stage: str) -> float:
        d_e = distance_edge(m1, m2)
        self.trace.append({
            "scale": float(scale), "pi0": float(pi0),
            "M1": m1, "M2": m2,
            "d_edge": d_e, "d_mid": distance_mid(m1, m2),
            "stage": stage,
        })
        return d_e


def fit_smd(kit: MomentKit) -> tuple:
    """Coarse grid then Nelder-Mead refine; returns (fitted_row, nm_result)."""
    print(f"Grid search: {len(SCALE_GRID)} scales x {len(PI0_GRID)} pi0 …")
    for i, scale in enumerate(SCALE_GRID, 1):
        engine = kit.build_engine(scale)
        for pi0 in PI0_GRID:
            m1, m2 = kit.moments(engine, pi0)
            kit.record(scale, pi0, m1, m2, "grid")
        if i % 5 == 0 or i == len(SCALE_GRID):
            print(f"  grid: {i}/{len(SCALE_GRID)} scales done")

    grid_best = min((r for r in kit.trace if r["stage"] == "grid"),
                    key=lambda r: (r["d_edge"], r["d_mid"]))
    print(f"  grid argmin: scale {grid_best['scale']:,.0f}, "
          f"pi0 {grid_best['pi0']:.3f}, D_edge {grid_best['d_edge']:.6g}")

    def objective(x):
        scale = 10.0 ** float(np.clip(x[0], *LOG10_SCALE_BOUNDS))
        pi0 = float(np.clip(x[1], 0.0, PI0_HARD_CAP))
        engine = kit.build_engine(scale)
        m1, m2 = kit.moments(engine, pi0)
        return kit.record(scale, pi0, m1, m2, "nelder_mead")

    x0 = np.array([math.log10(grid_best["scale"]), grid_best["pi0"]])
    print("Nelder-Mead refine …")
    nm = minimize(objective, x0, method="Nelder-Mead",
                  bounds=[LOG10_SCALE_BOUNDS, (0.0, PI0_HARD_CAP)],
                  options={"maxfev": NM_MAXFEV, "xatol": NM_XATOL,
                           "fatol": NM_FATOL})

    fitted = min(kit.trace, key=lambda r: (r["d_edge"], r["d_mid"]))
    return fitted, nm


def frontier_by_pi0(kit: MomentKit) -> list:
    """Achieved frontier: per-pi0 best (lexicographic) grid point."""
    rows = []
    for pi0 in PI0_GRID:
        cands = [r for r in kit.trace
                 if r["stage"] == "grid" and r["pi0"] == float(pi0)]
        best = min(cands, key=lambda r: (r["d_edge"], r["d_mid"]))
        rows.append({k: best[k] for k in
                     ("pi0", "scale", "M1", "M2", "d_edge", "d_mid")})
    return rows


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------
def _gate_failure(gate: str, detail: dict):
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(
        {"status": "GATE_FAILURE", "gate": gate, **detail},
        indent=2, default=float) + "\n")
    raise SystemExit(f"{gate} failure — SMD not run. {detail}")


def gate_g1(committed: dict, income, home_value, loans, df0, soma_rolloff) -> dict:
    """Harness parity: cached committed surface replayed under pi0=0 patch."""
    if not _surface_csv("recalibrated").exists():
        _gate_failure("G1", {"reason": "committed recalibrated surface CSV "
                                       "missing; refusing to rebuild it"})
    committed_share = committed["variants"]["recalibrated"]["share_pct"]
    with ForcedMoveOverride(0.0):
        a = run_variant("recalibrated",
                        committed["variants"]["recalibrated"]["mobility_scale"],
                        income, home_value, loans, df0, soma_rolloff)
    diff = a["share_pct"] - committed_share
    ok = abs(diff) <= G1_TOL_PP
    print(f"G1 parity: {a['share_pct']:.3f}% vs committed "
          f"{committed_share:.3f}% (diff {diff:+.4f}pp) "
          f"{'PASS' if ok else 'FAIL'}")
    if not ok:
        _gate_failure("G1", {"share_replayed": a["share_pct"],
                             "share_committed": committed_share,
                             "diff_pp": diff, "tol_pp": G1_TOL_PP})
    return {"share_replayed": a["share_pct"], "share_committed": committed_share,
            "diff_pp": diff, "tol_pp": G1_TOL_PP, "pass": ok,
            "replayed_variant": a}


def gate_g2(committed: dict, kit: MomentKit) -> dict:
    """Wrapper bit-parity at pi0=0 (exact float equality) + pi0 liveness."""
    scale = committed["variants"]["recalibrated"]["mobility_scale"]
    engine = kit.build_engine(scale)
    probes = [(rate, fric, vel, sys)
              for rate in (0.02, 0.045, M2_RATE, kit.wac)
              for fric in (0.05, abm.TRANSACTION_COST_MEAN, 0.175)
              for vel in (-0.01, 0.0, 0.02, 0.035)
              for sys in ("US", "Danish")]
    diffs = []
    for rate, fric, vel, sys in probes:
        base = engine._cpr_vec(rate, sys, fric, vel)          # unwrapped
        with ForcedMoveOverride(0.0):
            wrapped = engine._cpr_vec(rate, sys, fric, vel)   # pi0=0 wrapper
        diffs.append(abs(wrapped - base))
    max_diff = max(diffs)
    ok = max_diff <= G2_TOL
    print(f"G2 bit-parity: {len(probes)} probes, max |diff| = {max_diff!r} "
          f"{'PASS' if ok else 'FAIL'}")
    if not ok:
        _gate_failure("G2", {"n_probes": len(probes),
                             "max_abs_diff": max_diff, "tol": G2_TOL})
    m1_live, m2_live = kit.moments(engine, 0.05)
    ok_b = m2_live >= G2B_FLOOR - 1e-12
    print(f"G2b liveness: M2(pi0=0.05) = {m2_live:.4f} >= {G2B_FLOOR} "
          f"{'PASS' if ok_b else 'FAIL'}")
    if not ok_b:
        _gate_failure("G2b", {"m2_at_pi0_0p05": m2_live, "floor": G2B_FLOOR})
    return {"n_probes": len(probes), "max_abs_diff": max_diff, "tol": G2_TOL,
            "pass": ok,
            "G2b_liveness": {"m2_at_pi0_0p05": m2_live,
                             "floor": G2B_FLOOR, "pass": ok_b}}


def gate_g3(kit: MomentKit) -> dict:
    """Moment-convention parity: replay the committed external-gates
    zero-gap CPR 0.0585 at scale 4,472.0458984375, pi0=0."""
    ext = json.loads(EXTERNAL_GATES_JSON.read_text())
    scale_ext = ext["external_parameters"]["mobility_scale_external"]
    committed_cpr = ext["gates"]["G2_anchor"]["zero_gap_cpr"]
    engine = kit.build_engine(scale_ext)
    m1, _ = kit.moments(engine, 0.0)
    diff = m1 - committed_cpr
    ok = abs(diff) <= G3_TOL
    print(f"G3 convention parity: M1(scale {scale_ext:,.1f}, pi0=0) = "
          f"{m1:.4f} vs committed {committed_cpr:.4f} (diff {diff:+.5f}) "
          f"{'PASS' if ok else 'FAIL'}")
    if not ok:
        _gate_failure("G3", {"zero_gap_cpr": m1, "committed": committed_cpr,
                             "diff": diff, "tol": G3_TOL,
                             "scale_external": scale_ext})
    return {"zero_gap_cpr": m1, "committed": committed_cpr, "diff": diff,
            "tol": G3_TOL, "scale_external": scale_ext, "pass": ok}


# ---------------------------------------------------------------------------
def classify_recovery(share: float) -> str:
    if share > PREREGISTRATION["undercuts_paradigm_above_pct"]:
        return "above_band"
    lo, hi = PREREGISTRATION["corroborates_band_pct"]
    if lo <= share <= hi:
        return "inside_band"
    if hi < share <= PREREGISTRATION["undercuts_paradigm_above_pct"]:
        return "ambiguous_35_50"
    return "below_band"


_FEASIBLE_READING_KEY = {
    "above_band": "joint_fit_feasible_above_band",
    "inside_band": "joint_fit_feasible_inside_band",
    "ambiguous_35_50": "joint_fit_feasible_ambiguous",
    "below_band": "joint_fit_feasible_below_band",
}


def main() -> None:
    assert tuple(M1_BAND) == (0.055, 0.063), "M1 band drifted from ANCHOR_BAND"
    committed = json.loads(CROSS_DESIGN_JSON.read_text())

    print("Fetching macro/SOMA frames …")
    df0 = fed.fetch_data()
    soma_rolloff = fed.fetch_soma_mbs_monthly()
    income, home_value = abm.fetch_macro_from_fred()
    loans = load_freddie_structural_sample(abm.N_HOUSEHOLDS)

    kit = MomentKit(income, home_value, loans)
    print(f"WAC (zero-gap rate, external-gates convention) = {kit.wac:.4%}")

    # --- Gates (halt on failure) ------------------------------------------
    g1 = gate_g1(committed, income, home_value, loans, df0, soma_rolloff)
    g2 = gate_g2(committed, kit)
    g3 = gate_g3(kit)

    # --- Fit ---------------------------------------------------------------
    fitted, nm = fit_smd(kit)
    scale_star, pi0_star = fitted["scale"], fitted["pi0"]

    # Deterministic recheck at the fitted point (fresh engine).
    engine_star = kit.build_engine(scale_star)
    m1_star, m2_star = kit.moments(engine_star, pi0_star)
    recheck_diff = max(abs(m1_star - fitted["M1"]), abs(m2_star - fitted["M2"]))
    print(f"Fitted-point recheck: max moment diff {recheck_diff!r} "
          f"(expected 0.0 — engine is deterministic)")

    m1_ok, m2_ok = in_bands(m1_star, m2_star)
    feasible = m1_ok and m2_ok
    verdict = "joint_fit_feasible" if feasible else "joint_fit_infeasible"
    pi0_realized = round(pi0_star * abm.N_HOUSEHOLDS) / abm.N_HOUSEHOLDS

    print(f"\nFitted point: scale {scale_star:,.1f}, pi0 {pi0_star:.4f} "
          f"(realized point mass {pi0_realized:.4f})")
    print(f"  M1 = {m1_star:.4f} in [{M1_BAND[0]}, {M1_BAND[1]}]: {m1_ok}")
    print(f"  M2 = {m2_star:.4f} in [{M2_BAND[0]}, {M2_BAND[1]}]: {m2_ok}")
    print(f"  D_edge = {fitted['d_edge']:.6g}, D_mid = {fitted['d_mid']:.6g}")
    print(f"  VERDICT: {verdict}")

    # --- ONE surface build + scoring at the fitted point -------------------
    print("\nScoring fitted point through cross-design harness "
          "(one surface build) …")
    with ForcedMoveOverride(pi0_star):
        scored = run_variant("smd_fitted", scale_star, income, home_value,
                             loans, df0, soma_rolloff, rebuild=True)

    if feasible:
        band = classify_recovery(scored["share_pct"])
        reading = VERDICT_READINGS[_FEASIBLE_READING_KEY[band]]
        classification = band
    else:
        reading = VERDICT_READINGS["joint_fit_infeasible"]
        classification = "not_applicable_infeasible"

    payload = {
        "mode": "smd_two_moment",
        "spec": ("round-17 R17-K (DC4); two-parameter (mobility scale + "
                 "forced-move point mass pi0) / two-external-moment SMD; "
                 "cross-design harness; roadmap gate #43"),
        "structural_family_note": (
            "pi0 EXTENDS the structural family (opt-in wrapper in this "
            "script only; production engine untouched on disk and "
            "bit-preserved at pi0=0 per G2); diagnostic tests whether the "
            "floor anchor's work is recoverable from external moments"),
        "moments": {
            "M1_zero_gap": {"convention": "cpr_at(WAC, 'US', friction=mean, "
                                          "velocity=0); WAC = mean coupon",
                            "wac": kit.wac, "band": list(M1_BAND),
                            "source": "L&R zero-gap anchor "
                                      "(abm_external_gates.ANCHOR_BAND)"},
            "M2_deep_gap_floor": {"convention": "cpr_at(0.08, 'US', "
                                                "friction=mean, velocity=0)",
                                  "band": list(M2_BAND),
                                  "source": "observed involuntary-turnover "
                                            "floor band (paper-cited)"},
            "freeze_share_note": ("both moments at velocity 0 -> wait-and-see "
                                  "gate inert; freeze share has zero gradient "
                                  "and was rejected ex ante as the second "
                                  "parameter"),
        },
        "distance": {
            "criterion": "sum of squared relative deviations from nearest "
                         "band edge (0 inside band)",
            "reported_alongside": "sum of squared relative deviations from "
                                  "band midpoints",
            "feasibility_rule": "band membership of BOTH moments at the "
                                "fitted point (closed intervals)",
            "fitted_point_rule": "lexicographic (d_edge, d_mid) minimum over "
                                 "grid + Nelder-Mead trace",
        },
        "parameters": {
            "scale_bracket": list(SCALE_BRACKET),
            "pi0_bounds": [0.0, PI0_HARD_CAP],
            "pi0_grid_max": float(PI0_GRID[-1]),
            "forced_set_seed": FORCED_SET_SEED,
            "pi0_resolution": 1.0 / abm.N_HOUSEHOLDS,
        },
        "gates": {"G1_harness_parity": {k: g1[k] for k in
                                        ("share_replayed", "share_committed",
                                         "diff_pp", "tol_pp", "pass")},
                  "G2_wrapper_bit_parity": g2,
                  "G3_moment_convention": g3},
        "search": {
            "grid": {"n_scales": len(SCALE_GRID), "n_pi0": len(PI0_GRID),
                     "n_points": len(SCALE_GRID) * len(PI0_GRID)},
            "nelder_mead": {"maxfev": NM_MAXFEV, "xatol": NM_XATOL,
                            "n_fev": int(nm.nfev), "converged": bool(nm.success),
                            "message": str(nm.message)},
            "n_engine_builds": kit.n_engine_builds,
            "n_trace_evals": len(kit.trace),
        },
        "fitted": {
            "scale": scale_star,
            "pi0_requested": pi0_star,
            "pi0_realized_point_mass": pi0_realized,
            "M1": m1_star, "M2": m2_star,
            "M1_in_band": m1_ok, "M2_in_band": m2_ok,
            "d_edge": fitted["d_edge"], "d_mid": fitted["d_mid"],
            "recheck_max_moment_diff": recheck_diff,
        },
        "frontier_by_pi0": frontier_by_pi0(kit),
        "verdict": verdict,
        "verdict_reading": reading,
        "scored_at_fit": scored,
        "recovery_classification": classification,
        "preregistration": PREREGISTRATION,
        "committed_references": {
            "cross_design_share_recalibrated":
                committed["variants"]["recalibrated"]["share_pct"],
            "cross_design_scale_recalibrated":
                committed["variants"]["recalibrated"]["mobility_scale"],
            "external_gates_zero_gap_cpr": g3["committed"],
            "external_gates_scale": g3["scale_external"],
        },
        "invariance": INVARIANCE_STATEMENT,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")

    print("\n" + "=" * 68)
    print(" SMD TWO-MOMENT DIAGNOSTIC (R17-K / DC4)")
    print("=" * 68)
    print(f" Verdict: {verdict}")
    print(f" Fitted:  scale {scale_star:,.1f}, pi0 {pi0_realized:.4f}, "
          f"M1 {m1_star:.4f}, M2 {m2_star:.4f}, D_edge {fitted['d_edge']:.6g}")
    print(f" Scored:  {scored['share_pct']:.1f}% of benchmark "
          f"(${scored['trapped_b']:.1f}B) -> {classification}")
    print(" Frontier (per-pi0 best D_edge):")
    for row in payload["frontier_by_pi0"]:
        print(f"   pi0 {row['pi0']:.3f}: scale {row['scale']:>11,.0f}  "
              f"M1 {row['M1']:.4f}  M2 {row['M2']:.4f}  "
              f"D_edge {row['d_edge']:.6g}")
    print(f" {INVARIANCE_STATEMENT}")
    print(f" Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
