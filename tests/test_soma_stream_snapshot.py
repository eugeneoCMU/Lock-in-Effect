from pathlib import Path
import sys

import polars as pl

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "hazard"))
from soma_stream_snapshot import build


def test_latest_pre_qt_record_excludes_paid_off_and_non_30yr(tmp_path):
    def orig(loan_id, term):
        row = [""] * 32
        row[0], row[10], row[11], row[12] = "740", "200000", "75", "3.5"
        row[15], row[16], row[19], row[21] = "FRM", "PA", loan_id, str(term)
        return "|".join(row)

    def perf(loan_id, period, balance, zb=""):
        row = [""] * 32
        row[0], row[1], row[2], row[3], row[4], row[8] = (
            loan_id, period, str(balance), "0", "36", zb)
        return "|".join(row)

    o = tmp_path / "orig_2019Q1.txt"
    p = tmp_path / "perf_2019Q1.txt"
    out = tmp_path / "snapshot.parquet"
    o.write_text("\n".join([orig("F19Q1SURVIVE", 360),
                              orig("F19Q1PREPAID", 360),
                              orig("F19Q1FIFTEEN", 180)]))
    p.write_text("\n".join([
        perf("F19Q1SURVIVE", "202205", 100000),
        perf("F19Q1SURVIVE", "202206", 99000),
        perf("F19Q1PREPAID", "202204", 100000),
        perf("F19Q1PREPAID", "202205", 0, "01"),
        perf("F19Q1FIFTEEN", "202205", 100000),
    ]))
    report = build(o, p, out)
    result = pl.read_parquet(out)
    assert report["pre_qt_survivors"] == 1
    assert result["loan_id"].to_list() == ["F19Q1SURVIVE"]
    assert result["reporting_period"].to_list() == ["202205"]
    assert result["original_loan_term"].to_list() == [360]


def test_old_positive_record_is_not_a_may_2022_survivor(tmp_path):
    orig = [""] * 32
    orig[0], orig[10], orig[11], orig[12] = "740", "200000", "75", "3.5"
    orig[15], orig[19], orig[21] = "FRM", "F18Q1OLD", "360"
    perf = [""] * 32
    perf[0], perf[1], perf[2], perf[4] = "F18Q1OLD", "202110", "100000", "36"
    o, p, out = (tmp_path / "orig_2018Q1.txt", tmp_path / "perf_2018Q1.txt",
                 tmp_path / "snapshot.parquet")
    o.write_text("|".join(orig))
    p.write_text("|".join(perf))
    report = build(o, p, out)
    assert report["pre_qt_survivors"] == 0
    assert pl.read_parquet(out).is_empty()
