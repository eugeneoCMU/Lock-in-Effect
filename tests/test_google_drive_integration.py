"""
Config-resolution tests for common/google_drive.py and common/data_loader.py.

REWRITTEN (suite-hardening pass). The three functions previously in this file —
test_config_resolution, test_credentials, test_folder_id — contained NO assert
statements. They printed diagnostics and `return True`/`return False`, so pytest
collected them, ran them, saw a non-None return (warning only) and marked them
PASSED unconditionally. All three passed on a machine with no credentials at
all, which is precisely the situation they claimed to detect. Three green ticks
for zero coverage.

What replaces them tests the actual resolution CONTRACT, hermetically:
precedence between the environment and .env, the failure mode when a required
key is unset, and the .env parser's handling of comments, quoting and
whitespace. None of it needs real credentials, and all of it fails when the
resolution logic is wrong.

The old file also doubled as a human-facing setup diagnostic. That is kept, but
moved out of the test namespace into `main()` under __main__ so it can never
again be mistaken for coverage.

Run with:  python3 -m pytest tests/test_google_drive_integration.py
Diagnose:  python3 tests/test_google_drive_integration.py --diagnose
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from common import data_loader, google_drive


@pytest.fixture
def clean_caches():
    """These resolvers are lru_cached; clear before AND after so tests neither
    inherit nor leak a memoized value."""
    fns = (
        google_drive._get_api_key,
        google_drive._get_service_account_path,
        data_loader._get_data_folder_id,
        data_loader._get_cache_dir,
    )
    for f in fns:
        f.cache_clear()
    yield
    for f in fns:
        f.cache_clear()


@pytest.fixture
def dotenv(tmp_path, monkeypatch):
    """Point the .env reader at a temp file this test controls."""
    path = tmp_path / ".env"
    monkeypatch.setattr(google_drive, "_DOTENV", path)
    return path


# ---------------------------------------------------------------------------
# _read_dotenv — the parser everything else sits on
# ---------------------------------------------------------------------------
def test_read_dotenv_returns_none_when_the_file_is_absent(dotenv):
    assert not dotenv.exists()
    assert google_drive._read_dotenv("ANYTHING") is None


def test_read_dotenv_reads_a_plain_assignment_and_first_wins(dotenv):
    dotenv.write_text("DATA_FOLDER_ID=abc123\n")
    assert google_drive._read_dotenv("DATA_FOLDER_ID") == "abc123"

    # A duplicated key is the realistic .env accident (an old value left above
    # a new one, or vice versa). The parser returns on the FIRST match; a
    # rewrite that builds a dict and returns the last one silently flips which
    # credential a machine uses, with no error anywhere.
    dotenv.write_text("DATA_FOLDER_ID=first\nDATA_FOLDER_ID=second\n")
    assert google_drive._read_dotenv("DATA_FOLDER_ID") == "first"


@pytest.mark.parametrize("line,expected", [
    ('K="quoted"', "quoted"),
    ("K='single'", "single"),
    ("K=  spaced  ", "spaced"),
    ('K =  "both" ', "both"),
    ("K=", ""),
    ("K=a=b=c", "a=b=c"),          # only the FIRST '=' splits
    ("K=has spaces inside", "has spaces inside"),
])
def test_read_dotenv_strips_quotes_and_whitespace(dotenv, line, expected):
    dotenv.write_text(line + "\n")
    assert google_drive._read_dotenv("K") == expected


def test_read_dotenv_ignores_comments_and_blanks(dotenv):
    """The commented line is written WITHOUT a space after the '#'.

    With '# K=...' the key strips to '# K', which fails the exact-match test
    anyway — so dropping the `startswith('#')` guard entirely still returns
    'real' and the test cannot see it. '#K=...' strips to '#K'... which also
    fails. The case that actually distinguishes the guard is a commented
    assignment whose key text is exactly the key once '#' is consumed, which
    is what a `lstrip('#')`-style rewrite or a dropped guard combined with
    prefix matching produces. Both spellings are therefore asserted, and the
    commented-out VALUE is asserted never to be returned.
    """
    dotenv.write_text(
        "#K=commented_out\n"
        "# K=also_commented\n"
        "\n"
        "   \n"
        "NOT_AN_ASSIGNMENT\n"
        "K=real\n"
    )
    got = google_drive._read_dotenv("K")
    assert got == "real"
    assert got not in ("commented_out", "also_commented")
    # A comment is not an assignment even when it is the ONLY line mentioning
    # the key: the answer must be None, not the commented-out value.
    dotenv.write_text("#K=commented_out\n# K=also_commented\n")
    assert google_drive._read_dotenv("K") is None


def test_read_dotenv_does_not_match_a_key_by_prefix(dotenv):
    """GOOGLE_DRIVE_API_KEY_OLD must not answer for GOOGLE_DRIVE_API_KEY."""
    dotenv.write_text("GOOGLE_DRIVE_API_KEY_OLD=stale\n")
    assert google_drive._read_dotenv("GOOGLE_DRIVE_API_KEY") is None


def test_read_dotenv_matches_the_key_exactly_and_case_sensitively(dotenv):
    """HOLE (adversarial mutation pass). The prefix test above uses a LONGER
    stored key, so a `startswith` slip is caught, but two other ways of
    loosening the match were not: a case-insensitive compare, and a parser
    that stops caring about the key at all and returns the first value it
    finds. Both fired no test. Env-var names are case-sensitive, and a
    lowercase line must not answer for the real key.
    """
    dotenv.write_text("google_drive_api_key=wrong_case\n")
    assert google_drive._read_dotenv("GOOGLE_DRIVE_API_KEY") is None

    # A file whose FIRST assignment is a different key entirely: a parser that
    # ignores the key returns "decoy" here.
    dotenv.write_text("SOMETHING_ELSE=decoy\nGOOGLE_DRIVE_API_KEY=real\n")
    assert google_drive._read_dotenv("GOOGLE_DRIVE_API_KEY") == "real"
    assert google_drive._read_dotenv("NOT_PRESENT") is None


def test_read_dotenv_returns_none_for_a_missing_key(dotenv):
    dotenv.write_text("OTHER=value\n")
    assert google_drive._read_dotenv("K") is None


# ---------------------------------------------------------------------------
# Environment-over-dotenv precedence
# ---------------------------------------------------------------------------
def test_api_key_prefers_the_environment_over_dotenv(clean_caches, dotenv,
                                                     monkeypatch):
    dotenv.write_text("GOOGLE_DRIVE_API_KEY=from_dotenv\n")
    monkeypatch.setenv("GOOGLE_DRIVE_API_KEY", "from_env")
    assert google_drive._get_api_key() == "from_env"


def test_api_key_falls_back_to_dotenv(clean_caches, dotenv, monkeypatch):
    dotenv.write_text("GOOGLE_DRIVE_API_KEY=from_dotenv\n")
    monkeypatch.delenv("GOOGLE_DRIVE_API_KEY", raising=False)
    assert google_drive._get_api_key() == "from_dotenv"


def test_api_key_is_none_when_configured_nowhere(clean_caches, dotenv,
                                                 monkeypatch):
    """The old test_credentials returned False here and still PASSED."""
    monkeypatch.delenv("GOOGLE_DRIVE_API_KEY", raising=False)
    assert not dotenv.exists()
    assert google_drive._get_api_key() is None


def test_empty_env_value_falls_through_to_dotenv(clean_caches, dotenv,
                                                 monkeypatch):
    """`os.environ.get(...) or _read_dotenv(...)` — an empty string is falsy and
    must NOT shadow a real .env value."""
    dotenv.write_text("GOOGLE_DRIVE_API_KEY=from_dotenv\n")
    monkeypatch.setenv("GOOGLE_DRIVE_API_KEY", "")
    assert google_drive._get_api_key() == "from_dotenv"


def test_service_account_path_precedence(clean_caches, dotenv, monkeypatch):
    dotenv.write_text("GOOGLE_DRIVE_CREDENTIALS_JSON=/from/dotenv.json\n")
    monkeypatch.setenv("GOOGLE_DRIVE_CREDENTIALS_JSON", "/from/env.json")
    assert google_drive._get_service_account_path() == "/from/env.json"

    google_drive._get_service_account_path.cache_clear()
    monkeypatch.delenv("GOOGLE_DRIVE_CREDENTIALS_JSON", raising=False)
    assert google_drive._get_service_account_path() == "/from/dotenv.json"


def test_api_key_and_service_account_read_different_keys(clean_caches, dotenv,
                                                         monkeypatch):
    """A copy-paste slip between these two resolvers would make the API key
    resolve to a filesystem path (or vice versa)."""
    monkeypatch.delenv("GOOGLE_DRIVE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_DRIVE_CREDENTIALS_JSON", raising=False)
    dotenv.write_text(
        "GOOGLE_DRIVE_API_KEY=the_key\n"
        "GOOGLE_DRIVE_CREDENTIALS_JSON=/the/path.json\n"
    )
    assert google_drive._get_api_key() == "the_key"
    assert google_drive._get_service_account_path() == "/the/path.json"


# ---------------------------------------------------------------------------
# _get_data_folder_id — required, so it must RAISE, not return a falsy value
# ---------------------------------------------------------------------------
def test_folder_id_resolves_from_the_environment(clean_caches, dotenv,
                                                 monkeypatch):
    monkeypatch.setenv("DATA_FOLDER_ID", "folder_from_env")
    assert data_loader._get_data_folder_id() == "folder_from_env"


def test_folder_id_resolves_from_dotenv(clean_caches, dotenv, monkeypatch):
    monkeypatch.delenv("DATA_FOLDER_ID", raising=False)
    dotenv.write_text("DATA_FOLDER_ID=folder_from_dotenv\n")
    assert data_loader._get_data_folder_id() == "folder_from_dotenv"


def test_folder_id_raises_when_unset(clean_caches, dotenv, monkeypatch):
    """The old test_folder_id caught RuntimeError, printed a hint, returned
    False, and PASSED. The contract is that this RAISES — silently returning
    None would send an empty folder id into every Drive query."""
    monkeypatch.delenv("DATA_FOLDER_ID", raising=False)
    assert not dotenv.exists()
    with pytest.raises(RuntimeError, match="DATA_FOLDER_ID"):
        data_loader._get_data_folder_id()


def test_folder_id_prefers_the_environment_over_dotenv(clean_caches, dotenv,
                                                       monkeypatch):
    """HOLE (adversarial mutation pass). The two tests above set exactly one
    source each — env-only, then dotenv-only — so neither can see which side
    wins when BOTH are set. Inverting the `or` chain to
    `_read_dotenv(...) or os.environ.get(...)` fired no test in the suite,
    even though it silently reverses which Drive folder every download reads
    from. The API-key resolver has this test; the folder-id resolver did not.
    """
    dotenv.write_text("DATA_FOLDER_ID=folder_from_dotenv\n")
    monkeypatch.setenv("DATA_FOLDER_ID", "folder_from_env")
    assert data_loader._get_data_folder_id() == "folder_from_env"


def test_folder_id_raises_on_an_empty_value(clean_caches, dotenv, monkeypatch):
    monkeypatch.setenv("DATA_FOLDER_ID", "")
    assert not dotenv.exists()
    with pytest.raises(RuntimeError):
        data_loader._get_data_folder_id()


def test_folder_id_raises_on_an_empty_dotenv_value(clean_caches, dotenv,
                                                   monkeypatch):
    """HOLE (adversarial mutation pass). The empty-value test above sets an
    empty ENVIRONMENT variable, and `os.environ.get` returning "" is falsy, so
    the `or` chain hands None to the guard either way — which makes a
    `if folder_id is None` rewrite of `if not folder_id` invisible there.

    An empty value in the .env file is different: `_read_dotenv` returns the
    empty STRING, not None, so that rewrite accepts it and an empty folder id
    goes into every Drive query. Probing the guard from the .env side is what
    distinguishes the two spellings.
    """
    monkeypatch.delenv("DATA_FOLDER_ID", raising=False)
    dotenv.write_text("DATA_FOLDER_ID=\n")
    assert google_drive._read_dotenv("DATA_FOLDER_ID") == ""  # not None
    with pytest.raises(RuntimeError, match="DATA_FOLDER_ID"):
        data_loader._get_data_folder_id()


# ---------------------------------------------------------------------------
# _get_cache_dir
# ---------------------------------------------------------------------------
def test_cache_dir_honours_the_env_var_and_creates_the_directory(
    clean_caches, tmp_path, monkeypatch
):
    target = tmp_path / "nested" / "cache"
    monkeypatch.setenv("DATA_CACHE_DIR", str(target))
    got = data_loader._get_cache_dir()
    assert got == target
    assert got.is_dir()  # created, including the missing parent


def test_cache_dir_defaults_to_data_cache(clean_caches, tmp_path, monkeypatch):
    monkeypatch.delenv("DATA_CACHE_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    got = data_loader._get_cache_dir()
    assert got == Path("./data/cache")
    assert (tmp_path / "data" / "cache").is_dir()


def test_cache_dir_is_idempotent_on_an_existing_directory(
    clean_caches, tmp_path, monkeypatch
):
    target = tmp_path / "cache"
    target.mkdir()
    (target / "keep.txt").write_text("x")
    monkeypatch.setenv("DATA_CACHE_DIR", str(target))
    assert data_loader._get_cache_dir() == target
    assert (target / "keep.txt").read_text() == "x"  # not wiped


# ---------------------------------------------------------------------------
# Human-facing setup diagnostic — deliberately NOT a test.
# ---------------------------------------------------------------------------
def main() -> int:
    """Print the live Google Drive configuration. Diagnostic only: it reports
    on this machine's environment, which is not a property of the code and
    cannot be a pass/fail assertion."""
    print("=" * 60)
    print("Google Drive configuration (diagnostic, not a test)")
    print("=" * 60)

    try:
        print(f"  cache directory : {data_loader._get_cache_dir()}")
    except Exception as e:  # pragma: no cover - diagnostic path
        print(f"  cache directory : ERROR {e}")

    api_key = google_drive._get_api_key()
    if api_key:
        print(f"  API key         : found ({len(api_key)} chars)")
    else:
        sa = google_drive._get_service_account_path()
        if sa and Path(sa).expanduser().is_file():
            print(f"  service account : {Path(sa).expanduser()}")
        elif sa:
            print(f"  service account : MISSING FILE at {sa}")
        else:
            print("  credentials     : none configured "
                  "(set GOOGLE_DRIVE_API_KEY in .env)")

    try:
        print(f"  folder id       : {data_loader._get_data_folder_id()}")
    except RuntimeError as e:
        print(f"  folder id       : not configured ({e})")

    print("=" * 60)
    return 0


if __name__ == "__main__":
    if "--diagnose" in sys.argv:
        sys.exit(main())
    sys.exit(pytest.main([__file__, "-v"]))
