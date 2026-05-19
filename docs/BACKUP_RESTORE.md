# Backup and Restore

## Backup policy

Run backups before:

- Upgrades
- Schema changes
- Graph rebuilds
- Data cleanup
- New destructive migration tooling

## Backup script (`scripts/backup.sh`)

```bash
./scripts/backup.sh [output-dir]
```

The script:
- Checks for `pg_dump` availability and exits with clear error if missing.
- Dumps PostgreSQL (custom format) and copies ChromaDB data.
- Creates a compressed tar archive with timestamp.
- Default output: `~/northstar-backups/`.

## Restore script (`scripts/restore.sh`)

```bash
./scripts/restore.sh <backup-file>
```

The script:
- **Prompts for confirmation** before destroying the current database.
- Requires explicit `y`/`Y` to proceed; anything else aborts.
- Restores PostgreSQL with `pg_restore --clean --if-exists`.
- Restores ChromaDB data if present in the backup.

## Restore acceptance criteria

A backup is not trusted until a restore drill proves that:

- Project records are readable.
- Source/report records are present.
- Graph export can be imported into a clean target.
- Quality checks still pass after restore.
- Operator dashboards can read restored state.

## Git policy

Do not commit backup archives, database dumps, graph exports, or local restore artifacts. Store them outside the repository or in a dedicated encrypted backup system.
