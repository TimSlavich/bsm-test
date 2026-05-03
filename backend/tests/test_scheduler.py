"""Scheduler lifecycle + bootstrap tests.

Verifies:
- ``start_scheduler`` registers one job per active BrandKeyword.
- ``stop_scheduler`` is idempotent.
- ``bootstrap_brand_seeds`` is idempotent (re-running doesn't dup keywords).
- The job function delegates to ``run_scan`` and swallows exceptions.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select

from brand_monitor.bootstrap import bootstrap_brand_seeds
from brand_monitor.db import get_session
from brand_monitor.db.models import Base, BrandKeyword
from brand_monitor.db.session import get_engine
from brand_monitor.scheduler import (
    _scheduled_scan,
    get_scheduler,
    start_scheduler,
    stop_scheduler,
)


@pytest_asyncio.fixture
async def fresh_db():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await stop_scheduler()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_bootstrap_is_idempotent(fresh_db):
    await bootstrap_brand_seeds()
    await bootstrap_brand_seeds()  # second call must not duplicate
    async with get_session() as session:
        kw = (await session.execute(select(BrandKeyword))).scalars().all()
    # STARCASINO has 3 monitored_keywords
    assert len(kw) == 3
    assert {k.keyword for k in kw} == {"starcasino", "starcasino bonus", "starcasino review"}


@pytest.mark.asyncio
async def test_start_scheduler_registers_job_per_keyword(fresh_db):
    await bootstrap_brand_seeds()
    sched = await start_scheduler()
    try:
        jobs = sched.get_jobs()
        assert len(jobs) == 3
        assert all(j.id.startswith("starcasino:") for j in jobs)
    finally:
        await stop_scheduler()
    assert get_scheduler() is None


@pytest.mark.asyncio
async def test_stop_scheduler_idempotent():
    await stop_scheduler()  # no-op when nothing is running
    await stop_scheduler()
    assert get_scheduler() is None


@pytest.mark.asyncio
async def test_scheduled_scan_delegates_to_run_scan_and_swallows():
    # Happy path: run_scan called once, no exception escapes.
    with patch(
        "brand_monitor.services.scan.run_scan", new=AsyncMock(return_value=None)
    ) as mock_run:
        await _scheduled_scan("starcasino", "starcasino", "NL")
    assert mock_run.await_count == 1

    # Failure path: run_scan raises but the job function must not.
    with patch(
        "brand_monitor.services.scan.run_scan",
        new=AsyncMock(side_effect=RuntimeError("simulated outage")),
    ):
        await _scheduled_scan("starcasino", "starcasino", "NL")  # must not raise
