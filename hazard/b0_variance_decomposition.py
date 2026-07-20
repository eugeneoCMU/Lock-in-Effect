"""
B0 pre-registered variance decomposition of empirical monthly CPR.

METHOD FIXED BEFORE INSPECTING RESULTS:
  Y_t   = empirical annual CPR, exposure-weighted, from cohort_month_panel.parquet
          SMM_t = sum(prepaid_upb_t)/sum(exposure_upb_t); CPR_t = 1-(1-SMM_t)^12
  SEASONAL block S = 11 month-of-year dummies (Jan omitted)
  RATE block R     = exposure-weighted mean rate gap g_t = wmean(coupon) - MORTGAGE30US/100
                     at lags 0,1,2,3  (LAG SET DECLARED BEFORE RUNNING; NO SEARCH)
  Decomposition of Var(Y) via OLS R^2:
      R2_S, R2_R, R2_full (S+R together, plus intercept)
      Sequential Type I ordering A (S then R): seasonal=R2_S, rate=R2_full-R2_S
      Sequential Type I ordering B (R then S): rate=R2_R, seasonal=R2_full-R2_R
      SHAPLEY (order-invariant, = LMG with 2 blocks):
          phi_S = 0.5*(R2_S + (R2_full - R2_R))
          phi_R = 0.5*(R2_R + (R2_full - R2_S))
      residual = 1 - R2_full
  ADJUDICATION: the pre-commitment (rate share >= 0.15) is adjudicated on the
  SHAPLEY rate share, on the FULL PANEL. QT window reported alongside.

NETWORK DEPENDENCY: the rate block is fetched LIVE from FRED (MORTGAGE30US) using
the key resolved by common/fred_key.py from the gitignored .env. There is no
committed cache, so this module cannot be re-run offline; the frozen artifact at
hazard/data/b0_variance_decomposition.json is the record of the adjudicated run.
"""
import json, sys, urllib.request
from pathlib import Path
import numpy as np, pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from common.fred_key import get_fred_api_key

OUT = str(_ROOT / "hazard" / "data" / "b0_variance_decomposition.json")
PANEL = str(_ROOT / "hazard" / "data" / "cohort_month_panel.parquet")
LAGS = [0, 1, 2, 3]
THRESH = 0.15

d = pd.read_parquet(PANEL)
g = d.groupby("reporting_period", as_index=False).agg(
    prepaid=("prepaid_upb", "sum"), expo=("exposure_upb", "sum"))
g["smm"] = g["prepaid"] / g["expo"]
g["cpr"] = 1.0 - (1.0 - g["smm"]) ** 12
# exposure-weighted mean coupon per month
d["_wc"] = d["coupon"] * d["exposure_upb"]
wc = d.groupby("reporting_period", as_index=False).agg(wc=("_wc", "sum"), e=("exposure_upb", "sum"))
wc["wcoupon"] = wc["wc"] / wc["e"]
g = g.merge(wc[["reporting_period", "wcoupon"]], on="reporting_period")
g["period"] = pd.to_datetime(g["reporting_period"].astype(str), format="%Y%m")
g = g.sort_values("period").reset_index(drop=True)

# --- FRED MORTGAGE30US -> monthly mean
key = get_fred_api_key()
url = ("https://api.stlouisfed.org/fred/series/observations?series_id=MORTGAGE30US"
       f"&api_key={key}&file_type=json&observation_start=2016-01-01")
obs = json.loads(urllib.request.urlopen(url, timeout=60).read())["observations"]
fr = pd.DataFrame([(o["date"], o["value"]) for o in obs], columns=["date", "v"])
fr = fr[fr.v != "."].copy()
fr["date"] = pd.to_datetime(fr["date"]); fr["v"] = fr["v"].astype(float)
fr["period"] = fr["date"].values.astype("datetime64[M]")
mr = fr.groupby("period", as_index=False)["v"].mean().rename(columns={"v": "mort30"})
mr["period"] = pd.to_datetime(mr["period"])
g = g.merge(mr, on="period", how="left")
assert g["mort30"].notna().all(), g[g.mort30.isna()]

g["gap"] = g["wcoupon"] - g["mort30"] / 100.0
for L in LAGS:
    g[f"gap_l{L}"] = g["gap"].shift(L)
g["moy"] = g["period"].dt.month

print("FULL EMPIRICAL SERIES (period, CPR_annual, wmean_coupon, MORTGAGE30US, gap_pp):")
for _, r in g.iterrows():
    print(f"  {r.period:%Y-%m}  CPR={r.cpr*100:7.4f}%  coupon={r.wcoupon*100:6.4f}%  "
          f"mort30={r.mort30:6.3f}%  gap={(r.gap*100):+7.4f}pp")


def r2(y, X):
    X = np.column_stack([np.ones(len(y)), X]) if X.size else np.ones((len(y), 1))
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sst = ((y - y.mean()) ** 2).sum()
    return 1.0 - (resid ** 2).sum() / sst


def decompose(sub, label):
    sub = sub.dropna(subset=[f"gap_l{L}" for L in LAGS]).copy()
    y = sub["cpr"].to_numpy(float)
    n = len(y)
    S = pd.get_dummies(sub["moy"], prefix="m", drop_first=True).to_numpy(float)
    R = sub[[f"gap_l{L}" for L in LAGS]].to_numpy(float)
    r2s, r2r, r2f = r2(y, S), r2(y, R), r2(y, np.column_stack([S, R]))
    phi_s = 0.5 * (r2s + (r2f - r2r))
    phi_r = 0.5 * (r2r + (r2f - r2s))
    res = {
        "label": label, "n_months": int(n),
        "first": f"{sub.period.iloc[0]:%Y-%m}", "last": f"{sub.period.iloc[-1]:%Y-%m}",
        "n_seasonal_dummies": int(S.shape[1]), "lags": LAGS,
        "R2_seasonal_only": r2s, "R2_rate_only": r2r, "R2_full": r2f,
        "typeI_order_S_then_R": {"seasonal": r2s, "rate": r2f - r2s, "residual": 1 - r2f},
        "typeI_order_R_then_S": {"rate": r2r, "seasonal": r2f - r2r, "residual": 1 - r2f},
        "shapley": {"seasonal": phi_s, "rate": phi_r, "residual": 1 - r2f},
        "shapley_rate_share": phi_r,
        "verdict_vs_threshold": "PASS" if phi_r >= THRESH else "CONCEDE",
    }
    print(f"\n=== {label} === n={n} ({res['first']}..{res['last']})")
    print(f"  R2_seasonal_only={r2s:.4f}  R2_rate_only={r2r:.4f}  R2_full={r2f:.4f}")
    print(f"  TypeI S->R : seasonal={r2s:.4f} rate={r2f-r2s:.4f} resid={1-r2f:.4f}")
    print(f"  TypeI R->S : rate={r2r:.4f} seasonal={r2f-r2r:.4f} resid={1-r2f:.4f}")
    print(f"  SHAPLEY    : seasonal={phi_s:.4f} rate={phi_r:.4f} resid={1-r2f:.4f}  -> {res['verdict_vs_threshold']}")
    return res


full = decompose(g, "FULL_PANEL_2017_01..2025_09")
qt_mask = (g.period >= "2022-06-01") & (g.period <= "2025-11-30")
qt = decompose(g[qt_mask], "QT_WINDOW_2022_06..2025_11")

out = {
    "method_prefixed_before_results": __doc__.strip(),
    "threshold_TIMING_RATE_SHARE_MIN": THRESH,
    "adjudicated_on": "SHAPLEY rate share, FULL PANEL",
    "series": [{"period": f"{r.period:%Y-%m}", "cpr_annual": r.cpr, "smm": r.smm,
                "wmean_coupon": r.wcoupon, "mortgage30us_pct": r.mort30, "gap_decimal": r.gap}
               for _, r in g.iterrows()],
    "full_panel": full, "qt_window": qt,
    "final_verdict": "TIMING_FIXABLE" if full["shapley_rate_share"] >= THRESH else "CONCEDE_LEVELS_ONLY",
}
json.dump(out, open(OUT, "w"), indent=2, default=float)
print("\nFINAL:", out["final_verdict"])
