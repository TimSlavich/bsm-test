"""Pydantic v2 request/response schemas for the API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, Field, PlainSerializer


def _ensure_utc(v: datetime | str | None) -> datetime | str | None:
    """Treat naive datetimes as UTC. We persist naive UTC throughout (see
    ``brand_monitor.time``) but the wire format must be unambiguous so the
    browser doesn't re-interpret as local time."""
    if isinstance(v, datetime) and v.tzinfo is None:
        return v.replace(tzinfo=timezone.utc)
    return v


def _ser_utc(v: datetime | None) -> str | None:
    if v is None:
        return None
    if v.tzinfo is None:
        v = v.replace(tzinfo=timezone.utc)
    # ``isoformat`` on an aware datetime emits ``…+00:00`` which JS Date
    # parses correctly. Replace the offset with ``Z`` for visual brevity.
    return v.isoformat().replace("+00:00", "Z")


# Always-aware-UTC datetime annotation — coerces naive on the way in,
# serializes with explicit ``Z`` suffix on the way out.
UtcDatetime = Annotated[
    datetime,
    BeforeValidator(_ensure_utc),
    PlainSerializer(_ser_utc, return_type=str, when_used="json"),
]


class ScanRequest(BaseModel):
    """Loose schema — business-rule validation lives in
    :func:`brand_monitor.api.validation.validate_scan_request` so all
    field problems surface in one structured 400 response instead of
    Pydantic intercepting and returning only the first.
    """

    brand_slug: str = Field("", examples=["starcasino"])
    keyword: str = Field("", examples=["starcasino"])
    geo: str = Field("NL", examples=["NL"])
    top_n: int = Field(10, examples=[10])


class ResultItem(BaseModel):
    position: int
    url: str
    domain: str
    title: str
    category: str
    subcategory: str
    confidence: float
    stage_used: int
    reasoning: str
    reason_code: str | None = None
    # Structured signals — preferred over parsing ``reasoning`` on the
    # frontend. Shape mirrors ``DomainClassification.signals`` JSON column.
    signals: dict[str, Any] = Field(default_factory=dict)


class ScanResponse(BaseModel):
    snapshot_id: int
    captured_at: UtcDatetime
    brand_slug: str
    keyword: str
    geo: str
    # Which fetcher strategy actually fired ("google_playwright",
    # "duckduckgo_html", "fixture", or "none").
    source: str
    n_results: int
    results: list[ResultItem]


class CategoryShare(BaseModel):
    category: str
    count: int
    percent: float


class SnapshotSummary(BaseModel):
    snapshot_id: int
    captured_at: UtcDatetime
    keyword: str
    geo: str
    n_results: int
    distribution: list[CategoryShare]


class DomainRow(BaseModel):
    domain: str
    category: str
    subcategory: str
    confidence: float
    stage_used: int
    classified_at: UtcDatetime


class TrendPoint(BaseModel):
    """One day in a brand's category-share trend."""

    date: str  # ISO date YYYY-MM-DD
    snapshot_id: int
    official: float
    affiliate_to_brand: float
    competitor_hijacking: float
    informational: float


class BrandSnapshotSummary(BaseModel):
    snapshot_id: int
    captured_at: UtcDatetime
    keyword: str
    geo: str
    n_results: int


class BrandCreate(BaseModel):
    slug: str = Field(..., min_length=2, max_length=64)
    name: str
    geo: str = Field(..., min_length=2, max_length=4)
    official_domains: list[str] = Field(default_factory=list)
    known_partners: list[str] = Field(default_factory=list)
    known_competitors: list[str] = Field(default_factory=list)


class BrandWhitelistsUpdate(BaseModel):
    official_domains: list[str] | None = None
    known_partners: list[str] | None = None
    known_competitors: list[str] | None = None


class BrandResponse(BaseModel):
    model_config = {"from_attributes": True}

    slug: str
    name: str
    geo: str
    official_domains: list[str]
    known_partners: list[str]
    known_competitors: list[str]


class DiffEntry(BaseModel):
    domain: str
    title: str
    url: str
    category: str
    subcategory: str
    position: int


class DiffMoved(BaseModel):
    domain: str
    title: str
    url: str
    category_from: str
    category_to: str
    subcategory_from: str
    subcategory_to: str
    position_from: int
    position_to: int


class SnapshotDiff(BaseModel):
    a: BrandSnapshotSummary
    b: BrandSnapshotSummary
    added: list[DiffEntry]      # in B, not in A
    removed: list[DiffEntry]    # in A, not in B
    moved: list[DiffMoved]      # in both, position or category changed
    unchanged: list[DiffEntry]  # same position, same category


class KeywordResponse(BaseModel):
    id: int
    brand_slug: str
    keyword: str
    geo: str
    frequency_hours: int
    active: bool
    last_scan_at: UtcDatetime | None = None
    next_run_at: UtcDatetime | None = None


class KeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=128)
    geo: str = Field(..., min_length=2, max_length=4)
    frequency_hours: int = Field(24, ge=1, le=24 * 30)
    active: bool = True


class KeywordUpdate(BaseModel):
    keyword: str | None = Field(None, min_length=1, max_length=128)
    geo: str | None = Field(None, min_length=2, max_length=4)
    frequency_hours: int | None = Field(None, ge=1, le=24 * 30)
    active: bool | None = None
