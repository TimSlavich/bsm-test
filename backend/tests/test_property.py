"""Property-based tests with Hypothesis — invariants of the classifier.

These are *true* property tests: inputs are generated from broad strategies
(arbitrary domains, arbitrary signal mixes) and the asserted invariants
must hold for every generated example. They protect against bugs that
parametrized lists never see — empty edges, unicode, asymmetric mention
counts, redirect-ratio boundary conditions, etc.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

from brand_monitor.classifier.algorithm import classify_algorithm
from brand_monitor.classifier.pipeline import LLM_ESCALATION_THRESHOLD
from brand_monitor.classifier.signals import PageSignals
from brand_monitor.classifier.taxonomy import (
    SUBCATEGORY_TO_CATEGORY,
    Category,
    Classification,
    Subcategory,
)
from brand_monitor.classifier.whitelist import (
    WHITELIST_CONFIDENCE,
    classify_whitelist,
)
from brand_monitor.domain import canonical_domain
from brand_monitor.seeds.starcasino import STARCASINO

pytestmark = pytest.mark.property


# -- Strategies ---------------------------------------------------------------

# Generate hostnames spanning the realistic NL iGaming SERP space, including
# the multi-level non-PSL suffixes (com.nl, co.nl, net.nl) that broke the
# old tldextract-based root-domain logic.
_LABEL = st.from_regex(r"[a-z0-9][a-z0-9-]{0,30}[a-z0-9]", fullmatch=True)
_TLD = st.sampled_from(
    ["com", "nl", "be", "de", "io", "co.uk", "com.nl", "co.nl", "net.nl"]
)
_HOST = st.builds(lambda label, tld: f"{label}.{tld}", _LABEL, _TLD)
_URL = st.builds(
    lambda host, path: f"https://{host}{path}",
    _HOST,
    st.from_regex(r"/[a-z0-9/_\-]{0,40}", fullmatch=True),
)


# -- Invariants on canonical_domain ------------------------------------------


@given(_URL)
@settings(max_examples=300, deadline=None)
def test_canonical_domain_is_lowercase_and_idempotent(url: str):
    a = canonical_domain(url)
    assert a == a.lower()
    # Idempotent: a second call on the result returns the same value.
    assert canonical_domain(a) == a


@given(_HOST)
def test_canonical_domain_strips_optional_www(host: str):
    assume(not host.startswith("www."))
    assert canonical_domain(f"https://www.{host}/x") == host
    assert canonical_domain(f"https://{host}/x") == host


@given(_URL)
def test_canonical_domain_handles_userinfo_and_port(url: str):
    """userinfo@host:port should not leak into the canonical identifier."""
    out = canonical_domain(url.replace("https://", "https://user:pass@", 1))
    assert "@" not in out
    out_p = canonical_domain(url.replace("https://", "https://user@host.example:8443/x"))
    assert ":" not in out_p


# -- Invariants on the classifier --------------------------------------------


@given(
    affiliate_links=st.lists(
        _URL.map(lambda u: f"{u}?ref=42"),  # tag every URL as a tracker-shaped link
        max_size=15,
    ),
    brand_mentions=st.integers(min_value=0, max_value=200),
    competitor_mentions=st.integers(min_value=0, max_value=200),
    destinations=st.lists(_HOST, max_size=15),
    schema_types=st.lists(
        st.sampled_from(["Review", "Article", "NewsArticle", "Organization", "FAQPage"]),
        max_size=4,
    ),
)
@settings(
    max_examples=300, deadline=None, suppress_health_check=[HealthCheck.too_slow]
)
def test_classifier_always_returns_valid_classification(
    affiliate_links, brand_mentions, competitor_mentions, destinations, schema_types
):
    """The Stage-2 algorithm must always return a valid Classification."""
    s = PageSignals(
        domain="random.example",
        affiliate_links=affiliate_links,
        has_tracker_in_links=False,
        schema_types=schema_types,
        schema_review_target=None,
        text_content="x" * 100,
        brand_mention_count=brand_mentions,
        competitor_mention_counts={"hollandcasino": competitor_mentions},
        primary_cta_url=None,
        h1_text="",
        title="",
    )
    full_destinations = [f"https://{d}/" for d in destinations]
    c = classify_algorithm(s, full_destinations, STARCASINO)
    # Invariant set:
    assert isinstance(c, Classification)
    assert 0.0 <= c.confidence <= 1.0
    assert SUBCATEGORY_TO_CATEGORY[c.subcategory] == c.category
    assert c.stage_used == 2


@given(
    brand_ratio=st.floats(min_value=0.6, max_value=1.0),
    affiliate_count=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_majority_brand_redirects_imply_affiliate_to_brand(
    brand_ratio: float, affiliate_count: int
):
    """When ≥60% of redirects go to the brand, verdict must be affiliate-to-brand.

    This is the *anti-hijacker* invariant — the core classification claim
    of the system, and the most important property to enforce.
    """
    n_brand = max(1, int(affiliate_count * brand_ratio))
    n_other = affiliate_count - n_brand
    destinations = [
        f"https://{next(iter(STARCASINO.official_domains))}/x" for _ in range(n_brand)
    ] + [f"https://random{i}.example/x" for i in range(n_other)]
    s = PageSignals(
        domain="partner.example",
        affiliate_links=[f"https://t.example/aff?{i}" for i in range(affiliate_count)],
        text_content="StarCasino review " * 5,
        brand_mention_count=5,
        title="StarCasino Review",
    )
    c = classify_algorithm(s, destinations, STARCASINO)
    assert c.category == Category.AFFILIATE_TO_BRAND, (
        f"Expected affiliate_to_brand for brand_ratio={brand_ratio}, got {c.category}"
    )


@given(
    comp_ratio=st.floats(min_value=0.6, max_value=1.0),
    affiliate_count=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_majority_competitor_redirects_imply_hijacker(
    comp_ratio: float, affiliate_count: int
):
    """When ≥60% of redirects go to competitors → competitor_hijacking."""
    n_comp = max(1, int(affiliate_count * comp_ratio))
    n_other = affiliate_count - n_comp
    competitor = next(iter(STARCASINO.known_competitors))
    destinations = [f"https://{competitor}/x" for _ in range(n_comp)] + [
        f"https://other{i}.example/x" for i in range(n_other)
    ]
    s = PageSignals(
        domain="hijacker.example",
        affiliate_links=[f"https://t.example/aff?{i}" for i in range(affiliate_count)],
        text_content="Looks like StarCasino but not really",
        brand_mention_count=3,
    )
    c = classify_algorithm(s, destinations, STARCASINO)
    assert c.category == Category.COMPETITOR_HIJACKING


@given(st.sampled_from(list(STARCASINO.official_domains)))
def test_official_whitelist_invariant(domain: str):
    """A domain in official_domains must always classify Official @ stage 1."""
    c = classify_whitelist(f"https://{domain}/", STARCASINO)
    assert c is not None
    assert c.category == Category.OFFICIAL
    assert c.stage_used == 1
    assert c.confidence == WHITELIST_CONFIDENCE


@given(st.sampled_from(list(STARCASINO.known_competitors)))
def test_competitor_whitelist_invariant(domain: str):
    """Known competitor → hijacker_direct_competitor @ stage 1."""
    c = classify_whitelist(f"https://{domain}/", STARCASINO)
    assert c is not None
    assert c.subcategory == Subcategory.HIJACKER_DIRECT_COMPETITOR
    assert c.stage_used == 1


@given(_HOST)
@settings(max_examples=200, deadline=None)
def test_unknown_host_misses_whitelist(host: str):
    """Random hosts not in any seed list must return None at stage 1."""
    assume(host not in STARCASINO.official_domains)
    assume(host not in STARCASINO.known_partners)
    assume(host not in STARCASINO.known_competitors)
    # Avoid colliding with the static info-domain seed list.
    from brand_monitor.seeds.info_domains import INFO_DOMAIN_TO_SUBCATEGORY

    assume(host not in INFO_DOMAIN_TO_SUBCATEGORY)
    c = classify_whitelist(f"https://{host}/", STARCASINO)
    assert c is None


def test_low_confidence_threshold_is_consistent():
    """The escalation threshold + LOW_CONFIDENCE constant must agree.

    Stage-2 returns LOW_CONFIDENCE on its ambiguous fallback; the pipeline
    only escalates to LLM when stage-2 confidence < threshold. If the two
    drift apart, the LLM never fires (or fires too eagerly).
    """
    from brand_monitor.classifier.algorithm import LOW_CONFIDENCE

    assert LOW_CONFIDENCE < LLM_ESCALATION_THRESHOLD, (
        "Stage-2 ambiguous fallback must trigger LLM escalation by construction"
    )
