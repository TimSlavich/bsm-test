"""Guard: Alembic head must produce the same schema as ``Base.metadata``.

If a model gains a column / index without a matching autogenerate migration,
this test fails — preventing the silent drift between dev (``create_all``)
and prod (Alembic-managed) that's the classic "works on my machine" trap.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext

from brand_monitor.db.models import Base
from brand_monitor.db.session import get_engine


_SQLITE_TYPE_NOISE = (
    sa.JSON,
    sa.Text,
    sa.String,
    sa.DateTime,
    sa.Boolean,
)


def _is_sqlite_type_noise(diff: object) -> bool:
    """Filter only the well-known SQLite-vs-metadata type-comparison noise.

    SQLite has 5 storage classes (NULL/INTEGER/REAL/TEXT/BLOB) and applies
    "type affinity" — it does not preserve ``Text`` vs ``String(N)`` vs
    ``DateTime`` vs ``JSON`` distinctions in a way that round-trips through
    ``compare_metadata``. We allow-list those specific column types only;
    a future ``Integer → BigInteger`` or ``Float → Numeric`` change is
    NOT noise and will surface here even on SQLite.
    """
    if not isinstance(diff, tuple):
        return False
    op = diff[0]
    if op != "modify_type":
        return False
    # Tuple shape: ("modify_type", schema, table, col, info, old_type, new_type)
    try:
        old_type = diff[-2]
        new_type = diff[-1]
    except IndexError:
        return False
    return isinstance(old_type, _SQLITE_TYPE_NOISE) and isinstance(
        new_type, _SQLITE_TYPE_NOISE
    )


@pytest.mark.asyncio
async def test_alembic_head_matches_metadata():
    engine = get_engine()
    backend_root = Path(__file__).resolve().parents[1]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

        def _upgrade(sync_conn) -> None:
            cfg.attributes["connection"] = sync_conn
            command.upgrade(cfg, "head")

        await conn.run_sync(_upgrade)

        def _diff(sync_conn) -> list:
            ctx = MigrationContext.configure(sync_conn)
            return compare_metadata(ctx, Base.metadata)

        diff = await conn.run_sync(_diff)
        dialect_name = (await conn.run_sync(lambda c: c.dialect.name))

    if dialect_name == "sqlite":
        # Only on SQLite: drop the type-noise. Any other diff (added column,
        # removed index, FK change) still fails the test.
        real = [d for d in diff if not _is_sqlite_type_noise(d)]
    else:
        real = list(diff)

    assert not real, (
        f"Alembic head drifted from metadata on {dialect_name!r}:\n{real}"
    )
