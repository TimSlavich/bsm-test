"""App configuration via pydantic-settings + .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # `cwd` differs between `uv run start` (backend/) and docker compose
        # (project root). Both candidates are listed explicitly; later wins.
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "sqlite+aiosqlite:///./brand_monitor.db"
    serp_engine: str = "playwright"
    litellm_base_url: str | None = None
    litellm_api_key: str | None = None
    arbiter_model: str = "openrouter/meta-llama/llama-3.3-70b-instruct:free"
    # Comma-separated fallback chain. When the primary model rate-limits or
    # errors, the arbiter rotates to the next entry. Leave empty to use only
    # ``arbiter_model``; populate with multiple free models for resilience.
    arbiter_models: str = (
        "openrouter/meta-llama/llama-3.3-70b-instruct:free,"
        "openrouter/meta-llama/llama-3.2-3b-instruct:free"
    )
    arbiter_provider: str = "openrouter"
    arbiter_timeout_s: float = 25.0
    # Prod path runs Alembic; dev / pytest flip this to True for `create_all`.
    auto_create_tables: bool = True
    # In-process scheduler — off by default so dev runs don't spawn scans.
    scheduler_enabled: bool = False
    bootstrap_brand_seeds: bool = True
    cors_allow_origins: str = "http://localhost:5173"
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"
    log_level: str = "INFO"

    @property
    def llm_arbiter_enabled(self) -> bool:
        return bool(self.litellm_api_key)

    @property
    def langfuse_enabled(self) -> bool:
        return bool(self.langfuse_public_key and self.langfuse_secret_key)

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]

    @property
    def arbiter_model_chain(self) -> list[str]:
        """Ordered fallback list. Falls back to ``arbiter_model`` if the
        ``arbiter_models`` env var is empty or only whitespace."""
        chain = [m.strip() for m in self.arbiter_models.split(",") if m.strip()]
        return chain or [self.arbiter_model]


@lru_cache
def get_settings() -> Settings:
    return Settings()
