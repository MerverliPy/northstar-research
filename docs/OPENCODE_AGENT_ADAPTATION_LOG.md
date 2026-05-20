# OpenCode Agent Adaptation Log

This log records the high-value agents adapted for Northstar Research from the GitHub agent pack review.

## Installed agents

| Adapted agent | Source inspiration | Why it benefits Northstar | How to use |
|---|---|---|---|
| `@llm-extraction-engineer` | AI engineer | Reviews local LLM extraction, embeddings, ChromaDB/vector behavior, quality scoring, structured outputs, and hallucination/source-attribution risk. | Use before changing `northstar-llm`, `northstar-vector`, extraction jobs, or model parsing. |
| `@data-pipeline-reviewer` | Data engineer | Protects import, staging, promotion, PostgreSQL canonical data, Neo4j/ChromaDB derived stores, lineage, idempotency, and cleanup behavior. | Use before changes to import, promotion, repositories, models, cleanup, backup/restore, or derived-store sync. |
| `@api-test-engineer` | API tester | Adds deeper FastAPI, async, safety-gate, and frontend/backend contract test coverage beyond contract review alone. | Use when adding or changing routes, API clients, extraction endpoints, cleanup endpoints, graph/search/report flows, or tests. |
| `@db-performance-reviewer` | Database optimizer | Focuses on indexes, unbounded queries, SQLAlchemy async session patterns, Alembic safety, Neo4j queries, pagination, and repository performance. | Use before schema, migration, repository, query, graph, or large-list changes. |
| `@appsec-reviewer` | Security engineer | Adds read-only AppSec review for SSRF, injection, XSS, secrets/log leaks, CORS, exports, scraping, and destructive flags. | Use before scraping, imports/exports, rendered user content, settings, logs, or safety-flag changes. |
| `@performance-benchmarker` | Performance benchmarker | Designs safe benchmarks for extraction, vector search, graph queries, API latency, portal build/runtime, and large imports. | Use before optimizing or adding high-volume flows. |
| `@accessibility-auditor` | Accessibility auditor | Adds focused review for portal keyboard flow, semantics, forms, tables, modals, graphs, mobile, and reduced-motion behavior. | Use before UI or PWA changes. |
| `@codebase-cartographer` | Codebase onboarding engineer | Prevents broad context loading by mapping the smallest relevant files and flows before bigger work. | Use before ambiguous changes or when you need a flow map. |
| `@ops-reliability-reviewer` | Infrastructure maintainer | Reviews Docker Compose, health/doctor scripts, systemd units, backup/restore, logs, ports, and local-first reliability. | Use before ops, local setup, backup, restore, health, or service changes. |

## Installed command

| Command | Purpose |
|---|---|
| `/northstar-agent-audit` | Selects the smallest relevant subset of the adapted agents for a scoped audit. |

## Operating policy

- Use specialist agents only when their role materially improves quality, safety, or repeatability.
- Prefer targeted file reads over broad repo scans.
- Keep destructive operations gated.
- Run `make lint`, `make test`, and `make check-secrets` after implementation changes.
- Do not use these agents as a substitute for tests, code review, or safety gates.
