#!/usr/bin/env python3
"""
Round-18 R18-K (optional light leg): isolate a 2015-2016-acquisition-vintage
observed-speed figure from the pre-2017 tail the round-16 W2 run already priced.

SPEC (committed before execution; interpretation thresholds ex ante)
--------------------------------------------------------------------
PURPOSE
  Referee E1 asks for out-of-time evidence on cohorts outside the 2017-2021
  calibration universe, NAMING the 2015-2016 originations specifically.  The
  round-16 run `vintage_residual_bound` (script hazard/vintage_residual_bound.py,
  artifact hazard/data/vintage_residual_bound_results.json) already prices
  observed QT-window speeds of out-of-universe cohorts from the Fannie ingest's
  per-quarter cells and folds the referee's named 2015-2016 cohorts inside an
  AGGREGATE pre-2017 tail (observed CPR 5.264%, differential +0.962pp vs the
  sampled universe's 4.303%, 0.48% exposure share, $8.44B of the $11.75B bound).
  This leg RE-AGGREGATES THE SAME INGEST CELLS to report a 2015-2016-SPECIFIC
  figure, plus the residual pre-2015 tail so the decomposition is complete.
  It changes NOTHING upstream: same loader, same QT window, same pooled-dollar
  CPR convention, same face share and sensitivity anchors.  The aggregation
  helpers (pooled_cpr_pct / mean_monthly_cpr_pct) and every anchor constant are
  IMPORTED from vintage_residual_bound, not re-derived.

INPUTS (all local or committed; nothing fetched)
  data/fannie_quarters/cells_FNMA{2017Q1..2022Q4}.parquet  (24 files, local,
      gitignored) — the identical cells vintage_residual_bound consumes;
      columns used: vintage, period, exposure_upb, prepaid_upb, loan_count.
  data/fannie_quarters/manifest.json  (local) — staged_loans / staged_rows /
      cells_rows per quarter (G2 tie).
  data/fannie_replication_results.json  (committed, artifact d8199eb) —
      universe block for the local-manifest-vs-committed tie.
  data/vintage_residual_bound_results.json  (committed round-16 artifact) —
      the parity reference: committed sampled/2022/pre-2017 CPRs, the $11.75B
      bound, and the $8.44B pre-2017 leg bound are read from here and MUST be
      reproduced EXACTLY from the cells before any re-cutting (G1).
  data/ginnie_bound.json, data/expectation_benchmark_results.json — anchor
      constants (sensitivity 82.8 $B/pp; benchmark 764.7482532227002 $B).
  hazard/wal_table.py VINTAGE_SHARES — the 10.6% pre-2017 face share (imported
      via vintage_residual_bound.SHARE_PRE2017).
  common/qt_window.py — QT window bounds (single source of truth).

CONSTRUCTION (exact, deterministic; no randomness, no wall-clock in artifact)
  1. Load the 24 cell files, concat, mask to the QT window (half-open
     2022-06-01 <= period < 2025-12-01, 42 months) — the SAME loader/mask the
     parent uses.
  2. Segments by origination vintage (partition of the parent's pre_2017 leg):
       sampled_2017_2021: vintage in VINTAGE_YEARS (2017-2021) — sampled proxy;
       vintage_2022:      vintage == 2022;
       pre_2017:          vintage <= 2016  (the committed aggregate tail);
       vintage_2015_2016: vintage in {2015, 2016}  (referee's named cohorts);
       pre_2015:          vintage <= 2014  (residual tail, completes pre_2017).
  3. Per-segment window CPR via the IMPORTED pooled_cpr_pct: compound-annualized
     pooled dollar SMM (== exposure-weighted mean monthly SMM), the house
     convention for observed speeds.  Disclosed secondary variant: the imported
     mean_monthly_cpr_pct (unweighted window mean of monthly pooled CPRs).
  4. 2015-2016-specific reporting (referee-facing):
       observed_speed_pct       = pooled_cpr_pct(vintage_2015_2016)
       differential_pp          = observed_speed_pct - CPR_sampled
       exposure_share_of_observed_pct, exposure_share_within_pre2017_pct
       full_share_leg_bound_b   = 0.106 * differential_pp * 82.8  — the 2015-16
           speed carrying the ENTIRE pre-2017 face share (2015-16 is ~99.99% of
           the pre-2017 observed exposure), a drop-in for the committed $8.44B
           pre-2017 leg;
       book_bound_with_1516_b   = |0.231*d_2022 + 0.106*differential_pp| * 82.8
           and its % of benchmark — the total bound with the 2015-16 speed
           substituted for the pre-2017 tail (essentially the committed
           $11.75B / 1.54%).
  5. Residual pre-2015 tail reported symmetrically (observed_speed_pct,
     differential_pp, exposure share, loan-months, vintages present) so the
     decomposition is complete and auditable.
  6. Exposure-split additive decomposition of the committed $8.44B pre-2017 leg
     bound (share_pre2017 apportioned by each sub-segment's share of pre-2017
     observed exposure) is reported alongside; the two split legs sum to the
     committed pre-2017 leg to within the CPR-nonlinearity gap (pooled CPR is
     not exposure-linear), the gap being reported.  The HARD additivity gate
     (G3) is at the dollar / loan-month level, where the partition is exact.

GATES (numbered; reference + tolerance + source; artifact with results is
written ONLY if all pass — on failure a GATE_FAILURE stub is written and the
process exits nonzero)
  G1 parity — reproduce the committed round-16 figures EXACTLY from the cells
     before re-cutting: sampled/2022/pre-2017 pooled CPRs, the $11.75B bound,
     and the $8.44B pre-2017 leg bound, each read from
     vintage_residual_bound_results.json, matched to abs tol 1e-9 (observed
     bit-identical at spec time — same cells, same imported pooled_cpr_pct).
  G2 manifest integrity — exactly the 24 spec tags present as cell files and
     manifest entries; each cell file's rows == its manifest cells_rows;
     manifest staged_loans / staged_rows totals == the COMMITTED
     fannie_replication_results.json universe (17,606,999 / 825,814,383);
     observed vintage range within [2010, 2022].  (Same construction as the
     parent's G2; the imported TAGS / paths are the single source.)
  G3 additivity + coverage — the 2015-16 and pre-2015 segments partition the
     pre_2017 leg:
       (a) exposure_upb sum: exp(2015-16) + exp(pre-2015) == exp(pre_2017)
           EXACTLY (same rows repartitioned; observed diff 0.0 at spec time);
       (b) loan_count sum: lc(2015-16) + lc(pre-2015) == lc(pre_2017) EXACTLY
           (3,444,695 + 332 == 3,445,027 at spec time);
       (c) prepaid_upb sum: within rel tol 1e-12 (float-summation order only;
           observed rel ~2e-16 at spec time);
       (d) recombined pooled CPR from the summed sub-segment dollars ==
           committed pre-2017 CPR within abs tol 1e-9 pp;
       (e) vintage-set completeness: {2015-16 vintages} U {pre-2015 vintages}
           == {pre_2017 vintages}, disjoint (no vintage dropped or
           double-counted);
       (f) coverage: the 2015-16 segment has full 42-month QT coverage
           (42 == common.qt_window.expected_qt_active_months()); pre-2015
           coverage/loan-months reported (degenerate tail; non-gating).
  G4 constants integrity — anchors equal their committed sources (imported):
     sensitivity 82.8 == ginnie_bound.json trapped_sensitivity_b_per_pp;
     share_pre2017 0.106 == wal_table VINTAGE_SHARES["pre2017"];
     benchmark 764.7482532227002 == expectation_benchmark_results.json
     cap_benchmark_b (abs tol 1e-9).

PRE-COMMITTED INTERPRETATION (fixed ex ante)
  Because 2015-16 carries ~99.99% of the pre-2017 observed exposure, the
  isolated 2015-16 figure is expected to essentially coincide with the
  committed pre-2017 aggregate; the finding is a REFINEMENT confirming the
  referee's named cohorts sit inside the already-priced tail, not a new bound.
  Sign travels unchanged from the parent: a POSITIVE differential (2015-16
  prepaid FASTER than the sampled universe) signs the extrapolation error
  toward OVERSTATING trapped liquidity — conservative for the headline, the
  same direction as the static Ginnie composition bound.  Whichever numbers
  obtain are the reading; no post-hoc reframing.

CAVEATS (inherited from the parent, stated ex ante)
  * Fannie observed speeds proxy the SOMA book's segment behavior.
  * The 2015-16 / pre-2015 legs are the seasoned tail of the 2017+ acquisition
    files (a survivor-composition-tilted subset), not a random draw of
    2015-16 / pre-2015 originations; the 10.6% pre-2017 face share is applied
    as-is.
  * The pre-2015 residual is degenerate (a few hundred QT loan-months across
    vintages 2010-2013; no 2014 vintage present in the ingest) and is reported
    for completeness, not as an estimate.

OUTPUT
  data/vintage_1516_subleg_results.json — headline statistics ONLY (no
  per-quarter / per-cell values), same provenance posture as the parent.

Run:  cd hazard && python3 vintage_1516_subleg.py   (~seconds; pure arithmetic
      on local parquet + committed JSON; no network, no engine)
"""
from __future__ import annotations

import json
import time

import polars as pl

# Reuse — do NOT duplicate — the parent's loader constants and aggregation.
from config import QT_END, QT_START, VINTAGE_YEARS
from common.qt_window import expected_qt_active_months
from vintage_residual_bound import (
    BENCHMARK_B,
    EXPECT_BENCH_JSON,
    GINNIE_BOUND_JSON,
    MANIFEST_PATH,
    QUARTER_DIR,
    REPLICATION_JSON,
    RESULTS_JSON as PARENT_RESULTS_JSON,
    SENSITIVITY_B_PER_PP,
    SHARE_2022,
    SHARE_PRE2017,
    TAGS,
    VINTAGE_RANGE,
    mean_monthly_cpr_pct,
    pooled_cpr_pct,
)
from config import DATA_DIR

RESULTS_JSON = DATA_DIR / "vintage_1516_subleg_results.json"

G1_ABS_TOL = 1e-9          # reproduce committed CPRs / bounds (bit-identical at spec time)
G3_ADD_REL_TOL = 1e-12     # prepaid additivity (float-summation order only)
G3_CPR_ABS_TOL = 1e-9      # recombined-CPR vs committed pre-2017 CPR (pp)
G4_ABS_TOL = 1e-9


def _fail(gates: dict, msg: str) -> None:
    RESULTS_JSON.write_text(json.dumps(
        {"mode": "vintage_1516_subleg", "status": "GATE_FAILURE",
         "gates": gates, "detail": msg}, indent=2, default=float) + "\n")
    raise SystemExit(f"GATE FAILURE — {msg} (results not written)")


def _seg_stats(frame: pl.DataFrame, total_exp: float, pre2017_exp: float,
               cpr_sampled: float) -> dict:
    exp = float(frame["exposure_upb"].sum())
    return {
        "cpr_pct": pooled_cpr_pct(frame),
        "mean_monthly_cpr_pct": mean_monthly_cpr_pct(frame),
        "qt_months": int(frame["period"].n_unique()),
        "qt_loan_months": int(frame["loan_count"].sum()),
        "qt_exposure_usd_t": exp / 1e12,
        "exposure_share_of_observed_pct": exp / total_exp * 100.0,
        "exposure_share_within_pre2017_pct": exp / pre2017_exp * 100.0,
        "differential_pp": pooled_cpr_pct(frame) - cpr_sampled,
        "vintages_present": sorted(int(v) for v in frame["vintage"].unique()),
    }


def main() -> None:
    t0 = time.perf_counter()
    gates: dict = {}

    manifest = json.load(open(MANIFEST_PATH))
    replication = json.load(open(REPLICATION_JSON))
    ginnie = json.load(open(GINNIE_BOUND_JSON))
    bench_src = json.load(open(EXPECT_BENCH_JSON))
    committed = json.load(open(PARENT_RESULTS_JSON))
    c_seg = committed["results"]["segments"]
    C_SAMPLED = c_seg["sampled_2017_2021"]["cpr_pct"]
    C_2022 = c_seg["vintage_2022"]["cpr_pct"]
    C_PRE2017 = c_seg["pre_2017"]["cpr_pct"]
    C_BOUND_B = committed["results"]["bound_b"]
    C_PRE2017_LEG_B = committed["results"]["leg_bound_pre2017_b"]

    cell_paths = {t: QUARTER_DIR / f"cells_{t}.parquet" for t in TAGS}
    frames = {t: pl.read_parquet(p) for t, p in cell_paths.items() if p.exists()}

    # ---- G2 manifest integrity (same construction as parent) ----------------
    missing_files = [t for t in TAGS if t not in frames]
    manifest_tags_ok = sorted(manifest.keys()) == sorted(TAGS)
    per_file_ok = all(f.height == manifest.get(t, {}).get("cells_rows")
                      for t, f in frames.items())
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

    # ---- QT window mask + segments (same convention as parent) --------------
    qt = cells.filter((pl.col("period") >= QT_START.to_pydatetime())
                      & (pl.col("period") < QT_END.to_pydatetime()))
    n_months_expected = expected_qt_active_months()  # 42
    seg = {
        "sampled_2017_2021": qt.filter(pl.col("vintage").is_in(list(VINTAGE_YEARS))),
        "vintage_2022": qt.filter(pl.col("vintage") == 2022),
        "pre_2017": qt.filter(pl.col("vintage") <= 2016),
        "vintage_2015_2016": qt.filter(pl.col("vintage").is_in([2015, 2016])),
        "pre_2015": qt.filter(pl.col("vintage") <= 2014),
    }

    cpr = {k: pooled_cpr_pct(v) for k, v in seg.items()}

    # ---- G1 parity: reproduce committed figures EXACTLY before re-cutting ----
    d_2022 = cpr["vintage_2022"] - cpr["sampled_2017_2021"]
    d_pre2017 = cpr["pre_2017"] - cpr["sampled_2017_2021"]
    e_book = SHARE_2022 * d_2022 + SHARE_PRE2017 * d_pre2017
    bound_b = abs(e_book) * SENSITIVITY_B_PER_PP
    pre2017_leg_b = SHARE_PRE2017 * d_pre2017 * SENSITIVITY_B_PER_PP
    g1 = {
        "cpr_sampled": {"got": cpr["sampled_2017_2021"], "want": C_SAMPLED,
                        "pass": abs(cpr["sampled_2017_2021"] - C_SAMPLED) <= G1_ABS_TOL},
        "cpr_2022": {"got": cpr["vintage_2022"], "want": C_2022,
                     "pass": abs(cpr["vintage_2022"] - C_2022) <= G1_ABS_TOL},
        "cpr_pre2017": {"got": cpr["pre_2017"], "want": C_PRE2017,
                        "pass": abs(cpr["pre_2017"] - C_PRE2017) <= G1_ABS_TOL},
        "bound_b": {"got": bound_b, "want": C_BOUND_B,
                    "pass": abs(bound_b - C_BOUND_B) <= G1_ABS_TOL},
        "pre2017_leg_bound_b": {"got": pre2017_leg_b, "want": C_PRE2017_LEG_B,
                                "pass": abs(pre2017_leg_b - C_PRE2017_LEG_B) <= G1_ABS_TOL},
    }
    gates["G1_parity"] = {**g1, "abs_tol": G1_ABS_TOL,
                          "pass": all(v["pass"] for v in g1.values())}
    print(f"G1 parity vs committed round-16 artifact: sampled {cpr['sampled_2017_2021']:.6f}% "
          f"2022 {cpr['vintage_2022']:.6f}% pre2017 {cpr['pre_2017']:.6f}% "
          f"bound ${bound_b:.6f}B leg ${pre2017_leg_b:.6f}B  "
          f"{'PASS' if gates['G1_parity']['pass'] else 'FAIL'}")
    if not gates["G1_parity"]["pass"]:
        _fail(gates, "G1 parity vs committed vintage_residual_bound artifact failed")

    # ---- G4 constants integrity ---------------------------------------------
    g4 = {
        "sensitivity": {"got": ginnie["trapped_sensitivity_b_per_pp"], "want": SENSITIVITY_B_PER_PP,
                        "pass": ginnie["trapped_sensitivity_b_per_pp"] == SENSITIVITY_B_PER_PP},
        "share_pre2017": {"got": SHARE_PRE2017, "want": 0.106, "pass": SHARE_PRE2017 == 0.106},
        "benchmark": {"got": bench_src["cap_benchmark_b"], "want": BENCHMARK_B,
                      "pass": abs(bench_src["cap_benchmark_b"] - BENCHMARK_B) <= G4_ABS_TOL},
    }
    gates["G4_constants_integrity"] = {**g4, "pass": all(v["pass"] for v in g4.values())}
    print(f"G4 constants integrity: sensitivity {SENSITIVITY_B_PER_PP} $B/pp, "
          f"share_pre2017 {SHARE_PRE2017}, benchmark {BENCHMARK_B:.4f}  "
          f"{'PASS' if gates['G4_constants_integrity']['pass'] else 'FAIL'}")
    if not gates["G4_constants_integrity"]["pass"]:
        _fail(gates, "G4 constants integrity failed")

    # ---- segment statistics --------------------------------------------------
    total_exp = float(qt["exposure_upb"].sum())
    pre2017_exp = float(seg["pre_2017"]["exposure_upb"].sum())
    cpr_s = cpr["sampled_2017_2021"]
    stats = {k: _seg_stats(v, total_exp, pre2017_exp, cpr_s) for k, v in seg.items()}

    # ---- G3 additivity + coverage -------------------------------------------
    exp_1516 = float(seg["vintage_2015_2016"]["exposure_upb"].sum())
    exp_pre15 = float(seg["pre_2015"]["exposure_upb"].sum())
    prep_1516 = float(seg["vintage_2015_2016"]["prepaid_upb"].sum())
    prep_pre15 = float(seg["pre_2015"]["prepaid_upb"].sum())
    prep_pre2017 = float(seg["pre_2017"]["prepaid_upb"].sum())
    lc_1516 = int(seg["vintage_2015_2016"]["loan_count"].sum())
    lc_pre15 = int(seg["pre_2015"]["loan_count"].sum())
    lc_pre2017 = int(seg["pre_2017"]["loan_count"].sum())

    exp_add_ok = (exp_1516 + exp_pre15) == pre2017_exp
    lc_add_ok = (lc_1516 + lc_pre15) == lc_pre2017
    prep_add_diff = (prep_1516 + prep_pre15) - prep_pre2017
    prep_add_ok = abs(prep_add_diff) <= G3_ADD_REL_TOL * abs(prep_pre2017)
    smm_recomb = (prep_1516 + prep_pre15) / (exp_1516 + exp_pre15)
    cpr_recomb = (1.0 - (1.0 - smm_recomb) ** 12) * 100.0
    cpr_recomb_ok = abs(cpr_recomb - C_PRE2017) <= G3_CPR_ABS_TOL
    v1516 = set(stats["vintage_2015_2016"]["vintages_present"])
    vpre15 = set(stats["pre_2015"]["vintages_present"])
    vpre2017 = set(stats["pre_2017"]["vintages_present"])
    vset_ok = (v1516 | vpre15) == vpre2017 and not (v1516 & vpre15)
    cover_1516_ok = stats["vintage_2015_2016"]["qt_months"] == n_months_expected
    gates["G3_additivity_coverage"] = {
        "exposure_add": {"exp_2015_2016": exp_1516, "exp_pre_2015": exp_pre15,
                         "sum": exp_1516 + exp_pre15, "pre_2017": pre2017_exp,
                         "exact": exp_add_ok},
        "loan_count_add": {"lc_2015_2016": lc_1516, "lc_pre_2015": lc_pre15,
                           "sum": lc_1516 + lc_pre15, "pre_2017": lc_pre2017,
                           "exact": lc_add_ok},
        "prepaid_add": {"sum": prep_1516 + prep_pre15, "pre_2017": prep_pre2017,
                        "abs_diff": prep_add_diff, "rel_tol": G3_ADD_REL_TOL,
                        "pass": prep_add_ok},
        "recombined_cpr": {"got": cpr_recomb, "committed_pre2017": C_PRE2017,
                           "abs_diff_pp": abs(cpr_recomb - C_PRE2017),
                           "abs_tol_pp": G3_CPR_ABS_TOL, "pass": cpr_recomb_ok},
        "vintage_set_partition": {"v_2015_2016": sorted(v1516), "v_pre_2015": sorted(vpre15),
                                  "v_pre_2017": sorted(vpre2017), "disjoint_and_complete": vset_ok},
        "coverage": {"months_2015_2016": stats["vintage_2015_2016"]["qt_months"],
                     "months_pre_2015": stats["pre_2015"]["qt_months"],
                     "expected": n_months_expected,
                     "loan_months_pre_2015": lc_pre15,
                     "pass_2015_2016": cover_1516_ok},
        "pass": (exp_add_ok and lc_add_ok and prep_add_ok and cpr_recomb_ok
                 and vset_ok and cover_1516_ok),
    }
    print(f"G3 additivity+coverage: exp exact {exp_add_ok}, lc exact {lc_add_ok} "
          f"({lc_1516:,}+{lc_pre15}={lc_pre2017:,}), prepaid rel "
          f"{abs(prep_add_diff)/abs(prep_pre2017):.1e}, recombined CPR "
          f"{cpr_recomb:.6f}% (Δ{abs(cpr_recomb - C_PRE2017):.1e}pp), 2015-16 cover "
          f"{stats['vintage_2015_2016']['qt_months']}mo  "
          f"{'PASS' if gates['G3_additivity_coverage']['pass'] else 'FAIL'}")
    if not gates["G3_additivity_coverage"]["pass"]:
        _fail(gates, "G3 additivity/coverage failed")

    # ---- 2015-16-specific reporting -----------------------------------------
    d_1516 = stats["vintage_2015_2016"]["differential_pp"]
    d_pre15 = stats["pre_2015"]["differential_pp"]
    # (a) full-share: 2015-16 speed carrying the entire pre-2017 face share.
    full_share_leg_b = SHARE_PRE2017 * d_1516 * SENSITIVITY_B_PER_PP
    e_book_1516 = SHARE_2022 * d_2022 + SHARE_PRE2017 * d_1516
    book_bound_1516_b = abs(e_book_1516) * SENSITIVITY_B_PER_PP
    book_bound_1516_pct = book_bound_1516_b / BENCHMARK_B * 100.0
    # (b) exposure-split additive: apportion the 0.106 share by pre-2017 weight.
    w_1516 = exp_1516 / pre2017_exp
    w_pre15 = exp_pre15 / pre2017_exp
    split_share_1516 = SHARE_PRE2017 * w_1516
    split_share_pre15 = SHARE_PRE2017 * w_pre15
    split_leg_1516_b = split_share_1516 * d_1516 * SENSITIVITY_B_PER_PP
    split_leg_pre15_b = split_share_pre15 * d_pre15 * SENSITIVITY_B_PER_PP
    split_sum_b = split_leg_1516_b + split_leg_pre15_b
    nonlinearity_gap_b = split_sum_b - pre2017_leg_b

    sign_key = ("overstates_trapped" if d_1516 > 0
                else "understates_trapped" if d_1516 < 0 else "zero")

    payload = {
        "mode": "vintage_1516_subleg",
        "status": "PASS",
        "spec": ("round-18 R18-K optional light leg; re-aggregate the SAME "
                 "Fannie ingest cells to isolate the referee's named 2015-2016 "
                 "acquisition-vintage observed QT speed from the round-16 W2 "
                 "pre-2017 tail, with a completing pre-2015 residual (module "
                 "docstring, fixed ex ante). No upstream object modified; "
                 "loader/aggregation imported from vintage_residual_bound."),
        "qt_window": {"start": str(QT_START.date()), "end_exclusive": str(QT_END.date()),
                      "months": n_months_expected,
                      "source": "common/qt_window.py (half-open, production convention)"},
        "cpr_convention": ("pooled dollar SMM over the window, compound-annualized "
                           "CPR = 1-(1-SMM)^12 (imported pooled_cpr_pct); "
                           "mean-monthly variant disclosed"),
        "parent_run": {
            "script": "hazard/vintage_residual_bound.py",
            "artifact": "hazard/data/vintage_residual_bound_results.json",
            "committed_sampled_cpr_pct": C_SAMPLED,
            "committed_2022_cpr_pct": C_2022,
            "committed_pre2017_cpr_pct": C_PRE2017,
            "committed_bound_b": C_BOUND_B,
            "committed_pre2017_leg_bound_b": C_PRE2017_LEG_B,
        },
        "committed_anchors": {
            "benchmark_b": BENCHMARK_B,
            "sensitivity_b_per_pp": SENSITIVITY_B_PER_PP,
            "share_pre2017": SHARE_PRE2017,
            "share_2022": SHARE_2022,
            "source": ("imported from vintage_residual_bound (ginnie_bound.json / "
                       "expectation_benchmark_results.json / wal_table.VINTAGE_SHARES)"),
        },
        "gates": gates,
        "results": {
            "segments": stats,
            "vintage_2015_2016_specific": {
                "observed_speed_pct": cpr["vintage_2015_2016"],
                "mean_monthly_cpr_pct": stats["vintage_2015_2016"]["mean_monthly_cpr_pct"],
                "differential_vs_sampled_pp": d_1516,
                "sampled_universe_cpr_pct": cpr_s,
                "exposure_share_of_observed_pct": stats["vintage_2015_2016"]["exposure_share_of_observed_pct"],
                "exposure_share_within_pre2017_pct": stats["vintage_2015_2016"]["exposure_share_within_pre2017_pct"],
                "qt_loan_months": stats["vintage_2015_2016"]["qt_loan_months"],
                "vintages_present": stats["vintage_2015_2016"]["vintages_present"],
                "full_share_leg_bound_b": full_share_leg_b,
                "book_bound_with_1516_b": book_bound_1516_b,
                "book_bound_with_1516_pct_of_benchmark": book_bound_1516_pct,
                "sign_direction": sign_key,
                "note": ("2015-16 carries ~99.99% of the pre-2017 observed "
                         "exposure, so full_share_leg_bound_b is the drop-in "
                         "for the committed $8.44B pre-2017 leg and "
                         "book_bound_with_1516_b is essentially the committed "
                         "$11.75B / 1.54% bound."),
            },
            "pre_2015_residual": {
                "observed_speed_pct": cpr["pre_2015"],
                "differential_vs_sampled_pp": d_pre15,
                "exposure_share_of_observed_pct": stats["pre_2015"]["exposure_share_of_observed_pct"],
                "qt_loan_months": stats["pre_2015"]["qt_loan_months"],
                "vintages_present": stats["pre_2015"]["vintages_present"],
                "note": ("degenerate tail (a few hundred QT loan-months across "
                         "2010-2013; no 2014 vintage in the ingest); reported "
                         "for completeness only, not an estimate."),
            },
            "bound_decomposition": {
                "committed_pre2017_leg_bound_b": pre2017_leg_b,
                "exposure_split_leg_2015_2016_b": split_leg_1516_b,
                "exposure_split_leg_pre_2015_b": split_leg_pre15_b,
                "exposure_split_sum_b": split_sum_b,
                "cpr_nonlinearity_gap_b": nonlinearity_gap_b,
                "pre2017_weight_2015_2016": w_1516,
                "pre2017_weight_pre_2015": w_pre15,
                "note": ("exposure-split legs sum to the committed pre-2017 leg "
                         "to within the CPR-nonlinearity gap (pooled CPR is not "
                         "exposure-linear); the exact partition is at the "
                         "dollar/loan-month level in gate G3."),
            },
        },
        "caveats": [
            "Fannie observed speeds proxy the SOMA book (same posture as the parent run).",
            ("2015-16 / pre-2015 legs are the seasoned tail of 2017+ acquisition "
             "files (survivor-composition-tilted), not random 2015-16 / pre-2015 "
             "origination draws; the 10.6% pre-2017 face share is applied as-is."),
            ("pre-2015 residual is degenerate (a few hundred QT loan-months, "
             "vintages 2010-2013, no 2014); reported for completeness."),
        ],
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")

    print(f"\n2015-16 observed QT speed {cpr['vintage_2015_2016']:.6f}% "
          f"({d_1516:+.6f}pp vs sampled {cpr_s:.6f}%), exposure share "
          f"{stats['vintage_2015_2016']['exposure_share_of_observed_pct']:.6f}% "
          f"({stats['vintage_2015_2016']['exposure_share_within_pre2017_pct']:.4f}% of pre-2017 tail)")
    print(f"2015-16 full-share leg bound ${full_share_leg_b:.4f}B (vs committed "
          f"pre-2017 leg ${pre2017_leg_b:.4f}B); book bound w/2015-16 "
          f"${book_bound_1516_b:.4f}B ({book_bound_1516_pct:.4f}% of benchmark)")
    print(f"pre-2015 residual {cpr['pre_2015']:.6f}% ({d_pre15:+.6f}pp), "
          f"{stats['pre_2015']['qt_loan_months']} loan-months, vintages "
          f"{stats['pre_2015']['vintages_present']}")
    print(f"exposure-split additivity: 1516 ${split_leg_1516_b:.6f}B + pre2015 "
          f"${split_leg_pre15_b:.6f}B = ${split_sum_b:.6f}B (gap "
          f"${nonlinearity_gap_b:+.2e}B vs committed leg)")
    print(f"Results saved to {RESULTS_JSON}  ({time.perf_counter() - t0:.1f}s)")


if __name__ == "__main__":
    main()
