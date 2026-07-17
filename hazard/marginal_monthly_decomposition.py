#!/usr/bin/env python3
"""
Round-17 R17-L (referee DC6 + Q7): month-by-month lock-in marginal path and
month x coupon-cohort decomposition.

SPEC (committed before execution; gates, tolerances, and interpretation
rules fixed ex ante in this header — spec-before-run discipline)
--------------------------------------------------------------------------

PURPOSE
  DC6 asks how the beta1=0 null and the central Path B distribute the
  shortfall over TIME — nothing at HEAD shows the monthly marginal path
  (the Theil profiles are estimator-vs-empirical only; the committed
  marginal decomposition is terminal-per-cell only).  Q7 asks for the
  month x coupon-cohort cross, which exists on neither axis alone: the
  committed monthly parquets have no cell dimension and the committed cell
  artifact (marginal_decomposition_results.json) has no month dimension.
  Two parts, one script:

  Part A — pure arithmetic on committed artifacts (no network, no engine):
    monthly marginal path  m_t = simulated_rolloff_b(central)_t
                                 - simulated_rolloff_b(null)_t
    from data/microsim_results.parquet (central) and
    data/microsim_results_pq0.0.parquet (beta1=0 null).  Sign convention:
    simulated_rolloff_b is NEGATIVE (rolloff as balance change); the null
    prepays more (cumulative -669.31 B vs central -598.97 B), so m_t > 0
    month by month and sum(m_t) = +70.345 B, the committed lock-in
    marginal.  Also derived: the null leg's cumulative error profile vs
    the empirical path, for app:theil, as

        null_profile_t = pathB_profile_t + cumsum(null - central)_t
                       = pathB_profile_t - cumsum(m)_t

    (the roadmap's formula, "pathB profile + cumsum(null-central)",
    paper/v16/revision_roadmap_round17.md R17-L feasibility (i); sign
    verified against committed anchors: terminal = pathB terminal
    53.78183118396042 MINUS 70.34506041989584 = -16.5632 B, matching
    no_lockin_null_results.json null_trapped_b - extension_risk_results_
    literature_microsim.json empirical_trapped_b = -16.56322923593541 B.
    A "+70.345" phrasing of this identity that circulated in task notes is
    the sign-flipped variant and is NOT the theil_data.json convention.)
    Reported (descriptive, no interpretation branch): the 42-month m_t
    array, its cumulative profile, early/mid/late third shares with the
    thirds fixed EX ANTE by month index — months 1-14 / 15-28 / 29-42 of
    the 42-month QT window (2022-06..2025-11) — and the peak month.
    Deterministic values derived from the committed artifacts during spec
    preparation (read-only; Part A has no run-time freedom): thirds
    14.964 / 29.472 / 25.910 B = 21.27% / 41.90% / 36.83%, peak 2023-11
    (m = 2.291 B).  The run must reproduce these or halt at the gates.

  Part B — light re-run of the committed decomposition engine, retaining
    monthly frames: the 2 parity legs + 15 vintage x coupon ablation cells
    of hazard/marginal_decomposition.py, EXACTLY as committed (same
    committed 75k loan sample, same RNG_SEED, same production beta1 =
    rothstein_beta1(ROTHSTEIN_Q_DECLINE_MID), same macro/empirical frames
    from live FRED + NY Fed SOMA — the engine's runtime requirement,
    unchanged), but capturing each leg's monthly simulated_rolloff_b
    array.  Per-cell monthly marginal: m_t^g = central_t - variant_g_t
    (central = the committed parquet column; gate B1 proves it
    bit-identical to the freshly captured central parity leg).  Cells are
    aggregated to the three coupon buckets {<3.0%, 3.0-4.0%, >=4.0%}
    (sum over vintages) for the month x coupon exhibit.

CAPTURE MECHANISM (the committed module is imported, never modified)
  hazard/marginal_decomposition.py binds microsim_engine._simulate_regime
  into its module namespace at import ("from microsim_engine import
  _simulate_regime"); its run_leg resolves the name at call time.  This
  script rebinds marginal_decomposition._simulate_regime to a wrapper that
  calls the original, records (index, simulated_rolloff_b copy) from the
  returned frame, and returns the SAME frame object — so the committed
  run_leg code object executes unchanged and score_extension_risk sees an
  identical input; bit-identical scalars are guaranteed by construction
  and verified by gates B1/B2.  Patch-and-restore in try/finally
  (curtailment_danish_scaling.py harness convention).

GATES (numbered; HALT semantics: on failure a GATE_FAILURE payload is
written to the results JSON for diagnosis, the figure artifact is NOT
written, and the script exits nonzero BEFORE any new quantity beyond the
failed gate prints — marginal_decomposition.py convention)
  A1 aggregate reproduction (two clauses, both HALT):
     (i)  sum(central col) - sum(null col) == 70.34506041989584 B
          BIT-EXACT.  Determinism tested read-only before this spec was
          fixed: the difference-of-column-sums is bit-exact and stable.
     (ii) |sum(m_t) - 70.34506041989584| <= 1e-9 relative.  Bit-exactness
          of the elementwise sum is FRAGILE by measurement, not
          assumption: every summation order tested read-only (np.sum,
          ndarray.sum, cumsum terminal, Python left-fold) gives
          70.34506041989579, i.e. 5.68e-14 B = 8.1e-16 relative from the
          committed total — float associativity, not signal.  The 1e-9
          relative tolerance is therefore the pre-committed gate for
          sum-of-differences forms; measured slack is ~7 orders inside it.
  A2 null-profile identity (offline, vs committed anchors; HALT):
     (a) stored pathB terminal (figures/theil_data.json
         cumulative_error.terminal_b.pathB, == last array element and
         42 months, months matching the parquet index) must equal
         committed hazard_trapped_b - empirical_trapped_b within 1e-9 B.
     (b) derived null terminal = pathB terminal - sum(m_t) must equal
         committed null_trapped_b - empirical_trapped_b within 1e-9 B
         (measured slack ~1.4e-14 B; tolerance is float-associativity
         headroom only).
  B0 live-input parity (after the FRED/SOMA fetch, before any engine leg;
     HALT; make_theil_data.py G3 conventions, no silent fallback):
     Rolloff_Source == "SOMA" on all 42 window months; live empirical
     trapped within +/-0.01 B of committed 764.7482532227002; the pathB
     cumulative error profile RECOMPUTED from the committed central
     parquet against the live SOMA actual matches the stored
     theil_data.json array with max per-month |diff| <= 0.01 B (this is
     the substantive check that "the pathB profile used matches the
     stored array"; residual differences at this gate are live-FRED input
     revisions, common to all runs — danish_discount_bound convention).
  B1 parity-leg reproduction with capture active (HALT):
     central leg (constant production-beta1 vector): scalar trapped
     within 1e-6 B of committed 818.5300844066606 (marginal_decomposition
     PARITY_TOL_B; committed run measured diff 0.0) AND captured monthly
     simulated_rolloff_b BIT-EXACT (max |diff| == 0.0) against the
     committed central parquet column, on an identical 42-month index;
     null leg (all-zero vector): same vs 748.1850239867648 and the pq0.0
     parquet.  Monthly bit-exactness is the proof that the capture
     wrapper did not perturb the simulation AND that the live macro frame
     reproduces the committed runs' inputs.
  B2 cell terminal reproduction (HALT): each of the 15 cells' terminal
     marginal, computed exactly as committed (marginal_b =
     CENTRAL_TRAPPED_B - trapped_g, scored scalar), must equal the
     committed marginal_decomposition_results.json cells[].marginal_b
     BIT-EXACT (max |diff| == 0.0), cells matched on (vintage, bucket)
     and n_loans.  Bit-exactness is achievable because B1 proves the
     macro inputs bit-identical and the engine is seed-deterministic;
     the committed parity gates measured diff 0.0.
  B3 per-month additivity:
     (i)  terminal identity (HALT): sum_t [m_t - sum_g m_t^g] must equal
          the committed G3 residual +0.7247122310469649 B within 1e-9 B
          absolute (pure summation-order headroom given A1 + B2; the
          committed residual is the interaction term, TOTAL - sum of
          cells = 1.0% of the marginal).
     (ii) monthly profile (EX-ANTE INTERPRETATION RULE, not a halt —
          the committed G3's own semantics, applied to the time axis):
          if max_t |cumsum residual_t| <= 10% of the committed total
          marginal (7.034 B), the month x coupon exhibit is read in
          share language ("monthly_shares_readable"); otherwise the
          decomposition is reported as approximate only, no share
          language ("approximate_only").  Both branches write the
          artifact with the verdict and max monthly / max cumulative
          residuals recorded.

PRE-COMMITTED POSTURE (unchanged from tab:theil / §V.C)
  These are fit diagnostics, NOT timing credentials: no timing claim is
  made for any estimator in any branch (peak-lag intervals span zero; the
  beta1=0 null shares Path B's -3 peak).  Expectation-setter: the Path B
  engine carries no calendar-month seasonality, so seasonal structure can
  enter the exhibits only through the empirical comparison, never through
  the simulated marginal.  Thirds shares and peak month are descriptive.

ARTIFACTS (written ONLY if all HALT gates pass)
  data/marginal_monthly_decomposition_results.json
    gates (A1/A2/B0/B1/B2/B3 measured-vs-reference + pass), part_a
    {months, m_t_b, cumulative_m_b, thirds, peak, pathB stored profile,
    derived null profile}, part_b {cells with monthly arrays + committed
    comparison, coupon_buckets with monthly/cumulative/terminal/pp,
    additivity block}, run metadata.
  figures/marginal_monthly_data.json  (figure-ready; theil_data.json
    precedent)  months, aggregate m_t + cumulative + thirds + peak,
    per-coupon-bucket m_t + cumulative + terminals, pathB/null cumulative
    error profiles, bases disclosure, posture note.

NO-TOUCH LIST (read-only inputs; this script must not modify)
  hazard/marginal_decomposition.py (imported engine; monkeypatched in
  memory, patch restored in finally, file untouched), microsim_engine.py,
  competing_risks.py, config.py, data/loan_sample.parquet,
  data/microsim_results.parquet, data/microsim_results_pq0.0.parquet,
  data/marginal_decomposition_results.json, data/no_lockin_null_results
  .json, data/extension_risk_results_literature_microsim.json,
  figures/theil_data.json.  Only the two ARTIFACTS above are written.

Run:  cd hazard && python3 marginal_monthly_decomposition.py
Runtime estimate: FRED/SOMA fetches + 17 engine legs; the committed
decomposition run took 190.2 s for the same 17 legs -> ~4-5 min total.
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
import polars as pl

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "hazard"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import marginal_decomposition as md  # committed engine — imported, never modified
from config import LOAN_SAMPLE_PATH, QT_START, RNG_SEED, ROTHSTEIN_Q_DECLINE_MID  # noqa: E402
from extension_risk import score_extension_risk  # noqa: E402
from literature_hazard import rothstein_beta1  # noqa: E402
from macro import (  # noqa: E402
    assert_qt_window_only,
    build_empirical_metrics,
    calculate_dynamic_friction,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
)
from markov import load_transition_matrix  # noqa: E402

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "marginal_monthly_decomposition_results.json"
FIGURE_JSON = _REPO / "figures" / "marginal_monthly_data.json"

CENTRAL_PARQUET = DATA_DIR / "microsim_results.parquet"
NULL_PARQUET = DATA_DIR / "microsim_results_pq0.0.parquet"
THEIL_JSON = _REPO / "figures" / "theil_data.json"
COMMITTED_CELLS_JSON = DATA_DIR / "marginal_decomposition_results.json"
NO_LOCKIN_JSON = DATA_DIR / "no_lockin_null_results.json"
EXT_LIT_JSON = DATA_DIR / "extension_risk_results_literature_microsim.json"

N_MONTHS = 42
THIRDS_SLICES = ((0, 14), (14, 28), (28, 42))  # months 1-14 / 15-28 / 29-42
THIRDS_LABELS = ("early_m01_14", "mid_m15_28", "late_m29_42")

# Committed anchors — quoted, not re-derived (marginal_decomposition.py
# convention; cross-checked against the committed JSONs at load).
TOTAL_MARGINAL_B = md.TOTAL_MARGINAL_B            # 70.34506041989584
CENTRAL_TRAPPED_B = md.CENTRAL_TRAPPED_B          # 818.5300844066606
NULL_TRAPPED_B = md.NULL_TRAPPED_B                # 748.1850239867648
EMPIRICAL_TRAPPED_B = 764.7482532227002           # ext-risk committed artifact
COMMITTED_G3_RESIDUAL_B = 0.7247122310469649      # committed interaction term

# Tolerances (rationale in the header; all pre-committed).
A1_REL_TOL = 1e-9              # sum-of-differences; measured slack 8.1e-16
A2_ABS_TOL_B = 1e-9            # profile terminal identities; measured ~1e-14
LIVE_PARITY_TOL_B = 0.01       # live-FRED/SOMA revisions headroom (G3 conv.)
SCALAR_PARITY_TOL_B = md.PARITY_TOL_B   # 1e-6 B, committed parity convention
MONTHLY_BITEXACT_TOL_B = 0.0   # capture must not perturb the sim
CELL_BITEXACT_TOL_B = 0.0      # committed parity measured diff 0.0
B3_TERMINAL_TOL_B = 1e-9       # summation-order headroom only
B3_MONTHLY_THRESHOLD_FRAC = 0.10  # committed G3 rule, applied to cum profile


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def _halt(gates: dict, msg: str) -> None:
    """GATE_FAILURE: diagnostic payload to results JSON, no figure artifact."""
    payload = {
        "mode": "marginal_monthly_decomposition",
        "status": "GATE_FAILURE",
        "failed": msg,
        "gates": gates,
        "git_commit": _git_head(),
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    raise SystemExit(
        f"GATE FAILURE — {msg}\nDiagnostic payload written to {RESULTS_JSON}; "
        "figure artifact NOT written. Withdraw, do not reinterpret."
    )


def _capturing(orig, store: list):
    """Wrap _simulate_regime: record the monthly rolloff, return the SAME frame.

    The frame object is passed through unmodified, so run_leg /
    score_extension_risk execute on bit-identical input; the recorded
    column is copied immediately so later mutation cannot reach it.
    """
    def wrapped(*args, **kwargs):
        sim = orig(*args, **kwargs)
        store.append((sim.index.copy(),
                      sim["simulated_rolloff_b"].to_numpy(dtype=float).copy()))
        return sim
    return wrapped


def main() -> None:
    t0 = time.perf_counter()
    gates: dict = {}

    # =====================================================================
    # Part A — pure arithmetic on committed artifacts (offline)
    # =====================================================================
    central_df = pd.read_parquet(CENTRAL_PARQUET)
    null_df = pd.read_parquet(NULL_PARQUET)
    assert central_df.index.equals(null_df.index), (
        "central and null parquets disagree on the monthly index")
    assert len(central_df) == N_MONTHS, (
        f"central parquet has {len(central_df)} rows, expected {N_MONTHS}")
    months = [ts.strftime("%Y-%m") for ts in central_df.index]

    central = central_df["simulated_rolloff_b"].to_numpy(dtype=float)
    null = null_df["simulated_rolloff_b"].to_numpy(dtype=float)
    m = central - null                    # monthly marginal path, $B (>0)
    cum_m = np.cumsum(m)

    # Committed-anchor cross-checks (quoted constants vs their source JSONs).
    no_lockin = json.loads(NO_LOCKIN_JSON.read_text())
    ext_lit = json.loads(EXT_LIT_JSON.read_text())
    assert no_lockin["lockin_marginal_b"] == TOTAL_MARGINAL_B
    assert no_lockin["null_trapped_b"] == NULL_TRAPPED_B
    assert no_lockin["central_trapped_b"] == CENTRAL_TRAPPED_B
    assert ext_lit["empirical_trapped_b"] == EMPIRICAL_TRAPPED_B
    assert ext_lit["hazard_trapped_b"] == CENTRAL_TRAPPED_B

    # --- GATE A1 ---------------------------------------------------------
    cols_diff = float(np.sum(central)) - float(np.sum(null))
    elem_sum = float(np.sum(m))
    a1_bitexact = cols_diff == TOTAL_MARGINAL_B
    a1_rel_err = abs(elem_sum - TOTAL_MARGINAL_B) / TOTAL_MARGINAL_B
    a1_pass = a1_bitexact and a1_rel_err <= A1_REL_TOL
    gates["A1_aggregate_reproduction"] = {
        "cols_diff_b": cols_diff,
        "committed_total_b": TOTAL_MARGINAL_B,
        "cols_diff_bitexact": bool(a1_bitexact),
        "elementwise_sum_b": elem_sum,
        "elementwise_rel_err": a1_rel_err,
        "rel_tol": A1_REL_TOL,
        "pass": bool(a1_pass),
    }
    print(f"[GATE A1] sum(central)-sum(null) = {cols_diff!r} "
          f"(bit-exact: {a1_bitexact}); sum(m_t) = {elem_sum!r} "
          f"(rel err {a1_rel_err:.2e} <= {A1_REL_TOL:.0e})  "
          f"{'PASS' if a1_pass else 'FAIL'}")
    if not a1_pass:
        _halt(gates, "A1 aggregate reproduction failed")

    # --- GATE A2 ---------------------------------------------------------
    theil = json.loads(THEIL_JSON.read_text())
    ce = theil["cumulative_error"]
    pathb_stored = np.asarray(ce["pathB"], dtype=float)
    a2_struct_ok = (
        len(pathb_stored) == N_MONTHS
        and ce["months"] == months
        and ce["terminal_b"]["pathB"] == pathb_stored[-1]
    )
    pathb_terminal = float(pathb_stored[-1])
    a2a_ref = CENTRAL_TRAPPED_B - EMPIRICAL_TRAPPED_B
    a2a_diff = pathb_terminal - a2a_ref
    null_profile = pathb_stored - cum_m           # + cumsum(null - central)
    null_terminal = float(null_profile[-1])
    a2b_ref = NULL_TRAPPED_B - EMPIRICAL_TRAPPED_B
    a2b_diff = null_terminal - a2b_ref
    a2_pass = (a2_struct_ok and abs(a2a_diff) <= A2_ABS_TOL_B
               and abs(a2b_diff) <= A2_ABS_TOL_B)
    gates["A2_null_profile_identity"] = {
        "stored_array_structure_ok": bool(a2_struct_ok),
        "pathb_terminal_stored_b": pathb_terminal,
        "pathb_terminal_ref_b": a2a_ref,
        "pathb_terminal_diff_b": a2a_diff,
        "null_terminal_derived_b": null_terminal,
        "null_terminal_ref_b": a2b_ref,
        "null_terminal_diff_b": a2b_diff,
        "abs_tol_b": A2_ABS_TOL_B,
        "convention": ("null_profile = stored pathB profile + "
                       "cumsum(null - central) = pathB - cumsum(m); "
                       "terminal = pathB terminal - total marginal"),
        "pass": bool(a2_pass),
    }
    print(f"[GATE A2] pathB terminal {pathb_terminal:+.6f} B vs committed "
          f"{a2a_ref:+.6f} B (diff {a2a_diff:+.2e}); derived null terminal "
          f"{null_terminal:+.6f} B vs committed {a2b_ref:+.6f} B "
          f"(diff {a2b_diff:+.2e}; tol {A2_ABS_TOL_B:.0e} B)  "
          f"{'PASS' if a2_pass else 'FAIL'}")
    if not a2_pass:
        _halt(gates, "A2 null-profile identity failed")

    # --- Part A report (prints only after A gates pass) ------------------
    thirds_b = [float(m[a:b].sum()) for a, b in THIRDS_SLICES]
    thirds_share = [t / elem_sum * 100.0 for t in thirds_b]
    peak_idx = int(np.argmax(m))
    print("\nPart A — monthly lock-in marginal m_t (central - null, $B):")
    for lab, tb, sh in zip(THIRDS_LABELS, thirds_b, thirds_share):
        print(f"  {lab:>13}: {tb:7.3f} B  ({sh:5.2f}%)")
    print(f"  peak month: {months[peak_idx]}  m = {m[peak_idx]:.4f} B; "
          f"m_t range [{m.min():.4f}, {m.max():.4f}] B, all positive: "
          f"{bool((m > 0).all())}")

    # =====================================================================
    # Part B — engine re-run with monthly capture
    # =====================================================================
    print("\nPart B — building macro/empirical frames (live FRED + SOMA; "
          "engine requirement, no fallback) …")
    try:
        macro_raw = fetch_data()
    except Exception as exc:
        print(f"FATAL: FRED fetch failed ({exc}). A fallback would be a "
              "spec amendment. Aborting; no artifact.")
        sys.exit(1)
    soma = fetch_soma_mbs_monthly()
    if soma is None:
        print("FATAL: NY Fed SOMA fetch failed. Refusing the WSHOMCB-diff "
              "fallback (spec: no silent fallback). Aborting; no artifact.")
        sys.exit(1)
    empirical = build_empirical_metrics(macro_raw, soma_rolloff=soma)
    macro = calculate_dynamic_friction(macro_raw)
    trans = load_transition_matrix()
    qt_start_idx = macro.index.get_indexer([QT_START], method="nearest")[0]
    holdings_b = float(macro.iloc[qt_start_idx]["WSHOMCB"]) / 1_000

    # --- GATE B0: live-input parity --------------------------------------
    qt_emp = qt_active_frame(empirical)
    assert_qt_window_only(qt_emp.index)
    if len(qt_emp) != N_MONTHS or not qt_emp.index.equals(central_df.index):
        _halt(gates, "B0: live empirical window does not match the "
                     "committed parquet index")
    soma_ok = bool((qt_emp["Rolloff_Source"] == "SOMA").all())
    emp_trapped_live = float(qt_emp["Extension_Delta_Billions"].sum())
    emp_parity_diff = emp_trapped_live - EMPIRICAL_TRAPPED_B
    actual = qt_emp["Actual_Monthly_Rolloff_Billions"].to_numpy(dtype=float)
    pathb_live = np.cumsum(central - actual)
    pathb_profile_max_diff = float(np.abs(pathb_live - pathb_stored).max())
    b0_pass = (soma_ok and abs(emp_parity_diff) <= LIVE_PARITY_TOL_B
               and pathb_profile_max_diff <= LIVE_PARITY_TOL_B)
    gates["B0_live_input_parity"] = {
        "rolloff_source_all_soma": soma_ok,
        "empirical_trapped_live_b": emp_trapped_live,
        "empirical_trapped_committed_b": EMPIRICAL_TRAPPED_B,
        "empirical_parity_diff_b": emp_parity_diff,
        "pathb_profile_max_monthly_abs_diff_b": pathb_profile_max_diff,
        "tol_b": LIVE_PARITY_TOL_B,
        "pass": bool(b0_pass),
    }
    print(f"[GATE B0] SOMA source {soma_ok}; live empirical trapped "
          f"{emp_trapped_live:.4f} B (diff {emp_parity_diff:+.2e} B); "
          f"recomputed pathB profile vs stored max |diff| "
          f"{pathb_profile_max_diff:.2e} B (tol {LIVE_PARITY_TOL_B} B)  "
          f"{'PASS' if b0_pass else 'FAIL'}")
    if not b0_pass:
        _halt(gates, "B0 live-input parity failed (live-FRED/SOMA revision "
                     "or window drift)")

    # --- Loan sample + committed cell grid --------------------------------
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)
    n_loans = len(loans)
    vintage = loans["vintage"].to_numpy()
    coupon = loans["coupon"].to_numpy()          # decimal in committed sample
    cbucket = md.coupon_bucket(coupon)
    beta1_prod = rothstein_beta1(ROTHSTEIN_Q_DECLINE_MID)
    committed = json.loads(COMMITTED_CELLS_JSON.read_text())
    committed_cells = committed["cells"]
    assert committed["gates"]["G3_additivity"]["residual_b"] == \
        COMMITTED_G3_RESIDUAL_B, "committed G3 residual anchor drifted"

    # --- Engine legs with capture (patch-and-restore) ---------------------
    captured: list = []
    orig_sim = md._simulate_regime
    md._simulate_regime = _capturing(orig_sim, captured)
    try:
        # GATE B1: parity legs (scalar + monthly bit-exact).
        print("\n[B1] central parity leg (capture active) …")
        g1_trapped = md.run_leg(loans, macro, trans, holdings_b,
                                np.full(n_loans, beta1_prod), empirical)
        g1_idx, g1_monthly = captured[-1]
        print("[B1] null parity leg (capture active) …")
        g2_trapped = md.run_leg(loans, macro, trans, holdings_b,
                                np.zeros(n_loans), empirical)
        g2_idx, g2_monthly = captured[-1]

        g1_scalar_diff = g1_trapped - CENTRAL_TRAPPED_B
        g2_scalar_diff = g2_trapped - NULL_TRAPPED_B
        idx_ok = bool(g1_idx.equals(central_df.index)
                      and g2_idx.equals(central_df.index))
        g1_monthly_max = float(np.abs(g1_monthly - central).max()) \
            if idx_ok else float("nan")
        g2_monthly_max = float(np.abs(g2_monthly - null).max()) \
            if idx_ok else float("nan")
        b1_pass = (idx_ok
                   and abs(g1_scalar_diff) <= SCALAR_PARITY_TOL_B
                   and abs(g2_scalar_diff) <= SCALAR_PARITY_TOL_B
                   and g1_monthly_max <= MONTHLY_BITEXACT_TOL_B
                   and g2_monthly_max <= MONTHLY_BITEXACT_TOL_B)
        gates["B1_parity_legs"] = {
            "index_matches_parquet": idx_ok,
            "central_scalar_b": float(g1_trapped),
            "central_scalar_diff_b": float(g1_scalar_diff),
            "null_scalar_b": float(g2_trapped),
            "null_scalar_diff_b": float(g2_scalar_diff),
            "scalar_tol_b": SCALAR_PARITY_TOL_B,
            "central_monthly_max_abs_diff_b": g1_monthly_max,
            "null_monthly_max_abs_diff_b": g2_monthly_max,
            "monthly_tol_b": MONTHLY_BITEXACT_TOL_B,
            "pass": bool(b1_pass),
        }
        print(f"[GATE B1] central {g1_trapped:.10f} B "
              f"(diff {g1_scalar_diff:+.3e}), monthly max|diff| "
              f"{g1_monthly_max:.1e}; null {g2_trapped:.10f} B "
              f"(diff {g2_scalar_diff:+.3e}), monthly max|diff| "
              f"{g2_monthly_max:.1e}  {'PASS' if b1_pass else 'FAIL'}")
        if not b1_pass:
            _halt(gates, "B1 parity failed — capture perturbed the sim or "
                         "live inputs drifted from the committed runs")

        # 15 ablation cells, EXACT committed loop order.
        print("\n[B2] 15 vintage x coupon ablation cells (capture active) …")
        cell_rows = []
        cell_monthly = np.zeros((len(committed_cells), N_MONTHS))
        i = 0
        for v in sorted(set(int(x) for x in vintage)):
            for b, lab in enumerate(md.COUPON_LABELS):
                ref = committed_cells[i]
                if (ref["vintage"], ref["coupon_bucket"]) != (v, lab):
                    _halt(gates, f"B2: cell order mismatch at index {i} "
                                 f"(got {(v, lab)}, committed "
                                 f"{(ref['vintage'], ref['coupon_bucket'])})")
                mask = (vintage == v) & (cbucket == b)
                n_g = int(mask.sum())
                if n_g != ref["n_loans"]:
                    _halt(gates, f"B2: n_loans mismatch in cell {v} {lab} "
                                 f"(got {n_g}, committed {ref['n_loans']})")
                if n_g == 0:
                    marg_b, m_g = 0.0, np.zeros(N_MONTHS)
                else:
                    vec = np.full(n_loans, beta1_prod)
                    vec[mask] = 0.0
                    trapped = md.run_leg(loans, macro, trans, holdings_b,
                                         vec, empirical)
                    idx_g, monthly_g = captured[-1]
                    if not idx_g.equals(central_df.index):
                        _halt(gates, f"B2: cell {v} {lab} index drift")
                    marg_b = CENTRAL_TRAPPED_B - trapped   # committed formula
                    m_g = central - monthly_g              # monthly marginal
                cell_monthly[i] = m_g
                cell_rows.append({
                    "vintage": v, "coupon_bucket": lab, "n_loans": n_g,
                    "balance_share_pct": ref["balance_share_pct"],
                    "marginal_b": float(marg_b),
                    "committed_marginal_b": ref["marginal_b"],
                    "diff_vs_committed_b": float(marg_b - ref["marginal_b"]),
                    "monthly_sum_minus_terminal_b": float(m_g.sum() - marg_b),
                    "monthly_marginal_b": [float(x) for x in m_g],
                })
                print(f"  {v} {lab:>9}: n={n_g:>6}  marginal {marg_b:+8.4f} B"
                      f"  (committed diff "
                      f"{marg_b - ref['marginal_b']:+.1e})")
                i += 1
    finally:
        md._simulate_regime = orig_sim

    # --- GATE B2 verdict --------------------------------------------------
    b2_max_diff = max(abs(r["diff_vs_committed_b"]) for r in cell_rows)
    b2_pass = b2_max_diff <= CELL_BITEXACT_TOL_B
    gates["B2_cell_terminal_reproduction"] = {
        "n_cells": len(cell_rows),
        "max_abs_diff_vs_committed_b": b2_max_diff,
        "tol_b": CELL_BITEXACT_TOL_B,
        "max_abs_monthly_sum_vs_terminal_b": max(
            abs(r["monthly_sum_minus_terminal_b"]) for r in cell_rows),
        "pass": bool(b2_pass),
    }
    print(f"[GATE B2] 15 cell terminals vs committed artifact: max |diff| "
          f"{b2_max_diff:.1e} B (tol {CELL_BITEXACT_TOL_B})  "
          f"{'PASS' if b2_pass else 'FAIL'}")
    if not b2_pass:
        _halt(gates, "B2 cell terminal reproduction failed")

    # --- GATE B3: per-month additivity ------------------------------------
    cells_sum_monthly = cell_monthly.sum(axis=0)
    residual_monthly = m - cells_sum_monthly
    cum_residual = np.cumsum(residual_monthly)
    terminal_residual = float(cum_residual[-1])
    b3_terminal_diff = terminal_residual - COMMITTED_G3_RESIDUAL_B
    b3_terminal_pass = abs(b3_terminal_diff) <= B3_TERMINAL_TOL_B
    max_monthly_resid = float(np.abs(residual_monthly).max())
    max_cum_resid = float(np.abs(cum_residual).max())
    b3_threshold_b = B3_MONTHLY_THRESHOLD_FRAC * TOTAL_MARGINAL_B
    b3_verdict = ("monthly_shares_readable"
                  if max_cum_resid <= b3_threshold_b else "approximate_only")
    gates["B3_per_month_additivity"] = {
        "terminal_residual_b": terminal_residual,
        "committed_residual_b": COMMITTED_G3_RESIDUAL_B,
        "terminal_diff_b": b3_terminal_diff,
        "terminal_tol_b": B3_TERMINAL_TOL_B,
        "terminal_pass": bool(b3_terminal_pass),
        "max_abs_monthly_residual_b": max_monthly_resid,
        "max_abs_cumulative_residual_b": max_cum_resid,
        "monthly_threshold_b": b3_threshold_b,
        "monthly_threshold_frac_of_total": B3_MONTHLY_THRESHOLD_FRAC,
        "verdict": b3_verdict,
        "pass": bool(b3_terminal_pass),  # verdict clause is interpretive
    }
    print(f"[GATE B3] terminal residual {terminal_residual:+.10f} B vs "
          f"committed {COMMITTED_G3_RESIDUAL_B:+.10f} B (diff "
          f"{b3_terminal_diff:+.2e}, tol {B3_TERMINAL_TOL_B:.0e})  "
          f"{'PASS' if b3_terminal_pass else 'FAIL'}")
    if not b3_terminal_pass:
        _halt(gates, "B3 terminal additivity identity failed")
    print(f"[B3 verdict] max monthly |residual| {max_monthly_resid:.4f} B, "
          f"max cumulative |residual| {max_cum_resid:.4f} B vs threshold "
          f"{b3_threshold_b:.3f} B -> {b3_verdict}")

    # --- Coupon-bucket aggregation (month x coupon exhibit) ----------------
    bench = float(score_extension_risk(central_df, empirical)
                  ["empirical_trapped_b"])
    bucket_rows = {}
    for b, lab in enumerate(md.COUPON_LABELS):
        rows_b = [i for i, r in enumerate(cell_rows)
                  if r["coupon_bucket"] == lab]
        monthly_b = cell_monthly[rows_b].sum(axis=0)
        terminal_b = float(sum(cell_rows[i]["marginal_b"] for i in rows_b))
        bucket_rows[lab] = {
            "n_loans": int(sum(cell_rows[i]["n_loans"] for i in rows_b)),
            "balance_share_pct": float(sum(
                cell_rows[i]["balance_share_pct"] for i in rows_b)),
            "terminal_marginal_b": terminal_b,
            "marginal_pp": terminal_b / bench * 100.0,
            "share_of_cells_sum_pct": terminal_b
            / float(sum(r["marginal_b"] for r in cell_rows)) * 100.0,
            "monthly_marginal_b": [float(x) for x in monthly_b],
            "cumulative_marginal_b": [float(x) for x in np.cumsum(monthly_b)],
        }
        print(f"  bucket {lab:>9}: terminal {terminal_b:+8.4f} B "
              f"({bucket_rows[lab]['marginal_pp']:+.3f} pp)")

    runtime_s = round(time.perf_counter() - t0, 1)

    # =====================================================================
    # Artifacts (all HALT gates passed)
    # =====================================================================
    part_a = {
        "months": months,
        "m_t_b": [float(x) for x in m],
        "cumulative_m_b": [float(x) for x in cum_m],
        "thirds": {
            "definition": "month index ex ante: months 1-14 / 15-28 / 29-42",
            "labels": list(THIRDS_LABELS),
            "dollars_b": thirds_b,
            "shares_pct": thirds_share,
        },
        "peak": {"month": months[peak_idx], "m_b": float(m[peak_idx]),
                 "index_1based": peak_idx + 1},
        "all_months_positive": bool((m > 0).all()),
        "pathb_cumulative_error_b_stored": [float(x) for x in pathb_stored],
        "null_cumulative_error_b_derived": [float(x) for x in null_profile],
        "profile_terminals_b": {"pathB": pathb_terminal,
                                "null": null_terminal},
    }
    payload = {
        "mode": "marginal_monthly_decomposition",
        "spec": ("round-17 R17-L (DC6 + Q7): monthly lock-in marginal path "
                 "m_t = central - null from committed parquets (Part A) + "
                 "month x coupon-cohort decomposition via monthly-capture "
                 "re-run of the committed marginal_decomposition engine "
                 "(Part B); spec fixed ex ante in the module docstring"),
        "engine": committed["engine"],
        "basis": committed["basis"],
        "posture": ("fit diagnostics, not timing credentials (tab:theil / "
                    "SV.C posture, pre-committed); the Path B engine has no "
                    "calendar-month seasonality"),
        "git_commit": _git_head(),
        "created_utc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"),
        "committed_anchors": {
            "total_marginal_b": TOTAL_MARGINAL_B,
            "central_trapped_b": CENTRAL_TRAPPED_B,
            "null_trapped_b": NULL_TRAPPED_B,
            "empirical_trapped_b": EMPIRICAL_TRAPPED_B,
            "committed_g3_residual_b": COMMITTED_G3_RESIDUAL_B,
            "sources": [
                "data/no_lockin_null_results.json",
                "data/extension_risk_results_literature_microsim.json",
                "data/marginal_decomposition_results.json",
                "figures/theil_data.json",
            ],
        },
        "gates": gates,
        "part_a": part_a,
        "part_b": {
            "cells": cell_rows,
            "coupon_buckets": bucket_rows,
            "additivity": {
                "aggregate_m_t_b": [float(x) for x in m],
                "cells_sum_monthly_b": [float(x) for x in cells_sum_monthly],
                "residual_monthly_b": [float(x) for x in residual_monthly],
                "cumulative_residual_b": [float(x) for x in cum_residual],
                "terminal_residual_b": terminal_residual,
                "verdict": b3_verdict,
            },
            "benchmark_b": bench,
        },
        "runtime_s": runtime_s,
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\nResults saved to {RESULTS_JSON}")

    figure_payload = {
        "mode": "marginal_monthly_decomposition_figure_data",
        "spec": payload["spec"],
        "window": {"start": months[0], "end": months[-1],
                   "n_months": N_MONTHS},
        "months": months,
        "aggregate": {
            "m_t_b": part_a["m_t_b"],
            "cumulative_b": part_a["cumulative_m_b"],
            "total_b": TOTAL_MARGINAL_B,
            "thirds": part_a["thirds"],
            "peak": part_a["peak"],
        },
        "coupon_buckets": {
            lab: {
                "m_t_b": bucket_rows[lab]["monthly_marginal_b"],
                "cumulative_b": bucket_rows[lab]["cumulative_marginal_b"],
                "terminal_b": bucket_rows[lab]["terminal_marginal_b"],
                "share_of_cells_sum_pct":
                    bucket_rows[lab]["share_of_cells_sum_pct"],
            } for lab in md.COUPON_LABELS
        },
        "null_vs_central": {
            "pathB_cumulative_error_b": part_a[
                "pathb_cumulative_error_b_stored"],
            "null_cumulative_error_b": part_a[
                "null_cumulative_error_b_derived"],
            "terminal_b": part_a["profile_terminals_b"],
        },
        "additivity_verdict": b3_verdict,
        "bases": {
            "m_t": ("hazard/data/microsim_results.parquet minus "
                    "hazard/data/microsim_results_pq0.0.parquet "
                    "simulated_rolloff_b (central minus beta1=0 null; "
                    "rolloff stored negative, so m_t > 0 = dollars trapped "
                    "by lock-in that month)"),
            "cells": ("group-ablation legs of hazard/"
                      "marginal_decomposition.py with monthly capture; "
                      "m_t^g = central_t - variant_g_t, committed central "
                      "parquet column (bit-identical to the captured "
                      "central parity leg, gate B1)"),
            "profiles": ("theil_data.json convention: cumulative "
                         "(simulated - SOMA actual) rolloff, $B; null "
                         "profile derived as pathB + cumsum(null - "
                         "central)"),
        },
        "gates_all_pass": True,
        "note": ("Fit diagnostics, not timing credentials (posture "
                 "pre-committed): no timing claim is made for any "
                 "estimator; the engine carries no calendar-month "
                 "seasonality, so seasonal structure enters only through "
                 "the empirical comparison. Feeds the R17-L month x "
                 "coupon exhibit (fig11 companion) and app:theil null "
                 "profile row."),
    }
    FIGURE_JSON.write_text(
        json.dumps(figure_payload, indent=2, default=float) + "\n")
    print(f"Figure data saved to {FIGURE_JSON}")
    print(f"\nAll gates PASS; verdict {b3_verdict}; runtime {runtime_s} s")


if __name__ == "__main__":
    main()
