# Northstar Research — Build Workflow Rules

## Conductor Role

You are the conductor. Your job:
1. Read BUILD_CONTRACT.md before every wave
2. Spawn parallel agents for each task in a wave
3. Collect results, write next contract, proceed

## Agent Naming Convention

| Agent ID | Role | Wave |
|---|---|---|
| `foundation` | docker-compose, .env, systemd, scripts | Wave 1 |
| `schema` | Alembic migrations, seed data, init SQL | Wave 1 |
| `gitops` | Dockerfiles, pyproject.toml per package, CI, Makefile | Wave 1 |
| `agent-smith` | Research Agent service (port 8099) | Wave 2 |
| `bridge` | Chat Import Bridge service (port 3022) | Wave 2 |
| `portal` | Research Portal service (port 3010) | Wave 2 |
| `qa` | Unit + integration + E2E tests, 80% coverage | Wave 3 |
| `shield` | Backup/restore scripts, extraction CLI, docs sync | Wave 3 |

## Handoff Protocol

1. Before starting a wave, read the current `contracts/BUILD_CONTRACT.md`
2. After completing a wave, write `contracts/BUILD_CONTRACT.md` with:
   - What was built (exact file paths, port numbers, model names)
   - Safety flag values (FORCE_GRAPH_EXTRACTION, ENABLE_DESTRUCTIVE_CLEANUP, etc.)
   - API route contracts for all services
   - What the next wave needs to know
3. Never skip reading the contract

## Safety Rules

- FORCE_GRAPH_EXTRACTION=false by default
- ENABLE_DESTRUCTIVE_CLEANUP=false by default
- PostgreSQL is source of truth. Neo4j is derived.
- Chat Import Bridge never mutates PG or Neo4j before explicit promotion
- All destructive actions require backup validation + explicit flag
- Extraction returns 403 unless FORCE_GRAPH_EXTRACTION=true
- Cleanup is read-only/dry-run unless ENABLE_DESTRUCTIVE_CLEANUP=true

## Wave Execution Order

Wave 0 → Wave 1 (parallel) → Wave 2 (parallel) → Wave 3 (parallel)

Within parallel waves, spawn all agents simultaneously. Each agent gets:
- The current BUILD_CONTRACT.md
- Its specific task description
- Exact file paths it must create
