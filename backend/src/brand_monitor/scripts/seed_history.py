"""Seed N fake historical snapshots so the trend chart has data on a fresh DB.

Usage::

    uv run python -m brand_monitor.scripts.seed_history --brand starcasino --days 7

This is *not* a substitute for real historical scans — it lets you demo the
trend visualisation immediately after a fresh ``docker compose up``. The
generated snapshots are clearly marked with ``source="seed"`` in
``serp_snapshots`` so they can be filtered out for production analytics.
"""

from __future__ import annotations

import argparse
import asyncio
import random
from datetime import timedelta

import structlog
from sqlalchemy import select

from ..classifier.taxonomy import Category, Subcategory
from ..db import get_session
from ..db.models import (
    Brand,
    DomainClassification,
    SerpResult,
    SerpSnapshot,
)
from ..seeds.starcasino import BRANDS
from ..time import utc_now

log = structlog.get_logger()

# Plausible mock distribution that drifts over time so the trend chart
# actually wiggles. (official, affiliate, hijacker, info) — must sum to 10.
_DEFAULT_TRAJECTORY = [
    (3, 4, 1, 2),
    (3, 5, 1, 1),
    (4, 4, 1, 1),
    (4, 3, 2, 1),
    (3, 3, 2, 2),
    (3, 4, 2, 1),
    (4, 4, 1, 1),
    (4, 5, 0, 1),
    (3, 4, 1, 2),
    (3, 5, 1, 1),
]


SUBS_BY_CATEGORY: dict[Category, list[Subcategory]] = {
    Category.OFFICIAL: [Subcategory.OFFICIAL_APEX, Subcategory.OFFICIAL_LOCALIZED],
    Category.AFFILIATE_TO_BRAND: [
        Subcategory.AFFILIATE_LISTICLE,
        Subcategory.AFFILIATE_DEDICATED_REVIEW,
        Subcategory.AFFILIATE_BONUS_PROMO,
    ],
    Category.COMPETITOR_HIJACKING: [
        Subcategory.HIJACKER_AFFILIATE_TO_OTHERS,
        Subcategory.HIJACKER_DIRECT_COMPETITOR,
    ],
    Category.INFORMATIONAL: [Subcategory.INFO_OTHER, Subcategory.INFO_NEWS],
}


async def seed(brand_slug: str, days: int) -> None:
    if brand_slug not in BRANDS:
        raise SystemExit(f"Unknown brand '{brand_slug}'. Known: {list(BRANDS)}")
    seed_obj = BRANDS[brand_slug]

    async with get_session() as session:
        brand = (
            await session.execute(select(Brand).where(Brand.slug == brand_slug))
        ).scalar_one_or_none()
        if brand is None:
            brand = Brand(
                slug=seed_obj.slug,
                name=seed_obj.name,
                geo=seed_obj.geo,
                official_domains=list(seed_obj.official_domains),
                known_partners=list(seed_obj.known_partners),
                known_competitors=list(seed_obj.known_competitors),
            )
            session.add(brand)
            await session.flush()

        rng = random.Random(42)
        for day_offset in range(days):
            captured = utc_now() - timedelta(days=days - day_offset)
            mix = _DEFAULT_TRAJECTORY[day_offset % len(_DEFAULT_TRAJECTORY)]
            categories: list[Category] = (
                [Category.OFFICIAL] * mix[0]
                + [Category.AFFILIATE_TO_BRAND] * mix[1]
                + [Category.COMPETITOR_HIJACKING] * mix[2]
                + [Category.INFORMATIONAL] * mix[3]
            )
            rng.shuffle(categories)

            snap = SerpSnapshot(
                brand_id=brand.id,
                keyword=seed_obj.monitored_keywords[0],
                geo=brand.geo,
                source="seed",
                captured_at=captured,
                raw_serp={"seeded": True},
            )
            session.add(snap)
            await session.flush()

            for pos, cat in enumerate(categories, start=1):
                sub = rng.choice(SUBS_BY_CATEGORY[cat])
                domain = f"seed-{cat.value[:6]}-{day_offset}-{pos}.example"
                cls = DomainClassification(
                    brand_id=brand.id,
                    domain=domain,
                    category=cat.value,
                    subcategory=sub.value,
                    confidence=round(rng.uniform(0.6, 0.95), 2),
                    stage_used=rng.choice([1, 2, 3]),
                    signals={"seeded": True},
                    reasoning=f"[seed] {sub.value}",
                    classified_at=captured,
                )
                session.add(cls)
                await session.flush()
                session.add(
                    SerpResult(
                        snapshot_id=snap.id,
                        position=pos,
                        url=f"https://{domain}/",
                        domain=domain,
                        title=f"Seeded {sub.value} #{pos}",
                        snippet="Seeded fixture",
                        classification_id=cls.id,
                    )
                )
        await session.flush()
        log.info("seeded_history", brand=brand_slug, days=days)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed fake historical snapshots")
    parser.add_argument("--brand", default="starcasino")
    parser.add_argument("--days", type=int, default=7)
    args = parser.parse_args()
    asyncio.run(seed(args.brand, args.days))


if __name__ == "__main__":
    main()
