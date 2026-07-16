#!/usr/bin/env python3
"""
Expectations-based benchmark complement (pre-committed; spec fixed in this
header before any run executed — referee Q10, round-14 report).

Referee ask: the paper's $764.7B benchmark is CAP-relative (phased $17.5B →
$35B/month redemption caps), and market participants expected the caps to be
non-binding for MBS; complement the decomposition with a
"reasonable-expectation" benchmark (e.g., New York Fed staff projections) to
show the results are not an artifact of the cap-relative basis. The paper
currently argues the cap basis is the only non-circular one (III.D) while
itself citing the NY Fed projection — this run closes that tension with
arithmetic instead of argument.

SPEC (fixed ex ante):
- Expectation source, pinned: the SOMA agency-MBS paydown/runoff projection
  published in the Federal Reserve Bank of New York's "Open Market
  Operations During 2022" annual report (the projection vintage
  contemporaneous with QT's start — a genuine ex-ante expectation; the same
  document the manuscript already cites as nyfed2022). Baseline scenario.
  The published path is transcribed into PROJECTED_RUNOFF_B below at the
  granularity the report prints (with the report page/exhibit recorded in
  PROJECTION_PROVENANCE); if the report prints coarser-than-monthly totals,
  they are spread uniformly within each printed period (rule fixed here,
  before anyone sees what it does to the numbers).
- Window: June 2022 – November 2025 inclusive (the paper's 42 active QT
  months), matching the cap-relative benchmark's window exactly.
- Construction: E-shortfall = Σ projected runoff − Σ actual runoff over the
  window, with the actual leg computed by the SAME pipeline machinery as the
  production benchmark (macro.fetch_data + fetch_soma_mbs_monthly +
  build_empirical_metrics; no new empirical constructions). Every
  estimator's trapped-liquidity DOLLAR is unchanged by construction — this
  run re-QUOTES committed artifacts on the new basis; it re-runs nothing.
- Reported per estimator (from committed artifacts only: the production
  central/null caches' scored values as recorded in
  no_lockin_null_results.json, fannie_replication_results.json, and the
  ABM manifests' headline dollars): trapped $B (unchanged), share of the
  E-benchmark, and the lock-in marginal on both bases ($B identical;
  pp rescaled by the benchmark ratio).
- Gates: (i) transcription self-check — the transcribed path must reproduce
  the report's printed cumulative total (TRANSCRIPTION_TOTAL_B) exactly;
  (ii) parity — the cap-relative shares recomputed here from committed
  artifacts must reproduce the published values to ±0.01pp (scoring-
  environment sanity, same convention as every other run); (iii) identity —
  share_E × E-benchmark == trapped_b to machine precision.
- Ex-ante interpretive threshold: the paper's mechanical-majority claim
  survives the basis change iff the β₁=0 null still recovers the majority
  (>50%) of the expectations-based shortfall; estimator RANKING and every
  dollar difference are basis-invariant by construction and are asserted,
  not argued. If the null's E-share falls below the central's by more than
  the cap-basis gap ±0.5pp, the basis choice is load-bearing and the
  manuscript must say so wherever the decomposition is quoted.
- Expected artifact: hazard/data/expectation_benchmark_results.json.

EXECUTION BLOCKER (deliberate): PROJECTED_RUNOFF_B is None until the
projection path is transcribed from the source document by a human (or an
agent quoting the exhibit verbatim) and recorded in PROJECTION_PROVENANCE.
The spec is committed first; the transcription is an input, not a choice —
nothing else in this file may change after transcription.

Run:  cd hazard && python3 expectation_benchmark.py
      -> data/expectation_benchmark_results.json
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "expectation_benchmark_results.json"
CAP_BENCHMARK_B = 764.748          # the production cap-relative benchmark
PARITY_TOL_PP = 0.01

# ---- SPEC AMENDMENT (disclosed 2026-07-16, BEFORE transcription) ------------
# The spec header pins "Open Market Operations During 2022" while requiring
# (a) a projection vintage contemporaneous with QT's start and (b) coverage
# of the full June 2022 - November 2025 window. Those clauses are satisfiable
# only by the report published DURING 2022: "Open Market Operations During
# 2021" (Markets Group, FRBNY, May 2022), whose projections start from the
# February 28, 2022 balance sheet, incorporate the FOMC's May 2022 Plans,
# and model runoff beginning June 2022. The "During 2022" report (published
# April 2023) projects from the December 30, 2022 balance sheet ("Projections
# start with the Federal Reserve balance sheet as of December 30, 2022",
# its Appendix 4) and cannot cover Jun-Dec 2022 at all, and contains no
# agency-MBS-specific paydown series. Root cause: title/vintage confusion in
# the round-14 spec sketch (the same sketch also mis-identified the report
# with the manuscript's nyfed2022, which is the September 2022 Teller Window
# post). Document name corrected here, in a commit that PRECEDES the
# transcription commit so the ordering is auditable; every other spec clause
# (window, construction, gates, threshold, spread rule) is unchanged. Same
# amendment convention as TECHNICAL.md §24.2 (a3ef6b7).

# ---- REQUIRED TRANSCRIPTION (see EXECUTION BLOCKER in the spec) ------------
# The report's agency-MBS projection (Chart 34) is published as YEAR-END
# HOLDINGS LEVELS, not runoff flows; the transcription constants below are
# therefore the five published levels, quoted verbatim from the NY Fed's own
# published chart-data workbook for the report (omo2021-xls.xlsx, sheet
# "Chart 34", column "Agency MBS", $B; 2021 historical, 2022+ projected).
# PROJECTED_RUNOFF_B and TRANSCRIPTION_TOTAL_B are derived from these levels
# by first difference / telescoping — exact arithmetic on published values.
# Consequence for gate (i), disclosed: for a levels-format source the
# self-check reduces to a telescoping identity, so its evidentiary weight
# rests on the workbook citation below and on the independent verification
# recorded in TECHNICAL.md §25.5 (workbook re-read, chart-render match, and
# printed text anchors), not on the assert alone.
PUBLISHED_YE_AGENCY_MBS_LEVELS_B: dict = {
    "2021": 2615.5,   # historical year-end level
    "2022": 2599.6,   # projected
    "2023": 2319.9,   # projected
    "2024": 2072.8,   # projected
    "2025": 1849.7,   # projected
}
# {"YYYY": projected agency-MBS runoff, $B} at the report's printed
# (annual) granularity: first difference of the published levels.
PROJECTED_RUNOFF_B: dict | None = {
    str(y): (PUBLISHED_YE_AGENCY_MBS_LEVELS_B[str(y - 1)]
             - PUBLISHED_YE_AGENCY_MBS_LEVELS_B[str(y)])
    for y in (2022, 2023, 2024, 2025)
}
# The published cumulative total for the transcribed horizon: the telescoped
# decline between the two published endpoint levels, YE2021 minus YE2025.
TRANSCRIPTION_TOTAL_B: float | None = (
    PUBLISHED_YE_AGENCY_MBS_LEVELS_B["2021"]
    - PUBLISHED_YE_AGENCY_MBS_LEVELS_B["2025"]
)
PROJECTION_PROVENANCE: str | None = (
    "Federal Reserve Bank of New York, 'Open Market Operations During 2021' "
    "(report to the FOMC, published May 2022 per the report cover; the "
    "workbook's own cover sheet carries a 'Released: May 2021' typo), "
    "Chart 34 'Projected SOMA Domestic Securities Holdings by Asset Class', "
    "printed p.49 (PDF p.51), baseline scenario (the report's single path: "
    "May 2022 Plans caps, no MBS sales, runoff modeled from June 2022; "
    "projections start from the February 28, 2022 balance sheet per "
    "Appendix 4). Levels from the NY Fed's published chart-data workbook "
    "https://www.newyorkfed.org/medialibrary/media/markets/omo/"
    "omo2021-xls.xlsx, sheet 'Chart 34', column 'Agency MBS'. Cross-checks: "
    "Treasuries+MBS reproduce the report's printed anchors (YE2025 total "
    "5963.9 ~ the printed '$5.9 trillion' mid-2025 plateau; agency share "
    "32.4% at YE2022 vs printed 'roughly 32 percent through 2025'; the "
    "report's printed p.31 (PDF p.33) '$2.61 trillion (32 percent)' matches "
    "the YE2021 level). "
    "Note, direction disclosed: the 2022 printed period nets first-half-2022 "
    "settlement inflows against Jun-Dec runoff, so the in-window projected "
    "runoff for 2022 is if anything UNDERSTATED, which understates the "
    "E-benchmark and overstates every share_E."
)


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    if PROJECTED_RUNOFF_B is None or TRANSCRIPTION_TOTAL_B is None:
        raise SystemExit(
            "expectation_benchmark: PROJECTED_RUNOFF_B not yet transcribed "
            "from the pinned source (see PROJECTION_PROVENANCE requirements "
            "in the spec header). The spec is committed; fill the constants "
            "with the report's printed values and rerun. Nothing else in "
            "this file may change."
        )

    t0 = time.perf_counter()
    from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

    # (i) transcription self-check
    total = float(sum(PROJECTED_RUNOFF_B.values()))
    assert abs(total - TRANSCRIPTION_TOTAL_B) < 1e-9, (
        f"transcription does not reproduce the printed total: "
        f"{total} vs {TRANSCRIPTION_TOTAL_B}"
    )

    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    # Actual runoff over the window from the same pipeline objects the
    # production benchmark uses; E-shortfall = projected − actual.
    from macro import qt_active_frame

    qt_emp = qt_active_frame(empirical)
    assert len(qt_emp) == 42, f"QT window is {len(qt_emp)} months, want 42"
    cap_benchmark = float(qt_emp["Extension_Delta_Billions"].sum())
    # Environment-sanity: the live-recomputed cap benchmark must reproduce
    # the pinned production constant (makes CAP_BENCHMARK_B load-bearing).
    assert abs(cap_benchmark - CAP_BENCHMARK_B) < 0.01, cap_benchmark
    actual_decline_b = -float(qt_emp["Actual_Monthly_Rolloff_Billions"].sum())

    # Spread rule (fixed in the spec header): each printed period's runoff is
    # spread uniformly over its calendar months, then clipped to the window.
    monthly: dict[str, float] = {}
    for key, v in PROJECTED_RUNOFF_B.items():
        months = ([f"{key}-{m:02d}" for m in range(1, 13)]
                  if len(key) == 4 else [key])
        for m in months:
            monthly[m] = monthly.get(m, 0.0) + float(v) / len(months)
    window_months = [p.strftime("%Y-%m") for p in qt_emp.index.to_period("M")]
    missing = [m for m in window_months if m not in monthly]
    assert not missing, f"projection does not cover window months: {missing}"
    projected_window_b = float(sum(monthly[m] for m in window_months))

    e_benchmark = projected_window_b - actual_decline_b

    # ---- Estimator re-quotes (committed artifacts only) --------------------
    null_art = json.loads((DATA_DIR / "no_lockin_null_results.json").read_text())
    fannie_art = json.loads(
        (DATA_DIR / "fannie_replication_results.json").read_text())
    manifest = json.loads(
        (DATA_DIR.parent.parent / "abm" / "data" / "runs"
         / "run-2026-07-04-15yr-foldin" / "manifest.json").read_text())
    shared_art = json.loads(
        (DATA_DIR / "shared_layer_scoring_results.json").read_text())

    estimators = {
        "path_b_central": {
            "trapped_b": null_art["central_trapped_b"],
            "published_share_cap_pct": null_art["central_share_pct"],
        },
        "path_b_null": {
            "trapped_b": null_art["null_trapped_b"],
            "published_share_cap_pct": null_art["null_share_pct"],
        },
        "fannie_central": {
            "trapped_b": fannie_art["path_b"]["central_trapped_b"],
            "published_share_cap_pct": fannie_art["path_b"]["central_share_pct"],
        },
        "fannie_null": {
            "trapped_b": fannie_art["path_b"]["null_trapped_b"],
            "published_share_cap_pct": fannie_art["path_b"]["null_share_pct"],
        },
        "abm_production": {
            "trapped_b": manifest["metrics"]["dollars_b"]["us_trapped"],
            "published_share_cap_pct":
                manifest["metrics"]["dollars_b"]["share_explained_pct"],
        },
    }

    # (ii) parity gate — cap-relative shares recomputed here must reproduce
    # the published values to ±0.01pp.
    parity_ok = True
    for name, row in estimators.items():
        row["share_cap_pct"] = row["trapped_b"] / cap_benchmark * 100.0
        row["parity_diff_pp"] = (
            row["share_cap_pct"] - row["published_share_cap_pct"])
        if abs(row["parity_diff_pp"]) > PARITY_TOL_PP:
            parity_ok = False
    assert parity_ok, "cap-basis parity gate failed: " + json.dumps(
        {k: v["parity_diff_pp"] for k, v in estimators.items()})

    # (iii) identity gate — share_E × E-benchmark == trapped_b exactly.
    for row in estimators.values():
        row["share_E_pct"] = row["trapped_b"] / e_benchmark * 100.0
        assert abs(row["share_E_pct"] / 100.0 * e_benchmark
                   - row["trapped_b"]) < 1e-9

    marginal_b = (estimators["path_b_central"]["trapped_b"]
                  - estimators["path_b_null"]["trapped_b"])
    marginal_pp_cap = marginal_b / cap_benchmark * 100.0
    marginal_pp_e = marginal_b / e_benchmark * 100.0

    # Ex-ante interpretive threshold and load-bearing trigger from the spec.
    # The trigger is implemented two-sided (|E-gap − cap-gap| > 0.5pp), the
    # conservative reading of the spec's one-sided prose.
    null_share_e = estimators["path_b_null"]["share_E_pct"]
    survives = null_share_e > 50.0
    gap_e_pp = (estimators["path_b_central"]["share_E_pct"] - null_share_e)
    basis_load_bearing = abs(gap_e_pp - marginal_pp_cap) > 0.5

    # Supplementary translation (NOT gated; reported for legibility): the
    # projection-implied cap-shortfall wedge is common to every estimator,
    # so, like the shared/standalone netting, it cancels from the marginal
    # and from every dollar difference. The comparison figure (the null's
    # benchmark-consistent shared-basis recovery) is READ from the committed
    # shared-layer artifact, not hard-coded.
    cap_target_b = -float(qt_emp["QT_Target_Billions"].sum())
    projection_implied_cap_shortfall_b = cap_target_b - projected_window_b
    expected_share_of_cap_shortfall_pct = (
        projection_implied_cap_shortfall_b / cap_benchmark * 100.0)
    null_shared_share_pct = float(
        shared_art["results"]["no_lockin_null"]["share_pct"])
    expected_vs_null_shared_pp = (
        expected_share_of_cap_shortfall_pct - null_shared_share_pct)

    # Amendment (disclosed, post-first-run; supplementary, NOT gated): the
    # anticipated-share point value rides on the pre-committed uniform-spread
    # rule for the projection's printed 2022 ANNUAL NET (-$15.9B), which nets
    # first-half settlement inflows against Jun-Dec runoff. A settlement-aware
    # allocation instead assigns the first-half rise to Jan-May (proxy: the
    # REALIZED Jan-May 2022 change in the same SOMA series the benchmark
    # uses), implying Jun-Dec projected runoff of (annual net + H1 rise).
    # This bounds the anticipated share from below; the pre-committed rule's
    # 88.5% is the upper end. Both allocations leave the large-majority
    # reading and the >50% threshold unchanged.
    h1_2022_rise_b = float(soma.loc["2022-01":"2022-05"].sum())
    alt_2022_window_b = float(PROJECTED_RUNOFF_B["2022"]) + h1_2022_rise_b
    projected_window_alt_b = (projected_window_b
                              - float(PROJECTED_RUNOFF_B["2022"]) * 7.0 / 12.0
                              + alt_2022_window_b)
    wedge_alt_b = cap_target_b - projected_window_alt_b
    share_alt_pct = wedge_alt_b / cap_benchmark * 100.0
    e_alt_b = projected_window_alt_b - actual_decline_b
    null_share_e_alt_pct = (estimators["path_b_null"]["trapped_b"]
                            / e_alt_b * 100.0)

    payload = {
        "mode": "expectation_benchmark",
        "spec": "hazard/expectation_benchmark.py header (committed 88ef11e); "
                "document-name amendment committed pre-transcription (see "
                "SPEC AMENDMENT block)",
        "projection_provenance": PROJECTION_PROVENANCE,
        "transcription": {
            "published_ye_agency_mbs_levels_b": PUBLISHED_YE_AGENCY_MBS_LEVELS_B,
            "printed_period_runoff_b": PROJECTED_RUNOFF_B,
            "transcription_total_b": TRANSCRIPTION_TOTAL_B,
            "self_check": (
                "PASS — reduces to a telescoping identity for a "
                "levels-format source; evidentiary weight on the workbook "
                "citation and the independent verification in TECHNICAL.md "
                "§25.5"),
        },
        "window": {
            "months": 42,
            "spread_rule": "uniform within printed period, clipped to window",
            "projected_runoff_window_b": projected_window_b,
            "actual_runoff_window_b": actual_decline_b,
            "rolloff_source": str(qt_emp["Rolloff_Source"].iloc[0]),
        },
        "e_benchmark_b": e_benchmark,
        "cap_benchmark_b": cap_benchmark,
        "gates": {
            "i_transcription_self_check":
                "PASS (telescoping identity; see transcription.self_check)",
            "ii_cap_parity": {
                k: v["parity_diff_pp"] for k, v in estimators.items()},
            "iii_identity": "PASS (machine precision)",
        },
        "estimators": estimators,
        "lockin_marginal": {
            "dollars_b": marginal_b,
            "pp_of_cap_benchmark": marginal_pp_cap,
            "pp_of_e_benchmark": marginal_pp_e,
        },
        "threshold": {
            "rule": "null share_E > 50%",
            "null_share_E_pct": null_share_e,
            "mechanical_majority_survives": survives,
        },
        "basis_load_bearing": {
            "rule": "|E-basis central-null gap - cap-basis gap| > 0.5pp "
                    "(two-sided, conservative reading of the spec's prose)",
            "gap_E_pp": gap_e_pp,
            "gap_cap_pp": marginal_pp_cap,
            "triggered": basis_load_bearing,
            "reading": (
                "pp magnitudes rescale by the benchmark ratio "
                f"({cap_benchmark / e_benchmark:.2f}x); dollars and rankings "
                "are basis-invariant. The manuscript must state that "
                "percentage-point magnitudes are cap-basis quantities."),
        },
        "supplementary_projection_wedge": {
            "cap_target_window_b": cap_target_b,
            "projection_implied_cap_shortfall_b":
                projection_implied_cap_shortfall_b,
            "expected_share_of_realized_cap_shortfall_pct":
                expected_share_of_cap_shortfall_pct,
            "null_shared_basis_share_pct": null_shared_share_pct,
            "expected_minus_null_shared_pp": expected_vs_null_shared_pp,
            "note": (
                "Share of the realized cap-shortfall that the NY Fed's "
                "ex-ante (May 2022) projection already anticipated, "
                "compared with the beta1=0 null's benchmark-consistent "
                "(shared-basis) recovery read from "
                "shared_layer_scoring_results.json. Supplementary, not "
                "gated."),
        },
        "settlement_aware_allocation": {
            "h1_2022_realized_rise_b": h1_2022_rise_b,
            "implied_jun_dec_2022_projected_runoff_b": alt_2022_window_b,
            "projected_runoff_window_b": projected_window_alt_b,
            "projection_implied_cap_shortfall_b": wedge_alt_b,
            "expected_share_of_realized_cap_shortfall_pct": share_alt_pct,
            "e_benchmark_b": e_alt_b,
            "null_share_E_pct": null_share_e_alt_pct,
            "threshold_survives": null_share_e_alt_pct > 50.0,
            "note": (
                "Disclosed post-first-run amendment; supplementary, not "
                "gated. Lower bound on the anticipated share under an "
                "allocation that assigns the projection's 2022 first-half "
                "settlement inflows to Jan-May (proxy: realized H1-2022 "
                "change in the benchmark's own SOMA series); the "
                "pre-committed uniform-spread rule's value is the upper "
                "end. The anticipated share is bounded within roughly "
                "three-quarters to nine-tenths under any defensible "
                "intra-2022 allocation."),
        },
        "runtime_s": round(time.perf_counter() - t0, 1),
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": _git_head(),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")

    print(f"E-benchmark: projected {projected_window_b:.3f}B - actual "
          f"{actual_decline_b:.3f}B = {e_benchmark:.3f}B "
          f"(cap benchmark {cap_benchmark:.3f}B)")
    print(f"Parity gate (ii): max |diff| "
          f"{max(abs(v['parity_diff_pp']) for v in estimators.values()):.2e} pp"
          f" -> PASS")
    for name, row in estimators.items():
        print(f"  {name:>16}: trapped {row['trapped_b']:8.2f}B  cap "
              f"{row['share_cap_pct']:6.1f}%  E {row['share_E_pct']:7.1f}%")
    print(f"Marginal: {marginal_b:+.2f}B = {marginal_pp_cap:+.2f}pp (cap) = "
          f"{marginal_pp_e:+.2f}pp (E)")
    print(f"Threshold: null share_E {null_share_e:.1f}% > 50% -> "
          f"mechanical-majority {'SURVIVES' if survives else 'FAILS'}")
    print(f"Load-bearing trigger: {'FIRES' if basis_load_bearing else 'no'} "
          f"(E-gap {gap_e_pp:+.1f}pp vs cap-gap {marginal_pp_cap:+.1f}pp)")
    print(f"Projection-implied cap-shortfall: "
          f"{projection_implied_cap_shortfall_b:.2f}B = "
          f"{expected_share_of_cap_shortfall_pct:.2f}% of the realized "
          f"cap-shortfall, vs null shared-basis "
          f"{null_shared_share_pct:.2f}% (diff "
          f"{expected_vs_null_shared_pp:+.2f}pp)")
    print(f"Settlement-aware allocation (lower bound): H1-2022 rise "
          f"{h1_2022_rise_b:.2f}B -> Jun-Dec projected {alt_2022_window_b:.2f}B, "
          f"window {projected_window_alt_b:.2f}B, anticipated share "
          f"{share_alt_pct:.2f}%, null share_E {null_share_e_alt_pct:.1f}% "
          f"(threshold {'survives' if null_share_e_alt_pct > 50 else 'FAILS'})")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
