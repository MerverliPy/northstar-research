#!/usr/bin/env bash
set -euo pipefail

AGENT_URL="${RESEARCH_AGENT_URL:-http://127.0.0.1:8099/health}"
PORTAL_STATUS_URL="${RESEARCH_PORTAL_STATUS_URL:-http://127.0.0.1:3010/api/knowledge/status}"
BRIDGE_URL="${CHAT_IMPORT_BRIDGE_URL:-http://127.0.0.1:3022/health}"

echo "== Northstar Research health check =="

check_url() {
  local label="$1"
  local url="$2"
  local code
  code="$(curl -fsS -o /tmp/northstar-research-health.out -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || true)"
  printf '%-28s %s  %s\n' "$label" "${code:-000}" "$url"
}

check_url "Research Agent" "$AGENT_URL"
check_url "Portal knowledge status" "$PORTAL_STATUS_URL"
check_url "Chat Import Bridge" "$BRIDGE_URL"

if [ -x ./check-auto-extract-eligibility.sh ]; then
  echo
  echo "== Watcher =="
  ./check-auto-extract-eligibility.sh || true
else
  echo
  echo "Watcher script not found in this checkout."
fi
