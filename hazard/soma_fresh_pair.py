"""Paired response-on/off sensitivity for the fresh Freddie cell-targeted draw."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT, ROOT / "abm", ROOT / "hazard"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import agents  # noqa: E402
import book_composition_marginal as prior  # noqa: E402
import microsim_engine  # noqa: E402
from joint_soma_pair import joint_reweight, targets  # noqa: E402
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly  # noqa: E402
from soma_fresh_sample import BOOK, OUTPUT as SAMPLE, REPORT as SAMPLE_REPORT  # noqa: E402

OUTPUT = ROOT / "hazard/data/soma_fresh_pair_results.json"


def main() -> None:
    if not SAMPLE.exists() or not SAMPLE_REPORT.exists():
        raise FileNotFoundError("Run soma_fresh_sample.py first")
    sample_report = json.loads(SAMPLE_REPORT.read_text())
    if sample_report["n"] != 75_000 or len(sample_report["source_quarters"]) != 20:
        raise ValueError("Fresh draw is not the required 75,000 loans / 20 quarters")
    loans = pl.read_parquet(SAMPLE)
    target, mass = targets(json.loads(BOOK.read_text()))
    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    previous_fetch = microsim_engine.fetch_data
    previous_reweight = agents.MicrosimPool.reweight_to_soma_coupons
    report = {}
    microsim_engine.fetch_data = lambda *args, **kwargs: macro
    try:
        # The same loan IDs and random seeds enter both response legs.
        agents.MicrosimPool.reweight_to_soma_coupons = joint_reweight(target, report)
        pair = prior.pair(loans, empirical, cohorts=[])
    finally:
        agents.MicrosimPool.reweight_to_soma_coupons = previous_reweight
        microsim_engine.fetch_data = previous_fetch
    if report["max_target_share_error"] > 1e-8:
        raise RuntimeError("Joint balance targets did not match")
    result = {
        "mode": "fresh_freddie_umbs30_cell_targeted_paired_sensitivity",
        "sample_report": str(SAMPLE_REPORT.relative_to(ROOT)),
        "n": len(loans),
        "listed_cells_total_soma_face_share": mass,
        "pair": pair,
        "weighting": report,
        "scope": "Paired model marginal using a new Freddie 30-year May-2022 survivor draw, with listed June-2022 UMBS 30-year coupon-by-vintage cell shares. Conditional whole-pool scaling; not a causal estimate or a direct full-SOMA estimate.",
    }
    OUTPUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Fresh joint-cell marginal: {pair['marginal_pp']:.4f} pp; "
          f"${pair['marginal_b']:.4f}B")


if __name__ == "__main__":
    main()
