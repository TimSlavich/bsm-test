"""Persist bundled ``BrandSeed`` rows + monitored keywords on startup.

Idempotent and additive — safe to invoke on every boot. Lets the
classifier rely on the DB rather than the in-memory seed (so admin
endpoint updates take effect immediately on the next scan).
"""

from __future__ import annotations

import structlog
from sqlalchemy import select

from .db import get_session
from .db.models import Brand, BrandKeyword
from .seeds.starcasino import BRANDS

log = structlog.get_logger()


async def bootstrap_brand_seeds() -> None:
    """Ensure each ``BRANDS[slug]`` exists in the DB along with its keywords."""
    async with get_session() as session:
        for seed in BRANDS.values():
            stmt = select(Brand).where(Brand.slug == seed.slug)
            brand = (await session.execute(stmt)).scalar_one_or_none()
            if brand is None:
                brand = Brand(
                    slug=seed.slug,
                    name=seed.name,
                    geo=seed.geo,
                    official_domains=list(seed.official_domains),
                    known_partners=list(seed.known_partners),
                    known_competitors=list(seed.known_competitors),
                )
                session.add(brand)
                await session.flush()
                log.info("bootstrap_brand_inserted", slug=seed.slug)

            existing_kw = (
                await session.execute(
                    select(BrandKeyword.keyword).where(BrandKeyword.brand_id == brand.id)
                )
            ).scalars().all()
            existing_set = set(existing_kw)
            for kw in seed.monitored_keywords:
                if kw in existing_set:
                    continue
                session.add(
                    BrandKeyword(
                        brand_id=brand.id,
                        keyword=kw,
                        geo=seed.geo,
                        frequency_hours=24,
                        active=True,
                    )
                )
            await session.flush()
