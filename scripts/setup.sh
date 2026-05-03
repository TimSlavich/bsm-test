#!/usr/bin/env bash
# First-time setup: install all deps for backend and frontend.
# Run this once after cloning the repo.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cyan()  { printf "\033[36m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }
red()   { printf "\033[31m%s\033[0m\n" "$*"; }

# 1. Check uv
if ! command -v uv >/dev/null 2>&1; then
  red "uv is not installed."
  echo "Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi
cyan "uv: $(uv --version)"

# 2. Check node + npm
if ! command -v npm >/dev/null 2>&1; then
  red "npm is not installed (Node.js 20+ required)."
  exit 1
fi
cyan "node: $(node --version)"
cyan "npm:  $(npm --version)"

# 3. .env
if [ ! -f "$ROOT/.env" ]; then
  cp "$ROOT/.env.example" "$ROOT/.env"
  cyan "Created .env from .env.example"
else
  cyan ".env already exists — leaving it alone"
fi

# 4. Backend
cyan "→ uv sync (backend)"
(cd "$ROOT/backend" && uv sync)

cyan "→ playwright install chromium"
(cd "$ROOT/backend" && uv run playwright install chromium)

# 5. Frontend
cyan "→ npm install (frontend)"
(cd "$ROOT/frontend" && npm install)

green ""
green "Setup complete. Next:"
green "  ./scripts/dev.sh        # start backend + frontend together"
green "  ./scripts/test.sh       # run all tests"
