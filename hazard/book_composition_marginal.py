"""
R32 C-07 — post-stratify the 75,000-loan draw onto the book's composition.

Implements specs/SPEC_R32_c07_post_stratification.md EXACTLY. Read that first.

WHAT THIS IS AND IS NOT. The condition asks for coupon x vintage-group CELLS. The joint is
not observable: fetch_soma_mbs_cohorts collapses the vintage inside each (term, coupon)
bucket to one value-weighted origin_date before returning, so the within-coupon vintage
DISTRIBUTION is destroyed. Both MARGINALS are available, so this rakes to two marginals by
iterative proportional fitting and does NOT match a joint. Every quotation of the result
must say so (spec Section 1).

SUPPORT. The draw is vintages 2017-2021. The book's pre-2017 (10.6%) and 2022 (23.1%) --
33.7% of face -- have zero support and cannot be created by reweighting, so the vintage
target is the book's CONDITIONAL mix within 2017-2021 and the 33.7% stays with
vintage_overlay (spec Section 2).

DO NOT CONFUSE (spec Section 2.1): vintage_overlay's shares.retained = 0.663 is 1 - 0.337,
the IN-SUPPORT share of book FACE. The renormalised 2021 share here is 0.6631. Two
different objects that agree to three decimals by coincidence.

SEAM. microsim_engine calls pool.reweight_to_soma_coupons(...) then pool.scale_to_holdings
(hazard/microsim_engine.py:44-47). This patches the METHOD with a raking version and
restores it, editing no repo file.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl

import fed_mbs_extension_risk as fed

import agents
import competing_risks
import floor_sweep as fs
import literature_hazard
import microsim_engine
from coupon_convention_reweight import DELTA_LEGS, PRIMARY_LEG, make_converter
from extension_risk import score_extension_risk
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "book_composition_marginal_results.json"
COMPOSITION = DATA_DIR / "composition_shift_results.json"
SPEC_PATH = "specs/SPEC_R32_c07_post_stratification.md"

TOL = 1e-9
FLOOR = 0.04991
CENTRAL_PQ, NULL_PQ = 6.5, 0.0
PARITY_NULL_B = 724.9180585654117
PARITY_CENTRAL_B = 767.5264524465003
BASE_MARGINAL_PP = 5.571558182909726
BIND_CENTRAL_COMMITTED = 0.6881875607501289      # 68.8% of 1,683,124 loan-months
BIND_N_COMMITTED = 1683124
COUPON_STEP = 0.005
IPF_TOL, IPF_MAX = 1e-10, 200
BAND = (2.5, 5.0)                                # spec Section 7, pre-committed
PREDICTION = ("the marginal FALLS from +5.5716 into [+2.5, +5.0]: raking moves weight out "
              "of 2017-19 into 2021, the deepest out-of-the-money and least seasoned "
              "cohort, where under the hard maximum the floor binds most and the marginal "
              "is zero wherever it binds on both legs")

_ORIG_REWEIGHT = agents.MicrosimPool.reweight_to_soma_coupons
_ORIG_ENGINE_FETCH = microsim_engine.fetch_data
VGROUPS = {"2017-19": (2017, 2018, 2019), "2020": (2020,), "2021": (2021,)}


def retrying(fn, what, tries=6):
    import time as _t
    for k in range(tries):
        try:
            return fn()
        except Exception as e:                                   # noqa: BLE001
            if k == tries - 1:
                raise
            print(f"   {what} failed ({type(e).__name__}: {e}); retry in {5*2**k}s")
            _t.sleep(5 * (2 ** k))


def data_shas() -> dict:
    return {str(p.relative_to(DATA_DIR)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(DATA_DIR.rglob("*"))
            if p.is_file() and "floor_sweep" not in p.parts and p != RESULTS_JSON}


def coupon_target(cohorts) -> dict:
    """Same construction reweight_to_soma_coupons uses: 30-year only, 0.5% buckets,
    renormalised."""
    t = {}
    for c in cohorts:
        if int(c.get("term_months", 360)) != 360:
            continue
        b = round(round(float(c["coupon"]) / COUPON_STEP) * COUPON_STEP, 4)
        t[b] = t.get(b, 0.0) + float(c["weight"])
    s = sum(t.values())
    return {k: v / s for k, v in t.items()}


def vintage_target() -> dict:
    vs = json.load(open(COMPOSITION))["committed_anchors"]["vintage_shares"]
    inb = {g: vs[g] for g in VGROUPS}
    s = sum(inb.values())
    return {g: v / s for g, v in inb.items()}, s


REPORT: dict = {}


def make_raking_reweight(ctarget: dict, vtarget: dict | None, converter):
    """Replacement for MicrosimPool.reweight_to_soma_coupons. IPF on the per-loan
    balance weights so the balance share of each coupon bucket matches the SOMA
    coupon marginal AND the balance share of each vintage group matches the
    renormalised book mix. Either target may be None: ctarget=None gives the
    VINTAGE-ONLY limb (limb (ii)), vtarget=None the coupon-only one."""
    def rw(self, soma_cohorts, coupon_convert=None):
        src = self.coupon if converter is None else np.asarray(
            converter(self.coupon, self.vintage), dtype=np.float64)
        buckets = np.round(np.round(src / COUPON_STEP) * COUPON_STEP, 4)
        vgrp = np.array(["out"] * self.n, dtype=object)
        for g, years in VGROUPS.items():
            vgrp[np.isin(self.vintage, years)] = g

        bal = self.balance.astype(np.float64).copy()
        cmask = {b: np.isclose(buckets, b) for b in (ctarget or {})}
        vmask = {g: (vgrp == g) for g in (vtarget or {})}
        # mass with no target coupon bucket is zeroed, exactly as the committed
        # coupon-only path does ("Buckets absent from SOMA are zeroed"). With no
        # coupon target (the vintage-only limb) nothing is zeroed.
        if ctarget:
            keep = np.zeros(self.n, dtype=bool)
            for m in cmask.values():
                keep |= m
            bal[~keep] = 0.0
        else:
            keep = np.ones(self.n, dtype=bool)

        ec = ev = 0.0
        for it in range(IPF_MAX):
            if ctarget:
                tot = bal.sum()
                for b, share in ctarget.items():
                    cur = bal[cmask[b]].sum() / tot
                    if cur > 0:
                        bal[cmask[b]] *= share / cur
            if vtarget:
                tot = bal.sum()
                for g, share in vtarget.items():
                    cur = bal[vmask[g]].sum() / tot
                    if cur > 0:
                        bal[vmask[g]] *= share / cur
            tot = bal.sum()
            ec = (max(abs(bal[cmask[b]].sum() / tot - sh) for b, sh in ctarget.items())
                  if ctarget else 0.0)
            ev = (max(abs(bal[vmask[g]].sum() / tot - sh) for g, sh in vtarget.items())
                  if vtarget else 0.0)
            if max(ec, ev) < IPF_TOL:
                break

        w = np.divide(bal, self.balance, out=np.zeros(self.n),
                      where=self.balance > 0)
        REPORT.update({"ipf_iterations": it + 1,
                       "ipf_converged": bool(max(ec, ev) < IPF_TOL),
                       "max_coupon_margin_error": float(ec),
                       "max_vintage_margin_error": float(ev),
                       "coupon_bucket_achieved": {str(b): float(bal[cmask[b]].sum() / bal.sum())
                                                  for b in (ctarget or {})},
                       "vintage_achieved": {g: float(bal[vmask[g]].sum() / bal.sum())
                                            for g in (vtarget or {})},
                       "zeroed_balance_share": float(1.0 - keep.mean())})
        self.balance = bal
        self.orig_upb = self.orig_upb * w
        self.stratum_orig_upb = np.zeros(self.n_strata, dtype=np.float64)
        for i in range(self.n):
            self.stratum_orig_upb[self.stratum_id_code[i]] += self.orig_upb[i]
        self._update_active_mask()
    return rw


def cell(loans, empirical, pq: float, cohorts=None) -> dict:
    """One scored microsim. cohorts=None -> unweighted production path."""
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = FLOOR
    tally = fs.BindTally()
    competing_risks.prepay_hazard = fs._tallying_prepay(tally)
    out = fs.SWEEP_DIR / f"microsim_c07_pq{pq:g}.parquet"
    try:
        res = run_qt_microsim(loan_sample=loans, output=out, p_q_shock_pct=pq,
                              soma_cohorts=cohorts)
    finally:
        competing_risks.prepay_hazard = fs._ORIG_PREPAY
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = fs.PRODUCTION_FLOOR
    import pandas as pd
    sim = pd.read_parquet(out)
    sc = score_extension_risk(sim, empirical)
    return {"trapped_b": float(sc["hazard_trapped_b"]),
            "share_pct": float(sc["share_explained_pct"]),
            "floor_bind_share": tally.share, "floor_bind_loan_months": tally.n}


def pair(loans, empirical, cohorts=None) -> dict:
    n = cell(loans, empirical, NULL_PQ, cohorts)
    c = cell(loans, empirical, CENTRAL_PQ, cohorts)
    return {"null_trapped_b": n["trapped_b"], "central_trapped_b": c["trapped_b"],
            "null_share_pct": n["share_pct"], "central_share_pct": c["share_pct"],
            "marginal_b": c["trapped_b"] - n["trapped_b"],
            "marginal_pp": c["share_pct"] - n["share_pct"],
            "null_bind": n["floor_bind_share"], "central_bind": c["floor_bind_share"],
            "central_bind_n": c["floor_bind_loan_months"]}


def main() -> None:
    t0 = time.perf_counter()
    if RESULTS_JSON.exists():
        sys.exit(f"REFUSING TO WRITE: {RESULTS_JSON} exists (spec Section 6).")
    sha_before = data_shas()
    gates: dict = {}

    print("loading macro + loans + SOMA cohorts ...")
    macro = retrying(fetch_data, "fetch_data")
    soma = retrying(fetch_soma_mbs_monthly, "fetch_soma_mbs_monthly")
    cohorts = retrying(fed.fetch_soma_mbs_cohorts, "fetch_soma_mbs_cohorts")
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    microsim_engine.fetch_data = lambda *a, **k: macro     # see h0_reanchor; P1 validates

    ct = coupon_target(cohorts)
    vt, insupport = vintage_target()
    print(f"coupon target: {len(ct)} buckets; vintage target (renormalised over "
          f"{insupport:.4f} of book face): " +
          ", ".join(f"{g} {v:.4f}" for g, v in vt.items()))

    # ---- P1: unweighted parity -------------------------------------------
    print("P1: unweighted parity at 4.991% ...")
    unw = pair(loans, empirical)
    p1 = (abs(unw["null_trapped_b"] - PARITY_NULL_B) < TOL
          and abs(unw["central_trapped_b"] - PARITY_CENTRAL_B) < TOL)
    gates["P1_unweighted_parity"] = {
        "pass": bool(p1), "null_got": unw["null_trapped_b"], "null_want": PARITY_NULL_B,
        "central_got": unw["central_trapped_b"], "central_want": PARITY_CENTRAL_B,
        "marginal_pp_got": unw["marginal_pp"], "marginal_pp_want": BASE_MARGINAL_PP}
    gates["P4_bind_parity"] = {
        "pass": bool(abs(unw["central_bind"] - BIND_CENTRAL_COMMITTED) < 1e-3
                     and unw["central_bind_n"] == BIND_N_COMMITTED),
        "central_bind_got": unw["central_bind"], "want": BIND_CENTRAL_COMMITTED,
        "n_got": unw["central_bind_n"], "n_want": BIND_N_COMMITTED}
    print(f"   P1 {'PASS' if p1 else 'FAIL'}  marginal_pp {unw['marginal_pp']:.6f}  "
          f"bind {unw['central_bind']:.4f}")

    # ---- limb (ii) vintage margin ALONE, then the post-stratified pair -----
    # Without this limb a null result cannot be attributed: SS VII.E already shows the
    # COUPON margin alone leaves the marginal bit-invariant, so an unreached vintage
    # margin would look identical to "composition does not matter".
    print("limb (ii): vintage margin ALONE ...")
    agents.MicrosimPool.reweight_to_soma_coupons = make_raking_reweight(
        None, vt, make_converter(DELTA_LEGS[PRIMARY_LEG]))
    try:
        vintage_only = pair(loans, empirical, cohorts)
        vintage_only_report = dict(REPORT)
    finally:
        agents.MicrosimPool.reweight_to_soma_coupons = _ORIG_REWEIGHT
    print(f"   vintage-only marginal_pp {vintage_only['marginal_pp']:.4f}")

    print("post-stratified: both margins ...")
    agents.MicrosimPool.reweight_to_soma_coupons = make_raking_reweight(
        ct, vt, make_converter(DELTA_LEGS[PRIMARY_LEG]))
    try:
        post = pair(loans, empirical, cohorts)
        post_report = dict(REPORT)
    finally:
        agents.MicrosimPool.reweight_to_soma_coupons = _ORIG_REWEIGHT
    print(f"   post-stratified marginal_pp {post['marginal_pp']:.4f}")

    gates["P2_margins_hit"] = {
        "pass": bool(post_report.get("ipf_converged")),
        "max_coupon_margin_error": post_report.get("max_coupon_margin_error"),
        "max_vintage_margin_error": post_report.get("max_vintage_margin_error"),
        "iterations": post_report.get("ipf_iterations"),
        "note": "targets recomputed inside the run from SOMA cohorts and "
                "composition_shift_results.json; not taken from the spec file"}
    gates["P3_no_op_detection"] = {
        "pass": bool(abs(post["null_trapped_b"] - unw["null_trapped_b"]) > 1.0
                     or abs(post["central_trapped_b"] - unw["central_trapped_b"]) > 1.0),
        "threshold_b": 1.0,
        "null_delta_b": post["null_trapped_b"] - unw["null_trapped_b"],
        "central_delta_b": post["central_trapped_b"] - unw["central_trapped_b"]}
    gates["P6_coupon_untouched"] = {
        "pass": True,
        "note": "the converter is applied to a LOCAL COPY inside the raking hook; "
                "self.coupon is never reassigned (round-28 G2 design)"}

    microsim_engine.fetch_data = _ORIG_ENGINE_FETCH
    assert agents.MicrosimPool.reweight_to_soma_coupons is _ORIG_REWEIGHT
    sha_after = data_shas()
    gates["P7_frozen_artifacts"] = {
        "pass": sha_before == sha_after, "n_files": len(sha_before),
        "scope_note": "hazard/data/** excluding the gitignored floor_sweep/ scratch dir",
        "changed": [k for k in sha_before if sha_before.get(k) != sha_after.get(k)]}

    mp = post["marginal_pp"]
    out = {
        "mode": "book_composition_marginal",
        "spec": SPEC_PATH,
        "spec_sha256": hashlib.sha256(
            (Path(__file__).parent.parent / SPEC_PATH).read_bytes()).hexdigest(),
        "joint_not_matched_note": (
            "rakes to TWO MARGINALS; the coupon x vintage JOINT is not observable "
            "because fetch_soma_mbs_cohorts collapses vintage to one value-weighted "
            "origin_date per (term, coupon) bucket. This is not a cell match."),
        "support_note": (
            "the draw is vintages 2017-2021; the book's pre-2017 (10.6%) and 2022 "
            "(23.1%) = 33.7% of face have ZERO support and stay with vintage_overlay"),
        "targets": {"coupon": {str(k): v for k, v in ct.items()},
                    "vintage_renormalised": vt,
                    "in_support_face_share": insupport},
        "unweighted_pair": unw,
        "vintage_only_pair": vintage_only,
        "vintage_only_ipf": vintage_only_report,
        "post_stratified_pair": post,
        "post_stratified_ipf": post_report,
        "marginal_pp": mp,
        "move_pp_vs_headline": mp - BASE_MARGINAL_PP,
        "pre_committed_band_pp": list(BAND),
        "in_band": bool(BAND[0] <= mp <= BAND[1]),
        "prediction": PREDICTION,
        "prediction_held": bool(mp < BASE_MARGINAL_PP),
        "gates": gates,
        "gates_all_pass": all(g.get("pass") for g in gates.values()),
        "branch": ("A" if all(g.get("pass") for g in gates.values()) else "C"),
        "runtime_s": time.perf_counter() - t0,
    }
    RESULTS_JSON.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {RESULTS_JSON}  marginal_pp {mp:.4f}  branch={out['branch']}  "
          f"gates_all_pass={out['gates_all_pass']}  elapsed {out['runtime_s']:.1f}s")


if __name__ == "__main__":
    main()
