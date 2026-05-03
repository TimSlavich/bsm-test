"""Shared pytest fixtures.

Tests must NEVER touch the developer's `./brand_monitor.db` — they get a
dedicated in-memory-style sqlite file (per pytest run, in tmp). This is
forced via DATABASE_URL env override BEFORE the app's settings are imported.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Make src/ importable without installing the package
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Force a per-process tempfile for the test DB so we never clobber
# the dev/prod sqlite file via drop_all in fixtures.
_TMP_DB = Path(tempfile.gettempdir()) / f"brand_monitor_test_{os.getpid()}.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DB}"
os.environ.setdefault("AUTO_CREATE_TABLES", "true")
