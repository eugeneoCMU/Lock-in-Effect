"""
Google Drive integration for fetching data files.

Credential resolution order:
  1. GOOGLE_DRIVE_CREDENTIALS_JSON environment variable (path to service account JSON)
  2. A `GOOGLE_DRIVE_CREDENTIALS_JSON=...` line in gitignored `.env` at the repo root
  3. Raise, pointing the user at `.env.example`

Service account credentials are obtained from Google Cloud Console:
  https://console.cloud.google.com → Create service account → Download JSON key

Share your Google Drive folder with the service account email to grant access.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DOTENV = _REPO_ROOT / ".env"


def _read_dotenv(key: str) -> str | None:
    """Read a key from the .env file."""
    if not _DOTENV.is_file():
        return None
    for raw in _DOTENV.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return None


@lru_cache(maxsize=1)
def _get_credentials_path() -> str:
    """Resolve path to service account JSON credentials."""
    cred_path = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_JSON") or _read_dotenv(
        "GOOGLE_DRIVE_CREDENTIALS_JSON"
    )
    if not cred_path:
        raise RuntimeError(
            "GOOGLE_DRIVE_CREDENTIALS_JSON not found. Set the "
            "GOOGLE_DRIVE_CREDENTIALS_JSON environment variable or copy "
            ".env.example to .env and fill it in with the path to your service "
            "account JSON key. Create one at: "
            "https://console.cloud.google.com → Service Accounts"
        )
    return cred_path


@lru_cache(maxsize=1)
def authenticate_service_account() -> Any:
    """
    Authenticate using Google Drive service account credentials.
    Returns a Google Drive API service object.
    """
    cred_path = _get_credentials_path()
    cred_path = Path(cred_path).expanduser().resolve()

    if not cred_path.is_file():
        raise FileNotFoundError(f"Credentials file not found: {cred_path}")

    try:
        credentials = Credentials.from_service_account_file(
            str(cred_path), scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
    except Exception as e:
        raise RuntimeError(f"Failed to load credentials from {cred_path}: {e}")

    service = build("drive", "v3", credentials=credentials)
    return service


def list_folder_files(
    service: Any, folder_id: str, query: Optional[str] = None
) -> list[Dict[str, str]]:
    """
    List files in a Google Drive folder.

    Args:
        service: Google Drive API service object
        folder_id: Google Drive folder ID
        query: Optional additional query filter (e.g., "name contains 'freddie'")

    Returns:
        List of dicts with 'id', 'name', 'mimeType'
    """
    q = f"'{folder_id}' in parents and trashed=false"
    if query:
        q += f" and {query}"

    try:
        results = service.files().list(q=q, spaces="drive", pageSize=100,
                                       fields="files(id, name, mimeType)").execute()
        return results.get("files", [])
    except Exception as e:
        raise RuntimeError(f"Failed to list folder {folder_id}: {e}")


def download_file(service: Any, file_id: str, dest_path: Path | str) -> None:
    """
    Download a file from Google Drive to local disk.

    Args:
        service: Google Drive API service object
        file_id: Google Drive file ID
        dest_path: Destination file path
    """
    dest_path = Path(dest_path)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        request = service.files().get_media(fileId=file_id)
        with open(dest_path, "wb") as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
    except Exception as e:
        raise RuntimeError(f"Failed to download file {file_id} to {dest_path}: {e}")


def find_file_by_name(
    service: Any, folder_id: str, filename: str
) -> Optional[str]:
    """
    Find a file by name in a folder. Returns the file ID if found.

    Args:
        service: Google Drive API service object
        folder_id: Google Drive folder ID
        filename: Name of the file to find

    Returns:
        File ID if found, None otherwise
    """
    files = list_folder_files(service, folder_id, query=f"name='{filename}'")
    if files:
        return files[0]["id"]
    return None


def get_or_download(
    service: Any,
    folder_id: str,
    filename: str,
    cache_dir: Path | str = "./data/cache",
) -> Path:
    """
    Download a file from Google Drive, using local cache if available.

    Args:
        service: Google Drive API service object
        folder_id: Google Drive folder ID
        filename: Name of the file in Google Drive
        cache_dir: Local cache directory

    Returns:
        Path to the cached/downloaded file
    """
    cache_dir = Path(cache_dir)
    cache_path = cache_dir / filename

    if cache_path.is_file():
        return cache_path

    file_id = find_file_by_name(service, folder_id, filename)
    if not file_id:
        raise FileNotFoundError(
            f"File '{filename}' not found in Google Drive folder {folder_id}"
        )

    download_file(service, file_id, cache_path)
    return cache_path
