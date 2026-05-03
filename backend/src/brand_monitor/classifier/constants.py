"""Tunable knobs for the classification pipeline.

Kept in one place so the magic numbers (confidence bounds, escalation
thresholds, fan-out limits, SSRF caps) are reviewable as a unit and don't
drift between modules.
"""

from __future__ import annotations

# --- Stage 3 (LLM arbiter) ---------------------------------------------------

# Stage-3 confidences are clamped into this band. Even if the model returns
# 1.0 we treat it as 0.95 — there's always residual uncertainty in scraped
# text, and a too-confident LLM verdict shouldn't outrank stage-1 whitelist
# hits (which sit at 0.95 by construction).
LLM_MIN_CONFIDENCE = 0.5
LLM_MAX_CONFIDENCE = 0.95

# How many characters of scraped text to include in the prompt. Most pages
# state their purpose in the first viewport; longer excerpts mostly add
# token cost and prompt-injection surface.
LLM_TEXT_EXCERPT_CHARS = 2000

# How many chars of stage-2 ``reasoning`` to inline as context.
LLM_STAGE2_REASONING_CHARS = 300

# Reasons the arbiter didn't run because of *configuration* (vs. a live
# call failure). The fallback path tags the verdict ``llm_disabled`` for
# these so dashboards can distinguish "no key" from "model rejected us".
LLM_DISABLED_REASONS = frozenset({"no_api_key", "litellm_not_installed"})

# --- Stage 2 → Stage 3 escalation -------------------------------------------

# Below this stage-2 confidence we hand the URL to the LLM arbiter.
LLM_ESCALATION_THRESHOLD = 0.65

# --- HTTP fetcher (SSRF + fan-out) ------------------------------------------

DEFAULT_HTTP_TIMEOUT_S = 15.0
MAX_REDIRECTS = 10

# A hostile page can list hundreds of affiliate links — keep fan-out bounded.
REDIRECT_CONCURRENCY = 5

# SSRF guard: cap response bodies. Affiliate trackers are tiny; SERP target
# pages rarely exceed a few hundred KB of text. Anything larger is either
# noise (binary) or a tarpit.
MAX_RESPONSE_BYTES = 2_000_000
