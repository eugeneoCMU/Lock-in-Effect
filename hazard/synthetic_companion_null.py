#!/usr/bin/env python3
"""
Mechanism-removed null leg for the symmetric companion test.
(Pre-committed; spec fixed in this header before any run executed.)

WHAT THIS MODULE IS FOR. synthetic_companion.py runs Path B on an
independently-calibrated synthetic population and recovers 105.966% of the
benchmark, against 107.0% on the real Freddie book. revised_paper_v17.tex
(sec:robustness-synthesis) reads that near-equality as "substantially
strengthening" the aggregate-level paradigm claim: the loan-level survival
structure reaches a comparable aggregate recovery with no real covariates at
all.

The exhibit has no mechanism-removed leg. Everywhere else in this paper a
recovery LEVEL is explicitly disclaimed as floor-dominated and uninformative —
the beta1 = 0 null already recovers 88.7% of the benchmark on the real book,
which is exactly why the paper identifies the MARGINAL and not the level
(sec:identification). The companion test is the one place a recovery level is
still being read as evidence, and the reason is that nobody ran its null. This
module runs it.

The 106.0% is a level. If the beta1 = 0 leg on the SAME synthetic population
recovers nearly as much, then the companion test's evidential content is the
DIFFERENTIAL between the two legs, not the level, and the manuscript's
"substantially strengthened" language is claiming more than the exhibit
supports. Whichever way it falls is reported verbatim.

SPEC (fixed ex ante)
====================

- POPULATION: synthetic_population.build_synthetic_population(
  calibration="baseline") — the identical call synthetic_companion.py makes
  for its headline cell. Both legs below are run on the SAME population
  object, built once, so the two legs cannot differ through the draw.

- CENTRAL LEG: microsim_engine.run_qt_microsim(loan_sample=pop, macro=macro,
  regimes=("US",), p_q_shock_pct=6.5). 6.5 is
  config.ROTHSTEIN_Q_DECLINE_MID * 100, i.e. the engine's own default, so the
  central leg is the committed configuration written out explicitly rather
  than inherited.

- NULL LEG: the SAME call with p_q_shock_pct = 0.0 and NOTHING else changed.
  literature_hazard.rothstein_beta1(0.0) == 0.0 is asserted before either leg
  runs, so "p_q_shock_pct = 0" is verified to mean "beta1 = 0 exactly" and not
  merely "beta1 small". The two legs differ in beta1 and in no other argument;
  this is enforced by construction, both legs going through one call site with
  a single varying parameter.

- SCORING: extension_risk.score_extension_risk against the same empirical
  metrics frame (macro.build_empirical_metrics with SOMA roll-off), the same
  standalone scorer the committed companion run uses. Reported per leg:
  hazard_trapped_b, share_explained_pct, and the lag-0 CPR correlation.

- PARITY GATE (HARD; asserted BEFORE the differential is read; on failure the
  run STOPS and writes a GATE_FAILURE payload rather than reinterpreting
  anything): the central leg must reproduce the committed
  data/synthetic_companion_results.json cell
  two_by_two.hazard_synthetic_pathB BIT-EXACTLY — trapped_b
  810.3754477878556 and share_pct 105.96630255419079, exact float equality,
  not a tolerance. This module drives the engine through its own call site
  rather than synthetic_companion's `_score_pathB` wrapper, so anything less
  than bit-exactness means the re-wiring changed the object under study and
  the null below is about a different simulation.

- REPORTED DIFFERENTIAL (fixed ex ante):
      marginal_pp = central.share_pct - null.share_pct
      marginal_b  = central.trapped_b - null.trapped_b
      null_share_of_central_pct = null.share_pct / central.share_pct * 100

- VERDICT LANGUAGE (pre-committed, covers both outcomes). Threshold
  MATERIAL_DIFFERENTIAL_PP = 25.0 points, set by the paper's own precedent:
  the real-book null recovers 88.7% against the central's 107.0%, an 18.3-point
  differential that the paper ALREADY treats as too small to license a
  level-based reading (sec:identification demotes the level for exactly this
  reason). A companion-test differential at or below that order of magnitude
  therefore cannot license one either. 25.0 is set above the real-book 18.3 so
  the threshold is not tuned to pass.
    "level_reading_unsupported"  if marginal_pp <= MATERIAL_DIFFERENTIAL_PP —
        the null recovers most of what the central leg does on the same
        synthetic population, so the 106.0% is a floor-dominated level like
        every other level in this paper; the companion test's content is the
        differential, and language crediting the LEVEL with strengthening the
        paradigm claim overstates the exhibit.
    "level_reading_supported"    if marginal_pp > MATERIAL_DIFFERENTIAL_PP —
        the synthetic recovery is mechanism-driven rather than floor-driven
        and the existing reading stands.
  Both branches are pre-written; whichever the data selects is reported
  verbatim.

Output
------
data/synthetic_companion_null_results.json: spec echo, parity gate block, both
legs, the differential, and the pre-committed verdict.

Run:  cd hazard && python3 synthetic_companion_null.py
Runtime estimate: 2 engine legs on the synthetic population, ~1 min.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from config import ROTHSTEIN_Q_DECLINE_MID, SIM_RESULTS_PATH
from extension_risk import score_extension_risk
from literature_hazard import rothstein_beta1
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly
from microsim_engine import run_qt_microsim
from synthetic_population import build_synthetic_population

DATA_DIR = SIM_RESULTS_PATH.parent
RESULTS_JSON = DATA_DIR / "synthetic_companion_null_results.json"
COMMITTED_JSON = DATA_DIR / "synthetic_companion_results.json"

CENTRAL_SHOCK_PCT = ROTHSTEIN_Q_DECLINE_MID * 100.0  # 6.5, the engine default
NULL_SHOCK_PCT = 0.0
MATERIAL_DIFFERENTIAL_PP = 25.0

FLOORSWEEP_JSON = DATA_DIR / "floor_sweep_results.json"
OOSIDENT_JSON = DATA_DIR / "oos_identification_results.json"


def _real_book_reference() -> dict:
    """The real-book central-minus-null gap the manuscript quotes as precedent.

    This was previously three hardcoded literals, and they were wrong in a way
    hardcoding is exactly how you get: the 107.0% central leg is the STANDALONE
    scorer's share and the 88.7% null is the SHARED-basis share, so their 18.3pp
    difference differenced two different accounting bases and corresponded to no
    quantity at all. Both legs are now read from one artifact on one basis, so
    the gap cannot silently cross bases again. The gap is basis-invariant (the
    shared layer's netting is common to both legs), but it is NOT floor-
    invariant, so both calibrations are reported.
    """
    rows = json.loads(FLOORSWEEP_JSON.read_text())["rows"]
    r4 = next(r for r in rows if r["floor_annual_cpr_pct"] == 4.0)
    central = float(r4["central"]["share_pct"])
    null = float(r4["null"]["share_pct"])
    oos = json.loads(OOSIDENT_JSON.read_text())["instrument1_marginal_table"]
    head = next(t for t in oos if abs(t["floor_annual_cpr_pct"] - 4.991) < 1e-6)
    return {
        "note": ("the paper's own precedent for demoting a recovery level: on the real "
                 "Freddie book the central leg and the beta1=0 null differ by the gap "
                 "below, already treated as too small to license a level-based reading "
                 "(sec:identification). BOTH legs are the standalone scorer's shares "
                 "from floor_sweep_results.json, i.e. ONE basis; an earlier version of "
                 "this block differenced a standalone central against a shared null and "
                 "reported a spurious 18.3pp."),
        "basis": "standalone scorer (extension_risk.score_extension_risk), both legs",
        "source": "data/floor_sweep_results.json rows[floor=4.0]",
        "calibration": "in-sample calibration point, 4.0% in-window involuntary floor",
        "central_share_pct": central,
        "null_share_pct": null,
        "differential_pp": central - null,
        "off_window_floor_pct": float(head["floor_annual_cpr_pct"]),
        "off_window_differential_pp": float(head["band"]["6.5"]["marginal_pp"]),
        "off_window_source": "data/oos_identification_results.json "
                             "instrument1_marginal_table[4.991].band['6.5'].marginal_pp",
        "superseded_cross_basis_differential_pp": 18.3,
    }


def _leg(pop, macro, empirical, tag: str, shock_pct: float) -> dict:
    """One Path B leg. The ONLY varying argument is p_q_shock_pct."""
    tmp = DATA_DIR / f"_synth_null_{tag}.parquet"
    try:
        paths = run_qt_microsim(loan_sample=pop, macro=macro, regimes=("US",),
                                output=tmp, p_q_shock_pct=shock_pct)
        res = score_extension_risk(paths["US"], empirical)
    finally:
        if tmp.exists():
            tmp.unlink()
    return {
        "p_q_shock_pct": shock_pct,
        "beta1": rothstein_beta1(shock_pct / 100.0),
        "trapped_b": float(res["hazard_trapped_b"]),
        "share_pct": float(res["share_explained_pct"]),
        "cpr_r_lag0": float(res["cross_correlation"].get(0)),
    }


def main() -> None:
    t0 = time.perf_counter()

    # "p_q_shock_pct = 0" must mean "beta1 = 0 exactly", not "beta1 small".
    assert rothstein_beta1(NULL_SHOCK_PCT / 100.0) == 0.0, \
        "null leg does not zero beta1 exactly"

    committed = json.loads(COMMITTED_JSON.read_text())
    c_cell = committed["two_by_two"]["hazard_synthetic_pathB"]
    c_trapped = float(c_cell["trapped_b"])
    c_share = float(c_cell["share_pct"])

    print("Building macro/empirical frames and synthetic population …")
    macro = fetch_data()
    empirical = build_empirical_metrics(fetch_data(), soma_rolloff=fetch_soma_mbs_monthly())
    pop = build_synthetic_population(calibration="baseline")

    print(f"Central leg (p_q_shock_pct={CENTRAL_SHOCK_PCT}) …")
    central = _leg(pop, macro, empirical, "central", CENTRAL_SHOCK_PCT)

    trapped_exact = (central["trapped_b"] == c_trapped)
    share_exact = (central["share_pct"] == c_share)
    parity_pass = trapped_exact and share_exact
    print(f"  trapped {central['trapped_b']:.12f}  committed {c_trapped:.12f}  "
          f"diff {abs(central['trapped_b']-c_trapped):.3e}  "
          f"{'EXACT' if trapped_exact else 'MISMATCH'}")
    print(f"  share   {central['share_pct']:.12f}  committed {c_share:.12f}  "
          f"diff {abs(central['share_pct']-c_share):.3e}  "
          f"{'EXACT' if share_exact else 'MISMATCH'}")

    parity = {
        "rule": ("exact float equality against data/synthetic_companion_results.json "
                 "two_by_two.hazard_synthetic_pathB"),
        "central_trapped_b": central["trapped_b"],
        "committed_trapped_b": c_trapped,
        "abs_diff_trapped_b": abs(central["trapped_b"] - c_trapped),
        "central_share_pct": central["share_pct"],
        "committed_share_pct": c_share,
        "abs_diff_share_pct": abs(central["share_pct"] - c_share),
        "bit_exact": parity_pass,
        "pass": parity_pass,
    }

    if not parity_pass:
        RESULTS_JSON.write_text(json.dumps({
            "mode": "synthetic_companion_null", "status": "GATE_FAILURE",
            "parity": parity, "central": central,
        }, indent=2, default=float) + "\n")
        raise SystemExit("Parity gate failure — null leg not run.")

    print(f"Null leg (p_q_shock_pct={NULL_SHOCK_PCT}, beta1=0) …")
    null = _leg(pop, macro, empirical, "null", NULL_SHOCK_PCT)
    print(f"  trapped {null['trapped_b']:.6f} B  share {null['share_pct']:.6f}%")

    marginal_pp = central["share_pct"] - null["share_pct"]
    marginal_b = central["trapped_b"] - null["trapped_b"]
    null_share_of_central = null["share_pct"] / central["share_pct"] * 100

    verdict = ("level_reading_supported" if marginal_pp > MATERIAL_DIFFERENTIAL_PP
               else "level_reading_unsupported")

    payload = {
        "mode": "synthetic_companion_null",
        "null_for": ("synthetic_companion.py / data/synthetic_companion_results.json "
                     "two_by_two.hazard_synthetic_pathB (revised_paper_v17.tex "
                     "sec:robustness-synthesis)"),
        "spec": (f"same baseline synthetic population, both legs through one call site; "
                 f"central p_q_shock_pct={CENTRAL_SHOCK_PCT} vs null "
                 f"p_q_shock_pct={NULL_SHOCK_PCT} (beta1=0 exactly, asserted); "
                 f"nothing else differs"),
        "engine": ("microsim_engine.run_qt_microsim, US regime, synthetic baseline "
                   "population; standalone scorer extension_risk.score_extension_risk"),
        "parity_gate": parity,
        "central": central,
        "null_beta1_0": null,
        "differential": {
            "marginal_pp": marginal_pp,
            "marginal_b": marginal_b,
            "null_share_of_central_pct": null_share_of_central,
        },
        "real_book_reference": _real_book_reference(),
        "material_differential_threshold_pp": MATERIAL_DIFFERENTIAL_PP,
        "verdict": verdict,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    RESULTS_JSON.write_text(json.dumps(payload, indent=2, default=float) + "\n")
    print(f"\ncentral {central['share_pct']:.3f}%  null {null['share_pct']:.3f}%  "
          f"differential {marginal_pp:+.3f} pp / {marginal_b:+.3f} B")
    print(f"verdict: {verdict}")
    print(f"Results saved to {RESULTS_JSON}")


if __name__ == "__main__":
    main()
