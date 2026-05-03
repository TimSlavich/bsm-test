#!/usr/bin/env bash
# Quick CLI to trigger a scan against a running backend.
# Usage:
#   ./scripts/scan.sh                           # defaults: starcasino, NL
#   ./scripts/scan.sh starcasino "starcasino bonus" NL
#   ./scripts/scan.sh starcasino starcasino NL 5

set -euo pipefail

BRAND="${1:-starcasino}"
KEYWORD="${2:-starcasino}"
GEO="${3:-NL}"
TOP_N="${4:-10}"
HOST="${HOST:-http://localhost:8000}"

curl -sS -X POST "$HOST/api/scans" \
  -H "Content-Type: application/json" \
  -d "{\"brand_slug\":\"$BRAND\",\"keyword\":\"$KEYWORD\",\"geo\":\"$GEO\",\"top_n\":$TOP_N}" \
  | python3 -m json.tool
