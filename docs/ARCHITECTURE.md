# Architecture

## Concept

Northstar Research is a local RAG research system with a knowledge-graph layer. The LLM provides reasoning and summarization, while durable project records, sources, reports, summaries, embeddings, and graph projections make the workflow auditable and repeatable.

## High-level flow

```text
User topic or approved chat transcript
  -> source material is stored
  -> summaries, claims, and entities are extracted
  -> PostgreSQL stores durable project records
  -> embeddings support semantic retrieval
  -> Neo4j visualizes project/entity/claim/source/report relationships
  -> portal dashboards expose quality, cleanup, watcher, and graph views
```

## Components

| Component | Role |
|---|---|
| Research Agent | Research workflow, APIs, health checks, graph extraction, quality scoring, cleanup reports. |
| PostgreSQL | Source of truth for projects, sources, reports, metadata, and durable records. All FK relationships use `ondelete="CASCADE"`. |
| Neo4j | Visual relationship layer for graph views and graph quality checks. Password must be explicitly configured (no default). |
| Native WSL Portal | Operator UI (PWA) on local port `3010`. Offline shell, installable, SW update prompt via toast. |
| Tailscale Serve | Optional HTTPS exposure to trusted tailnet clients. |
| Watcher | Read-only reporter for completed projects without graphs. |
| Controlled Gate | Safe extraction gate that skips existing graphs, caps work, and checks quality. |
| Chat Import Bridge | Manual staging area for chat transcripts before promotion into research projects. Promotion gated behind `PROMOTION_ENABLED` flag. |
| Ollama | Local LLM inference (`OLLAMA_HOST`). EmbeddingService uses 60s timeout, LLMService uses 3-retry exponential backoff. |

## Source-of-truth rule

PostgreSQL is authoritative. Neo4j is a derived projection for visibility and relationship traversal. If the two disagree, inspect PostgreSQL first and rebuild graph projections through controlled extraction only after backup validation.

## Service ports

| Service | Port | Notes |
|---|---|---|
| Research Agent | 8099 | Core CRUD API, extraction, search, quality |
| Research Portal | 3010 | Jinja2+HTMX UI, API proxy to agent, SPA fallback |
| Chat Import Bridge | 3022 | SQLite staging import, gated promotion to Agent |
| PostgreSQL | 5432 | Docker container, `restart: unless-stopped` |
| Neo4j Bolt | 7687 | Docker container, healthcheck enabled, `restart: unless-stopped` |
| Neo4j HTTP | 7474 | HTTP endpoint for Neo4j browser |

## Proxy architecture

Portal proxies agent API calls through `routers/api_proxy.py`. The proxy:
- Includes `/api/v1` prefix in the agent base URL
- Whitelists only safe headers (accept, accept-encoding, user-agent)
- Transforms agent response shapes to portal-compatible paginated responses
- Returns 503 when agent is unreachable (with logged warnings)

## Safety gates

| Flag | Default | Scope |
|---|---|---|
| `FORCE_GRAPH_EXTRACTION` | `false` | Enables graph extraction endpoints |
| `ENABLE_DESTRUCTIVE_CLEANUP` | `false` | Enables destructive cleanup routes |
| `PROMOTION_ENABLED` | `false` | Enables chat-import promotion to Agent |

All three gates default to disabled. Destructive/gated routes return 403 unless explicitly enabled.

## Data integrity

- All list endpoint `limit` query params enforce `ge=1, le=1000`.
- `LLMResponseCache` key includes system_prompt, temperature, and max_tokens to prevent cache poisoning.
- VectorStore health check uses real `list_collections()` for liveness verification.
- VectorStore.add_documents() uses `embed_batch()` for batch embedding performance.
- Search result scores are normalized for cosine distance (`1.0 - dist/2.0`).
- All Pydantic `confidence` and `quality_score` fields have `Field(ge=0.0, le=1.0)` validators.
- `updated_at` columns present on all tables (entities, claims, analyses, extraction_logs).
- Entity aliases are `list[str]` (JSON array), not dict.
- LLMService.generate() has 3-retry exponential backoff for TimeoutException, ConnectError, ReadError.
- Schema ordering follows Create → Read → Update convention for all entities.
- Portal routers share a single Jinja2 template environment from `template_utils.py`.
- Docker containers run as non-root `appuser`.

## Infrastructure hardening

- `restore.sh` prompts for confirmation before destructive restore.
- `backup.sh` checks for `pg_dump` availability before running.
- Dockerfile runs as non-root `appuser` (3-stage multi-stage build).
- Docker-compose services use `restart: unless-stopped` with Neo4j healthcheck.
- EmbeddingService httpx client has 60s timeout.
- SPA file serving has path traversal protection.
- SSE chat endpoint uses CORS middleware only (no wildcard header).
