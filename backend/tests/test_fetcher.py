"""Regression tests for SERP parsers — replays saved fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest

from brand_monitor.serp.fetcher import (
    SerpFetcher,
    _root,
    parse_ddg_html,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_root_strips_www_and_keeps_full_nl_hostname():
    # Critical: NL hosts like *.com.nl / *.co.nl / *.net.nl are NOT on the
    # Public Suffix List as multi-level suffixes. We use full hostname so
    # 'starcasino.nl' and 'starcasino.com.nl' don't collapse to the same key.
    assert _root("https://starcasino.nl/casino") == "starcasino.nl"
    assert _root("https://starcasino.com.nl/") == "starcasino.com.nl"
    assert _root("https://starcasino.co.nl/") == "starcasino.co.nl"
    assert _root("https://www.starcasino.nl/x") == "starcasino.nl"
    assert _root("starcasino.be") == "starcasino.be"


def test_parse_ddg_starcasino_nl_fixture_returns_at_least_10_results():
    html = (FIXTURES / "ddg_starcasino_nl.html").read_text(encoding="utf-8")
    results = parse_ddg_html(html)
    assert len(results) >= 10
    # Position numbers are 1-indexed and contiguous
    assert [r.position for r in results[:10]] == list(range(1, 11))
    # The official starcasino.nl must appear and unwrapped (not a duckduckgo URL)
    assert any("starcasino.nl" in r.domain for r in results)
    for r in results:
        assert r.url.startswith("http")
        assert "duckduckgo.com" not in r.domain


@pytest.mark.asyncio
async def test_fetcher_falls_back_to_fixture_when_upstream_disabled(tmp_path):
    fixture = FIXTURES / "ddg_starcasino_nl.html"
    f = SerpFetcher(prefer_playwright=False, fixture_path=fixture)
    # Force DDG path off by patching _fetch_duckduckgo to fail
    async def _boom(*a, **kw):
        raise RuntimeError("simulated upstream failure")

    f._fetch_duckduckgo = _boom  # type: ignore[assignment]
    results = await f.fetch("starcasino", geo="NL", num=10)
    assert len(results) == 10
