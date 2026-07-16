#!/usr/bin/env python3
"""
Round-15 Q2: extract the monthly agency CPR/CDR/CRR series from the December
2025 Ginnie Mae Global Markets Analysis Report (GMAR) chart vector paths.

Source document (public):
  https://www.ginniemae.gov/data_and_reports/reporting/Documents/global_market_analysis_dec25.pdf
  Section 4.1 "Prepayment Rates", Figures 12 (Aggregate 1-Month CPR),
  13 (CDR), 14 (CRR); underlying data Recursion, as of November 2025.
  The December 2025 issue is used because its methodology note states the
  aggregation was revised to weighted-average UPB in that issue — one
  consistent (and SOMA-relevant, dollar-weighted) methodology across the
  full plotted history, unlike stitching endpoint labels across the
  2022-2025 issues, which span three chart/aggregation regimes.

Method: the three series are stroked vector polylines (distinct RGB per
agency, 102 monthly vertices each, June 2017 - November 2025). The y-axis
slope is calibrated from the chart's gridline-label spacing; the offset is
anchored on the printed endpoint labels (CPR 8.1/8.8/11.9, CDR 0.5/0.4/1.6,
CRR 7.7/8.4/10.4 for Fannie/Freddie/Ginnie). Validation, embedded in the
output artifact:
  (a) endpoint residuals vs printed labels (must be <= 0.05pp);
  (b) cross-chart identity CPR = 1-(1-CRR)(1-CDR), computed from the
      independently extracted CRR and CDR charts (report mean/max |err|).

Usage:  python3 tools/extract_gmar_dec25.py <path-to-gmar-dec25.pdf>
Writes: hazard/data/gmar_dec25_cpr_series.json
The PDF itself is NOT committed (12 MB, public URL above).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "hazard" / "data" / "gmar_dec25_cpr_series.json"

COLORS = {
    (0.284, 0.445, 0.720): "fannie",
    (0.929, 0.490, 0.185): "freddie",
    (0.639, 0.733, 0.226): "ginnie",
}
PRINTED = {
    "cpr": {"fannie": 8.1, "freddie": 8.8, "ginnie": 11.9},
    "cdr": {"fannie": 0.5, "freddie": 0.4, "ginnie": 1.6},
    "crr": {"fannie": 7.7, "freddie": 8.4, "ginnie": 10.4},
}
BAND_TO_NAME = {3: "cpr", 5: "cdr", 6: "crr"}


def colorkey(c):
    if c is None:
        return None
    for k, v in COLORS.items():
        if all(abs(a - b) < 0.02 for a, b in zip(k, c)):
            return v
    return None


def main(pdf_path: str) -> None:
    import fitz
    fitz.TOOLS.mupdf_display_errors(False)
    doc = fitz.open(pdf_path)
    page = next(p for p in doc
                if "Aggregate 1-Month CPR" in p.get_text()
                and "Aggregate 1-Month CDR" in p.get_text())

    series = {}
    for d in page.get_drawings():
        name = colorkey(d.get("color"))
        if not name or len(d["items"]) < 50:
            continue
        pts = []
        for it in d["items"]:
            if it[0] == "l":
                if not pts:
                    pts.append((it[1].x, it[1].y))
                pts.append((it[2].x, it[2].y))
        series.setdefault(round(d["rect"].y1 / 100), {})[name] = pts

    td = page.get_text("dict")
    spans = [(s["bbox"][0], s["bbox"][1], s["bbox"][3], s["text"].strip())
             for b in td["blocks"] for l in b.get("lines", [])
             for s in l["spans"]]

    months = [f"{y}-{m:02d}" for y in range(2017, 2026) for m in range(1, 13)]
    months = months[months.index("2017-06"): months.index("2025-11") + 1]

    out = {"months": months, "source": {
        "document": "Ginnie Mae Global Markets Analysis Report, December 2025 issue",
        "url": "https://www.ginniemae.gov/data_and_reports/reporting/Documents/global_market_analysis_dec25.pdf",
        "figures": "Figure 12 (CPR), 13 (CDR), 14 (CRR); data: Recursion, as of Nov 2025",
        "methodology_note": "aggregation revised to weighted-average UPB in the Dec-2025 issue",
        "extraction": "vector-polyline vertices; slope from gridline-label spacing, offset from printed endpoint labels",
    }, "validation": {}}

    for band, cdict in series.items():
        name = BAND_TO_NAME.get(band)
        if name is None:
            continue
        vy = [p[1] for pts in cdict.values() for p in pts]
        lo, hi = min(vy) - 45, max(vy) + 12
        ylabels = [((y0 + y1) / 2, float(t.rstrip("%"))) for x0, y0, y1, t in spans
                   if x0 < 118 and re.fullmatch(r"\d{1,2}%", t)
                   and lo <= (y0 + y1) / 2 <= hi]
        assert len(ylabels) >= 3, (name, ylabels)
        ys = np.array([p[0] for p in ylabels]); vs = np.array([p[1] for p in ylabels])
        m = np.polyfit(ys, vs, 1)[0]
        b = float(np.mean([PRINTED[name][ag] - m * pts[-1][1]
                           for ag, pts in cdict.items()]))
        resid = {ag: round(PRINTED[name][ag] - (m * pts[-1][1] + b), 4)
                 for ag, pts in cdict.items()}
        assert all(abs(r) <= 0.05 for r in resid.values()), (name, resid)
        for ag, pts in cdict.items():
            assert len(pts) == len(months), (name, ag, len(pts))
            dx = np.diff([p[0] for p in pts])
            assert dx.std() < 0.35, "non-uniform x spacing"
            out[name] = out.get(name, {})
            out[name][ag] = [round(m * p[1] + b, 3) for p in pts]
        out["validation"][f"{name}_endpoint_residual_pp"] = resid

    err = []
    for ag in ("fannie", "freddie", "ginnie"):
        for i in range(len(months)):
            comb = 1 - (1 - out["crr"][ag][i] / 100) * (1 - out["cdr"][ag][i] / 100)
            err.append(abs(comb - out["cpr"][ag][i] / 100) * 100)
    out["validation"]["cpr_vs_crr_cdr_identity_pp"] = {
        "mean_abs": round(float(np.mean(err)), 4),
        "max_abs": round(float(np.max(err)), 4),
    }
    assert out["validation"]["cpr_vs_crr_cdr_identity_pp"]["max_abs"] <= 0.25

    OUT.write_text(json.dumps(out, indent=1) + "\n")
    print(f"Wrote {OUT}")
    print("validation:", json.dumps(out["validation"], indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
