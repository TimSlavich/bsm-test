"""Verify taxonomy invariants — a single source of truth must stay consistent."""

from __future__ import annotations

import pytest

from brand_monitor.classifier.taxonomy import (
    CATEGORY_COLOR,
    SUBCATEGORY_TO_CATEGORY,
    Category,
    Classification,
    Subcategory,
)


def test_every_subcategory_has_a_category():
    for sub in Subcategory:
        assert sub in SUBCATEGORY_TO_CATEGORY, f"{sub} not mapped to a category"


def test_every_category_has_a_color():
    for cat in Category:
        assert cat in CATEGORY_COLOR, f"{cat} missing dashboard color"


def test_classification_rejects_invalid_subcategory_for_category():
    with pytest.raises(ValueError, match="does not belong"):
        Classification(
            category=Category.OFFICIAL,
            subcategory=Subcategory.AFFILIATE_LISTICLE,
            confidence=0.9,
            stage_used=1,
            signals={},
        )


def test_classification_rejects_invalid_confidence():
    with pytest.raises(ValueError, match=r"confidence"):
        Classification(
            category=Category.OFFICIAL,
            subcategory=Subcategory.OFFICIAL_APEX,
            confidence=1.5,
            stage_used=1,
            signals={},
        )


def test_classification_rejects_invalid_stage():
    with pytest.raises(ValueError, match=r"stage_used"):
        Classification(
            category=Category.OFFICIAL,
            subcategory=Subcategory.OFFICIAL_APEX,
            confidence=0.9,
            stage_used=4,
            signals={},
        )


def test_count_of_subcategories_per_category():
    """Document the agreed taxonomy: 4 categories × specific subcategory counts."""
    counts: dict[Category, int] = {}
    for cat in SUBCATEGORY_TO_CATEGORY.values():
        counts[cat] = counts.get(cat, 0) + 1
    assert counts[Category.OFFICIAL] == 4
    assert counts[Category.AFFILIATE_TO_BRAND] == 4
    assert counts[Category.COMPETITOR_HIJACKING] == 3
    assert counts[Category.INFORMATIONAL] == 5
    assert sum(counts.values()) == 16
