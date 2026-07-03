"""
Extract Freddie Mac Standard Dataset historical zips into hazard/data/raw/.

Source layout (annual zip):
  historical_data_2020.zip
    └── historical_data_2020Q1.zip
          ├── historical_data_2020Q1.txt      (origination)
          └── historical_data_time_2020Q1.txt (performance)

Output layout (ingest-compatible):
  hazard/data/raw/orig_2020Q1.txt
  hazard/data/raw/perf_2020Q1.txt
"""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from config import HAZARD_DIR, RAW_DIR, VINTAGE_YEARS

# Repo-root folder where user placed annual historical zips
HISTORIC_FREDDIE_DIR = HAZARD_DIR.parent / "Historic Freddie"


def _quarterly_tags_in_annual(annual_zip: Path) -> list[str]:
    with zipfile.ZipFile(annual_zip) as zf:
        tags = []
        for name in zf.namelist():
            if not name.endswith(".zip"):
                continue
            stem = Path(name).stem  # historical_data_2020Q1
            tag = stem.replace("historical_data_", "")
            tags.append(tag)
        return sorted(tags)


def extract_quarter(
    annual_zip: Path,
    tag: str,
    dest_dir: Path,
    overwrite: bool = False,
) -> tuple[Path, Path] | None:
    """Extract one quarter from an annual zip into orig_/perf_ txt files."""
    orig_out = dest_dir / f"orig_{tag}.txt"
    perf_out = dest_dir / f"perf_{tag}.txt"
    if orig_out.exists() and perf_out.exists() and not overwrite:
        return orig_out, perf_out

    inner_name = f"historical_data_{tag}.zip"
    with zipfile.ZipFile(annual_zip) as annual:
        if inner_name not in annual.namelist():
            print(f"  WARNING: {inner_name} not in {annual_zip.name}")
            return None
        with tempfile.TemporaryDirectory(prefix="freddie_") as tmp:
            tmp_path = Path(tmp)
            annual.extract(inner_name, tmp)
            with zipfile.ZipFile(tmp_path / inner_name) as quarterly:
                quarterly.extractall(tmp)
            orig_src = tmp_path / f"historical_data_{tag}.txt"
            perf_src = tmp_path / f"historical_data_time_{tag}.txt"
            if not orig_src.exists() or not perf_src.exists():
                print(f"  WARNING: missing orig/perf txt inside {inner_name}")
                return None
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(orig_src), str(orig_out))
            shutil.move(str(perf_src), str(perf_out))
    print(f"  Extracted {tag} → {orig_out.name}, {perf_out.name}")
    return orig_out, perf_out


def extract_historic_freddie(
    source_dir: Path = HISTORIC_FREDDIE_DIR,
    dest_dir: Path = RAW_DIR,
    years: list[int] | None = None,
    overwrite: bool = False,
) -> list[tuple[Path, Path]]:
    """Extract all quarterly orig/perf pairs from annual historical zips."""
    years = years or VINTAGE_YEARS
    if not source_dir.exists():
        print(f"No Historic Freddie folder at {source_dir}")
        return []

    pairs: list[tuple[Path, Path]] = []
    for year in years:
        annual = source_dir / f"historical_data_{year}.zip"
        if not annual.exists():
            print(f"Skipping {year}: {annual.name} not found")
            continue
        print(f"Processing {annual.name} …")
        for tag in _quarterly_tags_in_annual(annual):
            result = extract_quarter(annual, tag, dest_dir, overwrite=overwrite)
            if result:
                pairs.append(result)
    print(f"Ready: {len(pairs)} orig/perf pair(s) in {dest_dir}")
    return pairs


def ensure_raw_files(
    source_dir: Path = HISTORIC_FREDDIE_DIR,
    dest_dir: Path = RAW_DIR,
    require_complete: bool = False,
) -> bool:
    """Extract historic zips if source exists; use partial extracts when disk-limited."""
    from ingest import discover_raw_files

    if not source_dir.exists():
        return False

    existing = discover_raw_files(dest_dir)
    if existing:
        expected = sum(
            1 for y in VINTAGE_YEARS
            if (source_dir / f"historical_data_{y}.zip").exists()
        ) * 4
        if len(existing) >= expected and expected > 0:
            print(f"Freddie raw already prepared ({len(existing)} pairs).")
            return True
        if not require_complete:
            print(
                f"Using {len(existing)} Freddie orig/perf pair(s) "
                f"(partial extract; expected {expected})."
            )
            return True

    print(f"Preparing Freddie files from {source_dir} …")
    try:
        pairs = extract_historic_freddie(source_dir, dest_dir)
    except OSError as exc:
        existing = discover_raw_files(dest_dir)
        if existing:
            print(f"Extract stopped ({exc}); continuing with {len(existing)} pair(s).")
            return True
        raise
    return len(pairs) > 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract Historic Freddie zips to hazard/data/raw/")
    parser.add_argument("--overwrite", action="store_true", help="Re-extract even if txt exists")
    parser.add_argument("--years", nargs="*", type=int, default=None)
    args = parser.parse_args()
    extract_historic_freddie(
        years=args.years,
        overwrite=args.overwrite,
    )
