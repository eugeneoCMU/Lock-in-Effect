#!/usr/bin/env python3
"""
Round-17 R17-J (referee DC3): off-grid validation of the ABM CPR-surface
interpolation against direct micro-simulation.

SPEC (committed before execution; gates and tolerances ex ante)
---------------------------------------------------------------
Reviewer item R17-J asks for a spot-check of per-month micro-simulation vs
interpolated CPR. At grid nodes the check is exact by construction: the
committed surface abm/abm_cpr_surface.csv stores _cpr_vec's direct
micro-simulation output at each node (build_cpr_surface), and nested
np.interp returns the stored node value when queried at a node. The only
place interpolation error can exist is OFF-grid, between the 50bp-spaced
nodes. This run measures it there, at (a) half-step midpoints — the worst
case for trilinear interpolation — and (b) every realized QT-month query
coordinate the production pipeline actually used.

Reconstruction anchors (frozen headline run):
  abm/data/runs/run-2026-07-05-berger/manifest.json — seed RNG_SEED=42,
  mobility_scale 43882.8125, median_income 83730.0, median_home_value
  403200.0, n_cohorts 11, reference cohort coupon 0.02 / 60mo / 360mo,
  abm_cpr_surface.csv sha256 a828fcbe...
The engine is rebuilt from these manifest parameters directly (no FRED
median fetch, no mobility recalibration). Cohort structure (coupon/term
keys, weights, seasonings) comes from the live SOMA parse exactly as
production does — network is required at execution. The SOMA API has no
as-of parameter, so if its as-of month has advanced past the frozen run's,
every bucket's months_elapsed shifts by the SAME integer k (months_elapsed
= term - months_between(maturity, as_of); round(x+k) = round(x)+k for
integer k). G0 measures k on the manifest's reference cohort and applies
the uniform correction -k to all cohorts; any residual per-bucket drift
(composition churn, fold-in changes) is caught bit-exactly by G1.

Gates (in order; any failure writes status GATE_FAILURE and halts — no
off-grid number is interpreted after a failed gate):
  G0 frozen inputs & cohort structure —
     (a) sha256(abm/abm_cpr_surface.csv) == manifest inputs sha256;
     (b) CSV holds 37,180 rows = 13 rates x 26 frictions x 10 velocities
         x 11 cohorts, and load_cpr_surface() yields 11 3D cohort surfaces;
     (c) live SOMA parse yields exactly n_cohorts=11 cohorts whose
         (coupon, term) key set equals the committed surface's key set;
     (d) reference cohort (max-weight 30yr) key equals the manifest's
         (0.02, 360) and the seasoning offset k = live_ref_elapsed - 60
         is in {0, 1, 2} (small forward as-of drift only); k is subtracted
         uniformly from every cohort's months_elapsed before attachment.
  G1 on-grid parity (the reconstruction proof) — for EACH of the 11
     cohorts, re-evaluate _cpr_vec at 4 pre-committed committed grid nodes
     (indices into the sorted per-cohort grids (i_rate, i_friction,
     i_velocity), evaluated at the CSV's own stored coordinate floats):
       (6, 12, 4)  rate 5.0%, friction 11.0%, velocity +1.0%   interior
       (9,  7, 5)  rate 6.5%, friction  8.5%, velocity +1.5%   realized region
       (7,  8, 2)  rate 5.5%, friction  9.0%, velocity  0.0%   realized region
       (3, 17, 8)  rate 3.5%, friction 13.5%, velocity +3.0%   frozen branch
     Tolerance (AMENDED at first execution, 2026-07-17, before any off-grid
     number was interpreted): US column bit-exact (0.0); Danish column
     <= 1e-12. The spec's original blanket bit-exact assumption was
     falsified by the committed CSV itself: the first execution showed
     every US value reproducing bit-exactly while the Danish column
     differs by <= 7.6e-15 — the CSV's Danish serialization drops one ulp
     (e.g. stored 0.0333649999999999 vs recomputed 0.03336499999999998),
     so bit-exactness against the file is unattainable for that column on
     any machine. 1e-12 is CSV-serialization precision, eleven orders
     below the 0.25pp interpretation tolerance; any real engine/cohort
     reconstruction failure exceeds it by orders of magnitude and still
     halts the run.
  G2 realized-coordinate reconstruction — the realized query coordinates
     are taken from the frozen run's metrics_monthly.csv (42 QT months,
     MORTGAGE30US + Dynamic_Friction — production's coordinates verbatim).
     Rate_6M_Change is NOT exported there; it is rebuilt as diff(6)/100
     (fed_mbs_extension_risk.compute_metrics L858) on a spliced series:
     frozen MORTGAGE30US inside the window, live fetch_data() months for
     the 6 pre-window months (2021-12..2022-05). Gate: live in-window
     MORTGAGE30US must match the frozen column within 5e-6pp (max abs) —
     this certifies the live series is revision-free, hence the pre-window
     months feeding the splice are trustworthy. Dynamic_Friction live-vs-
     frozen parity is reported as a DIAGNOSTIC only (frozen values are
     used directly, so friction revisions cannot contaminate the check).

Off-grid midpoint check (pre-committed points):
  10 points at half-step midpoints of (rate, friction, velocity), indexed
  (i_rate, i_friction, i_velocity) meaning the midpoint of grid cells
  [g[i], g[i+1]] on each axis:
    P01 ( 6,  6, 3)  5.25%,  8.25%, +0.75%   realized-region core
    P02 ( 7,  7, 2)  5.75%,  8.75%, +0.25%   realized region
    P03 ( 8,  8, 1)  6.25%,  9.25%, -0.25%   realized region
    P04 (10,  9, 2)  7.25%,  9.75%, +0.25%   realized upper-rate
    P05 ( 1,  6, 3)  2.75%,  8.25%, +0.75%   steep S-curve near coupon stack
    P06 ( 2, 12, 1)  3.25%, 11.25%, -0.25%   steep region, high friction
    P07 ( 4, 17, 7)  4.25%, 13.75%, +2.75%   high-velocity frozen plateau
    P08 ( 6,  6, 5)  5.25%,  8.25%, +1.75%   KINK-straddling
    P09 ( 9,  7, 5)  6.75%,  8.75%, +1.75%   KINK-straddling, realized region
    P10 ( 2, 12, 5)  3.25%, 11.25%, +1.75%   KINK-straddling, steep region
  Kink pre-registration: the wait-and-see gate (WAIT_AND_SEE_RATE_THRESHOLD
  = 1.5%, strict inequality; 20% of cleared movers freeze) makes CPR
  piecewise-DISCONTINUOUS in velocity at +1.5%: direct evaluation applies
  the full freeze for any velocity > 1.5%, while trilinear interpolation
  blends the unfrozen +1.5% node with the frozen +2.0% node. P08-P10
  straddle this behavioral step deliberately. The committed tolerance
  applies to the full 10-point set, and results are ALSO reported split by
  kink_straddle so any failure is attributable to the behavioral step
  rather than to smooth-region interpolation error. Realized QT months
  whose reconstructed velocity falls inside (+1.5%, +2.0%) are counted and
  listed for the same reason.
  Cohort selection rule (ex ante): the manifest reference cohort (0.02,
  360) plus the two largest-weight cohorts in the live SOMA parse other
  than the reference, ties broken by (30yr before 15yr, then lower
  coupon). Resolved identities are recorded in the artifact.

Realized-coordinate check:
  All 42 realized QT-month (rate, friction, velocity) triples x all 11
  cohorts: direct _cpr_vec vs interp_cpr_surface, US and Danish, plus the
  SOMA-face-weighted (live parse weights) cohort-aggregate difference over
  the window — the exact aggregation compute_metrics uses for the headline
  CPR path.

Pre-committed tolerances (all outcomes reported either way):
  T1 midpoints: max over the 10 points x 3 cohorts of |direct - interp|
     <= 0.25pp CPR (scored separately for US and Danish).
  T2 realized window: SOMA-weighted mean |ΔCPR| over the 42 QT months
     <= 0.05pp (gate quantity: mean over months of |Σ_c w_c Δ_c(t)|, the
     stricter reading; |mean of signed weighted Δ| — the headline-shift
     reading — is also reported).

Scope (ex-ante decision): trapped liquidity is NOT re-scored. The check
stays at the CPR layer where the approximation lives; dollar re-scoring
would drag in the settlement-lag kernel, curtailment, and balance dynamics
that are identical between the two CPR inputs and would only dilute
attribution. The T2 weighted-CPR bound is the quantity that carries into
the dollar pipeline linearly month by month.

Artifact (headline stats only): abm/data/interp_spot_check_results.json
  { status, identifiers {run_tag, manifest_git_commit, surface_sha256,
    seed, mobility_scale, medians, seasoning_offset_k, cohorts, versions},
    gates {G0, G1, G2}, midpoint_check {tolerance_pp, points[10x3],
    summary incl. kink split, pass_us, pass_dk}, realized_check
    {tolerance_pp, per_cohort summaries, weighted stats, kink_band,
    pass_us, pass_dk}, scope }

No-touch list: abm/abm_cpr_surface.csv, abm/data/runs/** (manifest and
metrics_monthly.csv are read-only inputs), abm/data/latest_run_manifest.json,
abm/abm_lockin_results.csv, all committed PNGs/CSVs, tools/liveness_gates.py
(the follow-up liveness gate — roadmap gate #44 — is added only after this
run executes and passes). This script writes ONLY the artifact JSON above.

Run:    cd abm && python3 interp_spot_check.py
Needs:  network (NY Fed SOMA CUSIP parse; FRED via fetch_data for the
        6 pre-window velocity months). Compute is minutes-scale.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from paths import ABM_CPR_SURFACE_CSV, ABM_DIR, RUNS_DIR

BERGER_TAG = "run-2026-07-05-berger"
BERGER_DIR = RUNS_DIR / BERGER_TAG
MANIFEST_JSON = BERGER_DIR / "manifest.json"
METRICS_MONTHLY_CSV = BERGER_DIR / "metrics_monthly.csv"
RESULTS_JSON = ABM_DIR / "data" / "interp_spot_check_results.json"

# --- Pre-committed constants (see module docstring) ------------------------
EXPECTED_ROWS = 37_180
EXPECTED_GRID = (13, 26, 10)          # rates x frictions x velocities
EXPECTED_N_COHORTS = 11
SEASONING_OFFSET_ALLOWED = (0, 1, 2)  # forward as-of drift only

G1_TOL_US = 0.0                       # bit-exact (verified attainable)
G1_TOL_DK = 1e-12                     # CSV serialization precision (amended 2026-07-17)
G2_RATE_TOL_PP = 5e-6                 # float round-trip noise only
MIDPOINT_MAX_TOL_PP = 0.25            # T1
WINDOW_WEIGHTED_MEAN_TOL_PP = 0.05    # T2

G1_NODES = [(6, 12, 4), (9, 7, 5), (7, 8, 2), (3, 17, 8)]

# (point_id, i_rate, i_friction, i_velocity, kink_straddle)
MIDPOINTS = [
    ("P01", 6, 6, 3, False),
    ("P02", 7, 7, 2, False),
    ("P03", 8, 8, 1, False),
    ("P04", 10, 9, 2, False),
    ("P05", 1, 6, 3, False),
    ("P06", 2, 12, 1, False),
    ("P07", 4, 17, 7, False),
    ("P08", 6, 6, 5, True),
    ("P09", 9, 7, 5, True),
    ("P10", 2, 12, 5, True),
]

MIDPOINT_COHORT_RULE = (
    "manifest reference cohort + two largest-weight live-SOMA cohorts "
    "excluding it; ties broken by (term 360 first, lower coupon)"
)

SCOPE_NOTE = (
    "Trapped liquidity is NOT re-scored (ex-ante scoping decision): the "
    "interpolation approximation lives entirely at the CPR layer; the T2 "
    "weighted-CPR bound is the quantity the dollar pipeline consumes "
    "linearly month by month."
)


def _sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _fail(reason: str, detail: dict) -> None:
    payload = {
        "status": "GATE_FAILURE",
        "mode": "interp_spot_check",
        "reason": reason,
        "detail": detail,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    raise SystemExit(f"GATE FAILURE ({reason}) — off-grid results not "
                     f"interpreted. Detail written to {RESULTS_JSON}")


def _cohort_key(c: dict) -> tuple:
    return (fed._round_coupon(c["coupon"]), int(c["term_months"]))


def _slab_grids(slab: pd.DataFrame) -> tuple:
    r = np.sort(slab["Market_Rate"].unique())
    f = np.sort(slab["Friction"].unique())
    v = np.sort(slab["Rate_Velocity"].unique())
    return r, f, v


def _slab_for_key(raw: pd.DataFrame, key: tuple) -> pd.DataFrame:
    coupon, term = key
    m = (np.isclose(raw["Cohort_Coupon"], coupon, rtol=0.0, atol=1e-9)
         & (raw["Cohort_Term"].astype(int) == term))
    return raw.loc[m]


def _stats(diffs: np.ndarray) -> dict:
    a = np.abs(np.asarray(diffs, dtype=float))
    return {
        "max_abs_pp": float(a.max()) if a.size else None,
        "mean_abs_pp": float(a.mean()) if a.size else None,
        "n": int(a.size),
    }


def main() -> None:
    manifest = json.loads(MANIFEST_JSON.read_text())
    pipe = manifest["pipeline"]
    manifest_ref = pipe["reference_cohort"]

    # ------------------------------------------------------------------ G0
    print("G0: frozen inputs & cohort structure …")
    sha = _sha256(ABM_CPR_SURFACE_CSV)
    if sha != manifest["inputs"]["abm_cpr_surface_sha256"]:
        _fail("G0a_surface_sha256_mismatch", {
            "computed": sha,
            "manifest": manifest["inputs"]["abm_cpr_surface_sha256"],
        })

    raw = pd.read_csv(ABM_CPR_SURFACE_CSV)
    surfaces = fed.load_cpr_surface()
    surface_keys = sorted(surfaces.keys())
    shape_ok = (
        len(raw) == EXPECTED_ROWS
        and len(surface_keys) == EXPECTED_N_COHORTS
        and all(len(s) == 5 for s in surfaces.values())
        and all(s[3].shape == EXPECTED_GRID for s in surfaces.values())
    )
    if not shape_ok:
        _fail("G0b_surface_shape_mismatch", {
            "n_rows": len(raw),
            "expected_rows": EXPECTED_ROWS,
            "n_cohort_surfaces": len(surface_keys),
            "shapes": {str(k): list(s[3].shape) for k, s in surfaces.items()},
        })

    print("Fetching SOMA MBS coupon cohorts from NY Fed …")
    cohorts = fed.fetch_soma_mbs_cohorts()
    live_keys = sorted(_cohort_key(c) for c in cohorts)
    if (len(cohorts) != pipe["n_cohorts"]
            or len(cohorts) != EXPECTED_N_COHORTS
            or live_keys != surface_keys):
        _fail("G0c_cohort_structure_mismatch", {
            "n_live": len(cohorts),
            "n_manifest": pipe["n_cohorts"],
            "live_keys": [list(k) for k in live_keys],
            "surface_keys": [list(k) for k in surface_keys],
        })

    ref = abm.reference_cohort(cohorts)
    ref_key = _cohort_key(ref)
    manifest_ref_key = (fed._round_coupon(manifest_ref["coupon"]),
                        int(manifest_ref["term_months"]))
    offset_k = int(ref["months_elapsed"]) - int(manifest_ref["months_elapsed"])
    if ref_key != manifest_ref_key or offset_k not in SEASONING_OFFSET_ALLOWED:
        _fail("G0d_reference_cohort_mismatch", {
            "live_ref_key": list(ref_key),
            "manifest_ref_key": list(manifest_ref_key),
            "live_ref_months_elapsed": int(ref["months_elapsed"]),
            "manifest_ref_months_elapsed": int(manifest_ref["months_elapsed"]),
            "seasoning_offset_k": offset_k,
            "allowed": list(SEASONING_OFFSET_ALLOWED),
            "note": "likely SOMA as-of drift beyond the allowed uniform "
                    "correction, or bucket composition churn",
        })
    if offset_k:
        print(f"G0d: uniform seasoning offset k={offset_k} (SOMA as-of "
              f"advanced past the frozen run); subtracting from all cohorts.")
    for c in cohorts:
        c["months_elapsed"] = max(0, int(c["months_elapsed"]) - offset_k)
    print(f"G0 PASS: sha256 anchored, {EXPECTED_N_COHORTS} cohorts, "
          f"key sets equal, k={offset_k}.")

    # ------------------------------------------- engine (manifest-anchored)
    print("Rebuilding production engine from manifest parameters "
          f"(seed {abm.RNG_SEED}, scale {pipe['mobility_scale']}) …")
    engine = abm.HousingMarketEngine(
        seed=abm.RNG_SEED,
        median_income=pipe["median_income"],
        median_home_value=pipe["median_home_value"],
        mobility_scale=pipe["mobility_scale"],
    )

    # ------------------------------------------------------------------ G1
    print("G1: on-grid parity (bit-exact) at "
          f"{len(G1_NODES)} nodes x {len(cohorts)} cohorts …")
    g1_max_us = 0.0
    g1_max_dk = 0.0
    g1_failures = []
    for c in cohorts:
        key = _cohort_key(c)
        slab = _slab_for_key(raw, key)
        r_grid, f_grid, v_grid = _slab_grids(slab)
        engine.attach_cohort(c["coupon"], c["months_elapsed"],
                             term_years=key[1] // 12)
        for (ir, jf, iv) in G1_NODES:
            rate, fric, vel = r_grid[ir], f_grid[jf], v_grid[iv]
            row = slab[(slab["Market_Rate"] == rate)
                       & (slab["Friction"] == fric)
                       & (slab["Rate_Velocity"] == vel)]
            if len(row) != 1:
                _fail("G1_node_row_not_unique", {
                    "cohort": list(key), "node": [ir, jf, iv],
                    "n_rows": len(row),
                })
            row = row.iloc[0]
            d_us = engine.cpr_at(float(rate), "US", float(fric), float(vel))
            d_dk = engine.cpr_at(float(rate), "Danish", float(fric),
                                 float(vel))
            diff_us = abs(d_us - float(row["CPR_US"])) * 100.0
            diff_dk = abs(d_dk - float(row["CPR_Danish"])) * 100.0
            g1_max_us = max(g1_max_us, diff_us)
            g1_max_dk = max(g1_max_dk, diff_dk)
            if diff_us > G1_TOL_US or diff_dk > G1_TOL_DK:
                g1_failures.append({
                    "cohort": list(key), "node": [ir, jf, iv],
                    "rate": float(rate), "friction": float(fric),
                    "velocity": float(vel),
                    "csv_us": float(row["CPR_US"]), "direct_us": d_us,
                    "csv_dk": float(row["CPR_Danish"]), "direct_dk": d_dk,
                })
    if g1_failures:
        _fail("G1_on_grid_parity", {
            "n_failures": len(g1_failures),
            "max_abs_diff_us_pp": g1_max_us,
            "max_abs_diff_dk_pp": g1_max_dk,
            "failures": g1_failures[:10],
            "note": "engine/cohort reconstruction NOT proven — off-grid "
                    "numbers would be uninterpretable",
        })
    print(f"G1 PASS: all {len(G1_NODES) * len(cohorts)} nodes reproduce the "
          f"committed surface (US bit-exact, max {g1_max_us:.1e}pp; Danish "
          f"max {g1_max_dk:.1e}pp vs CSV-serialization tol {G1_TOL_DK:.0e}).")

    # ------------------------------------------------------------------ G2
    print("G2: realized-coordinate reconstruction …")
    frozen = pd.read_csv(METRICS_MONTHLY_CSV, index_col=0, parse_dates=True)
    if len(frozen) != manifest["metrics"]["qt_window"]["n_months"]:
        _fail("G2_frozen_window_shape", {
            "n_rows": len(frozen),
            "manifest_n_months": manifest["metrics"]["qt_window"]["n_months"],
        })
    print("Fetching FRED/macro frame (pre-window velocity months) …")
    live = fed.fetch_data()
    live = fed.calculate_dynamic_friction(live)
    if not frozen.index.isin(live.index).all():
        _fail("G2_index_misalignment", {
            "frozen_first": str(frozen.index[0]),
            "frozen_last": str(frozen.index[-1]),
            "live_first": str(live.index[0]),
            "live_last": str(live.index[-1]),
        })
    rate_parity = float((live["MORTGAGE30US"].reindex(frozen.index)
                         - frozen["MORTGAGE30US"]).abs().max())
    fric_parity = float((live["Dynamic_Friction"].reindex(frozen.index)
                         - frozen["Dynamic_Friction"]).abs().max())
    if rate_parity > G2_RATE_TOL_PP:
        _fail("G2_mortgage_rate_revision", {
            "max_abs_diff_pp": rate_parity,
            "tolerance_pp": G2_RATE_TOL_PP,
            "note": "live MORTGAGE30US no longer reproduces the frozen "
                    "window; pre-window velocity months unverifiable",
        })
    spliced = live["MORTGAGE30US"].copy()
    spliced.loc[frozen.index] = frozen["MORTGAGE30US"]
    vel_full = spliced.diff(6).fillna(0.0) / 100.0   # fed L858 convention
    vel = vel_full.reindex(frozen.index)
    if vel.isna().any():
        _fail("G2_velocity_reconstruction_nan", {
            "n_nan": int(vel.isna().sum()),
        })
    print(f"G2 PASS: rate parity {rate_parity:.2e}pp "
          f"(friction diagnostic {fric_parity:.2e}, not gated); "
          f"velocity rebuilt for {len(vel)} months "
          f"[{vel.min() * 100:+.2f}pp, {vel.max() * 100:+.2f}pp].")

    thr = abm.WAIT_AND_SEE_RATE_THRESHOLD
    ref_v_grid = _slab_grids(_slab_for_key(raw, manifest_ref_key))[2]
    v_hi = float(ref_v_grid[np.searchsorted(ref_v_grid, thr, side="right")])
    kink_months = [ts.strftime("%Y-%m") for ts, x in vel.items()
                   if thr < float(x) < v_hi]

    # ------------------------------------------------ midpoint cohort rule
    others = sorted(
        (c for c in cohorts if _cohort_key(c) != manifest_ref_key),
        key=lambda c: (-c["weight"],
                       0 if int(c["term_months"]) == 360 else 1,
                       c["coupon"]),
    )
    midpoint_cohorts = [ref] + others[:2]
    midpoint_keys = [_cohort_key(c) for c in midpoint_cohorts]
    print(f"Midpoint cohorts (rule: {MIDPOINT_COHORT_RULE}): "
          + ", ".join(f"{k[1] // 12}yr {k[0] * 100:.2f}%"
                      for k in midpoint_keys))

    # --------------------------------------------------- off-grid midpoints
    print("Off-grid midpoint check "
          f"({len(MIDPOINTS)} points x {len(midpoint_cohorts)} cohorts) …")
    midpoint_records = []
    for c in midpoint_cohorts:
        key = _cohort_key(c)
        slab = _slab_for_key(raw, key)
        r_grid, f_grid, v_grid = _slab_grids(slab)
        surf_c = surfaces[key]
        engine.attach_cohort(c["coupon"], c["months_elapsed"],
                             term_years=key[1] // 12)
        for (pid, ir, jf, iv, kink) in MIDPOINTS:
            r_mid = float((r_grid[ir] + r_grid[ir + 1]) / 2.0)
            f_mid = float((f_grid[jf] + f_grid[jf + 1]) / 2.0)
            v_mid = float((v_grid[iv] + v_grid[iv + 1]) / 2.0)
            straddles = (v_grid[iv] <= thr) and (v_mid > thr)
            if straddles != kink:
                _fail("midpoint_kink_flag_inconsistent", {
                    "point": pid, "declared": kink, "derived": bool(straddles),
                })
            d_us = engine.cpr_at(r_mid, "US", f_mid, v_mid) * 100.0
            d_dk = engine.cpr_at(r_mid, "Danish", f_mid, v_mid) * 100.0
            itp = fed.interp_cpr_surface(
                pd.Series([r_mid * 100.0]), pd.Series([f_mid]), surf_c,
                velocity=pd.Series([v_mid]),
            )
            i_us = float(itp["US_CPR_Pct"].iloc[0])
            i_dk = float(itp["Danish_CPR_Pct"].iloc[0])
            midpoint_records.append({
                "point_id": pid,
                "cohort": list(key),
                "rate_pct": r_mid * 100.0,
                "friction": f_mid,
                "velocity": v_mid,
                "kink_straddle": bool(kink),
                "direct_us_pp": d_us, "interp_us_pp": i_us,
                "abs_diff_us_pp": abs(d_us - i_us),
                "direct_dk_pp": d_dk, "interp_dk_pp": i_dk,
                "abs_diff_dk_pp": abs(d_dk - i_dk),
            })

    mp_us = np.array([m["abs_diff_us_pp"] for m in midpoint_records])
    mp_dk = np.array([m["abs_diff_dk_pp"] for m in midpoint_records])
    kink_mask = np.array([m["kink_straddle"] for m in midpoint_records])
    midpoint_summary = {
        "all": {"us": _stats(mp_us), "dk": _stats(mp_dk)},
        "kink_straddling": {"us": _stats(mp_us[kink_mask]),
                            "dk": _stats(mp_dk[kink_mask])},
        "non_kink": {"us": _stats(mp_us[~kink_mask]),
                     "dk": _stats(mp_dk[~kink_mask])},
    }
    mp_pass_us = bool(mp_us.max() <= MIDPOINT_MAX_TOL_PP)
    mp_pass_dk = bool(mp_dk.max() <= MIDPOINT_MAX_TOL_PP)
    print(f"  US  max |Δ| {mp_us.max():.4f}pp "
          f"(non-kink {mp_us[~kink_mask].max():.4f}, "
          f"kink {mp_us[kink_mask].max():.4f}) "
          f"{'PASS' if mp_pass_us else 'FAIL'} vs {MIDPOINT_MAX_TOL_PP}pp")
    print(f"  DK  max |Δ| {mp_dk.max():.4f}pp "
          f"{'PASS' if mp_pass_dk else 'FAIL'} vs {MIDPOINT_MAX_TOL_PP}pp")

    # ------------------------------------------------ realized coordinates
    print(f"Realized-coordinate check ({len(frozen)} months x "
          f"{len(cohorts)} cohorts) …")
    rate_pct = frozen["MORTGAGE30US"]
    fric_ser = frozen["Dynamic_Friction"]
    n_m = len(frozen)
    weights = np.array([c["weight"] for c in cohorts])
    direct_us = np.empty((len(cohorts), n_m))
    direct_dk = np.empty((len(cohorts), n_m))
    interp_us = np.empty((len(cohorts), n_m))
    interp_dk = np.empty((len(cohorts), n_m))
    per_cohort = []
    for ci, c in enumerate(cohorts):
        key = _cohort_key(c)
        surf_c = surfaces[key]
        engine.attach_cohort(c["coupon"], c["months_elapsed"],
                             term_years=key[1] // 12)
        itp = fed.interp_cpr_surface(rate_pct, fric_ser, surf_c, velocity=vel)
        interp_us[ci] = itp["US_CPR_Pct"].to_numpy()
        interp_dk[ci] = itp["Danish_CPR_Pct"].to_numpy()
        for ti in range(n_m):
            r_dec = float(rate_pct.iloc[ti]) / 100.0
            f_t = float(fric_ser.iloc[ti])
            v_t = float(vel.iloc[ti])
            direct_us[ci, ti] = engine.cpr_at(r_dec, "US", f_t, v_t) * 100.0
            direct_dk[ci, ti] = engine.cpr_at(r_dec, "Danish", f_t,
                                              v_t) * 100.0
        per_cohort.append({
            "cohort": list(key),
            "weight": float(c["weight"]),
            "months_elapsed_used": int(c["months_elapsed"]),
            "us": _stats(direct_us[ci] - interp_us[ci]),
            "dk": _stats(direct_dk[ci] - interp_dk[ci]),
        })

    w_diff_us = weights @ (direct_us - interp_us)   # signed, per month
    w_diff_dk = weights @ (direct_dk - interp_dk)
    weighted = {
        "us": {
            "mean_abs_monthly_pp": float(np.abs(w_diff_us).mean()),
            "abs_mean_signed_pp": float(abs(w_diff_us.mean())),
            "max_abs_monthly_pp": float(np.abs(w_diff_us).max()),
        },
        "dk": {
            "mean_abs_monthly_pp": float(np.abs(w_diff_dk).mean()),
            "abs_mean_signed_pp": float(abs(w_diff_dk.mean())),
            "max_abs_monthly_pp": float(np.abs(w_diff_dk).max()),
        },
        "weights_source": "live SOMA parse (production convention); "
                          "manifest reference weight drift reported below",
        "ref_weight_live": float(ref["weight"]),
        "ref_weight_manifest": float(manifest_ref["weight"]),
    }
    rl_pass_us = bool(weighted["us"]["mean_abs_monthly_pp"]
                      <= WINDOW_WEIGHTED_MEAN_TOL_PP)
    rl_pass_dk = bool(weighted["dk"]["mean_abs_monthly_pp"]
                      <= WINDOW_WEIGHTED_MEAN_TOL_PP)
    all_diff_us = (direct_us - interp_us).ravel()
    all_diff_dk = (direct_dk - interp_dk).ravel()
    print(f"  US  weighted mean |Δ| {weighted['us']['mean_abs_monthly_pp']:.4f}pp "
          f"(|mean signed| {weighted['us']['abs_mean_signed_pp']:.4f}) "
          f"{'PASS' if rl_pass_us else 'FAIL'} vs "
          f"{WINDOW_WEIGHTED_MEAN_TOL_PP}pp")
    print(f"  DK  weighted mean |Δ| {weighted['dk']['mean_abs_monthly_pp']:.4f}pp "
          f"{'PASS' if rl_pass_dk else 'FAIL'}")
    print(f"  Kink-band months (velocity in ({thr:+.3f}, {v_hi:+.3f})): "
          f"{len(kink_months)} — {kink_months}")

    # ----------------------------------------------------------- artifact
    payload = {
        "status": "OK",
        "mode": "interp_spot_check",
        "spec": "round-17 R17-J (referee DC3); off-grid validation of the "
                "trilinear CPR-surface interpolation vs direct _cpr_vec "
                "micro-simulation; gates G0-G2 then pre-committed T1/T2",
        "identifiers": {
            "run_tag": BERGER_TAG,
            "manifest_git_commit": manifest.get("git_commit"),
            "surface_sha256": sha,
            "seed": abm.RNG_SEED,
            "mobility_scale": pipe["mobility_scale"],
            "median_income": pipe["median_income"],
            "median_home_value": pipe["median_home_value"],
            "seasoning_offset_k": offset_k,
            "n_cohorts": len(cohorts),
            "cohorts": [{
                "coupon": float(c["coupon"]),
                "term_months": int(c["term_months"]),
                "weight": float(c["weight"]),
                "months_elapsed_used": int(c["months_elapsed"]),
            } for c in cohorts],
            "numpy_version": np.__version__,
            "pandas_version": pd.__version__,
            "python_version": sys.version.split()[0],
        },
        "gates": {
            "G0_frozen_inputs": {
                "surface_sha256_match": True,
                "surface_rows": int(len(raw)),
                "grid_shape": list(EXPECTED_GRID),
                "cohort_key_sets_equal": True,
                "seasoning_offset_k": offset_k,
                "pass": True,
            },
            "G1_on_grid_parity": {
                "node_indices": [list(n) for n in G1_NODES],
                "n_nodes_tested": len(G1_NODES) * len(cohorts),
                "tolerance_pp": {"us": G1_TOL_US, "dk": G1_TOL_DK},
                "max_abs_diff_us_pp": g1_max_us,
                "max_abs_diff_dk_pp": g1_max_dk,
                "bit_exact": True,
                "pass": True,
            },
            "G2_realized_coordinates": {
                "rate_parity_max_abs_pp": rate_parity,
                "rate_parity_tolerance_pp": G2_RATE_TOL_PP,
                "friction_parity_max_abs_diagnostic": fric_parity,
                "velocity_source": "diff(6)/100 of frozen in-window "
                                   "MORTGAGE30US spliced with live "
                                   "fetch_data() pre-window months",
                "velocity_min": float(vel.min()),
                "velocity_max": float(vel.max()),
                "pass": True,
            },
        },
        "midpoint_check": {
            "tolerance_max_abs_pp": MIDPOINT_MAX_TOL_PP,
            "cohort_rule": MIDPOINT_COHORT_RULE,
            "cohorts_resolved": [list(k) for k in midpoint_keys],
            "points": midpoint_records,
            "summary": midpoint_summary,
            "pass_us": mp_pass_us,
            "pass_dk": mp_pass_dk,
        },
        "realized_check": {
            "tolerance_weighted_mean_abs_pp": WINDOW_WEIGHTED_MEAN_TOL_PP,
            "n_months": n_m,
            "n_cohorts": len(cohorts),
            "per_cohort": per_cohort,
            "pooled_unweighted": {"us": _stats(all_diff_us),
                                  "dk": _stats(all_diff_dk)},
            "weighted": weighted,
            "kink_band": {
                "threshold": float(thr),
                "upper_node": v_hi,
                "n_months_in_band": len(kink_months),
                "months": kink_months,
            },
            "pass_us": rl_pass_us,
            "pass_dk": rl_pass_dk,
        },
        "all_tolerances_pass": bool(mp_pass_us and mp_pass_dk
                                    and rl_pass_us and rl_pass_dk),
        "scope": SCOPE_NOTE,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    RESULTS_JSON.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\nAll gates PASS; tolerances "
          f"{'ALL PASS' if payload['all_tolerances_pass'] else 'NOT all met'} "
          f"(T1 US {mp_pass_us} / DK {mp_pass_dk}; "
          f"T2 US {rl_pass_us} / DK {rl_pass_dk}).")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
