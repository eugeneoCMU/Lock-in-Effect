#!/usr/bin/env python3
"""V20-C: few-cluster coverage simulation for the floor-read inference ladder
(run tag: fewcluster_coverage).

Spec: specs/SPEC_V20_C_fewcluster_coverage_2026-08-04.md (see amendment V20-C-A1) —
adopted and committed before this script; this script committed before it ran.
Guarded-runner pattern: pinned committed inputs, single JSON output, abort gates.

DESIGN (per spec + A1). Monte Carlo calibrated to the binding R2 read's committed
design: G = 31 clusters with the COMMITTED leverage profile (v2 artifact
leverages_h; intercept-only weighted mean, so h_g are the exposure weights), truth
scale set to the committed CR1 SE (the oracle's known variance), Gaussian and
t5 heavy-tail cells, S = 5,000 draws, B = 999 wild replications. Constructions:
cluster-pairs percentile bootstrap; CR1-t(G-1); CR2 + Bell-McCaffrey dof;
CR3-t(G-1); Webb wild-t; Rademacher wild-t; restricted Webb wild-t (evaluated as
the test at the truth, which is exactly interval coverage for an inversion).

Decision rule (spec Sec.3, fixed ex ante): binding := the NARROWEST construction
with Gaussian coverage >= 93.0 AND t5 coverage >= 91.0. Branches: L1 if Webb
wild-t is selected; L2 if a BM sandwich is; L3 if nothing qualifies.

Writes ONLY data/fewcluster_coverage_results.json.

Run:  cd hazard && python3 fewcluster_coverage.py
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

HAZ = Path(__file__).resolve().parent
DATA = HAZ / "data"
OUT = DATA / "fewcluster_coverage_results.json"
V2_ART = DATA / "floor_inference_correction_v2_results.json"
READ = "R2_2018_gap<=-0.0025_age>=12"

S = 5000
B = 999
SEED = 20260804
ALPHA = 0.05
GAUSS_MIN, T5_MIN = 93.0, 91.0
EFF_WANT, EFF_TOL = 5.9, 0.1
LEV_WANT, LEV_TOL = 0.33, 0.01

WEBB = np.array([-np.sqrt(1.5), -1.0, -np.sqrt(0.5), np.sqrt(0.5), 1.0, np.sqrt(1.5)])


def main() -> None:
    t0 = time.perf_counter()
    art_hash = hashlib.sha256(V2_ART.read_bytes()).hexdigest()
    v2 = json.loads(V2_ART.read_text())
    read = v2["reads"][READ]
    h = np.asarray(read["leverages_h"], dtype=np.float64)
    G = int(read["n_clusters"])
    mu_true = float(read["R_smm"])
    se_true = float(read["se_cr1_smm"])
    assert len(h) == G

    h = h / h.sum()                       # weights (intercept-only leverage = weight)
    eff = 1.0 / float((h ** 2).sum())     # Herfindahl-inverse effective clusters
    lev_max = float(h.max())

    # ---- G-C2: committed design reproduced --------------------------------
    if abs(eff - EFF_WANT) > EFF_TOL or abs(lev_max - LEV_WANT) > LEV_TOL:
        sys.exit(f"ABORT G-C2: eff {eff:.2f} vs {EFF_WANT}, lev {lev_max:.3f} vs {LEV_WANT}")

    sd_truth = se_true                          # truth scale := committed CR1 SE
    sigma_g = sd_truth / np.sqrt((h ** 2).sum())  # per-cluster disturbance sd
    c1 = G / (G - 1.0)
    lam = h ** 2 / (1.0 - h)
    nu_bm = float(lam.sum() ** 2 / (lam ** 2).sum())   # BM dof, intercept-only
    tcrit_g1 = float(stats.t.ppf(1 - ALPHA / 2, G - 1))
    tcrit_bm = float(stats.t.ppf(1 - ALPHA / 2, nu_bm))
    zcrit = float(stats.norm.ppf(1 - ALPHA / 2))

    rng = np.random.default_rng(SEED)
    results = {}
    for cell in ("gaussian", "t5"):
        if cell == "gaussian":
            e = rng.standard_normal((S, G)) * sigma_g
        else:
            e = rng.standard_t(5, size=(S, G)) / np.sqrt(5.0 / 3.0) * sigma_g
        y = mu_true + e                                     # (S, G)
        mu_hat = y @ h                                      # (S,)
        u = y - mu_hat[:, None]                             # residuals
        hu = u * h[None, :]

        v_cr1 = c1 * (hu ** 2).sum(axis=1)
        se1 = np.sqrt(v_cr1)
        u2 = u / np.sqrt(1.0 - h)[None, :]
        v_cr2 = ((u2 * h[None, :]) ** 2).sum(axis=1)
        u3 = u / (1.0 - h)[None, :]
        v_cr3 = c1 * ((u3 * h[None, :]) ** 2).sum(axis=1)

        t_obs = (mu_hat - mu_true) / se1
        cov = {}
        cov["oracle_z"] = float(np.mean(np.abs(mu_hat - mu_true) / sd_truth <= zcrit)) * 100
        cov["cr1_t"] = float(np.mean(np.abs(t_obs) <= tcrit_g1)) * 100
        cov["cr2_bm"] = float(np.mean(np.abs((mu_hat - mu_true) / np.sqrt(v_cr2)) <= tcrit_bm)) * 100
        cov["cr3_t"] = float(np.mean(np.abs((mu_hat - mu_true) / np.sqrt(v_cr3)) <= tcrit_g1)) * 100

        widths = {
            "oracle_z": 2 * zcrit * sd_truth,
            "cr1_t": float(2 * tcrit_g1 * se1.mean()),
            "cr2_bm": float(2 * tcrit_bm * np.sqrt(v_cr2).mean()),
            "cr3_t": float(2 * tcrit_g1 * np.sqrt(v_cr3).mean()),
        }

        # ---- wild bootstrap (vectorized over B per draw, chunked over S) ---
        hit_webb = np.zeros(S, bool)
        hit_rade = np.zeros(S, bool)
        hit_rest = np.zeros(S, bool)
        w_webb_all = WEBB[rng.integers(0, 6, size=(S, B, G))]
        w_rade_all = rng.choice(np.array([-1.0, 1.0]), size=(S, B, G))
        wid_webb = np.zeros(S)
        for s in range(S):
            us = u[s]                                       # (G,)
            # unrestricted: y* = mu_hat + w*u
            for name, w in (("webb", w_webb_all[s]), ("rade", w_rade_all[s])):
                ystar = mu_hat[s] + w * us[None, :]         # (B, G)
                mstar = ystar @ h
                ustar = ystar - mstar[:, None]
                vstar = c1 * ((ustar * h[None, :]) ** 2).sum(axis=1)
                tstar = (mstar - mu_hat[s]) / np.sqrt(vstar)
                qlo, qhi = np.quantile(tstar, [ALPHA / 2, 1 - ALPHA / 2])
                ok = qlo <= t_obs[s] <= qhi
                if name == "webb":
                    hit_webb[s] = ok
                    wid_webb[s] = (qhi - qlo) * se1[s]
                else:
                    hit_rade[s] = ok
            # restricted Webb at the truth (inversion coverage)
            ur = y[s] - mu_true
            ystar = mu_true + w_webb_all[s] * ur[None, :]
            mstar = ystar @ h
            ustar = ystar - mstar[:, None]
            vstar = c1 * ((ustar * h[None, :]) ** 2).sum(axis=1)
            tstar = (mstar - mu_true) / np.sqrt(vstar)
            tr = (mu_hat[s] - mu_true) / se1[s]
            qlo, qhi = np.quantile(tstar, [ALPHA / 2, 1 - ALPHA / 2])
            hit_rest[s] = qlo <= tr <= qhi

        cov["webb_wild_t"] = float(hit_webb.mean()) * 100
        cov["rademacher_wild_t"] = float(hit_rade.mean()) * 100
        cov["restricted_webb"] = float(hit_rest.mean()) * 100
        widths["webb_wild_t"] = float(wid_webb.mean())
        widths["rademacher_wild_t"] = widths["webb_wild_t"]
        widths["restricted_webb"] = widths["webb_wild_t"]

        # percentile: cluster-pairs bootstrap
        hit_pct = np.zeros(S, bool)
        wid_pct = np.zeros(S)
        idx_all = rng.integers(0, G, size=(S, B, G))
        for s in range(S):
            idx = idx_all[s]
            hb = h[idx]
            yb = y[s][idx]
            mb = (hb * yb).sum(axis=1) / hb.sum(axis=1)
            lo, hi = np.quantile(mb, [ALPHA / 2, 1 - ALPHA / 2])
            hit_pct[s] = lo <= mu_true <= hi
            wid_pct[s] = hi - lo
        cov["percentile"] = float(hit_pct.mean()) * 100
        widths["percentile"] = float(wid_pct.mean())

        results[cell] = {"coverage_pct": cov, "mean_width_smm": widths}

    # ---- G-C1: oracle sanity ----------------------------------------------
    for cell in results:
        oc = results[cell]["coverage_pct"]["oracle_z"]
        if not (94.0 <= oc <= 96.0):
            sys.exit(f"ABORT G-C1: oracle coverage {oc:.2f} in {cell}")

    # ---- decision rule -----------------------------------------------------
    CONS = ["percentile", "cr1_t", "cr2_bm", "cr3_t",
            "webb_wild_t", "rademacher_wild_t", "restricted_webb"]
    qualifying = [c for c in CONS
                  if results["gaussian"]["coverage_pct"][c] >= GAUSS_MIN
                  and results["t5"]["coverage_pct"][c] >= T5_MIN]
    if qualifying:
        binding = min(qualifying, key=lambda c: results["gaussian"]["mean_width_smm"][c])
        branch = ("L1_webb_retains" if binding in ("webb_wild_t", "restricted_webb")
                  else "L2_bm_sandwich_binding" if binding == "cr2_bm"
                  else f"L2_other_binding_{binding}")
    else:
        binding, branch = None, "L3_nothing_qualifies"

    payload = {
        "mode": "fewcluster_coverage",
        "run_tag": "fewcluster_coverage",
        "spec": "specs/SPEC_V20_C_fewcluster_coverage_2026-08-04.md",
        "inputs": {"artifact": str(V2_ART.name), "sha256": art_hash, "read": READ,
                   "G": G, "mu_true_smm": mu_true, "se_cr1_smm": se_true,
                   "effective_clusters": eff, "max_leverage": lev_max,
                   "bm_dof": nu_bm, "S": S, "B": B, "seed": SEED},
        "gates": {"G_C1_oracle": {c: results[c]["coverage_pct"]["oracle_z"] for c in results},
                  "G_C2_design": {"effective_clusters": eff, "max_leverage": lev_max}},
        "cells": results,
        "qualifying": qualifying,
        "binding_construction": binding,
        "landing_branch": branch,
        "runtime_s": round(time.perf_counter() - t0, 1),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n")
    g = results["gaussian"]["coverage_pct"]
    print("coverage (gaussian): " + ", ".join(f"{c}={g[c]:.1f}" for c in CONS))
    t5c = results["t5"]["coverage_pct"]
    print("coverage (t5):       " + ", ".join(f"{c}={t5c[c]:.1f}" for c in CONS))
    print(f"binding: {binding}  branch: {branch}")
    print(f"Wrote {OUT} ({payload['runtime_s']}s)")


if __name__ == "__main__":
    main()
