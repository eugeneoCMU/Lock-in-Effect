"""Session-wide test setup.

Several modules resolve the FRED API key at IMPORT time (hazard/config.py via
common/fred_key.py:get_fred_api_key, which raises RuntimeError when no key is
present), so a test file that imports them transitively cannot be collected
without one.

Nine test files each set a dummy for themselves. That made the whole suite pass
while leaving single-file runs broken, because the guarantee depended on
alphabetical collection order putting one of those nine first:

    $ pytest tests/test_units_conventions.py
    Interrupted: 1 error during collection

Setting it here makes it structural instead of incidental. conftest.py is
imported before any test module, so every invocation gets it -- one file, the
whole directory, or `-k` a single test.

The value is deliberately a non-functional placeholder: no test may make a live
FRED call, so anything that reaches the network with this key should fail loudly
rather than quietly hit the real API.
"""
from __future__ import annotations

import os

os.environ.setdefault("FRED_API_KEY", "test-dummy-key")
