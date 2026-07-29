#!/usr/bin/env python3
"""
covariate_ablation_offwindow.py — the covariate block re-run at the headline
off-window floor (round-28 WP-C5; REVIEW2 finding #6 / DA-M1: the paper's
largest disclosed sensitivity exists only at the demoted in-sample floor).

PRE-COMMITTED SPEC (fixed BEFORE any run; committed before first execution;
full drafting spec at specs/SPEC_round28_B2_C4_C5.md SPEC C5, gates and
expectations adopted unchanged; engine route deviation labeled below).

LABELED DEVIATION from the drafted spec: legs run through
floor_sweep._run_scored (default regime tuple, the B2/C3-validated harness)
rather than a direct run_qt_microsim(regimes=("US",)) call. US-leg
regime-tuple invariance is established bit-exactly in the committed record
(bootstrap_pathb_cluster G1; B2/C3 parity this round), and _run_scored
supplies the bind tally and floor restore for free.

DESIGN. Scenarios {production (-0.15, +0.10), zeroed (0, 0), re-estimated
(-0.393082485292068, +0.20848086275975533 — PINNED from
covariate_priors_results.json, asserted 1e-12)} x legs {null pq 0, central
pq 6.5} x floors {4.0%, 4.991% (consumed from oos artifact)} = 12 engine
runs. Coefficients enter by in-place LITERATURE_COEFS mutation (the engine
never forwards the coefs argument), restored + asserted after each leg.
beta_burnout stays -0.5 throughout.

PARITY GATES (BLOCKING):
  G0d WIRING (analytic, floor zeroed for the probe): fico_z=1 =>
      h(beta_fico=0)/h(beta_fico=-0.15) == exp(0.15) to 1e-12; symmetric LTV.
  G0e LEAK (analytic): fico_z=ltv_z=0 => the three scenarios' hazards are
      IDENTICAL (diff exactly 0).
  G0f PROVENANCE: pinned re-estimated betas == artifact points to 1e-12.
  G0g BASIS: calibration_reconciliation offset == 9.096091632702699.
  G1/G2 production @4.0: central 818.5300844066606 / null 748.1850239867648;
      marginal +70.34506041989584 B / +9.198459770709789 pp (1e-9).
  G5 production @4.991: central 767.5264524465003 / null 724.9180585654117.
  G6 bind anchors @PSA-production: central 4.0 0.36269282595934704, central
      4.991 0.6881875607501289, null 4.0 0.14340654639824515, n 1683124.
  G7 CROSS-ARTIFACT REPLAY (the run's most important gate): fresh zeroed and
      re-estimated central legs @4.0 reproduce 828.2105611766495 and
      774.5297606295118 to 1e-9 — retro-fitting parity to the committed
      108.3%/101.3% literals. FAIL => the in-sample literals are the finding;
      STOP.
  G8 RESTORATION after every leg.
  G-refit (attempted, soft): one un-bootstrapped fit_credit_betas replay
      reproduces the pinned betas to 1e-9; on import/data failure recorded
      skipped, not failed (the G0f pin against the artifact stands).

PRE-COMMITTED EXPECTATIONS (drafted spec C5.4): the LEVEL swing compresses
off-window by factor [0.45, 0.60] (uncensored-share proxy 0.489; burnout
precedent 0.528) => projected total swing ~3.7pp (band +-1.0pp); asymmetry:
the zeroed (downward-hazard) leg compresses at least as much as the
re-estimated; the MARGINAL swing's direction is NOT pre-signed (burnout
precedent amplified 1.27x) and is reported under the +-1pp convention.

LANDING RULE (ex ante; branch on swing_off vs the off-window marginal
5.571558182909726 pp; ALL tex landings queue for Eugene):
  (i)   swing_off >= marginal      -> tex-301 sentence strengthened and
        restated at the headline floor.                            [posture]
  (ii)  marginal/2 <= swing_off < marginal (PROJECTED, ratio ~0.66) ->
        sentence stands, gains floor label + measured figure.
  (iii) swing_off < marginal/2     -> sentence requalified in-sample-only.
                                                                    [posture]
Unconditional: tab:uncertainty gains the off-window covariate entry; tex 263
gains the off-window pair on the burnout-sentence model; tex 911 re-checked;
runindex + verdicts rows.

MUST NOT CHANGE: committed covariate_priors_results.json; the in-sample
108.3/101.3/92.2--99.2 literals (floor-labeled later, not altered); the
headline +5.6; config.py; any .tex file.

Run:  cd hazard && python3 covariate_ablation_offwindow.py
      -> data/covariate_ablation_offwindow_results.json (frozen)
12 engine runs, ~26s each.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import polars as pl

import competing_risks
import floor_sweep as fs
import literature_hazard as lh
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "covariate_ablation_offwindow_results.json"
OOS_ARTIFACT = DATA_DIR / "oos_identification_results.json"
COV_ARTIFACT = DATA_DIR / "covariate_priors_results.json"
CALIB_ARTIFACT = DATA_DIR / "calibration_reconciliation_results.json"

TOL, TOLP = 1e-9, 1e-12
PIN_FICO, PIN_LTV = -0.393082485292068, 0.20848086275975533
PROD_FICO, PROD_LTV = -0.15, 0.10
ANCH = {(0.04, 0.0): 748.1850239867648, (0.04, 6.5): 818.5300844066606,
        (0.04991, 0.0): 724.9180585654117, (0.04991, 6.5): 767.5264524465003}
G7 = {"zeroed": 828.2105611766495, "reest": 774.5297606295118}
BINDS = {(0.04, 6.5): 0.36269282595934704, (0.04991, 6.5): 0.6881875607501289,
         (0.04, 0.0): 0.14340654639824515}
BIND_N = 1683124
MARGINAL_OFF_PP = 5.571558182909726
COMPRESS_BAND = (0.45, 0.60)
SCEN = {"prod": (PROD_FICO, PROD_LTV), "zeroed": (0.0, 0.0),
        "reest": (PIN_FICO, PIN_LTV)}


def set_betas(bf: float, bl: float) -> None:
    lh.LITERATURE_COEFS["beta_fico"] = bf
    lh.LITERATURE_COEFS["beta_ltv"] = bl


def analytic_gates() -> dict:
    age = np.array([30.0]); gap = np.array([-0.01]); z0 = np.array([0.0])
    one = np.array([1.0])
    cur = lh.INVOLUNTARY_CPR_ANNUAL
    lh.INVOLUNTARY_CPR_ANNUAL = 1e-12
    try:
        def h(bf, bl, fz, lz):
            c = dict(lh.LITERATURE_COEFS); c["beta_fico"] = bf; c["beta_ltv"] = bl
            return float(lh.prepay_hazard(age, gap, z0, np.array([fz]),
                                          np.array([lz]), coefs=c)[0])
        wf = abs(h(0.0, PROD_LTV, 1.0, 0.0) / h(PROD_FICO, PROD_LTV, 1.0, 0.0)
                 - np.exp(0.15))
        wl = abs(h(PROD_FICO, 0.0, 0.0, 1.0) / h(PROD_FICO, PROD_LTV, 0.0, 1.0)
                 - np.exp(-0.10))
        leaks = {k: h(bf, bl, 0.0, 0.0) for k, (bf, bl) in SCEN.items()}
        leak = max(abs(leaks[a] - leaks[b]) for a in leaks for b in leaks)
    finally:
        lh.INVOLUNTARY_CPR_ANNUAL = cur
    return {"G0d_wiring": {"fico_dev": wf, "ltv_dev": wl,
                           "pass": wf < TOLP and wl < TOLP},
            "G0e_leak": {"max_abs": leak, "pass": leak == 0.0}}


def attempt_refit() -> dict:
    try:
        import pandas as pd  # noqa
        import covariate_priors_estimation as cpe
        panel = pl.read_parquet(cpe.PANEL_PATH)
        pdf = cpe.enrich_panel_with_macro(panel)
        pdf = pdf.dropna(subset=["rate_gap_bps", "exposure", "loan_age",
                                 "stratum_id"])
        pdf = pdf[pdf["exposure"] > 0]
        train = pdf[pdf["period"] < cpe.HOLDOUT_DATE].copy()
        loans = pl.read_parquet(cpe.LOAN_SAMPLE_PATH)
        fm, fsd = loans["fico"].mean(), loans["fico"].std()
        lm, lsd = loans["orig_ltv"].mean(), loans["orig_ltv"].std()
        fmap = {r["fico_bucket"]: (r["fico"] - fm) / fsd
                for r in loans.group_by("fico_bucket")
                .agg(pl.col("fico").mean()).iter_rows(named=True)}
        lmap = {r["ltv_bucket"]: (r["orig_ltv"] - lm) / lsd
                for r in loans.group_by("ltv_bucket")
                .agg(pl.col("orig_ltv").mean()).iter_rows(named=True)}
        zf = train["fico_bucket"].map(fmap).astype(float)
        zl = train["ltv_bucket"].map(lmap).astype(float)
        alpha = float(json.load(open(cpe.HAZARD_COEF_PATH))["ridge_alpha"])
        bf, bl = cpe.fit_credit_betas(train, zf, zl, alpha)
        return {"skipped": False, "beta_fico": bf, "beta_ltv": bl,
                "pass": abs(bf - PIN_FICO) < TOL and abs(bl - PIN_LTV) < TOL}
    except Exception as e:  # soft gate per spec
        return {"skipped": True, "reason": repr(e)[:200], "pass": True}


def main() -> None:
    oos = json.load(open(OOS_ARTIFACT))
    off = oos["headline_oos_marginal"]["clean_floor_point_pct"]
    assert abs(off - 4.991) < TOL
    floors = [0.04, off / 100.0]
    cov = json.load(open(COV_ARTIFACT))
    g0f = (abs(cov["estimated"]["beta_fico"]["point"] - PIN_FICO) < TOLP
           and abs(cov["estimated"]["beta_ltv"]["point"] - PIN_LTV) < TOLP)
    offset = json.load(open(CALIB_ARTIFACT))["basis_map"]["offset_pp"]
    g0g = abs(offset - 9.096091632702699) < TOL

    gates = analytic_gates()
    gates["G0f_provenance"] = {"pass": g0f}
    gates["G0g_basis"] = {"offset": offset, "pass": g0g}
    gates["G_refit"] = attempt_refit()
    print("analytic/provenance gates:",
          {k: v["pass"] for k, v in gates.items()})

    print("Shared macro frame (fetched once) ...")
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)

    t0 = time.perf_counter()
    legs: dict = {}
    resto = True
    for scen, (bf, bl) in SCEN.items():
        for floor in floors:
            for pq in (0.0, 6.5):
                set_betas(bf, bl)
                try:
                    r = fs._run_scored(loans, empirical, floor, pq)
                finally:
                    set_betas(PROD_FICO, PROD_LTV)
                resto = resto and (
                    lh.LITERATURE_COEFS["beta_fico"] == PROD_FICO
                    and lh.LITERATURE_COEFS["beta_ltv"] == PROD_LTV
                    and lh.LITERATURE_COEFS["beta_burnout"] == -0.5
                    and abs(lh.INVOLUNTARY_CPR_ANNUAL - 0.04) < TOL)
                r["scenario"] = scen
                r["share_pct_shared"] = r["share_pct"] - offset
                legs[f"{scen}|{floor*100:g}|{pq:g}"] = r
                print(f"  {scen:6s} floor {floor*100:g} pq {pq:g}: "
                      f"${r['trapped_b']:7.2f}B ({r['share_pct']:.2f}%)")

    for (fl, pq), want in ANCH.items():
        got = legs[f"prod|{fl*100:g}|{pq:g}"]["trapped_b"]
        gates[f"G12_prod_{fl*100:g}_{pq:g}"] = {
            "got": got, "want": want, "pass": abs(got - want) < TOL}
    m40 = (legs["prod|4|6.5"]["trapped_b"] - legs["prod|4|0"]["trapped_b"])
    gates["G3_marginal_insample"] = {
        "got_b": m40, "want_b": 70.34506041989584,
        "pass": abs(m40 - 70.34506041989584) < TOL}
    g6 = all(abs(legs[f"prod|{fl*100:g}|{pq:g}"]["floor_bind_share"] - w) < TOL
             and legs[f"prod|{fl*100:g}|{pq:g}"]["floor_bind_loan_months"] == BIND_N
             for (fl, pq), w in BINDS.items())
    gates["G6_bind"] = {"pass": g6}
    for scen, want in G7.items():
        got = legs[f"{scen}|4|6.5"]["trapped_b"]
        gates[f"G7_replay_{scen}"] = {"got": got, "want": want,
                                      "pass": abs(got - want) < TOL}
    gates["G8_restoration"] = {"pass": resto}
    all_pass = all(v["pass"] for v in gates.values())

    def block(fl):
        p, z, r = (legs[f"{s}|{fl}|6.5"]["share_pct"] for s in ("prod", "zeroed", "reest"))
        pn, zn, rn = (legs[f"{s}|{fl}|0"]["share_pct"] for s in ("prod", "zeroed", "reest"))
        return {"zeroed_delta_pp": z - p, "reest_delta_pp": r - p,
                "total_swing_pp": z - r,
                "total_swing_b": legs[f"zeroed|{fl}|6.5"]["trapped_b"]
                                 - legs[f"reest|{fl}|6.5"]["trapped_b"],
                "marginal_prod_pp": p - pn, "marginal_zeroed_pp": z - zn,
                "marginal_reest_pp": r - rn,
                "marginal_swing_pp": (z - zn) - (r - rn)}
    b40, b49 = block("4"), block("4.991")
    comp = {"level_zeroed": b49["zeroed_delta_pp"] / b40["zeroed_delta_pp"]
                            if b40["zeroed_delta_pp"] else None,
            "level_reest": b49["reest_delta_pp"] / b40["reest_delta_pp"]
                           if b40["reest_delta_pp"] else None,
            "level_total": b49["total_swing_pp"] / b40["total_swing_pp"],
            "marginal_total": (b49["marginal_swing_pp"] / b40["marginal_swing_pp"]
                               if b40["marginal_swing_pp"] else None),
            "burnout_precedent_level": 0.5283, "burnout_precedent_marginal": 1.2685,
            "uncensored_share_proxy": 0.4893,
            "within_band_045_060": COMPRESS_BAND[0] <= b49["total_swing_pp"]
                                   / b40["total_swing_pp"] <= COMPRESS_BAND[1]}
    ratio = b49["total_swing_pp"] / MARGINAL_OFF_PP
    branch = ("i" if b49["total_swing_pp"] >= MARGINAL_OFF_PP
              else "ii" if b49["total_swing_pp"] >= MARGINAL_OFF_PP / 2
              else "iii")

    status = "OK" if all_pass else "GATE_FAILURE"
    payload = {
        "mode": "covariate_ablation_offwindow", "status": status,
        "spec": ("scenarios prod/zeroed/re-estimated x paired legs x both "
                 "floors via floor_sweep seamless in-place coefficient "
                 "mutation; G0d/e analytic wiring+leak, G7 cross-artifact "
                 "replay of the committed 108.3/101.3 literals; compression "
                 "band [0.45,0.60] pre-committed on the LEVEL swing; "
                 "marginal-swing direction not pre-signed; landing "
                 "(i)/(ii)/(iii) on swing_off vs the off-window marginal."),
        "pinned_coefficients": {"beta_fico": PIN_FICO, "beta_ltv": PIN_LTV,
                                "source": "covariate_priors_results.json"},
        "parity_gates": gates, "parity_gates_all_pass": all_pass,
        "legs": legs,
        "block_at_production_floor": b40, "block_at_offwindow_floor": b49,
        "compression": comp,
        "comparison_vs_marginal": {
            "swing_pp_offwindow": b49["total_swing_pp"],
            "marginal_pp_offwindow": MARGINAL_OFF_PP, "ratio": ratio,
            "insample_ratio": b40["total_swing_pp"] / 9.198459770709789,
            "exceeds_marginal": b49["total_swing_pp"] >= MARGINAL_OFF_PP},
        "landing_branch": branch,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    def _np(o):
        if hasattr(o, "item"):
            return o.item()
        raise TypeError(f"not serializable: {type(o)}")
    with open(RESULTS_JSON, "w") as f:
        json.dump(payload, f, indent=2, default=_np)
        f.write("\n")
    print(f"\nstatus {status}; swing in-sample {b40['total_swing_pp']:.2f}pp "
          f"-> off-window {b49['total_swing_pp']:.2f}pp "
          f"(compression {comp['level_total']:.3f}); marginal swing "
          f"{b40['marginal_swing_pp']:+.2f} -> {b49['marginal_swing_pp']:+.2f}pp; "
          f"branch ({branch})")
    if status != "OK":
        raise SystemExit(f"{status} — nothing lands in the manuscript.")


if __name__ == "__main__":
    main()
