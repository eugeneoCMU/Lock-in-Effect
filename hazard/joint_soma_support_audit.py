"""Audit joint SOMA coupon/vintage support in the saved Freddie loan sample.

The 2022-06-29 SOMA grid reports cells exceeding 0.1% of total MBS face.
Loan note coupons are shifted down by the primary 80 bp convention before
rounding to the 50 bp pass-through grid. This is a support audit, not an
estimate of a SOMA-weighted runoff effect.
"""

from __future__ import annotations

import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
BOOK = ROOT / "hazard/data/composition_shift_results.json"
LOANS = ROOT / "hazard/data/loan_sample.parquet"
OUT = ROOT / "hazard/data/joint_soma_support_audit.json"


def vintage_group(year: int) -> str:
    if year <= 2016:
        return "pre2017"
    if year <= 2019:
        return "2017-19"
    return str(year)


def audit(book: dict, loans: pl.DataFrame) -> dict:
    soma = book["soma_book"]["asof_june_2022"]
    grid = soma["joint_cells_min_share_0p1pct"]
    cells = {
        key: share for key, share in grid.items()
        if key.startswith("UMBS|30yr|")
    }
    sample = (
        loans.with_columns(
            (pl.col("coupon") - 0.008).truediv(0.005).round(0)
            .mul(0.5).round(1).cast(pl.String).alias("pass_coupon_pct"),
            pl.when(pl.col("vintage") <= 2019)
            .then(pl.lit("2017-19"))
            .otherwise(pl.col("vintage").cast(pl.String)).alias("vintage_group"),
        )
        .with_columns(
            pl.concat_str(
                [pl.lit("UMBS|30yr|"), "pass_coupon_pct", pl.lit("|"), "vintage_group"]
            ).alias("book_cell")
        )
        .group_by("book_cell")
        .agg(pl.len().alias("n_loans"), pl.col("balance").sum().alias("sample_balance"))
    )
    support = {r["book_cell"]: r for r in sample.to_dicts()}
    listed_mass = sum(grid.values())
    umbs_30_listed = sum(cells.values())
    matched = sum(share for key, share in cells.items()
                  if key in support and support[key]["sample_balance"] > 0)
    in_vintage = sum(share for key, share in cells.items()
                     if key.rsplit("|", 1)[1] in ("2017-19", "2020", "2021"))
    return {
        "as_of": soma["as_of"],
        "sample_loans": loans.height,
        "sample_vintages": [loans["vintage"].min(), loans["vintage"].max()],
        "coupon_conversion_note_minus_pp": 0.8,
        "book_grid_min_share_of_total_face": 0.001,
        "grid_listed_share_of_total_face": listed_mass,
        "grid_omitted_share_of_total_face": 1 - listed_mass,
        "listed_umbs_30yr_share_of_total_face": umbs_30_listed,
        "listed_umbs_30yr_in_sample_vintages_share_of_total_face": in_vintage,
        "listed_joint_cells_with_sample_support_share_of_total_face": matched,
        "matched_share_of_listed_umbs_30yr": matched / umbs_30_listed,
        "matched_share_of_total_soma_mbs_face": matched,
        "cells": [
            {"cell": key, "book_share_of_total_face": share,
             "n_loans": support.get(key, {}).get("n_loans", 0),
             "sample_balance": support.get(key, {}).get("sample_balance", 0.0)}
            for key, share in sorted(cells.items(), key=lambda kv: -kv[1])
        ],
        "interpretation": (
            "Support only. The sample lacks term and Fannie/Freddie identity within UMBS; "
            "the grid omits cells below 0.1% of total MBS face. No paired microsimulation "
            "or cell-level floor-binding estimate is made here."
        ),
    }


def main() -> None:
    result = audit(json.loads(BOOK.read_text()), pl.read_parquet(LOANS))
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Matched listed cells: {result['matched_share_of_total_soma_mbs_face']:.3%} "
          "of total SOMA MBS face")


if __name__ == "__main__":
    main()
