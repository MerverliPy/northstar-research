#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <backup-file>"
  exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "ERROR: backup file not found: $BACKUP_FILE"
  exit 1
fi

TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

echo "Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$TMPDIR"

if [ -f "$TMPDIR/northstar-pg.dump" ]; then
  echo "Restoring PostgreSQL..."
  PGPASSWORD="${POSTGRES_PASSWORD:-northstar}" pg_restore \
    -h "${POSTGRES_HOST:-127.0.0.1}" \
    -p "${POSTGRES_PORT:-5432}" \
    -U "${POSTGRES_USER:-northstar}" \
    -d "${POSTGRES_DB:-northstar}" \
    --clean \
    --if-exists \
    "$TMPDIR/northstar-pg.dump"
else
  echo "WARN no PostgreSQL dump found in backup, skipping."
fi

if [ -d "$TMPDIR/chromadb" ]; then
  CHROMA_DIR="${CHROMA_PERSIST_DIR:-$HOME/.cache/northstar/chromadb}"
  echo "Restoring ChromaDB to $CHROMA_DIR..."
  rm -rf "$CHROMA_DIR"
  mkdir -p "$(dirname "$CHROMA_DIR")"
  cp -a "$TMPDIR/chromadb" "$CHROMA_DIR"
else
  echo "WARN no ChromaDB backup found, skipping."
fi

echo "Restore complete from $BACKUP_FILE"
