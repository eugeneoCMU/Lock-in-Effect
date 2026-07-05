#!/usr/bin/env python3
"""
3.1 — Full-book SOMA cohort weighting in the hazard microsim.

The Path B microsim samples Freddie 2017-2021 loans (WAC ~3.4%), which do not
match the actual SOMA book's coupon composition (WAC ~2.5%, dominated by 2.0-2.5%
pandemic coupons). This reruns Path B with per-loan balances reweighted so the
pool's coupon-bucket composition matches SOMA (`reweight_to_soma_coupons`), and
reports the shift vs the current balance-weighted result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
for p in (_REPO, _REPO / "abm"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from extension_risk import score_extension_risk
from loan_sample import load_or_build_loan_sample
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim

OUT = _REPO / "hazard" / "data" / "full_book_weighting_results.json"


def _run(loans, macro, empirical, soma_cohorts, tag):
    out = _REPO / "hazard" / "data" / f"_fullbook_{tag}.parquet"
    paths = run_qt_microsim(loan_sample=loans, macro=macro, regimes=("US",),
                            output=out, soma_cohorts=soma_cohorts)
    res = score_extension_risk(paths["US"], empirical)
    if out.exists():
        out.unlink()
    return {
        "trapped_b": res["hazard_trapped_b"],
        "share_pct": res["share_explained_pct"],
        "cpr_r_lag0": res["cross_correlation"].get(0),
        "peak_lag": res["best_lag"],
    }


def _run_path_a(empirical, soma_cohorts):
    from simulate import simulate_qt_window
    sim = simulate_qt_window(soma_cohorts=soma_cohorts)
    res = score_extension_risk(sim, empirical)
    return {
        "trapped_b": res["hazard_trapped_b"],
        "share_pct": res["share_explained_pct"],
        "cpr_r_lag0": res["cross_correlation"].get(0),
        "peak_lag": res["best_lag"],
    }


def _table(title, base, full):
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)
    print(f"  {'':22}{'balance-wt':>14}{'full-book':>14}")
    print(f"  {'Trapped $B':22}{base['trapped_b']:>14.1f}{full['trapped_b']:>14.1f}")
    print(f"  {'Share %':22}{base['share_pct']:>14.1f}{full['share_pct']:>14.1f}")
    print(f"  {'CPR r(lag0)':22}{base['cpr_r_lag0']:>14.3f}{full['cpr_r_lag0']:>14.3f}")
    print(f"  {'Peak lag':22}{base['peak_lag']:>14}{full['peak_lag']:>14}")
    print("-" * 60)
    print(f"  Trapped shift: {full['trapped_b']-base['trapped_b']:+.1f}B "
          f"({full['share_pct']-base['share_pct']:+.1f}pp)")


def main() -> None:
    from fed_mbs_extension_risk import fetch_soma_mbs_cohorts

    loans = load_or_build_loan_sample()
    macro = fetch_data()
    empirical = build_empirical_metrics(fetch_data(),
                                        soma_rolloff=fetch_soma_mbs_monthly())

    print("Fetching SOMA cohorts …")
    cohorts = fetch_soma_mbs_cohorts()

    print("Path B baseline (balance-weighted) …")
    b_base = _run(loans, macro, empirical, None, "base")
    print("Path B full-book …")
    b_full = _run(loans, macro, empirical, cohorts, "fullbook")

    print("Path A baseline (balance-weighted) …")
    a_base = _run_path_a(empirical, None)
    print("Path A full-book …")
    a_full = _run_path_a(empirical, cohorts)

    payload = {
        "sample_wac_pct": float(loans["coupon"].mean()) * 100,
        "path_b": {"balance_weighted": b_base, "full_book_weighted": b_full},
        "path_a": {"balance_weighted": a_base, "full_book_weighted": a_full},
    }
    OUT.write_text(json.dumps(payload, indent=2))

    _table("FULL-BOOK SOMA WEIGHTING — Path B (literature microsim)", b_base, b_full)
    _table("FULL-BOOK SOMA WEIGHTING — Path A (cohort GLM)", a_base, a_full)
    print(f"\n  Saved: {OUT}")


if __name__ == "__main__":
    main()
