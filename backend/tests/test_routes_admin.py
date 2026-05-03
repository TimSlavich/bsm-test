"""Integration tests for brand-admin endpoints + trend/snapshot endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from brand_monitor.time import utc_now

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from brand_monitor.db import get_session
from brand_monitor.db.models import (
    Base,
    Brand,
    DomainClassification,
    SerpResult,
    SerpSnapshot,
)
from brand_monitor.db.session import get_engine
from brand_monitor.main import app
from brand_monitor.seeds.starcasino import BrandSeed


@pytest_asyncio.fixture
async def client():
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_create_brand_then_update_whitelists(client):
    payload = {
        "slug": "testbrand",
        "name": "TestBrand",
        "geo": "NL",
        "official_domains": ["testbrand.nl"],
        "known_partners": [],
        "known_competitors": ["evilcompetitor.nl"],
    }
    r = await client.post("/api/brands", json=payload)
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["slug"] == "testbrand"
    assert set(body["official_domains"]) == {"testbrand.nl"}

    # duplicate → 409
    r2 = await client.post("/api/brands", json=payload)
    assert r2.status_code == 409

    # update partial whitelists
    r3 = await client.put(
        "/api/brands/testbrand/whitelists",
        json={"known_partners": ["partner.nl"]},
    )
    assert r3.status_code == 200, r3.text
    body3 = r3.json()
    assert body3["known_partners"] == ["partner.nl"]
    # untouched fields persist
    assert body3["official_domains"] == ["testbrand.nl"]
    assert body3["known_competitors"] == ["evilcompetitor.nl"]


@pytest.mark.asyncio
async def test_brand_snapshots_and_trend_endpoints(client):
    # Build a brand + 3 snapshots on different days with varying distributions
    async with get_session() as session:
        brand = Brand(
            slug="trendbrand",
            name="TrendBrand",
            geo="NL",
            official_domains=[],
            known_partners=[],
            known_competitors=[],
        )
        session.add(brand)
        await session.flush()
        for offset, mix in enumerate(
            [
                ("official", "official", "informational"),
                ("official", "affiliate_to_brand", "informational"),
                ("affiliate_to_brand", "competitor_hijacking", "informational"),
            ]
        ):
            snap = SerpSnapshot(
                brand_id=brand.id,
                keyword="trendbrand",
                geo="NL",
                source="seed",
                captured_at=utc_now() - timedelta(days=2 - offset),
                raw_serp={},
            )
            session.add(snap)
            await session.flush()
            for i, cat in enumerate(mix):
                cls = DomainClassification(
                    brand_id=brand.id,
                    domain=f"d{offset}-{i}.example",
                    category=cat,
                    subcategory=(
                        "official_apex"
                        if cat == "official"
                        else "affiliate_listicle"
                        if cat == "affiliate_to_brand"
                        else "hijacker_affiliate_to_others"
                        if cat == "competitor_hijacking"
                        else "info_other"
                    ),
                    confidence=0.8,
                    stage_used=2,
                    signals={},
                    reasoning="seeded",
                )
                session.add(cls)
                await session.flush()
                session.add(
                    SerpResult(
                        snapshot_id=snap.id,
                        position=i + 1,
                        url=f"https://d{offset}-{i}.example/",
                        domain=f"d{offset}-{i}.example",
                        title="x",
                        snippet="",
                        classification_id=cls.id,
                    )
                )

    r = await client.get("/api/brands/trendbrand/snapshots?days=7")
    assert r.status_code == 200, r.text
    snaps = r.json()
    assert len(snaps) == 3
    assert all(s["n_results"] == 3 for s in snaps)

    r2 = await client.get("/api/brands/trendbrand/trend?days=7")
    assert r2.status_code == 200, r2.text
    trend = r2.json()
    assert len(trend) == 3
    # Each point sums to ~100% across 4 categories
    for p in trend:
        total = (
            p["official"]
            + p["affiliate_to_brand"]
            + p["competitor_hijacking"]
            + p["informational"]
        )
        assert 99.0 <= total <= 101.0


@pytest.mark.asyncio
async def test_datetime_fields_serialize_with_explicit_utc_offset(client):
    """Regression: every datetime in API responses must carry an explicit
    UTC offset. Without it the browser parses naive timestamps as local
    time and the dashboard reports the wrong "X hours ago" to users in
    non-UTC timezones.
    """
    # Seed: a brand + a snapshot.
    async with get_session() as session:
        brand = Brand(
            slug="tzbrand",
            name="TzBrand",
            geo="NL",
            official_domains=[],
            known_partners=[],
            known_competitors=[],
        )
        session.add(brand)
        await session.flush()
        snap = SerpSnapshot(
            brand_id=brand.id,
            keyword="tz",
            geo="NL",
            source="seed",
            captured_at=datetime.now(UTC).replace(tzinfo=None),
            raw_serp={},
        )
        session.add(snap)

    r = await client.get("/api/brands/tzbrand/snapshots?days=7")
    assert r.status_code == 200, r.text
    payload = r.json()
    assert len(payload) == 1
    captured_at = payload[0]["captured_at"]
    assert captured_at.endswith("Z") or "+" in captured_at, (
        f"datetime field is missing UTC offset: {captured_at!r}"
    )


@pytest.mark.asyncio
async def test_snapshot_diff_route_does_not_collide_with_id_path(client):
    """Regression: ``/snapshots/diff`` must not be matched by
    ``/snapshots/{snapshot_id: int}`` (would 422 on the path-coercion).
    With no snapshots yet, the diff endpoint should respond 404 — proving
    the literal-path route was selected, not the parameterised sibling.
    """
    r = await client.get("/api/snapshots/diff?a=1&b=2")
    assert r.status_code == 404, r.text
    body = r.json()
    assert "snapshot" in body["detail"].lower()


@pytest.mark.asyncio
async def test_keyword_crud_lifecycle(client):
    """Full CRUD: create → list → patch → delete. Checks 409 on duplicates and 404s."""
    brand_payload = {
        "slug": "kwbrand",
        "name": "KwBrand",
        "geo": "NL",
        "official_domains": [],
        "known_partners": [],
        "known_competitors": [],
    }
    assert (await client.post("/api/brands", json=brand_payload)).status_code == 201

    # Create
    r = await client.post(
        "/api/brands/kwbrand/keywords",
        json={"keyword": "kwbrand", "geo": "nl", "frequency_hours": 12, "active": True},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["keyword"] == "kwbrand"
    assert body["geo"] == "NL"  # normalized
    assert body["frequency_hours"] == 12
    assert body["active"] is True
    assert body["last_scan_at"] is None
    keyword_id = body["id"]

    # Duplicate → 409
    r2 = await client.post(
        "/api/brands/kwbrand/keywords",
        json={"keyword": "kwbrand", "geo": "NL", "frequency_hours": 24},
    )
    assert r2.status_code == 409

    # List
    listing = await client.get("/api/brands/kwbrand/keywords")
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    # Patch frequency + deactivate
    r3 = await client.patch(
        f"/api/brands/keywords/{keyword_id}",
        json={"frequency_hours": 6, "active": False},
    )
    assert r3.status_code == 200
    assert r3.json()["frequency_hours"] == 6
    assert r3.json()["active"] is False

    # Delete
    r4 = await client.delete(f"/api/brands/keywords/{keyword_id}")
    assert r4.status_code == 204
    assert (await client.get("/api/brands/kwbrand/keywords")).json() == []

    # 404 on phantom id
    assert (await client.delete("/api/brands/keywords/99999")).status_code == 404


@pytest.mark.asyncio
async def test_admin_whitelist_update_flows_into_classifier(client):
    """Regression: PUT /whitelists must affect what the classifier sees.

    Earlier the pipeline read from the in-memory ``BrandSeed``, ignoring
    DB updates. We verify here by asserting that ``BrandSeed.from_db_row``
    reflects the persisted change immediately after the admin call.
    """
    payload = {
        "slug": "wlbrand",
        "name": "WhitelistBrand",
        "geo": "NL",
        "official_domains": ["wlbrand.nl"],
        "known_partners": [],
        "known_competitors": [],
    }
    r = await client.post("/api/brands", json=payload)
    assert r.status_code == 201

    r2 = await client.put(
        "/api/brands/wlbrand/whitelists",
        json={"known_competitors": ["evil.nl", "bad.nl"]},
    )
    assert r2.status_code == 200

    async with get_session() as session:
        brand = (
            await session.execute(select(Brand).where(Brand.slug == "wlbrand"))
        ).scalar_one()
    seed = BrandSeed.from_db_row(brand)
    assert seed.known_competitors == frozenset({"evil.nl", "bad.nl"})
    assert seed.official_domains == frozenset({"wlbrand.nl"})
