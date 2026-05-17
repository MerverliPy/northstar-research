#!/usr/bin/env bash
set -euo pipefail

echo "== Northstar Research health check =="

fail=0

check_url() {
  local label="$1"
  local url="$2"
  local code
  code="$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null || true)"
  if [ "$code" = "200" ]; then
    printf 'ok   %-28s %s\n' "$label" "$url"
  else
    printf 'FAIL %-28s %s (HTTP %s)\n' "$label" "$url" "${code:-000}"
    fail=1
  fi
}

check_url "Research Agent" "http://127.0.0.1:8099/health"
check_url "Chat Import Bridge" "http://127.0.0.1:3022/health"
check_url "Research Portal" "http://127.0.0.1:3010/health"

echo "---"
if [ "$fail" -eq 0 ]; then
  echo "All services healthy."
else
  echo "Some services are DOWN."
  exit 1
fi
