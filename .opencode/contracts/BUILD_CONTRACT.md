# BUILD CONTRACT — Northstar Research

## Wave Progress

| Wave | Status | Agents |
|---|---|---|
| 0: Shared Foundation | ✅ Completed | models, llm, vector, db |
| 1: Infrastructure | ✅ Completed | foundation, schema, gitops |
| 2: Three Services | ✅ Completed | agent-smith, bridge, portal |
| 3: Tests + Hardening | ❌ Not started | qa, shield |

## Last Completed Wave

**Wave 2 — Three Services** (3 parallel agents):

### Agent `agent-smith` — apps/research-agent/ (port 8099)
- `research_agent/main.py` — FastAPI app, lifespan, CORS, /health
- `research_agent/config.py` — Settings with safety flags
- `research_agent/dependencies.py` — DI singletons (PG, Neo4j, LLM, Vector)
- `research_agent/routers/projects.py` — CRUD /api/v1/projects
- `research_agent/routers/sources.py` — CRUD /api/v1/sources
- `research_agent/routers/entities.py` — CRUD /api/v1/entities
- `research_agent/routers/claims.py` — CRUD /api/v1/claims
- `research_agent/routers/reports.py` — CRUD /api/v1/reports
- `research_agent/routers/extraction.py` — POST /extract, GET /status, GET /queue (403 unless force)
- `research_agent/routers/quality.py` — POST /score, GET /history
- `research_agent/routers/cleanup.py` — GET /report (dry-run), POST /execute (403 unless flag)
- `research_agent/routers/search.py` — POST / vector search
- `research_agent/services/extraction.py` — LLM→entities→PG→Neo4j→Chroma pipeline
- `research_agent/services/quality.py` — LLM scoring → Analysis record
- pyproject.toml updated with pydantic-settings, httpx

### Agent `bridge` — apps/chat-import-bridge/ (port 3022)
- `chat_import_bridge/main.py` — FastAPI app, lifespan, CORS, /health
- `chat_import_bridge/config.py` — Settings (staging DB path, Agent URL)
- `chat_import_bridge/models.py` — StagedImport SQLAlchemy model
- `chat_import_bridge/database.py` — staging DB engine + sessions
- `chat_import_bridge/routers/imports.py` — POST /paste, GET /, GET/{id}, DELETE/{id}
- `chat_import_bridge/routers/export.py` — GET /{id}/markdown
- `chat_import_bridge/routers/promotion.py` — POST /{id}, POST /batch
- `chat_import_bridge/services/staging_db.py` — engine + session factory (aiosqlite)
- `chat_import_bridge/services/staging.py` — staging CRUD operations
- `chat_import_bridge/services/export.py` — to_markdown formatter
- `chat_import_bridge/services/promotion.py` — httpx POST to Agent API

### Agent `portal` — apps/research-portal/ (port 3010)
- `research_portal/main.py` — FastAPI app, lifespan, Jinja2 templates, /health
- `research_portal/config.py` — Settings
- `research_portal/dependencies.py` — PG + Neo4j repo DI
- `research_portal/routers/dashboard.py` — GET / — stats + recent projects
- `research_portal/routers/quality.py` — GET/POST /quality — scores + HTMX trigger
- `research_portal/routers/cleanup.py` — GET/POST /cleanup — dry-run, 403 unless flag
- `research_portal/routers/extraction.py` — GET/POST /extraction — 403 unless force
- `research_portal/routers/visual.py` — GET /graph, GET /graph/data/{id} — vis.js JSON
- `templates/base.html` — nav (5 links), HTMX+Alpine+vis.js CDN, clean CSS
- `templates/dashboard.html` — 4 stat cards + projects table
- `templates/quality.html` — sources w/ color-coded scores
- `templates/cleanup.html` — report + disabled Execute button
- `templates/extraction.html` — source table w/ status badges
- `templates/graph_viewer.html` — project dropdown + vis.js network

---

**Wave 1 — Infrastructure** (3 parallel agents):

### Agent `foundation` — docker/, config/, scripts/, systemd/
- `docker/docker-compose.yml` — PG 16 + Neo4j 5 containers
- `config/.env.example` — all 18 env vars (PG, Neo4j, Ollama, Chroma, safety flags)
- `scripts/doctor.sh` — preflight checks (deps, .venv, Ollama, 4 packages)
- `scripts/check-health.sh` — pings 3 service /health endpoints
- `scripts/backup.sh` — pg_dump + Chroma dir → timestamped tar.gz
- `scripts/restore.sh` — pg_restore + Chroma dir from backup
- `systemd/user/phase1-daily-use.service` — docker compose oneshot
- `systemd/user/research-portal-native.service` — native uvicorn service
- Removed obsolete `.example` stub files

### Agent `schema` — apps/research-agent/migrations/, sql/
- `migrations/alembic.ini` — Alembic config (async PG target)
- `migrations/env.py` — async Alembic env (northstar_models metadata)
- `migrations/script.py.mako` — migration template
- `migrations/versions/001_initial_schema.py` — 7 tables with FKs + JSONB
- `sql/init.sql` — bootstrap database + user
- `sql/seed.sql` — sample data (2 projects, 1 source)
- `sql/README.md` — migration usage docs

### Agent `gitops` — Dockerfile, app pyproject.toml files, CI, Makefile
- `Dockerfile` — multi-stage (agent:8099, bridge:3022, portal:3010)
- `apps/research-agent/pyproject.toml`
- `apps/chat-import-bridge/pyproject.toml`
- `apps/research-portal/pyproject.toml`
- `.github/workflows/ci.yml` — lint (ruff), test (pytest + PG/Neo4j services), docker-compose config check
- `Makefile` — install, install-all, test, lint (ruff), tree targets

---

**Wave 0 — Shared Foundation** (4 parallel agents):

### Agent `models` — packages/northstar-models/
- `__init__.py` — public API exports
- `enums.py` — ProjectStatus, ExtractionStatus, EntityType, QualityStatus, LLMTask
- `base.py` — CommonModel with UUID PK + timestamps
- `models.py` — 7 SQLAlchemy 2.0 ORM models (Project, Source, Entity, Claim, Report, Analysis, ExtractionLog)
- `schemas.py` — Pydantic v2 CRUD schemas + PaginatedResponse, quality/extraction/search/cleanup types
- `pyproject.toml`

### Agent `llm` — packages/northstar-llm/
- `__init__.py` — exports LLMService, EmbeddingService
- `service.py` — LLMService (Qwen3→Llama3.1 fallback chain), EmbeddingService (nomic-embed-text), LLMError
- `cache.py` — LLMResponseCache with diskcache (24h TTL, SHA256 keys)
- `pyproject.toml`

### Agent `vector` — packages/northstar-vector/
- `__init__.py` — exports VectorStore, VectorStoreError, DocumentChunk, SearchResult, CollectionInfo
- `schemas.py` — Pydantic schemas for vector operations
- `client.py` — VectorStore (async ChromaDB wrapper, auto-embedding pipeline via EmbeddingService)
- `pyproject.toml`

### Agent `db` — packages/northstar-db/
- `__init__.py` — exports PostgresRepository, Neo4jRepository, GraphError
- `pg_repo.py` — PostgresRepository with full async CRUD for all 7 models + bulk operations
- `neo4j_repo.py` — Neo4jRepository with entity nodes, relationships, subgraph traversal, pathfinding
- `pyproject.toml`

## Safety Flags

| Flag | Default | Current |
|---|---|---|
| FORCE_GRAPH_EXTRACTION | false | false |
| ENABLE_DESTRUCTIVE_CLEANUP | false | false |

## Port Assignments

| Service | Port |
|---|---|
| Research Agent | 8099 |
| Chat Import Bridge | 3022 |
| Research Portal | 3010 |
| PostgreSQL | 5432 |
| Neo4j | 7687 |

## Model Stack

| Role | Model |
|---|---|
| Primary reasoning | Qwen3:14b |
| Fast fallback | Llama3.1:8b |
| Embeddings | Nomic-embed-text |

## Next Action

Start Wave 3: Build tests (qa) and hardening (shield) — unit/integration/E2E tests, CLI tools, backup/restore finalization.
