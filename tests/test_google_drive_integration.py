"""
Quick test to verify Google Drive integration is properly configured.
Run with: python3 tests/test_google_drive_integration.py
"""

import sys
from pathlib import Path

# Add repo root to path
_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from common.google_drive import _get_credentials_path, authenticate_service_account
from common.data_loader import _get_data_folder_id, _get_cache_dir


def test_config_resolution():
    """Test that environment and .env configuration are properly resolved."""
    print("Testing configuration resolution...")

    # Test cache dir
    try:
        cache_dir = _get_cache_dir()
        print(f"  ✓ Cache directory: {cache_dir}")
    except Exception as e:
        print(f"  ✗ Cache directory error: {e}")
        return False

    return True


def test_credentials():
    """Test that credentials can be loaded (if configured)."""
    print("\nTesting credential resolution...")

    try:
        cred_path = _get_credentials_path()
        print(f"  ✓ Credentials path found: {cred_path}")

        # Check if file exists
        cred_file = Path(cred_path).expanduser()
        if cred_file.is_file():
            print(f"  ✓ Credentials file exists")
            return True
        else:
            print(f"  ✗ Credentials file not found: {cred_file}")
            print("    Hint: Set GOOGLE_DRIVE_CREDENTIALS_JSON in .env or environment")
            return False
    except RuntimeError as e:
        print(f"  ⓘ Credentials not configured: {e}")
        print("    Hint: Set GOOGLE_DRIVE_CREDENTIALS_JSON in .env or environment")
        return False


def test_folder_id():
    """Test that Google Drive folder ID is configured."""
    print("\nTesting Google Drive folder ID...")

    try:
        folder_id = _get_data_folder_id()
        print(f"  ✓ Folder ID found: {folder_id}")
        return True
    except RuntimeError as e:
        print(f"  ⓘ Folder ID not configured: {e}")
        print("    Hint: Set DATA_FOLDER_ID in .env or environment")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Google Drive Integration Test")
    print("=" * 60)

    results = []
    results.append(test_config_resolution())
    results.append(test_credentials())
    results.append(test_folder_id())

    print("\n" + "=" * 60)
    if all(results):
        print("✓ All tests passed! Google Drive is fully configured.")
    else:
        missing = []
        if not results[1]:
            missing.append("GOOGLE_DRIVE_CREDENTIALS_JSON")
        if not results[2]:
            missing.append("DATA_FOLDER_ID")

        if missing:
            print(f"⚠ Configuration incomplete. Missing: {', '.join(missing)}")
            print("\nTo set up Google Drive:")
            print("  1. Copy .env.example to .env")
            print("  2. Follow the setup instructions in README.md (§3)")
        else:
            print("✓ Basic configuration complete.")

    print("=" * 60)


if __name__ == "__main__":
    main()
