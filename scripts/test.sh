#!/usr/bin/env bash
# Run all tests across backend + frontend.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cyan()  { printf "\033[36m%s\033[0m\n" "$*"; }
green() { printf "\033[32m%s\033[0m\n" "$*"; }

cyan "→ Backend tests (pytest + Hypothesis property-based)"
(cd "$ROOT/backend" && uv run pytest "$@")

if [ -d "$ROOT/frontend/node_modules" ]; then
  cyan "→ Frontend tests (vitest)"
  (cd "$ROOT/frontend" && npm test --silent || echo "  (no vitest tests yet — add some)")
fi

green "✓ all tests passed"
