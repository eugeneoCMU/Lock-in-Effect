#!/usr/bin/env python3
"""V20-A: compounding-consistent beta1=0 null (run tag: compounding_consistent_null).

Spec: specs/SPEC_V20_A_compounding_null_2026-08-04.md — adopted and committed before
this script; this script committed before it ran. Guarded-runner pattern: sha-pinned
imports, frozen artifacts read-only, single JSON output, gates that ABORT.

DESIGN. The production scorer renormalizes each month's simulated dollar flows to the
REALIZED holdings path (microsim_engine._simulate_regime: scale = WSHOMCB_t / sim
balance_t). The compounding-consistent variant anchors once at the QT opening (the
pool is already scaled to opening holdings by scale_to_holdings) and lets each leg
evolve its own counterfactual balance path: scale = 1.0 every month. Nothing else
changes. The engine walk is copied VERBATIM below but for that one line, and gate
G-A1b proves the copy: run with renormalize=True it must reproduce the committed
production rows bit-identically.

Writes ONLY data/compounding_null_results.json (+ scratch microsim parquets under
data/runs/, same convention as oos_identification).

Run:  cd hazard && python3 compounding_null.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import polars as pl

HAZ = Path(__file__).resolve().parent
if str(HAZ) not in sys.path:
    sys.path.insert(0, str(HAZ))

# ---------------------------------------------------------------- sha pins
PINS = {
    "microsim_engine.py": "02315bba37777728d863c5522e02a459bfd3dbae28eba83aac3cbecb972b8ff0",
    "competing_risks.py": "08be5b3c74c75f5c543fb857e52c4d54e9fd6bb31f4cbd29b21989acbf4aa29a",
    "extension_risk.py": "ecf142146f5db0354b5147e5097d1ae3c5836e2fc57900b156ea009e9e1ebbeb",
    "literature_hazard.py": "c75a653b53cbc0ea033dc7b54cb62804b630a701c2a044d6a8288838decb9540",
    "agents.py": "a9b8487a4658110fb3d59362025e77b6d5aa5ca32b29619935913a36aa620081",
    "oos_identification.py": "4bfe9b1a125d08441d6a6e484d8ebc2b91da18f33dff8d4d857f9985f94d9b08",
    "calibration_reconciliation.py": "027f1dbb088520aeb725db9648f6ba89b366a6d7bcb4cea5f4068a71f4070191",
}
for fname, want in PINS.items():
    got = hashlib.sha256((HAZ / fname).read_bytes()).hexdigest()
    if got != want:
        sys.exit(f"ABORT pin mismatch: {fname} {got[:12]} != {want[:12]}")

import competing_risks                      # noqa: E402
import literature_hazard                    # noqa: E402
import calibration_reconciliation as cr     # noqa: E402
import oos_identification as oos            # noqa: E402
from agents import MicrosimPool             # noqa: E402
from competing_risks import monthly_step    # noqa: E402
from config import (                        # noqa: E402
    N_LOANS, QT_END, QT_START, RNG_SEED, ROTHSTEIN_Q_DECLINE_MID,
    LOAN_SAMPLE_PATH,
)
from extension_risk import (                # noqa: E402
    build_empirical_metrics, score_extension_risk,
)
from literature_hazard import rothstein_beta1   # noqa: E402
from loan_sample import load_or_build_loan_sample   # noqa: E402
from macro import (                         # noqa: E402
    calculate_dynamic_friction, fetch_data, fetch_soma_mbs_monthly,
)
from markov import load_transition_matrix   # noqa: E402

DATA = HAZ / "data"
OUT = DATA / "compounding_null_results.json"
RUN_DIR = DATA / "runs"

FLOOR = 0.04991           # headline off-window floor, decimal (oos engine convention)
PQ_CENTRAL = 6.5          # central elasticity band point
PQ_NULL = 0.0             # beta1 = 0

# Committed production anchors at floor 4.991 (oos_identification_results.json,
# instrument1_marginal_table row): the G-A1 bit-identity targets.
COMMITTED = {
    "null_trapped_b": 724.9180585654117,
    "null_share_pct": 94.79172466371236,
    "central_trapped_b": 767.5264524465003,
    "central_share_pct": 100.36328284662208,
    "marginal_b": 42.60839388108866,
    "marginal_pp": 5.571558182909726,
}


# ---------------------------------------------------------------- engine copy
# VERBATIM copy of microsim_engine._simulate_regime / run_qt_microsim but for the
# renormalize flag; G-A1b proves fidelity by bit-identical ON-mode reproduction.
def _simulate_regime_v20(
    loan_df: pl.DataFrame,
    macro: pd.DataFrame,
    regime: str,
    holdings_scale_b: float,
    trans: pd.DataFrame,
    seed: int,
    beta1: float,
    soma_cohorts: Optional[list] = None,
    coupon_convert=None,
    renormalize: bool = True,
) -> pd.DataFrame:
    """Walk one regime pool through QT window."""
    qt_index = macro.index[(macro.index >= QT_START) & (macro.index < QT_END)]
    pool = MicrosimPool(loan_df, regime=regime, rng=np.random.default_rng(seed))
    if soma_cohorts is not None:
        pool.reweight_to_soma_coupons(
            soma_cohorts, coupon_convert=coupon_convert)
    pool.scale_to_holdings(holdings_scale_b)

    records = []
    for ts in qt_index:
        mkt = float(macro.loc[ts, "MORTGAGE30US"]) / 100.0
        result = monthly_step(pool, mkt, trans=trans, beta1=beta1)

        exposure = result["exposure"]
        monthly_cpr = (result["prepay_upb"] / exposure) if exposure > 0 else 0.0
        annual_cpr_pct = monthly_cpr * 12 * 100

        total_bal = pool.total_exposure()
        holdings_b = float(macro.loc[ts, "WSHOMCB"]) / 1_000
        if renormalize:
            scale = holdings_b / max(total_bal / 1e9, 1e-6) if total_bal > 0 else 1.0
        else:
            scale = 1.0        # <-- the spec's single change: own balance path

        sched_b = result["sched_amt"] * scale / 1e9
        settled_b = result["settled_b"] * scale / 1e9
        sim_rolloff = -(settled_b + sched_b)

        records.append({
            "period": ts,
            "regime": regime,
            "market_rate_pct": mkt * 100,
            "hazard_cpr_pct": annual_cpr_pct,
            "prepay_upb": result["prepay_upb"],
            "exposure": exposure,
            "simulated_rolloff_b": sim_rolloff,
            "weighted_settled_b": settled_b,
            "weighted_sched_b": sched_b,
            "default_count": result["default_count"],
            "delinquency_stock": int(
                np.isin(pool.state_code, [1, 2, 3, 4]).sum()
            ),
        })

    return pd.DataFrame(records).set_index("period")


def _run_qt_microsim_v20(
    loan_sample: Optional[pl.DataFrame] = None,
    macro: Optional[pd.DataFrame] = None,
    n_loans: int = N_LOANS,
    regimes: tuple = ("US", "Danish"),
    seed: int = RNG_SEED,
    output: Path = None,
    p_q_shock_pct: float = ROTHSTEIN_Q_DECLINE_MID * 100,
    soma_cohorts: Optional[list] = None,
    coupon_convert=None,
    renormalize: bool = True,
) -> dict[str, pd.DataFrame]:
    beta1 = rothstein_beta1(p_q_shock_pct / 100.0)
    if loan_sample is None:
        loan_sample = load_or_build_loan_sample(n_loans=n_loans)
    if macro is None:
        macro = calculate_dynamic_friction(fetch_data())

    trans = load_transition_matrix()
    qt_start_idx = macro.index.get_indexer([QT_START], method="nearest")[0]
    holdings_b = float(macro.iloc[qt_start_idx]["WSHOMCB"]) / 1_000

    results = {}
    for i, regime in enumerate(regimes):
        results[regime] = _simulate_regime_v20(
            loan_sample,
            macro,
            regime,
            holdings_b,
            trans,
            seed=seed + i * 1000,
            beta1=beta1,
            soma_cohorts=soma_cohorts,
            coupon_convert=coupon_convert,
            renormalize=renormalize,
        )

    us = results.get("US", results[regimes[0]])
    dk = results.get("Danish", us)
    combined = us.copy()
    combined["CPR_US"] = us["hazard_cpr_pct"]
    combined["CPR_Danish"] = dk.reindex(us.index)["hazard_cpr_pct"]
    combined["Danish_simulated_rolloff_b"] = dk.reindex(us.index)["simulated_rolloff_b"]

    output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(output)
    return results


def _run_scored_v20(loans, macro, empirical, floor, pq, tag, renormalize):
    """Copy of oos_identification._run_scored driving the v20 engine copy."""
    literature_hazard.INVOLUNTARY_CPR_ANNUAL = floor
    tally = oos.BindTally()
    competing_risks.prepay_hazard = oos._tallying_prepay(tally)
    out_path = RUN_DIR / f"microsim_{tag}.parquet"
    try:
        _run_qt_microsim_v20(
            loan_sample=loans, macro=macro, output=out_path, p_q_shock_pct=pq,
            renormalize=renormalize,
        )
    finally:
        competing_risks.prepay_hazard = oos._ORIG_PREPAY
        literature_hazard.INVOLUNTARY_CPR_ANNUAL = oos.PRODUCTION_FLOOR
    sim = pd.read_parquet(out_path)
    score = score_extension_risk(sim, empirical)
    return {
        "floor_annual_cpr_pct": floor * 100.0,
        "p_q_shock_pct": pq,
        "beta1": rothstein_beta1(pq / 100.0),
        "trapped_b": float(score["hazard_trapped_b"]),
        "share_pct": float(score["share_explained_pct"]),
        "mean_us_cpr_pct": float(sim["hazard_cpr_pct"].mean()),
        "floor_bind_share": tally.share,
        "floor_bind_loan_months": tally.n,
    }


def main() -> None:
    t0 = time.perf_counter()
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    assert rothstein_beta1(0.0) == 0.0

    print("Shared macro frame (fetched once) …")
    macro_raw = fetch_data()
    macro = calculate_dynamic_friction(macro_raw)
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro_raw, soma_rolloff=soma)
    loans = pl.read_parquet(LOAN_SAMPLE_PATH)
    print(f"  {len(loans):,} loans")

    legs = {}
    # ---- G-A1a: production code path reproduces committed rows -------------
    print("\nG-A1a: production _run_scored reproduction at (4.991, 6.5/0.0) …")
    prod_c = oos._run_scored(loans, macro, empirical, FLOOR, PQ_CENTRAL, "v20a_prod_central")
    prod_n = oos._run_scored(loans, macro, empirical, FLOOR, PQ_NULL, "v20a_prod_null")
    ga1a = {
        "central_trapped_ok": prod_c["trapped_b"] == COMMITTED["central_trapped_b"],
        "central_share_ok": prod_c["share_pct"] == COMMITTED["central_share_pct"],
        "null_trapped_ok": prod_n["trapped_b"] == COMMITTED["null_trapped_b"],
        "null_share_ok": prod_n["share_pct"] == COMMITTED["null_share_pct"],
    }
    if not all(ga1a.values()):
        detail = {
            "prod_central": prod_c["trapped_b"], "prod_null": prod_n["trapped_b"],
            "committed": COMMITTED, "checks": ga1a,
        }
        sys.exit(f"ABORT G-A1a: production reproduction not bit-identical: {detail}")
    print("  G-A1a PASS (bit-identical)")

    # ---- G-A1b: the v20 copy, renormalize=True, same bit-identity ----------
    print("G-A1b: v20 engine copy, renormalize=True …")
    copy_c = _run_scored_v20(loans, macro, empirical, FLOOR, PQ_CENTRAL, "v20a_copy_central", True)
    copy_n = _run_scored_v20(loans, macro, empirical, FLOOR, PQ_NULL, "v20a_copy_null", True)
    ga1b = {
        "central_ok": copy_c["trapped_b"] == COMMITTED["central_trapped_b"],
        "null_ok": copy_n["trapped_b"] == COMMITTED["null_trapped_b"],
    }
    if not all(ga1b.values()):
        sys.exit(f"ABORT G-A1b: engine copy is not faithful: "
                 f"central {copy_c['trapped_b']} null {copy_n['trapped_b']} vs {COMMITTED}")
    print("  G-A1b PASS (copy faithful)")

    # ---- G-A2: leg configs differ only in beta1 ----------------------------
    ga2 = {"floor_equal": True, "seed_equal": True, "note":
           "both legs share FLOOR/seed/macro/loans by construction; only pq differs"}

    # ---- the compounding-consistent legs -----------------------------------
    print("\nCompounding-consistent legs (renormalize=False) …")
    cc_c = _run_scored_v20(loans, macro, empirical, FLOOR, PQ_CENTRAL, "v20a_cc_central", False)
    cc_n = _run_scored_v20(loans, macro, empirical, FLOOR, PQ_NULL, "v20a_cc_null", False)

    # ---- shared-basis conversion (committed affine layer) ------------------
    shared = cr._load(cr.SHARED_LAYER)
    bmap = cr.derive_basis_map(shared)
    if not bmap["path_invariance_gate"]["pass"]:
        sys.exit("ABORT: shared-layer path-invariance gate failed")
    cc_c_sh_b, cc_c_sh_pct = cr.to_shared(cc_c["trapped_b"], bmap)
    cc_n_sh_b, cc_n_sh_pct = cr.to_shared(cc_n["trapped_b"], bmap)
    prod_c_sh_b, prod_c_sh_pct = cr.to_shared(prod_c["trapped_b"], bmap)
    prod_n_sh_b, prod_n_sh_pct = cr.to_shared(prod_n["trapped_b"], bmap)

    marginal_cc_b = cc_c_sh_b - cc_n_sh_b
    marginal_cc_pp = cc_c_sh_pct - cc_n_sh_pct
    marginal_prod_pp = prod_c_sh_pct - prod_n_sh_pct   # = committed +5.5716

    # ---- landing branch (spec §3, thresholds fixed ex ante) ----------------
    anchor = COMMITTED["marginal_pp"]
    if marginal_cc_pp > anchor + 1e-9:
        branch = "L3_STOP_signing_violated"
    elif marginal_cc_pp >= anchor - 1.0:
        branch = "L1_within_1pp"
    else:
        branch = "L2_companion_figure"

    payload = {
        "mode": "compounding_consistent_null",
        "run_tag": "compounding_consistent_null",
        "spec": "specs/SPEC_V20_A_compounding_null_2026-08-04.md",
        "pins": PINS,
        "committed_anchors": COMMITTED,
        "gates": {"G_A1a": ga1a, "G_A1b": ga1b, "G_A2": ga2,
                  "shared_layer_path_invariance": True},
        "production_renormalized": {
            "central": {k: v for k, v in prod_c.items() if not k.startswith("_")},
            "null": {k: v for k, v in prod_n.items() if not k.startswith("_")},
            "central_shared_share_pct": prod_c_sh_pct,
            "null_shared_share_pct": prod_n_sh_pct,
            "marginal_pp_shared": marginal_prod_pp,
        },
        "compounding_consistent": {
            "central": {k: v for k, v in cc_c.items()},
            "null": {k: v for k, v in cc_n.items()},
            "central_recovery_cc_shared_pct": cc_c_sh_pct,
            "null_recovery_cc_shared_pct": cc_n_sh_pct,
            "marginal_cc_pp": marginal_cc_pp,
            "marginal_cc_b": marginal_cc_b,
        },
        "bias_priced_pp": marginal_prod_pp - marginal_cc_pp,
        "landing_branch": branch,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\n== compounding-consistent: central {cc_c_sh_pct:.2f}% shared, "
          f"null {cc_n_sh_pct:.2f}% shared, marginal {marginal_cc_pp:+.2f}pp "
          f"(${marginal_cc_b:+.1f}B); production {marginal_prod_pp:+.2f}pp; "
          f"bias {marginal_prod_pp - marginal_cc_pp:+.2f}pp; branch {branch}")
    print(f"Wrote {OUT} ({payload['runtime_s']}s)")


if __name__ == "__main__":
    main()
