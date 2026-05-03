"""In-process APScheduler driving recurring SERP monitoring.

Single-replica only — with ``uvicorn --workers >1`` each worker would spawn
its own scheduler and duplicate scans. ``BrandKeyword`` is the source of
truth; jobs are recomputed from the DB on every startup, so no persistent
jobstore is needed.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select

from .db import get_session
from .db.models import Brand, BrandKeyword, SerpSnapshot

log = structlog.get_logger()

_scheduler: AsyncIOScheduler | None = None
MISFIRE_GRACE_S = 600
# A small grace delay for the *first* fire of a never-scanned keyword so
# the dashboard shows data within a minute of boot, not 24 hours later.
INITIAL_DELAY_S = 30
# Stagger between simultaneous first-fires of different keywords. SQLite
# allows only one writer at a time; without a stagger, two scheduled
# scans landing in the same second race on the snapshot insert and the
# loser rolls back with ``database is locked``.
STAGGER_S = 20


def _compute_first_run(
    last_scan_at: datetime | None, frequency_hours: int, now: datetime | None = None
) -> datetime:
    """When should this job's first fire happen?

    - Never scanned → ``now + INITIAL_DELAY_S`` (so a fresh install sees data).
    - Last scan was less than ``frequency_hours`` ago → respect the cadence:
      next fire is ``last_scan_at + frequency_hours``. Stops every container
      restart from kicking off a redundant scan.
    - Last scan was longer ago than the cadence → fire after the grace
      delay (we're already overdue, but stagger so multiple keywords don't
      stampede simultaneously on boot).
    """
    now = now or datetime.now(timezone.utc)
    grace = now + timedelta(seconds=INITIAL_DELAY_S)
    if last_scan_at is None:
        return grace
    # ``last_scan_at`` from the DB is naive UTC; align with the aware ``now``.
    aware_last = (
        last_scan_at if last_scan_at.tzinfo else last_scan_at.replace(tzinfo=timezone.utc)
    )
    due = aware_last + timedelta(hours=frequency_hours)
    return due if due > grace else grace


async def _scheduled_scan(brand_slug: str, keyword: str, geo: str) -> None:
    """Run one scan; swallow and log every error.

    APScheduler hides exceptions inside its executor and would kill the
    job permanently — we log structured metadata instead.
    """
    from .services.scan import run_scan

    log.info("scheduled_scan_start", brand=brand_slug, keyword=keyword, geo=geo)
    try:
        async with get_session() as session:
            await run_scan(
                session=session,
                brand_slug=brand_slug,
                keyword=keyword,
                geo=geo,
            )
    except Exception as e:  # noqa: BLE001 — log everything, never raise.
        log.error(
            "scheduled_scan_failed",
            brand=brand_slug,
            keyword=keyword,
            geo=geo,
            error=str(e),
            exc_type=type(e).__name__,
        )


async def start_scheduler() -> AsyncIOScheduler:
    """Boot the scheduler and register one job per active ``BrandKeyword``.

    First-run time per job is computed from each keyword's ``last_scan_at``
    so a quick container restart doesn't trigger a redundant scan.
    """
    global _scheduler
    if _scheduler is not None:
        log.warning("scheduler_already_running")
        return _scheduler

    # Hard guard: APScheduler runs in-process. With multiple uvicorn workers
    # every replica would re-add the same jobs and race on the
    # (brand_id, domain) upsert. Refuse to start instead of duplicating work.
    workers = int(os.environ.get("WEB_CONCURRENCY", "1") or "1")
    if workers > 1:
        raise RuntimeError(
            f"SCHEDULER_ENABLED=true is incompatible with WEB_CONCURRENCY={workers}; "
            "use a single replica or wire an external scheduler (Temporal/Celery-beat)."
        )

    sched = AsyncIOScheduler(timezone="UTC")

    async with get_session() as session:
        rows = (
            await session.execute(
                select(BrandKeyword, Brand)
                .join(Brand, Brand.id == BrandKeyword.brand_id)
                .where(BrandKeyword.active.is_(True))
            )
        ).all()

        last_scans: dict[tuple[int, str, str], datetime] = {}
        for kw, brand in rows:
            last = (
                await session.execute(
                    select(SerpSnapshot.captured_at)
                    .where(SerpSnapshot.brand_id == brand.id)
                    .where(SerpSnapshot.keyword == kw.keyword)
                    .where(SerpSnapshot.geo == kw.geo)
                    .order_by(SerpSnapshot.captured_at.desc())
                    .limit(1)
                )
            ).scalar_one_or_none()
            if last is not None:
                last_scans[(brand.id, kw.keyword, kw.geo)] = last

    for idx, (kw, brand) in enumerate(rows):
        last_scan = last_scans.get((brand.id, kw.keyword, kw.geo))
        first_run = _compute_first_run(last_scan, kw.frequency_hours)
        # Stagger only the never-scanned keywords (which all collapse to
        # ``now + INITIAL_DELAY_S``); for cadenced re-runs the natural
        # ``last_scan_at`` already spreads them across time.
        if last_scan is None:
            first_run = first_run + timedelta(seconds=idx * STAGGER_S)
        sched.add_job(
            _scheduled_scan,
            trigger=IntervalTrigger(hours=kw.frequency_hours, start_date=first_run),
            args=[brand.slug, kw.keyword, kw.geo],
            id=_job_id(brand.slug, kw.keyword, kw.geo),
            replace_existing=True,
            misfire_grace_time=MISFIRE_GRACE_S,
            coalesce=True,
            max_instances=1,
        )

    sched.start()
    _scheduler = sched
    log.info("scheduler_started", n_jobs=len(rows))
    return sched


async def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
    log.info("scheduler_stopped")


def get_scheduler() -> AsyncIOScheduler | None:
    return _scheduler


def _job_id(brand_slug: str, keyword: str, geo: str) -> str:
    return f"{brand_slug}:{keyword}:{geo}"


def upsert_job(
    brand_slug: str,
    keyword: str,
    geo: str,
    frequency_hours: int,
    *,
    last_scan_at: datetime | None = None,
) -> None:
    """Add or update a scheduler job for a single keyword.

    Pass ``last_scan_at`` (when known) so an existing keyword's first fire
    respects the cadence rather than re-running immediately. No-op when the
    scheduler is disabled — admin endpoints call this safely in any mode.
    """
    sched = _scheduler
    if sched is None:
        return
    first_run = _compute_first_run(last_scan_at, frequency_hours)
    sched.add_job(
        _scheduled_scan,
        trigger=IntervalTrigger(hours=frequency_hours, start_date=first_run),
        args=[brand_slug, keyword, geo],
        id=_job_id(brand_slug, keyword, geo),
        replace_existing=True,
        misfire_grace_time=MISFIRE_GRACE_S,
        coalesce=True,
        max_instances=1,
    )


def remove_job(brand_slug: str, keyword: str, geo: str) -> None:
    """Remove a scheduler job. Safe to call when scheduler is off or job is absent."""
    sched = _scheduler
    if sched is None:
        return
    try:
        sched.remove_job(_job_id(brand_slug, keyword, geo))
    except Exception:  # noqa: BLE001 — APScheduler raises a custom JobLookupError; we don't care.
        pass


def get_job_next_run(brand_slug: str, keyword: str, geo: str) -> datetime | None:
    sched = _scheduler
    if sched is None:
        return None
    job = sched.get_job(_job_id(brand_slug, keyword, geo))
    return job.next_run_time if job else None
