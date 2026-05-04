"""Request validators that produce structured, frontend-friendly errors.

Pydantic catches schema-level mistakes (missing field, wrong type, range
violation), but it can't run async DB lookups or business-rule checks.
This module fills that gap: every validator returns a list of
:class:`ValidationProblem` records, keyed by field and reason code, so
the frontend can render inline field errors instead of showing a raw
500 / 404 message.

Frontend contract: a 400 response with body shape::

    {"detail": [
        {"field": "brand_slug", "code": "brand_unknown",
         "message": "Brand 'foo' is not registered."},
        ...
    ]}

The ``code`` field is stable and i18n-able on the frontend; ``message``
is a human-readable fallback in English.
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Brand
from ..seeds.starcasino import BRANDS
from ..serp.geos import supported_geo_codes


def _supported_geos() -> frozenset[str]:
    """Source of truth: the SERP fetcher's geo registry. Adding a new
    geo profile in ``serp/geos.py`` makes it instantly accepted by the
    validator — no duplication."""
    return frozenset(supported_geo_codes())

MAX_KEYWORD_LENGTH = 200


@dataclass(frozen=True)
class ValidationProblem:
    field: str
    code: str
    message: str

    def as_dict(self) -> dict[str, str]:
        return {"field": self.field, "code": self.code, "message": self.message}


async def validate_scan_request(
    *,
    session: AsyncSession,
    brand_slug: str,
    keyword: str,
    geo: str,
    top_n: int,
) -> list[ValidationProblem]:
    """Run all scan-request checks. Empty list = the request is good.

    Each check is independent so the response surfaces every problem the
    user has at once, rather than forcing them to fix-and-resubmit one
    field at a time.
    """
    problems: list[ValidationProblem] = []

    # ---- brand_slug -------------------------------------------------
    slug = (brand_slug or "").strip().lower()
    if not slug:
        problems.append(
            ValidationProblem(
                field="brand_slug",
                code="brand_required",
                message="Brand slug is required.",
            )
        )
    else:
        # Known either via bundled seed (auto-registers on first use) or
        # via an existing DB row created through the admin endpoints.
        in_seed = slug in BRANDS
        in_db = (
            await session.execute(select(Brand.id).where(Brand.slug == slug))
        ).scalar_one_or_none() is not None
        if not (in_seed or in_db):
            known = sorted(BRANDS.keys())
            problems.append(
                ValidationProblem(
                    field="brand_slug",
                    code="brand_unknown",
                    message=(
                        f"Brand '{slug}' is not registered. "
                        f"Known seeded brands: {', '.join(known)}. "
                        "Create one via POST /api/brands first."
                    ),
                )
            )

    # ---- keyword ----------------------------------------------------
    cleaned_kw = (keyword or "").strip()
    if not cleaned_kw:
        problems.append(
            ValidationProblem(
                field="keyword",
                code="keyword_required",
                message="Keyword is required.",
            )
        )
    elif len(cleaned_kw) > MAX_KEYWORD_LENGTH:
        problems.append(
            ValidationProblem(
                field="keyword",
                code="keyword_too_long",
                message=f"Keyword must be {MAX_KEYWORD_LENGTH} characters or fewer.",
            )
        )

    # ---- geo --------------------------------------------------------
    geo_norm = (geo or "").strip().upper()
    if not geo_norm:
        problems.append(
            ValidationProblem(
                field="geo",
                code="geo_required",
                message="Geo is required.",
            )
        )
    elif geo_norm not in _supported_geos():
        supported = ", ".join(sorted(_supported_geos()))
        problems.append(
            ValidationProblem(
                field="geo",
                code="geo_unsupported",
                message=(
                    f"Geo '{geo_norm}' is not yet supported. "
                    f"Supported: {supported}."
                ),
            )
        )

    # ---- top_n ------------------------------------------------------
    # Pydantic enforces 1≤n≤20 on the schema, but the SSE endpoint takes
    # this as a Query param so we double-check for direct callers.
    if top_n < 1 or top_n > 20:
        problems.append(
            ValidationProblem(
                field="top_n",
                code="top_n_out_of_range",
                message="top_n must be between 1 and 20.",
            )
        )

    return problems
