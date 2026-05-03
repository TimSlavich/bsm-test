"""Stage 3 — LLM arbiter via LiteLLM.

Contract: structured JSON output, Pydantic-validated. Any failure (network,
invalid JSON, bad subcategory, timeout) returns the stage-2 verdict
unchanged — this stage never raises.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any
from urllib.parse import urlparse

import structlog
from pydantic import BaseModel, Field, ValidationError, field_validator

from ..config import get_settings
from ..seeds.starcasino import BrandSeed
from .algorithm import classify_destinations
from .constants import LLM_DISABLED_REASONS, LLM_MAX_CONFIDENCE, LLM_MIN_CONFIDENCE
from .prompts import build_arbiter_prompt
from .signals import PageSignals
from .taxonomy import (
    SUBCATEGORY_TO_CATEGORY,
    Classification,
    ReasonCode,
    Subcategory,
)

log = structlog.get_logger()


class _LLMResponse(BaseModel):
    subcategory: Subcategory
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = Field(default="", max_length=2000)

    @field_validator("confidence")
    @classmethod
    def _clamp_conf(cls, v: float) -> float:
        return max(LLM_MIN_CONFIDENCE, min(LLM_MAX_CONFIDENCE, v))


def _fallback(stage2: Classification, *, reason: str, extra: dict[str, Any] | None = None) -> Classification:
    """Return the stage-2 verdict tagged with the reason the LLM didn't run.

    Two flags distinguish cause: ``llm_disabled`` (no key / package missing)
    vs ``llm_arbiter_failed`` (live call rejected). Confidence is never bumped.
    """
    flag_key = "llm_disabled" if reason in LLM_DISABLED_REASONS else "llm_arbiter_failed"
    merged_signals = {
        **stage2.signals,
        flag_key: True,
        "llm_failure_reason": reason,
        **(extra or {}),
    }
    return Classification(
        category=stage2.category,
        subcategory=stage2.subcategory,
        confidence=stage2.confidence,
        stage_used=2,
        signals=merged_signals,
        reasoning=f"{stage2.reasoning} | LLM arbiter {flag_key}: {reason}",
        reason_code=stage2.reason_code,
    )


_LANGFUSE_INSTALLED = False


def _maybe_install_langfuse() -> None:
    """Wire the Langfuse callback exactly once per process.

    Without the sentinel, every arbiter call would re-append callbacks and
    leak between test boundaries that monkeypatch ``litellm``.
    """
    global _LANGFUSE_INSTALLED
    if _LANGFUSE_INSTALLED:
        return
    s = get_settings()
    if not s.langfuse_enabled:
        return
    # Verify the Langfuse SDK is actually importable BEFORE telling LiteLLM
    # to call into it. Without this guard, LiteLLM's callback init raises
    # ``ModuleNotFoundError: No module named 'langfuse'`` on every LLM
    # call, which then propagates as ``llm_arbiter_call_failed`` and
    # rotates through the whole model chain pointlessly.
    try:
        import langfuse  # noqa: F401 — presence check
    except ImportError:
        log.warning(
            "langfuse_sdk_missing",
            hint="install the 'langfuse' Python package to enable tracing",
        )
        return
    try:
        import litellm

        if "langfuse" not in (litellm.success_callback or []):
            litellm.success_callback = [*(litellm.success_callback or []), "langfuse"]
        if "langfuse" not in (litellm.failure_callback or []):
            litellm.failure_callback = [*(litellm.failure_callback or []), "langfuse"]
        _LANGFUSE_INSTALLED = True
        log.info("langfuse_callbacks_registered", host=s.langfuse_host)
    except Exception as e:  # noqa: BLE001
        log.warning("langfuse_setup_failed", error=str(e))


async def classify_llm(
    url: str,
    signals: PageSignals,
    redirect_destinations: list[str],
    brand: BrandSeed,
    stage2_classification: Classification,
) -> Classification:
    settings = get_settings()
    if not settings.llm_arbiter_enabled:
        log.info("llm_arbiter_disabled_no_key")
        return _fallback(stage2_classification, reason="no_api_key")

    try:
        from litellm import acompletion
    except ImportError:
        log.warning("litellm_not_installed")
        return _fallback(stage2_classification, reason="litellm_not_installed")

    brand_ratio, comp_ratio = classify_destinations(redirect_destinations, brand)
    prompt = build_arbiter_prompt(
        url, signals, brand, brand_ratio, comp_ratio, stage2_classification
    )

    _maybe_install_langfuse()

    async def _call(model: str) -> Any:
        return await asyncio.wait_for(
            acompletion(
                model=model,
                api_base=settings.litellm_base_url,
                api_key=settings.litellm_api_key,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0,
                max_tokens=400,
                metadata={
                    "trace_name": "brand-monitor.classifier.arbiter",
                    "tags": ["brand-monitor", "stage-3", brand.slug, model],
                },
            ),
            timeout=settings.arbiter_timeout_s,
        )

    # Resilience strategy:
    # 1. Try each model in ``arbiter_model_chain`` (config). On rate-limit
    #    or transient error, rotate to the next model — different OpenRouter
    #    providers serve different models, so a 429 on Llama 3.3 free
    #    doesn't imply a 429 on Gemma 2 free.
    # 2. Within a single model, do one quick retry with backoff for
    #    transient blips. Further retries hold up the scan with little
    #    payoff.
    # 3. If every model in the chain fails, fall back to stage-2 verdict.
    chain = settings.arbiter_model_chain
    response: Any = None
    used_model: str | None = None
    last_err_name = "unknown"
    for model_idx, model in enumerate(chain):
        for attempt in range(2):
            try:
                response = await _call(model)
                used_model = model
                break
            except TimeoutError:
                log.warning(
                    "llm_arbiter_timeout",
                    url=url,
                    model=model,
                    timeout=settings.arbiter_timeout_s,
                )
                last_err_name = "TimeoutError"
                break  # don't retry timeouts; rotate to next model
            except Exception as e:  # noqa: BLE001
                last_err_name = type(e).__name__
                err_text = str(e)
                is_rate_limited = (
                    "RateLimit" in last_err_name or "429" in err_text
                )
                is_transient = (
                    is_rate_limited
                    or "Service" in last_err_name
                    or "503" in err_text
                    or "Timeout" in last_err_name
                )
                if is_transient and attempt == 0:
                    log.warning(
                        "llm_arbiter_transient_retry",
                        url=url,
                        model=model,
                        error=err_text[:200],
                    )
                    await asyncio.sleep(1.5)
                    continue
                log.warning(
                    "llm_arbiter_call_failed",
                    url=url,
                    model=model,
                    error=err_text[:300],
                )
                break  # rotate to next model
        if response is not None:
            break
        if model_idx + 1 < len(chain):
            log.info("llm_arbiter_rotating", from_model=model, to=chain[model_idx + 1])

    if response is None:
        return _fallback(stage2_classification, reason=f"call_failed:{last_err_name}")

    raw = ""
    try:
        # ``acompletion`` is typed as ``ModelResponse | CustomStreamWrapper``;
        # we don't pass ``stream=True`` so it's always the former, but the
        # union confuses static type checkers. Read attributes via getattr
        # and let the except below catch any shape mismatch at runtime.
        choice = getattr(response, "choices", [None])[0]
        message = getattr(choice, "message", None)
        raw = getattr(message, "content", None) or ""
        parsed = _LLMResponse.model_validate(json.loads(raw))
    except (json.JSONDecodeError, ValidationError, AttributeError, IndexError, KeyError, TypeError) as e:
        log.warning("llm_arbiter_invalid_response", url=url, error=str(e), raw=raw[:200])
        return _fallback(stage2_classification, reason=f"invalid_response:{type(e).__name__}")

    sub = parsed.subcategory

    # Anti-injection guardrail: a hostile page can talk the model into
    # ``official_*`` by embedding fake instructions. Cross-check against
    # objective signals — a domain that isn't in the brand's whitelist
    # AND has zero brand-bound redirects can never legitimately be official.
    if sub.value.startswith("official_"):
        url_host = (urlparse(url).hostname or "").lower().lstrip("www.")
        in_whitelist = any(url_host == d or url_host.endswith("." + d) for d in brand.official_domains)
        if not in_whitelist and brand_ratio == 0.0:
            log.warning(
                "llm_arbiter_official_rejected",
                url=url,
                host=url_host,
                brand_ratio=brand_ratio,
            )
            return _fallback(
                stage2_classification,
                reason="official_claim_unsubstantiated",
                extra={"llm_subcategory_rejected": sub.value},
            )

    final_signals = {
        **stage2_classification.signals,
        "llm_reasoning": parsed.reasoning,
        "llm_model": used_model or settings.arbiter_model,
    }
    return Classification(
        category=SUBCATEGORY_TO_CATEGORY[sub],
        subcategory=sub,
        confidence=parsed.confidence,
        stage_used=3,
        signals=final_signals,
        reasoning=parsed.reasoning or f"[LLM] {sub.value}",
        reason_code=ReasonCode.LLM_ARBITER,
    )
