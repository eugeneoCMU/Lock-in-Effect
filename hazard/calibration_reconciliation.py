#!/usr/bin/env python3
"""
Headline-calibration reconciliation (July 2026 panel round).

The manuscript demotes the lock-in marginal from the 4.0% in-window
involuntary floor to the off-window floor measured on the 2018 rising-rate
leg (§V, §VII.E): the headline marginal is +$42.6B / +5.57pp at the clean
mid point 4.991%, with a clean band 4.695--5.334%. That demotion was never
propagated to the *recovery* numbers, which are still quoted at 4.0%:
"recovers 97.9% of the shortfall on a benchmark-consistent accounting
basis", "the beta1 = 0 null still recovers 88.7%", and the 0.2-point
convergence between that 88.7% and the NY Fed's ex-ante 88.5%. A recovery
measured at one floor and a marginal measured at another are not a
calibration; this module puts both on the headline floor.

WHAT IS COMPUTED
1. BASIS MAP. The paper's two accounting bases differ by a single additive
   macro layer. shared_layer_scoring.py runs every estimator through
   fed_mbs_extension_risk.compute_metrics(use_hazard_microsim=True); the
   committed artifact shows that layer nets a constant $69.56220187263008B
   of curtailment off the standalone scorer's trapped total, over a common
   $764.7482532227002B cap benchmark, IDENTICALLY for all five committed
   estimators (Path A at 121.5% standalone through the null at 97.8%). The
   layer is therefore path-invariant, hence floor-invariant, and the map

       trapped_shared = trapped_standalone - CURTAILMENT_NETTED_B
       share_shared   = trapped_shared / CAP_BENCHMARK_B * 100

   is exact. Gate A reproduces the committed shared-basis 97.9365% central
   and 88.7381% null from the committed standalone 107.0326% / 97.8342% to
   machine precision before anything new is computed. Gate B asserts the
   layer's path-invariance across all five committed estimators.

2. FLOOR-BY-FLOOR RECOVERY on that shared basis, at the committed floors of
   oos_identification_results.json: the production 4.0%, the clean band
   edges 4.695% / 5.334%, and the headline mid 4.991%. No new microsim is
   run: the standalone legs at every one of those floors are already
   committed in instrument1_marginal_table, and the map is exact. The MISS
   against the benchmark is 100 minus the central shared share.

3. THE 88.7-vs-88.5 CONVERGENCE re-examined at the headline floor, under
   BOTH allocations the expectation benchmark carries: the pre-committed
   uniform-spread rule (88.51496735220967%) and the settlement-aware
   allocation the manuscript itself calls more faithful (75.5765152376043%).

4. S1--S6 RESTATEMENTS: the five manuscript figures that are quoted against
   the demoted in-sample $70.345B total or misstated against their own
   artifact, recomputed against the headline $42.608B.

Companion sign-forcing statistics live in sign_forcing_stats.py.

Run:  cd hazard && python3 calibration_reconciliation.py
      -> data/calibration_reconciliation_results.json
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

SHARED_LAYER = DATA_DIR / "shared_layer_scoring_results.json"
FLOOR_SWEEP = DATA_DIR / "floor_sweep_results.json"
OOS = DATA_DIR / "oos_identification_results.json"
EXPECTATION = DATA_DIR / "expectation_benchmark_results.json"
MARGINAL_DECOMP = DATA_DIR / "marginal_decomposition_results.json"
SEASONAL_FLOOR = DATA_DIR / "seasonal_floor_timing_results.json"

OUT = DATA_DIR / "calibration_reconciliation_results.json"

# Committed manuscript anchors at the 4.0% in-window floor (§VII.F).
ANCHOR_CENTRAL_SHARED_PCT = 97.9365273968041
ANCHOR_NULL_SHARED_PCT = 88.73806762609433
ANCHOR_CENTRAL_STANDALONE_PCT = 107.0326190295068
ANCHOR_NULL_STANDALONE_PCT = 97.83415925879702

# Floors reported. 4.0 is the demoted in-window production calibration;
# 4.991 is the headline off-window point; 4.695/5.334 are its clean band.
HEADLINE_FLOOR_PCT = 4.991
CLEAN_BAND_PCT = (4.695, 5.334)
REPORT_FLOORS_PCT = (4.0, 4.695, 4.991, 5.334)

TOL = 1e-9  # bit-exact: the map is arithmetic on committed floats


def _load(p: Path) -> dict:
    return json.loads(p.read_text())


# ======================================================================
# 1. Basis map
# ======================================================================
def derive_basis_map(shared: dict) -> dict:
    """Extract the shared-accounting layer's constant netting and denominator."""
    res = shared["results"]
    curtailments = {k: v["curtailment_netted_b"] for k, v in res.items()}
    benchmarks = {k: v["empirical_trapped_b"] for k, v in res.items()}
    curt = curtailments["path_b_central"]
    cap = benchmarks["path_b_central"]
    # Gate B: the layer must be identical for every committed estimator, or
    # it is path-dependent and cannot be carried to an unrun floor.
    path_invariant = (
        all(abs(v - curt) < TOL for v in curtailments.values())
        and all(abs(v - cap) < TOL for v in benchmarks.values())
    )
    return {
        "curtailment_netted_b": curt,
        "cap_benchmark_b": cap,
        "offset_pp": curt / cap * 100.0,
        "path_invariance_gate": {
            "curtailment_by_estimator_b": curtailments,
            "cap_benchmark_by_estimator_b": benchmarks,
            "standalone_share_spread_pp": (
                max(v["standalone_share_pct"] for v in res.values())
                - min(v["standalone_share_pct"] for v in res.values())
            ),
            "pass": bool(path_invariant),
            "reading": (
                "the curtailment layer and the cap benchmark are identical "
                "across five estimators spanning 29.6pp of standalone "
                "recovery, so the layer does not depend on the CPR path and "
                "therefore does not depend on the floor that generates it"
            ),
        },
    }


def to_shared(trapped_standalone_b: float, bmap: dict) -> tuple[float, float]:
    """Standalone-scorer trapped $B -> (shared trapped $B, shared share %)."""
    t = trapped_standalone_b - bmap["curtailment_netted_b"]
    return t, t / bmap["cap_benchmark_b"] * 100.0


def parity_gate_4pct(bmap: dict, sweep: dict) -> dict:
    """Gate A: reproduce the committed 4.0% shared-basis anchors exactly."""
    row = next(
        r for r in sweep["rows"] if abs(r["floor_annual_cpr_pct"] - 4.0) < TOL
    )
    checks = {}
    for leg, anchor_shared, anchor_standalone in (
        ("central", ANCHOR_CENTRAL_SHARED_PCT, ANCHOR_CENTRAL_STANDALONE_PCT),
        ("null", ANCHOR_NULL_SHARED_PCT, ANCHOR_NULL_STANDALONE_PCT),
    ):
        got_standalone = row[leg]["share_pct"]
        _, got_shared = to_shared(row[leg]["trapped_b"], bmap)
        checks[leg] = {
            "standalone_share_got_pct": got_standalone,
            "standalone_share_want_pct": anchor_standalone,
            "standalone_diff_pp": got_standalone - anchor_standalone,
            "shared_share_got_pct": got_shared,
            "shared_share_want_pct": anchor_shared,
            "shared_diff_pp": got_shared - anchor_shared,
            "pass": bool(
                abs(got_standalone - anchor_standalone) < TOL
                and abs(got_shared - anchor_shared) < TOL
            ),
        }
    checks["all_pass"] = bool(all(v["pass"] for v in checks.values()
                                  if isinstance(v, dict)))
    return checks


# ======================================================================
# 2. Floor-by-floor recovery on the shared basis
# ======================================================================
def floor_table(oos: dict, bmap: dict) -> list[dict]:
    rows = []
    for r in oos["instrument1_marginal_table"]:
        f = round(r["floor_annual_cpr_pct"], 4)
        if not any(abs(f - t) < 1e-6 for t in REPORT_FLOORS_PCT):
            continue
        central = r["band"]["6.5"]
        n_t, n_s = to_shared(r["null_trapped_b"], bmap)
        c_t, c_s = to_shared(central["central_trapped_b"], bmap)
        rows.append({
            "floor_annual_cpr_pct": f,
            "role": (
                "in-window production (demoted)" if abs(f - 4.0) < 1e-6
                else "headline off-window point" if abs(f - HEADLINE_FLOOR_PCT) < 1e-6
                else "clean band edge"
            ),
            "standalone": {
                "central_trapped_b": central["central_trapped_b"],
                "central_share_pct": central["central_share_pct"],
                "null_trapped_b": r["null_trapped_b"],
                "null_share_pct": r["null_share_pct"],
            },
            "shared": {
                "central_trapped_b": c_t,
                "central_share_pct": c_s,
                "null_trapped_b": n_t,
                "null_share_pct": n_s,
            },
            "marginal_b": central["marginal_b"],
            "marginal_pp": central["marginal_pp"],
            "miss_vs_benchmark_pp": 100.0 - c_s,
            "null_miss_vs_benchmark_pp": 100.0 - n_s,
        })
    rows.sort(key=lambda x: x["floor_annual_cpr_pct"])
    return rows


# ======================================================================
# 3. The 88.7-vs-88.5 convergence, re-examined
# ======================================================================
def convergence(rows: list[dict], exp: dict) -> dict:
    head = next(r for r in rows
                if abs(r["floor_annual_cpr_pct"] - HEADLINE_FLOOR_PCT) < 1e-6)
    prod = next(r for r in rows if abs(r["floor_annual_cpr_pct"] - 4.0) < 1e-6)
    uniform = exp["supplementary_projection_wedge"][
        "expected_share_of_realized_cap_shortfall_pct"]
    settle = exp["settlement_aware_allocation"][
        "expected_share_of_realized_cap_shortfall_pct"]
    out = {
        "allocations": {
            "uniform_spread_pre_committed_pct": uniform,
            "settlement_aware_pct": settle,
        },
        "at_4pct_in_window_floor": {},
        "at_headline_floor": {},
        "band_at_clean_edges": {},
    }
    for label, row in (("at_4pct_in_window_floor", prod),
                       ("at_headline_floor", head)):
        n = row["shared"]["null_share_pct"]
        out[label] = {
            "floor_annual_cpr_pct": row["floor_annual_cpr_pct"],
            "null_shared_share_pct": n,
            "gap_vs_uniform_pp": n - uniform,
            "gap_vs_settlement_aware_pp": n - settle,
        }
    edges = {}
    for row in rows:
        if any(abs(row["floor_annual_cpr_pct"] - e) < 1e-6 for e in CLEAN_BAND_PCT):
            n = row["shared"]["null_share_pct"]
            edges[f"{row['floor_annual_cpr_pct']:.3f}"] = {
                "null_shared_share_pct": n,
                "gap_vs_uniform_pp": n - uniform,
                "gap_vs_settlement_aware_pp": n - settle,
            }
    out["band_at_clean_edges"] = edges
    out["verdict"] = (
        "the 0.2-point convergence is an artifact of the demoted in-window "
        "floor. At the headline calibration the null recovers "
        f"{out['at_headline_floor']['null_shared_share_pct']:.2f}% on the "
        "shared basis, "
        f"{abs(out['at_headline_floor']['gap_vs_uniform_pp']):.2f} points "
        "below the uniform-spread projection share and "
        f"{abs(out['at_headline_floor']['gap_vs_settlement_aware_pp']):.2f} "
        "points above the settlement-aware one. The coincidence does not "
        "survive either the floor demotion or the choice of allocation, and "
        "cannot be reported as a convergence."
    )
    return out


# ======================================================================
# 4. S1--S6 restatements against the headline total
# ======================================================================
def restatements(rows: list[dict], decomp: dict) -> dict:
    head = next(r for r in rows
                if abs(r["floor_annual_cpr_pct"] - HEADLINE_FLOOR_PCT) < 1e-6)
    prod = next(r for r in rows if abs(r["floor_annual_cpr_pct"] - 4.0) < 1e-6)
    m_head = head["marginal_b"]
    m_prod = prod["marginal_b"]

    shape_b = 4.897          # §VII.E seasonal-floor shape component
    vintage_bound_b = 11.748  # §V.C Fannie-proxy out-of-sample vintage bound

    cells = decomp["cells"]
    intens = sorted(
        c["share_of_sum_pct"] / c["balance_share_pct"] for c in cells
    )
    resid = decomp["gates"]["G3_additivity"]["residual_frac_of_total"]

    return {
        "S1_flat_floor_share": {
            "manuscript_line": 850,
            "component_b": shape_b,
            "as_printed_pct_of_in_sample": shape_b / m_prod * 100.0,
            "corrected_pct_of_headline": shape_b / m_head * 100.0,
            "note": (
                "printed as '7.0% of it' against the $70.345B in-sample "
                "total; against the headline $42.608B the same $4.897B is "
                f"{shape_b / m_head * 100:.1f}%."
            ),
        },
        "S2_vintage_bound_fraction": {
            "manuscript_line": 324,
            "bound_b": vintage_bound_b,
            "as_printed_fraction_of_in_sample": vintage_bound_b / m_prod,
            "corrected_fraction_of_headline": vintage_bound_b / m_head,
            "note": (
                "printed as 'about a sixth of the lock-in marginal' "
                f"({vintage_bound_b / m_prod * 100:.1f}% of $70.345B); against "
                f"the headline it is {vintage_bound_b / m_head * 100:.1f}%, "
                "more than a quarter."
            ),
        },
        "S3_unqualified_70b": {
            "manuscript_line": 595,
            "note": (
                "'+$70 billion of trapped roll-off' is quoted with no "
                "in-sample qualifier, unlike every other occurrence; the "
                "headline figure is $42.6B."
            ),
        },
        "S4_cross_basis_gap": {
            "manuscript_line": 716,
            "as_printed_pp": 18.3,
            "as_printed_construction": (
                "107.0% standalone central minus 88.7% SHARED null — the two "
                "terms sit on different accounting bases"
            ),
            "single_basis_gap_at_4pct_pp": (
                prod["standalone"]["central_share_pct"]
                - prod["standalone"]["null_share_pct"]
            ),
            "single_basis_gap_at_headline_pp": head["marginal_pp"],
            "note": (
                "the real-book central-minus-null differential on ONE basis "
                "is +9.20pp at the in-window floor and "
                f"+{head['marginal_pp']:.2f}pp at the headline floor; the "
                "18.3-point figure is a basis-crossing artifact."
            ),
        },
        "S5_intensity_range": {
            "manuscript_line": 476,
            "as_printed": "0.8x to 1.5x",
            "recomputed_min": intens[0],
            "recomputed_max": intens[-1],
            "note": (
                f"share_of_sum_pct / balance_share_pct spans "
                f"{intens[0]:.3f} to {intens[-1]:.3f}, not 0.8--1.5."
            ),
        },
        "S6_additivity_residual": {
            "manuscript_lines": [476, 483, 492],
            "as_printed": "the cells sum to within 1.0% of the paired-run total",
            "residual_frac_of_total": resid,
            "residual_pct_of_total": resid * 100.0,
            "claim_true_as_written": bool(resid <= 0.01),
            "note": (
                f"the artifact residual is {resid * 100:.2f}% of the total, "
                "above 1.0%; 'within 1.0%' is false as written."
            ),
        },
    }


def main() -> None:
    shared = _load(SHARED_LAYER)
    sweep = _load(FLOOR_SWEEP)
    oos = _load(OOS)
    exp = _load(EXPECTATION)
    decomp = _load(MARGINAL_DECOMP)

    bmap = derive_basis_map(shared)
    gate_a = parity_gate_4pct(bmap, sweep)
    gate_b = bmap.pop("path_invariance_gate")

    if not (gate_a["all_pass"] and gate_b["pass"]):
        raise SystemExit(
            "PARITY GATE FAILURE — the basis map does not reproduce the "
            "committed 4.0% anchors; nothing downstream may be cited."
        )

    rows = floor_table(oos, bmap)
    got_floors = {r["floor_annual_cpr_pct"] for r in rows}
    missing = [f for f in REPORT_FLOORS_PCT
               if not any(abs(f - g) < 1e-6 for g in got_floors)]
    if missing:
        raise SystemExit(f"floors absent from committed OOS table: {missing}")

    conv = convergence(rows, exp)
    rest = restatements(rows, decomp)

    head = next(r for r in rows
                if abs(r["floor_annual_cpr_pct"] - HEADLINE_FLOOR_PCT) < 1e-6)
    lo = next(r for r in rows if abs(r["floor_annual_cpr_pct"] - 4.695) < 1e-6)
    hi = next(r for r in rows if abs(r["floor_annual_cpr_pct"] - 5.334) < 1e-6)

    headline = {
        "floor_annual_cpr_pct": HEADLINE_FLOOR_PCT,
        "central_shared_share_pct": head["shared"]["central_share_pct"],
        "central_shared_share_band_pct": [
            hi["shared"]["central_share_pct"],
            lo["shared"]["central_share_pct"],
        ],
        "null_shared_share_pct": head["shared"]["null_share_pct"],
        "null_shared_share_band_pct": [
            hi["shared"]["null_share_pct"],
            lo["shared"]["null_share_pct"],
        ],
        "miss_vs_benchmark_pp": head["miss_vs_benchmark_pp"],
        "miss_vs_benchmark_band_pp": [
            lo["miss_vs_benchmark_pp"],
            hi["miss_vs_benchmark_pp"],
        ],
        "marginal_b": head["marginal_b"],
        "marginal_pp": head["marginal_pp"],
        "superseded_claim": (
            "recovers 97.9% of the shortfall on a benchmark-consistent "
            "accounting basis, landing within 2.1% of the benchmark"
        ),
        "corrected_claim": (
            f"recovers {head['shared']['central_share_pct']:.1f}% of the "
            "shortfall on a benchmark-consistent accounting basis at the "
            "off-window floor "
            f"({hi['shared']['central_share_pct']:.1f}--"
            f"{lo['shared']['central_share_pct']:.1f}% across the clean "
            f"band), a miss of {head['miss_vs_benchmark_pp']:.1f} points "
            f"({lo['miss_vs_benchmark_pp']:.1f}--"
            f"{hi['miss_vs_benchmark_pp']:.1f} across the band). The 97.9% "
            "figure and the 2.1-point miss belong to the demoted in-window "
            "calibration and cannot be quoted alongside the headline "
            "marginal."
        ),
    }

    payload = {
        "mode": "calibration_reconciliation",
        "spec": (
            "Propagate the off-window floor demotion from the lock-in "
            "marginal to the recovery figures. Basis map derived from the "
            "committed shared-layer artifact (constant curtailment netting "
            "over a constant cap benchmark, verified path-invariant); "
            "standalone legs at every reported floor read from the committed "
            "oos_identification marginal table; no new microsim run, no new "
            "scorer. Gate A reproduces the committed 4.0% shared-basis "
            "anchors bit-exactly before anything new is computed."
        ),
        "basis_map": bmap,
        "gates": {
            "A_committed_4pct_parity": gate_a,
            "B_layer_path_invariance": gate_b,
            "all_pass": bool(gate_a["all_pass"] and gate_b["pass"]),
        },
        "floor_table": rows,
        "headline_calibration": headline,
        "convergence_88_7_vs_88_5": conv,
        "restatements": rest,
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")

    print("=" * 78)
    print(" BASIS MAP")
    print("=" * 78)
    print(f"  shared = standalone - ${bmap['curtailment_netted_b']:.6f}B "
          f"over ${bmap['cap_benchmark_b']:.6f}B  "
          f"(= -{bmap['offset_pp']:.6f}pp)")
    print(f"  Gate A (4.0% anchors, bit-exact): "
          f"{'PASS' if gate_a['all_pass'] else 'FAIL'}")
    print(f"  Gate B (layer path-invariance):   "
          f"{'PASS' if gate_b['pass'] else 'FAIL'}")

    print("\n" + "=" * 78)
    print(" RECOVERY ON THE SHARED (BENCHMARK-CONSISTENT) BASIS")
    print("=" * 78)
    print(f"  {'floor':>7}{'central $B':>12}{'central %':>11}"
          f"{'null $B':>10}{'null %':>9}{'marginal':>18}{'miss':>8}")
    for r in rows:
        print(f"  {r['floor_annual_cpr_pct']:>6.3f}%"
              f"{r['shared']['central_trapped_b']:>12.1f}"
              f"{r['shared']['central_share_pct']:>10.2f}%"
              f"{r['shared']['null_trapped_b']:>10.1f}"
              f"{r['shared']['null_share_pct']:>8.2f}%"
              f"{r['marginal_b']:>+10.2f}B{r['marginal_pp']:>+7.2f}pp"
              f"{r['miss_vs_benchmark_pp']:>7.2f}")

    print("\n" + "=" * 78)
    print(" 88.7 vs 88.5 CONVERGENCE")
    print("=" * 78)
    for label in ("at_4pct_in_window_floor", "at_headline_floor"):
        c = conv[label]
        print(f"  floor {c['floor_annual_cpr_pct']:.3f}%: null shared "
              f"{c['null_shared_share_pct']:.2f}%  |  vs uniform-spread "
              f"{c['gap_vs_uniform_pp']:+.2f}pp  |  vs settlement-aware "
              f"{c['gap_vs_settlement_aware_pp']:+.2f}pp")

    print(f"\n  Saved: {OUT}")


if __name__ == "__main__":
    main()
