# Safety Doctrine

## Non-negotiable rules

1. PostgreSQL remains the source of truth.
2. Neo4j remains the visual relationship layer.
3. Existing graphs are skipped by default.
4. Force extraction is disabled unless intentionally rebuilding.
5. Cleanup remains read-only or dry-run by default.
6. Chat import promotion is gated behind `PROMOTION_ENABLED` (defaults to false).
7. Backups run before upgrades, rebuilds, or schema changes.
8. Restore drills validate that backups are usable and require explicit confirmation.

## Safety gates

| Flag | Default | Scope |
|---|---|---|
| `FORCE_GRAPH_EXTRACTION` | `false` | Enables graph extraction endpoints |
| `ENABLE_DESTRUCTIVE_CLEANUP` | `false` | Enables destructive cleanup routes |
| `PROMOTION_ENABLED` | `false` | Enables chat-import promotion to Agent |

All three gates default to disabled. Gated routes return 403 unless explicitly enabled.

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

## Infrastructure hardening

- `restore.sh` prompts for confirmation before destructive restore.
- `backup.sh` checks for `pg_dump` availability and exits with clear error if missing.
- Dockerfile runs as non-root `appuser` (multi-stage build).
- Docker-compose services use `restart: unless-stopped` with Neo4j healthcheck.
- Neo4j password has no hardcoded default — must be explicitly configured in both config and environment.
- SPA file serving has path traversal protection.
- SSE chat endpoint does not use wildcard CORS headers (relies on CORS middleware).
- Portal proxy whitelists only safe headers (accept, accept-encoding, user-agent).
