"""
High-level data loading from Google Drive with local caching.

Provides convenient functions to load Freddie Mac and SOMA datasets stored
in a Google Drive folder. Handles caching, pipe-delimited format detection,
and environment variable configuration.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

import pandas as pd

from common.google_drive import authenticate_service_account, get_or_download


@lru_cache(maxsize=1)
def _get_data_folder_id() -> str:
    """Resolve Google Drive folder ID for data."""
    folder_id = os.environ.get("DATA_FOLDER_ID")
    if not folder_id:
        raise RuntimeError(
            "DATA_FOLDER_ID environment variable not set. "
            "Set it in .env or as an environment variable with the Google Drive folder ID."
        )
    return folder_id


@lru_cache(maxsize=1)
def _get_cache_dir() -> Path:
    """Get cache directory, creating it if necessary."""
    cache_dir = Path(os.environ.get("DATA_CACHE_DIR", "./data/cache"))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _load_pipe_delimited(file_path: Path, **pd_kwargs) -> pd.DataFrame:
    """Load a pipe-delimited text file into a DataFrame."""
    return pd.read_csv(file_path, sep="|", **pd_kwargs)


def load_freddie_data(
    filename: str = "freddie_data.txt",
    cache_dir: Optional[Path | str] = None,
    force_refresh: bool = False,
    **pd_kwargs,
) -> pd.DataFrame:
    """
    Load Freddie Mac loan-level data from Google Drive.

    Args:
        filename: Name of the file in Google Drive (default: freddie_data.txt)
        cache_dir: Override cache directory (default: from DATA_CACHE_DIR env var)
        force_refresh: Re-download even if cached (default: False)
        **pd_kwargs: Additional arguments passed to pd.read_csv()

    Returns:
        DataFrame with Freddie Mac data
    """
    if cache_dir is None:
        cache_dir = _get_cache_dir()
    else:
        cache_dir = Path(cache_dir)

    cache_path = cache_dir / filename

    # Delete cached file if force_refresh is True
    if force_refresh and cache_path.is_file():
        cache_path.unlink()

    # Download if not cached
    if not cache_path.is_file():
        service = authenticate_service_account()
        folder_id = _get_data_folder_id()
        cache_path = get_or_download(service, folder_id, filename, cache_dir)

    return _load_pipe_delimited(cache_path, **pd_kwargs)


def load_soma_data(
    filename: str = "soma_holdings.txt",
    cache_dir: Optional[Path | str] = None,
    force_refresh: bool = False,
    **pd_kwargs,
) -> pd.DataFrame:
    """
    Load SOMA (System Open Market Account) holdings data from Google Drive.

    Args:
        filename: Name of the file in Google Drive (default: soma_holdings.txt)
        cache_dir: Override cache directory (default: from DATA_CACHE_DIR env var)
        force_refresh: Re-download even if cached (default: False)
        **pd_kwargs: Additional arguments passed to pd.read_csv()

    Returns:
        DataFrame with SOMA holdings data
    """
    if cache_dir is None:
        cache_dir = _get_cache_dir()
    else:
        cache_dir = Path(cache_dir)

    cache_path = cache_dir / filename

    # Delete cached file if force_refresh is True
    if force_refresh and cache_path.is_file():
        cache_path.unlink()

    # Download if not cached
    if not cache_path.is_file():
        service = authenticate_service_account()
        folder_id = _get_data_folder_id()
        cache_path = get_or_download(service, folder_id, filename, cache_dir)

    return _load_pipe_delimited(cache_path, **pd_kwargs)


def ensure_raw_freddie_files(
    years: list[int] | list[str],
    cache_dir: Optional[Path | str] = None,
    force_refresh: bool = False,
) -> list[tuple[Path, Path]]:
    """
    Ensure Freddie Mac raw file pairs (orig_*.txt, perf_*.txt) are available.
    Downloads from Google Drive if not present locally.

    Args:
        years: List of years or quarters to download (e.g., [2020, 2021] or ['2020', '2020Q1'])
        cache_dir: Override cache directory (default: from DATA_CACHE_DIR env var)
        force_refresh: Re-download even if cached (default: False)

    Returns:
        List of (orig_path, perf_path) tuples for available files
    """
    if cache_dir is None:
        cache_dir = _get_cache_dir()
    else:
        cache_dir = Path(cache_dir)

    cache_dir.mkdir(parents=True, exist_ok=True)
    service = authenticate_service_account()
    folder_id = _get_data_folder_id()

    pairs = []
    for year in years:
        year_str = str(year)
        # Try patterns: orig_2020.txt / perf_2020.txt AND orig_2020Q1.txt / perf_2020Q1.txt
        for suffix in [year_str, f"{year_str}Q1"]:
            orig_filename = f"orig_{suffix}.txt"
            perf_filename = f"perf_{suffix}.txt"

            orig_path = cache_dir / orig_filename
            perf_path = cache_dir / perf_filename

            # Delete if force_refresh
            if force_refresh:
                orig_path.unlink(missing_ok=True)
                perf_path.unlink(missing_ok=True)

            # Download if missing
            if not orig_path.is_file():
                try:
                    orig_path = get_or_download(service, folder_id, orig_filename, cache_dir)
                    print(f"Downloaded: {orig_filename}")
                except FileNotFoundError:
                    print(f"Not found in Google Drive: {orig_filename}")
                    continue

            if not perf_path.is_file():
                try:
                    perf_path = get_or_download(service, folder_id, perf_filename, cache_dir)
                    print(f"Downloaded: {perf_filename}")
                except FileNotFoundError:
                    print(f"Not found in Google Drive: {perf_filename}")
                    continue

            if orig_path.is_file() and perf_path.is_file():
                pairs.append((orig_path, perf_path))

    return pairs


def clear_cache(cache_dir: Optional[Path | str] = None) -> None:
    """
    Clear the local data cache.

    Args:
        cache_dir: Cache directory to clear (default: from DATA_CACHE_DIR env var)
    """
    if cache_dir is None:
        cache_dir = _get_cache_dir()
    else:
        cache_dir = Path(cache_dir)

    if cache_dir.is_dir():
        import shutil

        shutil.rmtree(cache_dir)
        print(f"Cleared cache: {cache_dir}")
