#!/usr/bin/env python3
"""
Round-16 W2: observed-speed bound on the 2022 / pre-2017 vintage
extrapolation residual (the "no bound of either kind" concession).

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------
PURPOSE
  The manuscript concedes in three places (tex III.D "the vintage dimension
  carries no such bound", V.C "carries no bound of either kind" with the
  23.1% / 10.6% face shares, VIII.A's open item) that extrapolating the
  2017-2021-estimated hazards to the 2022 vintage (23.1% of SOMA book face)
  and pre-2017 vintages (10.6%) is unbounded: neither the coupon reweighting
  nor the Ginnie speed comparison constrains it.  The W4 Fannie replication
  ingest (spec cbabbd2, artifact d8199eb) left per-quarter cohort-month cell
  files locally that contain OBSERVED QT-window prepayment for exactly those
  out-of-sample vintage groups (acquisition files carry a seasoned
  origination tail back to 2010, and the 2022 acquisition quarters carry the
  2022 vintage the combined panel's 2017-2021 filter drops).  This run
  builds the missing bound in the template of the paper's static Ginnie
  composition bound (tex V.C): observed differential CPR x face share x
  dollars-per-CPR-point sensitivity.

INPUTS (all local or committed; nothing fetched)
  data/fannie_quarters/cells_FNMA{2017Q1..2022Q4}.parquet  (24 files, local,
      gitignored) — per-quarter build_panel_from_files outputs; columns used:
      vintage, period, exposure_upb, prepaid_upb, loan_count.  Observed
      vintages 2010-2022.
  data/fannie_quarters/manifest.json  (local) — per-quarter staged_loans /
      staged_rows / cells_rows written by fannie_replication.py.
  data/cohort_month_panel_fannie.parquet  (local; combine_quarter_cells
      output over the same cells, vintage-filtered 2017-2021) — G1/G3 parity
      reference.
  data/fannie_replication_results.json  (committed, artifact d8199eb) —
      universe block {staged_loans_total 17,606,999; staged_rows_total
      825,814,383} for G2's local-manifest-vs-committed-artifact tie.
  data/ginnie_bound.json  (committed) — trapped_sensitivity_b_per_pp = 82.8
      ($B per CPR point; derivation recorded there: beta1=0 null vs central,
      $70.3B per 0.85pp mean CPR — the constant tex V.C rounds to "roughly
      $83 billion per CPR point" and ginnie_cpr_overlay.py uses in its
      linearized check) and the static bound_b [20.3, 47.3].
  data/expectation_benchmark_results.json  (committed) — cap_benchmark_b
      764.7482532227002 cross-checks the quoted benchmark constant.
  data/gmar_dec25_cpr_series.json  (committed) — published full-universe
      Fannie CPR series; NON-GATING context diagnostic only.
  hazard/wal_table.py VINTAGE_SHARES  (committed code) — the authoritative
      in-repo source of the face shares (SOMA CUSIP tabulation, Table 6
      note; tex sec:robustness-wal): 2022 = 0.231, pre2017 = 0.106.
  common/qt_window.py — QT window bounds (single source of truth).

CONSTRUCTION (exact, deterministic; no randomness, no wall-clock in artifact)
  1. QT window: QT_START (2022-06-01) <= period < QT_END (2025-12-01), the
     half-open production window from common/qt_window.py — 42 months
     Jun-2022..Nov-2025, the same convention ginnie_cpr_overlay.py and the
     production scorer aggregate over.
  2. Load the 24 cell files, concat, mask to the QT window.  Segments (by
     origination vintage):
       sampled_2017_2021: vintage in config.VINTAGE_YEARS (2017-2021) —
                          the sampled-universe proxy;
       vintage_2022:      vintage == 2022;
       pre_2017:          vintage <= 2016 (observed 2010-2016).
  3. Per-segment window CPR: pooled dollar SMM, compound-annualized —
       SMM_seg = sum(prepaid_upb) / sum(exposure_upb)   over all QT rows
       CPR_seg = 1 - (1 - SMM_seg)^12
     Pooled dollar SMM IS the exposure-weighted mean of monthly SMMs (the
     weights are each month's exposure), i.e. the task's "aggregate
     exposure-weighted SMM then annualize".  Compound annualization is the
     house convention for OBSERVED speeds (ginnie_cpr_overlay.py's SMM<->CPR
     conversions; the GMAR Dec-25 extraction identity CPR=1-(1-CRR)(1-CDR));
     the x12 convention is model-engine-internal only and is not used here.
     Disclosed secondary variant (reported, never primary): unweighted
     window mean of monthly compound-annualized CPRs.
  4. Signed differentials vs the sampled universe (pp):
       d_2022    = CPR_2022    - CPR_sampled
       d_pre2017 = CPR_pre2017 - CPR_sampled
  5. Book-CPR extrapolation error (pp), face-share weighted:
       e = 0.231 * d_2022 + 0.106 * d_pre2017
     (shares from wal_table.VINTAGE_SHARES; the sampled 2017-2021 legs carry
     zero error by construction — they ARE the estimation universe).
  6. Dollar bound, static-Ginnie-bound template:
       bound_b = |e| * 82.8      signed by sign(e); per-leg bounds
       share_i * d_i * 82.8 also reported.
  7. Expressed as % of the committed $764.7482532227002B benchmark.

GATES (numbered; reference + tolerance + source; artifact with results is
written ONLY if all pass — on failure a GATE_FAILURE stub is written and
the process exits nonzero)
  G1 parity — QT-window sums over vintages 2017-2021 from the cells must
     reconcile against the committed combined panel
     (cohort_month_panel_fannie.parquet): exposure_upb and prepaid_upb to
     relative tolerance 1e-9 (combine_quarter_cells is a pure groupby-sum of
     these same cells, so only float-summation order differs; observed at
     spec time: exposure 92,571,970,958,106.84 / prepaid 338,652,698,406.21,
     rel diff ~5e-16), loan_count exactly (393,755,296 at spec time).
  G2 manifest integrity — (a) exactly the 24 spec tags FNMA2017Q1..FNMA2022Q4
     present as both cell files and manifest entries; (b) each cell file's
     row count == its manifest cells_rows (total 175,383 at spec time);
     (c) manifest staged_loans / staged_rows totals equal the COMMITTED
     fannie_replication_results.json universe block exactly (17,606,999 /
     825,814,383) — ties the local derived files to the committed run of
     record; (d) observed vintage range within [2010, 2022].
  G3 sanity — (a) every segment has nonzero QT-window exposure and full
     42-month coverage (42 = common.qt_window.expected_qt_active_months());
     (b) the sampled-universe pooled CPR from the cells' raw dollars matches
     the same statistic recomputed from the committed panel's own
     monthly_prepay_rate column (exposure-weighted; the replication's
     observed aggregate) within +/-0.01pp (cross-construction check; the
     rate column carries ingest.py's exposure clip(lower_bound=1), observed
     at spec time to agree within ~1e-5pp).
  G4 constants integrity — quoted anchors equal their committed sources:
     sensitivity 82.8 == ginnie_bound.json trapped_sensitivity_b_per_pp;
     static bound [20.3, 47.3] == ginnie_bound.json bound_b; face shares
     0.231/0.106 == wal_table.VINTAGE_SHARES["2022"/"pre2017"] (and the five
     shares sum to 0.999, the printed tabulation's coverage); benchmark
     764.7482532227002 == expectation_benchmark_results.json cap_benchmark_b
     (abs tol 1e-9); lock-in marginal +70.34506041989584 B quoted from the
     committed no_lockin_null_results.json-derived anchor (as in
     marginal_decomposition.py).

PRE-COMMITTED INTERPRETATION (fixed ex ante; every outcome has its reading)
  Sign of e (net, share-weighted; per-leg signs reported alongside):
    e > 0  (out-of-sample vintages prepaid FASTER than sampled): the
           production extrapolation understates book-wide observed CPR, so
           simulated roll-off is too slow and trapped liquidity is
           OVERSTATED by up to the bound — conservative for the headline,
           the same direction as the static Ginnie composition bound.
    e < 0  (slower): trapped liquidity is UNDERSTATED by up to the bound —
           anti-conservative for the headline; reported symmetrically with
           the same prominence.
    e == 0: bound $0; the concession is closed at zero measured residual.
  Materiality (|bound_b| against the committed static Ginnie bound
  [20.3, 47.3] $B and the +70.345 $B lock-in marginal; sentence patterns
  fixed here, numbers filled at run time):
    |bound_b| < 20.3  -> verdict "below_ginnie_bound":
      "The previously unbounded vintage extrapolation is bounded at
       ${B}B ({P}% of the $764.7B benchmark) — below the static Ginnie
       composition bound's lower edge ($20.3B) and {M}% of the +$70.3B
       lock-in marginal."
    20.3 <= |bound_b| <= 47.3 -> verdict "comparable_to_ginnie_bound":
      "The vintage extrapolation residual is bounded at ${B}B ({P}% of
       benchmark) — comparable to the static Ginnie composition bound
       ($20.3-47.3B) and {M}% of the +$70.3B lock-in marginal."
    |bound_b| > 47.3 -> verdict "exceeds_ginnie_bound":
      "The vintage extrapolation residual is bounded at ${B}B ({P}% of
       benchmark) — larger than the static Ginnie composition bound; at
       {M}% of the +$70.3B lock-in marginal this is a material caveat
       upgrade for III.D/V.C/VIII.A."
      (if additionally |bound_b| >= 70.345 the verdict string becomes
       "exceeds_lockin_marginal" and the sentence appends: "It is
       comparable to or exceeds the lock-in marginal itself.")
  The verdict names the dollar bound only; the sign reading travels with it
  unchanged.  No post-hoc reframing: whichever cell obtains is the reading.

CAVEATS (stated ex ante; carried in the artifact)
  * Fannie observed speeds proxy the SOMA book's segment behavior — the
    same single-agency-proxy posture as the GMAR overlay and the Freddie
    production calibration itself.
  * The pre-2017 leg is a seasoned/selected acquisition subset (the 2-year
    seasoned tail of 2017+ acquisition files; ~3.4M QT loan-months vs 394M
    sampled), not a random draw of pre-2017 originations; its CPR is a
    survivor-composition-tilted estimate and the 10.6% face share is applied
    to it as-is.
  * The 2022 leg covers acquisitions through 2022Q4 while SOMA's
    2022-vintage face skews toward H1-2022 settlements (the Q10
    settlement-aware amendment's allocation caveat); the leg is a
    full-year-2022 speed applied to an H1-tilted face.
  * The face shares span the full book INCLUDING Ginnie collateral (20.4%),
    so this vintage bound and the agency bound overlap on Ginnie's
    out-of-sample vintages; both are one-dimensional bounds in the
    manuscript's two-bounds template, not additive components.
  * The GMAR full-universe Fannie window-mean CPR is reported as a
    non-gating context diagnostic; it is expected to sit ABOVE the sampled
    subset (it includes post-2022 high-coupon production) and gates nothing.

OUTPUT
  data/vintage_residual_bound_results.json — headline statistics ONLY.
  Top-level keys: mode, spec, qt_window, cpr_convention, committed_anchors,
  gates, results, diagnostics, caveats.  results carries: per-segment
  {cpr_pct, qt_loan_months, qt_exposure_usd_t, exposure_share_of_observed_pct,
  differential_pp (non-sampled legs), leg_bound_b (non-sampled legs)},
  book_cpr_error_pp, bound_b, bound_pct_of_benchmark, sign_direction,
  mean_monthly_variant {segment cprs, book_cpr_error_pp, bound_b},
  interpretation {verdict, sentence, thresholds}.

LICENSE / PROVENANCE (identical posture to fannie_replication.py, ratified)
  The artifact carries headline statistics only — NO per-quarter,
  per-vintage-month, or cell-level values.  The input cells, manifest, and
  combined panel stay local and gitignored.  Segment-level window
  aggregates (three CPRs, loan-month counts) are manuscript-grade headline
  statistics of the same kind fannie_replication_results.json ships.

Run:  cd hazard && python3 vintage_residual_bound.py   (~seconds; pure
      arithmetic on local parquet + committed JSON; no network, no engine)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import polars as pl

from config import DATA_DIR, QT_END, QT_START, VINTAGE_YEARS
from common.qt_window import expected_qt_active_months  # noqa: E402
from wal_table import VINTAGE_SHARES  # SOMA CUSIP tabulation (Table 6 note)

QUARTER_DIR = DATA_DIR / "fannie_quarters"
MANIFEST_PATH = QUARTER_DIR / "manifest.json"
PANEL_PATH = DATA_DIR / "cohort_month_panel_fannie.parquet"  # prepare_fannie.FANNIE_PANEL_PATH
REPLICATION_JSON = DATA_DIR / "fannie_replication_results.json"
GINNIE_BOUND_JSON = DATA_DIR / "ginnie_bound.json"
EXPECT_BENCH_JSON = DATA_DIR / "expectation_benchmark_results.json"
GMAR_JSON = DATA_DIR / "gmar_dec25_cpr_series.json"
RESULTS_JSON = DATA_DIR / "vintage_residual_bound_results.json"

TAGS = [f"FNMA{y}{q}" for y in range(2017, 2023) for q in ("Q1", "Q2", "Q3", "Q4")]

# Committed anchors (quoted, not re-derived; G4 ties them to their sources).
BENCHMARK_B = 764.7482532227002          # expectation_benchmark_results.json cap_benchmark_b
SENSITIVITY_B_PER_PP = 82.8              # ginnie_bound.json trapped_sensitivity_b_per_pp
STATIC_GINNIE_BOUND_B = (20.3, 47.3)     # ginnie_bound.json bound_b
LOCKIN_MARGINAL_B = 70.34506041989584    # committed null-vs-central marginal (marginal_decomposition.py)
SHARE_2022 = VINTAGE_SHARES["2022"]      # 0.231 (tex line: "23.1% of book face")
SHARE_PRE2017 = VINTAGE_SHARES["pre2017"]  # 0.106 ("pre-2017 vintages another 10.6%")

G1_REL_TOL = 1e-9
G3_CPR_TOL_PP = 0.01
G4_ABS_TOL = 1e-9
VINTAGE_RANGE = (2010, 2022)

SENTENCES = {
    "below_ginnie_bound": (
        "The previously unbounded vintage extrapolation is bounded at "
        "${B:.1f}B ({P:.1f}% of the $764.7B benchmark) — below the static "
        "Ginnie composition bound's lower edge ($20.3B) and {M:.0f}% of the "
        "+$70.3B lock-in marginal."
    ),
    "comparable_to_ginnie_bound": (
        "The vintage extrapolation residual is bounded at ${B:.1f}B "
        "({P:.1f}% of benchmark) — comparable to the static Ginnie "
        "composition bound ($20.3-47.3B) and {M:.0f}% of the +$70.3B "
        "lock-in marginal."
    ),
    "exceeds_ginnie_bound": (
        "The vintage extrapolation residual is bounded at ${B:.1f}B "
        "({P:.1f}% of benchmark) — larger than the static Ginnie composition "
        "bound; at {M:.0f}% of the +$70.3B lock-in marginal this is a "
        "material caveat upgrade for III.D/V.C/VIII.A."
    ),
}
SIGN_READINGS = {
    "overstates_trapped": (
        "Out-of-sample vintages prepaid FASTER than the sampled universe over "
        "the QT window; the extrapolation error is signed toward OVERSTATING "
        "trapped liquidity — conservative for the headline, the same "
        "direction as the static Ginnie composition bound."
    ),
    "understates_trapped": (
        "Out-of-sample vintages prepaid SLOWER than the sampled universe over "
        "the QT window; the extrapolation error is signed toward "
        "UNDERSTATING trapped liquidity — anti-conservative for the "
        "headline, reported symmetrically."
    ),
    "zero": "Zero measured residual; the concession is closed at $0.",
}


def _fail(gates: dict, msg: str) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"mode": "vintage_residual_bound", "status": "GATE_FAILURE",
         "gates": gates, "detail": msg}, indent=2, default=float) + "\n")
    raise SystemExit(f"GATE FAILURE — {msg} (results not written)")


def pooled_cpr_pct(frame: pl.DataFrame) -> float:
    """Compound-annualized pooled dollar SMM (== exposure-weighted mean SMM)."""
    smm = frame["prepaid_upb"].sum() / frame["exposure_upb"].sum()
    return (1.0 - (1.0 - smm) ** 12) * 100.0


def mean_monthly_cpr_pct(frame: pl.DataFrame) -> float:
    """Disclosed variant: unweighted window mean of monthly pooled CPRs."""
    m = (frame.group_by("period")
         .agg(pl.col("prepaid_upb").sum(), pl.col("exposure_upb").sum())
         .with_columns(((1 - (1 - pl.col("prepaid_upb") / pl.col("exposure_upb")) ** 12) * 100)
                       .alias("cpr")))
    return float(m["cpr"].mean())


def main() -> None:
    t0 = time.perf_counter()
    gates: dict = {}

    # ---- load ---------------------------------------------------------------
    manifest = json.load(open(MANIFEST_PATH))
    replication = json.load(open(REPLICATION_JSON))
    ginnie = json.load(open(GINNIE_BOUND_JSON))
    bench_src = json.load(open(EXPECT_BENCH_JSON))

    cell_paths = {t: QUARTER_DIR / f"cells_{t}.parquet" for t in TAGS}
    frames = {t: pl.read_parquet(p) for t, p in cell_paths.items() if p.exists()}

    # ---- G2 manifest integrity ---------------------------------------------
    missing_files = [t for t in TAGS if t not in frames]
    manifest_tags_ok = sorted(manifest.keys()) == sorted(TAGS)
    rows_ok = {t: (f.height, manifest.get(t, {}).get("cells_rows"))
               for t, f in frames.items()}
    per_file_ok = all(got == want for got, want in rows_ok.values())
    staged_loans = sum(m["staged_loans"] for m in manifest.values())
    staged_rows = sum(m["staged_rows"] for m in manifest.values())
    uni = replication["universe"]
    committed_tie_ok = (staged_loans == uni["staged_loans_total"]
                        and staged_rows == uni["staged_rows_total"])
    cells = pl.concat(list(frames.values())) if frames else pl.DataFrame()
    vmin, vmax = (int(cells["vintage"].min()), int(cells["vintage"].max())) if len(cells) else (0, 0)
    vintage_ok = VINTAGE_RANGE[0] <= vmin and vmax <= VINTAGE_RANGE[1]
    gates["G2_manifest_integrity"] = {
        "files_present": len(frames), "files_expected": len(TAGS),
        "manifest_tags_match_spec": manifest_tags_ok,
        "per_file_rows_match_manifest": per_file_ok,
        "cells_rows_total": int(cells.height),
        "staged_loans_total": {"got": staged_loans, "want": uni["staged_loans_total"]},
        "staged_rows_total": {"got": staged_rows, "want": uni["staged_rows_total"]},
        "committed_artifact_tie": committed_tie_ok,
        "vintage_range": [vmin, vmax], "vintage_range_ok": vintage_ok,
        "pass": (not missing_files and manifest_tags_ok and per_file_ok
                 and committed_tie_ok and vintage_ok),
    }
    print(f"G2 manifest integrity: {len(frames)}/{len(TAGS)} files, "
          f"rows {int(cells.height):,}, staged {staged_loans:,} loans / "
          f"{staged_rows:,} rows vs committed "
          f"{'OK' if committed_tie_ok else 'MISMATCH'}  "
          f"{'PASS' if gates['G2_manifest_integrity']['pass'] else 'FAIL'}")
    if not gates["G2_manifest_integrity"]["pass"]:
        _fail(gates, "G2 manifest integrity failed")

    # ---- QT window mask (common/qt_window.py convention) --------------------
    qt = cells.filter((pl.col("period") >= QT_START.to_pydatetime())
                      & (pl.col("period") < QT_END.to_pydatetime()))
    n_months_expected = expected_qt_active_months()  # 42

    segments = {
        "sampled_2017_2021": qt.filter(pl.col("vintage").is_in(list(VINTAGE_YEARS))),
        "vintage_2022": qt.filter(pl.col("vintage") == 2022),
        "pre_2017": qt.filter(pl.col("vintage") <= 2016),
    }

    # ---- G1 parity: cells (2017-2021, QT window) vs committed panel ---------
    panel = pl.read_parquet(PANEL_PATH)
    panel_qt = panel.filter((pl.col("period") >= QT_START.to_pydatetime())
                            & (pl.col("period") < QT_END.to_pydatetime()))
    c = segments["sampled_2017_2021"]
    checks = {}
    for col in ("exposure_upb", "prepaid_upb"):
        got, want = float(c[col].sum()), float(panel_qt[col].sum())
        checks[col] = {"got": got, "want": want,
                       "rel_diff": abs(got - want) / abs(want),
                       "pass": abs(got - want) <= G1_REL_TOL * abs(want)}
    lc_got, lc_want = int(c["loan_count"].sum()), int(panel_qt["loan_count"].sum())
    checks["loan_count"] = {"got": lc_got, "want": lc_want, "pass": lc_got == lc_want}
    gates["G1_parity"] = {**checks, "rel_tol": G1_REL_TOL,
                          "pass": all(v["pass"] for v in checks.values())}
    print(f"G1 parity vs committed panel: exposure rel "
          f"{checks['exposure_upb']['rel_diff']:.1e}, prepaid rel "
          f"{checks['prepaid_upb']['rel_diff']:.1e}, loan_count "
          f"{lc_got - lc_want:+d}  "
          f"{'PASS' if gates['G1_parity']['pass'] else 'FAIL'}")
    if not gates["G1_parity"]["pass"]:
        _fail(gates, "G1 parity vs committed Fannie panel failed")

    # ---- G4 constants integrity ---------------------------------------------
    shares_sum = sum(VINTAGE_SHARES.values())
    g4 = {
        "sensitivity": {"got": ginnie["trapped_sensitivity_b_per_pp"],
                        "want": SENSITIVITY_B_PER_PP,
                        "pass": ginnie["trapped_sensitivity_b_per_pp"] == SENSITIVITY_B_PER_PP},
        "static_bound": {"got": ginnie["bound_b"], "want": list(STATIC_GINNIE_BOUND_B),
                         "pass": list(ginnie["bound_b"]) == list(STATIC_GINNIE_BOUND_B)},
        "share_2022": {"got": SHARE_2022, "want": 0.231, "pass": SHARE_2022 == 0.231},
        "share_pre2017": {"got": SHARE_PRE2017, "want": 0.106, "pass": SHARE_PRE2017 == 0.106},
        "shares_sum": {"got": shares_sum, "want": 0.999,
                       "pass": abs(shares_sum - 0.999) <= 1e-12},
        "benchmark": {"got": bench_src["cap_benchmark_b"], "want": BENCHMARK_B,
                      "pass": abs(bench_src["cap_benchmark_b"] - BENCHMARK_B) <= G4_ABS_TOL},
    }
    gates["G4_constants_integrity"] = {**g4, "pass": all(v["pass"] for v in g4.values())}
    print(f"G4 constants integrity: sensitivity {SENSITIVITY_B_PER_PP} $B/pp, "
          f"shares {SHARE_2022}/{SHARE_PRE2017} (sum {shares_sum}), benchmark "
          f"{BENCHMARK_B:.4f}  "
          f"{'PASS' if gates['G4_constants_integrity']['pass'] else 'FAIL'}")
    if not gates["G4_constants_integrity"]["pass"]:
        _fail(gates, "G4 constants integrity failed")

    # ---- segment statistics --------------------------------------------------
    total_exp = float(qt["exposure_upb"].sum())
    seg_stats = {}
    for name, frame in segments.items():
        seg_stats[name] = {
            "cpr_pct": pooled_cpr_pct(frame),
            "mean_monthly_cpr_pct": mean_monthly_cpr_pct(frame),
            "qt_months": int(frame["period"].n_unique()),
            "qt_loan_months": int(frame["loan_count"].sum()),
            "qt_exposure_usd_t": float(frame["exposure_upb"].sum()) / 1e12,
            "exposure_share_of_observed_pct":
                float(frame["exposure_upb"].sum()) / total_exp * 100.0,
        }

    # ---- G3 sanity ------------------------------------------------------------
    coverage_ok = all(s["qt_months"] == n_months_expected and s["qt_exposure_usd_t"] > 0
                      for s in seg_stats.values())
    smm_panel = ((panel_qt["monthly_prepay_rate"] * panel_qt["exposure_upb"]).sum()
                 / panel_qt["exposure_upb"].sum())
    cpr_panel = (1.0 - (1.0 - smm_panel) ** 12) * 100.0
    cpr_cells = seg_stats["sampled_2017_2021"]["cpr_pct"]
    cross_ok = abs(cpr_cells - cpr_panel) <= G3_CPR_TOL_PP
    gates["G3_sanity"] = {
        "expected_qt_months": n_months_expected,
        "segment_coverage": {n: {"months": s["qt_months"],
                                 "exposure_usd_t": s["qt_exposure_usd_t"]}
                             for n, s in seg_stats.items()},
        "coverage_pass": coverage_ok,
        "sampled_cpr_cells_pct": cpr_cells,
        "sampled_cpr_panel_ratecol_pct": cpr_panel,
        "abs_diff_pp": abs(cpr_cells - cpr_panel),
        "tol_pp": G3_CPR_TOL_PP,
        "cross_construction_pass": cross_ok,
        "pass": coverage_ok and cross_ok,
    }
    print(f"G3 sanity: coverage {n_months_expected}mo x3 segments "
          f"{'OK' if coverage_ok else 'FAIL'}; sampled CPR {cpr_cells:.4f}% vs "
          f"panel-rate-col {cpr_panel:.4f}% (diff {abs(cpr_cells - cpr_panel):.2e}pp)  "
          f"{'PASS' if gates['G3_sanity']['pass'] else 'FAIL'}")
    if not gates["G3_sanity"]["pass"]:
        _fail(gates, "G3 sanity failed")

    # ---- bound (primary: pooled construction) --------------------------------
    def bound_block(cpr_key: str) -> dict:
        cpr_s = seg_stats["sampled_2017_2021"][cpr_key]
        d_2022 = seg_stats["vintage_2022"][cpr_key] - cpr_s
        d_pre = seg_stats["pre_2017"][cpr_key] - cpr_s
        e = SHARE_2022 * d_2022 + SHARE_PRE2017 * d_pre
        return {
            "differential_2022_pp": d_2022,
            "differential_pre2017_pp": d_pre,
            "leg_bound_2022_b": SHARE_2022 * d_2022 * SENSITIVITY_B_PER_PP,
            "leg_bound_pre2017_b": SHARE_PRE2017 * d_pre * SENSITIVITY_B_PER_PP,
            "book_cpr_error_pp": e,
            "bound_b": abs(e) * SENSITIVITY_B_PER_PP,
            "bound_signed_b": e * SENSITIVITY_B_PER_PP,
            "bound_pct_of_benchmark": abs(e) * SENSITIVITY_B_PER_PP / BENCHMARK_B * 100.0,
        }

    primary = bound_block("cpr_pct")
    variant = bound_block("mean_monthly_cpr_pct")

    e = primary["book_cpr_error_pp"]
    sign_key = "overstates_trapped" if e > 0 else ("understates_trapped" if e < 0 else "zero")
    bound_b = primary["bound_b"]
    if bound_b < STATIC_GINNIE_BOUND_B[0]:
        verdict = "below_ginnie_bound"
    elif bound_b <= STATIC_GINNIE_BOUND_B[1]:
        verdict = "comparable_to_ginnie_bound"
    else:
        verdict = "exceeds_ginnie_bound"
    sentence = SENTENCES[verdict].format(
        B=bound_b, P=primary["bound_pct_of_benchmark"],
        M=bound_b / LOCKIN_MARGINAL_B * 100.0)
    if verdict == "exceeds_ginnie_bound" and bound_b >= LOCKIN_MARGINAL_B:
        verdict = "exceeds_lockin_marginal"
        sentence += " It is comparable to or exceeds the lock-in marginal itself."

    # ---- non-gating context diagnostic: GMAR full-universe Fannie mean -------
    gmar = json.load(open(GMAR_JSON))
    i0, i1 = gmar["months"].index("2022-06"), gmar["months"].index("2025-11")
    fannie_series = gmar["cpr"]["fannie"][i0:i1 + 1]
    gmar_mean = sum(fannie_series) / len(fannie_series)

    for name in ("vintage_2022", "pre_2017"):
        seg_stats[name]["differential_pp"] = (
            seg_stats[name]["cpr_pct"] - seg_stats["sampled_2017_2021"]["cpr_pct"])

    payload = {
        "mode": "vintage_residual_bound",
        "spec": ("round-16 W2; observed Fannie QT-window speeds bound the "
                 "2022/pre-2017 vintage extrapolation in the static Ginnie "
                 "bound template (module docstring, fixed ex ante)"),
        "qt_window": {"start": str(QT_START.date()),
                      "end_exclusive": str(QT_END.date()),
                      "months": n_months_expected,
                      "source": "common/qt_window.py (half-open, production convention)"},
        "cpr_convention": ("pooled dollar SMM over the window (== exposure-"
                           "weighted mean monthly SMM), compound-annualized "
                           "CPR = 1-(1-SMM)^12 — house convention for "
                           "observed speeds (ginnie_cpr_overlay.py / GMAR "
                           "extraction); mean-monthly variant disclosed"),
        "committed_anchors": {
            "benchmark_b": BENCHMARK_B,
            "sensitivity_b_per_pp": SENSITIVITY_B_PER_PP,
            "sensitivity_source": ("data/ginnie_bound.json "
                                   "trapped_sensitivity_b_per_pp (beta1=0 "
                                   "null vs central: $70.3B per 0.85pp mean "
                                   "CPR; tex 'roughly $83 billion per CPR point')"),
            "static_ginnie_bound_b": list(STATIC_GINNIE_BOUND_B),
            "lockin_marginal_b": LOCKIN_MARGINAL_B,
            "face_shares": {"vintage_2022": SHARE_2022, "pre_2017": SHARE_PRE2017,
                            "source": ("hazard/wal_table.py VINTAGE_SHARES "
                                       "(SOMA CUSIP tabulation, Table 6 note; "
                                       "tex sec:robustness-wal)")},
        },
        "gates": gates,
        "results": {
            "segments": seg_stats,
            **primary,
            "sign_direction": sign_key,
            "sign_reading": SIGN_READINGS[sign_key],
            "mean_monthly_variant": variant,
            "interpretation": {
                "verdict": verdict,
                "sentence": sentence,
                "thresholds": {"ginnie_bound_b": list(STATIC_GINNIE_BOUND_B),
                               "lockin_marginal_b": LOCKIN_MARGINAL_B},
            },
        },
        "diagnostics": {
            "gmar_dec25_fannie_full_universe_window_mean_cpr_pct": gmar_mean,
            "note": ("non-gating context: full-universe published Fannie CPR "
                     "includes post-2022 high-coupon production, expected to "
                     "sit above the 2017-2021 acquisition subset"),
        },
        "caveats": [
            "Fannie observed speeds proxy the SOMA book (same posture as the GMAR overlay).",
            ("pre-2017 leg is a seasoned/selected acquisition-file tail "
             f"({seg_stats['pre_2017']['qt_loan_months']:,} QT loan-months), "
             "not a random pre-2017 origination draw; the 10.6% face share "
             "is applied to it as-is."),
            ("2022 leg covers acquisitions through 2022Q4 while SOMA 2022 "
             "face skews to H1-2022 settlements (Q10 settlement-aware "
             "amendment)."),
            ("face shares span the full book incl. Ginnie (20.4%); this "
             "bound and the agency bound overlap on Ginnie's out-of-sample "
             "vintages — one-dimensional bounds, not additive."),
        ],
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")

    s = seg_stats
    print(f"\nSegment CPRs (pooled, compound-annualized): "
          f"sampled {s['sampled_2017_2021']['cpr_pct']:.3f}%  "
          f"2022 {s['vintage_2022']['cpr_pct']:.3f}% "
          f"({primary['differential_2022_pp']:+.3f}pp)  "
          f"pre-2017 {s['pre_2017']['cpr_pct']:.3f}% "
          f"({primary['differential_pre2017_pp']:+.3f}pp)")
    print(f"Book-CPR extrapolation error {e:+.4f}pp x {SENSITIVITY_B_PER_PP} $B/pp "
          f"-> bound ${bound_b:.2f}B ({primary['bound_pct_of_benchmark']:.2f}% "
          f"of benchmark; signed {primary['bound_signed_b']:+.2f}B)")
    print(f"Sign: {sign_key}.  Verdict: {verdict}.")
    print(sentence)
    print(f"Mean-monthly variant bound ${variant['bound_b']:.2f}B "
          f"({variant['bound_pct_of_benchmark']:.2f}%) — disclosed, not primary")
    print(f"Results saved to {RESULTS_JSON}  ({time.perf_counter() - t0:.1f}s)")


if __name__ == "__main__":
    main()
