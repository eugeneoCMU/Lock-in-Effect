"""Verify and record provenance for the fresh Freddie joint-cell sensitivity."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import polars as pl

from soma_fresh_sample import BOOK, OUTPUT as SAMPLE, QUARTERS, REPORT, SNAPSHOTS
from soma_fresh_pair import OUTPUT as PAIR

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hazard/data/soma_fresh_audit.json"
BENCHMARK_B = 764.7482532227002


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    sample_report = json.loads(REPORT.read_text())
    pair_result = json.loads(PAIR.read_text())
    book = json.loads(BOOK.read_text())
    assert len(QUARTERS) == 20
    assert sample_report["source_quarters"] == QUARTERS
    assert pair_result["n"] == sample_report["n"] == 75_000

    snapshot_paths = [SNAPSHOTS / f"{quarter}.parquet" for quarter in QUARTERS]
    assert all(path.exists() for path in snapshot_paths)
    universe_ids = pl.concat([pl.read_parquet(path, columns=["loan_id"])
                              for path in snapshot_paths])
    assert universe_ids.height == sample_report["source_universe_30yr_survivors"]
    assert universe_ids["loan_id"].n_unique() == universe_ids.height
    sample = pl.read_parquet(SAMPLE)
    assert sample.height == sample["loan_id"].n_unique() == 75_000
    assert sample["reporting_period"].unique().to_list() == ["202205"]
    assert sample["original_loan_term"].unique().to_list() == [360]
    assert sample["balance"].min() > 0
    assert sample.join(universe_ids, on="loan_id", how="semi").height == 75_000

    cells = sample_report["cell_report"]
    assert len(cells) == len(pair_result["weighting"]["cell_counts"]) == 12
    assert all(row["freddie_universe_loans"] >= row["sample_loans"] > 0
               for row in cells.values())
    assert sum(row["sample_loans"] for row in cells.values()) == 75_000
    assert pair_result["weighting"]["cell_counts"] == {
        cell: row["sample_loans"] for cell, row in cells.items()
    }
    assert pair_result["weighting"]["max_target_share_error"] < 1e-8
    assert pair_result["weighting"]["supported_sample_balance_share"] == 1.0

    pair = pair_result["pair"]
    assert pair["null_bind_n"] == pair["central_bind_n"] > 0
    null_bound = pair["null_bind"] * pair["null_bind_n"]
    central_bound = pair["central_bind"] * pair["central_bind_n"]
    assert abs(null_bound - round(null_bound)) < 1e-8
    assert abs(central_bound - round(central_bound)) < 1e-8
    assert abs(pair["central_trapped_b"] - pair["null_trapped_b"]
               - pair["marginal_b"]) < 1e-10
    assert abs(pair["central_share_pct"] - pair["null_share_pct"]
               - pair["marginal_pp"]) < 1e-10
    assert abs(pair["marginal_b"] / BENCHMARK_B * 100
               - pair["marginal_pp"]) < 1e-10

    saved = json.loads((ROOT / "hazard/data/joint_soma_pair_results.json").read_text())
    code_paths = [ROOT / "hazard" / name for name in (
        "soma_stream_snapshot.py", "soma_fresh_sample.py", "soma_fresh_pair.py",
        "soma_fresh_audit.py", "joint_soma_pair.py", "book_composition_marginal.py",
        "microsim_engine.py", "agents.py", "competing_risks.py", "macro.py",
    )]
    result = {
        "status": "passed",
        "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                            text=True).strip(),
        "source_snapshot_sha256": {path.stem: sha(path) for path in snapshot_paths},
        "source_snapshot_rows": {path.stem: pl.read_parquet(path).height
                                 for path in snapshot_paths},
        "code_sha256": {str(path.relative_to(ROOT)): sha(path) for path in code_paths},
        "input_dates": {"survivor_month": "2022-05", "soma_joint_grid_as_of":
                        book["soma_book"]["asof_june_2022"]["as_of"],
                        "qt_window": "2022-06 through 2025-11"},
        "sample_seed": sample_report["seed"],
        "sample_n": sample.height,
        "universe_n": universe_ids.height,
        "target_cells": len(cells),
        "min_target_cell_sample_n": min(row["sample_loans"] for row in cells.values()),
        "max_target_balance_share_error": pair_result["weighting"]["max_target_share_error"],
        "supported_total_soma_face_share": pair_result["listed_cells_total_soma_face_share"],
        "benchmark_b": BENCHMARK_B,
        "fresh_marginal_b": pair["marginal_b"],
        "fresh_marginal_pp": pair["marginal_pp"],
        "saved_sample_joint_marginal_b": saved["joint_pair"]["marginal_b"],
        "saved_sample_joint_marginal_pp": saved["joint_pair"]["marginal_pp"],
        "production_anchor_marginal_pp": saved["baseline_pair"]["marginal_pp"],
        "floor_binding": {
            "evaluated_loan_months_each_leg": pair["null_bind_n"],
            "response_off_bound_months": round(null_bound),
            "response_on_bound_months": round(central_bound),
            "response_off_share": pair["null_bind"],
            "response_on_share": pair["central_bind"],
        },
        "output_sha256": {str(path.relative_to(ROOT)): sha(path)
                          for path in (SAMPLE, REPORT, PAIR)},
        "interpretation": "Freddie-only May-2022 survivor draw targeted to listed June-2022 UMBS 30-year coupon-by-vintage cells after an assumed 80 bp note-to-pass-through bridge. The supported 47.6% book slice is scaled to all holdings in both legs. This is a conditional whole-pool model sensitivity, not the actual dollar contribution of that slice or a full-SOMA causal estimate.",
    }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Fresh audit passed: {sample.height:,} loans; "
          f"{pair['marginal_pp']:.4f} pp; ${pair['marginal_b']:.4f}B")


if __name__ == "__main__":
    main()
