# Contributing

## Operating rules

1. Preserve PostgreSQL as the source of truth.
2. Treat Neo4j as a visual and query layer, not the master copy.
3. Keep graph cleanup read-only or dry-run unless a reviewed migration explicitly enables writes.
4. Never force graph extraction in routine changes.
5. Keep scripts small, reviewable, and safe for mobile copy/paste workflows.
6. Do not commit real secrets, databases, exports, backups, local logs, or private host details.

## Pull request checklist

- [ ] Adds or updates documentation for operator-visible behavior.
- [ ] Includes rollback or no-op behavior for operational scripts.
- [ ] Avoids destructive database/graph actions by default.
- [ ] Runs `make doctor` and `make lint`.
- [ ] Does not add private runtime artifacts.
