#!/usr/bin/env python3
"""
Sensitivity sweep of the U.S.-transplant refinance-in-place channel (§20.1).

§20 anchored the U.S.-transplant refi-in-place CPR to Berger's ~1bp GE result
(≈0). This sweeps that parameter from 0 up to the partial-equilibrium reduced
form ceiling (~18%/yr, the estimate §20 rejected as over-predicting; Denmark's
own ~33%/yr opportunity hazard is an even-more-generous alternative) and reports
the institutional gap for BOTH frameworks at each point, the breakeven refi
where each gap crosses zero, and how much margin the best estimate (≈0) has.

For the ABM the refi is a flat additive Danish hazard, so the Danish CPR surface
column is transformed analytically (no rebuild). For Path B the module global is
set and the microsim Danish regime re-runs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

import abm_lockin_simulation as abm
import fed_mbs_extension_risk as fed
from common.berger_calibration import (
    LAMBDA, set_us_transplant_refi, us_transplant_refi_reduced_form,
)

MICROSIM = Path(__file__).resolve().parents[1] / "hazard" / "data" / "microsim_results.parquet"
OUT = Path(__file__).resolve().parent / "data" / "refi_sweep_results.json"

# Ceiling = the rejected PE reduced-form estimate (~18%/yr, §20). Sweep 7 points.
PE_CEILING = 0.18
SWEEP = [round(x, 3) for x in np.linspace(0.0, PE_CEILING, 7)]


def _transform_surface_refi(surface: dict, refi: float) -> dict:
    """Danish CPR' = 1−(1−move)(1−refi), applied to each cohort's z_dk grid."""
    out = {}
    for key, tup in surface.items():
        parts = list(tup)
        z_dk = parts[-1]
        parts[-1] = 100.0 * (1.0 - (1.0 - z_dk / 100.0) * (1.0 - refi))
        out[key] = tuple(parts)
    return out


def _gap_abm(df, surface, refi, soma, cohorts, abm_params) -> float:
    m = fed.export_headline_metrics(fed.compute_metrics(
        df.copy(), surface=_transform_surface_refi(surface, refi),
        soma_rolloff=soma, cohorts=cohorts, use_burnout=False,
        apply_settlement_lag_kernel=True, abm_params=abm_params))
    return m["dollars_b"]["institutional_gap"]


def _gap_pathB(df, refi, soma) -> float:
    set_us_transplant_refi(refi)
    m = fed.export_headline_metrics(fed.compute_metrics(
        df.copy(), soma_rolloff=soma, use_hazard_microsim=True,
        apply_settlement_lag_kernel=True))
    return m["dollars_b"]["institutional_gap"]


def _breakeven(xs, ys) -> float | None:
    """First x where y crosses zero (linear interpolation)."""
    for i in range(1, len(xs)):
        if ys[i - 1] == 0:
            return xs[i - 1]
        if ys[i - 1] * ys[i] < 0:
            x0, x1, y0, y1 = xs[i - 1], xs[i], ys[i - 1], ys[i]
            return x0 + (0 - y0) * (x1 - x0) / (y1 - y0)
    return None


def main() -> None:
    df = fed.fetch_data()
    soma = fed.fetch_soma_mbs_monthly()
    cohorts = fed.fetch_soma_mbs_cohorts()
    ref = abm.reference_cohort(cohorts)
    income, home_value = abm.fetch_macro_from_fred()
    scale = abm.calibrate_mobility_scale(
        income, home_value, cohort_rate=ref["coupon"],
        cohort_months=ref["months_elapsed"])
    abm_params = {"mobility_scale": scale, "median_income": income,
                  "median_home_value": home_value}
    surface = fed.load_cpr_surface()

    backup = MICROSIM.with_suffix(".sweepbackup.parquet")
    if MICROSIM.exists():
        backup.write_bytes(MICROSIM.read_bytes())

    rows = []
    try:
        for refi in SWEEP:
            g_abm = _gap_abm(df, surface, refi, soma, cohorts, abm_params)
            g_pb = _gap_pathB(df, refi, soma)
            rows.append({"refi_inplace_cpr": refi, "gap_abm_b": g_abm,
                         "gap_pathB_b": g_pb})
            print(f"  refi={refi*100:5.1f}%  gap ABM=${g_abm:+8.1f}B  "
                  f"Path B=${g_pb:+8.1f}B")
    finally:
        set_us_transplant_refi(0.0)
        if backup.exists():
            MICROSIM.write_bytes(backup.read_bytes())
            backup.unlink()

    xs = [r["refi_inplace_cpr"] for r in rows]
    be_abm = _breakeven(xs, [r["gap_abm_b"] for r in rows])
    be_pb = _breakeven(xs, [r["gap_pathB_b"] for r in rows])

    # Representative PE estimate at QT-typical market 6.5%, coupon 2.5%.
    pe_rep = float(us_transplant_refi_reduced_form(
        np.array([0.025]), 0.065, np.array([48]))[0])

    payload = {
        "sweep": rows,
        "ceiling_pe_reduced_form": PE_CEILING,
        "pe_representative_at_qt": pe_rep,
        "danish_lambda_ceiling": LAMBDA["DK"],
        "best_estimate_refi": 0.0,
        "breakeven_refi": {"abm": be_abm, "path_b": be_pb},
    }
    OUT.write_text(json.dumps(payload, indent=2))

    print("\n" + "=" * 64)
    print(" REFI-IN-PLACE SWEEP — institutional gap vs U.S.-transplant refi")
    print("=" * 64)
    print(f"  best estimate (Berger ~1bp): refi ≈ 0%")
    print(f"  PE reduced-form ceiling: {PE_CEILING*100:.0f}%  "
          f"(representative at QT ≈ {pe_rep*100:.1f}%); "
          f"Danish λ ceiling {LAMBDA['DK']*100:.0f}%")
    print(f"  breakeven (gap=0):  ABM = "
          f"{'n/a' if be_abm is None else f'{be_abm*100:.1f}%'}   "
          f"Path B = {'n/a' if be_pb is None else f'{be_pb*100:.1f}%'}")
    print(f"  Saved: {OUT}")


if __name__ == "__main__":
    main()
