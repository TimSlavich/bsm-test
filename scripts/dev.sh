#!/usr/bin/env bash
# Run backend (uv run start) + frontend (npm run dev) together.
# Backend runs in background; frontend in foreground.
# Ctrl+C terminates both cleanly.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cyan()  { printf "\033[36m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }

# .env check
if [ ! -f "$ROOT/.env" ]; then
  red "Missing .env. Run ./scripts/setup.sh first."
  exit 1
fi

# Optional: start postgres if docker-compose is available and user wants it
START_PG=${START_POSTGRES:-0}
if [ "$START_PG" = "1" ]; then
  cyan "→ Starting postgres via docker compose"
  docker compose up -d postgres
fi

# Pick a free backend port (default 8000, fallback to 8001 if busy)
BACKEND_PORT=${BACKEND_PORT:-8000}

# Start backend
cyan "→ Backend on http://localhost:$BACKEND_PORT"
(cd "$ROOT/backend" && uv run start --port "$BACKEND_PORT") &
BACKEND_PID=$!

# Trap signals to terminate backend when frontend exits or user hits Ctrl+C
cleanup() {
  echo ""
  cyan "→ Shutting down…"
  if kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
  fi
  green "✓ stopped"
}
trap cleanup EXIT INT TERM

# Wait briefly so backend logs are above frontend logs
sleep 1.5

# Start frontend in foreground
cyan "→ Frontend on http://localhost:5173 (proxies /api → :$BACKEND_PORT)"
(cd "$ROOT/frontend" && npm run dev)
