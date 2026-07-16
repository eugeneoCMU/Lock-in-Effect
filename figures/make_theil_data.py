#!/usr/bin/env python3
"""
Round-16 W4: dynamic-fit diagnostics — Theil decomposition + cumulative
error profiles for the three estimators (fit diagnostics, NOT timing
credentials).

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------

PURPOSE
  Reviewer asks for dynamic-fit diagnostics beyond level recovery: a Theil
  decomposition (where each estimator's monthly error lives — bias vs
  variance vs covariance) and cumulative error profiles (the running dollar
  divergence between each simulated rolloff path and the empirical SOMA
  path).  The paper's posture is unchanged and is restated here ex ante: NO
  timing credential is claimed for any estimator (peak-lag moving-block
  intervals span zero; the beta1=0 null shares Path B's -3 peak; §V.C).
  These diagnostics FORMALIZE the fit decomposition already narrated in the
  manuscript; they feed a new appendix table (tab:theil) and 2-3 sentences
  in sec:pathb, labeled fit diagnostics throughout.

INPUTS (all committed except the two public APIs)
  abm/data/runs/run-2026-07-04-15yr-foldin/metrics_monthly.csv
      ABM production fold-in run: US_CPR_Pct (simulated), Empirical_CPR_Pct
      (ABM-side empirical back-out), US_Missed_Rolloff_Billions (= US
      simulated rolloff - QT target, monthly), Extension_Delta_Billions
      (= actual SOMA rolloff - QT target, monthly), QT_Target_Billions.
  abm/data/runs/run-2026-07-04-15yr-foldin/manifest.json
      Committed references: metrics.cross_correlation (gate G1),
      metrics.dollars_b.us_trapped / empirical_trapped (gate G2).
  hazard/data/simulation_results.parquet
      Path A (spec v4, hash-identical to the frozen
      run-2026-07-14-pathA-seasonal artifact): hazard_cpr_pct,
      simulated_rolloff_b.
  hazard/data/microsim_results.parquet
      Path B (literature microsim, central 6.5%): hazard_cpr_pct,
      simulated_rolloff_b.
  hazard/data/runs/run-2026-07-14-pathA-seasonal/manifest.json
      Committed references: headline.r_lag0 / best_lag (gate G4),
      headline.trapped_b = 928.892970289881 (gate G6).
  hazard/data/extension_risk_results_literature_microsim.json
      Committed references: cross_correlation (gate G5), hazard_trapped_b
      = 818.5300844066606 (gate G7), empirical_trapped_b
      = 764.7482532227002 (gate G3).
  Network (primary empirical series; exactly the make_ccf_data.py path):
      FRED via fredapi (FRED_API_KEY from repo .env) + NY Fed SOMA API,
      through macro.fetch_data / macro.fetch_soma_mbs_monthly /
      macro.build_empirical_metrics.  If either fetch fails the script
      EXITS NONZERO with a clear message — no silent WSHOMCB fallback (a
      fallback decision would be a disclosed spec amendment).

CONSTRUCTION (deterministic; window = 42 months 2022-06..2025-11, the
active QT window, month-end stamps; no wall-clock, no randomness)
  Empirical CPR path (primary): hazard-side back-out, exactly as
  make_ccf_data.py builds it — build_empirical_metrics(
  calculate_dynamic_friction(fetch_data()), soma_rolloff=
  fetch_soma_mbs_monthly()), then qt_active_frame + assert_qt_window_only.
  Simulated CPR paths: ABM US_CPR_Pct (committed CSV); Path A / Path B
  hazard_cpr_pct (committed parquets), reindexed onto the empirical index.

  For each estimator s vs empirical e (n=42 levels, n-1=41 first diffs):
  (a) Theil U1 on levels:
        U1 = sqrt(mean((s-e)^2)) / (sqrt(mean(s^2)) + sqrt(mean(e^2)))
      (bounded [0,1]; 0 = perfect).
  (b) Theil U2 on first differences:
        U2 = sqrt(mean((ds-de)^2)) / sqrt(mean(de^2)),  d = one-month diff
      (RMSE of predicted month-over-month changes relative to the naive
      no-change forecast; U2 > 1 = worse than no-change).
  (c) Standard Theil MSE decomposition, on THREE transforms — levels,
      first differences, linearly detrended (per-series OLS on t=0..n-1,
      residuals; detrended means are 0 by construction, so the detrended
      bias share is exactly 0):
        bias = (mean(s)-mean(e))^2
        var  = (sd(s)-sd(e))^2          [population sd, ddof=0]
        cov  = 2*(1-r)*sd(s)*sd(e)      [r = Pearson correlation]
      bias+var+cov == MSE identically under ddof=0 (gate G9); shares are
      reported in PERCENT of the sum.
  (d) Cumulative error profiles (per month, $B):
        Path A/B leg: cumsum(simulated_rolloff_b)
                      - cumsum(Actual_Monthly_Rolloff_Billions)   [hazard-
                      side SOMA actual, same source the recovery figures /
                      score_extension_risk use]
        ABM leg:      cumsum(US_Missed_Rolloff_Billions
                      - Extension_Delta_Billions)  from the committed
                      metrics_monthly.csv (= cumsum(US simulated rolloff -
                      ABM-side SOMA actual); settlement-lag kernel applied
                      to the simulated leg per the fold-in manifest).
      Bases are DISCLOSED in the artifact.  All legs share the QT cap
      schedule (-17.5 x3, -35.0 x39, sum -1417.5), so each leg's terminal
      value equals its trapped-$B aggregate minus the empirical trapped-$B
      on that leg's own basis, and the terminal simulated cumsums reproduce
      tab:estimators by construction: Path B cumsum -599.0B -> $818.5B
      trapped, Path A -488.6B -> $928.9B (gates G6/G7).
  (e) Empirical-series variant: the ABM-side back-out (Empirical_CPR_Pct
      from the committed CSV) is computed alongside the primary hazard-side
      series; both lag-0 correlations vs Path B are reported (gate G8; the
      tex already discloses a third-decimal difference between the two
      back-outs).

GATES (numbered; any failure => no artifact, exit 1)
  G1 ABM CCF: cpr_cross_correlation(Empirical_CPR_Pct, US_CPR_Pct) at lags
     -3..+3 equals the fold-in manifest metrics.cross_correlation block,
     |diff| <= 1e-9 (same committed CSV, deterministic; make_ccf_data.py
     gate reused verbatim).
  G2 ABM dollar aggregates: sum(US_Missed_Rolloff_Billions) equals manifest
     dollars_b.us_trapped (90.98115583016241) and
     sum(Extension_Delta_Billions) equals dollars_b.empirical_trapped
     (764.7482532227002), |diff| <= 1e-9 B each.
  G3 Empirical parity: SOMA fetch succeeded (no WSHOMCB fallback,
     Rolloff_Source == "SOMA") AND the live empirical trapped sum equals
     the committed empirical_trapped_b 764.7482532227002 within +/-0.01 B
     (extension_risk_results_literature_microsim.json; the
     fannie_replication.py parity-tolerance convention).
  G4 Path A CCF: r at lag 0 within 1e-3 of the frozen v4 manifest headline
     r_lag0 (-0.37817286723880483), and the -3..+3 peak (max |r|) at the
     manifest best_lag (-2).  (make_ccf_data.py gate reused.)
  G5 Path B CCF: lags -3..+3 equal
     extension_risk_results_literature_microsim.json cross_correlation,
     |diff| <= 1e-6.  (make_ccf_data.py gate reused.)
  G6 Path A terminal reproduction: sum(simulated_rolloff_b - QT target)
     over the window equals the frozen manifest headline trapped_b
     928.892970289881 within +/-0.1 B (cumsum -488.6 B -> $928.9B).
  G7 Path B terminal reproduction: same construction equals the committed
     hazard_trapped_b 818.5300844066606 within +/-0.1 B (cumsum -599.0 B
     -> $818.5B).
  G8 Empirical-variant check: |r_lag0(hazard-side emp, Path B CPR) -
     r_lag0(ABM-side emp, Path B CPR)| < 0.02.
  G9 Theil identity: for every estimator x transform, |bias+var+cov - MSE|
     <= 1e-9 * MSE and the three shares sum to 100 within 1e-9 pp (guards
     the ddof=0 convention the decomposition identity requires).

PRE-COMMITTED INTERPRETATION (fixed ex ante; the diagnostics sharpen, not
reverse, the printed narrative)
  Expected reading (quick-pass prototype values; production must be derived
  independently and should land near): Path B's levels error is
  VARIANCE-dominated with near-zero bias share (~0.259 U1, shares ~2/91/7)
  — level accuracy without co-movement; the residual is under-dispersion
  vs the seasonal empirical path.  ABM's levels error is BIAS-dominated
  (~0.436 U1, shares ~71/0/28) — level failure.  Path A sits between
  (~0.420 U1, shares ~21/10/69).  Detrended, all three are
  covariance/variance-dominated with bias exactly 0 (ABM ~0.808 U1,
  0/0/100; Path A ~0.835, 0/41/59; Path B ~0.979, 0/94/6).
  Outcome branches:
    - If the shares land as expected (Path B levels bias share <= 10% and
      var share >= 50%; ABM levels bias share >= 50%): the manuscript
      sentences read Path B as level-accurate but under-dispersed and the
      ABM as level-biased — the existing narrative, formalized.
    - Any other configuration: the table prints the shares as computed and
      the sec:pathb sentences describe the actual dominant component; no
      re-framing, no threshold moves.
    - U2 > 1 for all three estimators is the EXPECTED outcome (no
      estimator beats the naive no-change forecast month-over-month) and
      is reported as such.  If any estimator lands U2 < 1, that is still
      NOT claimed as a timing credential — it stays a fit diagnostic and
      is reported with the same label.
  In every branch: no timing credential is claimed for any estimator; the
  numbers feed the fit-decomposition appendix table (tab:theil) and 2-3
  sentences in sec:pathb only.

OUTPUT (written ONLY if all gates pass)
  figures/theil_data.json with keys:
    window                {start, end, n_months, n_diffs}
    estimators            per estimator {u1_levels, u2_diffs, u1_detrended,
                          decomp:{levels, diffs, detrended each
                          {bias_share, var_share, cov_share, mse}}}
                          (shares in PERCENT of the decomposition sum)
    cumulative_error      {months[], pathA[], pathB[], abm[], bases,
                          terminal_b}
    empirical_variant_check  {r_lag0_pathb_hazard_side,
                          r_lag0_pathb_abm_side, abs_diff, tolerance}
    gates                 G1..G9 measured-vs-reference + pass flags
    plus top-level spec echo (mode, spec, sources, note).

PROVENANCE
  All inputs are committed in-repo artifacts or public APIs (FRED, NY Fed
  SOMA); no restricted loan-level data is touched and the artifact carries
  headline statistics only.

Run:  python3 figures/make_theil_data.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hazard"))

from config import MICROSIM_RESULTS_PATH, SIM_RESULTS_PATH  # noqa: E402
from macro import (  # noqa: E402
    assert_qt_window_only,
    build_empirical_metrics,
    calculate_dynamic_friction,
    cpr_cross_correlation,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
)

OUT = ROOT / "figures" / "theil_data.json"
FOLDIN_DIR = ROOT / "abm" / "data" / "runs" / "run-2026-07-04-15yr-foldin"
PATHA_MANIFEST = (
    ROOT / "hazard" / "data" / "runs" / "run-2026-07-14-pathA-seasonal"
    / "manifest.json"
)
EXT_LIT = ROOT / "hazard" / "data" / "extension_risk_results_literature_microsim.json"

N_MONTHS = 42
CCF_TOL_ABM = 1e-9
DOLLAR_TOL_ABM_B = 1e-9
EMP_PARITY_TOL_B = 0.01
CCF_TOL_PATHA_LAG0 = 1e-3
CCF_TOL_PATHB = 1e-6
TERMINAL_TOL_B = 0.1
VARIANT_R_TOL = 0.02
IDENTITY_REL_TOL = 1e-9


def _fail(msg: str) -> None:
    print(f"GATE FAILED: {msg}")
    sys.exit(1)


# --- Theil statistics (formulas fixed in the spec header) -------------------

def theil_u1(sim: np.ndarray, emp: np.ndarray) -> float:
    rmse = float(np.sqrt(np.mean((sim - emp) ** 2)))
    return rmse / (float(np.sqrt(np.mean(sim ** 2)))
                   + float(np.sqrt(np.mean(emp ** 2))))


def theil_u2_diffs(sim: np.ndarray, emp: np.ndarray) -> float:
    ds, de = np.diff(sim), np.diff(emp)
    return float(np.sqrt(np.mean((ds - de) ** 2)) / np.sqrt(np.mean(de ** 2)))


def mse_decomposition(sim: np.ndarray, emp: np.ndarray) -> dict:
    """bias/variance/covariance shares (percent) of the Theil MSE identity."""
    ms, me = float(sim.mean()), float(emp.mean())
    ss, se = float(sim.std(ddof=0)), float(emp.std(ddof=0))
    r = float(np.corrcoef(sim, emp)[0, 1])
    bias = (ms - me) ** 2
    var = (ss - se) ** 2
    cov = 2.0 * (1.0 - r) * ss * se
    total = bias + var + cov
    mse = float(np.mean((sim - emp) ** 2))
    return {
        "bias_share": 100.0 * bias / total,
        "var_share": 100.0 * var / total,
        "cov_share": 100.0 * cov / total,
        "mse": mse,
        "_identity_rel_err": abs(total - mse) / mse,
    }


def detrend(x: np.ndarray) -> np.ndarray:
    t = np.arange(len(x), dtype=float)
    coef = np.polyfit(t, x, 1)
    return x - np.polyval(coef, t)


def estimator_block(sim: np.ndarray, emp: np.ndarray) -> dict:
    transforms = {
        "levels": (sim, emp),
        "diffs": (np.diff(sim), np.diff(emp)),
        "detrended": (detrend(sim), detrend(emp)),
    }
    decomp = {name: mse_decomposition(s, e) for name, (s, e) in transforms.items()}
    return {
        "u1_levels": theil_u1(sim, emp),
        "u2_diffs": theil_u2_diffs(sim, emp),
        "u1_detrended": theil_u1(*transforms["detrended"]),
        "decomp": decomp,
    }


def main() -> None:
    # --- ABM production series (self-contained committed CSV) --------------
    csv = pd.read_csv(FOLDIN_DIR / "metrics_monthly.csv",
                      index_col=0, parse_dates=True)
    foldin_manifest = json.loads((FOLDIN_DIR / "manifest.json").read_text())

    # G1: ABM CCF vs fold-in manifest (make_ccf_data.py gate, reused).
    sub = csv.dropna(subset=["Empirical_CPR_Pct", "US_CPR_Pct"])
    abm_ccf = cpr_cross_correlation(
        sub["Empirical_CPR_Pct"].reset_index(drop=True),
        sub["US_CPR_Pct"].reset_index(drop=True),
        max_lag=3,
    )
    want_abm = {int(k): v
                for k, v in foldin_manifest["metrics"]["cross_correlation"].items()}
    for lag, want in want_abm.items():
        if abs(abm_ccf[lag] - want) > CCF_TOL_ABM:
            _fail(f"G1 ABM lag {lag}: got {abm_ccf[lag]:.10f}, "
                  f"manifest {want:.10f}")
    print(f"[GATE G1] ABM CCF +/-3 == fold-in manifest to {CCF_TOL_ABM:.0e} "
          f"(lag 0 = {abm_ccf[0]:+.4f})  PASS")

    # G2: ABM dollar aggregates vs fold-in manifest.
    dollars = foldin_manifest["metrics"]["dollars_b"]
    abm_trapped = float(csv["US_Missed_Rolloff_Billions"].sum())
    abm_emp_trapped = float(csv["Extension_Delta_Billions"].sum())
    d_us = abm_trapped - dollars["us_trapped"]
    d_emp = abm_emp_trapped - dollars["empirical_trapped"]
    if abs(d_us) > DOLLAR_TOL_ABM_B or abs(d_emp) > DOLLAR_TOL_ABM_B:
        _fail(f"G2 ABM aggregates: us_trapped diff {d_us:+.3e} B, "
              f"empirical_trapped diff {d_emp:+.3e} B")
    print(f"[GATE G2] ABM sums == manifest (us_trapped {abm_trapped:.4f} B, "
          f"empirical {abm_emp_trapped:.4f} B)  PASS")

    # --- Hazard empirical series (network; no silent fallback) -------------
    print("Fetching hazard macro + SOMA for the primary empirical series ...")
    try:
        macro = calculate_dynamic_friction(fetch_data())
    except Exception as exc:
        print(f"FATAL: FRED fetch failed ({exc}). The primary empirical "
              "series cannot be built; a fallback would be a spec amendment. "
              "Aborting.")
        sys.exit(1)
    soma = fetch_soma_mbs_monthly()
    if soma is None:
        print("FATAL: NY Fed SOMA fetch failed. Refusing the WSHOMCB-diff "
              "fallback (spec: no silent fallback). Aborting.")
        sys.exit(1)
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    qt_emp = qt_active_frame(empirical)
    assert_qt_window_only(qt_emp.index)
    if len(qt_emp) != N_MONTHS:
        _fail(f"empirical window has {len(qt_emp)} months, expected {N_MONTHS}")
    if not (qt_emp["Rolloff_Source"] == "SOMA").all():
        _fail("G3: Rolloff_Source is not SOMA on the QT window")

    ext_lit = json.loads(EXT_LIT.read_text())
    emp_trapped_live = float(qt_emp["Extension_Delta_Billions"].sum())
    d_parity = emp_trapped_live - ext_lit["empirical_trapped_b"]
    if abs(d_parity) > EMP_PARITY_TOL_B:
        _fail(f"G3 empirical parity: live trapped {emp_trapped_live:.4f} B "
              f"vs committed {ext_lit['empirical_trapped_b']:.4f} B "
              f"(diff {d_parity:+.4f} B > {EMP_PARITY_TOL_B} B)")
    print(f"[GATE G3] SOMA source + empirical trapped {emp_trapped_live:.4f} B "
          f"== committed (diff {d_parity:+.2e} B)  PASS")

    # ABM CSV must sit on the same 42 month-end stamps as the hazard frame.
    if not csv.index.equals(qt_emp.index):
        _fail("ABM metrics_monthly.csv index != hazard QT-window index")

    # --- Simulated hazard paths --------------------------------------------
    def load_sim(parquet: Path) -> pd.DataFrame:
        sim = pd.read_parquet(parquet)
        qt_sim = sim.reindex(qt_emp.index).dropna(subset=["simulated_rolloff_b"])
        assert_qt_window_only(qt_sim.index)
        if len(qt_sim) != N_MONTHS:
            _fail(f"{parquet.name}: {len(qt_sim)} months, expected {N_MONTHS}")
        return qt_sim

    path_a = load_sim(Path(SIM_RESULTS_PATH))
    path_b = load_sim(Path(MICROSIM_RESULTS_PATH))

    # G4: Path A CCF vs frozen v4 manifest (make_ccf_data.py gate, reused).
    headline = json.loads(PATHA_MANIFEST.read_text())["headline"]
    pa_ccf = cpr_cross_correlation(
        qt_emp["Empirical_CPR_Pct"], path_a["hazard_cpr_pct"], max_lag=3)
    if abs(pa_ccf[0] - headline["r_lag0"]) > CCF_TOL_PATHA_LAG0:
        _fail(f"G4 Path A lag 0: got {pa_ccf[0]:.5f}, "
              f"frozen manifest {headline['r_lag0']:.5f}")
    pa_peak = max(range(-3, 4), key=lambda k: abs(pa_ccf[k]))
    if pa_peak != int(headline["best_lag"]):
        _fail(f"G4 Path A +/-3 peak: got {pa_peak}, "
              f"frozen manifest {headline['best_lag']}")
    print(f"[GATE G4] Path A lag 0 = {pa_ccf[0]:+.4f} (manifest "
          f"{headline['r_lag0']:+.4f}), peak at {pa_peak}  PASS")

    # G5: Path B CCF vs committed artifact (make_ccf_data.py gate, reused).
    pb_ccf = cpr_cross_correlation(
        qt_emp["Empirical_CPR_Pct"], path_b["hazard_cpr_pct"], max_lag=3)
    want_pb = {int(k): v for k, v in ext_lit["cross_correlation"].items()}
    for lag, want in want_pb.items():
        if abs(pb_ccf[lag] - want) > CCF_TOL_PATHB:
            _fail(f"G5 Path B lag {lag}: got {pb_ccf[lag]:.8f}, "
                  f"committed {want:.8f}")
    print(f"[GATE G5] Path B CCF +/-3 == committed artifact to "
          f"{CCF_TOL_PATHB:.0e} (lag 0 = {pb_ccf[0]:+.4f})  PASS")

    # --- Terminal reproduction gates (tab:estimators by construction) ------
    target = qt_emp["QT_Target_Billions"]
    trapped_pa = float((path_a["simulated_rolloff_b"] - target).sum())
    trapped_pb = float((path_b["simulated_rolloff_b"] - target).sum())
    d_pa = trapped_pa - headline["trapped_b"]
    d_pb = trapped_pb - ext_lit["hazard_trapped_b"]
    if abs(d_pa) > TERMINAL_TOL_B:
        _fail(f"G6 Path A terminal: recomputed trapped {trapped_pa:.4f} B vs "
              f"frozen manifest {headline['trapped_b']:.4f} B "
              f"(diff {d_pa:+.4f} B)")
    print(f"[GATE G6] Path A cumsum {float(path_a['simulated_rolloff_b'].sum()):.1f} B "
          f"-> trapped {trapped_pa:.4f} B == manifest (diff {d_pa:+.2e} B)  PASS")
    if abs(d_pb) > TERMINAL_TOL_B:
        _fail(f"G7 Path B terminal: recomputed trapped {trapped_pb:.4f} B vs "
              f"committed {ext_lit['hazard_trapped_b']:.4f} B "
              f"(diff {d_pb:+.4f} B)")
    print(f"[GATE G7] Path B cumsum {float(path_b['simulated_rolloff_b'].sum()):.1f} B "
          f"-> trapped {trapped_pb:.4f} B == committed (diff {d_pb:+.2e} B)  PASS")

    # --- G8: empirical-series variant check ---------------------------------
    r0_hazard_side = pb_ccf[0]
    r0_abm_side = cpr_cross_correlation(
        csv["Empirical_CPR_Pct"], path_b["hazard_cpr_pct"], max_lag=0)[0]
    r0_diff = abs(r0_hazard_side - r0_abm_side)
    if r0_diff >= VARIANT_R_TOL:
        _fail(f"G8 empirical variant: lag-0 r vs Path B differs by "
              f"{r0_diff:.4f} (hazard-side {r0_hazard_side:+.4f}, ABM-side "
              f"{r0_abm_side:+.4f}; tolerance {VARIANT_R_TOL})")
    print(f"[GATE G8] empirical back-out variants: lag-0 r vs Path B "
          f"{r0_hazard_side:+.4f} (hazard-side) vs {r0_abm_side:+.4f} "
          f"(ABM-side), diff {r0_diff:.4f} < {VARIANT_R_TOL}  PASS")

    # --- Theil diagnostics (primary hazard-side empirical) ------------------
    emp = qt_emp["Empirical_CPR_Pct"].to_numpy(dtype=float)
    sims = {
        "abm": csv["US_CPR_Pct"].to_numpy(dtype=float),
        "path_a": path_a["hazard_cpr_pct"].to_numpy(dtype=float),
        "path_b": path_b["hazard_cpr_pct"].to_numpy(dtype=float),
    }
    estimators = {}
    g9_max_ident = 0.0
    g9_max_share = 0.0
    for name, sim in sims.items():
        block = estimator_block(sim, emp)
        for tname, dec in block["decomp"].items():
            ident = dec.pop("_identity_rel_err")
            share_err = abs(dec["bias_share"] + dec["var_share"]
                            + dec["cov_share"] - 100.0)
            g9_max_ident = max(g9_max_ident, ident)
            g9_max_share = max(g9_max_share, share_err)
            if ident > IDENTITY_REL_TOL or share_err > IDENTITY_REL_TOL:
                _fail(f"G9 Theil identity: {name}/{tname} rel err {ident:.2e},"
                      f" share sum err {share_err:.2e}")
        estimators[name] = block
        dl = block["decomp"]["levels"]
        dt = block["decomp"]["detrended"]
        print(f"  {name:>7}: U1 {block['u1_levels']:.3f}  "
              f"U2(diffs) {block['u2_diffs']:.3f}  "
              f"levels {dl['bias_share']:.1f}/{dl['var_share']:.1f}/"
              f"{dl['cov_share']:.1f}  detrended {dt['bias_share']:.1f}/"
              f"{dt['var_share']:.1f}/{dt['cov_share']:.1f}")
    print(f"[GATE G9] Theil identity holds for all estimators x transforms "
          f"(max rel err {g9_max_ident:.1e}, max share-sum err "
          f"{g9_max_share:.1e})  PASS")

    # --- Cumulative error profiles ($B) --------------------------------------
    actual = qt_emp["Actual_Monthly_Rolloff_Billions"]
    cum_pa = (path_a["simulated_rolloff_b"] - actual).cumsum()
    cum_pb = (path_b["simulated_rolloff_b"] - actual).cumsum()
    cum_abm = (csv["US_Missed_Rolloff_Billions"]
               - csv["Extension_Delta_Billions"]).cumsum()
    months = [ts.strftime("%Y-%m") for ts in qt_emp.index]

    payload = {
        "mode": "theil_dynamic_fit_diagnostics",
        "spec": ("round-16 W4: Theil U1/U2 + bias/variance/covariance MSE "
                 "decomposition (levels, first diffs, linearly detrended) and "
                 "cumulative rolloff-error profiles, 42-month QT window; fit "
                 "diagnostics only — no timing credential is claimed for any "
                 "estimator"),
        "window": {"start": months[0], "end": months[-1],
                   "n_months": N_MONTHS, "n_diffs": N_MONTHS - 1},
        "units_note": ("u1/u2 dimensionless; decomp *_share values are "
                       "PERCENT of the Theil decomposition sum (== MSE, "
                       "ddof=0); mse in pp^2 of annualized CPR; cumulative "
                       "error in $B"),
        "estimators": estimators,
        "cumulative_error": {
            "months": months,
            "pathA": [float(v) for v in cum_pa],
            "pathB": [float(v) for v in cum_pb],
            "abm": [float(v) for v in cum_abm],
            "bases": {
                "pathA": ("hazard/data/simulation_results.parquet "
                          "simulated_rolloff_b (settlement-weighted engine "
                          "rolloff, spec v4) minus hazard-side SOMA "
                          "Actual_Monthly_Rolloff_Billions "
                          "(macro.build_empirical_metrics)"),
                "pathB": ("hazard/data/microsim_results.parquet "
                          "simulated_rolloff_b minus the same hazard-side "
                          "SOMA actual"),
                "abm": ("committed metrics_monthly.csv: "
                        "cumsum(US_Missed_Rolloff_Billions - "
                        "Extension_Delta_Billions) = cumsum(US simulated "
                        "rolloff - ABM-side SOMA actual); settlement-lag "
                        "kernel on the simulated leg per the fold-in "
                        "manifest"),
                "common": ("all legs share the QT cap schedule, so each "
                           "terminal value equals that leg's trapped-$B "
                           "aggregate minus the empirical trapped-$B on its "
                           "own basis"),
            },
            "terminal_b": {
                "pathA": float(cum_pa.iloc[-1]),
                "pathB": float(cum_pb.iloc[-1]),
                "abm": float(cum_abm.iloc[-1]),
            },
        },
        "empirical_variant_check": {
            "r_lag0_pathb_hazard_side": r0_hazard_side,
            "r_lag0_pathb_abm_side": float(r0_abm_side),
            "abs_diff": float(r0_diff),
            "tolerance": VARIANT_R_TOL,
        },
        "gates": {
            "G1_abm_ccf": {"tol": CCF_TOL_ABM, "lag0": abm_ccf[0],
                           "pass": True},
            "G2_abm_dollar_sums": {
                "us_trapped_b": abm_trapped, "diff_b": d_us,
                "empirical_trapped_b": abm_emp_trapped,
                "empirical_diff_b": d_emp, "tol_b": DOLLAR_TOL_ABM_B,
                "pass": True},
            "G3_empirical_parity": {
                "live_trapped_b": emp_trapped_live,
                "committed_b": ext_lit["empirical_trapped_b"],
                "diff_b": d_parity, "tol_b": EMP_PARITY_TOL_B,
                "rolloff_source": "SOMA", "pass": True},
            "G4_patha_ccf": {"r_lag0": pa_ccf[0],
                             "manifest_r_lag0": headline["r_lag0"],
                             "peak_lag": pa_peak, "tol": CCF_TOL_PATHA_LAG0,
                             "pass": True},
            "G5_pathb_ccf": {"tol": CCF_TOL_PATHB, "lag0": pb_ccf[0],
                             "pass": True},
            "G6_patha_terminal": {
                "recomputed_trapped_b": trapped_pa,
                "reference_b": headline["trapped_b"], "diff_b": d_pa,
                "cumsum_sim_rolloff_b":
                    float(path_a["simulated_rolloff_b"].sum()),
                "tol_b": TERMINAL_TOL_B, "pass": True},
            "G7_pathb_terminal": {
                "recomputed_trapped_b": trapped_pb,
                "reference_b": ext_lit["hazard_trapped_b"], "diff_b": d_pb,
                "cumsum_sim_rolloff_b":
                    float(path_b["simulated_rolloff_b"].sum()),
                "tol_b": TERMINAL_TOL_B, "pass": True},
            "G8_empirical_variant": {"abs_diff": float(r0_diff),
                                     "tol": VARIANT_R_TOL, "pass": True},
            "G9_theil_identity": {"max_rel_err": g9_max_ident,
                                  "max_share_sum_err_pp": g9_max_share,
                                  "tol": IDENTITY_REL_TOL, "pass": True},
        },
        "sources": {
            "abm": "abm/data/runs/run-2026-07-04-15yr-foldin/"
                   "metrics_monthly.csv (production fold-in run; US_CPR_Pct "
                   "scored against the primary hazard-side empirical series)",
            "path_a": "hazard/data/simulation_results.parquet (spec v4, "
                      "hash-identical to run-2026-07-14-pathA-seasonal) vs "
                      "macro.build_empirical_metrics",
            "path_b": "hazard/data/microsim_results.parquet vs "
                      "macro.build_empirical_metrics",
        },
        "note": ("Fit diagnostics, not timing credentials (posture "
                 "pre-committed in the spec header): no timing claim is made "
                 "for any estimator; peak-lag intervals span zero and the "
                 "beta1=0 null shares Path B's -3 peak (manuscript §V.C). "
                 "Feeds appendix table tab:theil and 2-3 sentences in "
                 "sec:pathb."),
    }
    OUT.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"All gates passed. Written to {OUT}")


if __name__ == "__main__":
    main()
