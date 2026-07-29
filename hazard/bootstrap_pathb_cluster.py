#!/usr/bin/env python3
"""
Path B stratum-CLUSTER bootstrap — the sampling layer the within-stratum
bootstrap cannot see.

PRE-COMMITTED SPEC (fixed in this header BEFORE any run, per the convention of
floor_form_offwindow.py / concave_marginal.py / burnout_ablation.py).

=======================================================================
WHAT IS WRONG WITH THE COMMITTED BOOTSTRAP
=======================================================================
bootstrap_pathb.py resamples loans WITHIN each stratum and preserves each
stratum's loan count (stratified_resample, line 63). Between-stratum sampling
variance is therefore never drawn. That is why its interval is degenerate --
marginal sd 0.0164pp, 95% interval [9.1664, 9.2286] -- and it is why the
manuscript can say the loan draw "contributes essentially no uncertainty".
The statement is true of the scheme that was run and says nothing about the
scheme that matters.

The repository already contains cluster resampling: bootstrap_se.py resamples
the strata with replacement for Path A. It was never applied to Path B.

=======================================================================
TWO FACTS ESTABLISHED BEFORE WRITING THIS SCRIPT
=======================================================================
(1) VARIABLE LOAN COUNT IS SAFE. A cluster bootstrap resamples 130 clusters
    with replacement, so the total loan count varies replicate to replicate.
    That does not corrupt the scoring, because the pool's absolute size is
    normalised away TWICE: agents.py:205 scale_to_holdings rescales all
    balances so total UPB matches Fed holdings at QT start, and
    microsim_engine.py:57-58 then recomputes
        scale = WSHOMCB_t / pool_exposure_t
    every month, with all dollar flows multiplied by it. Simulated roll-off is
    therefore a RATE (fraction of pool prepaying) times an EXOGENOUS LEVEL
    (WSHOMCB). Pool size cancels; composition does not. Composition is exactly
    the thing cluster resampling perturbs, so the variance of interest
    survives and only the nuisance variance of total pool size is removed.

    This had to be checked first: had the rescaling absorbed composition too,
    a cluster bootstrap would have produced a second falsely-tight interval
    and looked like a result.

(2) THE EFFECTIVE CLUSTER COUNT IS 26, NOT 130. The strata are violently
    unequal -- 1 to 6,076 loans, median 136. On balance weights the largest
    single stratum is 9.77% of the sample and the top five are 35.3%, giving
    an effective count 1/sum(p^2) = 25.8. Any interval from this design must
    be reported with that number beside it, or "130 clusters" reads as far
    more information than it carries. With ~26 effective clusters a percentile
    interval is itself noisy, which is a limit of the design and not something
    more replicates can fix.

=======================================================================
SPEC
=======================================================================
- Resampling: draw 130 stratum_ids WITH REPLACEMENT; concatenate every loan of
  each drawn stratum. Total loan count varies by construction (see fact 1).
  Replicate r uses numpy default_rng(r) for the resample only.
- Simulation: production convention otherwise -- engine RNG_SEED 42 held fixed
  across replicates (default-channel draws are not the object of interest),
  US regime only, one shared macro frame fetched once, raw-basis scoring via
  extension_risk.score_extension_risk.
- Legs: paired central (p_q 6.5) and beta_1 = 0 null (p_q 0) per replicate, so
  the marginal is differenced WITHIN replicate.
- Floor: 4.991% by default -- the off-window anchor the paper headlines. The
  committed within-stratum bootstrap ran at the 4.0% production floor, which
  is the DEMOTED calibration, so the headline floor is the decision-relevant
  one and is run first.
- Reported: 2.5/50/97.5 percentiles and sd for central share, null share and
  the paired marginal, plus the effective cluster count and the largest
  cluster's balance share.

PARITY (G1, must hold before anything new is reported): the UNRESAMPLED loan
sample must reproduce the committed off-window legs bit-exactly --
    central $767.5264524465003B   null $724.9180585654117B
(oos_identification_results.json, replayed bit-exactly by burnout_ablation's
G6 under this same US-only convention).

=======================================================================
EX-ANTE VERDICT (fixed before the run; precedence T3 -> T1/T2/T3)
=======================================================================
The decision-relevant comparison is against the FLOOR-READ cluster bootstrap's
[+2.974329560125351, +8.01850965353176]pp (floor_uncertainty_results.json),
which tab:uncertainty currently labels "the binding layer".

  T1  cluster marginal interval WIDTH < 50% of the floor-read width
      -> the floor read remains the binding layer; tab:uncertainty's label
         stands; the degenerate within-stratum claim is replaced by a real
         interval and the paper states both layers.
  T2  width between 50% and 100% of the floor-read width
      -> the two layers are comparable; "the binding layer" is retired for a
         two-layer statement naming both.
  T3  width >= the floor-read width
      -> loan/stratum sampling is the binding layer. tab:uncertainty L509 and
         its caption move, and the abstract's uncertainty sentence must be
         re-checked against the wider interval.

  Reported in every branch, obliging only itself:
  R1 the ratio of the cluster interval width to the committed within-stratum
     width (0.0622pp on the marginal at the 4.0% floor). A ratio near 1 would
     mean between-stratum variance is negligible after all, which would be a
     finding about the design rather than about the estimate.
  R2 whether the committed point marginal (+5.5715581829pp at this floor) lies
     inside the cluster interval. Outside would indicate the point estimate is
     not central to its own resampling distribution.

Nothing here licenses a headline change on its own: the marginal's identified
content is the calibration-and-form envelope, and this run adds one more
uncertainty layer to that envelope rather than replacing it.

Run:  cd hazard && python3 bootstrap_pathb_cluster.py [--reps 200] [--floor 4.991]
"""
from __future__ import annotations

import argparse
import os
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

import literature_hazard
from config import LOAN_SAMPLE_PATH
from extension_risk import score_extension_risk
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).resolve().parent / "data"
RESULTS_JSON = DATA_DIR / "bootstrap_pathb_cluster_results.json"
DRAWS_CSV = DATA_DIR / "bootstrap_pathb_cluster_draws.csv"
TMP_PARQUET = DATA_DIR / "_bootstrap_pathb_cluster_tmp.parquet"

CENTRAL_PQ = 6.5
NULL_PQ = 0.0
PRODUCTION_FLOOR = 0.04
DEFAULT_FLOOR_PCT = 4.991

# committed anchors by floor (ROUND-28 C4 patch, specs/SPEC_round28_B2_C4_C5.md
# C4.2): 4.991 from oos_identification_results.json band 6.5; 4.0 from
# no_lockin_null_results.json.
ANCHORS_BY_FLOOR = {
    4.991: (767.5264524465003, 724.9180585654117, 5.5715581829),
    4.0: (818.5300844066606, 748.1850239867648, 9.198459770709789),
    # ROUND-28 C2 amendment A3: band-end anchors for the P4 floor-invariance
    # probe, committed band-6.5 cells of oos_identification_results.json
    # .instrument1_marginal_table (the 4.991 row bit-matches the line above).
    4.695: (785.7883567116477, 734.0068506865199, 6.771052540089784),
    5.334: (743.8451864084004, 711.2235461485112, 4.265670450690081),
}
COMMITTED_CENTRAL_B, COMMITTED_NULL_B, COMMITTED_MARGINAL_PP = \
    ANCHORS_BY_FLOOR[DEFAULT_FLOOR_PCT]
TOL_PARITY = 1e-9

# floor_uncertainty_results.json part_a_sampling_uncertainty.mf4_binding_uncertainty
FLOOR_READ_CI_PP = (2.974329560125351, 8.01850965353176)
# committed within-stratum marginal interval width at the 4.0% floor
WITHIN_STRATUM_WIDTH_PP = 9.2286 - 9.1664


def cluster_resample(loans: pl.DataFrame, rng: np.random.Generator) -> pl.DataFrame:
    """Draw the strata with replacement; take every loan of each drawn stratum.

    Total loan count varies by construction. See fact (1) in the header: the
    engine normalises pool size away twice, so this is safe and is what makes
    between-stratum composition variance visible.
    """
    pdf = loans.to_pandas()
    groups = {k: g.index.to_numpy() for k, g in pdf.groupby("stratum_id", sort=True)}
    keys = np.array(sorted(groups))
    drawn = rng.choice(keys, size=len(keys), replace=True)
    idx = np.concatenate([groups[k] for k in drawn])
    return pl.from_pandas(pdf.loc[idx].reset_index(drop=True))


def _run_leg(loans_r: pl.DataFrame, macro: pd.DataFrame,
             empirical: pd.DataFrame, pq: float) -> tuple[float, float]:
    res = run_qt_microsim(
        loan_sample=loans_r, macro=macro, regimes=("US",),
        output=TMP_PARQUET, p_q_shock_pct=pq,
    )
    score = score_extension_risk(res["US"], empirical)
    return float(score["hazard_trapped_b"]), float(score["share_explained_pct"])


def effective_clusters(loans: pl.DataFrame) -> dict:
    pdf = loans.to_pandas()
    w = pdf.groupby("stratum_id")["orig_upb"].sum()
    p = (w / w.sum()).to_numpy()
    return {
        "n_clusters": int(len(p)),
        "effective_n_clusters": float(1.0 / np.sum(p ** 2)),
        "largest_cluster_balance_share": float(p.max()),
        "top5_balance_share": float(np.sort(p)[-5:].sum()),
    }


def classify(width_pp: float) -> str:
    """Ex-ante partition against the floor-read interval. Pure, so it is
    testable without a run."""
    fw = FLOOR_READ_CI_PP[1] - FLOOR_READ_CI_PP[0]
    if width_pp < 0.5 * fw:
        return "T1"
    if width_pp < fw:
        return "T2"
    return "T3"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--floor", type=float, default=DEFAULT_FLOOR_PCT,
                    help="involuntary floor, annual CPR percent")
    args = ap.parse_args()
    floor = args.floor / 100.0
    # ROUND-28 C4 patch: floor-tagged outputs at non-default floors; the
    # committed off-window artifact (gate #84) is overwrite-guarded; anchors
    # are floor-conditional.
    global RESULTS_JSON, DRAWS_CSV, COMMITTED_CENTRAL_B, COMMITTED_NULL_B, \
        COMMITTED_MARGINAL_PP
    if abs(args.floor - DEFAULT_FLOOR_PCT) > 1e-12:
        tag = f"_floor{args.floor:g}"
        RESULTS_JSON = DATA_DIR / f"bootstrap_pathb_cluster_results{tag}.json"
        DRAWS_CSV = DATA_DIR / f"bootstrap_pathb_cluster_draws{tag}.csv"
        if DRAWS_CSV.exists():
            DRAWS_CSV.unlink()
    elif not os.environ.get("ALLOW_DEFAULT_FLOOR_OVERWRITE"):
        raise SystemExit(
            "refusing to overwrite the committed off-window artifact "
            "(gate #84); set ALLOW_DEFAULT_FLOOR_OVERWRITE=1 to force")
    try:
        COMMITTED_CENTRAL_B, COMMITTED_NULL_B, COMMITTED_MARGINAL_PP = \
            ANCHORS_BY_FLOOR[round(args.floor, 6)]
    except KeyError:
        raise SystemExit(f"no committed anchors for floor {args.floor}%")

    print("Fetching shared macro frame + empirical benchmark …")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)

    clus = effective_clusters(loans)
    print(f"clusters {clus['n_clusters']}, effective "
          f"{clus['effective_n_clusters']:.1f}, largest "
          f"{clus['largest_cluster_balance_share'] * 100:.2f}% of balance")

    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    try:
        # ---- G1 parity: unresampled sample must replay the committed legs ----
        print(f"\nG1 parity at floor {args.floor}% (unresampled) …")
        pc_b, _ = _run_leg(loans, macro, empirical, CENTRAL_PQ)
        pn_b, _ = _run_leg(loans, macro, empirical, NULL_PQ)
        d_c = abs(pc_b - COMMITTED_CENTRAL_B)
        d_n = abs(pn_b - COMMITTED_NULL_B)
        ok = d_c < TOL_PARITY and d_n < TOL_PARITY
        print(f"  central {pc_b:.10f} (want {COMMITTED_CENTRAL_B:.10f}, d {d_c:.3e})")
        print(f"  null    {pn_b:.10f} (want {COMMITTED_NULL_B:.10f}, d {d_n:.3e})")
        print(f"  G1_parity [{'PASS' if ok else 'FAIL'}]")
        if not ok:
            raise SystemExit(
                "G1 parity FAILED — the unresampled sample does not reproduce "
                "the committed off-window legs. Nothing is written; the run is "
                "void, not merely unfavourable."
            )

        rows = []
        t0 = time.perf_counter()
        for rep in range(1, args.reps + 1):
            rng = np.random.default_rng(rep)
            loans_r = cluster_resample(loans, rng)
            c_b, c_pct = _run_leg(loans_r, macro, empirical, CENTRAL_PQ)
            n_b, n_pct = _run_leg(loans_r, macro, empirical, NULL_PQ)
            row = {
                "rep": rep, "n_loans": int(loans_r.height),
                "central_trapped_b": c_b, "central_share_pct": c_pct,
                "null_trapped_b": n_b, "null_share_pct": n_pct,
                "marginal_b": c_b - n_b, "marginal_pp": c_pct - n_pct,
            }
            rows.append(row)
            pd.DataFrame([row]).to_csv(
                DRAWS_CSV, mode="a", header=not DRAWS_CSV.exists(), index=False,
            )
            if rep % 10 == 0 or rep == 1:
                el = time.perf_counter() - t0
                print(f"rep {rep:4d}/{args.reps}  n {loans_r.height:6d}  "
                      f"central {c_pct:6.2f}%  null {n_pct:6.2f}%  "
                      f"marginal {c_pct - n_pct:+5.2f}pp  "
                      f"[{el / rep:.1f}s/rep, "
                      f"~{el / rep * (args.reps - rep) / 60:.0f}m left]",
                      flush=True)
        runtime_s = time.perf_counter() - t0
    finally:
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = PRODUCTION_FLOOR
        assert literature_hazard.INVOLUNTARY_CPR_ANNUAL == PRODUCTION_FLOOR
    if TMP_PARQUET.exists():
        TMP_PARQUET.unlink()

    df = pd.DataFrame(rows)

    def pcts(col: str) -> dict:
        q = np.percentile(df[col], [2.5, 50.0, 97.5])
        return {"p2_5": float(q[0]), "median": float(q[1]), "p97_5": float(q[2]),
                "mean": float(df[col].mean()), "sd": float(df[col].std(ddof=1))}

    marg = pcts("marginal_pp")
    width = marg["p97_5"] - marg["p2_5"]
    fw = FLOOR_READ_CI_PP[1] - FLOOR_READ_CI_PP[0]
    raw_tier = classify(width)
    if abs(args.floor - DEFAULT_FLOOR_PCT) > 1e-12:
        # T-tiers partition against the OFF-WINDOW floor-read interval and are
        # non-operative at other floors (ROUND-28 C4 patch): reference only;
        # operative comparisons are the same-floor within-stratum width and
        # the in-sample calibration box (11.1pp).
        verdict = {"verdict_offwindow_reference_only": raw_tier,
                   "vs_calibration_box_width_pp": width / 11.1}
    else:
        verdict = raw_tier
    r2_inside = bool(marg["p2_5"] <= COMMITTED_MARGINAL_PP <= marg["p97_5"])

    payload = {
        "mode": "bootstrap_pathb_cluster",
        "spec": (
            "stratum-CLUSTER resample with replacement (130 strata drawn with "
            "replacement, every loan of each drawn stratum taken; total loan "
            "count varies by construction); resample rng seed = replicate "
            "index; engine seed 42 fixed; US regime only; central (p_q 6.5) + "
            "null (p_q 0) per replicate; raw-basis scoring; percentile intervals"
        ),
        "floor_annual_cpr_pct": args.floor,
        "n_reps": int(len(df)),
        "cluster_structure": clus,
        "parity_gates": {
            "G1_central_b": {"got": pc_b, "want": COMMITTED_CENTRAL_B,
                             "pass": True},
            "G1_null_b": {"got": pn_b, "want": COMMITTED_NULL_B, "pass": True},
        },
        "parity_gates_all_pass": True,
        "central_share_pct": pcts("central_share_pct"),
        "null_share_pct": pcts("null_share_pct"),
        "marginal_pp": marg,
        "marginal_b": pcts("marginal_b"),
        "n_loans": pcts("n_loans"),
        "comparison": {
            "cluster_interval_width_pp": width,
            "floor_read_interval_pp": list(FLOOR_READ_CI_PP),
            "floor_read_width_pp": fw,
            "width_ratio_vs_floor_read": width / fw,
            "within_stratum_width_pp_at_4pct": WITHIN_STRATUM_WIDTH_PP,
            "within_stratum_same_floor": abs(args.floor - 4.0) < 1e-9,
            "R1_width_ratio_vs_within_stratum": width / WITHIN_STRATUM_WIDTH_PP,
            "R2_committed_point_inside": r2_inside,
            "committed_point_marginal_pp": COMMITTED_MARGINAL_PP,
        },
        "verdict": verdict,
        "runtime_s": runtime_s,
    }
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=1)

    print("\n" + "=" * 74)
    print(" PATH B STRATUM-CLUSTER BOOTSTRAP")
    print("=" * 74)
    print(f"  clusters {clus['n_clusters']} (effective "
          f"{clus['effective_n_clusters']:.1f}); loans per replicate "
          f"{df['n_loans'].min()}–{df['n_loans'].max()}")
    print(f"  marginal  {marg['median']:+.4f}pp  95% "
          f"[{marg['p2_5']:+.4f}, {marg['p97_5']:+.4f}]  sd {marg['sd']:.4f}pp")
    print(f"  width {width:.4f}pp vs floor-read {fw:.4f}pp "
          f"(ratio {width / fw:.2f}) vs within-stratum "
          f"{WITHIN_STRATUM_WIDTH_PP:.4f}pp (ratio "
          f"{width / WITHIN_STRATUM_WIDTH_PP:.1f}x)")
    print(f"  R2 committed point inside interval: {r2_inside}")
    print(f"  verdict: {verdict}")
    print(f"  runtime {runtime_s:,.0f}s")


if __name__ == "__main__":
    main()
