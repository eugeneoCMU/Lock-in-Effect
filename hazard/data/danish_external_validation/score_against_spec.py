#!/usr/bin/env python3
"""Score DNVPDKR2 pull against SPEC_danish_redemption_validation_2026-07-28.md (incl. addendum).
Committed metrics: M2' (FKE, DKK, <=2% coupons, annualized total-redemption rate), M1' (FKE all-coupon),
FK context, 30y variant, N1/N2 cross-check. Load-bearing window 2022M07-2023M12. Thresholds: 8%/12%/boundary +-0.25pp."""
import csv, json, sys
LOW = ["B","C","D","E","F","G","H","I"]          # coupons <= 2% per spec (negative coupons included; ~zero stock expected)
data = {}                                          # (typ, mat, kupon, datat) -> {month: value}
with open(sys.argv[1], encoding="utf-8-sig") as f:
    for r in csv.DictReader(f, delimiter=";"):
        v = r["INDHOLD"].strip()
        if v in ("", "..", "-"): continue
        data.setdefault((r["TYPREAL"], r["LØBETID3"], r["KUPON2"], r["DATAT"]), {})[r["TID"]] = float(v)
months = sorted({m for d in data.values() for m in d})
def series(typ, mat, kupons, datat):
    out = {}
    for m in months:
        vals = [data.get((typ, mat, k, datat), {}).get(m) for k in kupons]
        if any(v is not None for v in vals): out[m] = sum(v for v in vals if v is not None)
    return out
def ann_rates(typ, mat, kupons):
    n1, n2 = series(typ, mat, kupons, "N1"), series(typ, mat, kupons, "N2")
    out = {}
    for i, m in enumerate(months[1:], 1):
        prev = months[i-1]
        if m in n2 and prev in n1 and n1[prev] > 0:
            x = -n2[m] / n1[prev]                  # monthly redemption fraction (net txn sign-flipped)
            out[m] = 1 - (1 - x) ** 12
    return out, n1, n2
def window_mean(rates, lo, hi):
    sel = [v for m, v in rates.items() if lo <= m <= hi]
    return (sum(sel) / len(sel), len(sel)) if sel else (None, 0)
LB = ("2022M07", "2023M12")
res = {}
for label, typ, mat, kup in [("M2prime_FKE_le2pct_allmat", "FKE", "A0", LOW),
                             ("M1prime_FKE_allcoupon_allmat", "FKE", "A0", ["A0"]),
                             ("FK_allcallable_context", "FK", "A0", ["A0"]),
                             ("M2prime_FKE_le2pct_30y", "FKE", "5", LOW)]:
    rates, n1, n2 = ann_rates(typ, mat, kup)
    mean, n = window_mean(rates, *LB)
    res[label] = {"loadbearing_mean_annualized": mean, "n_months": n,
                  "monthly_annualized_2022M06_2025M11": {m: round(v, 5) for m, v in rates.items() if "2022M06" <= m <= "2025M11"},
                  "stock_2022M06": n1.get("2022M06"), "stock_2023M12": n1.get("2023M12")}
# N1/N2 cross-check on FKE all-coupon, all maturities (load-bearing window)
n1, n2 = series("FKE", "A0", ["A0"], "N1"), series("FKE", "A0", ["A0"], "N2")
chk = []
for i, m in enumerate(months[1:], 1):
    prev = months[i-1]
    if LB[0] <= m <= LB[1] and m in n1 and prev in n1 and m in n2:
        chk.append(abs((n1[m] - n1[prev]) - n2[m]))
res["crosscheck_FKE_maxabs_dN1_minus_N2_mDKK"] = max(chk) if chk else None
R = res["M2prime_FKE_le2pct_allmat"]["loadbearing_mean_annualized"]
verdict = ("RULE-A-PRIME (strongly falsified)" if R > 0.12 else
           "BOUNDARY" if abs(R - 0.08) <= 0.0025 else
           "RULE-A (pin falsified)" if R > 0.08 else "RULE-B (pin supported)")
res["R_loadbearing"] = R
res["verdict_per_committed_mapping"] = verdict
json.dump(res, open(sys.argv[2], "w"), indent=1)
print(f"R (FKE, <=2% coupon, ann. total-redemption rate, mean 2022M07-2023M12): {R:.4%}  over {res['M2prime_FKE_le2pct_allmat']['n_months']} months")
print(f"  implied extraordinary lower bound (R - 4pp allowance): {R-0.04:.4%}")
print(f"FKE all-coupon: {res['M1prime_FKE_allcoupon_allmat']['loadbearing_mean_annualized']:.4%} | FK all-callable (net-of-issuance context): {res['FK_allcallable_context']['loadbearing_mean_annualized']:.4%} | FKE <=2% 30y: {res['M2prime_FKE_le2pct_30y']['loadbearing_mean_annualized']:.4%}")
print(f"cross-check max|dN1-N2| (m DKK): {res['crosscheck_FKE_maxabs_dN1_minus_N2_mDKK']}")
print(f"VERDICT: {verdict}")
q = res["M2prime_FKE_le2pct_allmat"]["monthly_annualized_2022M06_2025M11"]
for m in ["2022M07","2022M09","2022M11","2023M01","2023M04","2023M07","2023M10","2023M12","2024M06","2025M06"]:
    if m in q: print(f"   {m}: {q[m]:.2%}")
