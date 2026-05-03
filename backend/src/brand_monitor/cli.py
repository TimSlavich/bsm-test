"""Console entry points exposed via [project.scripts] in pyproject.toml.

Usage::

    uv run start            → uvicorn dev server
    uv run start --prod     → uvicorn without --reload
    uv run migrate          → alembic upgrade head (in-process, no subprocess)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config


def start() -> None:
    """Run the FastAPI app with uvicorn."""
    parser = argparse.ArgumentParser(description="Run the Brand Monitor API")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--prod", action="store_true", help="Disable --reload")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    uvicorn.run(
        "brand_monitor.main:app",
        host=args.host,
        port=args.port,
        reload=not args.prod,
        workers=args.workers if args.prod else 1,
        log_level="info",
    )


def migrate() -> None:
    """Run ``alembic upgrade head`` in-process (no subprocess, no PATH lookup)."""
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    command.upgrade(cfg, "head")
