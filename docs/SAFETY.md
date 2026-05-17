# Safety Doctrine

## Non-negotiable rules

1. PostgreSQL remains the source of truth.
2. Neo4j remains the visual relationship layer.
3. Existing graphs are skipped by default.
4. Force extraction is disabled unless intentionally rebuilding.
5. Cleanup remains read-only or dry-run by default.
6. Backups run before upgrades, rebuilds, or schema changes.
7. Restore drills validate that backups are usable.
8. Chat import is manual approval first; no silent auto-import.

## Safe extraction pattern

```bash
./check-auto-extract-eligibility.sh
./controlled-auto-extract-run-one.sh
./controlled-auto-extract-run-batch.sh validate
./controlled-auto-extract-run-batch.sh run 2
```

Run extraction only when `eligible_project_count` is greater than `0`.

## Destructive action policy

Any script that deletes, merges, prunes, rewrites, or force-rebuilds data must:

- Require an explicit flag.
- Print exactly what it will affect.
- Offer dry-run mode first.
- Require a fresh backup or export validation.
- Record an audit artifact.
