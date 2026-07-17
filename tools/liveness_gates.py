#!/usr/bin/env python3
"""
Liveness gates: manuscript-vs-artifact checks as a runnable script
(pre-submission freeze item (iii) mechanized; see TECHNICAL.md §22).

Exit 0 iff ALL gates pass; each gate prints PASS/FAIL. Three gate classes:

1. Zero-count greps — phrases that must be ABSENT from the manuscript
   (retired claims, superseded numbers, and stale framing; each phrase's
   retirement is recorded in TECHNICAL.md §12.1/§22.4 or the run ledger).
2. Exactly-one greps — sentences that must be PRESENT exactly once
   (the ratified title and load-bearing provenance sentences).
3. Manuscript-vs-manifest cross-checks — a claim in the tex and a flag in
   a frozen run manifest must agree; failing when either side flips
   without the other (the defect class a review round caught in the
   Danish counterfactual's description).

Run:  python3 tools/liveness_gates.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "paper" / "v16" / "revised_paper_v16.tex"
MANIFEST = ROOT / "abm" / "data" / "runs" / "run-2026-07-04-15yr-foldin" / "manifest.json"
FANNIE_RESULTS = ROOT / "hazard" / "data" / "fannie_replication_results.json"
OVERLAY_RESULTS = ROOT / "hazard" / "data" / "ginnie_cpr_overlay_results.json"
DECOMP_RESULTS = ROOT / "hazard" / "data" / "marginal_decomposition_results.json"
ABMEXT_RESULTS = ROOT / "abm" / "data" / "abm_external_gates_results.json"
EXPECT_RESULTS = ROOT / "hazard" / "data" / "expectation_benchmark_results.json"
VINTAGE_RESULTS = ROOT / "hazard" / "data" / "vintage_residual_bound_results.json"
THEIL_RESULTS = ROOT / "figures" / "theil_data.json"
MLCOMP_RESULTS = ROOT / "hazard" / "data" / "ml_comparator_holdout_results.json"
COMPSHIFT_RESULTS = ROOT / "hazard" / "data" / "composition_shift_results.json"
FREEZE_RESULTS = ROOT / "abm" / "data" / "freeze_sensitivity_results.json"
ISOTONIC_RESULTS = ROOT / "hazard" / "data" / "landmark_isotonic_results.json"
MARGMONTH_RESULTS = ROOT / "hazard" / "data" / "marginal_monthly_decomposition_results.json"
INTERP_RESULTS = ROOT / "abm" / "data" / "interp_spot_check_results.json"
SMD_RESULTS = ROOT / "abm" / "data" / "smd_two_moment_results.json"
WALTAB_RESULTS = ROOT / "hazard" / "data" / "wal_table_results.json"
CURTDEMO_RESULTS = ROOT / "hazard" / "data" / "curtailment_profile_demo_results.json"
SPREADVAR_RESULTS = ROOT / "hazard" / "data" / "expectation_spread_variants_results.json"
DANBOUND_RESULTS = ROOT / "hazard" / "data" / "danish_discount_bound.json"


def _gates_ok(gates: dict) -> bool:
    """True iff every in-run gate entry reports pass (dict with 'pass', bool, or nested)."""
    def one(v):
        if isinstance(v, dict):
            if "pass" in v:
                return bool(v["pass"])
            return all(one(x) for x in v.values())
        return bool(v)
    return all(one(v) for v in gates.values())

ZERO_COUNT = [
    "production specification omits",
    "never route the same loan-month",
    "behavioral gate is future work",
    "Two items are bound",
    "10.26",
    "stranding an estimated",
    "roughly 13\\% of the benchmark",
    "That mortgage lock-in slowed",
    "1.3 years too long",
]

EXACTLY_ONE = [
    "\\title{Mortgage Lock-In and the Federal Reserve's Quantitative Tightening Shortfall}",
    "frozen manifests say otherwise",
    "9.96\\% of home value",
    "supersede this tag",
]

KERNEL_TEX_PHRASE = "kernel is retained in production"

# --- Post-freeze consistency pass (2026-07-14) ------------------------------
# Superseded spec v3 figures that must stay out of the tex except where
# explicitly labeled, ledger-completeness checks, and figure-script
# hardcoded-literal gates (the defect class the pass existed to kill:
# figure generators must READ committed artifacts, never carry the numbers).

# "894.8" (the spec v3 composed Path A) may appear only within 120 chars of
# a "spec v3" label; the unlabeled form was the §VII.F defect.
SUPERSEDED_CONTEXTUAL = {"894.8": "spec v3"}

# The Appendix A run ledger must record the Path A spec v3 -> v4 supersession.
LEDGER_SECTION = "\\section{Superseded Figures and Run Ledger}"
LEDGER_REQUIRED = ["spec v3", "121.5"]

FIGURE_SCRIPTS = [
    "figures/make_figures.py",
    "figures/make_ccf_data.py",
    "abm/monte_carlo_simulation.py",
]

# Benchmark shares (% of the $764.7B benchmark) and headline dollar figures
# that have ever been displayed in a figure; none may be hardcoded in a
# figure script (values arrive via json/manifest reads).
SHARE_LITERALS = [
    "119.7", "894.8", "117.0", "110.6", "112.4", "121.5", "127.5",
    "107.0", "109.1", "97.9", "96.9", "106.0", "100.04", "88.7",
    "59.3", "20.9", "11.9", "11.1", "71.1", "54.9", "45.1", "33.7",
    "764.7", "915.0", "915.1", "928.9", "905.1", "818.5", "834.6",
    "974.7", "91.0", "84.5", "453.5", "159.5", "765.1",
]

# The retracted timing convention may not reappear in any figure script.
FIGURE_FORBIDDEN = ["model CPR leads", "model leads", "TBA settlement"]

# Freeze item (ii), LaTeX half: every cross-reference goes through \ref —
# a hardcoded "Table 7" / "Section V.C" literal would silently drift when
# floats renumber. Comments are stripped before matching.
HARDCODED_XREF = {
    "Table N literal": r"Table[~ ]\d",
    "Figure N literal": r"Figure[~ ]\d",
    "Section roman literal": r"Section[~ ][IVX]+(?:\.[A-Z])?(?![a-zA-Z}])",
    "Appendix letter literal": r"Appendix[~ ][AB](?![a-zA-Z}])",
    "Equation (N) literal": r"[Ee]quation[~ ]\(\d\)",
}


def main() -> int:
    tex = TEX.read_text()
    failures = 0

    for phrase in ZERO_COUNT:
        n = tex.count(phrase)
        ok = n == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] zero-count {phrase!r}: {n}")

    for phrase in EXACTLY_ONE:
        n = tex.count(phrase)
        ok = n == 1
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] exactly-one {phrase!r}: {n}")

    import re
    tex_nc = re.sub(r"(?<!\\)%.*", "", tex)
    for label, pat in HARDCODED_XREF.items():
        n = len(re.findall(pat, tex_nc))
        ok = n == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] no-hardcoded-xref {label}: {n}")

    # --- Post-freeze pass gates ---------------------------------------------
    for phrase, label in SUPERSEDED_CONTEXTUAL.items():
        bad = 0
        start = 0
        while (idx := tex.find(phrase, start)) != -1:
            window = tex[max(0, idx - 120): idx + 120]
            if label not in window:
                bad += 1
            start = idx + len(phrase)
        ok = bad == 0
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] superseded-unless-labeled "
              f"{phrase!r} (label {label!r}): {bad} unlabeled")

    lstart = tex.find(LEDGER_SECTION)
    lend = tex.find("\\section{", lstart + 1) if lstart != -1 else -1
    ledger = tex[lstart:lend] if lstart != -1 and lend != -1 else ""
    for needle in LEDGER_REQUIRED:
        ok = lstart != -1 and needle in ledger
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] ledger-contains {needle!r}")

    for rel in FIGURE_SCRIPTS:
        src = (ROOT / rel).read_text()
        hits = [lit for lit in SHARE_LITERALS
                if re.search(rf"(?<![\d.]){re.escape(lit)}(?!\d)", src)]
        ok = not hits
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] figure-script-no-share-literals "
              f"{rel}: {hits if hits else 0}")
        fhits = [p for p in FIGURE_FORBIDDEN if p in src]
        ok = not fhits
        failures += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] figure-script-no-retracted-timing "
              f"{rel}: {fhits if fhits else 0}")

    manifest = json.loads(MANIFEST.read_text())
    flag = bool(manifest.get("pipeline", {}).get("apply_settlement_lag_kernel"))
    phrase_present = KERNEL_TEX_PHRASE in tex
    ok = flag == phrase_present
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check settlement-lag kernel: "
        f"manifest apply_settlement_lag_kernel={flag}, "
        f"tex {KERNEL_TEX_PHRASE!r} present={phrase_present} "
        f"(must agree; either side flipping without the other fails)"
    )

    # Round-14 W4: the manuscript's Fannie replication sentences must agree
    # with the committed artifact — the envelope gate must actually have
    # passed, and the printed marginal must be the artifact's, rounded as
    # printed (+$XX.X billion / +X.XX points). Same manifest-vs-tex contract
    # as the settlement-lag gate: either side moving without the other fails.
    fannie = json.loads(FANNIE_RESULTS.read_text())
    env = fannie["gates"]["gate_envelope"]
    claims = tex.count("run \\texttt{fannie\\_replication}")
    marg_b = f"+\\${fannie['path_b']['lockin_marginal_b']:.1f}"
    marg_pp = f"+{fannie['path_b']['lockin_marginal_share_pp']:.2f}"
    ok = (bool(env["pass"]) and claims == 1
          and marg_b in tex and marg_pp in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check fannie replication: "
        f"artifact envelope pass={env['pass']}, tex run-citation count="
        f"{claims} (want 1), marginal literals {marg_b!r}/{marg_pp!r} "
        f"present={marg_b in tex}/{marg_pp in tex}"
    )

    # Round-15 Q2: the Ginnie CPR overlay sentences must agree with the
    # committed artifact — G1 parity passed, the differential attribution
    # verdict is inside_static_bound, and the printed corrected shares and
    # differential are the artifact's, rounded as printed.
    ov = json.loads(OVERLAY_RESULTS.read_text())
    g3d = ov["gates"]["G3_static_bound"]["differential_attribution"]
    prim = ov["variants"]["primary"]
    claims = tex.count("run \\texttt{ginnie\\_cpr\\_overlay}")
    lit_central = f"{prim['central']['share_shared_pct']:.1f}\\%"
    lit_null = f"{prim['null']['share_shared_pct']:.1f}\\%"
    lit_diff = f"+\\${g3d['primary_minus_placebo_b']:.1f}"
    ok = (bool(ov["gates"]["G1_parity"]["pass"])
          and g3d["verdict_differential"] == "inside_static_bound"
          and claims == 1
          and lit_central in tex and lit_null in tex and lit_diff in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check ginnie overlay: "
        f"G1 pass={ov['gates']['G1_parity']['pass']}, differential verdict="
        f"{g3d['verdict_differential']}, tex run-citation count={claims} "
        f"(want 1), literals {lit_central!r}/{lit_null!r}/{lit_diff!r} "
        f"present={lit_central in tex}/{lit_null in tex}/{lit_diff in tex}"
    )

    # Round-15 Q3: the marginal-decomposition sentences must agree with the
    # committed artifact — parity gates passed, the additivity verdict is
    # shares_readable, and the printed composition shares are the artifact's.
    dec = json.loads(DECOMP_RESULTS.read_text())
    g3 = dec["gates"]["G3_additivity"]
    claims = tex.count("run \\texttt{marginal\\_decomposition}")
    cells = dec["cells"]
    top = max(c["share_of_sum_pct"] for c in cells)
    v2021 = sum(c["marginal_b"] for c in cells if c["vintage"] >= 2020)
    v_share = v2021 / g3["sum_cells_b"] * 100
    ok = (bool(dec["gates"]["G1_central_parity"]["pass"])
          and bool(dec["gates"]["G2_null_parity"]["pass"])
          and g3["verdict"] == "shares_readable"
          and claims == 1
          and all(c["marginal_b"] > 0 for c in cells)
          and abs(v_share - 72) < 1 and abs(top - 21) < 1)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check marginal decomposition: "
        f"G1/G2 pass, verdict={g3['verdict']}, tex run-citation count={claims} "
        f"(want 1), all-cells-positive={all(c['marginal_b'] > 0 for c in cells)}, "
        f"2020-21 share {v_share:.1f}% (printed 72%), max cell {top:.1f}% "
        f"(printed 21%)"
    )

    # Round-15 Q4: the ABM external-gates sentences must agree with the
    # committed artifact — both gates passed, and the printed recovery and
    # mobility scales are the artifact's, rounded as printed.
    ext = json.loads(ABMEXT_RESULTS.read_text())
    claims = tex.count("run \\texttt{abm\\_external\\_gates}")
    lit_share = f"{ext['results']['external']['share_pct']:.1f}\\%"
    scale_ext = ext["external_parameters"]["mobility_scale_external"]
    lit_scale = f"{scale_ext:,.0f}".replace(",", "{,}")
    ok = (bool(ext["gates"]["G1_harness_parity"]["pass"])
          and bool(ext["gates"]["G2_anchor"]["pass"])
          and bool(ext["floor_diagnostic"]["violates_observed_floor"])
          and claims == 1 and lit_share in tex and lit_scale in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check abm external gates: "
        f"G1/G2 pass, floor-violation={ext['floor_diagnostic']['violates_observed_floor']}, "
        f"tex run-citation count={claims} (want 1), literals "
        f"{lit_share!r}/{lit_scale!r} present={lit_share in tex}/{lit_scale in tex}"
    )

    # Round-15 Q10: the expectations-benchmark sentences must agree with the
    # committed artifact — the threshold must have survived, parity must be
    # inside tolerance, and the printed literals must be the artifact's,
    # rounded as printed.
    exp = json.loads(EXPECT_RESULTS.read_text())
    claims = tex.count("run \\texttt{expectation\\_benchmark}")
    wedge = exp["supplementary_projection_wedge"]
    lit_proj = f"\\${exp['window']['projected_runoff_window_b']:.1f}"
    lit_e = f"\\${exp['e_benchmark_b']:.1f}"
    lit_wedge_share = f"{wedge['expected_share_of_realized_cap_shortfall_pct']:.1f}\\%"
    max_parity = max(abs(v) for v in exp["gates"]["ii_cap_parity"].values())
    saa = exp["settlement_aware_allocation"]
    lit_h1 = f"\\${saa['h1_2022_realized_rise_b']:.1f}"
    lit_alt = f"{saa['expected_share_of_realized_cap_shortfall_pct']:.1f}\\%"
    ok = (bool(exp["threshold"]["mechanical_majority_survives"])
          and bool(saa["threshold_survives"])
          and max_parity <= 0.01
          and claims == 1
          and lit_proj in tex and lit_e in tex and lit_wedge_share in tex
          and lit_h1 in tex and lit_alt in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check expectation benchmark: "
        f"threshold survives={exp['threshold']['mechanical_majority_survives']}, "
        f"max parity |diff|={max_parity:.1e}pp, tex run-citation count={claims} "
        f"(want 1), literals {lit_proj!r}/{lit_e!r}/{lit_wedge_share!r} "
        f"present={lit_proj in tex}/{lit_e in tex}/{lit_wedge_share in tex}"
    )

    # Round-16 W2: the vintage-residual-bound sentences must agree with the
    # committed artifact — all four in-run gates passed, the pre-committed
    # verdict/sign are as printed, and the printed segment speeds and dollar
    # bound are the artifact's, rounded as printed.
    vin = json.loads(VINTAGE_RESULTS.read_text())
    vr = vin["results"]
    claims = tex.count("run \\texttt{vintage\\_residual\\_bound}")
    lit_bound = f"\\${vr['bound_b']:.1f} billion"
    lit_2022 = f"{vr['segments']['vintage_2022']['cpr_pct']:.2f}\\%"
    lit_pre = f"{vr['segments']['pre_2017']['cpr_pct']:.2f}\\%"
    lit_sampled = f"{vr['segments']['sampled_2017_2021']['cpr_pct']:.2f}\\%"
    ok = (all(bool(g["pass"]) for g in vin["gates"].values())
          and vr["interpretation"]["verdict"] == "below_ginnie_bound"
          and vr["sign_direction"] == "overstates_trapped"
          and claims == 1
          and lit_bound in tex and lit_2022 in tex and lit_pre in tex
          and lit_sampled in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check vintage residual bound: "
        f"in-run gates all pass={all(bool(g['pass']) for g in vin['gates'].values())}, "
        f"verdict={vr['interpretation']['verdict']}, sign={vr['sign_direction']}, "
        f"tex run-citation count={claims} (want 1), literals "
        f"{lit_bound!r}/{lit_sampled!r}/{lit_2022!r}/{lit_pre!r} present="
        f"{lit_bound in tex}/{lit_sampled in tex}/{lit_2022 in tex}/{lit_pre in tex}"
    )

    # Round-16 W4: the Theil dynamic-fit sentences and appendix table must
    # agree with the committed artifact — all nine in-run gates passed and
    # the printed U statistics and Path B / ABM error shares are the
    # artifact's, rounded as printed.
    thl = json.loads(THEIL_RESULTS.read_text())
    est = thl["estimators"]
    claims = tex.count("run \\texttt{make\\_theil\\_data}")
    lit_u1_pathb = f"{est['path_b']['u1_levels']:.3f}"
    lit_u2_abm = f"{est['abm']['u2_diffs']:.3f}"
    lit_pathb_var = f"{est['path_b']['decomp']['levels']['var_share']:.1f}\\%"
    lit_abm_bias_tbl = f"{est['abm']['decomp']['levels']['bias_share']:.1f}"
    ok = (all(bool(g["pass"]) for g in thl["gates"].values())
          and claims == 1
          and lit_u1_pathb in tex and lit_u2_abm in tex
          and lit_pathb_var in tex and lit_abm_bias_tbl in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check theil dynamic fit: "
        f"in-run gates all pass={all(bool(g['pass']) for g in thl['gates'].values())}, "
        f"tex run-citation count={claims} (want 1), literals "
        f"{lit_u1_pathb!r}/{lit_u2_abm!r}/{lit_pathb_var!r}/{lit_abm_bias_tbl!r} "
        f"present={lit_u1_pathb in tex}/{lit_u2_abm in tex}/"
        f"{lit_pathb_var in tex}/{lit_abm_bias_tbl in tex}"
    )

    # Round-16 W6: the flexible-learner comparator sentences must agree with
    # the committed artifact — parity and sanity gates passed, the
    # pre-committed overall verdict is as printed, and the printed holdout
    # RMSEs are the artifact's, rounded as printed.
    mlc = json.loads(MLCOMP_RESULTS.read_text())
    hgb = mlc["learners"]["hgb_poisson"]
    glm = mlc["learners"]["poisson_glm"]
    claims = tex.count("run \\texttt{ml\\_comparator\\_holdout}")
    lit_hgb_w = f"{hgb['rmse_weighted_pp']:.1f} points"
    lit_hgb_u = f"{hgb['rmse_unweighted_pp']:.1f} against 37.9"
    lit_glm = f"{glm['rmse_weighted_pp']:.1f} and {glm['rmse_unweighted_pp']:.1f} points"
    ok = (all(bool(g["pass"]) for g in mlc["gates"].values())
          and mlc["interpretation"]["overall_verdict"]
              == "flexible_fit_helps_no_headline_change"
          and claims == 1
          and lit_hgb_w in tex and lit_hgb_u in tex and lit_glm in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check ml comparator holdout: "
        f"in-run gates all pass={all(bool(g['pass']) for g in mlc['gates'].values())}, "
        f"verdict={mlc['interpretation']['overall_verdict']}, tex run-citation "
        f"count={claims} (want 1), literals {lit_hgb_w!r}/{lit_hgb_u!r}/{lit_glm!r} "
        f"present={lit_hgb_w in tex}/{lit_hgb_u in tex}/{lit_glm in tex}"
    )

    # Round-17 R17-B (gate #38): the composition-shift appendix table must
    # agree with the committed artifact — all in-run gates passed and the
    # printed PSI values are the artifact's, rounded as printed.
    cs = json.loads(COMPSHIFT_RESULTS.read_text())
    svb = cs["comparisons"]["sample_vs_book"]
    xag = cs["comparisons"]["freddie_vs_fannie"]
    claims = tex.count("run \\texttt{composition\\_shift}")
    lits = [f"{svb['agency']['psi']:.2f}", f"{svb['vintage']['psi']:.2f}",
            f"{svb['coupon']['psi']:.2f}", f"PSI {xag['state']['psi']:.3f}",
            f"PSI {xag['fico']['psi']:.3f}"]
    ok = (_gates_ok(cs["gates"]) and claims == 1
          and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check composition shift: "
        f"in-run gates all pass={_gates_ok(cs['gates'])}, tex run-citation "
        f"count={claims} (want 1), PSI literals {lits} present="
        f"{[l in tex for l in lits]}"
    )

    # Round-17 R17-C (gate #39): the freeze-sensitivity paragraph must agree
    # with the committed artifact — all gates passed, the floor invariance
    # held at every share, and the printed dollars are the artifact's.
    fz = json.loads(FREEZE_RESULTS.read_text())
    p1 = fz["part1"]["legs"]
    p2 = fz["part2"]["legs"]
    claims = tex.count("run \\texttt{freeze\\_sensitivity}")
    lits = [f"\\${p1['freeze_off']['trapped_b']:.1f} billion",
            f"\\${p1['trigger_100bp']['trapped_b']:.1f} to "
            f"\\${p1['trigger_200bp']['trapped_b']:.1f} billion",
            f"\\${p2['share_0.100000']['leg']['trapped_b']:.1f} billion",
            f"\\${p2['share_0.182600']['leg']['trapped_b']:.1f} billion",
            f"\\${p2['share_0.300000']['leg']['trapped_b']:.1f} billion",
            f"+\\${fz['part1']['freeze_contribution']['trapped_b']:.1f}"]
    ok = (_gates_ok(fz["gates"]) and claims == 1
          and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check freeze sensitivity: "
        f"in-run gates all pass={_gates_ok(fz['gates'])}, tex run-citation "
        f"count={claims} (want 1), literals present={[l in tex for l in lits]}"
    )

    # Round-17 R17-D (gate #40): the isotonic-recalibration sentence must
    # agree with the committed artifact — gates passed, verdict as printed.
    iso = json.loads(ISOTONIC_RESULTS.read_text())
    isoc = iso["isotonic_recalibration"]
    claims = tex.count("run \\texttt{landmark\\_isotonic\\_holdout}")
    lits = [f"to {isoc['rmse_weighted_pp']:.2f} points",
            f"RMSE at {isoc['rmse_unweighted_pp']:.1f}",
            f"$-{abs(isoc['r2_unweighted']):.3f}$"]
    ok = (_gates_ok(iso["gates"])
          and iso["interpretation"]["overall_verdict"] == "no_material_change"
          and claims == 1 and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check landmark isotonic: "
        f"in-run gates all pass={_gates_ok(iso['gates'])}, "
        f"verdict={iso['interpretation']['overall_verdict']}, tex run-citation "
        f"count={claims} (want 1), literals present={[l in tex for l in lits]}"
    )

    # Round-17 R17-L (gate #41): the marginal-timing sentences must agree
    # with the committed artifact — gates passed, thirds/peak/buckets as
    # printed, and the app:theil null terminal is the artifact's.
    mm = json.loads(MARGMONTH_RESULTS.read_text())
    th = mm["part_a"]["thirds"]["shares_pct"]
    cb = mm["part_b"]["coupon_buckets"]
    claims = tex.count("run \\texttt{marginal\\_monthly\\_decomposition}")
    lit_thirds = f"{th[0]:.1f}\\%/{th[1]:.1f}\\%/{th[2]:.1f}\\%"
    lit_peak = f"\\${mm['part_a']['peak']['m_b']:.2f} billion"
    lit_buckets = (f"{cb['<3.0%']['share_of_cells_sum_pct']:.1f}\\%/"
                   f"{cb['3.0-4.0%']['share_of_cells_sum_pct']:.1f}\\%/"
                   f"{cb['>=4.0%']['share_of_cells_sum_pct']:.1f}\\%")
    lit_null = f"-\\${abs(mm['part_a']['null_cumulative_error_b_derived'][-1]):.1f}"
    ok = (_gates_ok(mm["gates"])
          and mm["part_b"]["additivity"]["verdict"] == "monthly_shares_readable"
          and claims == 1
          and lit_thirds in tex and lit_peak in tex and lit_buckets in tex
          and lit_null in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check marginal monthly: "
        f"in-run gates all pass={_gates_ok(mm['gates'])}, "
        f"verdict={mm['part_b']['additivity']['verdict']}, tex run-citation "
        f"count={claims} (want 1), literals "
        f"{lit_thirds!r}/{lit_peak!r}/{lit_buckets!r}/{lit_null!r} present="
        f"{lit_thirds in tex}/{lit_peak in tex}/{lit_buckets in tex}/{lit_null in tex}"
    )

    # Round-17 R17-J (gate #42): the interpolation spot-check sentence must
    # agree with the committed artifact — reconstruction gates passed and
    # the printed non-kink max and weighted mean are the artifact's.
    isc = json.loads(INTERP_RESULTS.read_text())
    claims = tex.count("run \\texttt{interp\\_spot\\_check}")
    nonkink = isc["midpoint_check"]["summary"]["non_kink"]["us"]["max_abs_pp"]
    wmean = isc["realized_check"]["weighted"]["us"]["mean_abs_monthly_pp"]
    lit_nk = f"at most {nonkink:.2f} points"
    lit_wm = f"{wmean:.2f} points of CPR over the window"
    ok = (_gates_ok(isc["gates"]) and claims == 1
          and lit_nk in tex and lit_wm in tex
          and "August--November 2022" in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check interp spot check: "
        f"reconstruction gates all pass={_gates_ok(isc['gates'])}, tex "
        f"run-citation count={claims} (want 1), literals {lit_nk!r}/{lit_wm!r} "
        f"present={lit_nk in tex}/{lit_wm in tex}"
    )

    # Round-17 R17-K (gate #43): the SMD paragraph must agree with the
    # committed artifact — gates passed, verdict joint_fit_infeasible, and
    # the printed fitted point and scored recovery are the artifact's.
    smd = json.loads(SMD_RESULTS.read_text())
    fit = smd["fitted"]
    claims = tex.count("run \\texttt{smd\\_two\\_moment}")
    lit_m1 = f"{fit['M1']:.4f}"
    lit_m2 = f"{fit['M2']:.4f}"
    lit_rec = f"{smd['scored_at_fit']['share_pct']:.1f}\\% of benchmark"
    lit_pi0 = f"{fit['pi0_realized_point_mass'] * 100:.1f}\\%"
    ok = (_gates_ok(smd["gates"])
          and smd["verdict"] == "joint_fit_infeasible"
          and claims == 1
          and lit_m1 in tex and lit_m2 in tex and lit_rec in tex
          and lit_pi0 in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check smd two-moment: "
        f"in-run gates all pass={_gates_ok(smd['gates'])}, "
        f"verdict={smd['verdict']}, tex run-citation count={claims} (want 1), "
        f"literals {lit_m1!r}/{lit_m2!r}/{lit_rec!r}/{lit_pi0!r} present="
        f"{lit_m1 in tex}/{lit_m2 in tex}/{lit_rec in tex}/{lit_pi0 in tex}"
    )

    # Round-17 R17-E (gate #44): the two Danish WAL rows must agree with the
    # committed artifact rows and the derived rule-only shortening.
    wt = json.loads(WALTAB_RESULTS.read_text())
    rows = wt["rows"]
    dus = rows["danish_us_intercept"]
    dlv = rows["danish_level"]
    lit_dus = (f"({dus['mean_cpr_pct']:.2f}\\%) & {dus['wal_june_2022']:.1f} & "
               f"{dus['wal_nov_2025']:.1f}")
    lit_dlv = (f"({dlv['mean_cpr_pct']:.2f}\\%) & {dlv['wal_june_2022']:.1f} & "
               f"{dlv['wal_nov_2025']:.1f}")
    lit_short = f"{wt['rule_only_wal_shortening_years']:.1f}-year rule-only shortening"
    ok = lit_dus in tex and lit_dlv in tex and lit_short in tex
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check danish wal rows: literals "
        f"{lit_dus!r}/{lit_dlv!r}/{lit_short!r} present="
        f"{lit_dus in tex}/{lit_dlv in tex}/{lit_short in tex}"
    )

    # Round-17 follow-up R17-I (gate #45): the curtailment-demonstration
    # sentence must agree with the committed artifact — gates passed, the
    # identity held, and the printed netted totals/wedges are the artifact's.
    cpd = json.loads(CURTDEMO_RESULTS.read_text())
    claims = tex.count("run \\texttt{curtailment\\_profile\\_demo}")
    seas = cpd["results"]["seasonal"]
    regi = cpd["results"]["regime_split"]
    lits = [f"\\${seas['netted_b']:.2f} and \\${regi['netted_b']:.2f} billion",
            f"{seas['wedge_pp']:.2f} and {regi['wedge_pp']:.2f} points"]
    ok = (cpd["status"] == "ok" and _gates_ok(cpd["gates"])
          and bool(cpd["demonstration"]["identity_holds"])
          and claims == 1 and all(l in tex for l in lits))
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check curtailment profile demo: "
        f"status={cpd['status']}, identity_holds="
        f"{cpd['demonstration']['identity_holds']}, tex run-citation "
        f"count={claims} (want 1), literals present={[l in tex for l in lits]}"
    )

    # Round-17 follow-up R17-M (gate #46): the spread-variants sentence must
    # agree with the committed artifact — parity gates passed, threshold
    # survives at every variant, and the printed range is the artifact's.
    spv = json.loads(SPREADVAR_RESULTS.read_text())
    claims = tex.count("run \\texttt{expectation\\_spread\\_variants}")
    var = spv["variants"]
    share = lambda k: var[k]["expected_share_of_realized_cap_shortfall_pct"]
    lit_2022 = (f"{min(share('v1_2022_linear_back_ramp'), share('v4_2022_linear_front_ramp')):.1f}--"
                f"{max(share('v1_2022_linear_back_ramp'), share('v4_2022_linear_front_ramp')):.1f}\\%")
    lit_2025 = (f"{share('v2_2025_all_front'):.1f}--"
                f"{spv['diagnostic']['d1_2025_linear_back_ramp']['expected_share_of_realized_cap_shortfall_pct']:.1f}\\%")
    lit_brk = f"{share('v3_2025_all_december'):.1f}\\%"
    all_survive = (all(bool(v["threshold_survives"]) for v in var.values())
                   and bool(spv["diagnostic"]["d1_2025_linear_back_ramp"]["threshold_survives"]))
    g1s = spv["gates"]["g1_uniform_central_parity"]["status"]
    g2s = spv["gates"]["g2_settlement_aware_parity"]["status"]
    ok = (g1s == "PASS" and g2s == "PASS"
          and all_survive and claims == 1
          and lit_2022 in tex and lit_2025 in tex and lit_brk in tex)
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check spread variants: "
        f"parity g1/g2={g1s}/{g2s}, "
        f"all-survive={all_survive}, tex run-citation count={claims} (want 1), "
        f"literals {lit_2022!r}/{lit_2025!r}/{lit_brk!r} present="
        f"{lit_2022 in tex}/{lit_2025 in tex}/{lit_brk in tex}"
    )

    # Round-17 follow-up R17-E (gate #47): tab:discount's five rows must
    # agree with the filled-grid artifact — flips as printed, deltas all zero.
    dbd = json.loads(DANBOUND_RESULTS.read_text())
    runs = dbd["runs"]
    ok_flips = all(
        ("{:,}".format(runs[k]["flipped_loan_months"]).replace(",", "{,}") + " of 1{,}683{,}082") in tex
        for k in ("spread_25bp", "spread_50bp", "spread_75bp", "spread_100bp")
    )
    ok_zero = all(v == 0.0 for v in dbd["deltas_vs_baseline_b"].values())
    ok = ok_flips and ok_zero
    failures += 0 if ok else 1
    print(
        f"[{'PASS' if ok else 'FAIL'}] cross-check danish grid fill: "
        f"flip literals present={ok_flips}, all deltas zero={ok_zero} "
        f"(grid {sorted(dbd['spreads_bp'])})"
    )

    print(f"\n{'ALL GATES PASS' if failures == 0 else f'{failures} GATE(S) FAILED'}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
