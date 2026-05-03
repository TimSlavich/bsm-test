# Backend image: Python 3.12 + uv + Playwright Chromium + non-root runtime.
#
# Two-stage build keeps the final image lean: deps are resolved in the
# builder stage with a populated cache; only the venv + source land in
# the runtime stage. Migrations run in-process at startup (entrypoint) —
# acceptable for the single-replica prototype; production multi-replica
# deployments should split migrations into a separate one-shot service.
FROM python:3.12-slim AS builder

ENV UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_COMPILE_BYTECODE=1 \
    PYTHONDONTWRITEBYTECODE=1

# uv: official wheels-based installer (https://docs.astral.sh/uv/)
COPY --from=ghcr.io/astral-sh/uv:0.5.4 /uv /usr/local/bin/uv

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
RUN uv sync --frozen --no-dev


FROM python:3.12-slim AS runtime

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    AUTO_CREATE_TABLES=false

# Runtime system deps. Playwright's `--with-deps` does an apt-get install
# of ~150MB of Chrome-required libraries — accept the size for prototype
# realism. A lean prod image would copy `~/.cache/ms-playwright/` from the
# builder and install only the listed system libs.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 1001 app \
    && useradd --system --uid 1001 --gid app --create-home --home-dir /home/app app \
    && mkdir -p /data \
    && chown -R app:app /data

WORKDIR /app
COPY --from=builder --chown=app:app /app /app

USER app
RUN python -m playwright install chromium

# Re-enter as root only to install the system-level Playwright deps; this
# layer doesn't change between rebuilds because the chromium download is
# already cached in /home/app above.
USER root
RUN python -m playwright install-deps chromium && rm -rf /var/lib/apt/lists/*
USER app

EXPOSE 8000

# Apply migrations then start the server. `start --prod` disables --reload.
CMD ["sh", "-c", "alembic upgrade head && uvicorn brand_monitor.main:app --host 0.0.0.0 --port 8000"]
