"""Single datetime convention: **naive UTC throughout.**

DB columns are plain ``DateTime`` (not TIMESTAMPTZ) so SQLite and Postgres
behave identically out of the box. To switch to timezone-aware columns in
production, change :func:`utc_now`, alter the columns, and update every
``timedelta`` comparison site in one go — don't half-migrate.
"""

from __future__ import annotations

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Naive UTC ``datetime`` — use everywhere we touch DB timestamps."""
    return datetime.now(UTC).replace(tzinfo=None)
