#!/usr/bin/env python3
"""
Round-17 R17-C: wait-and-see freeze ablation + parameter sweep (referee T3/Q4).

SPEC (committed before execution; gates and interpretation fixed ex ante)
-------------------------------------------------------------------------
Reviewer item R17-C (T3 + Q4, paper/v16/revision_roadmap_round17.md; liveness
gate #39): the 20% freeze share and 150bp/6-month trigger are author
calibrations (conceded at tex L119).  The falsification waterfall bundles
DTI + loss aversion + wait-and-see into one stage, so the freeze's separate
contribution to the production headline is not isolable from any committed
artifact, and no trigger/share sweep with the floor anchor RETAINED exists
(the round-15 external-gates run changed the share jointly with dropping the
floor).  This run supplies both, in the production accounting.

STRUCTURAL FACT (stated ex ante, exploited throughout): the involuntary-
turnover floor anchor is computed by abm_lockin_simulation.calibrate_
mobility_scale via engine.cpr_at(0.08, "US"), whose rate_velocity parameter
DEFAULTS TO 0.0, while the freeze gate binds only when rate_velocity >
WAIT_AND_SEE_RATE_THRESHOLD (strict inequality; lines ~250-252 and ~464-465).
The floor anchor therefore lives entirely in the zero-velocity regime and NO
freeze parameterization (share or trigger) can move it, by construction.
Gate G6 asserts this rather than assumes it; the assertion is the
pre-committed answer to Q4's "without compromising the involuntary-turnover
floor".  A corollary (asserted as G1, mirroring the committed fig8 generator
in figures/make_figures.py): velocity enters the committed CPR surface ONLY
through the freeze, so the ten velocity slices collapse to two regimes
(unfrozen: v <= 0.015; frozen: v > 0.015).  Freeze-off ablation and trigger
re-parameterization are therefore pure re-mappings of which velocity regime
each realized QT month reads on the COMMITTED surface — no surface rebuild.

PART 1 — freeze-off ablation + trigger sweep (committed-surface arithmetic).
  Scoring path: the frozen production accounting — fed_mbs_extension_risk.
  compute_metrics(surface=committed abm_cpr_surface.csv as multi-cohort dict,
  soma_rolloff=SOMA monthly, cohorts=live SOMA cohorts, use_burnout=False,
  apply_settlement_lag_kernel=True) → export_headline_metrics, i.e. the exact
  build_production_metrics path that froze run-2026-07-05-berger, minus the
  (unused-in-this-path) mobility recalibration and with the committed surface
  loaded from disk (sha-checked) instead of rebuilt.
  Realized coordinate stream: each month's (MORTGAGE30US, Dynamic_Friction,
  Rate_6M_Change) as computed inside compute_metrics from the live-refetched
  frame — the same stream the frozen run consumed (G2 certifies parity).
  Variants re-map ONLY the velocity coordinate handed to interp_cpr_surface
  (monkeypatched wrapper, restored in finally):
    production leg ..... raw realized Rate_6M_Change (trilinear, as frozen);
    freeze_off ......... every month -> 0.0 (unfrozen node);
    trigger tau in {100bp, 150bp, 200bp} .. v > tau -> 0.020 (frozen node),
                         else -> 0.0.  Strict >, matching the engine gate.
  Note stated ex ante: the committed surface's trilinear lookup renders the
  freeze as a linear ramp across realized velocity in (0.015, 0.020) rather
  than a step at 0.015; the production leg reproduces that committed ramp,
  the binary trigger legs pin a step at the stated tau (so trigger_150bp is
  reported alongside, not identical to, the production leg; they differ only
  in partial-freeze months, whose count is reported).
  Headline of Part 1: freeze isolated contribution = production - freeze_off
  (trapped $B, recovery-share pp, mean-CPR pp), reported as descriptive
  accounting.

PART 2 — share sweep {10%, 18.26% (L&R-implied, committed), 30%}, floor
  anchor RETAINED (one multi-cohort surface rebuild per share).
  Harness: the external-gates pattern (abm_external_gates.py) — override the
  module constant abm.WAIT_AND_SEE_PROB, run calibrate_mobility_scale exactly
  as production does (reference-cohort anchor, pinned manifest medians), one
  build_multi_cohort_surfaces per share, restore in finally.
  Scoring path: the SAME path as Part 1's production leg (compute_metrics on
  the rebuilt multi-cohort surface with raw realized velocities) — chosen
  over cross_design_test.run_variant so both parts report in the same
  production accounting units; its parity gate is G4+G5 below (the rebuilt
  production-share surface must reproduce the committed abm_cpr_surface.csv
  bit-style, and its score must equal the Part 1 production leg).
  The L&R-implied share is READ from the committed
  abm/data/abm_external_gates_results.json (external_parameters.
  wait_and_see_prob = 0.18259962499999982; derivation 1-(1-0.065)^(1.5x2);
  run aa65eee, TECHNICAL.md sec 25.3) — not re-derived.

PARITY GATES (all HALT with a GATE_FAILURE artifact before any new quantity
is printed for the part they guard; no hardcoded expected results except
parity to committed values, each read from its committed file at runtime):
  G0 committed-state identity:
     a. abm/data/latest_run_manifest.json run_tag == "run-2026-07-05-berger"
        (the reference run; its manifest lives at
        abm/data/runs/run-2026-07-05-berger/manifest.json);
     b. sha256(abm/abm_cpr_surface.csv) == manifest inputs.abm_cpr_surface_
        sha256 (committed value a828fcbe5c33ce40b75719f64c64ad84c8135da4
        5c00089578c6146889caa2d6);
     c. abm.WAIT_AND_SEE_RATE_THRESHOLD == 0.015, abm.WAIT_AND_SEE_PROB ==
        0.20, and the velocity grid contains the 0.0 / 0.015 / 0.020 nodes;
     d. committed L&R share == 1-(1-0.065)^3 within 1e-12.
  G1 two-regime velocity structure of the committed surface, per cohort and
     for both CPR_US and CPR_Danish (atol 1e-12), plus non-vacuity (the two
     US regimes differ somewhere).  Mirrors the fig8 assertion.
  G2 production-leg parity vs the frozen manifest metrics (run tag
     run-2026-07-05-berger):
     a. live SOMA cohort keyset == committed surface keyset (11 cohorts);
        reference cohort == manifest reference (coupon 0.02, 60mo);
        SOMA monthly rolloff available (manifest rolloff_source "SOMA");
     b. us_trapped 84.50667328005531 B  (tol +-0.5 B)
        share_explained 11.050260386204029 % (tol +-0.10 pp)
        empirical_trapped 764.7482532227002 B (tol +-0.5 B)
        danish_trapped 812.9212962858466 B (tol +-0.5 B)
        us_cpr_mean 11.760904343422906 % (tol +-0.05 pp).
     Tolerances absorb only upstream data-revision noise in the live refetch
     (FRED/SOMA); the scoring arithmetic itself is deterministic.
  G3 calibration parity: calibrate_mobility_scale with the manifest-pinned
     inputs (income 83730.0, home 403200.0, reference cohort 2.00%/60mo, all
     read from the manifest) must reproduce the manifest mobility_scale
     43882.8125 (tol 1e-6) — certifies the HEAD engine still reproduces the
     committed calibration before any rebuild is interpreted.
  G4 surface-rebuild parity: the rebuilt production-share (20%) multi-cohort
     surface must equal the committed abm_cpr_surface.csv on the identical
     grid (max |delta CPR| <= 1e-12, both columns) — certifies HEAD engine
     spec parity so share-variant surfaces differ only via the share.
  G5 rescore identity: the rebuilt 20% surface scored through the Part 1
     path must reproduce the Part 1 production leg (|delta trapped| <= 1e-6
     B, i.e. one thousand dollars on an $84.5B quantity; looser than G4's
     1e-12 surface tolerance can propagate) — ties the two parts' scoring
     paths together.
  G6 floor invariance (the Q4 gate), per share s in {0.10, L&R, 0.30}: the
     production calibration re-run under WAIT_AND_SEE_PROB = s must return a
     scale identical to the production-share calibration (tol 1e-9) and an
     identical zero-velocity floor CPR at 8% market (tol 1e-12).

PRE-COMMITTED INTERPRETATION (fixed before results): all Part 1 and Part 2
numbers are reported as descriptive accounting — the freeze's isolated
contribution to the production headline and the recovery numbers under
alternative triggers/shares.  The G6 invariance assertion, not any recovery
number, is the answer to Q4's "without compromising the involuntary-turnover
floor": the floor cannot move because the anchor is evaluated at zero rate
velocity, where the freeze gate never binds.  No verdict vocabulary beyond
reporting contributions and the invariance check.

SCOPE NOTE (stated ex ante): parity anchors to run-2026-07-05-berger — the
latest frozen production accounting (abm/data/latest_run_manifest.json) and
the one the committed abm_cpr_surface.csv belongs to (sha match).  The paper
headline tag run-2026-07-04-15yr-foldin ($90.98B / 11.90%) is NOT
reproducible at HEAD (its surface predates the native-15yr gate; different
sha), so freeze contributions are reported against the berger accounting
($84.5B / 11.05%); the prose pass must label the basis accordingly.

Output:  abm/data/freeze_sensitivity_results.json (headline statistics only)
Run:     cd abm && python3 freeze_sensitivity.py
Runtime: Part 1 minutes (network + five compute_metrics scorings on the
         committed surface); Part 2 four multi-cohort surface builds
         (11 cohorts x 3,380 grid points each; the build is documented as
         minutes-scale) + three calibrations — roughly 10-30 minutes
         end-to-end.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from paths import ABM_CPR_SURFACE_CSV, ABM_DIR, LATEST_RUN_MANIFEST, RUNS_DIR

RESULTS_JSON = ABM_DIR / "data" / "freeze_sensitivity_results.json"
EXTERNAL_GATES_JSON = ABM_DIR / "data" / "abm_external_gates_results.json"

REFERENCE_RUN_TAG = "run-2026-07-05-berger"

# Part 1 trigger sweep (decimal 6-month rate change; strict >, engine gate).
TRIGGER_GRID = (0.010, 0.015, 0.020)
# Part 2 share sweep endpoints; the middle value is READ from the committed
# external-gates artifact at runtime (G0d checks its derivation).
SHARE_LOW, SHARE_HIGH = 0.10, 0.30

# Velocity nodes used by the Part 1 re-mapping (validated by G0c/G1).
UNFROZEN_NODE = 0.0
FROZEN_NODE = 0.020

# Gate tolerances (see header).
G2_TOL_TRAPPED_B = 0.5
G2_TOL_SHARE_PP = 0.10
G2_TOL_CPR_MEAN_PP = 0.05
G3_TOL_SCALE = 1e-6
G4_TOL_SURFACE = 1e-12
G5_TOL_TRAPPED_B = 1e-6
G6_TOL_SCALE = 1e-9
G6_TOL_FLOOR = 1e-12
FLOOR_RATE = 0.08  # calibration anchor market rate (production value)


# ---------------------------------------------------------------------------
# Gate plumbing: HALT with a GATE_FAILURE artifact before new quantities.
# ---------------------------------------------------------------------------
def gate_fail(gate: str, detail: dict) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"status": "GATE_FAILURE", "gate": gate, "detail": detail,
         "generated_utc": datetime.now(timezone.utc).isoformat()},
        indent=2, default=float) + "\n")
    raise SystemExit(f"{gate} FAILURE — run halted before interpretation. "
                     f"Detail written to {RESULTS_JSON}")


def check(gate: str, ok: bool, detail: dict, msg: str) -> None:
    print(f"{gate}: {msg} {'PASS' if ok else 'FAIL'}")
    if not ok:
        gate_fail(gate, detail)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Surface helpers
# ---------------------------------------------------------------------------
def surface_keyset(surf_df: pd.DataFrame) -> set:
    return {(fed._round_coupon(c), int(t))
            for c, t in surf_df.groupby(["Cohort_Coupon", "Cohort_Term"])
                               .groups.keys()}


def surface_df_to_dict(surf_df: pd.DataFrame) -> dict:
    """Multi-cohort surface DataFrame -> load_cpr_surface()-style dict."""
    surfaces = {}
    for (coupon, term), grp in surf_df.groupby(["Cohort_Coupon",
                                                "Cohort_Term"]):
        slab = grp.drop(columns=["Cohort_Coupon", "Cohort_Term"])
        surfaces[(fed._round_coupon(coupon), int(term))] = \
            fed._surface_tuple_from_dataframe(slab)
    return surfaces


def two_regime_check(surf_df: pd.DataFrame, threshold: float) -> dict:
    """G1: velocity enters only through the freeze (fig8 assertion pattern).

    For every cohort and both CPR columns, all slices with v <= threshold
    must equal the v=0 slice and all slices with v > threshold must equal
    the v=FROZEN_NODE slice.  Returns summary stats; raises via gate_fail
    on violation.
    """
    max_regime_dev = 0.0
    max_us_regime_gap = 0.0
    for (coupon, term), grp in surf_df.groupby(["Cohort_Coupon",
                                                "Cohort_Term"]):
        def vel_slice(v, g=grp):
            return (g[np.isclose(g.Rate_Velocity, v)]
                    .sort_values(["Friction", "Market_Rate"]))
        base, frozen = vel_slice(UNFROZEN_NODE), vel_slice(FROZEN_NODE)
        for col in ("CPR_US", "CPR_Danish"):
            for v in np.sort(grp.Rate_Velocity.unique()):
                ref = frozen if v > threshold + 1e-4 else base
                dev = float(np.max(np.abs(vel_slice(v)[col].values
                                          - ref[col].values)))
                max_regime_dev = max(max_regime_dev, dev)
                if dev > 1e-12:
                    gate_fail("G1_two_regime", {
                        "cohort": [float(coupon), int(term)],
                        "column": col, "velocity": float(v),
                        "max_abs_dev": dev,
                    })
        max_us_regime_gap = max(
            max_us_regime_gap,
            float(np.max(np.abs(base.CPR_US.values - frozen.CPR_US.values))),
        )
    if max_us_regime_gap <= 0.0:
        gate_fail("G1_two_regime", {
            "reason": "freeze vacuous: frozen and unfrozen US regimes "
                      "identical everywhere",
        })
    return {"max_within_regime_dev": max_regime_dev,
            "max_us_regime_gap": max_us_regime_gap}


# ---------------------------------------------------------------------------
# Scoring: the production accounting, with an optional velocity re-map.
# ---------------------------------------------------------------------------
def score_leg(df0: pd.DataFrame, soma_rolloff: pd.Series, cohorts: list,
              surface: dict, velocity_map=None) -> tuple:
    """Run compute_metrics through the production path.

    velocity_map: None -> raw realized Rate_6M_Change (production trilinear);
    else a function mapping the realized velocity Series to the re-mapped
    Series handed to interp_cpr_surface (Part 1 regime re-mapping).
    """
    original = fed.interp_cpr_surface
    if velocity_map is not None:
        def wrapper(rate_pct, friction, surf, velocity=None):
            remapped = velocity_map(velocity) if velocity is not None else None
            return original(rate_pct, friction, surf, velocity=remapped)
        fed.interp_cpr_surface = wrapper
    try:
        df = fed.compute_metrics(
            df0.copy(),
            surface=surface,
            soma_rolloff=soma_rolloff,
            cohorts=cohorts,
            use_burnout=False,
            apply_settlement_lag_kernel=True,
        )
    finally:
        fed.interp_cpr_surface = original
    m = fed.export_headline_metrics(df)
    d = m["dollars_b"]
    leg = {
        "trapped_b": d["us_trapped"],
        "share_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "danish_trapped_b": d["danish_trapped"],
        "institutional_gap_b": d["institutional_gap"],
        "us_cpr_mean_pct": m["cpr_pct"]["us_abm"]["mean"],
    }
    return df, leg


def regime_month_counts(df: pd.DataFrame, trigger: float,
                        threshold: float) -> dict:
    """QT-window months by freeze regime under a strict-> trigger, plus the
    committed surface's partial-interpolation cell (threshold, FROZEN_NODE)."""
    qt = fed.qt_active_frame(df)
    v = qt["Rate_6M_Change"]
    return {
        "frozen": int((v > trigger).sum()),
        "unfrozen": int((v <= trigger).sum()),
        "partial_interp_cell": int(
            ((v > threshold) & (v < FROZEN_NODE)).sum()
        ),
        "n_months": int(len(v)),
    }


# ---------------------------------------------------------------------------
# Part 2: calibration + rebuild under a share override
# ---------------------------------------------------------------------------
def calibrate_and_floor(income: float, home_value: float,
                        ref_coupon: float, ref_months: int) -> tuple:
    """Production calibration + explicit zero-velocity floor readback."""
    scale = abm.calibrate_mobility_scale(
        income, home_value,
        cohort_rate=ref_coupon, cohort_months=ref_months,
    )
    engine = abm.HousingMarketEngine(
        median_income=income, median_home_value=home_value,
        mobility_scale=scale,
    )
    engine.attach_cohort(ref_coupon, ref_months)
    floor_cpr = engine.cpr_at(FLOOR_RATE, "US")   # rate_velocity defaults 0.0
    return scale, floor_cpr


def build_share_surface(share: float, scale: float, income: float,
                        home_value: float, cohorts: list) -> pd.DataFrame:
    """One multi-cohort surface build under WAIT_AND_SEE_PROB = share.

    Mirrors abm_lockin_simulation.main(): one engine (production seed), one
    build_multi_cohort_surfaces sweep.  Caller manages the constant override.
    """
    assert abs(abm.WAIT_AND_SEE_PROB - share) < 1e-15
    engine = abm.HousingMarketEngine(
        median_income=income, median_home_value=home_value,
        mobility_scale=scale,
    )
    return abm.build_multi_cohort_surfaces(engine, cohorts)


def main() -> None:
    # -- committed references ------------------------------------------------
    latest = json.loads(LATEST_RUN_MANIFEST.read_text())
    manifest = json.loads(
        (RUNS_DIR / REFERENCE_RUN_TAG / "manifest.json").read_text())
    ext = json.loads(EXTERNAL_GATES_JSON.read_text())
    ref_d = manifest["metrics"]["dollars_b"]
    ref_cpr_mean = manifest["metrics"]["cpr_pct"]["us_abm"]["mean"]
    pipe = manifest["pipeline"]
    lr_share = ext["external_parameters"]["wait_and_see_prob"]
    prod_share = abm.WAIT_AND_SEE_PROB
    prod_trigger = abm.WAIT_AND_SEE_RATE_THRESHOLD

    # -- G0: committed-state identity ---------------------------------------
    check("G0a_latest_tag", latest.get("run_tag") == REFERENCE_RUN_TAG,
          {"latest_run_tag": latest.get("run_tag"),
           "expected": REFERENCE_RUN_TAG},
          f"latest_run_manifest tag == {REFERENCE_RUN_TAG!r}")

    sha = _sha256(ABM_CPR_SURFACE_CSV)
    check("G0b_surface_sha",
          sha == manifest["inputs"]["abm_cpr_surface_sha256"],
          {"sha256": sha,
           "expected": manifest["inputs"]["abm_cpr_surface_sha256"]},
          "committed surface sha256 matches frozen manifest")

    grid = np.asarray(abm.RATE_VELOCITY_GRID)
    g0c_ok = (
        abs(prod_trigger - 0.015) < 1e-15
        and abs(prod_share - 0.20) < 1e-15
        and any(np.isclose(grid, UNFROZEN_NODE))
        and any(np.isclose(grid, prod_trigger))
        and any(np.isclose(grid, FROZEN_NODE))
    )
    check("G0c_constants", g0c_ok,
          {"threshold": prod_trigger, "share": prod_share,
           "velocity_grid": grid.tolist()},
          "production freeze constants (150bp / 20%) and velocity nodes")

    lr_expected = 1.0 - (1.0 - 0.065) ** (1.5 * 2)
    check("G0d_lr_share", abs(lr_share - lr_expected) < 1e-12,
          {"stored": lr_share, "derivation_1m1m065_pow3": lr_expected},
          f"committed L&R-implied share {lr_share:.10f} == 1-(1-0.065)^3")

    # -- G1: two-regime structure of the committed surface -------------------
    surf_df = pd.read_csv(ABM_CPR_SURFACE_CSV)
    g1 = two_regime_check(surf_df, prod_trigger)
    print(f"G1_two_regime: {surf_df.groupby(['Cohort_Coupon', 'Cohort_Term']).ngroups} "
          f"cohorts x 10 velocity slices collapse to 2 regimes "
          f"(max within-regime dev {g1['max_within_regime_dev']:.2e}; "
          f"max US regime gap {g1['max_us_regime_gap']:.4f}) PASS")
    committed_keys = surface_keyset(surf_df)

    # -- live frames (same fetches as the frozen production pipeline) --------
    print("\nFetching macro/SOMA frames (production fetch path) …")
    df0 = fed.fetch_data()
    soma_rolloff = fed.fetch_soma_mbs_monthly()
    cohorts = fed.fetch_soma_mbs_cohorts()
    ref = abm.reference_cohort(cohorts)

    live_keys = {(fed._round_coupon(c["coupon"]), int(c["term_months"]))
                 for c in cohorts}
    man_ref = pipe["reference_cohort"]
    g2a_ok = (
        soma_rolloff is not None
        and live_keys == committed_keys
        and abs(fed._round_coupon(ref["coupon"]) - man_ref["coupon"]) < 1e-12
        and int(ref["months_elapsed"]) == int(man_ref["months_elapsed"])
    )
    check("G2a_cohort_identity", g2a_ok,
          {"live_keys": sorted(map(list, live_keys)),
           "committed_keys": sorted(map(list, committed_keys)),
           "live_ref": [ref["coupon"], ref["months_elapsed"]],
           "manifest_ref": [man_ref["coupon"], man_ref["months_elapsed"]],
           "soma_rolloff": soma_rolloff is not None},
          f"live SOMA cohort keyset == committed surface keyset "
          f"({len(committed_keys)} cohorts); reference cohort matches manifest")

    # -- G2b: production-leg parity ------------------------------------------
    surface = fed.load_cpr_surface(ABM_CPR_SURFACE_CSV)
    df_prod, prod = score_leg(df0, soma_rolloff, cohorts, surface,
                              velocity_map=None)
    diffs = {
        "us_trapped_b": prod["trapped_b"] - ref_d["us_trapped"],
        "share_pp": prod["share_pct"] - ref_d["share_explained_pct"],
        "empirical_b": prod["empirical_trapped_b"] - ref_d["empirical_trapped"],
        "danish_b": prod["danish_trapped_b"] - ref_d["danish_trapped"],
        "us_cpr_mean_pp": prod["us_cpr_mean_pct"] - ref_cpr_mean,
    }
    g2b_ok = (
        abs(diffs["us_trapped_b"]) <= G2_TOL_TRAPPED_B
        and abs(diffs["share_pp"]) <= G2_TOL_SHARE_PP
        and abs(diffs["empirical_b"]) <= G2_TOL_TRAPPED_B
        and abs(diffs["danish_b"]) <= G2_TOL_TRAPPED_B
        and abs(diffs["us_cpr_mean_pp"]) <= G2_TOL_CPR_MEAN_PP
    )
    check("G2b_production_parity", g2b_ok,
          {"replayed": prod, "committed": ref_d,
           "committed_us_cpr_mean": ref_cpr_mean, "diffs": diffs},
          f"production leg ${prod['trapped_b']:.3f}B / "
          f"{prod['share_pct']:.4f}% vs frozen "
          f"${ref_d['us_trapped']:.3f}B / "
          f"{ref_d['share_explained_pct']:.4f}% "
          f"(dTrapped {diffs['us_trapped_b']:+.4f}B, "
          f"dShare {diffs['share_pp']:+.5f}pp)")

    # =======================================================================
    # PART 1 — freeze-off ablation + trigger sweep (no surface rebuild)
    # =======================================================================
    print("\n" + "=" * 68)
    print(" PART 1 — freeze ablation / trigger sweep on the committed surface")
    print("=" * 68)

    prod_counts = regime_month_counts(df_prod, prod_trigger, prod_trigger)
    prod["month_counts"] = prod_counts
    print(f" production leg: {prod_counts['frozen']} frozen / "
          f"{prod_counts['unfrozen']} unfrozen QT months "
          f"({prod_counts['partial_interp_cell']} in the partial-interp cell)")

    part1 = {"production": prod}

    def binary_map(trigger):
        def _map(vel):
            return pd.Series(
                np.where(vel.to_numpy(dtype=float) > trigger,
                         FROZEN_NODE, UNFROZEN_NODE),
                index=vel.index,
            )
        return _map

    def zero_map(vel):
        return pd.Series(UNFROZEN_NODE, index=vel.index)

    legs = [("freeze_off", zero_map, None)]
    legs += [(f"trigger_{int(round(t * 10000))}bp", binary_map(t), t)
             for t in TRIGGER_GRID]

    for name, vmap, trig in legs:
        df_leg, leg = score_leg(df0, soma_rolloff, cohorts, surface,
                                velocity_map=vmap)
        leg["month_counts"] = regime_month_counts(
            df_leg, trig if trig is not None else np.inf, prod_trigger)
        part1[name] = leg
        print(f" {name:<22s} trapped ${leg['trapped_b']:8.3f}B  "
              f"share {leg['share_pct']:7.4f}%  "
              f"CPR mean {leg['us_cpr_mean_pct']:.3f}%  "
              f"frozen months {leg['month_counts']['frozen']}")

    off = part1["freeze_off"]
    freeze_contribution = {
        "trapped_b": prod["trapped_b"] - off["trapped_b"],
        "share_pp": prod["share_pct"] - off["share_pct"],
        "us_cpr_mean_pp": prod["us_cpr_mean_pct"] - off["us_cpr_mean_pct"],
        "danish_trapped_b": prod["danish_trapped_b"] - off["danish_trapped_b"],
        "basis": f"production leg minus freeze_off, {REFERENCE_RUN_TAG} "
                 f"accounting",
    }
    print(f"\n Freeze isolated contribution (production - freeze_off): "
          f"{freeze_contribution['trapped_b']:+.3f}B trapped, "
          f"{freeze_contribution['share_pp']:+.4f}pp of benchmark, "
          f"{freeze_contribution['us_cpr_mean_pp']:+.3f}pp mean CPR")

    # =======================================================================
    # PART 2 — share sweep with the floor anchor retained
    # =======================================================================
    print("\n" + "=" * 68)
    print(" PART 2 — freeze-share sweep, floor anchor retained")
    print("=" * 68)

    # Calibration inputs pinned to the frozen manifest (reproducibility; the
    # live medians are recorded for provenance but NOT used).
    income = float(pipe["median_income"])
    home_value = float(pipe["median_home_value"])
    ref_coupon = float(man_ref["coupon"])
    ref_months = int(man_ref["months_elapsed"])
    try:
        live_income, live_home = abm.fetch_macro_from_fred()
    except Exception:
        live_income = live_home = None

    # G3: production calibration parity.
    scale_prod, floor_prod = calibrate_and_floor(
        income, home_value, ref_coupon, ref_months)
    check("G3_calibration_parity",
          abs(scale_prod - pipe["mobility_scale"]) <= G3_TOL_SCALE,
          {"calibrated": scale_prod, "committed": pipe["mobility_scale"],
           "pinned_inputs": {"income": income, "home_value": home_value,
                             "ref_coupon": ref_coupon,
                             "ref_months": ref_months}},
          f"calibrated scale {scale_prod:,.4f} == committed "
          f"{pipe['mobility_scale']:,.4f}")

    # G4: rebuild the production-share surface and compare to committed CSV.
    print("\nRebuilding production-share (20%) multi-cohort surface for "
          "parity …")
    rebuilt = build_share_surface(prod_share, scale_prod, income,
                                  home_value, cohorts)
    key_cols = ["Cohort_Coupon", "Cohort_Term", "Friction",
                "Rate_Velocity", "Market_Rate"]
    a = rebuilt.sort_values(key_cols).reset_index(drop=True)
    b = surf_df.sort_values(key_cols).reset_index(drop=True)
    g4_detail = {"rows_rebuilt": len(a), "rows_committed": len(b)}
    if len(a) == len(b) and np.allclose(a[key_cols].to_numpy(),
                                        b[key_cols].to_numpy(),
                                        rtol=0, atol=1e-12):
        g4_detail["max_abs_dev_us"] = float(
            np.max(np.abs(a.CPR_US.to_numpy() - b.CPR_US.to_numpy())))
        g4_detail["max_abs_dev_danish"] = float(
            np.max(np.abs(a.CPR_Danish.to_numpy() - b.CPR_Danish.to_numpy())))
        g4_ok = (g4_detail["max_abs_dev_us"] <= G4_TOL_SURFACE
                 and g4_detail["max_abs_dev_danish"] <= G4_TOL_SURFACE)
    else:
        g4_detail["grid_mismatch"] = True
        g4_ok = False
    check("G4_surface_rebuild_parity", g4_ok, g4_detail,
          f"rebuilt 20% surface == committed CSV "
          f"(max US dev {g4_detail.get('max_abs_dev_us', float('nan')):.2e})")

    # G5: rescore identity ties Part 2 scoring to the Part 1 production leg.
    _, rescored = score_leg(df0, soma_rolloff, cohorts,
                            surface_df_to_dict(rebuilt), velocity_map=None)
    check("G5_rescore_identity",
          abs(rescored["trapped_b"] - prod["trapped_b"]) <= G5_TOL_TRAPPED_B,
          {"rescored": rescored, "production_leg": prod},
          f"rebuilt-surface score ${rescored['trapped_b']:.6f}B == "
          f"production leg ${prod['trapped_b']:.6f}B")

    # Share legs: calibrate (G6), build, score.
    part2 = {
        "production_share": {
            "share": prod_share,
            "mobility_scale": scale_prod,
            "floor_cpr_at_8pct": floor_prod,
            "leg": rescored,
            "note": "rebuilt-surface rescoring; equals Part 1 production "
                    "leg per G5",
        },
    }
    g6 = {}
    for share in (SHARE_LOW, lr_share, SHARE_HIGH):
        label = f"share_{share:.6f}"
        print(f"\n[{label}] overriding WAIT_AND_SEE_PROB -> {share:.6f}")
        abm.WAIT_AND_SEE_PROB = share
        try:
            scale_s, floor_s = calibrate_and_floor(
                income, home_value, ref_coupon, ref_months)
            g6[label] = {
                "scale": scale_s, "scale_prod": scale_prod,
                "floor_cpr": floor_s, "floor_cpr_prod": floor_prod,
            }
            check(f"G6_floor_invariance[{label}]",
                  abs(scale_s - scale_prod) <= G6_TOL_SCALE
                  and abs(floor_s - floor_prod) <= G6_TOL_FLOOR,
                  g6[label],
                  f"scale {scale_s:,.4f} and floor CPR {floor_s:.4%} "
                  f"invariant to the freeze share")
            surf_s = build_share_surface(share, scale_s, income,
                                         home_value, cohorts)
        finally:
            abm.WAIT_AND_SEE_PROB = prod_share
        _, leg = score_leg(df0, soma_rolloff, cohorts,
                           surface_df_to_dict(surf_s), velocity_map=None)
        part2[label] = {
            "share": share,
            "mobility_scale": scale_s,
            "floor_cpr_at_8pct": floor_s,
            "leg": leg,
        }
        print(f" {label:<18s} trapped ${leg['trapped_b']:8.3f}B  "
              f"share {leg['share_pct']:7.4f}%  "
              f"CPR mean {leg['us_cpr_mean_pct']:.3f}%")

    # -- artifact ------------------------------------------------------------
    payload = {
        "mode": "freeze_sensitivity",
        "spec": ("round-17 R17-C (referee T3/Q4); freeze-off ablation + "
                 "trigger sweep on the committed surface (Part 1) and "
                 "freeze-share sweep with the floor anchor retained "
                 "(Part 2); gate #39"),
        "reference_run": {
            "tag": REFERENCE_RUN_TAG,
            "manifest": str((RUNS_DIR / REFERENCE_RUN_TAG / "manifest.json")
                            .relative_to(ABM_DIR.parent)),
            "surface_sha256": sha,
            "committed_dollars_b": ref_d,
            "committed_us_cpr_mean_pct": ref_cpr_mean,
            "scope_note": ("parity anchors to the latest frozen production "
                           "accounting; the fold-in paper-headline tag "
                           "run-2026-07-04-15yr-foldin is not reproducible "
                           "at HEAD (different surface sha)"),
        },
        "committed_parameters": {
            "wait_and_see_rate_threshold": prod_trigger,
            "wait_and_see_prob": prod_share,
            "lr_implied_share": lr_share,
            "lr_source": ("abm/data/abm_external_gates_results.json "
                          "external_parameters.wait_and_see_prob; "
                          "1-(1-0.065)^(1.5x2), run aa65eee, "
                          "TECHNICAL.md sec 25.3"),
        },
        "gates": {
            "G0a_latest_tag": {"pass": True, "tag": REFERENCE_RUN_TAG},
            "G0b_surface_sha": {"pass": True, "sha256": sha},
            "G0c_constants": {"pass": True},
            "G0d_lr_share": {"pass": True, "stored": lr_share},
            "G1_two_regime": {"pass": True, **g1},
            "G2a_cohort_identity": {"pass": True,
                                    "n_cohorts": len(committed_keys)},
            "G2b_production_parity": {"pass": True, "diffs": diffs,
                                      "tolerances": {
                                          "trapped_b": G2_TOL_TRAPPED_B,
                                          "share_pp": G2_TOL_SHARE_PP,
                                          "cpr_mean_pp": G2_TOL_CPR_MEAN_PP}},
            "G3_calibration_parity": {"pass": True, "scale": scale_prod,
                                      "committed": pipe["mobility_scale"]},
            "G4_surface_rebuild_parity": {"pass": True, **g4_detail},
            "G5_rescore_identity": {
                "pass": True,
                "abs_diff_b": abs(rescored["trapped_b"] - prod["trapped_b"])},
            "G6_floor_invariance": {"pass": True, **g6},
        },
        "part1": {
            "method": ("velocity-coordinate re-mapping on the committed "
                       "surface through the production compute_metrics "
                       "accounting; realized (rate, friction, velocity) "
                       "stream from the production fetch path; binary legs "
                       "map v > trigger to the 0.020 frozen node, else 0.0"),
            "legs": part1,
            "freeze_contribution": freeze_contribution,
        },
        "part2": {
            "method": ("external-gates harness pattern: override "
                       "WAIT_AND_SEE_PROB, production calibration re-run "
                       "per share (floor anchor retained), one multi-cohort "
                       "surface build per share, scored through the Part 1 "
                       "production path; calibration inputs pinned to the "
                       "frozen manifest"),
            "pinned_inputs": {"median_income": income,
                              "median_home_value": home_value,
                              "reference_cohort": [ref_coupon, ref_months]},
            "live_medians_recorded_not_used": [live_income, live_home],
            "legs": part2,
        },
        "interpretation_precommitted": (
            "Descriptive accounting only: the freeze contribution and the "
            "trigger/share recovery numbers are reported as contributions "
            "in the run-2026-07-05-berger production accounting. The G6 "
            "invariance gate — the calibrated mobility scale and the "
            "zero-velocity floor CPR at 8% market are unchanged across "
            "freeze shares because cpr_at(0.08,'US') evaluates at "
            "rate_velocity=0.0 where the freeze gate never binds — is the "
            "answer to Q4's 'without compromising the involuntary-turnover "
            "floor'. No verdict vocabulary."
        ),
        "cohort_weights_pct": {
            f"{c['term_months'] // 12}yr_{c['coupon'] * 100:.2f}":
                c["weight"] * 100 for c in cohorts},
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float)
                            + "\n")
    print(f"\nResults saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
