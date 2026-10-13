#!/usr/bin/env python3
"""One-quarter original-source audit; never writes to or deletes source files.

The frozen specification controls scope. Raw content is streamed, later outcome
fields are skipped, and individual IDs never appear in outputs. Eviction is an
explicit external FileManager step after this program's compact outputs verify.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import hashlib
import inspect
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import time
from schema import SOURCE_SEMANTICS_VERSION

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "specs/SPEC_2026-10-09_raw_2017Q1_audit.md"
SOURCE = Path("/Users/eugene/Library/CloudStorage/GoogleDrive-eugeneo@andrew.cmu.edu/My Drive/Fannie and Freddie MAC")
OUTPUT = ROOT / "output/research-limits/2026-10-09/rebuild/freddie-2017Q1"
CUTOFF = "202509"
KEYS = ["vintage", "coupon", "fico_bucket", "ltv_bucket", "reporting_period"]
GIB = 1024**3


def finite(value):
    try:
        value = float(value)
        return value if math.isfinite(value) else None
    except (ValueError, TypeError):
        return None


def metadata(path):
    stat = path.stat()
    return {"path": str(path), "size": stat.st_size,
            "allocated_bytes": stat.st_blocks * 512, "flags": stat.st_flags,
            "mtime_ns": stat.st_mtime_ns}


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def check_resources(path):
    free = shutil.disk_usage(path).free
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin":
        rss *= 1024
    if free < 12 * GIB:
        raise RuntimeError("Free disk fell below 12 GiB")
    if rss > 8 * GIB:
        raise RuntimeError("Audit RSS exceeded 8 GiB")
    return {"free_disk_bytes": free, "peak_rss_bytes": rss}


class IdentityExceptions:
    """Account for exact, frozen same-year ID placement exceptions only."""
    FIELDS = ('original_records', 'performance_rows', 'eligible_original_loans', 'eligible_original_upb')

    def __init__(self, quarter, record=None):
        self.quarter, self.record, self.seen = quarter, record, set()
        self.allowed = set()
        self.counts = dict.fromkeys(self.FIELDS, 0)
        if record is None:
            return
        ids = record.get('allowed_id_sha256', [])
        expected = record.get('expected', {})
        hashes = record.get('source_sha256', {})
        if (record.get('quarter') != quarter or not isinstance(ids, list) or not ids
                or any(not isinstance(x, str) or not re.fullmatch('[0-9a-f]{64}', x) for x in ids)
                or len(set(ids)) != len(ids) or set(expected) != set(self.FIELDS)
                or set(hashes) != {'origination', 'performance'}
                or any(not isinstance(x, str) or not re.fullmatch('[0-9a-f]{64}', x) for x in hashes.values())
                or any(type(expected[k]) is not int or expected[k] < 0 for k in self.FIELDS[:3])
                or expected['original_records'] != len(ids)
                or type(expected['eligible_original_upb']) not in (int, float)
                or not math.isfinite(expected['eligible_original_upb']) or expected['eligible_original_upb'] < 0):
            raise ValueError('Invalid frozen identity exception record')
        self.allowed = set(ids)

    def accept(self, loan_id, kind):
        if self.record is None:
            return False
        if (not re.fullmatch(('F' + self.quarter[2:4] + r'Q[1-4]\d+').encode(), loan_id)
                or loan_id.startswith(('F' + self.quarter[2:]).encode())):
            return False
        identifier = hashlib.sha256(loan_id).hexdigest()
        if identifier not in self.allowed:
            return False
        self.counts['original_records' if kind == 'origination' else 'performance_rows'] += 1
        if kind == 'origination':
            self.seen.add(identifier)
        return True

    def eligible(self, upb):
        self.counts['eligible_original_loans'] += 1
        self.counts['eligible_original_upb'] += upb

    def finish(self, source_hashes):
        if self.record is None:
            return None
        if (self.seen != self.allowed or self.counts != self.record['expected']
                or source_hashes != self.record['source_sha256']):
            raise ValueError('Frozen identity exception counts, allowlist or source hashes disagree')
        return dict(enabled=True, quarter=self.quarter,
            allowed_id_sha256=self.record['allowed_id_sha256'], source_sha256=source_hashes, **self.counts)


def schema_audit(orig_path, perf_path, *, quarter='2017Q1', exclude_zero_note_rate=False,
                 identity_exceptions=None):
    """Only identity/layout/date fields are inspected in performance here."""
    if not re.fullmatch(r'20\d{2}Q[1-4]', quarter):
        raise ValueError('Expected declared source quarter YYYYQn')
    id_pattern = ('F' + quarter[2:] + r'\d+').encode()
    identity = IdentityExceptions(quarter, identity_exceptions)
    loans, all_ids = {}, set()
    ow, pw = Counter(), Counter()
    o = {"rows": 0, "duplicate_ids": 0, "invalid_id_positions": 0,
         "eligible_ids": 0, "eligible_360_month_ids": 0}
    p = {"rows": 0, "invalid_id_positions": 0, "unknown_origination_ids": 0,
         "invalid_reporting_periods": 0, "pre_cutoff_rows": 0, "post_cutoff_date_rows": 0}
    oh, ph = hashlib.sha256(), hashlib.sha256()
    zero_rates=dict(enabled=exclude_zero_note_rate,otherwise_eligible_frm_count=0,
        otherwise_eligible_frm_upb=0.,known360_count=0,known360_upb=0.)
    with orig_path.open("rb") as source:
        for raw in source:
            oh.update(raw)
            o["rows"] += 1
            cols = raw.rstrip(b"\r\n").split(b"|")
            ow[len(cols)] += 1
            if len(cols) != 32:
                continue
            loan_id = cols[19]
            exceptional = not re.fullmatch(id_pattern, loan_id) and identity.accept(loan_id, 'origination')
            if not re.fullmatch(id_pattern, loan_id) and not exceptional:
                o["invalid_id_positions"] += 1
            if loan_id in all_ids:
                o["duplicate_ids"] += 1
            all_ids.add(loan_id)
            fico, upb, ltv, rate = (finite(cols[i]) for i in (0, 10, 11, 12))
            eligible = (cols[15] == b"FRM" and upb is not None and upb > 0
                        and ltv is not None and 1 <= ltv <= 200
                        and fico is not None and 300 <= fico <= 850)
            if eligible:
                if rate == 0 and exclude_zero_note_rate:
                    zero_rates['otherwise_eligible_frm_count']+=1
                    zero_rates['otherwise_eligible_frm_upb']+=upb
                    if finite(cols[21]) == 360:
                        zero_rates['known360_count']+=1
                        zero_rates['known360_upb']+=upb
                    continue
                # A missing rate cannot be assigned to a valid cohort; retain
                # this as a blocking positional/data ambiguity, not silently drop.
                if rate is None or not 0 < rate < 30:
                    o.setdefault("eligible_invalid_rate_rows", 0)
                    o["eligible_invalid_rate_rows"] += 1
                    continue
                o["eligible_ids"] += 1
                o["eligible_360_month_ids"] += int(cols[21] == b"360")
                if exceptional and cols[21] == b'360':
                    identity.eligible(upb)
                loans[loan_id] = (upb, round((rate / 100) / .005) * .005,
                                  "<680" if fico < 680 else "680-740" if fico < 740 else "740+",
                                  "≤80" if ltv <= 80 else ">80")
    print("Origination schema pass complete", flush=True)
    with perf_path.open("rb") as source:
        for raw in source:
            ph.update(raw)
            p["rows"] += 1
            cols = raw.rstrip(b"\r\n").split(b"|")
            pw[len(cols)] += 1
            if len(cols) != 32:
                continue
            if not re.fullmatch(id_pattern, cols[0]) and not identity.accept(cols[0], 'performance'):
                p["invalid_id_positions"] += 1
            if cols[0] not in all_ids:
                p["unknown_origination_ids"] += 1
            period = cols[1]
            if not re.fullmatch(rb"20\d{2}(0[1-9]|1[0-2])", period):
                p["invalid_reporting_periods"] += 1
            elif period <= CUTOFF.encode():
                p["pre_cutoff_rows"] += 1
            else:
                p["post_cutoff_date_rows"] += 1
            if p["rows"] % 2000000 == 0:
                check_resources(perf_path.parent)
                print(f"Schema rows checked: {p['rows']:,}", flush=True)
    o["sha256"], p["sha256"] = oh.hexdigest(), ph.hexdigest()
    identity_report = identity.finish({'origination': o['sha256'], 'performance': p['sha256']})
    o['zero_note_rate_exclusions']=zero_rates
    o["width_counts"], p["width_counts"] = dict(ow), dict(pw)
    passed = (set(ow) == {32} and set(pw) == {32}
              and o["duplicate_ids"] == o["invalid_id_positions"] == 0
              and not o.get("eligible_invalid_rate_rows", 0)
              and p["invalid_id_positions"] == p["unknown_origination_ids"] == p["invalid_reporting_periods"] == 0)
    return {"passed": passed, "origination": o, "performance": p,
            'source_semantics_version': SOURCE_SEMANTICS_VERSION,
            'identity_exceptions': identity_report}, loans


def audit_rows(perf_path, loans):
    """Bound memory to original IDs, cohort cells, and one loan's history."""
    counts = {name: 0 for name in [
        "eligible_pre_cutoff_rows", "invalid_balance_rows", "negative_balance_rows",
        "missing_or_nonfinite_age_rows", "within_loan_backward_rows", "duplicate_loan_month_rows",
        "loan_group_reentries", "missing_calendar_months", "valid_balance_missing_calendar_months",
        "first_observed_payoff_rows", "payoff_with_nonadjacent_prior_rows", "valid_balance_rows",
        "voluntary_payoff_rows", "loans_with_pre_cutoff_history",
    ]}
    counts.update(first_observed_payoff_fallback_upb=0.0,
                  payoff_with_nonadjacent_prior_upb=0.0)
    cells = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0, 0, 0, 0.0])
    seen, current, history = set(), None, []

    def finish(loan_id, group):
        if not group:
            return
        counts["loans_with_pre_cutoff_history"] += 1
        months = [x[0] for x in group]
        counts["within_loan_backward_rows"] += sum(b < a for a, b in zip(months, months[1:]))
        counts["duplicate_loan_month_rows"] += len(months) - len(set(months))
        counts["missing_calendar_months"] += max(months) - min(months) + 1 - len(set(months))
        valid = [x for x in group if x[1] is not None and x[1] >= 0]
        if not valid:
            return
        vm = [x[0] for x in valid]
        counts["valid_balance_missing_calendar_months"] += max(vm) - min(vm) + 1 - len(set(vm))
        upb, coupon, fico, ltv = loans[loan_id]
        # Source-order reference is distinct from actual legacy parallel-join
        # ordering; it is retained only as a diagnostic column.
        source_payoff = {}
        prior = None
        for month, balance, age, is_prepay in valid:
            source_payoff[month] = (upb if prior is None else prior) if is_prepay else 0.0
            prior = balance
        prior = prior_month = None
        for month, balance, age, is_prepay in sorted(valid, key=lambda x: x[0]):
            year, zero_month = divmod(month, 12)
            key = (2017, coupon, fico, ltv, f"{year:04d}{zero_month+1:02d}")
            c = cells[key]
            payoff = 0.0
            if is_prepay:
                counts["voluntary_payoff_rows"] += 1
                payoff = upb if prior is None else prior
                if prior is None:
                    counts["first_observed_payoff_rows"] += 1
                    counts["first_observed_payoff_fallback_upb"] += upb
                elif month != prior_month + 1:
                    counts["payoff_with_nonadjacent_prior_rows"] += 1
                    counts["payoff_with_nonadjacent_prior_upb"] += prior
            c[0] += balance
            c[1] += upb
            c[2] += payoff
            if age is not None:
                c[3] += age
                c[4] += 1
            c[5] += 1
            c[6] += source_payoff.get(month, 0.0)
            prior, prior_month = balance, month

    with perf_path.open("rb") as source:
        for row_number, raw in enumerate(source, 1):
            # Keep outcomes as uninterpreted bytes until the date cutoff passes.
            cols = raw.rstrip(b"\r\n").split(b"|")
            if cols[1] > CUTOFF.encode() or cols[0] not in loans:
                continue
            loan_id = cols[0]
            if loan_id != current:
                finish(current, history)
                if loan_id in seen:
                    counts["loan_group_reentries"] += 1
                seen.add(loan_id)
                current, history = loan_id, []
            counts["eligible_pre_cutoff_rows"] += 1
            balance, age = finite(cols[2]), finite(cols[4])
            if balance is None or balance < 0:
                counts["invalid_balance_rows"] += 1
                counts["negative_balance_rows"] += int(balance is not None and balance < 0)
            else:
                counts["valid_balance_rows"] += 1
            if age is None:
                counts["missing_or_nonfinite_age_rows"] += 1
            month = int(cols[1][:4]) * 12 + int(cols[1][4:]) - 1
            history.append((month, balance, age, cols[8] == b"01"))
            if len(history) > 10000:
                raise ValueError("Unbounded/repeated single-loan history; reference stopped")
            if row_number % 2000000 == 0:
                check_resources(perf_path.parent)
                print(f"Pre-cutoff streaming audit rows scanned: {row_number:,}", flush=True)
    finish(current, history)
    counts["reference_complete"] = counts["loan_group_reentries"] == counts["duplicate_loan_month_rows"] == 0
    output = []
    if counts["reference_complete"]:
        for key, c in sorted(cells.items()):
            output.append(dict(zip(KEYS, key), exposure_upb=c[0], orig_upb_sum=c[1],
                prepaid_upb=c[2], finite_age_sum=c[3], finite_age_count=c[4],
                loan_count=c[5], mean_loan_age=c[3]/c[4] if c[4] else None,
                source_order_prepaid_upb=c[6]))
    return counts, output


def replay_worker(orig, perf, destination, kind, frozen_ingest):
    """Run the frozen production code with an outcome-before-cutoff reader."""
    os.environ.setdefault("FRED_API_KEY", "audit-no-network")
    sys.path.insert(0, str(ROOT / "hazard"))
    import importlib.util
    module_spec = importlib.util.spec_from_file_location("audit_frozen_ingest", frozen_ingest)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    scan_source = inspect.getsource(module._scan_perf)
    if scan_source.count("lf.select([")==0:
        raise ValueError("Unexpected production performance reader; cutoff patch refused")
    scan_source = scan_source.replace("lf.select([", 'lf.filter(pl.col("reporting_period") <= "202509").select([', 1)
    namespace = dict(vars(module))
    exec(scan_source, namespace)
    build_source = inspect.getsource(module.build_panel_from_files)
    if kind == "legacy":
        needle = '.over("loan_sequence_number", order_by="reporting_period")'
        if build_source.count(needle) != 1:
            raise ValueError("Unexpected ordered-lag implementation; legacy patch refused")
        build_source = build_source.replace(needle, '.over("loan_sequence_number")')
    exec(build_source, namespace)
    namespace["build_panel_from_files"]([(orig, perf)], output=destination)


def monitored_replay(orig, perf, output, kind, frozen_ingest):
    destination = output / f"{kind}_production_cells.parquet"
    log_path = output / f"{kind}_production_replay.log"
    env = dict(os.environ, POLARS_MAX_THREADS="2", FRED_API_KEY="audit-no-network")
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", kind,
               "--orig", str(orig), "--perf", str(perf), "--output", str(destination),
               "--frozen-ingest", str(frozen_ingest)]
    start, peak, stopped = time.monotonic(), 0, None
    with log_path.open("w") as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        while process.poll() is None:
            probe = subprocess.run(["ps", "-o", "rss=", "-p", str(process.pid)],
                                   capture_output=True, text=True)
            try:
                peak = max(peak, int(probe.stdout.strip()) * 1024)
            except ValueError:
                pass
            if peak > 8*GIB or shutil.disk_usage(output).free < 12*GIB or time.monotonic()-start > 900:
                stopped = "memory_disk_or_15minute_guard"
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                break
            time.sleep(1)
        process.wait()
    return {"status": "completed" if process.returncode == 0 else "incomplete",
            "returncode": process.returncode, "stopped_reason": stopped,
            "peak_observed_rss_bytes": peak, "elapsed_seconds": time.monotonic()-start,
            "output": str(destination) if process.returncode == 0 else None, "log": str(log_path)}


def compare_reference(cells, path):
    import numpy as np
    import pandas as pd
    left = pd.DataFrame(cells).set_index(KEYS).sort_index()
    right = pd.read_parquet(path).set_index(KEYS).sort_index()
    result = {"keys_equal": left.index.equals(right.index), "columns": {}}
    if not result["keys_equal"]:
        return result
    for col in ["exposure_upb", "orig_upb_sum", "prepaid_upb", "loan_count", "mean_loan_age"]:
        a,b=left[col].to_numpy(float),right[col].to_numpy(float)
        delta=np.abs(a-b)
        result["columns"][col] = {
            "allclose": bool(np.allclose(a,b,rtol=1e-10,atol=1e-5,equal_nan=True)),
            "max_abs_difference": float(np.nanmax(delta)),
            "different_cells_beyond_tolerance": int((~np.isclose(a,b,rtol=1e-10,atol=1e-5,equal_nan=True)).sum()),
            "reference_sum": float(np.nansum(a)), "production_sum": float(np.nansum(b)),
        }
    return result


def run(orig, perf, output, replay=True):
    if orig.name != "orig_2017Q1.txt" or perf.name != "perf_2017Q1.txt":
        raise ValueError("Only the authorized 2017Q1 pair may be run")
    output.mkdir(parents=True, exist_ok=True)
    check_resources(output)
    frozen_spec = output / "spec_frozen.md"
    spec_bytes = SPEC.read_bytes()
    if frozen_spec.exists() and frozen_spec.read_bytes() != spec_bytes:
        raise ValueError("Specification differs from frozen copy")
    if not frozen_spec.exists():
        frozen_spec.write_bytes(spec_bytes)
        write_json(output / "spec_freeze.json", {"frozen_utc": datetime.now(timezone.utc).isoformat(),
                   "sha256": hashlib.sha256(spec_bytes).hexdigest()})
    before = {"origination": metadata(orig), "performance": metadata(perf)}
    write_json(output / "source_metadata_before.json", before)
    report = {"started_utc": datetime.now(timezone.utc).isoformat(), "cutoff": CUTOFF,
              "spec_sha256": hashlib.sha256(spec_bytes).hexdigest(),
              "source_metadata_before": before, "cleanup": "external verified FileManager eviction pending"}
    try:
        schema, loans = schema_audit(orig, perf)
        report["schema"] = schema
        write_json(output / "schema_audit.json", schema)
        if not schema["passed"]:
            report["status"] = "blocked_schema_or_source_ambiguity"
            report["outcomes_calculated"] = False
            return report
        raw_audit, cells = audit_rows(perf, loans)
        report["raw_audit"] = raw_audit
        report["outcomes_calculated"] = True
        write_json(output / "raw_audit.json", raw_audit)
        if not raw_audit["reference_complete"]:
            report["status"] = "blocked_duplicate_or_noncontiguous_histories"
            return report
        with (output / "independent_reference_cells.csv").open("w") as target:
            writer=csv.DictWriter(target, fieldnames=list(cells[0]))
            writer.writeheader()
            writer.writerows(cells)
        report["reference_cells"] = len(cells)
        report["reference_additive_totals"] = {c: sum(r[c] for r in cells) for c in
            ["exposure_upb", "orig_upb_sum", "prepaid_upb", "finite_age_sum", "finite_age_count", "loan_count"]}
        frozen_ingest = output / "ingest_source.py"
        frozen_ingest.write_bytes((ROOT / "hazard/ingest.py").read_bytes())
        report["ingest_sha256"] = hashlib.sha256(frozen_ingest.read_bytes()).hexdigest()
        report["replays"] = {}
        if replay:
            for kind in ["fixed", "legacy"]:
                print(f"Starting isolated {kind} production replay", flush=True)
                result = monitored_replay(orig, perf, output, kind, frozen_ingest)
                if result["status"] == "completed":
                    result["reference_comparison"] = compare_reference(cells, Path(result["output"]))
                report["replays"][kind] = result
                write_json(output / f"{kind}_comparison.json", result)
                if result["stopped_reason"]:
                    break
        report["status"] = "streaming_audit_completed"
        return report
    except Exception as exc:
        report["status"] = "stopped_error"
        report["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        report["finished_utc"] = datetime.now(timezone.utc).isoformat()
        report["resources"] = check_resources(output)
        report["source_metadata_after_reads"] = {"origination": metadata(orig), "performance": metadata(perf)}
        report["source_sizes_mtimes_unchanged"] = all(
            report["source_metadata_after_reads"][kind][k] == before[kind][k]
            for kind in before for k in ["size", "mtime_ns"])
        write_json(output / "results.json", report)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orig",type=Path,default=SOURCE/"orig_2017Q1.txt")
    parser.add_argument("--perf",type=Path,default=SOURCE/"perf_2017Q1.txt")
    parser.add_argument("--output",type=Path,default=OUTPUT)
    parser.add_argument("--no-replay",action="store_true")
    parser.add_argument("--worker",choices=["fixed","legacy"])
    parser.add_argument("--frozen-ingest",type=Path)
    args=parser.parse_args()
    if args.worker:
        replay_worker(args.orig,args.perf,args.output,args.worker,args.frozen_ingest)
    else:
        result=run(args.orig,args.perf,args.output,not args.no_replay)
        print(json.dumps({"status":result["status"],"output":str(args.output)},indent=2))


if __name__ == "__main__":
    main()
