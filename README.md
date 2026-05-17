# Northstar Research

Northstar Research is a local AI research system for source-backed research, structured project memory, controlled knowledge-graph extraction, and daily-use research workflows. The system is designed around a clear split of responsibilities:

- **PostgreSQL** is the source of truth for projects, sources, reports, summaries, metadata, and durable research records.
- **Neo4j** is the visual relationship layer for project graphs, entities, claims, sources, reports, and quality-reviewed graph outputs.
- **Research Agent** runs research, project APIs, extraction APIs, health checks, quality scoring, and cleanup reporting.
- **Native WSL Portal** exposes the operator UI for dashboards, graph viewing, quality reports, cleanup reports, watcher output, and controlled extraction.
- **Chat Import Bridge** stages manually approved chat transcripts before promotion into research projects.

## Current operating doctrine

1. Do not silently auto-import every chat. Use manual review and approval first.
2. Do not treat Neo4j as authoritative. It is a controlled projection from PostgreSQL.
3. Do not force graph extraction unless intentionally rebuilding with a fresh backup.
4. Keep cleanup tools read-only or dry-run until backup/export/restore validation is confirmed.
5. Never commit secrets, SQLite databases, logs, backups, exports, `.env` files, or local tailnet/IP details.

## Repository layout

```text
.
├── apps/                         # Application surfaces and service-specific code
│   ├── research-agent/            # Research API/worker service
│   ├── research-portal/           # Portal/UI service
│   └── chat-import-bridge/        # Manual chat staging bridge
├── config/                        # Example configuration only
├── docker/                        # Compose examples and container notes
├── docs/                          # Operator docs, architecture, safety, runbooks
├── scripts/                       # Safe helper scripts and checks
├── sql/                           # Schema/migration notes
├── systemd/user/                  # User service examples for WSL/systemd
├── tests/                         # Test suite placeholder
├── tools/                         # Local operator utilities placeholder
└── .github/                       # GitHub workflow and collaboration templates
```

## Quick start for a fresh checkout

```bash
git clone <your-repo-url> northstar-research
cd northstar-research
cp config/.env.example .env
make doctor
```

For an existing machine that already has a working local install, copy these repository root files into that project carefully. Do not overwrite working service scripts without reviewing them first.

## Daily operator check

```bash
make health
```

This calls local health endpoints and prints the expected graph-gate/watcher reminders. The script is intentionally conservative; it does not mutate databases or graph state.

## Documentation entry points

- [Repository structure](ROOT_STRUCTURE.md)
- [Setup](docs/SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Operations](docs/OPERATIONS.md)
- [Safety doctrine](docs/SAFETY.md)
- [Graph operations](docs/GRAPH_OPERATIONS.md)
- [Chat Import Bridge](docs/CHAT_IMPORT_BRIDGE.md)
- [Backup and restore](docs/BACKUP_RESTORE.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
