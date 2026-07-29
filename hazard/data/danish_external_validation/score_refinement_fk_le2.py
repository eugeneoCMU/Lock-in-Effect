#!/usr/bin/env python3
"""Refinement after the committed cross-check FAILED on FKE (subcategory reclassification):
same semantic target on FK x (coupon<=2%) — coupon is a fixed bond attribute (no migration),
and <=2%-coupon callable issuance ~0 in-window (residual issuance biases the rate DOWN = conservative).
Labeled as a verification-driven refinement per the spec's deviation rule."""
import csv, json, sys
LOW = ["B","C","D","E","F","G","H","I"]
data = {}
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
n1, n2 = series("FK","A0",LOW,"N1"), series("FK","A0",LOW,"N2")
rates, diffs = {}, {}
for i, m in enumerate(months[1:], 1):
    prev = months[i-1]
    if m in n2 and prev in n1 and n1[prev] > 0:
        rates[m] = 1 - (1 + n2[m]/n1[prev])**12
    if m in n1 and prev in n1 and m in n2:
        diffs[m] = (n1[m]-n1[prev]) - n2[m]
LB=[m for m in rates if "2022M07" <= m <= "2023M12"]
R = sum(rates[m] for m in LB)/len(LB)
chk = {m:d for m,d in diffs.items() if "2022M07" <= m <= "2023M12"}
maxchk = max(abs(d) for d in chk.values())
out = {"R_FK_le2pct_loadbearing_mean": R, "n_months": len(LB),
 "crosscheck_maxabs_dN1_minus_N2_mDKK": maxchk,
 "crosscheck_maxabs_as_share_of_stock": maxchk/n1["2022M06"],
 "stock_2022M06_mDKK": n1["2022M06"], "stock_2023M12_mDKK": n1["2023M12"],
 "monthly": {m: round(rates[m],5) for m in rates if "2022M06" <= m <= "2025M11"},
 "verdict": ("RULE-A-PRIME" if R>0.12 else "BOUNDARY" if abs(R-0.08)<=0.0025 else "RULE-A" if R>0.08 else "RULE-B")}
json.dump(out, open(sys.argv[2],"w"), indent=1)
print(f"FK x <=2%-coupon: R = {R:.4%} over {len(LB)} months; extraordinary lower bound = {R-0.04:.4%}")
print(f"stock 2022M06 = {n1['2022M06']/1e6:.3f}bn*1000 (m DKK: {n1['2022M06']:.0f}) -> 2023M12: {n1['2023M12']:.0f}")
print(f"cross-check max|dN1-N2| = {maxchk:.0f} m DKK = {maxchk/n1['2022M06']:.3%} of opening stock")
print(f"VERDICT: {out['verdict']}")
for m in ["2022M07","2022M09","2022M11","2023M01","2023M04","2023M07","2023M10","2023M12","2024M06","2025M06"]:
    if m in rates: print(f"   {m}: {rates[m]:.2%}")
