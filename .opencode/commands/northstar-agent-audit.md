---
description: Targeted audit using the smallest relevant Northstar specialist agents
agent: review
---

You are running a targeted Northstar specialist-agent audit.

Scope from user:
`$ARGUMENTS`

Rules:
- Do not call every specialist by default.
- Choose only the smallest relevant set of agents.
- Use `@codebase-cartographer` first only when the affected files or flow are unclear.
- Use `@llm-extraction-engineer` for LLM, extraction, embedding, ChromaDB, quality scoring, or Ollama behavior.
- Use `@data-pipeline-reviewer` for import, promotion, persistence, source lineage, PostgreSQL, Neo4j, ChromaDB sync, cleanup, backup, or derived-store consistency.
- Use `@api-test-engineer` for FastAPI, frontend/backend contracts, async tests, safety-gate tests, or integration coverage.
- Use `@db-performance-reviewer` for SQLAlchemy, Alembic, query plans, indexes, pagination, Neo4j query performance, or repository performance.
- Use `@appsec-reviewer` for scraping, untrusted content, CORS, secrets, logs, exports, destructive flags, or public exposure.
- Use `@performance-benchmarker` for latency, throughput, large import/export, extraction speed, graph/vector performance, or portal build/runtime performance.
- Use `@accessibility-auditor` for React/Vite portal accessibility, keyboard flow, ARIA, focus, forms, tables, modals, graphs, or mobile usability.
- Use `@ops-reliability-reviewer` for Docker Compose, doctor/health scripts, systemd, backup/restore, ports, logs, and local setup reliability.

Return:
1. selected agents and why
2. files/flows inspected
3. risks by severity
4. exact validation commands to run
5. whether implementation should proceed
6. unresolved questions
