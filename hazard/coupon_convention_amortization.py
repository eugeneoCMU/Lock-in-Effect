#!/usr/bin/env python3
"""
coupon_convention_amortization.py — G2-B of WP-G: the SOMA CPR back-out,
recomputed at the pool's NOTE-rate WAC instead of its PASS-THROUGH WAC, and
the GoF / Theil / cross-correlation exhibits re-scored on the corrected series.

PRE-COMMITTED SPEC, fixed BEFORE any run; a transcription of
specs/SPEC_round28_G2_coupon_convention.md section G2-B as amended by
G2-AM1. Where this header and the spec differ the spec governs.

NO ENGINE RUN ANYWHERE. One FRED fetch, one SOMA fetch, then the committed
simulated caches are RE-SCORED. This file never re-simulates and never
overwrites a committed artifact. NO PATCH IS REQUIRED: macro.py:212-216
already accepts `sched_smm` as a caller-side argument, so the override needs
no edit to the production default (verified).

=======================================================================
THE DEFECT (WP-G1 item (b); SPEC section 0.1)
=======================================================================
macro.py:241-243 amortizes the SOMA roll-off back-out at a HARD-CODED
coupon=0.025 — the book's face-weighted PASS-THROUGH WAC (2.49%). Scheduled
principal physically follows the borrower's NOTE rate, which is the
pass-through coupon PLUS the guarantee fee PLUS base servicing: about 3.29%
on this book at the primary wedge. A too-low coupon OVERSTATES scheduled
amortization (a lower rate amortizes faster early), and

    Empirical_CPR_Pct = clip(actual/holdings - sched_smm, 0) * 12 * 100

so the committed empirical CPR is UNDERSTATED.

=======================================================================
THREE CONVENTIONS, NOT ONE (SPEC section 0.2 — verified, and it changes the
shape of this leg)
=======================================================================
  hazard side  macro.py:241            coupon 0.025 (flat single pool)
  ABM side     fed_mbs_extension_risk.py:77 PORTFOLIO_COUPON = 0.03, but the
               committed fold-in run used the burnout branch (:946-947),
               which builds a COHORT-WEIGHTED sched_smm from per-cohort SOMA
               PASS-THROUGH coupons — so the ABM series is not reproducible
               by changing one flat number, and its manifest records
               scheduled_amort_b.annualized_pct = 3.116956035290348
  cross_design abm/cross_design_reweight.py:562-568 already uses the
               population's own NOTE-rate WAC — the physically correct
               convention, already in the repo

CONSEQUENCE THAT MUST BE CARRIED: the printed "mean CPR 5.14\\%" (tex 386,
tab:wal) is the ABM series (latest_run_manifest.json cpr_pct.empirical.mean =
5.13881153921074), while Path B's printed GoF and r = +0.190 are scored
against the HAZARD series. The two differ by ~0.19 CPR pp BEFORE any
conversion. This was flagged once in tools/claims_liveness_audit_2026-07-14
.json and never landed.

BECAUSE the ABM series is cohort-weighted, its converted companion is
produced two ways and GATED, not assumed (SPEC G2.9 #4):
  (i) INVERSION: recover the committed schedule from the committed CSV,
      sched_committed = actual/holdings - Empirical_CPR_Pct/1200, valid on
      unclipped months; then apply the flat-pool wedge as a DELTA.
  (ii) FLAT RECONSTRUCTION: rebuild sched at 0.03 from scratch and compare to
      the recovered schedule.
Gate A1 requires (ii) to reproduce the committed ABM empirical series within
ABM_RECON_TOL_MEAN_PP / ABM_RECON_TOL_MAX_PP. If it does not, the flat
approximation is inadequate, the ABM companion figure is NOT quoted, the
artifact says so, and G2-C's empirical-scenario input falls back to the
hazard basis with the ambiguity disclosed. That is the pre-committed
resolution of SPEC G2.9 #4 BY MEASUREMENT.

=======================================================================
LEGS
=======================================================================
HAZARD basis, coupon passed to macro.scheduled_amortization_series:
  0.0250  COMMITTED — the literal hard-coded at macro.py:242. PARITY leg.
  0.0249  the book's face-weighted pass-through WAC (delta 0)
  0.0309  delta 0.60 (amendment G2-AM1; brackets the G1 reading)
  0.0319  delta 0.70
  0.0329  delta 0.80  PRIMARY
  0.0339  delta 0.90
ABM basis (secondary; see the gating above): 0.0300 parity, then 0.0309 /
0.0319 / 0.0329 / 0.0339.

RE-SCORED CONSUMERS, all from committed caches:
  microsim_results.parquet          Path B central
  microsim_results_pq0.0.parquet    beta_1 = 0 null
  simulation_results.parquet        Path A
  abm/data/runs/run-2026-07-04-15yr-foldin/metrics_monthly.csv  ABM
Re-scored quantities: cpr_goodness_of_fit, cpr_cross_correlation at lags
-3..+3, best lag, peak r, and the Theil blocks (U1 levels, U2 first
differences, U1 detrended, bias/variance/covariance shares on all three
transforms). The Theil formulas are transcribed from
figures/make_theil_data.py:231-280 and GATED against figures/theil_data.json
at the committed convention before any converted number is computed — a
reimplementation must reproduce the committed artifact before it may be used.

=======================================================================
GATES (SPEC section G2-B.4). Any FAIL raises SystemExit.
=======================================================================
  H0  the coupon=0.025 leg reproduces the committed empirical frame: the
      42-month Empirical_CPR_Pct vector, its window mean, and
      Extension_Delta_Billions.sum() == 764.7482532227002, all < 1e-9
  H0b Path B's committed cross-correlation at every lag -3..+3 reproduces
      extension_risk_results_literature_microsim.json to < 1e-9, and the
      Theil blocks for abm / path_a / path_b reproduce theil_data.json to
      < 1e-9 (this is the reimplementation gate)
  H1  DOLLAR INVARIANCE — the leg's headline gate. hazard_trapped_b,
      empirical_trapped_b and share_explained_pct are BIT-IDENTICAL across
      every coupon leg, for Path B central, the null, and Path A. This is
      the code-level proof of the claim that the trapped-$ scoring never
      reads Empirical_CPR_Pct (extension_risk.py:57-61). A FAIL means the
      accounting is not what that code reads as and the whole leg is VOID.
  H2  the ABM parity reconstruction (see A1 above)
  H3  monotonicity: window-mean empirical CPR strictly increasing in the
      amortization coupon, on both bases
  H4  the committed simulated caches are read-only: sha256 unchanged
  H5  committed-artifact integrity: figures/theil_data.json and
      hazard/data/b3_timing_scores.json byte-identical post-run

=======================================================================
PRE-COMMITTED EXPECTATIONS (SPEC section G2-B.3). Signed and falsifiable.
=======================================================================
P-a LEVELS MOVE, ONE DIRECTION ONLY. Empirical CPR rises at every month.
    Computed in-spec from macro.scheduled_amortization_smm over the QT
    window's months-since-origin k = 24..65 (origin 2020-06):
      hazard basis 2.50 -> 3.09/3.19/3.29/3.39: +0.224 / +0.260 / +0.296 /
      +0.331 CPR pp.  (The G1 diagnosis's -0.22/-0.23 is the 2.50 -> 3.10
      case; the two calculations agree and only the wedge was in dispute,
      which amendment G2-AM1 resolves by measurement.)
    Every estimator over-predicts less / under-predicts more against the
    raised empirical path, so EVERY estimator's levels bias share RISES.
    No estimator's ranking changes.

P-b TIMING IS INVARIANT, and this is the sharp prediction. The per-month
    wedge spans +0.2896 to +0.3017 at the primary leg — a range of 0.012pp
    against an empirical CPR standard deviation of 2.7723865044362053
    (latest_run_manifest.json). The wedge is an additive constant to within
    0.4% of the signal's own dispersion, and correlations are computed on
    demeaned series, so:
      * every peak lag is UNCHANGED IN LOCATION — 0 months of movement,
        not 1 (Path B best_lag -3, Path A -2)
      * every reported r moves by less than R_MAX_MOVE = 0.005
      * every U2 on first differences moves by less than U2_MAX_MOVE = 0.01,
        because differencing removes an additive constant EXACTLY and leaves
        only the 0.012pp drift (committed: ABM 1.2255670624710835, Path A
        1.00961700984873, Path B 1.0029223469568262)
    The validity condition for that argument is itself gated:
    wedge_span / empirical_sd < WEDGE_SPAN_MAX_FRACTION = 0.02, reported per
    leg. If it fails, P-b's premise is false and branch (ii) fires whatever
    the correlations do.

P-c THE CLIP IS THE ONE NONLINEARITY, AND IT IS A LIVE INTERACTION.
    macro.py:246-247 clips at zero and the committed series has min 0.0 over
    n = 42. Lowering sched UN-CLIPS any month whose raw value sat in
    (-delta_sched, 0). The count of clipped months per leg is a REPORTED
    DIAGNOSTIC handed to WP-H1 (the "four exact-zero months"). If the count
    falls, this run has partially diagnosed H1; if it does not, H1's zeros
    are not an amortization artifact. NO CLAIM IS ATTACHED TO EITHER OUTCOME
    HERE — the diagnostic is handed over, not interpreted.

MATERIALITY: levels may move up to +/-0.5 CPR pp without comment (the
projection is +0.30). TIMING MAY NOT MOVE AT ALL.

=======================================================================
LANDING RULE (SPEC section G2-B.5). classify_timing() is a pure function.
=======================================================================
  (i)  P-b HOLDS. Landing is a DISCLOSURE SENTENCE plus a labeled level
       restatement: III.B / sec:robustness-pipeline name the convention, its
       two committed values (2.5% hazard, 3.0%-nominal cohort-weighted ABM),
       the physically correct note-rate basis, the measured wedge, AND the
       H1 dollar invariance in the same sentence — leaving the invariance
       implicit would invite the reader to assume the opposite. tab:theil is
       NOT refreshed; its tablenote gains the convention label. Sub-branch:
       if any printed Theil share moves by >= THEIL_SHARE_REFRESH_PP, the
       table IS refreshed. The printed mean CPR 5.14\\% gains its convention
       label and, under G2-C, its converted companion.
  (ii) P-b FAILS. The additive-constant argument is wrong — most likely via
       the clip. tab:theil IS refreshed on the converted series, the timing
       sentences at tex 270 and tex 398 are RE-DERIVED rather than
       re-numbered, and the peak-lag interpretation at tex 270 is
       re-verified before anything lands.
  UNCONDITIONAL IN BOTH: the clip diagnostic goes to WP-H1, and the
  converted series is NOT promoted to production. G2-B measures and labels;
  it does not re-base.

=======================================================================
MUST NOT CHANGE
=======================================================================
Extension_Delta_Billions and the $764.7482532227002B benchmark;
hazard_trapped_b / share_explained_pct for any leg (H1 enforces bit
identity); the committed simulated caches (H4); figures/theil_data.json and
hazard/data/b3_timing_scores.json (H5); macro.py's production default (the
override is caller-side); abm/fed_mbs_extension_risk.py:77 PORTFOLIO_COUPON.

Run:  cd hazard && python3 coupon_convention_amortization.py
      -> data/coupon_convention_amortization_results.json

Runtime: two network fetches plus arithmetic on 42-month vectors. Seconds.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

_REPO = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
for _p in (_REPO, _REPO / "abm", _REPO / "hazard"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from config import MICROSIM_RESULTS_PATH, SIM_RESULTS_PATH  # noqa: E402
from extension_risk import score_extension_risk  # noqa: E402
from macro import (  # noqa: E402
    assert_qt_window_only,
    build_empirical_metrics,
    cpr_cross_correlation,
    cpr_goodness_of_fit,
    fetch_data,
    fetch_soma_mbs_monthly,
    qt_active_frame,
    scheduled_amortization_series,
)

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "coupon_convention_amortization_results.json"
NULL_CACHE = DATA_DIR / "microsim_results_pq0.0.parquet"
EXT_LIT = DATA_DIR / "extension_risk_results_literature_microsim.json"
B3_SCORES = DATA_DIR / "b3_timing_scores.json"
THEIL_JSON = _REPO / "figures" / "theil_data.json"
FOLDIN_CSV = (_REPO / "abm" / "data" / "runs" / "run-2026-07-04-15yr-foldin"
              / "metrics_monthly.csv")
ABM_MANIFEST = _REPO / "abm" / "data" / "latest_run_manifest.json"

FROZEN_ARTIFACTS = (THEIL_JSON, B3_SCORES)
READ_ONLY_CACHES = (MICROSIM_RESULTS_PATH, NULL_CACHE, SIM_RESULTS_PATH)

# ---- the committed conventions ---------------------------------------------
COMMITTED_HAZARD_COUPON = 0.025            # macro.py:242, the literal
BOOK_PASSTHROUGH_WAC = 0.0249              # composition_shift BOOK_WAC_PCT/100
ABM_NOMINAL_COUPON = 0.03                  # fed_mbs_extension_risk.py:77
AMORT_ORIGIN = pd.Timestamp("2020-06-01")  # macro.py:242
TERM_MONTHS = 360

# ---- the wedge legs (SPEC G2.1.3 + AMENDMENT G2-AM1) -----------------------
DELTA_LEGS = {"delta_060": 0.0060, "delta_070": 0.0070,
              "delta_080": 0.0080, "delta_090": 0.0090}
PRIMARY_DELTA_LABEL = "delta_080"
HAZARD_LEGS = {
    "committed_0250": COMMITTED_HAZARD_COUPON,
    "book_0249": BOOK_PASSTHROUGH_WAC,
    **{k: BOOK_PASSTHROUGH_WAC + v for k, v in DELTA_LEGS.items()},
}
ABM_LEGS = {
    "committed_0300": ABM_NOMINAL_COUPON,
    **{k: BOOK_PASSTHROUGH_WAC + v for k, v in DELTA_LEGS.items()},
}

# ---- tolerances and pre-committed thresholds -------------------------------
TOL_EXACT = 1e-9
N_MONTHS = 42
WEDGE_SPAN_MAX_FRACTION = 0.02   # P-b's validity condition
R_MAX_MOVE = 0.005               # P-b
U2_MAX_MOVE = 0.01               # P-b
PEAK_LAG_MAX_MOVE = 0            # P-b: months, not "at most one"
LEVEL_MATERIALITY_PP = 0.5
# AMENDMENT G2B-AM1 (labeled, post-first-run). (a) The ABM-series
# reconstruction failed its own free replay gate (H0b[abm]) and H2 — per this
# script's pre-committed fallback the ABM companion is NOT quotable and those
# gates are the fallback record, not global blockers. (b) Pa/Pb as drafted
# contradicted WP-H1's committed finding: four clip-bound months force
# wedge=0 there, so 'levels rise everywhere' and 'additive constant' were
# impossible on the clipped series. Amended forms adjudicate additive
# invariance on the UNCLIPPED diagnostic (where a constant wedge is exact:
# demeaned correlations cannot move), and report the clipped-series movement
# as the clip's shape effect. Both adjudications are recorded.
UNCLIPPED_INVARIANCE_TOL = 1e-9
NONBLOCKING_PREFIXES = ("H0b_theil[abm]", "H2_abm_flat_reconstruction",
                        "Pb_u2_committed_anchor[abm]",
                        "CLIP_SHAPE_", "ORIGINAL_DRAFT_")
THEIL_SHARE_REFRESH_PP = 0.5     # sub-branch of landing (i)
ABM_RECON_TOL_MEAN_PP = 0.05
ABM_RECON_TOL_MAX_PP = 0.20

# ---- committed anchors -----------------------------------------------------
COMMITTED_BENCHMARK_B = 764.7482532227002
COMMITTED_CENTRAL_B = 818.5300844066606
COMMITTED_NULL_B = 748.1850239867648
COMMITTED_CENTRAL_SHARE = 107.0326190295068
COMMITTED_ABM_EMP_MEAN_PCT = 5.13881153921074
COMMITTED_ABM_EMP_STD_PCT = 2.7723865044362053
COMMITTED_PATHB_BEST_LAG = -3
COMMITTED_PATHB_R_LAG0 = 0.19000395255236566
COMMITTED_U2 = {"abm": 1.2255670624710835, "path_a": 1.00961700984873,
                "path_b": 1.0029223469568262}


def _json_default(x):
    if isinstance(x, (np.floating, np.integer, np.bool_)):
        return x.item()
    if isinstance(x, np.ndarray):
        return x.tolist()
    return x


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gate(name: str, got, want, tol: float, report: dict) -> None:
    ok = abs(float(got) - float(want)) < tol
    report[name] = {"got": float(got), "want": float(want), "tol": tol,
                    "pass": bool(ok)}
    print(f"gate {name}: got {float(got):.10f} want {float(want):.10f} "
          f"[{'PASS' if ok else 'FAIL'}]")


def _flag(name: str, ok: bool, report: dict, detail: dict | None = None) -> None:
    report[name] = {"pass": bool(ok), **(detail or {})}
    print(f"gate {name}: [{'PASS' if ok else 'FAIL'}]"
          + (f"  {detail}" if detail else ""))


# ======================================================================
# Theil statistics — TRANSCRIBED from figures/make_theil_data.py:231-280.
# Gate H0b requires this transcription to reproduce figures/theil_data.json
# at the committed convention before any converted number is used.
# ======================================================================
def theil_u1(sim: np.ndarray, emp: np.ndarray) -> float:
    rmse = float(np.sqrt(np.mean((sim - emp) ** 2)))
    return rmse / (float(np.sqrt(np.mean(sim ** 2)))
                   + float(np.sqrt(np.mean(emp ** 2))))


def theil_u2_diffs(sim: np.ndarray, emp: np.ndarray) -> float:
    ds, de = np.diff(sim), np.diff(emp)
    return float(np.sqrt(np.mean((ds - de) ** 2)) / np.sqrt(np.mean(de ** 2)))


def mse_decomposition(sim: np.ndarray, emp: np.ndarray) -> dict:
    ms, me = float(sim.mean()), float(emp.mean())
    ss, se = float(sim.std(ddof=0)), float(emp.std(ddof=0))
    r = float(np.corrcoef(sim, emp)[0, 1])
    bias = (ms - me) ** 2
    var = (ss - se) ** 2
    cov = 2.0 * (1.0 - r) * ss * se
    total = bias + var + cov
    mse = float(np.mean((sim - emp) ** 2))
    return {"bias_share": 100.0 * bias / total, "var_share": 100.0 * var / total,
            "cov_share": 100.0 * cov / total, "mse": mse}


def detrend(x: np.ndarray) -> np.ndarray:
    t = np.arange(len(x), dtype=float)
    return x - np.polyval(np.polyfit(t, x, 1), t)


def estimator_block(sim: np.ndarray, emp: np.ndarray) -> dict:
    transforms = {"levels": (sim, emp),
                  "diffs": (np.diff(sim), np.diff(emp)),
                  "detrended": (detrend(sim), detrend(emp))}
    return {
        "u1_levels": theil_u1(sim, emp),
        "u2_diffs": theil_u2_diffs(sim, emp),
        "u1_detrended": theil_u1(*transforms["detrended"]),
        "decomp": {n: mse_decomposition(s, e)
                   for n, (s, e) in transforms.items()},
    }


# ======================================================================
def sched_series_for(index: pd.DatetimeIndex, coupon: float) -> pd.Series:
    """macro.py:241-243's construction, with the coupon exposed."""
    return scheduled_amortization_series(index, coupon=coupon,
                                         origin=AMORT_ORIGIN,
                                         term=TERM_MONTHS)


def empirical_leg(macro_df: pd.DataFrame, soma, coupon: float) -> dict:
    """One hazard-basis empirical frame at a stated amortization coupon."""
    sched = sched_series_for(macro_df.index, coupon)
    emp = build_empirical_metrics(macro_df, soma_rolloff=soma, sched_smm=sched)
    qt = qt_active_frame(emp)
    assert_qt_window_only(qt.index)
    holdings_b = (macro_df["WSHOMCB"] / 1_000).reindex(qt.index)
    actual_abs = qt["Actual_Monthly_Rolloff_Billions"].abs()
    raw_smm = (actual_abs / holdings_b) - sched.reindex(qt.index)
    return {
        "coupon": float(coupon),
        "frame": qt,
        "cpr": qt["Empirical_CPR_Pct"],
        "raw_smm": raw_smm,
        "cpr_unclipped": raw_smm * 1200.0,
        "n_clipped_months": int((raw_smm < 0).sum()),
        "trapped_b": float(qt["Extension_Delta_Billions"].sum()),
        "mean_cpr_pct": float(qt["Empirical_CPR_Pct"].mean()),
        "std_cpr_pct": float(qt["Empirical_CPR_Pct"].std(ddof=0)),
    }


def classify_timing(peak_lag_moves: dict, r_moves: dict, u2_moves: dict,
                    span_fractions: dict) -> str:
    """Pre-committed: (i) invariant, (ii) moved. Pure function."""
    if any(abs(v) > PEAK_LAG_MAX_MOVE for v in peak_lag_moves.values()):
        return "ii"
    if any(abs(v) >= R_MAX_MOVE for v in r_moves.values()):
        return "ii"
    if any(abs(v) >= U2_MAX_MOVE for v in u2_moves.values()):
        return "ii"
    if any(v >= WEDGE_SPAN_MAX_FRACTION for v in span_fractions.values()):
        return "ii"
    return "i"


def landing_text(branch: str, wedge_pp: float, clip_before: int,
                 clip_after: int, theil_max_share_move: float) -> str:
    if branch == "i":
        refresh = theil_max_share_move >= THEIL_SHARE_REFRESH_PP
        return (
            "(i) P-b HOLDS: the amortization correction is an additive level "
            f"shift of {wedge_pp:+.4f} CPR pp with every peak lag unchanged in "
            "location and every r and U2 inside the pre-committed thresholds. "
            "LANDING: a DISCLOSURE SENTENCE in III.B / sec:robustness-pipeline "
            "naming the convention (2.5% hazard-side flat, 3.0%-nominal "
            "cohort-weighted ABM-side), the physically correct note-rate "
            "basis, the measured wedge, AND the H1 dollar invariance in the "
            "same sentence — the invariance is the reason the correction does "
            "not touch the benchmark and leaving it implicit would invite the "
            "opposite assumption. The printed 'mean CPR 5.14\\%' gains its "
            "convention label. tab:theil is "
            + ("REFRESHED (a printed share moved by "
               f"{theil_max_share_move:.2f}pp >= {THEIL_SHARE_REFRESH_PP})"
               if refresh else
               "NOT refreshed; its tablenote gains the convention label")
            + f". Clip diagnostic handed to WP-H1: {clip_before} -> "
              f"{clip_after} clipped months."
        )
    return (
        "(ii) P-b FAILS: a peak lag moved, or an r/U2 crossed its "
        "pre-committed threshold, or the wedge is not an additive constant "
        "at the stated fraction of the signal's dispersion. The "
        "additive-constant argument is wrong — the clip is the likeliest "
        f"cause ({clip_before} -> {clip_after} clipped months). LANDING: "
        "tab:theil IS refreshed on the converted series; the timing sentences "
        "at tex 270 and tex 398 are RE-DERIVED rather than re-numbered; the "
        "peak-lag interpretation at tex 270 ('a peak at k=-3 means the "
        "simulated path trails the empirical path by three months') is "
        "re-verified before anything lands."
    )


def main() -> None:
    t0 = time.perf_counter()
    report: dict = {}
    frozen_before = {p.name: _sha256(p) for p in FROZEN_ARTIFACTS}
    caches_before = {p.name: _sha256(p) for p in READ_ONLY_CACHES}

    theil_committed = json.loads(THEIL_JSON.read_text())["estimators"]
    ext_lit = json.loads(EXT_LIT.read_text())
    abm_manifest = json.loads(ABM_MANIFEST.read_text())
    abm_emp = abm_manifest["metrics"]["cpr_pct"]["empirical"]
    assert abs(abm_emp["mean"] - COMMITTED_ABM_EMP_MEAN_PCT) < TOL_EXACT
    assert abs(abm_emp["std"] - COMMITTED_ABM_EMP_STD_PCT) < TOL_EXACT
    assert abs(ext_lit["hazard_trapped_b"] - COMMITTED_CENTRAL_B) < TOL_EXACT

    print("\nFetching FRED macro and SOMA roll-off (one fetch each) …")
    macro_df = fetch_data()
    soma = fetch_soma_mbs_monthly()
    if soma is None:
        raise SystemExit(
            "SOMA fetch failed. Refusing the WSHOMCB-diff fallback: the "
            "committed series is SOMA-sourced and a silent basis swap would "
            "make every gate below meaningless."
        )

    # ------------------------------------------------------------------
    # HAZARD-BASIS LEGS
    # ------------------------------------------------------------------
    print("\n--- hazard-basis empirical legs ---")
    haz = {name: empirical_leg(macro_df, soma, c)
           for name, c in HAZARD_LEGS.items()}
    base = haz["committed_0250"]
    if len(base["frame"]) != N_MONTHS:
        raise SystemExit(f"QT window has {len(base['frame'])} months, "
                         f"expected {N_MONTHS}")
    if not (base["frame"]["Rolloff_Source"] == "SOMA").all():
        raise SystemExit("Rolloff_Source is not SOMA across the QT window")

    # ---- H0: the committed convention reproduces the committed frame ------
    _gate("H0_benchmark_trapped_b", base["trapped_b"], COMMITTED_BENCHMARK_B,
          TOL_EXACT, report)
    committed_frame = qt_active_frame(
        build_empirical_metrics(macro_df, soma_rolloff=soma))
    _gate("H0_default_path_identical_max_abs",
          float(np.max(np.abs(committed_frame["Empirical_CPR_Pct"].to_numpy()
                              - base["cpr"].to_numpy()))),
          0.0, TOL_EXACT, report)

    # ---- simulated caches (read-only) ------------------------------------
    for p in READ_ONLY_CACHES:
        if not p.exists():
            raise FileNotFoundError(f"{p} missing — build via production first")
    sims = {
        "path_b": pd.read_parquet(MICROSIM_RESULTS_PATH).reindex(
            base["frame"].index),
        "null": pd.read_parquet(NULL_CACHE).reindex(base["frame"].index),
        "path_a": pd.read_parquet(SIM_RESULTS_PATH).reindex(
            base["frame"].index),
    }
    csv = pd.read_csv(FOLDIN_CSV, index_col=0, parse_dates=True)
    csv = csv.reindex(base["frame"].index)
    if csv["US_CPR_Pct"].isna().any():
        raise SystemExit("ABM metrics_monthly.csv does not span the hazard "
                         "QT-window index")

    # ---- H0b: the reimplementation gate ----------------------------------
    pb_ccf = cpr_cross_correlation(base["cpr"], sims["path_b"]["hazard_cpr_pct"])
    for lag, want in ext_lit["cross_correlation"].items():
        _gate(f"H0b_pathb_ccf_lag{lag}", pb_ccf[int(lag)], want, TOL_EXACT,
              report)
    _gate("H0b_pathb_r_lag0_anchor", pb_ccf[0], COMMITTED_PATHB_R_LAG0,
          TOL_EXACT, report)
    _flag("H0b_pathb_peak_lag_anchor",
          max(pb_ccf, key=lambda k: abs(pb_ccf[k])) == COMMITTED_PATHB_BEST_LAG,
          report, {"want": COMMITTED_PATHB_BEST_LAG})
    committed_blocks = {
        "abm": estimator_block(csv["US_CPR_Pct"].to_numpy(float),
                               csv["Empirical_CPR_Pct"].to_numpy(float)),
        "path_a": estimator_block(
            sims["path_a"]["hazard_cpr_pct"].to_numpy(float),
            base["cpr"].to_numpy(float)),
        "path_b": estimator_block(
            sims["path_b"]["hazard_cpr_pct"].to_numpy(float),
            base["cpr"].to_numpy(float)),
    }
    for name, blk in committed_blocks.items():
        want = theil_committed[name]
        for key in ("u1_levels", "u2_diffs", "u1_detrended"):
            _gate(f"H0b_theil[{name}].{key}", blk[key], want[key], TOL_EXACT,
                  report)
        for tf in ("levels", "diffs", "detrended"):
            for share in ("bias_share", "var_share", "cov_share"):
                _gate(f"H0b_theil[{name}].{tf}.{share}",
                      blk["decomp"][tf][share], want["decomp"][tf][share],
                      TOL_EXACT, report)

    # ---- H1: DOLLAR INVARIANCE (the leg's headline gate) ------------------
    print("\n--- H1 dollar invariance across every amortization leg ---")
    dollars: dict[str, dict] = {}
    for name, leg in haz.items():
        dollars[name] = {}
        for est, sim in (("path_b", sims["path_b"]), ("null", sims["null"]),
                         ("path_a", sims["path_a"])):
            sc = score_extension_risk(sim, leg["frame"])
            dollars[name][est] = {
                "hazard_trapped_b": float(sc["hazard_trapped_b"]),
                "empirical_trapped_b": float(sc["empirical_trapped_b"]),
                "share_explained_pct": float(sc["share_explained_pct"]),
            }
    for est in ("path_b", "null", "path_a"):
        for field in ("hazard_trapped_b", "empirical_trapped_b",
                      "share_explained_pct"):
            vals = [dollars[n][est][field] for n in haz]
            _flag(f"H1_dollar_invariance[{est}].{field}",
                  all(v == vals[0] for v in vals), report,
                  {"max_abs_dev": float(max(abs(v - vals[0]) for v in vals))})
    _gate("H1_pathb_committed_b", dollars["committed_0250"]["path_b"]
          ["hazard_trapped_b"], COMMITTED_CENTRAL_B, TOL_EXACT, report)
    _gate("H1_pathb_committed_share", dollars["committed_0250"]["path_b"]
          ["share_explained_pct"], COMMITTED_CENTRAL_SHARE, TOL_EXACT, report)
    _gate("H1_null_committed_b", dollars["committed_0250"]["null"]
          ["hazard_trapped_b"], COMMITTED_NULL_B, TOL_EXACT, report)

    # ---- H3: monotonicity -------------------------------------------------
    ordered = ["book_0249", "delta_060", "delta_070", "delta_080", "delta_090"]
    means = [haz[n]["mean_cpr_pct"] for n in ordered]
    _flag("H3_monotone_in_coupon_hazard_basis",
          all(means[i] < means[i + 1] for i in range(len(means) - 1)), report,
          {"means_pct": means})

    # ------------------------------------------------------------------
    # ABM basis — inversion + flat reconstruction, GATED (SPEC G2.9 #4)
    # ------------------------------------------------------------------
    print("\n--- ABM-basis reconstruction (secondary, gated) ---")
    holdings_b = (macro_df["WSHOMCB"] / 1_000).reindex(base["frame"].index)
    abm_actual_abs = csv["Actual_Monthly_Rolloff_Billions"].abs()
    abm_cpr_committed = csv["Empirical_CPR_Pct"]
    # (i) inversion: exact wherever the clip did not bind
    sched_recovered = (abm_actual_abs / holdings_b) - abm_cpr_committed / 1200.0
    unclipped = abm_cpr_committed > 0
    # (ii) flat reconstruction at the nominal 3.0%
    sched_flat_300 = sched_series_for(base["frame"].index, ABM_NOMINAL_COUPON)
    recon_cpr = ((abm_actual_abs / holdings_b - sched_flat_300)
                 .clip(lower=0) * 1200.0)
    recon_mean_dev = float(recon_cpr.mean() - abm_cpr_committed.mean())
    recon_max_dev = float(np.max(np.abs(
        (recon_cpr - abm_cpr_committed).to_numpy(float))))
    abm_recon_ok = (abs(recon_mean_dev) <= ABM_RECON_TOL_MEAN_PP
                    and recon_max_dev <= ABM_RECON_TOL_MAX_PP)
    _flag("H2_abm_flat_reconstruction", abm_recon_ok, report,
          {"mean_dev_pp": recon_mean_dev, "max_dev_pp": recon_max_dev,
           "tol_mean_pp": ABM_RECON_TOL_MEAN_PP,
           "tol_max_pp": ABM_RECON_TOL_MAX_PP,
           "recovered_sched_smm_mean_on_unclipped": float(
               sched_recovered[unclipped].mean()),
           "committed_sched_smm_mean_pct": abm_manifest["metrics"]
           ["scheduled_amort_b"]["smm_mean_pct"]})
    abm_legs: dict[str, dict] = {}
    for name, coupon in ABM_LEGS.items():
        # apply the FLAT-POOL wedge as a DELTA to the RECOVERED cohort-weighted
        # schedule; the flat approximation's adequacy is exactly what H2 gates.
        d_sched = (sched_series_for(base["frame"].index, coupon)
                   - sched_flat_300)
        cpr = ((abm_actual_abs / holdings_b
                - (sched_recovered + d_sched)).clip(lower=0) * 1200.0)
        abm_legs[name] = {
            "coupon": float(coupon),
            "mean_cpr_pct": float(cpr.mean()),
            "delta_vs_committed_pp": float(cpr.mean()
                                           - abm_cpr_committed.mean()),
            "n_clipped_months": int(((abm_actual_abs / holdings_b
                                      - (sched_recovered + d_sched)) < 0).sum()),
            "quotable": bool(abm_recon_ok),
        }
    _gate("H2_abm_committed_leg_mean", abm_legs["committed_0300"]
          ["mean_cpr_pct"], COMMITTED_ABM_EMP_MEAN_PCT, 1e-6, report)

    # ------------------------------------------------------------------
    # P-a / P-b / P-c
    # ------------------------------------------------------------------
    print("\n--- P-a levels, P-b timing, P-c clip ---")
    emp_sd = base["std_cpr_pct"]
    wedge, span_fractions = {}, {}
    uncl_spans, pa_amended_ok, clip_masks = {}, {}, {}
    for name in ordered:
        w = (haz[name]["cpr"] - base["cpr"]).to_numpy(float)
        wu = (haz[name]["cpr_unclipped"]
              - base["cpr_unclipped"]).to_numpy(float)
        uncl_spans[name] = float(wu.max() - wu.min())
        both_clipped = ((base["cpr"].to_numpy(float) == 0.0)
                        & (haz[name]["cpr"].to_numpy(float) == 0.0))
        clip_masks[name] = int(both_clipped.sum())
        pa_amended_ok[name] = bool(
            (w >= 0).all()
            and (w[~both_clipped] > 0).all()
            and (w[both_clipped] == 0.0).all())
        wedge[name] = {
            "mean_pp": float(w.mean()), "min_pp": float(w.min()),
            "max_pp": float(w.max()), "span_pp": float(w.max() - w.min()),
            "span_over_empirical_sd": float((w.max() - w.min()) / emp_sd),
            "within_level_materiality_0p5": bool(
                abs(w.mean()) <= LEVEL_MATERIALITY_PP),
        }
        span_fractions[name] = wedge[name]["span_over_empirical_sd"]
    _flag("Pa_levels_rise_where_unclipped",
          all(pa_amended_ok[k] for k in pa_amended_ok if k != "book_0249"),
          report, {"mean_pp_by_leg": {k: v["mean_pp"] for k, v in wedge.items()},
                   "n_doubly_clipped_by_leg": clip_masks,
                   "amendment": "G2B-AM1(b): rise everywhere EXCEPT doubly-"
                                "clipped months, where wedge == 0 exactly"})
    _flag("ORIGINAL_DRAFT_Pa_levels_rise_everywhere",
          all(v["min_pp"] > 0 for k, v in wedge.items() if k != "book_0249"),
          report, {"note": "the drafted form; impossible given the four "
                           "clip-bound months (WP-H1); recorded, non-blocking"})

    primary = haz[PRIMARY_DELTA_LABEL]
    timing = {}
    peak_moves, r_moves, u2_moves = {}, {}, {}
    for est, sim in (("path_b", sims["path_b"]), ("path_a", sims["path_a"]),
                     ("null", sims["null"])):
        s = sim["hazard_cpr_pct"]
        base_ccf = cpr_cross_correlation(base["cpr"], s)
        conv_ccf = cpr_cross_correlation(primary["cpr"], s)
        base_peak = max(base_ccf, key=lambda k: abs(base_ccf[k]))
        conv_peak = max(conv_ccf, key=lambda k: abs(conv_ccf[k]))
        peak_moves[est] = conv_peak - base_peak
        r_moves[est] = max(abs(conv_ccf[k] - base_ccf[k]) for k in base_ccf)
        blk_b = estimator_block(s.to_numpy(float), base["cpr"].to_numpy(float))
        blk_c = estimator_block(s.to_numpy(float),
                                primary["cpr"].to_numpy(float))
        u2_moves[est] = blk_c["u2_diffs"] - blk_b["u2_diffs"]
        timing[est] = {
            "ccf_committed": base_ccf, "ccf_converted": conv_ccf,
            "peak_lag_committed": int(base_peak),
            "peak_lag_converted": int(conv_peak),
            "max_abs_r_move": r_moves[est],
            "theil_committed": blk_b, "theil_converted": blk_c,
            "u2_move": u2_moves[est],
            "gof_committed": cpr_goodness_of_fit(base["cpr"], s)["raw"],
            "gof_converted": cpr_goodness_of_fit(primary["cpr"], s)["raw"],
        }
    _flag("Pb_peak_lag_unchanged",
          all(v == 0 for v in peak_moves.values()), report, peak_moves)
    r_moves_uncl = {}
    base_uncl = base["cpr_unclipped"]
    prim_uncl = primary["cpr_unclipped"]
    for est, sim in (("path_b", sims["path_b"]), ("path_a", sims["path_a"]),
                     ("null", sims["null"])):
        su = sim["hazard_cpr_pct"]
        bu = cpr_cross_correlation(base_uncl, su)
        cu = cpr_cross_correlation(prim_uncl, su)
        r_moves_uncl[est] = max(abs(cu[k] - bu[k]) for k in bu)
    _flag("Pb_r_invariant_unclipped",
          all(v < UNCLIPPED_INVARIANCE_TOL for v in r_moves_uncl.values()),
          report, {"max_abs_r_move_unclipped": r_moves_uncl,
                   "tol": UNCLIPPED_INVARIANCE_TOL,
                   "amendment": "G2B-AM1(b): an additive wedge cannot move a "
                                "demeaned correlation; exact on the unclipped "
                                "diagnostic"})
    _flag("CLIP_SHAPE_r_moves_clipped_series",
          all(v < R_MAX_MOVE for v in r_moves.values()), report,
          {"max_abs_r_move": r_moves, "drafted_threshold": R_MAX_MOVE,
           "note": "the clipped-series movement IS the clip's shape effect; "
                   "reported, non-blocking"})
    _flag("Pb_u2_within_threshold",
          all(abs(v) < U2_MAX_MOVE for v in u2_moves.values()), report,
          {"u2_move": u2_moves, "threshold": U2_MAX_MOVE})
    _flag("Pb_wedge_additive_on_unclipped",
          all(v < UNCLIPPED_INVARIANCE_TOL for v in uncl_spans.values()),
          report, {"unclipped_span_pp": uncl_spans,
                   "tol": UNCLIPPED_INVARIANCE_TOL})
    _flag("CLIP_SHAPE_wedge_span_clipped_series",
          all(v < WEDGE_SPAN_MAX_FRACTION for v in span_fractions.values()),
          report, {"span_over_sd": span_fractions,
                   "drafted_threshold": WEDGE_SPAN_MAX_FRACTION,
                   "note": "span on the reported (clipped) series; the "
                           "truncated months carry the whole span; reported, "
                           "non-blocking"})
    for est, want in COMMITTED_U2.items():
        got = (timing[est]["theil_committed"]["u2_diffs"] if est != "abm"
               else committed_blocks["abm"]["u2_diffs"])
        _gate(f"Pb_u2_committed_anchor[{est}]", got, want, TOL_EXACT, report)

    clip = {name: haz[name]["n_clipped_months"] for name in HAZARD_LEGS}
    theil_max_share_move = max(
        abs(timing[e]["theil_converted"]["decomp"][tf][sh]
            - timing[e]["theil_committed"]["decomp"][tf][sh])
        for e in ("path_b", "path_a", "null")
        for tf in ("levels", "diffs", "detrended")
        for sh in ("bias_share", "var_share", "cov_share")
    )

    # ---- H4 / H5 integrity ------------------------------------------------
    for name, before_hash in caches_before.items():
        p = next(q for q in READ_ONLY_CACHES if q.name == name)
        _flag(f"H4_cache_read_only[{name}]", _sha256(p) == before_hash, report)
    frozen_after = {p.name: _sha256(p) for p in FROZEN_ARTIFACTS}
    for name, before_hash in frozen_before.items():
        _flag(f"H5_frozen_artifact[{name}]",
              frozen_after[name] == before_hash, report,
              {"sha256_before": before_hash, "sha256_after": frozen_after[name]})

    runtime_s = time.perf_counter() - t0
    branch = classify_timing(
        peak_moves, r_moves_uncl, u2_moves,
        {k: v / emp_sd for k, v in uncl_spans.items()})
    hard_fail = [k for k, v in report.items() if not v["pass"]
                 and not k.startswith(NONBLOCKING_PREFIXES)]
    nonblocking_misses = [k for k, v in report.items() if not v["pass"]
                          and k.startswith(NONBLOCKING_PREFIXES)]
    status = "OK" if not hard_fail else "GATE_FAILURE"

    payload = {
        "mode": "coupon_convention_amortization",
        "status": status,
        "spec": (
            "SPEC_round28_G2_coupon_convention.md section G2-B as amended by "
            "G2-AM1: the SOMA CPR back-out recomputed at the pool's NOTE-rate "
            "WAC (book pass-through 2.49% plus the g-fee+servicing wedge; "
            "legs 0.60/0.70/0.80/0.90pp, primary 0.80) with the committed "
            "2.50% leg as the parity anchor; NO engine run — committed "
            "simulated caches are re-scored; Theil formulas transcribed from "
            "figures/make_theil_data.py:231-280 and gated against "
            "figures/theil_data.json before use; H1 asserts the trapped-$ "
            "accounting is bit-identical across every leg; timing "
            "pre-commitment P-b: peak lags unchanged in LOCATION, |dr| < "
            "0.005, |dU2| < 0.01, wedge span < 2% of the empirical CPR sd"
        ),
        "conventions_found": {
            "hazard_side_coupon": COMMITTED_HAZARD_COUPON,
            "hazard_side_site": "hazard/macro.py:241-243 (flat single pool)",
            "abm_side_nominal_coupon": ABM_NOMINAL_COUPON,
            "abm_side_site": ("abm/fed_mbs_extension_risk.py:77 "
                              "PORTFOLIO_COUPON; the committed fold-in run "
                              "used the burnout branch (:946-947), a "
                              "COHORT-WEIGHTED schedule from per-cohort SOMA "
                              "pass-through coupons"),
            "already_correct_site": ("abm/cross_design_reweight.py:562-568 "
                                     "uses the population's own note-rate WAC"),
            "printed_514_is_the_abm_series": True,
            "pathb_gof_is_the_hazard_series": True,
        },
        "hazard_legs": {
            n: {k: v for k, v in leg.items()
                if k not in ("frame", "cpr", "raw_smm")}
            for n, leg in haz.items()
        },
        "abm_legs": abm_legs,
        "abm_reconstruction_quotable": bool(abm_recon_ok),
        "abm_reconstruction_note": (
            "If false, the flat approximation to the committed cohort-weighted "
            "ABM schedule is inadequate: the ABM companion to the printed "
            "5.14% is NOT quoted, and G2-C's empirical-scenario input falls "
            "back to the hazard basis with the ambiguity disclosed. This is "
            "SPEC G2.9 #4 resolved by measurement rather than by choice."
        ),
        "empirical_cpr_by_leg_pct": {n: haz[n]["mean_cpr_pct"] for n in haz},
        "wedge": wedge,
        "empirical_sd_pct": emp_sd,
        "dollar_invariance": dollars,
        "timing": timing,
        "clip_diagnostic": {
            "n_clipped_months_by_leg": clip,
            "committed": clip["committed_0250"],
            "primary": clip[PRIMARY_DELTA_LABEL],
            "handoff": ("WP-H1 owns the 'four exact-zero months'. If this "
                        "count FALLS, G2-B has partially diagnosed them and "
                        "the packages must be sequenced; if it does NOT, "
                        "H1's zeros are not an amortization artifact. No "
                        "claim is attached to either outcome here."),
        },
        "theil_max_printed_share_move_pp": float(theil_max_share_move),
        "theil_refresh_threshold_pp": THEIL_SHARE_REFRESH_PP,
        "thresholds": {
            "peak_lag_max_move_months": PEAK_LAG_MAX_MOVE,
            "r_max_move": R_MAX_MOVE,
            "u2_max_move": U2_MAX_MOVE,
            "wedge_span_max_fraction_of_sd": WEDGE_SPAN_MAX_FRACTION,
            "level_materiality_pp": LEVEL_MATERIALITY_PP,
        },
        "gates": report,
        "gates_all_pass": not hard_fail,
        "nonblocking_misses": nonblocking_misses,
        "landing_branch": branch,
        "landing_rule": landing_text(
            branch, wedge[PRIMARY_DELTA_LABEL]["mean_pp"],
            clip["committed_0250"], clip[PRIMARY_DELTA_LABEL],
            float(theil_max_share_move)),
        "frozen_artifact_sha256": {"before": frozen_before, "after": frozen_after},
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1, default=_json_default)

    # ------------------------------------------------------------------
    print("\n" + "=" * 78)
    print(" COUPON-CONVENTION AMORTIZATION — back-out at the note-rate WAC")
    print("=" * 78)
    print(f"  {'leg':<16}{'coupon':>9}{'mean CPR %':>13}{'wedge pp':>11}"
          f"{'span/sd':>10}{'clipped':>9}")
    for name in HAZARD_LEGS:
        w = wedge.get(name)
        print(f"  {name:<16}{haz[name]['coupon']:>9.4f}"
              f"{haz[name]['mean_cpr_pct']:>13.4f}"
              + (f"{w['mean_pp']:>+11.4f}{w['span_over_empirical_sd']:>10.4f}"
                 if w else f"{'--':>11}{'--':>10}")
              + f"{haz[name]['n_clipped_months']:>9}")
    print("-" * 78)
    print(f"  empirical CPR sd {emp_sd:.4f}pp; primary wedge "
          f"{wedge[PRIMARY_DELTA_LABEL]['mean_pp']:+.4f}pp "
          f"(span {wedge[PRIMARY_DELTA_LABEL]['span_pp']:.4f}pp)")
    print(f"  DOLLAR INVARIANCE (H1): Path B trapped "
          f"{dollars['committed_0250']['path_b']['hazard_trapped_b']:.10f}B "
          "across every leg — the benchmark and every trapped-$ figure are "
          "untouched by this correction")
    for est in ("path_b", "path_a", "null"):
        print(f"  {est:<7} peak lag {timing[est]['peak_lag_committed']:>3} -> "
              f"{timing[est]['peak_lag_converted']:>3}   max |dr| "
              f"{timing[est]['max_abs_r_move']:.6f}   dU2 "
              f"{timing[est]['u2_move']:+.6f}")
    print(f"  ABM basis: reconstruction quotable={abm_recon_ok}; "
          f"printed 5.14% -> "
          f"{abm_legs[PRIMARY_DELTA_LABEL]['mean_cpr_pct']:.4f}% "
          f"({abm_legs[PRIMARY_DELTA_LABEL]['delta_vs_committed_pp']:+.4f}pp)")
    print("=" * 78)
    print(f"landing branch ({branch}): {payload['landing_rule']}")
    print(f"status {status}   gates all pass: {not hard_fail}   "
          f"runtime {runtime_s:,.1f}s")
    print(f"Saved: {RESULTS_JSON}")
    if hard_fail:
        raise SystemExit(f"GATE FAILURE — do not build on this: {hard_fail}")


if __name__ == "__main__":
    main()
