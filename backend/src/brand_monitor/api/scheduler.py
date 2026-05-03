"""Scheduler inspection endpoint."""

from __future__ import annotations

from fastapi import APIRouter

from ..scheduler import get_scheduler

router = APIRouter(prefix="/scheduler", tags=["scheduler"])


@router.get("/jobs")
async def list_scheduler_jobs() -> dict:
    sched = get_scheduler()
    if sched is None:
        return {"enabled": False, "jobs": []}
    return {
        "enabled": True,
        "jobs": [
            {
                "id": j.id,
                "next_run_time": j.next_run_time.isoformat() if j.next_run_time else None,
                "trigger": str(j.trigger),
            }
            for j in sched.get_jobs()
        ],
    }
