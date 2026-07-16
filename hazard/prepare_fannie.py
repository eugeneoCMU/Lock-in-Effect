"""
Adapt Fannie Mae Single-Family Loan Performance (SF LPH) data into the
Freddie-shaped orig_/perf_ layout that hazard/ingest.py already consumes.

WHY SYNTHESIZE orig_/perf_ PAIRS (option a)
-------------------------------------------
Fannie ships ONE 108-field record layout with the static origination attributes
repeated on every monthly row (there is no separate origination file). Freddie
ships TWO 32-field pipe-delimited headerless files per quarter joined on
loan_sequence_number. By deduping Fannie's static fields into a synthesized
orig_<TAG>.txt and projecting its dynamic fields into a synthesized
perf_<TAG>.txt - both Freddie-CODED, not merely Freddie-shaped - the audited
ingest.py path is reused UNCHANGED and the estimator stays byte-for-byte
identical across agencies, which is the entire point of the external
replication. No edit to hazard/schema.py or hazard/ingest.py is required.

Three Fannie->Freddie encodings are applied HERE (never in ingest.py), because
ingest.py's helpers are Freddie-format-specific and fail SILENTLY on native
Fannie values:
  1. loan_sequence_number is SYNTHESIZED as f"F{yy}Q{q}{loan_identifier}" from
     Origination Date (field 14, MMYYYY). ingest._vintage_from_seq slices
     chars 1-2 for the vintage year, so this makes the vintage correct BY
     CONSTRUCTION. Fannie's real Loan Identifier (field 2) carries no vintage
     (glossary: "does not correspond to other mortgage loan identifiers") and
     would otherwise slice to garbage (e.g. "100012345678" -> vintage 2000).
  2. Dates are transcoded MMYYYY -> YYYYMM. ingest.py parses reporting_period
     with "%Y%m"; Fannie dates are MMYYYY (glossary fields 3/14/15/19/45...).
  3. Delinquency status is translated from Fannie's X(2) coding ("00","01",
     "99","XX") to Freddie's unpadded single-char coding that
     ingest._map_servicer_state expects. (Affects only the secondary Markov
     mode_state; the headline hazard reads is_prepay, i.e. ZBC == "01".)

The synthesized perf file is written SORTED by (loan_sequence_number,
reporting_period). This is BEST-EFFORT parity with Freddie, not a guarantee:
ingest.py computes prev_upb as `current_upb.shift(1).over(loan)` on the output
of an inner join (perf.join(orig)), and Polars does not guarantee an inner join
preserves left-frame row order. prev_upb IS the estimator's dependent variable
(prepaid_upb -> hazard events), so this is the same latent ordering dependence
Freddie already relies on, not a solved problem. Fannie stages field 46 (UPB at
the Time of Removal) as an ORDER-INDEPENDENT cross-check on prepaid_upb; a
guaranteed fix would add an explicit sort inside ingest.py (out of scope, would
touch the frozen Freddie path). See FIRST-DOWNLOAD CHECKLIST.

SAFETY / SCOPE (additive)
-------------------------
  * No network and no Fannie credentials are touched at import time
    (common/fannie_lph.py is imported lazily inside the fetching functions).
    NB: the top-level `from config import ...` transitively reads the FRED key
    (config.py calls get_fred_api_key()), a credential-FILE read shared with the
    existing Freddie path -- no network, and it already succeeds in this repo
    (a .env with FRED_API_KEY is present). No Fannie data is read at import.
  * Fannie staged pairs default to a DEDICATED subdirectory (FANNIE_RAW_DIR =
    RAW_DIR/"fannie"). ingest.discover_raw_files globs RAW_DIR non-recursively,
    so Fannie files never pool with Freddie's, and the Freddie panel is never
    overwritten (Fannie writes its own FANNIE_PANEL_PATH). load_or_build_panel
    is never called (it triggers the Freddie Google-Drive fallback).
  * Everything the glossary does NOT settle is a PARAMETER with a documented
    default, never a hardcoded assumption, and the physical column count is
    ASSERTED at stage time (a wrong delimiter or field count fails loudly
    rather than silently shifting every positional name).

RESOLVED from Fannie's public FAQ ("SF Loan Performance Dataset FAQs",
capitalmarkets.fanniemae.com/.../sf-loan-performance-dataset-faqs.pdf):
  * File format: CSV, from the October 2020 release (FAQ #20). DEFAULT_SEPARATOR
    is "," accordingly, BUT several fields (Seller/Servicer Name, X(50)) can
    contain commas, and agency ".csv" files are sometimes pipe-delimited, so the
    separator stays a parameter and the column-count assertion is the real
    guard. Confirm the delimiter on the first real file.
  * No header row (FAQ #15: "the files do not include column headings").
    DEFAULT_HAS_HEADER = False.
  * One file per ACQUISITION quarter, origination + performance combined, since
    the October 2020 release (FAQ #11); so the quarterly endpoint slices by
    acquisition quarter and one staged tag == one vintage quarter.
  * Files arrive as ZIP (FAQ #4); fetch_lph_native_files unzips before staging.

UNRESOLVED (glossary + FAQ silent; confirm from one real download; see the
FIRST-DOWNLOAD CHECKLIST doc):
  * n_expected_cols: whether a real SF LPH file physically emits all 108
    positions or only the ~70 SF-applicable ones. Default 108; ASSERTED, so a
    mismatch aborts rather than corrupts.
  * exact on-disk padding of ZBC field 44 (declared X(3); "01" vs "001" vs
    " 01") -- normalized by stripping, but confirm "01" matches is_prepay.
  * six-month privacy mask rendering of field 12 (blank / 0 / sentinel).
  * whether Fannie emits post-removal monthly rows (affects loan counts and the
    Table-2 disclosures, NOT the estimator).
  * ZBC 06/16/96 exact trigger semantics (censoring vs disguised credit event).

PROVENANCE
----------
Fannie glossary (fields, codes, formats): (c) 2023 Fannie Mae, 6/26/2023, 108 fields.
https://capitalmarkets.fanniemae.com/sites/capmrkt/files/2023-06/crt-file-layout-and-glossary.pdf
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import polars as pl

from config import DATA_DIR, RAW_DIR
from schema import ORIG_COLS, PERF_COLS
from schema_fannie import (
    FANNIE_COLS,
    FANNIE_COLS_WIRE,
    FANNIE_ZB_LEGACY_CREDIT_EVENT,
)

# Dedicated Fannie staging locations (kept out of the Freddie glob / panel path).
FANNIE_RAW_DIR = RAW_DIR / "fannie"                       # synthesized orig_/perf_
FANNIE_NATIVE_DIR = DATA_DIR / "fannie_native"            # downloaded native LPH
FANNIE_PANEL_PATH = DATA_DIR / "cohort_month_panel_fannie.parquet"

# Defaults CONFIRMED against the real 2019Q1 download (2026-07-15): the wire
# format is PIPE-delimited (the FAQ's "CSV format" and the .csv inner filename
# notwithstanding — Seller/Servicer Name fields contain commas), headerless,
# 113 physical columns (glossary 108 + 5 appended; schema_fannie.FANNIE_COLS_WIRE).
# The column count is asserted at scan time so a wrong delimiter fails loudly.
DEFAULT_SEPARATOR = "|"
DEFAULT_HAS_HEADER = False       # FAQ #15: files carry no column headings
DEFAULT_N_COLS = len(FANNIE_COLS_WIRE)   # 113

# Natives at or above this size are staged via the streaming (low-memory)
# path: the eager collect() of the 2020Q2 refi-wave file (17 GB native,
# ~135M rows) is a deterministic OOM kill on a 16 GiB machine. Threshold
# sits above the largest eager-validated quarter (2017Q1, 3.6 GB) with
# margin.
LOW_MEMORY_NATIVE_BYTES = 5 * 2**30

# Quarter -> Fannie API literal
_Quarters = ("Q1", "Q2", "Q3", "Q4")


# ---------------------------------------------------------------------------
# Fannie -> Freddie value transforms (Polars expressions). Applied at stage
# time so ingest.py never sees a native Fannie encoding.
# ---------------------------------------------------------------------------
def _mmyyyy_to_yyyymm(col: str) -> pl.Expr:
    """MMYYYY (Fannie DATE) -> YYYYMM (Freddie / ingest.py '%Y%m'). Null-safe."""
    src = pl.col(col).str.strip_chars()
    return (
        pl.when(src.str.len_chars() == 6)
        .then(src.str.slice(2, 4) + src.str.slice(0, 2))
        .otherwise(None)
    )


def _synthesized_seq() -> pl.Expr:
    """
    Freddie-shaped loan_sequence_number: 'F' + YY + 'Q' + quarter + loan_identifier,
    with YY/quarter taken from Origination Date (field 14, MMYYYY). Makes
    ingest._vintage_from_seq (slice chars 1-2, +2000) correct by construction.
    """
    od = pl.col("origination_date").str.strip_chars()
    yy = od.str.slice(4, 2)                       # last two digits of YYYY
    mm = od.str.slice(0, 2).cast(pl.Int64, strict=False)
    q = ((mm - 1) // 3 + 1).cast(pl.Utf8)
    return pl.concat_str([
        pl.lit("F"), yy, pl.lit("Q"), q,
        pl.col("loan_identifier").str.strip_chars(),
    ])


def _translate_delinquency() -> pl.Expr:
    """
    Fannie field 40 (X(2): '00','01',...,'99','XX', blank-after-removal) ->
    Freddie unpadded codes consumed by ingest._map_servicer_state
    ('0','1','2','3'..'9'). Any count >= 3 months collapses to '3' (the D90+
    branch); 'XX'/blank -> '' (falls through to Current, as for a removed loan).
    Robust to either '0' or '00' padding (field-40 padding is UNRESOLVED).
    """
    raw = pl.col("delinquency_status").str.strip_chars()
    n = raw.cast(pl.Int64, strict=False)
    return (
        pl.when(raw.is_in(["", "XX"]) | n.is_null()).then(pl.lit(""))
        .when(n == 0).then(pl.lit("0"))
        .when(n == 1).then(pl.lit("1"))
        .when(n == 2).then(pl.lit("2"))
        .otherwise(pl.lit("3"))  # 3+ months delinquent -> D90+ bucket
    )


def _normalize_zbc() -> pl.Expr:
    """Field 44 is declared X(3) though all values are 2 chars - strip padding
    so ingest.py's exact `== '01'` match fires regardless of ' 01' / '01 '.
    (Real-file check 2026-07-15: values ARE two-digit: 01/02/06/09/16.)"""
    return pl.col("zero_balance_code").str.strip_chars()


def _unmask_early_upb() -> pl.Expr:
    """
    Fannie masks Current Actual UPB (field 12) for a loan's first six months
    "due to borrower privacy considerations" (glossary), and the real file
    renders the mask as 0.00, NOT blank (verified 2026-07-15: e.g. a loan_age-3
    row with original UPB 324000.00 carries current_upb '0.00' and no ZBC).
    Left as-is, those rows enter ingest.py with zero exposure and, worse, a
    genuine prepay in month 7 would compute prepaid_upb from a masked-zero
    prev_upb. IMPUTE original_upb for masked rows: current_upb == 0, no
    zero-balance code, loan age <= 6 (a genuine payoff carries ZBC in the same
    month it zeroes, verified, so it is excluded). Amortization over the first
    six months is negligible relative to the mask error. Controlled by
    stage_native_file(unmask_early_upb=...), default True.
    """
    upb = pl.col("current_upb").cast(pl.Float64, strict=False)
    age = pl.col("loan_age").cast(pl.Int64, strict=False)
    masked = (
        (upb == 0.0)
        & pl.col("zero_balance_code").str.strip_chars().is_null()
        & (age <= 6)
    )
    return pl.when(masked).then(pl.col("original_upb")).otherwise(pl.col("current_upb"))


# ---------------------------------------------------------------------------
# Native SF LPH parse + split into Freddie-shaped orig_/perf_ files
# ---------------------------------------------------------------------------
def scan_native_lph(
    path: Path,
    separator: str = DEFAULT_SEPARATOR,
    has_header: bool = DEFAULT_HAS_HEADER,
    n_cols: int = DEFAULT_N_COLS,
    names: list[str] | None = None,
) -> pl.LazyFrame:
    """
    Lazily scan a native Fannie SF LPH file as all-Utf8 with FANNIE_COLS names.

    The physical column count is CHECKED against n_cols before names are
    applied, so a wrong delimiter (too few OR too many columns) aborts with a
    friendly message rather than silently shifting every positional name or
    raising a raw polars error.

    POSITIONAL-MAP SAFETY: FANNIE_COLS is the full 108-in-order glossary layout,
    so the built-in map is valid ONLY for a file that emits all 108 positions.
    If an SF LPH file emits only the ~70 SF-applicable positions, they are a
    non-contiguous SUBSET (e.g. field 11 and 47-48 are dropped), NOT a prefix,
    so FANNIE_COLS[:70] would mis-map. This function therefore refuses n_cols
    != 108 unless the caller passes the actual ordered `names` for that file
    (which only a real download can establish). separator/has_header/n_cols are
    parameters (see module docstring).
    """
    if names is None:
        if n_cols == len(FANNIE_COLS_WIRE):
            names = FANNIE_COLS_WIRE      # verified real wire layout (113)
        elif n_cols == len(FANNIE_COLS):
            names = FANNIE_COLS           # bare glossary layout (108)
        else:
            raise ValueError(
                f"n_cols={n_cols} matches neither the verified wire layout "
                f"({len(FANNIE_COLS_WIRE)}) nor the glossary layout "
                f"({len(FANNIE_COLS)}). A file with a different width emits an "
                "unknown variant, so pass the actual ordered column names via "
                "`names=` (established from a real download) rather than "
                "relying on a prefix map."
            )
    names = names[:n_cols]

    # Scan first WITHOUT forcing names so we can measure the true width; polars
    # auto-names columns, and assigning names to a wrong-width frame would
    # otherwise raise an opaque ShapeError (too few) or silently number the
    # overflow (too many).
    raw = pl.scan_csv(
        path,
        separator=separator,
        has_header=has_header,
        infer_schema_length=0,       # all Utf8, exactly like ingest.py
        truncate_ragged_lines=True,
    )
    width = raw.limit(1).collect().width
    if width != n_cols:
        raise ValueError(
            f"{path.name}: parsed {width} columns, expected {n_cols} "
            f"(separator={separator!r}, has_header={has_header}). A wrong "
            "delimiter or an SF-LPH file that omits CAS/CIRT-only positions "
            "would land here. Confirm the delimiter and column count on this "
            "file, then pass --separator/--n-cols/--names. Refusing to scan."
        )
    return raw.rename(dict(zip(raw.collect_schema().names(), names)))


def _blank_frame_columns(cols: list[str], filled: dict[str, pl.Expr]) -> list[pl.Expr]:
    """Build the full ordered column list, using `filled` exprs where present
    and an empty-string literal elsewhere. All outputs are Utf8."""
    out: list[pl.Expr] = []
    for name in cols:
        if name in filled:
            out.append(filled[name].cast(pl.Utf8).fill_null("").alias(name))
        else:
            out.append(pl.lit("").alias(name))
    return out


def stage_native_file(
    native_path: Path,
    tag: str,
    dest_dir: Path = FANNIE_RAW_DIR,
    separator: str = DEFAULT_SEPARATOR,
    has_header: bool = DEFAULT_HAS_HEADER,
    n_cols: int = DEFAULT_N_COLS,
    overwrite: bool = False,
    validate_legacy_zbc: bool = True,
    unmask_early_upb: bool = True,
    low_memory: bool | None = None,
    delete_native_after_scan: bool = False,
) -> tuple[Path, Path]:
    """
    Split one native Fannie SF LPH file into Freddie-shaped orig_<TAG>.txt /
    perf_<TAG>.txt (32 cols each, pipe-delimited, headerless) under dest_dir.

    Origination fields are deduped to one row per loan; dynamic fields are kept
    per row. loan_sequence_number is synthesized on BOTH so the inner join in
    ingest.build_panel_from_files matches. The perf file is written sorted by
    (loan_sequence_number, reporting_period).

    low_memory (default: auto by native size, LOW_MEMORY_NATIVE_BYTES) stages
    via streaming sinks instead of eager collect(): perf rows sink UNSORTED to
    a temp file, then an on-disk streaming sort rewrites them in the same
    (loan_sequence_number, reporting_period) order — that key is unique per
    row, so the ordering is total and the perf bytes are identical to the
    eager path's (gated by tests/test_prepare_fannie_low_memory.py). The orig
    file's streaming unique does not preserve first-occurrence order, so it is
    sorted by loan_sequence_number instead (deterministic; values are static
    per loan and downstream use is key-based, so only row order differs from
    the eager path). delete_native_after_scan frees the native as soon as the
    last pass over it completes — for a 17 GB native the sort's disk spill
    plus output would otherwise not fit alongside it.
    """
    orig_out = dest_dir / f"orig_{tag}.txt"
    perf_out = dest_dir / f"perf_{tag}.txt"
    if orig_out.exists() and perf_out.exists() and not overwrite:
        return orig_out, perf_out
    if low_memory is None:
        low_memory = native_path.stat().st_size >= LOW_MEMORY_NATIVE_BYTES

    dest_dir.mkdir(parents=True, exist_ok=True)
    # scan_native_lph asserts the physical width == n_cols before naming.
    native = scan_native_lph(native_path, separator, has_header, n_cols)

    # Common synthesized/transcoded columns needed by both outputs.
    native = native.with_columns([
        _synthesized_seq().alias("loan_sequence_number"),
        _mmyyyy_to_yyyymm("reporting_period").alias("reporting_period_yyyymm"),
    ])

    if validate_legacy_zbc:
        # 97/98 are glossary-scoped to CAS deals <= 2015-C03 and must not appear
        # in an SF LPH file. Assert their absence rather than silently bucket.
        legacy = (
            native.select(_normalize_zbc().alias("zbc"))
            .filter(pl.col("zbc").is_in(list(FANNIE_ZB_LEGACY_CREDIT_EVENT)))
            .head(1)
            .collect()
        )
        if legacy.height:
            raise ValueError(
                f"{native_path.name}: legacy ZBC {FANNIE_ZB_LEGACY_CREDIT_EVENT} "
                "found in an SF LPH file (glossary scopes these to CAS deals "
                "<= 2015-C03). Aborting; confirm the source dataset."
            )

    # ---- orig_<TAG>.txt : dedupe static fields, one row per loan ----
    orig_filled = {
        "credit_score": pl.col("credit_score"),                       # field 24
        "first_payment_date": _mmyyyy_to_yyyymm("first_payment_date"),  # field 15
        "original_upb": pl.col("original_upb"),                       # field 10
        "original_ltv": pl.col("original_ltv"),                       # field 20
        "original_interest_rate": pl.col("original_interest_rate"),   # field 8
        "amortization_type": pl.col("amortization_type"),             # field 35
        "property_state": pl.col("property_state"),                   # field 31
        "loan_sequence_number": pl.col("loan_sequence_number"),       # synthesized
        "original_loan_term": pl.col("original_loan_term"),           # field 13
    }
    orig_lazy = (
        native
        .unique(subset=["loan_identifier"], keep="first")
        .select(_blank_frame_columns(ORIG_COLS, orig_filled))
    )
    if low_memory:
        orig_lazy.sort("loan_sequence_number").sink_csv(
            orig_out, separator="|", include_header=False
        )
        n_loans_staged = int(
            pl.scan_csv(orig_out, separator="|", has_header=False,
                        infer_schema_length=0)
            .select(pl.len()).collect().item()
        )
    else:
        orig = orig_lazy.collect()
        orig.write_csv(orig_out, separator="|", include_header=False)
        n_loans_staged = orig.height

    # ---- perf_<TAG>.txt : per-row dynamic fields, sorted for shift(1) ----
    perf_filled = {
        "loan_sequence_number": pl.col("loan_sequence_number"),       # synthesized
        "reporting_period": pl.col("reporting_period_yyyymm"),        # field 3 (YYYYMM)
        # field 12, with the first-six-months privacy mask (renders as 0.00)
        # imputed back to original_upb unless disabled.
        "current_upb": (_unmask_early_upb() if unmask_early_upb
                        else pl.col("current_upb")),
        "delinquency_status": _translate_delinquency(),              # field 40
        "loan_age": pl.col("loan_age"),                               # field 16
        "zero_balance_code": _normalize_zbc(),                        # field 44
        # field 46: staged (ingest.py does not read it, matching Freddie) so the
        # order-independent prepaid_upb cross-check in the checklist is available.
        "zero_balance_removal_upb": pl.col("zero_balance_removal_upb"),
        "borrower_assistance": pl.col("borrower_assistance"),         # field 102
    }
    if low_memory:
        # Pass 1: final-shape rows, UNSORTED, streamed to a temp file (the
        # staged reporting_period column IS the yyyymm sort key, so no helper
        # column is needed on the rescan).
        tmp_unsorted = perf_out.with_suffix(".unsorted.tmp")
        (
            native
            .select(_blank_frame_columns(PERF_COLS, perf_filled))
            .sink_csv(tmp_unsorted, separator="|", include_header=False)
        )
        if delete_native_after_scan:
            native_path.unlink()  # last pass over the native just completed
        # Pass 2: on-disk streaming sort into the final file. The key is
        # unique per row (one row per loan-month), so the order is total.
        (
            pl.scan_csv(tmp_unsorted, separator="|", has_header=False,
                        new_columns=PERF_COLS, infer_schema_length=0)
            .with_columns(pl.all().fill_null(""))
            .sort(["loan_sequence_number", "reporting_period"])
            .sink_csv(perf_out, separator="|", include_header=False)
        )
        tmp_unsorted.unlink()
        n_rows_staged = int(
            pl.scan_csv(perf_out, separator="|", has_header=False,
                        infer_schema_length=0)
            .select(pl.len()).collect().item()
        )
    else:
        perf = (
            native
            .select(
                _blank_frame_columns(PERF_COLS, perf_filled)
                + [pl.col("reporting_period_yyyymm")]
            )
            .sort(["loan_sequence_number", "reporting_period_yyyymm"])
            .select(PERF_COLS)  # drop the sort helper; emit exactly 32 cols
            .collect()
        )
        perf.write_csv(perf_out, separator="|", include_header=False)
        n_rows_staged = perf.height
        if delete_native_after_scan:
            native_path.unlink()

    print(f"  Staged {tag}: {orig_out.name} ({n_loans_staged:,} loans), "
          f"{perf_out.name} ({n_rows_staged:,} rows)"
          + ("  [low-memory path]" if low_memory else ""))
    return orig_out, perf_out


# ---------------------------------------------------------------------------
# Acquisition of the native file(s) via common/fannie_lph.py (network-bound;
# imported lazily so this module stays import-safe)
# ---------------------------------------------------------------------------
def fetch_lph_native_files(
    years: Iterable[int],
    quarters: Iterable[str] = _Quarters,
    staging_dir: Path = FANNIE_NATIVE_DIR,
    overwrite: bool = False,
) -> list[tuple[str, Path]]:
    """
    Download signed SF LPH file(s) for the given years/quarters into staging_dir.

    Returns [(tag, native_path), ...] with tag = f"FNMA{year}{quarter}".
    NOTE: whether the quarterly endpoint slices by acquisition or activity
    quarter is UNRESOLVED (see docstring); the tag records the endpoint params,
    not a verified vintage.
    """
    import zipfile

    from common.fannie_lph import download_signed_file, get_lph_urls_for_quarter

    staging_dir.mkdir(parents=True, exist_ok=True)
    out: list[tuple[str, Path]] = []
    for year in years:
        for quarter in quarters:
            entries = get_lph_urls_for_quarter(year, quarter)  # network
            for i, entry in enumerate(entries):
                s3_uri = entry.get("s3Uri")
                if not s3_uri:
                    continue
                suffix = f"_{i}" if len(entries) > 1 else ""
                tag = f"FNMA{year}{quarter}{suffix}"
                extracted = staging_dir / f"lph_{tag}.txt"
                if extracted.exists() and not overwrite:
                    print(f"  Have {extracted.name}")
                    out.append((tag, extracted))
                    continue
                # FAQ #4: files arrive as ZIP. Download the archive, then
                # extract its single data member to a stable lph_<TAG>.txt.
                archive = staging_dir / f"lph_{tag}.zip"
                print(f"  Downloading {tag} …")
                download_signed_file(s3_uri, archive)
                if zipfile.is_zipfile(archive):
                    with zipfile.ZipFile(archive) as zf:
                        members = [m for m in zf.namelist() if not m.endswith("/")]
                        if len(members) != 1:
                            raise ValueError(
                                f"{archive.name}: expected one data member, "
                                f"found {len(members)}: {members}. Confirm the "
                                "archive layout before staging."
                            )
                        with zf.open(members[0]) as src, open(extracted, "wb") as dst:
                            while chunk := src.read(1 << 20):
                                dst.write(chunk)
                    print(f"    Extracted {members[0]} -> {extracted.name}")
                else:
                    # Not a zip after all (delivery format is a confirm-item):
                    # treat the download as the raw data file.
                    archive.rename(extracted)
                out.append((tag, extracted))
    return out


def prepare_fannie(
    years: Iterable[int],
    quarters: Iterable[str] = _Quarters,
    native_dir: Path = FANNIE_NATIVE_DIR,
    dest_dir: Path = FANNIE_RAW_DIR,
    separator: str = DEFAULT_SEPARATOR,
    has_header: bool = DEFAULT_HAS_HEADER,
    n_cols: int = DEFAULT_N_COLS,
    overwrite: bool = False,
) -> list[tuple[Path, Path]]:
    """Download native SF LPH files and stage them into Freddie-shaped pairs."""
    native = fetch_lph_native_files(years, quarters, native_dir, overwrite=overwrite)
    pairs: list[tuple[Path, Path]] = []
    for tag, native_path in native:
        pairs.append(stage_native_file(
            native_path, tag, dest_dir,
            separator=separator, has_header=has_header, n_cols=n_cols,
            overwrite=overwrite,
        ))
    print(f"Ready: {len(pairs)} Fannie orig/perf pair(s) in {dest_dir}")
    return pairs


def build_fannie_panel(
    pairs: Iterable[tuple[Path, Path]] | None = None,
    dest_dir: Path = FANNIE_RAW_DIR,
    output: Path = FANNIE_PANEL_PATH,
) -> "pl.DataFrame":
    """
    Aggregate staged Fannie pairs into a cohort-month panel using ingest.py's
    build_panel_from_files UNCHANGED, writing to a Fannie-specific panel path
    (never the frozen Freddie PANEL_PATH). If `pairs` is None, discover already
    staged orig_/perf_ pairs under dest_dir.
    """
    from ingest import build_panel_from_files  # lazy: pulls config/common

    if pairs is None:
        pairs = []
        for o in sorted(dest_dir.glob("orig_*.txt")):
            p = dest_dir / f"perf_{o.stem.replace('orig_', '')}.txt"
            if p.exists():
                pairs.append((o, p))
    pairs = list(pairs)
    if not pairs:
        raise FileNotFoundError(f"No staged Fannie orig/perf pairs under {dest_dir}")
    return build_panel_from_files(pairs, output=output)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Stage Fannie SF LPH data into Freddie-shaped orig_/perf_ pairs."
    )
    parser.add_argument("--years", nargs="+", type=int, required=True,
                        help="Target vintage/activity years, e.g. 2020 2021")
    parser.add_argument("--quarters", nargs="+", default=list(_Quarters),
                        help="Quarters to pull (Q1 Q2 Q3 Q4 or All)")
    parser.add_argument("--separator", default=DEFAULT_SEPARATOR,
                        help="Native file delimiter (UNRESOLVED; default '|')")
    parser.add_argument("--has-header", action="store_true",
                        help="Native file carries a header row (UNRESOLVED; default no)")
    parser.add_argument("--n-cols", type=int, default=DEFAULT_N_COLS,
                        help="Physical column count of the native file (default 108)")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--build", action="store_true",
                        help="Also aggregate staged pairs into the Fannie panel")
    args = parser.parse_args()

    staged = prepare_fannie(
        years=args.years,
        quarters=args.quarters,
        separator=args.separator,
        has_header=args.has_header,
        n_cols=args.n_cols,
        overwrite=args.overwrite,
    )
    if args.build:
        build_fannie_panel(staged)
