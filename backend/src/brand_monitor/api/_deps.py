"""Shared FastAPI dependencies."""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session


async def session_dep() -> AsyncIterator[AsyncSession]:
    async with get_session() as s:
        yield s
