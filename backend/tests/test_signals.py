"""Signal extractor tests with HTML fixtures inline."""

from __future__ import annotations

from brand_monitor.classifier.signals import (
    count_keyword_in_text,
    extract_affiliate_links,
    extract_clean_text,
    extract_schema_types,
    extract_signals,
    is_affiliate_link,
)


def test_is_affiliate_link_path_pattern():
    assert is_affiliate_link("https://example.com/go/starcasino")
    assert is_affiliate_link("https://example.com/out/?id=42")
    assert is_affiliate_link("https://example.com/visit/welcome")


def test_is_affiliate_link_query_param():
    assert is_affiliate_link("https://example.com/casino?ref=abc")
    assert is_affiliate_link("https://example.com/?aff=12345&utm=x")


def test_is_affiliate_link_tracker_domain():
    assert is_affiliate_link("https://trk.voluum.com/abc123")


def test_is_not_affiliate_link():
    assert not is_affiliate_link("https://example.com/news/article")
    assert not is_affiliate_link("https://wikipedia.org/wiki/Casino")


def test_extract_affiliate_links_from_html():
    html = """
    <html><body>
        <a href="https://nice-review.com/go/starcasino?ref=42">Play</a>
        <a href="https://nice-review.com/about">About</a>
        <a href="/internal-page">Internal</a>
        <a href="https://hollandcasino.nl/visit/?aff=99">Holland</a>
    </body></html>
    """
    links = extract_affiliate_links(html, "https://nice-review.com/")
    assert "https://nice-review.com/go/starcasino?ref=42" in links
    assert "https://hollandcasino.nl/visit/?aff=99" in links
    assert all("about" not in link for link in links)


def test_extract_schema_review_target():
    html = """
    <html><head>
    <script type="application/ld+json">
    {"@type": "Review", "itemReviewed": {"@type": "Organization", "name": "StarCasino"}, "reviewRating": {"ratingValue": 4.5}}
    </script>
    </head><body></body></html>
    """
    types, target = extract_schema_types(html)
    assert "Review" in types
    assert target == "StarCasino"


def test_extract_schema_news_article():
    html = """
    <script type="application/ld+json">{"@type": "NewsArticle", "headline": "iGaming news"}</script>
    """
    types, target = extract_schema_types(html)
    assert "NewsArticle" in types
    assert target is None


def test_count_keyword_case_insensitive():
    text = "StarCasino is the best. We tried StarCasino for a week."
    assert count_keyword_in_text(text, "starcasino") == 2


def test_clean_text_strips_scripts():
    html = "<html><body><script>evil()</script><p>visible</p><style>x</style></body></html>"
    cleaned = extract_clean_text(html)
    assert "visible" in cleaned
    assert "evil" not in cleaned
    assert "x" not in cleaned


def test_extract_signals_e2e():
    html = """
    <html>
    <head><title>StarCasino review — best NL casinos</title>
    <script type="application/ld+json">{"@type":"Review","itemReviewed":{"name":"StarCasino"}}</script>
    </head>
    <body>
    <h1>Why StarCasino is the top pick</h1>
    <p>StarCasino offers great bonuses. Compare with HollandCasino and Unibet.</p>
    <a href="https://review.example/go/starcasino?ref=1" class="cta-btn">Play at StarCasino</a>
    <a href="https://review.example/go/hollandcasino?ref=2">Play at HollandCasino</a>
    </body></html>
    """
    s = extract_signals(
        html,
        "https://review.example/best-casinos",
        brand_name="StarCasino",
        competitor_names=["hollandcasino.nl", "unibet.nl"],
    )
    assert len(s.affiliate_links) == 2
    assert s.brand_mention_count >= 2
    assert s.competitor_mention_counts.get("hollandcasino", 0) >= 1
    assert s.schema_review_target == "StarCasino"
    assert "starcasino" in (s.primary_cta_url or "").lower()
