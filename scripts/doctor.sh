#!/usr/bin/env bash
set -euo pipefail

echo "== Northstar Research doctor =="

fail=0

need() {
  if command -v "$1" >/dev/null 2>&1; then
    printf 'ok   %s\n' "$1"
  else
    printf 'MISS %s\n' "$1"
    fail=1
  fi
}

need git
need bash
need curl
need docker

if command -v docker >/dev/null 2>&1; then
  if docker compose version >/dev/null 2>&1; then
    echo "ok   docker compose"
  else
    echo "MISS docker compose"
    fail=1
  fi
fi

if [ -f .env ]; then
  echo "warn .env exists (make sure it's gitignored)"
else
  echo "MISS .env file at repo root"
  fail=1
fi

if command -v python3 >/dev/null 2>&1; then
  pyver=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
  if awk "BEGIN {exit !($pyver >= 3.11)}"; then
    echo "ok   python3 ($(python3 --version 2>&1))"
  else
    echo "MISS python3 >= 3.11 (found $(python3 --version 2>&1))"
    fail=1
  fi
else
  echo "MISS python3"
  fail=1
fi

if [ -d .venv ]; then
  echo "ok   .venv exists"
else
  echo "MISS .venv directory"
  fail=1
fi

for pkg in northstar-db northstar-llm northstar-models northstar-vector; do
  if python3 -c "import $pkg" 2>/dev/null; then
    printf 'ok   package %s importable\n' "$pkg"
  else
    printf 'MISS package %s not importable\n' "$pkg"
    fail=1
  fi
done

if curl -fsS --max-time 3 http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "ok   Ollama reachable at http://127.0.0.1:11434"
else
  echo "WARN Ollama not reachable (optional, start manually if needed)"
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

check_file() {
  if [ -f "$1" ]; then
    printf 'ok   file %s\n' "$1"
  else
    printf 'MISS file %s\n' "$1"
    fail=1
  fi
}

check_file "$ROOT/apps/research-agent/pyproject.toml"
check_file "$ROOT/apps/chat-import-bridge/pyproject.toml"
check_file "$ROOT/apps/research-portal/pyproject.toml"

check_file "$ROOT/apps/research-agent/research_agent/main.py"
check_file "$ROOT/apps/chat-import-bridge/chat_import_bridge/main.py"
check_file "$ROOT/apps/research-portal/research_portal/main.py"

for tmpl in base.html dashboard.html extraction.html quality.html cleanup.html graph_viewer.html; do
  check_file "$ROOT/apps/research-portal/research_portal/templates/$tmpl"
done

check_file "$ROOT/apps/research-agent/migrations/alembic.ini"
check_file "$ROOT/apps/research-agent/migrations/env.py"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  if docker compose -f "$ROOT/docker/docker-compose.yml" config --quiet 2>/dev/null; then
    echo "ok   docker compose config valid"
  else
    echo "FAIL docker compose config invalid"
    fail=1
  fi
fi

echo "---"
if [ "$fail" -eq 0 ]; then
  echo "All critical checks passed."
else
  echo "Some critical checks FAILED."
  exit 1
fi
