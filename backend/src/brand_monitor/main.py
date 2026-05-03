"""FastAPI app entry point."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .bootstrap import bootstrap_brand_seeds
from .config import get_settings
from .db.models import Base
from .db.session import get_engine
from .scheduler import start_scheduler, stop_scheduler

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: ARG001
    settings = get_settings()
    engine = get_engine()
    # Prod / docker manage schema via Alembic; dev + tests use create_all.
    if settings.auto_create_tables:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        log.info("startup_create_all", db=settings.database_url)
    else:
        log.info("startup_alembic_managed", db=settings.database_url)

    if settings.bootstrap_brand_seeds:
        await bootstrap_brand_seeds()

    if settings.scheduler_enabled:
        await start_scheduler()

    try:
        yield
    finally:
        if settings.scheduler_enabled:
            await stop_scheduler()
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Brand SERP Monitor",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(router)
    return app


app = create_app()
