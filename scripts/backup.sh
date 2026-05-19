#!/usr/bin/env bash
set -euo pipefail

command -v pg_dump >/dev/null 2>&1 || { echo "ERROR: pg_dump not found. Install PostgreSQL client tools."; exit 1; }

OUTPUT_DIR="${1:-$HOME/northstar-backups}"
STAMP="$(date +%Y-%m-%d_%H-%M-%S)"
BACKUP_FILE="$OUTPUT_DIR/northstar-backup_$STAMP.tar.gz"
TMPDIR="$(mktemp -d)"

trap 'rm -rf "$TMPDIR"' EXIT

mkdir -p "$OUTPUT_DIR"

echo "Backing up PostgreSQL..."
PGPASSWORD="${POSTGRES_PASSWORD:-northstar}" pg_dump \
  -h "${POSTGRES_HOST:-127.0.0.1}" \
  -p "${POSTGRES_PORT:-5432}" \
  -U "${POSTGRES_USER:-northstar}" \
  -d "${POSTGRES_DB:-northstar}" \
  -F c \
  -f "$TMPDIR/northstar-pg.dump"

CHROMA_DIR="${CHROMA_PERSIST_DIR:-$HOME/.cache/northstar/chromadb}"
if [ -d "$CHROMA_DIR" ]; then
  echo "Backing up ChromaDB from $CHROMA_DIR..."
  cp -a "$CHROMA_DIR" "$TMPDIR/chromadb"
else
  echo "WARN ChromaDB directory not found at $CHROMA_DIR, skipping."
fi

echo "Creating archive..."
tar -czf "$BACKUP_FILE" -C "$TMPDIR" .

echo "Backup written to $BACKUP_FILE"
