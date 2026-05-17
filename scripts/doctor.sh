#!/usr/bin/env bash
set -euo pipefail

echo "== Northstar Research repository doctor =="

need() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'ok   %s\n' "$1"
  else
    printf 'miss %s\n' "$1"
  fi
}

need git
need bash
need curl
need docker

if command -v docker >/dev/null 2>&1; then
  docker compose version >/dev/null 2>&1 && echo "ok   docker compose" || echo "miss docker compose"
fi

[ -f .env ] && echo "warn .env exists; verify it is not tracked" || echo "ok   no root .env file"

scripts/verify-no-secrets.sh

echo "Doctor checks completed."
