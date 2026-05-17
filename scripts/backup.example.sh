#!/usr/bin/env bash
set -euo pipefail

# Example wrapper only. Prefer your existing backup-local-ai-research.sh on the production machine.

PROJECT_DIR="${PROJECT_DIR:-$HOME/local-ai-research}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/local-ai-research-backups}"
stamp="$(date +%Y-%m-%d_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

echo "Creating example file backup from $PROJECT_DIR"
tar --exclude='.git' --exclude='node_modules' --exclude='.venv' -czf "$BACKUP_DIR/local-ai-research_$stamp.tar.gz" -C "$(dirname "$PROJECT_DIR")" "$(basename "$PROJECT_DIR")"
echo "$BACKUP_DIR/local-ai-research_$stamp.tar.gz"
