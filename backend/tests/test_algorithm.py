"""Stage-2 algorithm classifier rule tests."""

from __future__ import annotations

from brand_monitor.classifier.algorithm import classify_algorithm
from brand_monitor.classifier.signals import PageSignals
from brand_monitor.classifier.taxonomy import Category, Subcategory
from brand_monitor.seeds.starcasino import STARCASINO


def _signals(**kwargs) -> PageSignals:
    defaults = dict(
        domain="example.com",
        affiliate_links=[],
        has_tracker_in_links=False,
        schema_types=[],
        schema_review_target=None,
        text_content="",
        brand_mention_count=0,
        competitor_mention_counts={},
        primary_cta_url=None,
        h1_text="",
        title="",
    )
    defaults.update(kwargs)
    return PageSignals(**defaults)


def test_partner_majority_redirects_to_brand():
    s = _signals(
        affiliate_links=["https://example.com/go/sc1", "https://example.com/go/sc2"],
        title="Best NL casinos 2026",
        brand_mention_count=5,
    )
    destinations = ["https://starcasino.nl/welcome", "https://starcasino.nl/play"]
    c = classify_algorithm(s, destinations, STARCASINO)
    assert c.category == Category.AFFILIATE_TO_BRAND
    assert c.confidence > 0.7


def test_hijacker_majority_redirects_to_competitors():
    s = _signals(
        affiliate_links=["https://example.com/go/x", "https://example.com/go/y"],
        title="Best NL casinos including starcasino",
        brand_mention_count=2,
        competitor_mention_counts={"hollandcasino": 5, "unibet": 3},
    )
    destinations = ["https://hollandcasino.nl/visit", "https://unibet.nl/welcome"]
    c = classify_algorithm(s, destinations, STARCASINO)
    assert c.category == Category.COMPETITOR_HIJACKING
    assert c.subcategory == Subcategory.HIJACKER_AFFILIATE_TO_OTHERS


def test_textbait_hijacker():
    """Brand heavily mentioned but redirects go elsewhere — classic hijacker."""
    s = _signals(
        affiliate_links=["https://example.com/go/x"],
        brand_mention_count=10,
        competitor_mention_counts={"hollandcasino": 1},
    )
    destinations = ["https://hollandcasino.nl/play"]
    c = classify_algorithm(s, destinations, STARCASINO)
    assert c.category == Category.COMPETITOR_HIJACKING


def test_no_affiliate_links_news():
    s = _signals(
        affiliate_links=[],
        schema_types=["NewsArticle"],
        brand_mention_count=2,
        title="StarCasino raises eyebrows",
    )
    c = classify_algorithm(s, [], STARCASINO)
    assert c.category == Category.INFORMATIONAL
    assert c.subcategory == Subcategory.INFO_NEWS


def test_no_affiliate_links_no_brand_other():
    s = _signals(affiliate_links=[], brand_mention_count=0)
    c = classify_algorithm(s, [], STARCASINO)
    assert c.category == Category.INFORMATIONAL


def test_schema_review_targets_brand_strong_partner_signal():
    s = _signals(
        affiliate_links=["https://r.com/go/x"],
        schema_review_target="starcasino",
        title="Review",
        brand_mention_count=5,
    )
    # Even with no resolved destinations, schema target alone yields high confidence
    c = classify_algorithm(s, [], STARCASINO)
    assert c.category == Category.AFFILIATE_TO_BRAND
    assert c.confidence >= 0.85


def test_low_confidence_escalation_signal():
    s = _signals(
        affiliate_links=["https://x.com/go/x"],
        brand_mention_count=2,
        competitor_mention_counts={"hollandcasino": 2},
    )
    # 50/50 split with no brand mention dominance — falls into ambiguous
    destinations = ["https://starcasino.nl/", "https://hollandcasino.nl/"]
    c = classify_algorithm(s, destinations, STARCASINO)
    # Either side reaches 0.5 threshold on the lower confidence path
    assert c.confidence < 0.85
