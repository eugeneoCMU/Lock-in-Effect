#!/usr/bin/env python3
"""
Expectations-based benchmark complement (pre-committed; spec fixed in this
header before any run executed — referee Q10, round-14 report).

Referee ask: the paper's $764.7B benchmark is CAP-relative (phased $17.5B →
$35B/month redemption caps), and market participants expected the caps to be
non-binding for MBS; complement the decomposition with a
"reasonable-expectation" benchmark (e.g., New York Fed staff projections) to
show the results are not an artifact of the cap-relative basis. The paper
currently argues the cap basis is the only non-circular one (III.D) while
itself citing the NY Fed projection — this run closes that tension with
arithmetic instead of argument.

SPEC (fixed ex ante):
- Expectation source, pinned: the SOMA agency-MBS paydown/runoff projection
  published in the Federal Reserve Bank of New York's "Open Market
  Operations During 2022" annual report (the projection vintage
  contemporaneous with QT's start — a genuine ex-ante expectation; the same
  document the manuscript already cites as nyfed2022). Baseline scenario.
  The published path is transcribed into PROJECTED_RUNOFF_B below at the
  granularity the report prints (with the report page/exhibit recorded in
  PROJECTION_PROVENANCE); if the report prints coarser-than-monthly totals,
  they are spread uniformly within each printed period (rule fixed here,
  before anyone sees what it does to the numbers).
- Window: June 2022 – November 2025 inclusive (the paper's 42 active QT
  months), matching the cap-relative benchmark's window exactly.
- Construction: E-shortfall = Σ projected runoff − Σ actual runoff over the
  window, with the actual leg computed by the SAME pipeline machinery as the
  production benchmark (macro.fetch_data + fetch_soma_mbs_monthly +
  build_empirical_metrics; no new empirical constructions). Every
  estimator's trapped-liquidity DOLLAR is unchanged by construction — this
  run re-QUOTES committed artifacts on the new basis; it re-runs nothing.
- Reported per estimator (from committed artifacts only: the production
  central/null caches' scored values as recorded in
  no_lockin_null_results.json, fannie_replication_results.json, and the
  ABM manifests' headline dollars): trapped $B (unchanged), share of the
  E-benchmark, and the lock-in marginal on both bases ($B identical;
  pp rescaled by the benchmark ratio).
- Gates: (i) transcription self-check — the transcribed path must reproduce
  the report's printed cumulative total (TRANSCRIPTION_TOTAL_B) exactly;
  (ii) parity — the cap-relative shares recomputed here from committed
  artifacts must reproduce the published values to ±0.01pp (scoring-
  environment sanity, same convention as every other run); (iii) identity —
  share_E × E-benchmark == trapped_b to machine precision.
- Ex-ante interpretive threshold: the paper's mechanical-majority claim
  survives the basis change iff the β₁=0 null still recovers the majority
  (>50%) of the expectations-based shortfall; estimator RANKING and every
  dollar difference are basis-invariant by construction and are asserted,
  not argued. If the null's E-share falls below the central's by more than
  the cap-basis gap ±0.5pp, the basis choice is load-bearing and the
  manuscript must say so wherever the decomposition is quoted.
- Expected artifact: hazard/data/expectation_benchmark_results.json.

EXECUTION BLOCKER (deliberate): PROJECTED_RUNOFF_B is None until the
projection path is transcribed from the source document by a human (or an
agent quoting the exhibit verbatim) and recorded in PROJECTION_PROVENANCE.
The spec is committed first; the transcription is an input, not a choice —
nothing else in this file may change after transcription.

Run:  cd hazard && python3 expectation_benchmark.py
      -> data/expectation_benchmark_results.json
"""
from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "expectation_benchmark_results.json"
CAP_BENCHMARK_B = 764.748          # the production cap-relative benchmark
PARITY_TOL_PP = 0.01

# ---- REQUIRED TRANSCRIPTION (see EXECUTION BLOCKER in the spec) ------------
# {"YYYY-MM" or "YYYY": projected agency-MBS runoff, $B} at the report's
# printed granularity; None until transcribed.
PROJECTED_RUNOFF_B: dict | None = None
# The report's own printed cumulative total for the transcribed horizon —
# the transcription must reproduce it exactly (gate i).
TRANSCRIPTION_TOTAL_B: float | None = None
PROJECTION_PROVENANCE: str | None = None   # document, page/exhibit, scenario


def _git_head() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True,
            cwd=Path(__file__).parent, check=True,
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    if PROJECTED_RUNOFF_B is None or TRANSCRIPTION_TOTAL_B is None:
        raise SystemExit(
            "expectation_benchmark: PROJECTED_RUNOFF_B not yet transcribed "
            "from the pinned source (see PROJECTION_PROVENANCE requirements "
            "in the spec header). The spec is committed; fill the constants "
            "with the report's printed values and rerun. Nothing else in "
            "this file may change."
        )

    t0 = time.perf_counter()
    from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

    # (i) transcription self-check
    total = float(sum(PROJECTED_RUNOFF_B.values()))
    assert abs(total - TRANSCRIPTION_TOTAL_B) < 1e-9, (
        f"transcription does not reproduce the printed total: "
        f"{total} vs {TRANSCRIPTION_TOTAL_B}"
    )

    macro = fetch_data()
    soma = fetch_soma_mbs_monthly()
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)

    # Actual runoff over the window from the same pipeline objects the
    # production benchmark uses; E-shortfall = projected − actual.
    # (Implementation reads the identical fields build_empirical_metrics
    # exposes for the cap-relative benchmark; no new constructions.)
    raise NotImplementedError(
        "actual-runoff extraction and artifact assembly are implemented "
        "in the same change that fills the transcription constants — the "
        "spec above fixes every decision they may not make."
    )


if __name__ == "__main__":
    main()
