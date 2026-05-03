"""Top-level API router — composes the per-resource sub-routers."""

from __future__ import annotations

from fastapi import APIRouter

from . import brands, favicons, scans, scheduler

router = APIRouter(prefix="/api", tags=["brand-monitor"])
router.include_router(scans.router)
router.include_router(brands.router)
router.include_router(scheduler.router)
router.include_router(favicons.router)


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "ok"}
