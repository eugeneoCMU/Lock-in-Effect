#!/usr/bin/env python3
"""
Round-18 R18-C: front-end DTI threshold sensitivity (referee W2 / Q6 / C3).

SPEC (committed before execution; gates and interpretation fixed ex ante)
-------------------------------------------------------------------------
Reviewer item R18-C (W2 + Q6 + C3, paper/v16/revision_roadmap_round18.md;
liveness gate #49).  The ABM's front-end DTI gate is DTI_MAX = 0.43, anchored
to the pre-2021 General QM limit (12 C.F.R. sec 1026.43(e)(2)(vi)) and
conceded in the manuscript (sec:method-frictions L144) as "a behavioral anchor
rather than a live regulatory constraint".  Round 17's `freeze_sensitivity`
supplied the freeze half of Q6; VIII.A (L805/L807) still lists "threshold
sensitivity for the ABM's front-end DTI gate" among the OPEN items.  This run
supplies it: the trapped-liquidity accounting under a front-end DTI wall of
36% / 43% / 50%, in the production run-2026-07-05-berger units, with the
involuntary-turnover floor RETAINED at every threshold.

SCOPE.  The ABM is NOT the headline estimator (sec:abm, tex L175): the +9.2pp
lock-in marginal is a hazard-framework object that contains no DTI gate.  This
is a bounding exhibit for a demoted institutional-counterfactual model, in the
same register as `freeze_sensitivity`.  No verdict vocabulary beyond reporting
the trapped range across the DTI wall and the floor-retention check.

SWEPT VALUES (front-end DTI ceiling, decimal; mortgage payment / gross income):
    0.36  — tighter than QM (a stress toward a conservative underwriting wall);
    0.43  — production value = the G1 parity anchor;
    0.50  — looser than QM (a stress toward a permissive wall).

STRUCTURAL FACT (stated ex ante, and the reason this run's floor gate DIFFERS
from freeze_sensitivity's G6).  In `freeze_sensitivity`, the swept parameter
(the wait-and-see freeze) binds ONLY when rate_velocity > 0.015, whereas the
floor anchor is computed by calibrate_mobility_scale via cpr_at(0.08,"US")
whose rate_velocity DEFAULTS TO 0.0 — so the freeze can never touch the floor,
and G6 there asserts the calibrated scale and floor CPR are LITERALLY
INVARIANT.  The DTI gate is different: `passes_dti = dti <= DTI_MAX` in
HousingMarketEngine._movers_mask binds at EVERY rate/friction/velocity grid
point, INCLUDING the zero-velocity 8% floor anchor.  The DTI wall therefore
DOES move the floor if the mobility scale is held fixed (measured at HEAD
before this run: at the production scale 43882.8125 the 8% US floor reads
4.42% / 4.83% / 5.09% at DTI 36 / 43 / 50).  "Floor retained" here means the
production discipline is reapplied: calibrate_mobility_scale is re-run under
each DTI ceiling, re-anchoring the 8% floor into its empirical [4%, 5%]
involuntary-turnover band, with the mobility scale as the free parameter that
absorbs the DTI change (this is exactly what a production re-run under a
different DTI wall would do).  Consequently the trapped-liquidity difference
across DTI is the production-consistent sensitivity — the DTI wall's effect on
the rate-sensitive portion of mobility AFTER the floor has been re-disciplined
— not a mechanical rescaling of the involuntary floor.  Corollary (stated ex
ante, exploited to bound the run): the Danish leg uses the imported
Berger-recalibrated flat elasticity (get_danish_moving_anchor()=="dk_level"),
which never consults the DTI gate, so danish_trapped is DTI-invariant by
construction (mirrors its invariance across every freeze_sensitivity leg).

METHOD (freeze_sensitivity Part-2 pattern; one multi-cohort surface rebuild
per DTI value; no committed artifact is modified).
  Per DTI ceiling d:
    1. override the module constant abm.DTI_MAX = d (restored in finally);
    2. calibrate_mobility_scale(income, home_value, ref_coupon, ref_months)
       exactly as production does — pinned manifest medians, reference-cohort
       anchor (floor RETAINED: the binary search re-targets cpr_at(0.08,"US")
       into [0.04, 0.05]);
    3. one build_multi_cohort_surfaces sweep (11 cohorts x 3,380 grid points),
       with the DTI ceiling baked into every grid point;
    4. restore abm.DTI_MAX;
    5. score through the production accounting — fed.compute_metrics(surface=
       rebuilt multi-cohort dict, soma_rolloff=SOMA monthly, cohorts=live SOMA
       cohorts, use_burnout=False, apply_settlement_lag_kernel=True) ->
       export_headline_metrics, the same build_production_metrics path that
       froze run-2026-07-05-berger, with raw realized velocities (no re-map).
  The DTI ceiling enters only calibration and surface construction; the scoring
  step interpolates the prebuilt surface and never consults DTI_MAX, so baking
  the DTI into the surface fully propagates it.
  Determinism: RNG_SEED = 42, N_HOUSEHOLDS = 10,000 throughout (production
  seed class); calibration inputs pinned to the frozen manifest.

PARITY / FLOOR GATES (all HALT with a GATE_FAILURE artifact before any other
DTI leg is interpreted; no hardcoded expected results except parity to
committed values, each read from its committed file at runtime):
  G0 committed-state identity:
     a. abm/data/latest_run_manifest.json run_tag == "run-2026-07-05-berger";
     b. sha256(abm/abm_cpr_surface.csv) == the frozen manifest's
        inputs.abm_cpr_surface_sha256;
     c. abm.DTI_MAX == 0.43 (the swept gate at production); the held-fixed
        freeze gate abm.WAIT_AND_SEE_PROB == 0.20 and
        abm.WAIT_AND_SEE_RATE_THRESHOLD == 0.015; RNG_SEED == 42,
        N_HOUSEHOLDS == 10000;
     d. live SOMA cohort keyset == committed surface keyset (11 cohorts);
        reference cohort == manifest reference (coupon 0.02, 60mo);
        SOMA monthly rolloff available.
  G1 DTI=43% parity anchor (production reproduction; ALL three sub-checks must
     pass before the 36% and 50% legs are built or interpreted):
     a. calibration parity: re-run under DTI = 0.43 reproduces the manifest
        mobility_scale 43882.8125 (tol 1e-6) and a floor CPR in [0.04, 0.05];
     b. surface-rebuild parity: the rebuilt 43% multi-cohort surface equals the
        committed abm_cpr_surface.csv on the identical grid (max |delta CPR| <=
        1e-12, both CPR_US and CPR_Danish);
     c. score parity vs the frozen manifest metrics (run-2026-07-05-berger):
        us_trapped 84.50667328 B (tol +-0.5 B), share_explained 11.0502604 %
        (tol +-0.10 pp), empirical_trapped 764.7482532 B (tol +-0.5 B),
        danish_trapped 812.9212963 B (tol +-0.5 B), us_cpr_mean 11.7609043 %
        (tol +-0.05 pp).  Tolerances absorb only upstream data-revision noise
        in the live FRED/SOMA refetch (the scoring arithmetic is
        deterministic); the HEAD-rescored trapped is expected near $84.531B,
        the freeze_sensitivity production-leg value.
  G6 floor retention (the Q6/W2 DTI analogue of freeze_sensitivity's G6), per
     DTI d in {0.36, 0.43, 0.50}: the re-calibrated floor CPR at 8% market lies
     in the empirical involuntary-turnover band [0.04, 0.05] — i.e. the floor
     is RETAINED under every DTI wall.  Reported alongside (not gated, because
     it is the mechanism being demonstrated): the fixed-scale floor CPR at 8%
     (production scale 43882.8125 held) showing the drift the re-calibration
     corrects, and the re-calibrated mobility scale that absorbs it.

PRE-COMMITTED INTERPRETATION (fixed before results).  All per-DTI trapped /
share / CPR figures are reported as descriptive accounting in the
run-2026-07-05-berger production units.  The isolated DTI contribution is
production(43%) minus the loosened(50%) and tightened(36%) legs, reported as a
signed contribution exactly as freeze_sensitivity reports production minus
freeze_off.  Verdict language, either outcome:
  * If the trapped figure moves materially across the 36/43/50 wall, report the
    span as the front-end-DTI sensitivity bound on the ABM trapped estimate,
    noting the ABM is a demoted counterfactual and the +9.2pp hazard marginal
    carries no DTI gate.
  * If the trapped figure is near-invariant across the wall, report that the
    floor-calibration discipline (re-anchoring the involuntary floor to
    [4,5]%) absorbs the DTI change, so the ABM trapped estimate is insensitive
    to the front-end DTI ceiling over 36-50%.
Either way the G6 retention check — the floor is re-anchored into its
empirical band at every threshold — is the direct answer to Q6's request for a
sensitivity "without compromising the involuntary-turnover floor".

Output:  abm/data/dti_threshold_sweep_results.json (headline statistics only)
Run:     cd abm && python3 dti_threshold_sweep.py
Runtime: three multi-cohort surface builds (11 cohorts x 3,380 grid points
         each) + three calibrations + four compute_metrics scorings on the
         live FRED/SOMA frames — roughly 10-30 minutes end-to-end (build is
         minutes-scale, per freeze_sensitivity).
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

RESULTS_JSON = ABM_DIR / "data" / "dti_threshold_sweep_results.json"

REFERENCE_RUN_TAG = "run-2026-07-05-berger"

# Swept front-end DTI ceilings (decimal). Production value 0.43 is the anchor.
PROD_DTI = 0.43
DTI_SWEEP = (0.36, 0.43, 0.50)

FLOOR_RATE = 0.08          # calibration anchor market rate (production value)
FLOOR_BAND = (0.04, 0.05)  # empirical involuntary-turnover floor band

# Gate tolerances (see header).
G1A_TOL_SCALE = 1e-6
G1B_TOL_SURFACE = 1e-12
G1C_TOL_TRAPPED_B = 0.5
G1C_TOL_SHARE_PP = 0.10
G1C_TOL_CPR_MEAN_PP = 0.05


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
# Surface helpers (identical to freeze_sensitivity)
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


# ---------------------------------------------------------------------------
# Scoring: the production accounting on a prebuilt surface (raw velocities).
# ---------------------------------------------------------------------------
def score_leg(df0: pd.DataFrame, soma_rolloff: pd.Series, cohorts: list,
              surface: dict) -> dict:
    df = fed.compute_metrics(
        df0.copy(),
        surface=surface,
        soma_rolloff=soma_rolloff,
        cohorts=cohorts,
        use_burnout=False,
        apply_settlement_lag_kernel=True,
    )
    m = fed.export_headline_metrics(df)
    d = m["dollars_b"]
    return {
        "trapped_b": d["us_trapped"],
        "share_pct": d["share_explained_pct"],
        "empirical_trapped_b": d["empirical_trapped"],
        "danish_trapped_b": d["danish_trapped"],
        "institutional_gap_b": d["institutional_gap"],
        "us_cpr_mean_pct": m["cpr_pct"]["us_abm"]["mean"],
    }


# ---------------------------------------------------------------------------
# Calibration + surface build under a DTI override
# ---------------------------------------------------------------------------
def floor_cpr_at(scale: float, income: float, home_value: float,
                 ref_coupon: float, ref_months: int) -> float:
    """Zero-velocity 8% US floor CPR at a given mobility scale (DTI as set)."""
    engine = abm.HousingMarketEngine(
        median_income=income, median_home_value=home_value,
        mobility_scale=scale,
    )
    engine.attach_cohort(ref_coupon, ref_months)
    return engine.cpr_at(FLOOR_RATE, "US")   # rate_velocity defaults to 0.0


def calibrate_and_floor(income: float, home_value: float,
                        ref_coupon: float, ref_months: int) -> tuple:
    """Production calibration (floor retained) + explicit floor readback.

    DTI_MAX must already be overridden by the caller. The binary search
    re-targets cpr_at(0.08,'US') into [0.04, 0.05], so the calibrated scale is
    the free parameter that absorbs the DTI change; the returned floor is the
    retained floor.
    """
    scale = abm.calibrate_mobility_scale(
        income, home_value,
        cohort_rate=ref_coupon, cohort_months=ref_months,
    )
    floor = floor_cpr_at(scale, income, home_value, ref_coupon, ref_months)
    return scale, floor


def build_dti_surface(dti: float, scale: float, income: float,
                      home_value: float, cohorts: list) -> pd.DataFrame:
    """One multi-cohort surface build under DTI_MAX = dti (caller-overridden)."""
    assert abs(abm.DTI_MAX - dti) < 1e-15
    engine = abm.HousingMarketEngine(
        median_income=income, median_home_value=home_value,
        mobility_scale=scale,
    )
    return abm.build_multi_cohort_surfaces(engine, cohorts)


def dti_leg(dti: float, income: float, home_value: float, ref_coupon: float,
            ref_months: int, prod_scale: float, df0: pd.DataFrame,
            soma_rolloff: pd.Series, cohorts: list) -> tuple:
    """Calibrate (floor retained), build, score one DTI ceiling.

    Returns (leg_dict, floor_diag_dict, rebuilt_surface_df).
    """
    old = abm.DTI_MAX
    abm.DTI_MAX = dti
    try:
        scale, floor = calibrate_and_floor(income, home_value,
                                           ref_coupon, ref_months)
        fixed_scale_floor = floor_cpr_at(prod_scale, income, home_value,
                                         ref_coupon, ref_months)
        surf = build_dti_surface(dti, scale, income, home_value, cohorts)
    finally:
        abm.DTI_MAX = old
    leg = score_leg(df0, soma_rolloff, cohorts, surface_df_to_dict(surf))
    leg.update({"dti_max": dti, "mobility_scale": scale,
                "floor_cpr_at_8pct": floor})
    floor_diag = {
        "dti_max": dti,
        "recalibrated_scale": scale,
        "recalibrated_floor_cpr": floor,
        "fixed_scale_floor_cpr": fixed_scale_floor,
        "in_band": FLOOR_BAND[0] <= floor <= FLOOR_BAND[1],
    }
    return leg, floor_diag, surf


def main() -> None:
    # -- committed references ------------------------------------------------
    latest = json.loads(LATEST_RUN_MANIFEST.read_text())
    manifest = json.loads(
        (RUNS_DIR / REFERENCE_RUN_TAG / "manifest.json").read_text())
    ref_d = manifest["metrics"]["dollars_b"]
    ref_cpr_mean = manifest["metrics"]["cpr_pct"]["us_abm"]["mean"]
    pipe = manifest["pipeline"]

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

    g0c_ok = (
        abs(abm.DTI_MAX - PROD_DTI) < 1e-15
        and abs(abm.WAIT_AND_SEE_PROB - 0.20) < 1e-15
        and abs(abm.WAIT_AND_SEE_RATE_THRESHOLD - 0.015) < 1e-15
        and abm.RNG_SEED == 42
        and abm.N_HOUSEHOLDS == 10000
    )
    check("G0c_constants", g0c_ok,
          {"dti_max": abm.DTI_MAX, "wait_and_see_prob": abm.WAIT_AND_SEE_PROB,
           "wait_and_see_threshold": abm.WAIT_AND_SEE_RATE_THRESHOLD,
           "rng_seed": abm.RNG_SEED, "n_households": abm.N_HOUSEHOLDS},
          "production constants (DTI 43%, freeze 20%/150bp, seed 42, N=10000)")

    surf_df = pd.read_csv(ABM_CPR_SURFACE_CSV)
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
    g0d_ok = (
        soma_rolloff is not None
        and live_keys == committed_keys
        and abs(fed._round_coupon(ref["coupon"]) - man_ref["coupon"]) < 1e-12
        and int(ref["months_elapsed"]) == int(man_ref["months_elapsed"])
    )
    check("G0d_cohort_identity", g0d_ok,
          {"live_keys": sorted(map(list, live_keys)),
           "committed_keys": sorted(map(list, committed_keys)),
           "live_ref": [ref["coupon"], ref["months_elapsed"]],
           "manifest_ref": [man_ref["coupon"], man_ref["months_elapsed"]],
           "soma_rolloff": soma_rolloff is not None},
          f"live SOMA cohort keyset == committed surface keyset "
          f"({len(committed_keys)} cohorts); reference cohort matches manifest")

    # Calibration inputs pinned to the frozen manifest (reproducibility).
    income = float(pipe["median_income"])
    home_value = float(pipe["median_home_value"])
    ref_coupon = float(man_ref["coupon"])
    ref_months = int(man_ref["months_elapsed"])
    try:
        live_income, live_home = abm.fetch_macro_from_fred()
    except Exception:
        live_income = live_home = None

    # =======================================================================
    # G1 — DTI = 43% parity anchor (must pass before 36% / 50% are built)
    # =======================================================================
    print("\n" + "=" * 68)
    print(" G1 — DTI = 43% parity anchor (production reproduction)")
    print("=" * 68)

    abm.DTI_MAX = PROD_DTI  # explicit; production value
    scale_prod, floor_prod = calibrate_and_floor(
        income, home_value, ref_coupon, ref_months)
    check("G1a_calibration_parity",
          abs(scale_prod - pipe["mobility_scale"]) <= G1A_TOL_SCALE
          and FLOOR_BAND[0] <= floor_prod <= FLOOR_BAND[1],
          {"calibrated": scale_prod, "committed": pipe["mobility_scale"],
           "floor_cpr": floor_prod, "floor_band": list(FLOOR_BAND),
           "pinned_inputs": {"income": income, "home_value": home_value,
                             "ref_coupon": ref_coupon,
                             "ref_months": ref_months}},
          f"scale {scale_prod:,.4f} == committed {pipe['mobility_scale']:,.4f} "
          f"and floor CPR {floor_prod:.4%} in [4%,5%]")

    print("\nRebuilding DTI=43% multi-cohort surface for parity …")
    abm.DTI_MAX = PROD_DTI
    try:
        rebuilt = build_dti_surface(PROD_DTI, scale_prod, income,
                                    home_value, cohorts)
    finally:
        abm.DTI_MAX = PROD_DTI
    key_cols = ["Cohort_Coupon", "Cohort_Term", "Friction",
                "Rate_Velocity", "Market_Rate"]
    a = rebuilt.sort_values(key_cols).reset_index(drop=True)
    b = surf_df.sort_values(key_cols).reset_index(drop=True)
    g1b_detail = {"rows_rebuilt": len(a), "rows_committed": len(b)}
    if len(a) == len(b) and np.allclose(a[key_cols].to_numpy(),
                                        b[key_cols].to_numpy(),
                                        rtol=0, atol=1e-12):
        g1b_detail["max_abs_dev_us"] = float(
            np.max(np.abs(a.CPR_US.to_numpy() - b.CPR_US.to_numpy())))
        g1b_detail["max_abs_dev_danish"] = float(
            np.max(np.abs(a.CPR_Danish.to_numpy() - b.CPR_Danish.to_numpy())))
        g1b_ok = (g1b_detail["max_abs_dev_us"] <= G1B_TOL_SURFACE
                  and g1b_detail["max_abs_dev_danish"] <= G1B_TOL_SURFACE)
    else:
        g1b_detail["grid_mismatch"] = True
        g1b_ok = False
    check("G1b_surface_rebuild_parity", g1b_ok, g1b_detail,
          f"rebuilt 43% surface == committed CSV "
          f"(max US dev {g1b_detail.get('max_abs_dev_us', float('nan')):.2e})")

    prod = score_leg(df0, soma_rolloff, cohorts, surface_df_to_dict(rebuilt))
    prod.update({"dti_max": PROD_DTI, "mobility_scale": scale_prod,
                 "floor_cpr_at_8pct": floor_prod})
    diffs = {
        "us_trapped_b": prod["trapped_b"] - ref_d["us_trapped"],
        "share_pp": prod["share_pct"] - ref_d["share_explained_pct"],
        "empirical_b": prod["empirical_trapped_b"] - ref_d["empirical_trapped"],
        "danish_b": prod["danish_trapped_b"] - ref_d["danish_trapped"],
        "us_cpr_mean_pp": prod["us_cpr_mean_pct"] - ref_cpr_mean,
    }
    g1c_ok = (
        abs(diffs["us_trapped_b"]) <= G1C_TOL_TRAPPED_B
        and abs(diffs["share_pp"]) <= G1C_TOL_SHARE_PP
        and abs(diffs["empirical_b"]) <= G1C_TOL_TRAPPED_B
        and abs(diffs["danish_b"]) <= G1C_TOL_TRAPPED_B
        and abs(diffs["us_cpr_mean_pp"]) <= G1C_TOL_CPR_MEAN_PP
    )
    check("G1c_score_parity", g1c_ok,
          {"replayed": prod, "committed": ref_d,
           "committed_us_cpr_mean": ref_cpr_mean, "diffs": diffs},
          f"43% leg ${prod['trapped_b']:.4f}B / {prod['share_pct']:.4f}% vs "
          f"frozen ${ref_d['us_trapped']:.4f}B / "
          f"{ref_d['share_explained_pct']:.4f}% "
          f"(dTrapped {diffs['us_trapped_b']:+.4f}B, "
          f"dShare {diffs['share_pp']:+.5f}pp)")

    # =======================================================================
    # DTI sweep — 36% and 50% (only after the 43% anchor passes G1)
    # =======================================================================
    print("\n" + "=" * 68)
    print(" DTI sweep — front-end ceiling 36% / 43% / 50%, floor retained")
    print("=" * 68)

    legs = {}
    floor_diags = {}
    # Reuse the anchor result for 43% (already built + scored + floor read).
    legs["dti_0.43"] = prod
    floor_diags["dti_0.43"] = {
        "dti_max": PROD_DTI,
        "recalibrated_scale": scale_prod,
        "recalibrated_floor_cpr": floor_prod,
        "fixed_scale_floor_cpr": floor_prod,   # production scale == recalib
        "in_band": FLOOR_BAND[0] <= floor_prod <= FLOOR_BAND[1],
    }
    print(f" dti_0.43 (anchor)  trapped ${prod['trapped_b']:8.4f}B  "
          f"share {prod['share_pct']:7.4f}%  CPR mean "
          f"{prod['us_cpr_mean_pct']:.4f}%  scale {scale_prod:,.1f}  "
          f"floor {floor_prod:.4%}")

    for dti in (d for d in DTI_SWEEP if abs(d - PROD_DTI) > 1e-15):
        label = f"dti_{dti:.2f}"
        print(f"\n[{label}] overriding DTI_MAX -> {dti:.2f}; "
              f"re-calibrate (floor retained), rebuild surface, score …")
        leg, fdiag, _ = dti_leg(dti, income, home_value, ref_coupon,
                                ref_months, scale_prod, df0, soma_rolloff,
                                cohorts)
        # G6 floor retention: the re-calibrated floor must land in [4%,5%].
        check(f"G6_floor_retention[{label}]", fdiag["in_band"], fdiag,
              f"re-calibrated floor CPR {fdiag['recalibrated_floor_cpr']:.4%} "
              f"in [4%,5%] (fixed-scale drift "
              f"{fdiag['fixed_scale_floor_cpr']:.4%}, "
              f"scale {fdiag['recalibrated_scale']:,.1f})")
        legs[label] = leg
        floor_diags[label] = fdiag
        print(f" {label}  trapped ${leg['trapped_b']:8.4f}B  "
              f"share {leg['share_pct']:7.4f}%  CPR mean "
              f"{leg['us_cpr_mean_pct']:.4f}%  scale "
              f"{leg['mobility_scale']:,.1f}  floor {leg['floor_cpr_at_8pct']:.4%}")

    # G6 also confirmed for the 43% anchor (floor already checked in band).
    check("G6_floor_retention[dti_0.43]",
          floor_diags["dti_0.43"]["in_band"], floor_diags["dti_0.43"],
          f"re-calibrated floor CPR {floor_prod:.4%} in [4%,5%] (anchor)")

    # -- isolated DTI contributions (production minus loosened / tightened) --
    loose = legs["dti_0.50"]
    tight = legs["dti_0.36"]
    dti_contribution = {
        "production_vs_loosened_50": {
            "trapped_b": prod["trapped_b"] - loose["trapped_b"],
            "share_pp": prod["share_pct"] - loose["share_pct"],
            "us_cpr_mean_pp": prod["us_cpr_mean_pct"] - loose["us_cpr_mean_pct"],
            "basis": "DTI 43% minus 50% (loosened wall), "
                     f"{REFERENCE_RUN_TAG} accounting",
        },
        "production_vs_tightened_36": {
            "trapped_b": prod["trapped_b"] - tight["trapped_b"],
            "share_pp": prod["share_pct"] - tight["share_pct"],
            "us_cpr_mean_pp": prod["us_cpr_mean_pct"] - tight["us_cpr_mean_pct"],
            "basis": "DTI 43% minus 36% (tightened wall), "
                     f"{REFERENCE_RUN_TAG} accounting",
        },
        "full_span_36_to_50": {
            "trapped_b": tight["trapped_b"] - loose["trapped_b"],
            "share_pp": tight["share_pct"] - loose["share_pct"],
            "note": "tightest minus loosest trapped span across the swept wall",
        },
    }
    print("\n Isolated DTI contribution (production accounting):")
    print(f"   43% vs 50% (loosened):  "
          f"{dti_contribution['production_vs_loosened_50']['trapped_b']:+.4f}B "
          f"trapped, "
          f"{dti_contribution['production_vs_loosened_50']['share_pp']:+.4f}pp")
    print(f"   43% vs 36% (tightened): "
          f"{dti_contribution['production_vs_tightened_36']['trapped_b']:+.4f}B "
          f"trapped, "
          f"{dti_contribution['production_vs_tightened_36']['share_pp']:+.4f}pp")
    print(f"   full span 36%->50%:     "
          f"{dti_contribution['full_span_36_to_50']['trapped_b']:+.4f}B trapped")

    # -- artifact ------------------------------------------------------------
    payload = {
        "mode": "dti_threshold_sweep",
        "status": "OK",
        "spec": ("round-18 R18-C (referee W2/Q6/C3); front-end DTI threshold "
                 "sensitivity 36/43/50% on the frozen berger surface, "
                 "freeze_sensitivity Part-2 harness pattern, floor retained; "
                 "gate #49"),
        "reference_run": {
            "tag": REFERENCE_RUN_TAG,
            "manifest": str((RUNS_DIR / REFERENCE_RUN_TAG / "manifest.json")
                            .relative_to(ABM_DIR.parent)),
            "surface_sha256": sha,
            "committed_dollars_b": ref_d,
            "committed_us_cpr_mean_pct": ref_cpr_mean,
            "scope_note": ("parity anchors to the latest frozen production "
                           "accounting; the ABM is a demoted institutional "
                           "counterfactual — the +9.2pp hazard marginal "
                           "carries no DTI gate"),
        },
        "swept_parameter": {
            "name": "front_end_dti_ceiling",
            "production_value": PROD_DTI,
            "swept_values": list(DTI_SWEEP),
            "source": ("abm.DTI_MAX; pre-2021 General QM limit "
                       "12 C.F.R. 1026.43(e)(2)(vi); front-end only "
                       "(mortgage payment / gross income)"),
            "danish_leg_dti_invariant": True,
            "danish_anchor": "dk_level (Berger flat elasticity; no DTI gate)",
        },
        "gates": {
            "G0a_latest_tag": {"pass": True, "tag": REFERENCE_RUN_TAG},
            "G0b_surface_sha": {"pass": True, "sha256": sha},
            "G0c_constants": {"pass": True, "dti_max": PROD_DTI,
                              "wait_and_see_prob": abm.WAIT_AND_SEE_PROB,
                              "rng_seed": abm.RNG_SEED,
                              "n_households": abm.N_HOUSEHOLDS},
            "G0d_cohort_identity": {"pass": True,
                                    "n_cohorts": len(committed_keys)},
            "G1a_calibration_parity": {"pass": True, "scale": scale_prod,
                                       "committed": pipe["mobility_scale"],
                                       "floor_cpr": floor_prod},
            "G1b_surface_rebuild_parity": {"pass": True, **g1b_detail},
            "G1c_score_parity": {"pass": True, "diffs": diffs,
                                 "tolerances": {
                                     "trapped_b": G1C_TOL_TRAPPED_B,
                                     "share_pp": G1C_TOL_SHARE_PP,
                                     "cpr_mean_pp": G1C_TOL_CPR_MEAN_PP}},
            "G6_floor_retention": {"pass": True, "band": list(FLOOR_BAND),
                                   "per_dti": floor_diags},
        },
        "method": ("freeze_sensitivity Part-2 pattern: override abm.DTI_MAX, "
                   "production calibration re-run per DTI (floor retained via "
                   "the [4,5]% binary search; mobility scale absorbs the DTI "
                   "change), one multi-cohort surface build per DTI, scored "
                   "through the production compute_metrics path with raw "
                   "realized velocities; calibration inputs pinned to the "
                   "frozen manifest; seed 42, N=10000"),
        "pinned_inputs": {"median_income": income,
                          "median_home_value": home_value,
                          "reference_cohort": [ref_coupon, ref_months]},
        "live_medians_recorded_not_used": [live_income, live_home],
        "legs": legs,
        "floor_retention": {
            "band": list(FLOOR_BAND),
            "note": ("unlike freeze_sensitivity's G6 (freeze never touches the "
                     "zero-velocity floor, so scale and floor are literally "
                     "invariant), the DTI gate binds at the 8% floor; 'floor "
                     "retained' means the floor is re-anchored into [4,5]% by "
                     "re-calibration, with the mobility scale as the absorbing "
                     "free parameter — the fixed_scale_floor_cpr column shows "
                     "the drift the re-calibration corrects"),
            "per_dti": floor_diags,
        },
        "dti_contribution": dti_contribution,
        "interpretation_precommitted": (
            "Descriptive accounting only, in run-2026-07-05-berger units. "
            "Per-DTI trapped/share/CPR are the production reproduction of the "
            "trapped-liquidity accounting under a 36/43/50% front-end DTI "
            "wall, floor retained. The isolated DTI contribution is "
            "production(43%) minus the loosened(50%) and tightened(36%) legs. "
            "The G6 floor-retention check — the involuntary-turnover floor is "
            "re-anchored into [4,5]% at every threshold — is the answer to "
            "Q6's 'without compromising the involuntary-turnover floor'. The "
            "ABM is not the headline estimator; the +9.2pp hazard marginal "
            "carries no DTI gate. No verdict vocabulary."
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
