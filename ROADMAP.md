# Roadmap

## Phase 1 - Repository foundation

- Keep root docs and runbooks accurate.
- Add minimal CI for shell syntax and repository hygiene.
- Preserve safe defaults for local-only operation.

## Phase 2 - Daily research workflow

- Finish manual Chat Import Bridge promotion flow.
- Map staged chat imports into durable PostgreSQL research projects only after review.
- Keep the bridge file/SQLite staged layer separate from production research records until promotion.

## Phase 3 - Graph automation hardening

- Use watcher and controlled gate for completed projects without graphs.
- Keep batch extraction capped and quality-gated.
- Expand graph quality checks before enabling any automated writes beyond extraction.

## Phase 4 - Backup and restore confidence

- Automate backup verification.
- Run repeatable Neo4j export/restore drills.
- Document restore acceptance criteria.
