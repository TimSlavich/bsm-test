"""Brand CRUD + history (snapshots, trend, domains) + keyword scheduler config."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import scheduler as scheduler_mod
from ..classifier.taxonomy import Category
from ..db.models import Brand, BrandKeyword, DomainClassification, SerpResult, SerpSnapshot
from ..time import utc_now
from ._deps import session_dep
from .schemas import (
    BrandCreate,
    BrandResponse,
    BrandSnapshotSummary,
    BrandWhitelistsUpdate,
    DomainRow,
    KeywordCreate,
    KeywordResponse,
    KeywordUpdate,
    TrendPoint,
)

router = APIRouter(prefix="/brands", tags=["brands"])


async def _load_brand_or_404(session: AsyncSession, slug: str) -> Brand:
    brand = (
        await session.execute(select(Brand).where(Brand.slug == slug))
    ).scalar_one_or_none()
    if brand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand not found")
    return brand


@router.post("", response_model=BrandResponse, status_code=status.HTTP_201_CREATED)
async def create_brand(
    req: BrandCreate, session: AsyncSession = Depends(session_dep)
) -> BrandResponse:
    existing = (
        await session.execute(select(Brand).where(Brand.slug == req.slug))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Brand '{req.slug}' already exists")
    brand = Brand(
        slug=req.slug,
        name=req.name,
        geo=req.geo,
        official_domains=list(req.official_domains),
        known_partners=list(req.known_partners),
        known_competitors=list(req.known_competitors),
    )
    session.add(brand)
    await session.flush()
    return BrandResponse.model_validate(brand)


@router.put("/{slug}/whitelists", response_model=BrandResponse)
async def update_brand_whitelists(
    slug: str,
    req: BrandWhitelistsUpdate,
    session: AsyncSession = Depends(session_dep),
) -> BrandResponse:
    brand = await _load_brand_or_404(session, slug)
    if req.official_domains is not None:
        brand.official_domains = list(req.official_domains)
    if req.known_partners is not None:
        brand.known_partners = list(req.known_partners)
    if req.known_competitors is not None:
        brand.known_competitors = list(req.known_competitors)
    await session.flush()
    return BrandResponse.model_validate(brand)


@router.get("/{slug}/domains", response_model=list[DomainRow])
async def list_brand_domains(
    slug: str, session: AsyncSession = Depends(session_dep)
) -> list[DomainRow]:
    brand = await _load_brand_or_404(session, slug)
    rows = (
        await session.execute(
            select(DomainClassification)
            .where(DomainClassification.brand_id == brand.id)
            .order_by(DomainClassification.classified_at.desc())
        )
    ).scalars().all()
    return [
        DomainRow(
            domain=r.domain,
            category=r.category,
            subcategory=r.subcategory,
            confidence=r.confidence,
            stage_used=r.stage_used,
            classified_at=r.classified_at,
        )
        for r in rows
    ]


@router.get("/{slug}/snapshots", response_model=list[BrandSnapshotSummary])
async def list_brand_snapshots(
    slug: str,
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(session_dep),
) -> list[BrandSnapshotSummary]:
    brand = await _load_brand_or_404(session, slug)
    since = utc_now() - timedelta(days=days)
    # Snapshot row + COUNT(*) of its results in one round-trip via GROUP BY.
    rows = (
        await session.execute(
            select(SerpSnapshot, func.count(SerpResult.id))
            .outerjoin(SerpResult, SerpResult.snapshot_id == SerpSnapshot.id)
            .where(SerpSnapshot.brand_id == brand.id)
            .where(SerpSnapshot.captured_at >= since)
            .group_by(SerpSnapshot.id)
            .order_by(SerpSnapshot.captured_at.desc())
        )
    ).all()
    return [
        BrandSnapshotSummary(
            snapshot_id=snap.id,
            captured_at=snap.captured_at,
            keyword=snap.keyword,
            geo=snap.geo,
            n_results=int(n_results),
        )
        for snap, n_results in rows
    ]


@router.get("/{slug}/keywords", response_model=list[KeywordResponse])
async def list_keywords(
    slug: str, session: AsyncSession = Depends(session_dep)
) -> list[KeywordResponse]:
    brand = await _load_brand_or_404(session, slug)
    rows = (
        await session.execute(
            select(BrandKeyword)
            .where(BrandKeyword.brand_id == brand.id)
            .order_by(BrandKeyword.id.asc())
        )
    ).scalars().all()
    return [await _to_keyword_response(session, brand, kw) for kw in rows]


@router.post(
    "/{slug}/keywords",
    response_model=KeywordResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_keyword(
    slug: str,
    req: KeywordCreate,
    session: AsyncSession = Depends(session_dep),
) -> KeywordResponse:
    brand = await _load_brand_or_404(session, slug)
    kw = BrandKeyword(
        brand_id=brand.id,
        keyword=req.keyword.strip(),
        geo=req.geo.upper(),
        frequency_hours=req.frequency_hours,
        active=req.active,
    )
    session.add(kw)
    try:
        await session.flush()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Keyword '{req.keyword}' for geo '{req.geo}' already exists for this brand",
        ) from e

    if kw.active:
        scheduler_mod.upsert_job(brand.slug, kw.keyword, kw.geo, kw.frequency_hours)

    return await _to_keyword_response(session, brand, kw)


@router.patch("/keywords/{keyword_id}", response_model=KeywordResponse)
async def update_keyword(
    keyword_id: int,
    req: KeywordUpdate,
    session: AsyncSession = Depends(session_dep),
) -> KeywordResponse:
    kw = await session.get(BrandKeyword, keyword_id)
    if kw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Keyword not found")
    brand = await session.get(Brand, kw.brand_id)
    if brand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Brand not found")

    # Track old identity so we can remove the old scheduler job if the
    # composite (keyword, geo) shifted.
    old_keyword = kw.keyword
    old_geo = kw.geo

    if req.keyword is not None:
        kw.keyword = req.keyword.strip()
    if req.geo is not None:
        kw.geo = req.geo.upper()
    if req.frequency_hours is not None:
        kw.frequency_hours = req.frequency_hours
    if req.active is not None:
        kw.active = req.active

    try:
        await session.flush()
    except IntegrityError as e:
        await session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Another keyword with this (keyword, geo) already exists for the brand",
        ) from e

    if old_keyword != kw.keyword or old_geo != kw.geo:
        scheduler_mod.remove_job(brand.slug, old_keyword, old_geo)

    if kw.active:
        # Pass the latest snapshot timestamp so re-activation / frequency
        # change doesn't kick off an immediate redundant scan.
        last_scan = await _last_scan_at(session, brand.id, kw.keyword, kw.geo)
        scheduler_mod.upsert_job(
            brand.slug, kw.keyword, kw.geo, kw.frequency_hours, last_scan_at=last_scan
        )
    else:
        scheduler_mod.remove_job(brand.slug, kw.keyword, kw.geo)

    return await _to_keyword_response(session, brand, kw)


async def _last_scan_at(
    session: AsyncSession, brand_id: int, keyword: str, geo: str
):
    return (
        await session.execute(
            select(SerpSnapshot.captured_at)
            .where(SerpSnapshot.brand_id == brand_id)
            .where(SerpSnapshot.keyword == keyword)
            .where(SerpSnapshot.geo == geo)
            .order_by(SerpSnapshot.captured_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


@router.delete("/keywords/{keyword_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_keyword(
    keyword_id: int, session: AsyncSession = Depends(session_dep)
) -> Response:
    kw = await session.get(BrandKeyword, keyword_id)
    if kw is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Keyword not found")
    brand = await session.get(Brand, kw.brand_id)
    keyword = kw.keyword
    geo = kw.geo
    await session.delete(kw)
    await session.flush()
    if brand is not None:
        scheduler_mod.remove_job(brand.slug, keyword, geo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _to_keyword_response(
    session: AsyncSession, brand: Brand, kw: BrandKeyword
) -> KeywordResponse:
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
    next_run = scheduler_mod.get_job_next_run(brand.slug, kw.keyword, kw.geo)
    return KeywordResponse(
        id=kw.id,
        brand_slug=brand.slug,
        keyword=kw.keyword,
        geo=kw.geo,
        frequency_hours=kw.frequency_hours,
        active=kw.active,
        last_scan_at=last,
        next_run_at=next_run,
    )


@router.get("/{slug}/trend", response_model=list[TrendPoint])
async def brand_trend(
    slug: str,
    days: int = Query(7, ge=1, le=90),
    session: AsyncSession = Depends(session_dep),
) -> list[TrendPoint]:
    """Per-day category share. Latest snapshot of the day wins, picked
    deterministically (asc by captured_at, then id)."""
    brand = await _load_brand_or_404(session, slug)
    since = utc_now() - timedelta(days=days)

    snaps = (
        await session.execute(
            select(SerpSnapshot.id, SerpSnapshot.captured_at)
            .where(SerpSnapshot.brand_id == brand.id)
            .where(SerpSnapshot.captured_at >= since)
            .order_by(SerpSnapshot.captured_at.asc(), SerpSnapshot.id.asc())
        )
    ).all()
    latest_by_day: dict[str, int] = {}
    for snap_id, captured_at in snaps:
        latest_by_day[captured_at.date().isoformat()] = snap_id
    if not latest_by_day:
        return []

    counts = (
        await session.execute(
            select(
                SerpResult.snapshot_id,
                DomainClassification.category,
                func.count(SerpResult.id),
            )
            .join(DomainClassification, SerpResult.classification_id == DomainClassification.id)
            .where(SerpResult.snapshot_id.in_(latest_by_day.values()))
            .group_by(SerpResult.snapshot_id, DomainClassification.category)
        )
    ).all()
    by_snap: dict[int, Counter[str]] = defaultdict(Counter)
    for snap_id, category, n in counts:
        by_snap[snap_id][category] += int(n)

    points: list[TrendPoint] = []
    for day in sorted(latest_by_day):
        snap_id = latest_by_day[day]
        c = by_snap.get(snap_id, Counter())
        total = sum(c.values()) or 1
        points.append(
            TrendPoint(
                date=day,
                snapshot_id=snap_id,
                official=round(c[Category.OFFICIAL.value] * 100 / total, 1),
                affiliate_to_brand=round(c[Category.AFFILIATE_TO_BRAND.value] * 100 / total, 1),
                competitor_hijacking=round(c[Category.COMPETITOR_HIJACKING.value] * 100 / total, 1),
                informational=round(c[Category.INFORMATIONAL.value] * 100 / total, 1),
            )
        )
    return points
