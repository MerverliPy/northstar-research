# Backup and Restore

## Backup policy

Run backups before:

- Upgrades
- Schema changes
- Graph rebuilds
- Data cleanup
- New destructive migration tooling

## Example commands

```bash
./backup-local-ai-research.sh
~/upgrade-neo4j-export-restore-drill.sh
```

## Restore acceptance criteria

A backup is not trusted until a restore drill proves that:

- Project records are readable.
- Source/report records are present.
- Graph export can be imported into a clean target.
- Quality checks still pass after restore.
- Operator dashboards can read restored state.

## Git policy

Do not commit backup archives, database dumps, graph exports, or local restore artifacts. Store them outside the repository or in a dedicated encrypted backup system.
