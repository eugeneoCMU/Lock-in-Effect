"""Paired sensitivity using the listed June-2022 UMBS 30-year joint cells.

This reweights the *saved* Freddie sample within its supported coupon x vintage
cells. It is not a fresh SOMA probability sample or a full-book estimate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "abm", ROOT / "hazard"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import agents  # noqa: E402
import book_composition_marginal as prior  # noqa: E402
import microsim_engine  # noqa: E402
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly  # noqa: E402

BOOK = ROOT / "hazard/data/composition_shift_results.json"
OUTPUT = ROOT / "hazard/data/joint_soma_pair_results.json"


def targets(book: dict) -> tuple[dict[tuple[float, str], float], float]:
    grid = book["soma_book"]["asof_june_2022"]["joint_cells_min_share_0p1pct"]
    selected = {}
    for key, share in grid.items():
        agency, term, coupon, vintage = key.split("|")
        if agency == "UMBS" and term == "30yr" and vintage in ("2017-19", "2020", "2021"):
            selected[(float(coupon) / 100, vintage)] = float(share)
    mass = sum(selected.values())
    return {key: value / mass for key, value in selected.items()}, mass


def joint_reweight(target: dict[tuple[float, str], float], report: dict):
    def apply(self, soma_cohorts, coupon_convert=None):
        if self.vintage is None:
            raise ValueError("Joint reweight requires loan vintages")
        # The primary coupon-convention leg: borrower note less 80 bp.
        converted = self.coupon - 0.008
        coupon_bucket = np.round(np.round(converted / 0.005) * 0.005, 4)
        vint = np.where(self.vintage <= 2019, "2017-19", self.vintage.astype(str))
        original = self.balance.copy()
        balance = np.zeros(self.n, dtype=np.float64)
        counts = {}
        for (coupon, vintage), share in target.items():
            mask = np.isclose(coupon_bucket, coupon) & (vint == vintage)
            count = int(mask.sum())
            counts[f"{coupon:.4f}|{vintage}"] = count
            cell_balance = original[mask].sum()
            if cell_balance <= 0:
                raise ValueError(f"Unsupported target cell {coupon}|{vintage}")
            balance[mask] = original[mask] * share / cell_balance
        balance *= original.sum()
        weights = np.divide(balance, original, out=np.zeros_like(balance), where=original > 0)
        self.balance = balance
        self.orig_upb *= weights
        self.stratum_orig_upb = np.bincount(
            self.stratum_id_code, weights=self.orig_upb, minlength=self.n_strata
        ).astype(np.float64)
        self._update_active_mask()
        report.update({"cell_counts": counts,
                       "supported_sample_balance_share": float(original[balance > 0].sum() / original.sum()),
                       "max_target_share_error": float(max(
                           abs(balance[(np.isclose(coupon_bucket, c) & (vint == v))].sum()
                               / balance.sum() - share)
                           for (c, v), share in target.items()))})
    return apply


def main() -> None:
    book = json.loads(BOOK.read_text())
    target, mass = targets(book)
    loans = pl.read_parquet(prior.fs.LOAN_SAMPLE_PATH)
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    previous_fetch = microsim_engine.fetch_data
    previous_reweight = agents.MicrosimPool.reweight_to_soma_coupons
    report = {}
    microsim_engine.fetch_data = lambda *args, **kwargs: macro
    try:
        print("Baseline paired parity...")
        baseline = prior.pair(loans, empirical)
        if abs(baseline["marginal_pp"] - prior.BASE_MARGINAL_PP) > 1e-8:
            raise RuntimeError("Baseline parity failed; refusing sensitivity result")
        agents.MicrosimPool.reweight_to_soma_coupons = joint_reweight(target, report)
        print("Joint-cell paired run...")
        joint = prior.pair(loans, empirical, cohorts=[])
    finally:
        agents.MicrosimPool.reweight_to_soma_coupons = previous_reweight
        microsim_engine.fetch_data = previous_fetch
    result = {
        "mode": "saved_sample_joint_umbs30_sensitivity",
        "book_as_of": book["soma_book"]["asof_june_2022"]["as_of"],
        "covered_total_soma_face_share": mass,
        "target_cells": {f"{c:.4f}|{v}": s for (c, v), s in target.items()},
        "baseline_pair": baseline,
        "joint_pair": joint,
        "move_pp": joint["marginal_pp"] - baseline["marginal_pp"],
        "weighting": report,
        "scope": "Conditional on listed UMBS 30-year cells in 2017-2021 and the saved Freddie sample; no new raw-universe draw, Ginnie, 15-year, 2022, or pre-2017 estimate.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Joint marginal {joint['marginal_pp']:.4f} pp; move {result['move_pp']:+.4f} pp")


if __name__ == "__main__":
    main()
