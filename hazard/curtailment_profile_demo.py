#!/usr/bin/env python3
"""
Curtailment time-profile demonstration (pre-committed; spec fixed in this
header before any run executed).

Reviewer item R17-I (referee Q2 + DC1, round 17). The reviewer asks for a
"monthly time-varying curtailment process tied to income" and a showing of
the marginal's stability under it. The premise is partly wrong — the
production curtailment already IS a monthly income-tied SMM
(fed_mbs_extension_risk.curtailment_series: DSPIC96 YoY mapped linearly to
CURTAILMENT_CPR_HEALTHY, ~0.84% annualized over the window) — and the
stability question has an ANALYTIC answer. This run is therefore a
DEMONSTRATION OF A CONSTRUCTION-LEVEL IDENTITY, not a sensitivity test:
there is no parameter here whose value is in doubt, only an identity whose
empirical exhibition the response letter can cite.

THE IDENTITY. Curtailment enters every U.S. leg only as an accounting-layer
netting term: Sum_t H_t * c_t, with H_t the ACTUAL WSHOMCB holdings path
(shared across legs) and c_t a monthly curtailment SMM computed once per
macro frame (fed_mbs_extension_risk.py, Curtailment_SMM assignment inside
compute_metrics; consumed additively in the microsim branch's U.S. rolloff).
The trapped-liquidity metric is a linear SIGNED sum of
(rolloff_t - target_t) over the 42-month QT window against a fixed
cap-target path (common/qt_window.py), with no per-month truncation. Hence
the identical H_t * c_t term subtracts out of (central - null) month by
month, and the lock-in marginal is invariant under ANY curtailment time
profile — seasonal, regime-split, arbitrary monthly — term-by-term, so
long as curtailment stays an accounting-layer flow (gate G2 enforces
exactly that). What a time profile CAN move is the common level: the
netted window total Sum_t H_t * c_t and hence the wedge — and because H_t
declines over the window, a front-loaded profile nets MORE dollars than a
back-loaded one of equal mean — uniformly across all U.S. legs.

SPEC (fixed ex ante) — four pre-committed profiles, applied as
multiplicative monthly factors on the curtailment SMM series:
  P0 UNIT      factor(t) = 1.0 every month (the parity leg).
  P1 SEASONAL  factor(t) = 1 + 0.25 * sin(2*pi*(month_of_year - 1)/12) —
               a mean-one month-of-year multiplier, +/-25% amplitude
               (peak April 1.25x, trough October 0.75x).
  P2 REGIME-SPLIT  factor(t) = 1.25 for calendar months before 2024-01,
               0.75 from 2024-01 on — an income-elasticity regime-break
               stand-in (2022-23 vs 2024-25), front-loaded by design.
  P3 SERVICER-MIX (round-18, R18-N optional)  a DETERMINISTIC two-servicer
               aggregation. Two servicer groups carry fixed portfolio
               shares s_A = 0.60 ("fast-remit") and s_B = 0.40
               ("slow-remit"), each with its OWN group-specific monthly
               factor: f_A(t) = 1.20 before 2024-01, 0.90 from 2024-01 on
               (a front-loaded servicer), and f_B(t) = 1.00 every month
               (a flat servicer). The share-weighted AGGREGATE is a single
               monthly factor a(t) = s_A f_A(t) + s_B f_B(t) = 1.12 before
               2024-01 and 0.94 from 2024-01 on, applied to the shared
               series exactly like P0–P2. The POINT of this profile is
               subsumption, not a new sensitivity: any servicer-
               heterogeneous curtailment pattern — however many groups,
               whatever their shares or group time-shapes — that is
               aggregated across servicers into a single monthly rate
               BEFORE it nets against the shared holdings path is, by that
               aggregation, one more monthly profile a(t), hence a special
               case of the identity below. It therefore moves only the
               common wedge (a(t) is front-loaded, so it nets more than
               unit) and leaves the marginal invariant to float headroom,
               exactly as P1/P2 do. The shares are asserted to sum to one
               (a servicer partition); the construction is fully
               deterministic with no draws.
- Machinery: the committed production caches, no microsim re-run. Each
  profile is scored on BOTH legs: the central Path B cache
  (data/microsim_results.parquet) and the beta1=0 null cache
  (data/microsim_results_pq0.0.parquet), read exactly as
  shared_layer_scoring.py reads them (_paths_from_combined_cache), scored
  through fed.compute_metrics(use_hazard_microsim=True) with
  _load_hazard_microsim_paths patched to the cached paths — the
  curtailment_danish_scaling.py (W6) harness. Live FRED + SOMA fetched
  once; no new data downloads.
- Profile patch: fed.curtailment_series is WRAPPED so the returned SMM
  series is multiplied by the profile factor (patch-and-restore per run,
  try/finally). Heritage warning, inherited from the W6 header: patching
  the fed.CURTAILMENT_CPR_HEALTHY global alone is a SILENT NO-OP — the
  constant is consumed only as a def-time-bound default argument of
  curtailment_series — so the function wrap is the operative patch. This
  script does not touch the global at all (the rate is not stressed; only
  the time shape is).

GATES (halt-on-fail BEFORE any new quantity prints; withdraw, do not
reinterpret; on failure a status payload is written to the artifact path
and the script exits nonzero):
  G1 unit-profile parity — anchors read AT RUNTIME from the committed
     data/shared_layer_scoring_results.json (never hardcoded; the values
     read at spec time are quoted here for the record):
       results.path_b_central.curtailment_netted_b = 69.56220187263008 $B
       results.no_lockin_null.curtailment_netted_b = 69.56220187263008 $B
       results.path_b_central.share_pct            = 97.9365273968041  %
       results.no_lockin_null.share_pct            = 88.73806762609433 %
     Netted totals within $0.01B (floor_form/W6 convention); shares within
     0.05pp. Residual differences at these gates are live-FRED input
     revisions, common to all runs here (the danish_discount_bound
     convention).
  G2 simulated CPR paths bit-identical across all profiles (US_CPR_Pct and
     Danish_CPR_Pct vs the unit-profile frame, per leg, asserted exactly
     0.0 as in the W6 script) — curtailment is accounting-layer only and
     no hazard/ module consumes it; any nonzero means the profile leaked
     into the simulation and the run must be withdrawn.
  G3 per profile, the netted monthly flow H_t * c_t applied to the central
     leg and to the null leg must be equal to machine precision
     month-by-month (gate: max |diff| <= 1e-9 $B; the expected and
     recorded outcome is exact bit-identity, since both legs compute it
     from the same macro frame through the same wrapped function).

PRE-COMMITTED EXPECTATION (the demonstration): for EVERY profile the
lock-in marginal — central minus null on the shared basis — equals the
unit-profile marginal to machine precision (tolerance 1e-6 pp / 1e-6 $B,
float-associativity headroom only, the W6 LINEARITY_TOL convention), and
the unit-profile marginal reproduces the committed
  +9.19845977070976 pp   (97.9365273968041 - 88.73806762609433)
  +$70.34506041989573 B  (748.9678825340305 - 678.6228221141348)
i.e. the manuscript's +9.199pp / +$70.345B, within the G1 tolerances.
The netted TOTAL is expected to move across profiles (P2 front-loads into
higher H_t months and so nets more dollars; P1 is mean-one and moves it
little) — that movement is the level/wedge channel and is reported, not
gated. If any profile moves the marginal beyond headroom the identity
claim is FALSIFIED: status payload, nonzero exit, withdraw not reinterpret.

DANISH LEGS OUT OF SCOPE: the W6 run (curtailment_danish_scaling.py)
already bounded the Danish curtailment differential below $1B across a
+/-25% level stress with exact endpoints (+$0.76B / +$0.66B, second-order
feedback pulling it DOWN at the high endpoint). This demo concerns the
U.S. marginal identity, where the netting is a common flow; the Danish
counterfactual-balance loop enters the institutional gap, not the U.S.
marginal. Danish columns still flow through the layer (it is two-regime by
interface) but no Danish quantity is gated or reported here beyond the G2
CPR bit-identity assertion.

Artifact: data/curtailment_profile_demo_results.json — headline stats
only: per-profile netted_b / wedge_pp / central_share / null_share /
marginal_pp / marginal_b, the max month-by-month
|central_netting - null_netting|, and the gates block. Liveness gate #45
(round-17 execution plan) will cross-check the artifact post-execution;
the gate is recorded by TECHNICAL.md, not by this script.

NO-TOUCH LIST: data/microsim_results.parquet and
data/microsim_results_pq0.0.parquet are read-only inputs;
data/shared_layer_scoring_results.json is a read-only anchor; the only
write is data/curtailment_profile_demo_results.json; fed module state is
patch-and-restored (try/finally) around every compute_metrics call; no
microsim re-run; no production cache is created, moved, or overwritten.

Run:  cd hazard && python3 curtailment_profile_demo.py
      -> data/curtailment_profile_demo_results.json
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "abm", _REPO / "hazard"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "curtailment_profile_demo_results.json"
SHARED_ANCHOR_ARTIFACT = DATA_DIR / "shared_layer_scoring_results.json"
NULL_CACHE = DATA_DIR / "microsim_results_pq0.0.parquet"

SEASONAL_AMPLITUDE = 0.25            # P1: +/-25% month-of-year amplitude
REGIME_PRE_FACTOR = 1.25             # P2: months before 2024-01
REGIME_POST_FACTOR = 0.75            # P2: months from 2024-01 on
REGIME_BREAK = pd.Period("2024-01", freq="M")

# P3 servicer_mix (round-18): a deterministic two-servicer partition whose
# group-specific monthly factors aggregate (share-weighted) to ONE monthly
# rate a(t) = s_A*f_A(t) + s_B*f_B(t) before it nets against the shared path.
SERVICER_A_SHARE = 0.60             # P3: "fast-remit" servicer group share
SERVICER_B_SHARE = 0.40             # P3: "slow-remit" servicer group share
SERVICER_A_PRE = 1.20               # P3: group A factor before 2024-01
SERVICER_A_POST = 0.90              # P3: group A factor from 2024-01 on
SERVICER_B_FACTOR = 1.00            # P3: group B factor (flat, every month)
assert abs(SERVICER_A_SHARE + SERVICER_B_SHARE - 1.0) < 1e-12, (
    "servicer shares must partition the book (sum to 1)")

PARITY_TOL_B = 0.01                  # $0.01B netting gates (W6 convention)
SHARE_PARITY_TOL_PP = 0.05           # share gates; residuals = live-FRED
NETTING_MATCH_TOL_B = 1e-9           # G3 machine-precision gate ($B)
MARGINAL_INVARIANCE_TOL_PP = 1e-6    # float-associativity headroom only
MARGINAL_INVARIANCE_TOL_B = 1e-6     # float-associativity headroom only


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _factor_unit(idx: pd.DatetimeIndex) -> np.ndarray:
    return np.ones(len(idx), dtype=float)


def _factor_seasonal(idx: pd.DatetimeIndex) -> np.ndarray:
    month = np.asarray(idx.month, dtype=float)
    return 1.0 + SEASONAL_AMPLITUDE * np.sin(2.0 * np.pi * (month - 1.0) / 12.0)


def _factor_regime(idx: pd.DatetimeIndex) -> np.ndarray:
    pre = idx.to_period("M") < REGIME_BREAK
    return np.where(pre, REGIME_PRE_FACTOR, REGIME_POST_FACTOR).astype(float)


def _factor_servicer_mix(idx: pd.DatetimeIndex) -> np.ndarray:
    """Deterministic two-servicer aggregation → one aggregate monthly rate.

    Group A ("fast-remit", share s_A) is front-loaded, f_A = 1.20 before the
    2024-01 break and 0.90 after; group B ("slow-remit", share s_B) is flat
    at 1.00. The share-weighted aggregate a(t) = s_A f_A(t) + s_B f_B(t) is a
    single monthly factor (1.12 pre-break, 0.94 after) applied to the shared
    curtailment SMM exactly like the other profiles — so any servicer-
    heterogeneous pattern that aggregates to a monthly rate is a special case
    of the identity, moving only the common wedge, not the marginal.
    """
    pre = idx.to_period("M") < REGIME_BREAK
    f_a = np.where(pre, SERVICER_A_PRE, SERVICER_A_POST).astype(float)
    f_b = np.full(len(idx), SERVICER_B_FACTOR, dtype=float)
    return SERVICER_A_SHARE * f_a + SERVICER_B_SHARE * f_b


PROFILES: dict[str, tuple[str, object]] = {
    "unit": (
        "factor(t) = 1.0 every month (parity leg)",
        _factor_unit,
    ),
    "seasonal": (
        "factor(t) = 1 + 0.25*sin(2*pi*(month_of_year-1)/12) — mean-one "
        "month-of-year multiplier, +/-25% amplitude",
        _factor_seasonal,
    ),
    "regime_split": (
        "factor(t) = 1.25 for months before 2024-01, 0.75 from 2024-01 on "
        "— income-elasticity regime-break stand-in",
        _factor_regime,
    ),
    "servicer_mix": (
        "deterministic two-servicer aggregation: shares 0.60/0.40 weight "
        "group factors f_A(t)=1.20 pre-2024-01/0.90 after and f_B(t)=1.00 "
        "into one monthly rate a(t)=1.12 pre/0.94 after — servicer "
        "heterogeneity that aggregates to a monthly rate, a special case of "
        "the identity",
        _factor_servicer_mix,
    ),
}


def _make_profiled_curtailment(original, factor_fn):
    """curtailment_series with the returned SMM multiplied by factor(t).

    The rate and income-fraction parameters pass through untouched; only
    the time shape is imposed. This wrap — not any module global — is the
    operative patch (see header: CURTAILMENT_CPR_HEALTHY is consumed only
    as a def-time-bound default argument of curtailment_series, so
    patching the global alone would be a silent no-op).
    """
    def patched(real_income_yoy_pct, **kwargs):
        base = original(real_income_yoy_pct, **kwargs)
        factors = pd.Series(
            factor_fn(base.index), index=base.index, dtype=float
        )
        return base * factors

    return patched


def _score_leg(fed, macro_abm, soma, micro_paths, factor_fn) -> dict:
    """One (profile, leg) pass through the shared accounting layer."""
    original_series = fed.curtailment_series
    original_loader = fed._load_hazard_microsim_paths
    fed.curtailment_series = _make_profiled_curtailment(
        original_series, factor_fn
    )
    fed._load_hazard_microsim_paths = lambda df: micro_paths
    try:
        m = fed.compute_metrics(
            macro_abm.copy(),
            soma_rolloff=soma,
            use_hazard_microsim=True,
            apply_settlement_lag_kernel=True,  # auto-off in microsim mode
        )
    finally:
        fed.curtailment_series = original_series
        fed._load_hazard_microsim_paths = original_loader

    qt = fed.qt_active_frame(m)
    assert len(qt) == fed.expected_qt_active_months(), (
        f"qt_active_frame has {len(qt)} months; expected "
        f"{fed.expected_qt_active_months()}"
    )
    hm = fed.export_headline_metrics(m)
    d = hm["dollars_b"]

    # Netted monthly flow: curtailment SMM on the ACTUAL holdings path —
    # by definition identical to the layer's own curtailment_b.total.
    netting_monthly = qt["WSHOMCB"] / 1_000 * qt["Curtailment_SMM"]
    netted = float(netting_monthly.sum())
    assert abs(netted - hm["curtailment_b"]["total"]) < 1e-9, (
        "window convention drift: frame-based netting != "
        "export_headline_metrics curtailment_b.total"
    )
    return {
        "frame": m,
        "netting_monthly": netting_monthly,
        "netted_b": netted,
        "share_pct": d["share_explained_pct"],
        "us_trapped_b": d["us_trapped"],
        "empirical_trapped_b": d["empirical_trapped"],
        "factor_window_mean": float(np.mean(factor_fn(qt.index))),
    }


def _fail(payload_base: dict, status: str, extra: dict, message: str):
    """House convention: gate failures write a status payload and exit."""
    payload = dict(payload_base)
    payload["status"] = status
    payload.update(extra)
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=float)
        f.write("\n")
    raise SystemExit(
        f"{status} — status payload written to {RESULTS_JSON} for "
        f"diagnosis; the run must be withdrawn, not reinterpreted. "
        f"{message}"
    )


def main() -> None:
    import fed_mbs_extension_risk as fed

    from config import MICROSIM_RESULTS_PATH
    from shared_layer_scoring import _paths_from_combined_cache

    t0 = time.perf_counter()

    payload_base = {
        "mode": "curtailment_profile_demo",
        "spec": ("hazard/curtailment_profile_demo.py module docstring "
                 "(fixed ex ante)"),
        "framing": ("demonstration of a construction-level identity "
                    "(R17-I / referee Q2 + DC1), not a sensitivity test"),
        "git_commit": _git_head(),
        "created_utc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"),
        "layer": ("fed_mbs_extension_risk.compute_metrics("
                  "use_hazard_microsim=True) over the committed production "
                  "caches (data/microsim_results.parquet central; "
                  "data/microsim_results_pq0.0.parquet null)"),
        "profiles": {name: desc for name, (desc, _) in PROFILES.items()},
    }

    # ---- Anchors: read at runtime from the committed artifact ---------------
    shared_anchor = json.load(open(SHARED_ANCHOR_ARTIFACT))
    res_anchor = shared_anchor["results"]
    anchor = {
        "netted_b_central": (
            res_anchor["path_b_central"]["curtailment_netted_b"]),
        "netted_b_null": (
            res_anchor["no_lockin_null"]["curtailment_netted_b"]),
        "share_central_pct": res_anchor["path_b_central"]["share_pct"],
        "share_null_pct": res_anchor["no_lockin_null"]["share_pct"],
        "us_trapped_central_b": res_anchor["path_b_central"]["us_trapped_b"],
        "us_trapped_null_b": res_anchor["no_lockin_null"]["us_trapped_b"],
    }
    anchor["marginal_pp"] = (
        anchor["share_central_pct"] - anchor["share_null_pct"])
    anchor["marginal_b"] = (
        anchor["us_trapped_central_b"] - anchor["us_trapped_null_b"])
    payload_base["anchors"] = {
        **anchor,
        "source": ("data/shared_layer_scoring_results.json: "
                   "results.{path_b_central,no_lockin_null}"
                   ".{curtailment_netted_b,share_pct,us_trapped_b}"),
    }

    print("Fetching ABM macro + SOMA (once; live FRED) …")
    macro_abm = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()

    print("Loading committed production microsim caches …")
    legs = {
        "central": _paths_from_combined_cache(MICROSIM_RESULTS_PATH),
        "null": _paths_from_combined_cache(NULL_CACHE),
    }

    # ---- Score every (profile, leg) pair; print progress only ---------------
    runs: dict[str, dict[str, dict]] = {}
    for name, (_desc, factor_fn) in PROFILES.items():
        runs[name] = {}
        for leg, micro_paths in legs.items():
            print(f"Scoring profile {name} / {leg} leg …")
            runs[name][leg] = _score_leg(
                fed, macro_abm, soma, micro_paths, factor_fn
            )
    runtime_s = time.perf_counter() - t0

    # ---- Structural assertion: empirical benchmark invariant ----------------
    emp0 = runs["unit"]["central"]["empirical_trapped_b"]
    for name in PROFILES:
        for leg in legs:
            assert abs(
                runs[name][leg]["empirical_trapped_b"] - emp0
            ) < 1e-9, "empirical benchmark moved across runs"

    # ---- G1: unit-profile parity against the committed artifact -------------
    unit = runs["unit"]
    g1_checks = {
        "netted_b_central": (
            unit["central"]["netted_b"], anchor["netted_b_central"],
            PARITY_TOL_B),
        "netted_b_null": (
            unit["null"]["netted_b"], anchor["netted_b_null"],
            PARITY_TOL_B),
        "share_central_pct": (
            unit["central"]["share_pct"], anchor["share_central_pct"],
            SHARE_PARITY_TOL_PP),
        "share_null_pct": (
            unit["null"]["share_pct"], anchor["share_null_pct"],
            SHARE_PARITY_TOL_PP),
    }
    g1 = {}
    for gname, (got, want, tol) in g1_checks.items():
        ok = abs(got - want) < tol
        g1[gname] = {"got": got, "want": want, "tol": tol, "pass": bool(ok)}
        print(f"G1 parity {gname}: got {got:.6f} want {want:.6f} "
              f"(tol {tol:g}) [{'PASS' if ok else 'FAIL'}]")

    # ---- G2: CPR paths bit-identical across profiles (per leg) --------------
    g2 = {}
    for name in PROFILES:
        for leg in legs:
            m_p = runs[name][leg]["frame"]
            m_0 = runs["unit"][leg]["frame"]
            us_diff = float(np.abs(
                m_p["US_CPR_Pct"].to_numpy()
                - m_0["US_CPR_Pct"].to_numpy()).max())
            dk_diff = float(np.abs(
                m_p["Danish_CPR_Pct"].to_numpy()
                - m_0["Danish_CPR_Pct"].to_numpy()).max())
            ok = us_diff == 0.0 and dk_diff == 0.0
            g2[f"{name}/{leg}"] = {
                "max_abs_us_cpr_diff_pp": us_diff,
                "max_abs_danish_cpr_diff_pp": dk_diff,
                "pass": bool(ok),
            }
            print(f"G2 CPR bit-identity {name}/{leg}: us {us_diff} "
                  f"dk {dk_diff} [{'PASS' if ok else 'FAIL'}]")

    # ---- G3: central-vs-null netting equal month-by-month -------------------
    g3 = {}
    for name in PROFILES:
        diff = (runs[name]["central"]["netting_monthly"]
                - runs[name]["null"]["netting_monthly"])
        max_abs = float(diff.abs().max())
        ok = max_abs <= NETTING_MATCH_TOL_B
        g3[name] = {
            "max_month_abs_netting_diff_b": max_abs,
            "netting_bit_identical": bool(max_abs == 0.0),
            "tol_b": NETTING_MATCH_TOL_B,
            "pass": bool(ok),
        }
        print(f"G3 netting central-vs-null {name}: max |diff| "
              f"{max_abs} $B [{'PASS' if ok else 'FAIL'}]")

    gates = {"G1_unit_parity": g1, "G2_cpr_bit_identity": g2,
             "G3_netting_central_vs_null": g3}
    gates_all_pass = (
        all(v["pass"] for v in g1.values())
        and all(v["pass"] for v in g2.values())
        and all(v["pass"] for v in g3.values())
    )
    gates["all_pass"] = gates_all_pass
    if not gates_all_pass:
        _fail(payload_base, "GATE_FAILURE",
              {"gates": gates, "runtime_s": round(runtime_s, 1)},
              "A parity or structural gate failed before any new quantity "
              "was reported.")

    # ---- Report (gates passed; new quantities may now print) ----------------
    unit_marginal_pp = (unit["central"]["share_pct"]
                        - unit["null"]["share_pct"])
    unit_marginal_b = (unit["central"]["us_trapped_b"]
                       - unit["null"]["us_trapped_b"])

    results = {}
    print("\n" + "=" * 78)
    print(" CURTAILMENT TIME-PROFILE DEMONSTRATION — U.S. marginal identity")
    print("=" * 78)
    for name in PROFILES:
        c, n = runs[name]["central"], runs[name]["null"]
        netted = c["netted_b"]
        wedge_pp = netted / emp0 * 100.0
        marginal_pp = c["share_pct"] - n["share_pct"]
        marginal_b = c["us_trapped_b"] - n["us_trapped_b"]
        results[name] = {
            "netted_b": netted,
            "wedge_pp": wedge_pp,
            "central_share": c["share_pct"],
            "null_share": n["share_pct"],
            "marginal_pp": marginal_pp,
            "marginal_b": marginal_b,
            "marginal_departure_from_unit_pp": marginal_pp - unit_marginal_pp,
            "marginal_departure_from_unit_b": marginal_b - unit_marginal_b,
            "max_abs_netting_diff_central_vs_null_b": (
                g3[name]["max_month_abs_netting_diff_b"]),
            "factor_window_mean": c["factor_window_mean"],
        }
        print(
            f"{name:<14} netted ${netted:6.2f}B  wedge {wedge_pp:5.2f}pp  "
            f"central {c['share_pct']:7.3f}%  null {n['share_pct']:7.3f}%  "
            f"marginal {marginal_pp:+.6f}pp / ${marginal_b:+.4f}B  "
            f"(dep. vs unit {marginal_pp - unit_marginal_pp:+.2e}pp)"
        )

    # ---- Pre-committed expectation: marginal invariant across profiles ------
    identity_holds = all(
        abs(r["marginal_departure_from_unit_pp"]) < MARGINAL_INVARIANCE_TOL_PP
        and abs(r["marginal_departure_from_unit_b"]) < MARGINAL_INVARIANCE_TOL_B
        for r in results.values()
    )
    demonstration = {
        "unit_marginal_pp": unit_marginal_pp,
        "unit_marginal_b": unit_marginal_b,
        "committed_marginal_pp": anchor["marginal_pp"],
        "committed_marginal_b": anchor["marginal_b"],
        "invariance_tol_pp": MARGINAL_INVARIANCE_TOL_PP,
        "invariance_tol_b": MARGINAL_INVARIANCE_TOL_B,
        "identity_holds": bool(identity_holds),
    }
    verdict = (
        "the lock-in marginal is identical across all curtailment time "
        "profiles to float-associativity headroom — the construction-level "
        "identity is demonstrated, no claim change"
        if identity_holds
        else "a profile moved the marginal beyond float headroom — the "
        "identity claim is falsified; withdraw, do not reinterpret"
    )
    demonstration["verdict"] = verdict
    print(f"\nunit marginal {unit_marginal_pp:+.11f}pp / "
          f"${unit_marginal_b:+.10f}B  (committed "
          f"{anchor['marginal_pp']:+.11f}pp / ${anchor['marginal_b']:+.10f}B)")
    print(f"verdict: {verdict}")

    if not identity_holds:
        _fail(payload_base, "IDENTITY_FALSIFIED",
              {"gates": gates, "results": results,
               "demonstration": demonstration,
               "runtime_s": round(runtime_s, 1)},
              "The pre-committed marginal-invariance expectation failed.")

    payload = dict(payload_base)
    payload.update({
        "status": "ok",
        "gates": gates,
        "results": results,
        "demonstration": demonstration,
        "runtime_s": round(runtime_s, 1),
    })
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=float)
        f.write("\n")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
