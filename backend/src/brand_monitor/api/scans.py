"""Scan trigger + per-snapshot read endpoints."""

from __future__ import annotations

import asyncio
import json
from collections import Counter

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from ..db.models import DomainClassification, SerpResult, SerpSnapshot
from ..services.scan import run_scan
from ._deps import session_dep
from .schemas import (
    CategoryShare,
    DiffEntry,
    DiffMoved,
    ResultItem,
    ScanRequest,
    ScanResponse,
    SnapshotDiff,
    SnapshotSummary,
)

router = APIRouter(tags=["scans"])


@router.post("/scans", response_model=ScanResponse, status_code=status.HTTP_201_CREATED)
async def trigger_scan(
    req: ScanRequest, session: AsyncSession = Depends(session_dep)
) -> ScanResponse:
    try:
        result = await run_scan(
            session=session,
            brand_slug=req.brand_slug,
            keyword=req.keyword,
            geo=req.geo,
            top_n=req.top_n,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(e)) from e

    return ScanResponse(
        snapshot_id=result.snapshot_id,
        captured_at=result.captured_at,
        brand_slug=req.brand_slug,
        keyword=result.keyword,
        geo=result.geo,
        source=result.source,
        n_results=len(result.results),
        results=[ResultItem(**r) for r in result.results],
    )


@router.get("/scans/stream")
async def stream_scan(
    brand_slug: str = Query(...),
    keyword: str = Query(...),
    geo: str = Query("NL", min_length=2, max_length=4),
    top_n: int = Query(10, ge=1, le=20),
):
    """Server-Sent Events stream of a live scan.

    Each event is a discrete classifier-pipeline step (``serp_fetch_start``,
    ``serp_fetched``, ``classifying`` per domain, ``classified`` per domain,
    ``persist_done``, then a final ``complete`` or ``error``). The session
    is opened inside the generator so it spans the full streaming lifetime.
    """

    queue: asyncio.Queue[tuple[str, dict] | None] = asyncio.Queue()

    async def emit(event: str, data: dict) -> None:
        await queue.put((event, data))

    async def runner() -> None:
        try:
            async with get_session() as session:
                result = await run_scan(
                    session=session,
                    brand_slug=brand_slug,
                    keyword=keyword,
                    geo=geo,
                    top_n=top_n,
                    on_progress=emit,
                )
            await queue.put(
                (
                    "complete",
                    {
                        "snapshot_id": result.snapshot_id,
                        "captured_at": result.captured_at.isoformat(),
                        "source": result.source,
                        "n_results": len(result.results),
                    },
                )
            )
        except ValueError as e:
            await queue.put(("error", {"type": "ValueError", "message": str(e)}))
        except Exception as e:  # noqa: BLE001
            await queue.put(("error", {"type": type(e).__name__, "message": str(e)}))
        finally:
            await queue.put(None)

    async def event_stream():
        task = asyncio.create_task(runner())
        try:
            while True:
                item = await queue.get()
                if item is None:
                    break
                event, data = item
                yield f"event: {event}\ndata: {json.dumps(data)}\n\n"
        finally:
            await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            # Disable nginx buffering so events arrive in real time.
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/snapshots/diff", response_model=SnapshotDiff)
async def snapshot_diff(
    a: int = Query(..., description="Older snapshot id"),
    b: int = Query(..., description="Newer snapshot id"),
    session: AsyncSession = Depends(session_dep),
) -> SnapshotDiff:
    """Compare two snapshots: which domains were added, removed, moved, kept."""
    snaps = (
        await session.execute(
            select(SerpSnapshot).where(SerpSnapshot.id.in_([a, b]))
        )
    ).scalars().all()
    if {s.id for s in snaps} != {a, b}:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "One or both snapshots not found")
    snap_a = next(s for s in snaps if s.id == a)
    snap_b = next(s for s in snaps if s.id == b)

    # Normalize ordering server-side: ``a`` is documented as "older" but we
    # don't trust the caller to enforce it. Swapping silently would invert
    # added/removed without raising — instead, sort by captured_at.
    if snap_a.captured_at > snap_b.captured_at:
        snap_a, snap_b = snap_b, snap_a
        a, b = b, a

    rows = (
        await session.execute(
            select(SerpResult, DomainClassification)
            .join(DomainClassification, SerpResult.classification_id == DomainClassification.id)
            .where(SerpResult.snapshot_id.in_([a, b]))
        )
    ).all()

    by_snap_by_domain: dict[int, dict[str, tuple[SerpResult, DomainClassification]]] = {a: {}, b: {}}
    for sr, cls in rows:
        by_snap_by_domain[sr.snapshot_id][sr.domain] = (sr, cls)

    a_domains = set(by_snap_by_domain[a].keys())
    b_domains = set(by_snap_by_domain[b].keys())

    added: list[DiffEntry] = []
    removed: list[DiffEntry] = []
    moved: list[DiffMoved] = []
    unchanged: list[DiffEntry] = []

    for d in sorted(b_domains - a_domains):
        sr, cls = by_snap_by_domain[b][d]
        added.append(_to_entry(sr, cls))
    for d in sorted(a_domains - b_domains):
        sr, cls = by_snap_by_domain[a][d]
        removed.append(_to_entry(sr, cls))
    for d in sorted(a_domains & b_domains):
        sr_a, cls_a = by_snap_by_domain[a][d]
        sr_b, cls_b = by_snap_by_domain[b][d]
        if sr_a.position == sr_b.position and cls_a.category == cls_b.category:
            unchanged.append(_to_entry(sr_b, cls_b))
        else:
            moved.append(
                DiffMoved(
                    domain=d,
                    title=sr_b.title,
                    url=sr_b.url,
                    category_from=cls_a.category,
                    category_to=cls_b.category,
                    subcategory_from=cls_a.subcategory,
                    subcategory_to=cls_b.subcategory,
                    position_from=sr_a.position,
                    position_to=sr_b.position,
                )
            )

    def _summary(snap: SerpSnapshot, domains: set[str]):
        from .schemas import BrandSnapshotSummary

        return BrandSnapshotSummary(
            snapshot_id=snap.id,
            captured_at=snap.captured_at,
            keyword=snap.keyword,
            geo=snap.geo,
            n_results=len(domains),
        )

    return SnapshotDiff(
        a=_summary(snap_a, a_domains),
        b=_summary(snap_b, b_domains),
        added=added,
        removed=removed,
        moved=moved,
        unchanged=unchanged,
    )


def _to_entry(sr: SerpResult, cls: DomainClassification) -> DiffEntry:
    return DiffEntry(
        domain=sr.domain,
        title=sr.title,
        url=sr.url,
        category=cls.category,
        subcategory=cls.subcategory,
        position=sr.position,
    )


# NOTE: literal-path routes (``/snapshots/diff``) must be declared BEFORE
# parameterised siblings (``/snapshots/{snapshot_id}``) — FastAPI matches
# in declaration order, otherwise ``diff`` is parsed as ``snapshot_id: int``
# and the request 422s before reaching the handler.


@router.get("/snapshots/{snapshot_id}", response_model=SnapshotSummary)
async def get_snapshot(
    snapshot_id: int, session: AsyncSession = Depends(session_dep)
) -> SnapshotSummary:
    snap = await session.get(SerpSnapshot, snapshot_id)
    if snap is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Snapshot not found")

    rows = (
        await session.execute(
            select(SerpResult, DomainClassification)
            .join(DomainClassification, SerpResult.classification_id == DomainClassification.id)
            .where(SerpResult.snapshot_id == snapshot_id)
        )
    ).all()

    counter: Counter[str] = Counter(c.category for _, c in rows)
    total = sum(counter.values()) or 1
    distribution = [
        CategoryShare(category=cat, count=cnt, percent=round(cnt * 100 / total, 1))
        for cat, cnt in counter.most_common()
    ]
    return SnapshotSummary(
        snapshot_id=snap.id,
        captured_at=snap.captured_at,
        keyword=snap.keyword,
        geo=snap.geo,
        n_results=total,
        distribution=distribution,
    )


@router.get("/snapshots/{snapshot_id}/results", response_model=list[ResultItem])
async def get_snapshot_results(
    snapshot_id: int, session: AsyncSession = Depends(session_dep)
) -> list[ResultItem]:
    rows = (
        await session.execute(
            select(SerpResult, DomainClassification)
            .join(DomainClassification, SerpResult.classification_id == DomainClassification.id)
            .where(SerpResult.snapshot_id == snapshot_id)
            .order_by(SerpResult.position)
        )
    ).all()
    return [
        ResultItem(
            position=sr.position,
            url=sr.url,
            domain=sr.domain,
            title=sr.title,
            category=c.category,
            subcategory=c.subcategory,
            confidence=c.confidence,
            stage_used=c.stage_used,
            reasoning=c.reasoning,
            reason_code=c.reason_code,
            signals=c.signals or {},
        )
        for sr, c in rows
    ]
