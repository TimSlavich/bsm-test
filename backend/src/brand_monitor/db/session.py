"""Process-scoped async engine and session factory.

A module-level singleton (rather than ``app.state``) because pytest
fixtures and CLI scripts use the same DB without a live FastAPI app.
Tests reset state via :func:`reset_engine`.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from ..config import get_settings


def _build_engine() -> AsyncEngine:
    url = get_settings().database_url
    # Inject the aiosqlite driver only when the URL is plain `sqlite://`;
    # `sqlite+aiosqlite://` already contains the hint and must not double-up.
    if url.startswith("sqlite://"):
        url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    engine = create_async_engine(url, echo=False, future=True)
    # SQLite single-writer hard limit: enable WAL so readers don't block
    # writers and bump the busy-timeout so concurrent scheduled scans wait
    # politely instead of failing with ``database is locked``. Postgres
    # and other dialects ignore this hook.
    if url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):  # noqa: ANN001
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=10000")
            cur.execute("PRAGMA synchronous=NORMAL")
            cur.close()

    return engine


_engine: AsyncEngine | None = None
_engine_lock = asyncio.Lock()
# Sync lock for the (sync) ``get_engine`` constructor — covers cases where
# pytest or a CLI script touches the engine from multiple threads before the
# event loop is up.
_engine_build_lock = threading.Lock()
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Return the cached engine, building it on first call."""
    global _engine, _sessionmaker
    if _engine is None:
        with _engine_build_lock:
            if _engine is None:
                engine = _build_engine()
                _sessionmaker = async_sessionmaker(
                    engine, expire_on_commit=False, class_=AsyncSession
                )
                _engine = engine
    return _engine


def sessionmaker_factory() -> async_sessionmaker[AsyncSession]:
    if _sessionmaker is None:
        get_engine()
    assert _sessionmaker is not None
    return _sessionmaker


async def reset_engine() -> None:
    """Drop and rebuild — used by tests that mutate ``DATABASE_URL``."""
    global _engine, _sessionmaker
    async with _engine_lock:
        if _engine is not None:
            await _engine.dispose()
        _engine = None
        _sessionmaker = None


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    sm = sessionmaker_factory()
    async with sm() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
