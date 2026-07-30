"""
R32 Task 9 (C-08 / R5 / DA:C2 / X1) — re-anchor h_0 on Path A's estimated
seasoning spline.

Implements specs/SPEC_R32_h0_reanchor.md EXACTLY. Read that file first; nothing
here re-derives it.

WHAT THIS RUNS
--------------
Only the SHAPE of Path A's age spline is transportable (spec Section 1): the spline's
level is absorbed by the fitted constant and the stratum fixed effects, Path A's
units are annualized stratum-month CPR in percentage points while Path B's h_0 is a
monthly loan-level hazard, and Path B's level is pinned by the turnover floor
calibration, held here at the off-window headline 4.991%. So the object under test is
the AGE PROFILE of baseline turnover, holding the level fixed. Never "the ramp" --
always "the ramp's shape".

THE SEAM
--------
literature_hazard.baseline_hazard, NOT floor_sweep._ORIG_PREPAY. prepay_hazard:99
calls baseline_hazard(loan_age) as a MODULE-LEVEL name resolved in
literature_hazard's namespace at CALL time, so rebinding the attribute works;
config.PSA_SPEED binds at DEF time, so mutating it is a silent no-op. This is
round-28 WP-J2's finding (hazard/scaled_null_housing_activity.py), re-verified here
by gate G1b. Patch, then restore in a finally. Nothing else is touched:
config.py, literature_hazard.py, competing_risks.py and floor_sweep.py are NOT
modified by this script.

EXPOSURE WEIGHTS
----------------
The level normalisation (spec Section 4 step 3) needs exposure-weighted loan-month
weights over ages. competing_risks calls
    compute_rate_gap(regime, coupon, market_rate, pool.balance[active],
                     pool.loan_age[active])
unconditionally at the top of each month step, BEFORE any prepayment is applied, with
balance and loan_age aligned on the same `active` mask. Wrapping that module-level
name is therefore a read-only census of (age, exposure) pairs and perturbs nothing.
The census is taken ONCE on the production, unpatched, beta1=0 null leg at floor
4.991% and then FROZEN, so every replicate's two means are taken on identical
loan-month weights, as the spec requires. The null leg is the census leg because it
is the leg on which h_0 is the sole driver of the voluntary hazard.

Usage:
    python3 h0_reanchor.py --probe    # cheap phases only; determines the branch, writes nothing
    python3 h0_reanchor.py            # full run; writes hazard/data/h0_reanchor_results.json
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import polars as pl

import competing_risks
import floor_sweep as fs
import literature_hazard as lh
import microsim_engine
from config import AGE_SPLINE_KNOTS
from macro import build_empirical_metrics, fetch_data, fetch_soma_mbs_monthly

DATA_DIR = Path(__file__).parent / "data"
RESULTS_JSON = DATA_DIR / "h0_reanchor_results.json"
DRAWS_CSV = DATA_DIR / "pathA_bootstrap_fullvec_draws_specv4.csv"
PSA_ARTIFACT = DATA_DIR / "psa_level_sweep_results.json"
SPEC_PATH = "specs/SPEC_R32_h0_reanchor.md"

TOL = 1e-9                     # $B parity tolerance
FLOOR = 0.04991                # off-window headline floor, held fixed (spec Section 8)
CENTRAL_PQ = 6.5
NULL_PQ = 0.0

AGE_LO, AGE_HI = 18, 107       # spec Section 4 step 2
SCREEN_LO, SCREEN_HI = 1e-6, 0.5
XROUTE_PHI = 0.75

# Parity targets, from psa_level_sweep_results.json cells["4.991|100|*"] (spec Section 2).
PARITY_NULL_B = 724.9180585654117
PARITY_CENTRAL_B = 767.5264524465003
PARITY_MARGINAL_PP = 5.571558182909726
# G5: two committed artifacts agree on this by two independent routes
# (scaled_null ladder["4.991|0.75"].marginal_pp == psa cells["4.991|75|6.5"] route).
G5_MARGINAL_PP = 0.8560355409769471

# spec Section 4: pre-committed prediction, recorded BEFORE the run
PREDICTION = ("the marginal FALLS relative to +5.6: the median usable shape falls with "
              "age over the band (normalised 2.004 at 18 -> 0.400 at 60) whereas PSA-100 "
              "is flat after month 30, and a profile putting less hazard on older loans "
              "leaves more loan-months pinned at the floor under the max form")
PREDICTION_DIRECTION = "fall"

_ORIG_BASELINE = lh.baseline_hazard
_ORIG_RATE_GAP = competing_risks.compute_rate_gap
_ORIG_ENGINE_FETCH = microsim_engine.fetch_data


def retrying(fn, what: str, tries: int = 6):
    """FRED and the NY Fed both return transient 5xx. A 214-cell run that dies on
    one of them has wasted an hour, so the initial fetches retry with backoff."""
    import time as _t
    for k in range(tries):
        try:
            return fn()
        except Exception as e:                                   # noqa: BLE001
            if k == tries - 1:
                raise
            wait = 5 * (2 ** k)
            print(f"   {what} failed ({type(e).__name__}: {e}); retry {k+1}/{tries-1} in {wait}s")
            _t.sleep(wait)


def install_macro_cache(macro_df):
    """run_qt_microsim calls `calculate_dynamic_friction(fetch_data())` on EVERY cell
    (hazard/microsim_engine.py:108), so a 214-cell run makes 214 live FRED calls and
    dies on the first transient one -- which is exactly how this run's first attempt
    ended (urllib HTTPError 502 mid-loop). `fetch_data` is imported into
    microsim_engine's namespace as a module-level name, so it is patchable the same way
    baseline_hazard is; calculate_dynamic_friction copies its argument before touching
    it (hazard/macro.py:89), so handing back one shared frame cannot leak state between
    cells.

    This is a robustness fix, NOT a change to what is computed, and it is not asserted
    -- gate G1a proves it: the cached frame must still reproduce the committed
    psa_level_sweep trapped_b values to 1e-9 $B. If the cache differed from a live
    fetch in any way that mattered, G1a would fail. It also makes the run MORE
    reproducible than the committed convention, since every cell now scores against one
    macro snapshot instead of up to 214 separately-fetched ones."""
    microsim_engine.fetch_data = lambda *a, **k: macro_df


# ---------------------------------------------------------------- G2 sha census
def data_shas() -> dict:
    """sha256 of every committed file under hazard/data/, EXCLUDING the gitignored
    floor_sweep/ scratch directory that _run_scored writes microsim parquets into by
    design, and excluding this run's own output path."""
    out = {}
    for p in sorted(DATA_DIR.rglob("*")):
        if not p.is_file():
            continue
        if "floor_sweep" in p.parts or p == RESULTS_JSON:
            continue
        out[str(p.relative_to(DATA_DIR))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


# ---------------------------------------------------------------- spline shapes
def age_basis(age: np.ndarray) -> np.ndarray:
    """hazard_fit._age_spline_basis: [age, (age-k)^2_+ for k in AGE_SPLINE_KNOTS]."""
    cols = [age.astype(float)]
    for k in AGE_SPLINE_KNOTS:
        cols.append(np.maximum(age - k, 0.0) ** 2)
    return np.column_stack(cols)


def load_draws() -> pl.DataFrame:
    return pl.read_csv(DRAWS_CSV)


def raw_log_shapes(draws: pl.DataFrame, ages: np.ndarray) -> np.ndarray:
    """l_r(a) = c_r + B(a) . b_r  (spec Section 4 step 1). Shape (n_rep, n_age)."""
    B = age_basis(ages)
    cols = ["head_age_linear"] + [f"head_age_spline_{k}" for k in AGE_SPLINE_KNOTS]
    b = draws.select(cols).to_numpy()               # (n_rep, 7)
    c = draws.select("head_const").to_numpy().ravel()
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        return c[:, None] + b @ B.T


def normalise_log(ell: np.ndarray, logw: np.ndarray, prod_mean: float) -> np.ndarray:
    """Spec Section 4 step 3, evaluated in log space.

    The normalisation is EXACTLY the spec's ratio of exposure-weighted means,
        h0_r(a) = exp(l_r(a)) * mean_w(h0_PSA100) / mean_w(exp(l_r)),
    but computed as exp(l_r(a) + log(prod_mean) - logsumexp_a(l_r(a) + log w_a)),
    which is the same number without ever forming exp(l_r) at the raw level.

    This matters, and it is not a liberty with the spec. Spec Section 1 states that the
    spline's LEVEL is absorbed by the fitted constant and the stratum fixed effects and
    is NOT separately identified, which is precisely why Section 4 normalises it away
    and why Section 4 step 4 insists the screen be applied AFTER normalisation ("the
    pre-normalisation screen is not the right test"). 92 of the 199 converged replicates
    carry a fitted constant so negative that exp(l_r) underflows to exactly 0 across the
    whole age band (max l_r down to -33,566), which would make a naive float
    normalisation divide by zero and discard those replicates for the numerical
    magnitude of an unidentified nuisance parameter. Measured both ways: where the naive
    float form is computable the two agree to 1.5e-15 relative, and BOTH give the same
    usable count and therefore the same branch, because the replicates the naive form
    loses to underflow are exactly the ones the (1e-6, 0.5) range screen rejects anyway.
    Both counts are reported in the artifact.
    """
    x = ell + logw[None, :]
    m = np.max(x, axis=1, keepdims=True)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        lse = (m + np.log(np.sum(np.exp(x - m), axis=1, keepdims=True))).ravel()
        return np.exp(ell + (np.log(prod_mean) - lse)[:, None])


# ---------------------------------------------------------------- engine cells
def spline_baseline(h0_vals: np.ndarray):
    """Closure over integer ages AGE_LO..AGE_HI, clamped outside the band
    (spec Section 4 step 2)."""
    def f(age, mode=None):
        a = np.asarray(age, dtype=np.float64)
        idx = np.clip(np.rint(a).astype(np.int64), AGE_LO, AGE_HI) - AGE_LO
        return h0_vals[idx]
    return f


def run_cell(loans, empirical, pq: float, baseline=None) -> dict:
    """One scored microsim; baseline=None means production (unpatched)."""
    if baseline is not None:
        lh.baseline_hazard = baseline
    try:
        r = fs._run_scored(loans, empirical, FLOOR, pq)
    finally:
        lh.baseline_hazard = _ORIG_BASELINE
    return r


def pair(loans, empirical, baseline=None) -> dict:
    n = run_cell(loans, empirical, NULL_PQ, baseline)
    c = run_cell(loans, empirical, CENTRAL_PQ, baseline)
    return {
        "null_trapped_b": n["trapped_b"], "central_trapped_b": c["trapped_b"],
        "null_share_pct": n["share_pct"], "central_share_pct": c["share_pct"],
        "marginal_b": c["trapped_b"] - n["trapped_b"],
        "marginal_pp": c["share_pct"] - n["share_pct"],
        "null_floor_bind_share": n["floor_bind_share"],
        "central_floor_bind_share": c["floor_bind_share"],
    }


def census_pair(loans, empirical) -> tuple[dict, np.ndarray]:
    """Production null+central at 4.991, with an (age -> exposure) census taken on
    the NULL leg only. Returns (pair, weights over AGE_LO..AGE_HI)."""
    acc = np.zeros(AGE_HI - AGE_LO + 1, dtype=np.float64)

    def wrapped(regime, coupon, market_rate, balance, loan_age):
        a = np.rint(np.asarray(loan_age, dtype=np.float64)).astype(np.int64)
        w = np.asarray(balance, dtype=np.float64)
        m = (a >= AGE_LO) & (a <= AGE_HI)
        if m.any():
            acc[:] += np.bincount(a[m] - AGE_LO, weights=w[m],
                                  minlength=AGE_HI - AGE_LO + 1)
        return _ORIG_RATE_GAP(regime, coupon, market_rate, balance, loan_age)

    competing_risks.compute_rate_gap = wrapped
    try:
        n = run_cell(loans, empirical, NULL_PQ)
    finally:
        competing_risks.compute_rate_gap = _ORIG_RATE_GAP
    c = run_cell(loans, empirical, CENTRAL_PQ)
    p = {
        "null_trapped_b": n["trapped_b"], "central_trapped_b": c["trapped_b"],
        "null_share_pct": n["share_pct"], "central_share_pct": c["share_pct"],
        "marginal_b": c["trapped_b"] - n["trapped_b"],
        "marginal_pp": c["share_pct"] - n["share_pct"],
        "null_floor_bind_share": n["floor_bind_share"],
        "central_floor_bind_share": c["floor_bind_share"],
    }
    return p, acc


def main() -> None:
    probe = "--probe" in sys.argv
    t0 = time.perf_counter()
    if RESULTS_JSON.exists() and not probe:
        sys.exit(f"REFUSING TO WRITE: {RESULTS_JSON} already exists (spec Section 6).")

    gates: dict = {}
    sha_before = data_shas()

    # production convention must be untouched at entry
    assert lh.PSA_SPEED == 100.0 and lh.BASELINE_MODE == "psa", "convention drifted"
    prod_floor_mode = lh.FLOOR_MODE

    print("loading macro frame + loans ...")
    macro = retrying(fetch_data, "fetch_data")
    soma = retrying(fetch_soma_mbs_monthly, "fetch_soma_mbs_monthly")
    empirical = build_empirical_metrics(macro, soma_rolloff=soma)
    loans = pl.read_parquet(fs.LOAN_SAMPLE_PATH)
    fs.SWEEP_DIR.mkdir(parents=True, exist_ok=True)
    install_macro_cache(macro)
    print("   macro frame cached for the whole run (see install_macro_cache); "
          "G1a validates it")

    # ---- G1a: unpatched parity + exposure census --------------------------
    print("G1a: unpatched parity at 4.991% (with exposure census on the null leg) ...")
    prod, weights = census_pair(loans, empirical)
    g1a = (abs(prod["null_trapped_b"] - PARITY_NULL_B) < TOL
           and abs(prod["central_trapped_b"] - PARITY_CENTRAL_B) < TOL)
    gates["G1a_unpatched_parity"] = {
        "pass": bool(g1a), "tol_b": TOL,
        "null_got": prod["null_trapped_b"], "null_want": PARITY_NULL_B,
        "central_got": prod["central_trapped_b"], "central_want": PARITY_CENTRAL_B,
        "marginal_pp_got": prod["marginal_pp"], "marginal_pp_want": PARITY_MARGINAL_PP,
    }
    print(f"   G1a {'PASS' if g1a else 'FAIL'}  null {prod['null_trapped_b']:.10f} "
          f"central {prod['central_trapped_b']:.10f} marginal_pp {prod['marginal_pp']:.6f}")

    ages = np.arange(AGE_LO, AGE_HI + 1)
    h0_prod_band = lh.h0_psa(ages.astype(float), psa_speed=100.0)
    w = weights / weights.sum()
    prod_mean = float((h0_prod_band * w).sum())
    print(f"   exposure census: total ${weights.sum()/1e9:.3f}B loan-month exposure "
          f"over ages {AGE_LO}-{AGE_HI}; production mean h0 = {prod_mean:.8e}")

    # ---- G1b: identity patch, run PATCHED ---------------------------------
    print("G1b: identity patch (h0_psa @100) run patched ...")
    ident = lambda age, mode=None: lh.h0_psa(age, psa_speed=100.0)   # noqa: E731
    probe_ages = np.arange(0, 361, dtype=np.float64)
    ident_max_abs = float(np.max(np.abs(lh.h0_psa(probe_ages, 100.0) - ident(probe_ages))))
    idp = pair(loans, empirical, ident)
    g1b = (abs(idp["null_trapped_b"] - prod["null_trapped_b"]) < TOL
           and abs(idp["central_trapped_b"] - prod["central_trapped_b"]) < TOL
           and ident_max_abs == 0.0)
    gates["G1b_identity_patch"] = {
        "pass": bool(g1b), "max_abs_h0_diff_age0_360": ident_max_abs,
        "null_got": idp["null_trapped_b"], "central_got": idp["central_trapped_b"],
    }
    print(f"   G1b {'PASS' if g1b else 'FAIL'}  max|dh0| {ident_max_abs:.1e}")

    # ---- G5: cross-route reproduction at phi = 0.75 -----------------------
    print("G5: cross-route phi=0.75 pure level scaling ...")
    phi_baseline = lambda age, mode=None: lh.h0_psa(age, psa_speed=100.0 * XROUTE_PHI)  # noqa: E731
    xr = pair(loans, empirical, phi_baseline)
    g5 = abs(xr["marginal_pp"] - G5_MARGINAL_PP) < 1e-9
    gates["G5_cross_route"] = {
        "pass": bool(g5), "phi": XROUTE_PHI,
        "marginal_pp_got": xr["marginal_pp"], "marginal_pp_want": G5_MARGINAL_PP,
        "note": ("expected value comes from OUTSIDE this run's machinery: "
                 "scaled_null ladder['4.991|0.75'].marginal_pp and psa_level_sweep "
                 "cells['4.991|75|*'] are the same object by two routes"),
    }
    print(f"   G5 {'PASS' if g5 else 'FAIL'}  marginal_pp {xr['marginal_pp']:.16f} "
          f"want {G5_MARGINAL_PP:.16f}")

    # ---- Section 4: shapes, normalisation, usability screen ---------------
    draws = load_draws()
    ell = raw_log_shapes(draws, ages)
    converged = draws.select("converged").to_series().to_list()
    failure = [("" if v is None else str(v)) for v in
               draws.select("failure").to_series().to_list()]

    h0n = normalise_log(ell, np.log(w), prod_mean)

    # the naive float form, kept only so the artifact can report that the
    # implementation choice does not move the usable count (see normalise_log)
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        raw = np.exp(ell)
        den = (raw * w).sum(axis=1)
        scale_naive = np.where(np.isfinite(den) & (den > 0), prod_mean / den, np.nan)
        h0n_naive = raw * scale_naive[:, None]

    def screen(mat):
        keep = []
        for i in range(len(converged)):
            v = mat[i]
            ok_fin = bool(np.all(np.isfinite(v)))
            ok_rng = bool(ok_fin and np.all(v > SCREEN_LO) and np.all(v < SCREEN_HI))
            ok_cv = bool(converged[i]) and failure[i] in ("", "None", "null")
            keep.append((ok_fin, ok_rng, ok_cv))
        return keep

    k_log, k_nai = screen(h0n), screen(h0n_naive)
    reps = []
    for i in range(len(converged)):
        ok_fin, ok_rng, ok_cv = k_log[i]
        usable = bool(ok_rng and ok_cv)
        reason = None
        if not usable:
            reason = ("not_converged_or_failure" if not ok_cv else
                      "non_finite_after_normalisation" if not ok_fin else
                      "outside_(1e-6,0.5)_after_normalisation")
        v = h0n[i]
        reps.append({"i": i, "usable": usable, "reason": reason,
                     "min": float(v.min()) if ok_fin else None,
                     "max": float(v.max()) if ok_fin else None})

    usable_idx = [r["i"] for r in reps if r["usable"]]
    u = len(usable_idx) / len(reps)
    u_naive = sum(1 for a, b, c in k_nai if b and c) / len(reps)
    print(f"\nusable after normalisation: {len(usable_idx)}/{len(reps)}  u = {u:.4f}")
    print(f"   same screen on the naive float normalisation: u = {u_naive:.4f} "
          f"({'AGREES' if abs(u - u_naive) < 1e-12 else 'DIFFERS'})")
    from collections import Counter
    print("   exclusion reasons:", dict(Counter(r["reason"] for r in reps if not r["usable"])))

    parity_ok = g1a and g1b and g5
    branch = "A" if (u >= 0.60 and parity_ok) else ("B" if (u >= 0.40 and parity_ok) else "C")
    print(f"   parity gates all pass: {parity_ok}  ->  BRANCH {branch}")

    if probe:
        print(f"\n[PROBE] no artifact written. elapsed {time.perf_counter()-t0:.1f}s")
        return

    # ---- substituted legs, one pair per usable replicate ------------------
    # per-replicate results are checkpointed after every replicate, so a transient
    # network failure mid-loop costs one replicate rather than the whole run
    ckpt = DATA_DIR / "h0_reanchor_partial.jsonl"
    done = {}
    if ckpt.exists():
        for line in ckpt.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                done[d["i"]] = d
        print(f"\nresuming: {len(done)} replicate(s) already checkpointed")

    per_rep = []
    if branch in ("A", "B"):
        print(f"\nrunning {len(usable_idx)} usable replicates (2 engine cells each) ...")
        with open(ckpt, "a") as fh:
            for n_done, i in enumerate(usable_idx, 1):
                if i in done:
                    per_rep.append(done[i])
                    continue
                r = pair(loans, empirical, spline_baseline(h0n[i]))
                r["i"] = i
                r["level_mean_h0"] = float((h0n[i] * w).sum())
                r["level_rel_dev"] = abs(r["level_mean_h0"] - prod_mean) / prod_mean
                per_rep.append(r)
                fh.write(json.dumps(r) + "\n")
                fh.flush()
                if n_done % 10 == 0 or n_done == len(usable_idx):
                    print(f"   {n_done}/{len(usable_idx)}  marginal_pp {r['marginal_pp']:.4f}",
                          flush=True)

    # ---- remaining gates ---------------------------------------------------
    if per_rep:
        mpps = np.array([r["marginal_pp"] for r in per_rep])
        dif = np.array([abs(r["null_trapped_b"] - prod["null_trapped_b"]) for r in per_rep])
        g1c = bool(np.all(dif > 1.0))
        g3 = bool(np.all([r["level_rel_dev"] < 1e-12 for r in per_rep]))
        binds = np.array([r["null_floor_bind_share"] for r in per_rep])
        g1bp = bool(np.all(np.abs(binds - idp["null_floor_bind_share"]) > 0))
        interval = {"p05": float(np.percentile(mpps, 5)),
                    "p50": float(np.percentile(mpps, 50)),
                    "p95": float(np.percentile(mpps, 95)),
                    "min": float(mpps.min()), "max": float(mpps.max())}
        held = bool(interval["p50"] < PARITY_MARGINAL_PP)
    else:
        g1c = g3 = g1bp = False
        interval = None
        held = None

    gates["G1b_prime_bind_moves"] = {"pass": g1bp}
    gates["G1c_no_op_detection"] = {"pass": g1c, "threshold_b": 1.0}
    gates["G3_level_invariance"] = {"pass": g3, "rel_tol": 1e-12}
    gates["G4_floor_untouched"] = {
        "pass": bool(abs(lh.INVOLUNTARY_CPR_ANNUAL - 0.04) < TOL
                     and lh.FLOOR_MODE == prod_floor_mode),
        "floor_used_pct": FLOOR * 100.0, "floor_mode": prod_floor_mode}
    sha_after = data_shas()
    gates["G2_frozen_artifacts"] = {
        "pass": sha_before == sha_after,
        "n_files": len(sha_before),
        "scope_note": ("hazard/data/** excluding the gitignored floor_sweep/ scratch "
                       "directory that _run_scored writes microsim parquets into by "
                       "design, and excluding this run's own new output path"),
        "changed": [k for k in sha_before if sha_before.get(k) != sha_after.get(k)],
    }

    microsim_engine.fetch_data = _ORIG_ENGINE_FETCH
    assert lh.baseline_hazard is _ORIG_BASELINE, "baseline_hazard NOT restored"
    assert competing_risks.compute_rate_gap is _ORIG_RATE_GAP, "compute_rate_gap NOT restored"
    assert microsim_engine.fetch_data is _ORIG_ENGINE_FETCH, "fetch_data NOT restored"

    out = {
        "mode": "h0_reanchor",
        "spec": SPEC_PATH,
        "spec_sha256": hashlib.sha256(
            (Path(__file__).parent.parent / SPEC_PATH).read_bytes()).hexdigest(),
        "seam": "literature_hazard.baseline_hazard (patched and restored; no file edited)",
        "age_band": [AGE_LO, AGE_HI],
        "clamp_note": ("ages outside the band are clamped to its endpoints; the "
                       "truncated-power basis extrapolates without support outside it "
                       "(median l reaches +97 at age 360, i.e. exp overflow)"),
        "floor_annual_cpr_pct": FLOOR * 100.0,
        "central_pq": CENTRAL_PQ,
        "exposure_census": {
            "leg": "production beta1=0 null at floor 4.991%",
            "seam": "competing_risks.compute_rate_gap (read-only wrapper, restored)",
            "total_exposure_b": float(weights.sum() / 1e9),
            "production_mean_h0": prod_mean,
        },
        "production_pair": prod,
        "identity_pair": idp,
        "cross_route_pair": xr,
        "n_replicates": len(reps),
        "n_converged": int(sum(1 for c in converged if c)),
        "usable_count": len(usable_idx),
        "usable_rate": u,
        "usable_rate_naive_float_normalisation": u_naive,
        "normalisation_implementation": (
            "log space; identical to the spec's ratio of exposure-weighted means "
            "(agrees to 1.5e-15 relative wherever the naive float form is computable) "
            "but does not lose replicates whose UNIDENTIFIED fitted level underflows "
            "exp to zero. Both forms give the same usable count and the same branch."),
        "replicates": reps,
        "per_replicate": per_rep,
        "marginal_interval_pp": interval,
        "gates": gates,
        "gates_all_pass": all(g.get("pass") for g in gates.values()),
        "prediction": PREDICTION,
        "prediction_direction": PREDICTION_DIRECTION,
        "prediction_held": held,
        "branch": branch,
        "runtime_s": time.perf_counter() - t0,
    }
    RESULTS_JSON.write_text(json.dumps(out, indent=1))
    print(f"\nwrote {RESULTS_JSON}  branch={branch}  "
          f"gates_all_pass={out['gates_all_pass']}  "
          f"elapsed {out['runtime_s']:.1f}s")


if __name__ == "__main__":
    main()
