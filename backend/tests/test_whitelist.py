"""Stage-1 whitelist classifier tests."""

from __future__ import annotations

from brand_monitor.classifier.taxonomy import Category, Subcategory
from brand_monitor.classifier.whitelist import classify_whitelist
from brand_monitor.seeds.starcasino import STARCASINO


def test_official_apex():
    c = classify_whitelist("https://starcasino.nl/", STARCASINO)
    assert c is not None
    assert c.category == Category.OFFICIAL
    assert c.subcategory == Subcategory.OFFICIAL_APEX
    assert c.stage_used == 1
    assert c.confidence > 0.9


def test_official_promo_landing():
    c = classify_whitelist("https://starcasino.nl/promo/welcome-bonus", STARCASINO)
    assert c is not None
    assert c.subcategory == Subcategory.OFFICIAL_PROMO_LANDING


def test_official_localized():
    c = classify_whitelist("https://starcasino.be/games", STARCASINO)
    assert c is not None
    assert c.subcategory == Subcategory.OFFICIAL_LOCALIZED


def test_known_partner_review_path():
    c = classify_whitelist("https://casino.nl/review/starcasino", STARCASINO)
    assert c is not None
    assert c.category == Category.AFFILIATE_TO_BRAND
    assert c.subcategory == Subcategory.AFFILIATE_DEDICATED_REVIEW


def test_known_partner_default_listicle():
    c = classify_whitelist("https://casino.nl/best-online-casinos", STARCASINO)
    assert c is not None
    assert c.subcategory == Subcategory.AFFILIATE_LISTICLE


def test_known_competitor():
    c = classify_whitelist("https://hollandcasino.nl/", STARCASINO)
    assert c is not None
    assert c.category == Category.COMPETITOR_HIJACKING
    assert c.subcategory == Subcategory.HIJACKER_DIRECT_COMPETITOR


def test_news_domain():
    c = classify_whitelist("https://nu.nl/economie/starcasino-nieuws", STARCASINO)
    assert c is not None
    assert c.category == Category.INFORMATIONAL
    assert c.subcategory == Subcategory.INFO_NEWS


def test_regulator_domain():
    c = classify_whitelist("https://kansspelautoriteit.nl/onderwerpen/", STARCASINO)
    assert c is not None
    assert c.subcategory == Subcategory.INFO_REGULATOR


def test_unknown_domain_returns_none():
    c = classify_whitelist("https://random-unknown-site.example/", STARCASINO)
    assert c is None
