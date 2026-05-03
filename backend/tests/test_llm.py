"""Tests for stage-3 LLM arbiter via mocked LiteLLM."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from brand_monitor.classifier.llm import classify_llm
from brand_monitor.classifier.signals import PageSignals
from brand_monitor.classifier.taxonomy import (
    Category,
    Classification,
    Subcategory,
)
from brand_monitor.config import get_settings
from brand_monitor.seeds.starcasino import STARCASINO


def _stage2_lowconf() -> Classification:
    return Classification(
        category=Category.INFORMATIONAL,
        subcategory=Subcategory.INFO_OTHER,
        confidence=0.55,
        stage_used=2,
        signals={"foo": "bar"},
        reasoning="Ambiguous signals",
    )


def _signals() -> PageSignals:
    return PageSignals(
        domain="example.com",
        affiliate_links=["https://t.example.com/aff?ref=123"],
        text_content="StarCasino review with bonus details.",
        brand_mention_count=3,
        title="StarCasino Review",
        h1_text="StarCasino: Honest Review",
    )


def _mock_response(content: str):
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


@pytest.fixture(autouse=True)
def _enable_arbiter(monkeypatch):
    """Force arbiter enabled with a fake key for the duration of these tests."""
    get_settings.cache_clear()
    monkeypatch.setenv("LITELLM_API_KEY", "test-key")
    monkeypatch.setenv("LITELLM_BASE_URL", "https://openrouter.example/api/v1")
    monkeypatch.setenv("ARBITER_MODEL", "openrouter/test/test-model")
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_llm_returns_stage3_on_valid_response():
    payload = json.dumps(
        {
            "subcategory": "affiliate_dedicated_review",
            "confidence": 0.82,
            "reasoning": "Clear partner review with brand schema.",
        }
    )
    with patch(
        "litellm.acompletion", new=AsyncMock(return_value=_mock_response(payload))
    ):
        result = await classify_llm(
            url="https://example.com/review",
            signals=_signals(),
            redirect_destinations=["https://starcasino.nl/welcome"],
            brand=STARCASINO,
            stage2_classification=_stage2_lowconf(),
        )
    assert result.stage_used == 3
    assert result.subcategory == Subcategory.AFFILIATE_DEDICATED_REVIEW
    assert result.category == Category.AFFILIATE_TO_BRAND
    assert 0.5 <= result.confidence <= 0.95
    assert "llm_reasoning" in result.signals


@pytest.mark.asyncio
async def test_llm_invalid_subcategory_falls_back_to_stage2():
    payload = json.dumps(
        {"subcategory": "totally_made_up", "confidence": 0.9, "reasoning": "x"}
    )
    stage2 = _stage2_lowconf()
    with patch(
        "litellm.acompletion", new=AsyncMock(return_value=_mock_response(payload))
    ):
        result = await classify_llm(
            url="https://example.com/x",
            signals=_signals(),
            redirect_destinations=[],
            brand=STARCASINO,
            stage2_classification=stage2,
        )
    assert result.stage_used == 2
    assert result.subcategory == stage2.subcategory
    assert result.confidence == stage2.confidence
    assert result.signals["llm_arbiter_failed"] is True


@pytest.mark.asyncio
async def test_llm_invalid_json_falls_back_to_stage2():
    stage2 = _stage2_lowconf()
    with patch(
        "litellm.acompletion",
        new=AsyncMock(return_value=_mock_response("not-a-json {{{")),
    ):
        result = await classify_llm(
            url="https://example.com/x",
            signals=_signals(),
            redirect_destinations=[],
            brand=STARCASINO,
            stage2_classification=stage2,
        )
    assert result.stage_used == 2
    assert result.signals["llm_arbiter_failed"] is True
    assert "JSONDecodeError" in result.signals["llm_failure_reason"]


@pytest.mark.asyncio
async def test_llm_network_error_falls_back():
    stage2 = _stage2_lowconf()
    with patch(
        "litellm.acompletion",
        new=AsyncMock(side_effect=RuntimeError("connection refused")),
    ):
        result = await classify_llm(
            url="https://example.com/x",
            signals=_signals(),
            redirect_destinations=[],
            brand=STARCASINO,
            stage2_classification=stage2,
        )
    assert result.stage_used == 2
    assert result.signals["llm_arbiter_failed"] is True
    assert "RuntimeError" in result.signals["llm_failure_reason"]


@pytest.mark.asyncio
async def test_llm_disabled_when_no_api_key(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.delenv("LITELLM_API_KEY", raising=False)
    monkeypatch.setenv("LITELLM_API_KEY", "")
    stage2 = _stage2_lowconf()
    result = await classify_llm(
        url="https://example.com/x",
        signals=_signals(),
        redirect_destinations=[],
        brand=STARCASINO,
        stage2_classification=stage2,
    )
    assert result.stage_used == 2
    assert result.signals["llm_failure_reason"] == "no_api_key"
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_llm_clamps_extreme_confidence():
    payload = json.dumps(
        {"subcategory": "info_other", "confidence": 0.99, "reasoning": "very sure"}
    )
    with patch(
        "litellm.acompletion", new=AsyncMock(return_value=_mock_response(payload))
    ):
        result = await classify_llm(
            url="https://example.com/x",
            signals=_signals(),
            redirect_destinations=[],
            brand=STARCASINO,
            stage2_classification=_stage2_lowconf(),
        )
    # clamped to LLM_MAX_CONFIDENCE = 0.95
    assert result.confidence <= 0.95
