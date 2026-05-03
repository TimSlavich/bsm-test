"""SQLAlchemy 2.0 models. Datetimes are naive UTC throughout — see ``time.py``."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# JSONB on Postgres (GIN-indexable, operator support); plain JSON on SQLite.
JsonCol = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass


class Brand(Base):
    __tablename__ = "brands"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    geo: Mapped[str] = mapped_column(String(8))
    official_domains: Mapped[list[str]] = mapped_column(JsonCol, default=list)
    known_partners: Mapped[list[str]] = mapped_column(JsonCol, default=list)
    known_competitors: Mapped[list[str]] = mapped_column(JsonCol, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    keywords: Mapped[list["BrandKeyword"]] = relationship(back_populates="brand")
    snapshots: Mapped[list["SerpSnapshot"]] = relationship(back_populates="brand")


class BrandKeyword(Base):
    __tablename__ = "brand_keywords"
    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(128))
    geo: Mapped[str] = mapped_column(String(8))
    frequency_hours: Mapped[int] = mapped_column(Integer, default=24)
    active: Mapped[bool] = mapped_column(default=True)

    brand: Mapped[Brand] = relationship(back_populates="keywords")
    __table_args__ = (UniqueConstraint("brand_id", "keyword", "geo", name="uq_brand_kw_geo"),)


class SerpSnapshot(Base):
    __tablename__ = "serp_snapshots"
    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(128), index=True)
    geo: Mapped[str] = mapped_column(String(8), index=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
    source: Mapped[str] = mapped_column(String(32), default="playwright")
    raw_serp: Mapped[dict[str, Any]] = mapped_column(JsonCol, default=dict)

    brand: Mapped[Brand] = relationship(back_populates="snapshots")
    results: Mapped[list["SerpResult"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class SerpResult(Base):
    __tablename__ = "serp_results"
    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_id: Mapped[int] = mapped_column(ForeignKey("serp_snapshots.id", ondelete="CASCADE"))
    position: Mapped[int]
    # Tracker chains with embedded encoded URLs blow past 2048 chars.
    url: Mapped[str] = mapped_column(Text)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(Text, default="")
    snippet: Mapped[str] = mapped_column(Text, default="")

    classification_id: Mapped[int | None] = mapped_column(
        ForeignKey("domain_classifications.id"), nullable=True
    )

    snapshot: Mapped[SerpSnapshot] = relationship(back_populates="results")
    classification: Mapped["DomainClassification | None"] = relationship()


class DomainClassification(Base):
    __tablename__ = "domain_classifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey("brands.id", ondelete="CASCADE"), index=True)
    domain: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    subcategory: Mapped[str] = mapped_column(String(64), index=True)
    confidence: Mapped[float]
    stage_used: Mapped[int]
    signals: Mapped[dict[str, Any]] = mapped_column(JsonCol, default=dict)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    reason_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    classified_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )

    __table_args__ = (UniqueConstraint("brand_id", "domain", name="uq_brand_domain_classification"),)
