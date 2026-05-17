#!/usr/bin/env bash
set -euo pipefail

echo "== Secret/runtime file guard =="

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Not inside a git working tree; skipping staged-file check."
  exit 0
fi

bad=0
while IFS= read -r path; do
  case "$path" in
    .env|.env.*|*.sqlite|*.sqlite3|*.db|*.pem|*.key|*.p12|*.pfx|*.tar|*.tar.gz|*.zip|backups/*|data/*|exports/*|logs/*)
      if [ "$path" != "data/.gitkeep" ] && [ "$path" != "exports/.gitkeep" ] && [ "$path" != "logs/.gitkeep" ]; then
        echo "blocked staged runtime/secret-like file: $path"
        bad=1
      fi
      ;;
  esac
done < <(git diff --cached --name-only)

if [ "$bad" -ne 0 ]; then
  echo "Refusing: remove blocked files from staging before commit."
  exit 1
fi

echo "No blocked staged files detected."
