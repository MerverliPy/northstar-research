# Codebase Cartography Audit — Northstar Research

**Date:** 2026-05-20
**Agent:** Codebase Cartographer (read-only mapping agent)
**Scope:** Complete repo audit — service boundaries, dependencies, file organization, data flows, configuration coupling

---

## 1. Architecture Health Score: **78/100 (B+)**

| Dimension | Score | Rationale |
|---|---|---|
| Package dependency hygiene | 90/100 | Clean chain, models at root, no circular imports |
| Cross-service isolation | 95/100 | Zero app-to-app code imports; all HTTP interop |
| Configuration coherence | 60/100 | Significant duplication, missing env docs, dual DB write points |
| File organization | 80/100 | Minor ROOT_STRUCTURE issues, orphan files from scaffold |
| Data flow resilience | 65/100 | No queue persistence, single Ollama dependency for orchestrator |
| Test architecture | 85/100 | Good mocking patterns, fixtures reusable, some gaps identified |

---

## 2. Dependency Graph

```
                          ┌─────────────────────────────────┐
                          │        northstar-models          │
                          │  (schemas.py, models.py, enums,  │
                          │   base.py — NO dependencies)     │
                          └──────┬──────────────┬────────────┘
                                 │              │
              ┌──────────────────┘              └──────────────────┐
              ▼                                                    ▼
┌─────────────────────┐                                ┌─────────────────────┐
│    northstar-llm    │                                │    northstar-db     │
│ (LLMService,        │                                │ (PostgresRepository, │
│  EmbeddingService,  │                                │  Neo4jRepository)   │
│  LLMResponseCache)  │                                │                     │
│                     │                                │ deps: models only    │
│ deps: httpx,        │                                └──────────┬──────────┘
│  diskcache,         │                                           │
│  structlog          │                                           │
└──────────┬──────────┘                                           │
           │                                                      │
           ▼                                                      │
┌─────────────────────┐                                           │
│   northstar-vector  │                                           │
│ (VectorStore,       │                                           │
│  DocumentChunk,     │                                           │
│  SearchResult)      │                                           │
│                     │                                           │
│ deps: llm (dynamic) │                                           │
│  chromadb, structlog│                                           │
└──────────┬──────────┘                                           │
           │                                                      │
           │    ┌─────────────────────────────────────────────────┘
           │    │
           ▼    ▼
┌────────────────────────────────────────────────────────────────────┐
│                    apps/research-agent (:8099)                     │
│  Imports: ALL four packages (models, llm, vector, db)             │
│  Routers: projects, sources, entities, claims, reports,           │
│           extraction, quality, cleanup, search, scraping          │
│  Services: extraction.py, quality.py, scraper.py                  │
│  All 4 package deps declared in pyproject.toml                    │
└────────────────────────────────────────────────────────────────────┘
     ▲ HTTP                                ▲ HTTP
     │                                    │
     │                     ┌──────────────┘
     │                     ▼
     │  ┌───────────────────────────────────────────────────────────────────┐
     │  │              apps/research-portal (:3010)                         │
     │  │  Imports: northstar-db, northstar-models (transitively)          │
     │  │  Routes: dashboard, extraction, quality, cleanup, visual,        │
     │  │          chat (SSE), api_proxy (pass-through to agent)           │
     │  │  Services: orchestrator.py, agent_tools.py, conversation.py      │
     │  │  ⚠️ orchestrator.py calls Ollama API DIRECTLY (bypasses llm pkg) │
     │  │  ⚠️ portal has DIRECT PG/Neo4j connections (dual write risk)     │
     │  │  Declares: northstar-models, northstar-db in pyproject.toml      │
     │  └───────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│             apps/chat-import-bridge (:3022)                     │
│  Imports: northstar-models ONLY (SourceCreate schema)          │
│  Own SQLite ORM: StagedImport, StagingBase (not northstar-db)  │
│  Services: staging.py, promotion.py, export.py, staging_db.py  │
│  Promotion → HTTP POST to agent /api/v1/sources                │
│  Declares: northstar-models in pyproject.toml                   │
└─────────────────────────────────────────────────────────────────┘
```

### External Infrastructure

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
│ Ollama   │   │PostgreSQL│   │  Neo4j   │   │ ChromaDB │
│ :11434   │   │ :5432    │   │ :7687    │   │ (local)  │
└────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘
     │              │              │              │
     ├──────────────┤              │              │
     │ Agent uses   │ Agent writes │ Agent writes │ Agent writes
     │ northstar-llm│ (durable)    │ (derived,    │ (derived)
     │              │              │  force-gated)│
     │ Portal       │ Portal reads │ Portal reads │ (no direct
     │ orchestrator │ /writes (⚠️) │ (read-only)  │  portal use)
     │ direct Ollama│              │              │
```

---

## 3. Package Dependency Matrix

| Package | Depends On (declared) | Depends On (imported) | Downstream Consumers |
|---|---|---|---|
| **northstar-models** | (none) | (none) | northstar-db, research-agent, research-portal, chat-import-bridge, tests |
| **northstar-llm** | (none in pyproject) | (none) | northstar-vector (dynamic), research-agent, tests |
| **northstar-vector** | northstar-llm | northstar-llm (try/except import) | research-agent, tests |
| **northstar-db** | northstar-models | northstar-models | research-agent, research-portal, tests |

**Key observations:**
- `northstar-llm` has ZERO declared package dependencies in pyproject.toml — only third-party (httpx, diskcache, structlog, pydantic). ✅ Correct — it's a leaf of the package tree.
- `northstar-vector` dynamically imports `northstar-llm` with a try/except guard (`client.py` line 13). This is a soft/optional dependency, but the pyproject.toml declares it as a hard dependency. ⚠️ **MEDIUM** — the try/except is dead code since the package always has the dep.
- `northstar-db` depends only on `northstar-models` — does NOT need `northstar-llm` or `northstar-vector`. ✅ Correct.
- Portal declares both `northstar-models` AND `northstar-db` in pyproject.toml, but `northstar-db` already depends on `northstar-models`. **LOW** — redundant but harmless.

---

## 4. Service Boundary Violations

| # | Finding | Severity | Details |
|---|---|---|---|
| V1 | **Portal orchestrator bypasses northstar-llm** | **HIGH** | `orchestrator.py` line 51 calls `self._llm_client.post(f"{self._ollama_url}/api/generate")` directly. This duplicates Ollama API client logic from `northstar-llm/service.py`. Two code paths to the same API — cache, retry, and error handling diverge. |
| V2 | **Portal has direct PostgreSQL + Neo4j connections** | **HIGH** | `research_portal/dependencies.py` initializes both `PostgresRepository` and `Neo4jRepository` directly. The portal writes/reads from the same DB that the agent manages. Dashboard, cleanup, quality, and extraction portal routers all use `get_db()` and `get_neo4j()` directly. Creates a dual-write surface to PostgreSQL's source-of-truth. |
| V3 | **Chat-import-bridge has own ORM models** | **MEDIUM** | `chat_import_bridge/models.py` defines `StagingBase(DeclarativeBase)` and `StagedImport` — completely separate from `northstar-models`. Not using the shared `CommonModel` base. Acceptable as the bridge is an independent staging area, but means no shared tooling (migrations, audit) applies. |
| V4 | **Portal pyproject.toml transitively redundant** | **LOW** | Portal declares `northstar-models` in deps, but `northstar-db` already pulls it transitively. Portal only uses models via `northstar-db` imports. |

---

## 5. Complete Import Map Per App

### 5.1 apps/research-agent

| File | Imports from packages |
|---|---|
| `main.py` | (none from packages — delegates to dependencies) |
| `config.py` | (none from packages — pure pydantic-settings) |
| `dependencies.py` | `northstar_db` (PostgresRepository, Neo4jRepository), `northstar_llm` (LLMService, EmbeddingService), `northstar_vector` (VectorStore) |
| `routers/projects.py` | `northstar_db` (PostgresRepository), `northstar_models` (ProjectCreate/Read/Update) |
| `routers/sources.py` | `northstar_db` (PostgresRepository), `northstar_models` (SourceCreate/Read) |
| `routers/entities.py` | `northstar_db` (PostgresRepository), `northstar_models` (EntityCreate/Read) |
| `routers/claims.py` | `northstar_db` (PostgresRepository), `northstar_models` (ClaimCreate/Read) |
| `routers/reports.py` | `northstar_db` (PostgresRepository), `northstar_models` (ReportCreate/Read) |
| `routers/extraction.py` | `northstar_db` (PostgresRepository, Neo4jRepository), `northstar_llm` (LLMService), `northstar_models` (schemas + ORM ExtractionLog), `northstar_vector` (VectorStore) |
| `routers/quality.py` | `northstar_db` (PostgresRepository), `northstar_llm` (LLMService), `northstar_models` (AnalysisRead, QualityScore*) |
| `routers/search.py` | `northstar_models` (SearchRequest, SearchResult), `northstar_vector` (VectorStore) |
| `routers/cleanup.py` | `northstar_db` (PostgresRepository, Neo4jRepository), `northstar_models` (CleanupReport, ORM Entity) |
| `routers/scraping.py` | `northstar_db` (PostgresRepository, Neo4jRepository), `northstar_llm` (LLMService), `northstar_models` (Scrape*, Source*), `northstar_vector` (VectorStore) |
| `services/extraction.py` | `northstar_db` (PostgresRepository, Neo4jRepository), `northstar_llm` (LLMService), `northstar_models` (schemas, enums), `northstar_vector` (DocumentChunk, VectorStore) |
| `services/quality.py` | `northstar_db` (PostgresRepository), `northstar_llm` (LLMService), `northstar_models` (AnalysisCreate, QualityScore*) |
| `services/scraper.py` | `northstar_models` (ScrapeRequest) |
| `migrations/env.py` | `northstar_models.models` (CommonModel) |
| `migrations/versions/001_initial_schema.py` | `northstar_models.enums` (enums) |

### 5.2 apps/research-portal

| File | Imports from packages |
|---|---|
| `main.py` | (none from packages — uses dependencies module) |
| `config.py` | (none — pure pydantic-settings) |
| `dependencies.py` | `northstar_db` (PostgresRepository, Neo4jRepository) |
| `routers/dashboard.py` | `northstar_db` (PostgresRepository, Neo4jRepository) |
| `routers/quality.py` | `northstar_db` (PostgresRepository) |
| `routers/cleanup.py` | `northstar_db` (PostgresRepository, Neo4jRepository) |
| `routers/extraction.py` | `northstar_db` (PostgresRepository) |
| `routers/visual.py` | `northstar_db` (PostgresRepository, Neo4jRepository) |
| `routers/chat.py` | (none from packages) |
| `routers/api_proxy.py` | (none from packages — only research_portal imports) |
| `services/orchestrator.py` | (none from packages) |
| `services/agent_tools.py` | (none from packages) |
| `services/conversation.py` | (none from packages — uses sqlite3 directly) |
| `template_utils.py` | (none from packages) |

### 5.3 apps/chat-import-bridge

| File | Imports from packages |
|---|---|
| `main.py` | (none from packages) |
| `config.py` | (none — pure pydantic-settings) |
| `database.py` | (none from packages) |
| `models.py` | (none from packages — own SQLAlchemy DeclarativeBase) |
| `services/staging.py` | (none — only own models) |
| `services/promotion.py` | `northstar_models.schemas` (SourceCreate) |
| `services/staging_db.py` | (none — only own models) |
| `services/export.py` | (none — only own models) |
| `routers/imports.py` | (none from packages) |
| `routers/promotion.py` | (none from packages) |
| `routers/export.py` | (none from packages) |

---

## 6. Cross-Service Coupling (HTTP)

All inter-service communication is over HTTP. No code-level imports between apps. ✅

```
chat-import-bridge ──HTTP POST /api/v1/sources──► research-agent
                       (promotion.py line 35, with SourceCreate payload)

research-portal ──HTTP POST/GET to multiple──► research-agent
                    routes via api_proxy.py, agent_tools.py,
                    quality.py, extraction.py, cleanup.py

research-portal ──HTTP POST /api/v1/promotion/──► chat-import-bridge
                    (agent_tools.py line 225, promote_import)
```

**⚠️ Portal duplicates agent API call sites**: `agent_tools.py` has 12 separate tool methods each making HTTP calls with hardcoded URL strings like `f"{self._agent_url}/api/v1/entities/?...` . Meanwhile `api_proxy.py` has a separate generic proxy path. Two code paths to the same agent — could diverge in error handling, auth, or URL construction.

---

## 7. File Organization Issues

| # | Finding | Severity | Details |
|---|---|---|---|
| F1 | **Root `.env` file exists** | **HIGH** | `.env` found at `/home/calvin/northstar-research-upload/northstar-research/.env` — must verify `.gitignore` excludes it. ROOT_STRUCTURE.md explicitly states "Never commit real .env files." |
| F2 | **SCAFFOLD_MANIFEST.txt is stale** | **LOW** | References `scripts/backup.example.sh` and `scripts/restore-drill.example.sh` which don't exist. Actual files are `scripts/backup.sh` and `scripts/restore.sh`. Also missing `scripts/verify-no-secrets.sh`. |
| F3 | **Orphan root file: backup_checklist.md** | **LOW** | Exists at repo root but not documented in ROOT_STRUCTURE.md. |
| F4 | **ROOT_STRUCTURE.md references `packages/.gitkeep`** | **LOW** | The file exists but minor — the directory now has real packages. |
| F5 | **`requirements.lock` at root not documented** | **LOW** | Not listed in ROOT_STRUCTURE.md root files table. |
| F6 | **AGENTS.md at root not documented** | **LOW** | Not in ROOT_STRUCTURE.md root files table. |
| F7 | **Data/exports/logs directories at root** | **LOW** | `data/`, `exports/`, `logs/` are runtime directories that should be gitignored. Verify they are in `.gitignore`. |
| F8 | **`.opencode/` directory at root** | **LOW** | Agent workspace directory — reasonable exception to the "no new top-level dirs" rule. |

---

## 8. Data Flow Mapping

### 8.1 Chat Import → Promotion → Agent → Extraction → Vector/Graph (complete trace)

```
STEP 1: STAGING
  User → POST /api/v1/imports/paste → chat-import-bridge
  └─ imports.py → staging.py/add_to_staging()
     └─ Creates StagedImport row in SQLite (staging.db)
        Fields: title, raw_content, source_type, status="pending"

STEP 2: PROMOTION (gated by PROMOTION_ENABLED)
  User → POST /api/v1/promotion/{import_id} → chat-import-bridge
  └─ promotion.py → promotion.py/promote_to_agent()
     ├─ Reads StagedImport from SQLite
     ├─ Creates SourceCreate(project_id, title, content_type, raw_content)
     └─ HTTP POST → research-agent:8099/api/v1/sources
        └─ sources.py → PostgresRepository.create_source()
           └─ INSERT INTO sources (...) → PostgreSQL
        └─ Updates StagedImport.status = "promoted" in SQLite

STEP 3: EXTRACTION (gated by FORCE_GRAPH_EXTRACTION or force=True)
  User → POST /api/v1/extraction/extract → research-agent
  └─ extraction.py → BackgroundTasks.add_task(run_extraction, ...)
     └─ extraction.py/run_extraction(source_id, llm, db, neo4j, vector_store):
        ├─ 3a. LLM EXTRACTION:
        │  └─ LLMService.generate_structured(ExtractionResult)
        │     └─ Ollama POST /api/generate → model generates structured JSON
        │     └─ Parsed into ExtractedEntity[] + ExtractedClaim[]
        │
        ├─ 3b. POSTGRESQL WRITE:
        │  ├─ PostgresRepository.bulk_create_entities(entity_creates)
        │  │  └─ INSERT INTO entities (...) → PostgreSQL
        │  └─ PostgresRepository.bulk_create_claims(claim_creates)
        │     └─ INSERT INTO claims (...) → PostgreSQL
        │
        ├─ 3c. VECTOR STORE (always):
        │  └─ VectorStore.add_documents("default", [DocumentChunk])
        │     ├─ EmbeddingService.embed_batch(texts) → Ollama POST /api/embed
        │     └─ ChromaDB collection.add(ids, metadatas, documents, embeddings)
        │
        └─ 3d. GRAPH STORE (only if force=True):
           ├─ Neo4jRepository.create_entity_node(entity)
           │  └─ MERGE (e:Entity {id}) SET e.name, e.entity_type, ...
           └─ Neo4jRepository.create_claim_relationship(claim)
              ├─ MERGE (s:Source {id})
              ├─ MERGE (e:Entity {id})
              └─ MERGE (s)-[r:MAKES_CLAIM]->(e) SET r.claim_text, ...

STEP 4: SEARCH
  User → POST /api/v1/search → research-agent
  └─ search.py → VectorStore.search(collection, query, top_k, filters)
     ├─ EmbeddingService.embed(query) → query vector
     └─ ChromaDB collection.query(query_embeddings, n_results, where=filters)
        └─ Returns SearchResult[] with normalized scores (1.0 - dist/2.0)

STEP 5: GRAPH VIEW
  Portal → GET /visual/data/{project_id} → research-portal
  └─ visual.py → Neo4jRepository.get_project_graph(project_id)
     └─ Cypher: MATCH (s:Source) WHERE s.project_id MATCH (s)-[r]-(e:Entity) ...
        └─ Returns {nodes, edges} for vis.js rendering
```

### 8.2 Single Points of Failure

| # | Component | Risk | Impact |
|---|---|---|---|
| SPF1 | **PostgreSQL** | Single DB instance, all writes go here | If down, ALL services fail (agent CRUD, portal dashboards, bridge promotion) |
| SPF2 | **Ollama** | Single LLM/embedding provider via local HTTP | If down: extraction fails, quality scoring fails, embedding fails, portal orchestrator fails, search fails |
| SPF3 | **ChromaDB** | Local embedded DB, no replication | If corrupted, vector search fails; no backup procedure documented for ChromaDB beyond `scripts/backup.sh` |
| SPF4 | **BackgroundTasks (FastAPI)** | Extraction runs as background task | If agent restarts during extraction, task is lost; no retry/queue persistence |
| SPF5 | **SQLite (staging.db)** | Single-file DB for import bridge | If corrupted, all staged imports lost; no built-in replication |
| SPF6 | **Neo4j** | Not strictly a SPOF for core ops | Graph views and entity counts fail but CRUD and extraction continue |

---

## 9. Configuration Coupling Analysis

### 9.1 Config File Comparison

| Setting | Agent config.py | Portal config.py | Bridge config.py | .env.example | Notes |
|---|---|---|---|---|---|
| `host` | ✅ 127.0.0.1:8099 | ✅ 127.0.0.1:3010 | ✅ 127.0.0.1:3022 | ❌ | Only commented in .env.example |
| `port` | ✅ 8099 | ✅ 3010 | ✅ 3022 | ❌ | Per-service, reasonable |
| `database_url` | ✅ | ✅ | ❌ | ✅ | **Duplicated** between agent + portal |
| `neo4j_uri` | ✅ | ✅ | ❌ | ✅ | **Duplicated** between agent + portal |
| `neo4j_user` | ✅ | ✅ | ❌ | ✅ | **Duplicated** |
| `neo4j_password` | ✅ | ✅ | ❌ | ✅ | **Duplicated** — shared secret in two services |
| `ollama_base_url` | ✅ | ✅ | ❌ | ✅ | **Duplicated** |
| `chroma_persist_dir` | ✅ | ✅ | ❌ | ✅ | Portal has this but never uses it (no northstar-vector dep) |
| `force_graph_extraction` | ✅ | ✅ | ❌ | ✅ | **Duplicated** safety gate |
| `enable_destructive_cleanup` | ✅ | ✅ | ❌ | ✅ | **Duplicated** safety gate |
| `promotion_enabled` | ❌ | ❌ | ✅ | ✅ | Bridge-only, correct |
| `log_level` | ✅ | ✅ | ✅ | ✅ | **Triplicated** |
| `primary_llm_model` | ✅ qwen3:14b | ❌ | ❌ | ✅ qwen3:14b | Portal uses `orchestrator_model` instead |
| `fallback_llm_model` | ✅ llama3.1:8b | ❌ | ❌ | ✅ llama3.1:8b | Only agent uses fallback |
| `embedding_model` | ✅ nomic-embed-text | ❌ | ❌ | ✅ | Only used by agent |
| `research_agent_url` | ❌ | ✅ http://127.0.0.1:8099 | ✅ http://127.0.0.1:8099 | ❌ | **MISSING from .env.example** |
| `chat_import_bridge_url` | ❌ | ✅ http://127.0.0.1:3022 | ❌ | ❌ | **MISSING from .env.example** |
| `orchestrator_model` | ❌ | ✅ qwen3:14b | ❌ | ❌ | Separate from `primary_llm_model`; could diverge |
| `conversation_db_path` | ❌ | ✅ | ❌ | ❌ | Portal-only SQLite |
| `staging_db_path` | ❌ | ❌ | ✅ | ❌ | Bridge-only SQLite |
| `scraper_*` (5 settings) | ✅ | ❌ | ❌ | ❌ | Agent-only scraper settings; missing from .env.example |
| `max_conversation_history` | ❌ | ✅ 50 | ❌ | ❌ | Portal-only |

### 9.2 Configuration Issues

| # | Finding | Severity | Details |
|---|---|---|---|
| C1 | **Dual DB connections create two write surfaces** | **CRITICAL** | Both agent and portal initialize PostgresRepository and Neo4jRepository independently. If their configs diverge (different URIs), inconsistent writes could occur. The architecture intent (portal uses agent API via proxy) is violated by direct DB access. |
| C2 | **Safety gates duplicated across agent + portal** | **HIGH** | `force_graph_extraction` and `enable_destructive_cleanup` must be set in BOTH agent AND portal configs for consistent behavior. Portal's own gates check `settings.force_graph_extraction` independently before calling the agent. |
| C3 | **`.env.example` missing 5+ service-specific settings** | **MEDIUM** | Missing: `research_agent_url`, `chat_import_bridge_url`, `orchestrator_model`, `conversation_db_path`, `staging_db_path`, all 5 `scraper_*` settings, `max_conversation_history`. Operators must discover these from source code. |
| C4 | **Model name duplication: `primary_llm_model` vs `orchestrator_model`** | **MEDIUM** | Agent uses `PRIMARY_LLM_MODEL=qwen3:14b` while portal uses `ORCHESTRATOR_MODEL=qwen3:14b`. If changed in only one place, they could use different models. |
| C5 | **Portal has `chroma_persist_dir` but never uses ChromaDB** | **LOW** | Dead config — portal has no northstar-vector dependency and never accesses ChromaDB directly. Adds confusion. |

---

## 10. Entry Points and CLI Tools

### 10.1 tools/*.py

| Tool | Entry point | Dependencies | Communicates with | Notes |
|---|---|---|---|---|
| `tools/extract.py` | `python tools/extract.py <source_id> [--force] [--agent-url]` | httpx only | Agent HTTP API only | Triggers extraction via agent, validates UUID |
| `tools/query.py` | `python tools/query.py <command> [options]` | httpx only | Agent HTTP API only | CRUD + search: projects/sources/entities/claims/search |
| `tools/export.py` | `python tools/export.py <source_id> [--format] [--output]` | httpx only | Agent HTTP API only | Exports source as markdown or JSON |
| `tools/__main__.py` | `python -m tools` | (none) | (none) | Help/listing only |

✅ **Tools use ZERO library packages** (no northstar-* imports) — purely HTTP clients to the agent API. This is correct architecture — tools are thin CLI wrappers.

### 10.2 scripts/*.sh

| Script | Dependencies | Actions | Destructive? |
|---|---|---|---|
| `scripts/doctor.sh` | git, bash, curl, docker, python3, .venv, packages | Validates environment readiness | No |
| `scripts/check-health.sh` | curl, psql (optional), nc (optional) | HTTP health checks + DB connectivity | No |
| `scripts/backup.sh` | pg_dump, tar | Dumps PostgreSQL + copies ChromaDB dir | No (read-only of source) |
| `scripts/restore.sh` | pg_restore, tar | **Prompts for confirmation**, then restores PG + ChromaDB | ✅ **DESTRUCTIVE** (gated by manual confirmation) |
| `scripts/verify-no-secrets.sh` | git, grep | Scans for accidental secret patterns | No |

✅ All scripts follow the "safe by default" principle. `restore.sh` has explicit confirmation prompt.

### 10.3 Docker / Service Entry Points

| Service | Port | Entry point | Dockerfile stage |
|---|---|---|---|
| research-agent | 8099 | `uvicorn research_agent.main:app` | Stage 1 |
| research-portal | 3010 | `uvicorn research_portal.main:app` | Stage 3 |
| chat-import-bridge | 3022 | `uvicorn chat_import_bridge.main:app` | Stage 2 |

---

## 11. Test Architecture Assessment

### 11.1 Test Coverage by Area

| Test file | What it tests | Quality |
|---|---|---|
| `tests/conftest.py` | All mock fixtures (db, llm, neo4j, vector, scraper, app clients) | ✅ Excellent — centralized mocks |
| `tests/test_agent_api.py` | Agent CRUD routers | ✅ Good |
| `tests/test_portal_api.py` | Portal routes | ✅ Good |
| `tests/test_bridge_api.py` | Bridge API | ✅ Good |
| `tests/test_extraction_service.py` | Extraction service logic | ✅ Good |
| `tests/test_quality_service.py` | Quality scoring service | ✅ Good |
| `tests/test_models.py` | Pydantic schema validation | ✅ Good |
| `tests/test_llm.py` | LLMService + cache | ✅ Good |
| `tests/test_vector.py` | VectorStore operations | ✅ Good |
| `tests/test_db_pg.py` | PostgresRepository | ✅ Good |
| `tests/test_db_neo4j.py` | Neo4jRepository | ✅ Good |
| `tests/test_safety_gates.py` | Force/extraction/cleanup gates | ✅ Good |
| `tests/test_scraper_service.py` | WebScraper logic | ✅ Good |
| `tests/test_scraper_api.py` | Scraping API endpoint | ✅ Good |
| `tests/test_conversation.py` | Conversation store | ✅ Good |
| `tests/test_orchestrator.py` | Portal orchestrator | ✅ Good |
| `tests/test_promotion_service.py` | Bridge promotion | ✅ Good |
| `tests/test_agent_tools.py` | AgentToolExecutor tools | ✅ Good |

**Gaps identified:**
- No test for `template_utils.py` (though it's trivial)
- No integration test for the complete "paste → promote → extract → search" flow
- No test for portal's `api_proxy.py` response transformation (transform_project, transform_report)
- No performance/load tests

---

## 12. Other Notable Observations

| # | Finding | Severity |
|---|---|---|
| O1 | **`northstar_vector/client.py` has dead try/except for EmbeddingService import** (line 12-15). Since pyproject.toml declares `northstar-llm` as a hard dependency, this import guard is unnecessary. | **LOW** |
| O2 | **Portal's `api_proxy.py` duplicates URL construction** — `agent_tools.py` also constructs agent API URLs with manual string formatting. Two code paths for the same calls. | **MEDIUM** |
| O3 | **Portal orchestrator uses its own Ollama HTTP client** with 120s timeout, separate from `northstar_llm` which uses 120s timeout with 3-retry exponential backoff. The orchestrator has NO retry logic, NO caching, NO fallback model. | **HIGH** |
| O4 | **`ExtractionLog` has `unique_together` on (source_id, project_id)** — prevents re-extraction of the same source within a project. This is intentional but could surprise operators. | **INFO** |
| O5 | **Chat-import-bridge's `StagedImport` uses INTEGER autoincrement IDs**, not UUIDs like all other entities. This is a significant type mismatch with the rest of the system. | **MEDIUM** |
| O6 | **Portal has its own SQLite DB** (`conversation.db`) for chat history — a third data store alongside PostgreSQL, Neo4j, ChromaDB, and bridge's staging.db. | **MEDIUM** |
| O7 | **No migration tooling for SQLite** — bridge uses `StagingBase.metadata.create_all()` at startup, portal uses raw SQL in `conversation.py`. No alembic for SQLite databases. | **MEDIUM** |

---

## 13. Recommended Follow-Up Actions

### Quick Wins (Low effort, high value)

1. **Verify `.env` is in `.gitignore`** (F1) — if not, add it immediately.
2. **Remove `chroma_persist_dir` from portal config.py** (C5) — dead config.
3. **Add missing settings to `.env.example`** (C3) — `research_agent_url`, `chat_import_bridge_url`, `orchestrator_model`.
4. **Update `SCAFFOLD_MANIFEST.txt`** (F2) — replace stale script references.
5. **Document `backup_checklist.md` in ROOT_STRUCTURE.md** (F3) or remove it.

### Structural Issues (Higher effort, architecture changes)

1. **Replace portal's orchestrator Ollama calls with `northstar-llm`** (V1, O3) — eliminates code duplication, gains retry+fallback+caching.
2. **Consider removing portal's direct DB access** (V2, C1) — route all data operations through agent API to maintain single write surface.
3. **Add extraction queue persistence** (SPF4) — use PostgreSQL as a job queue instead of FastAPI BackgroundTasks.
4. **Align bridge integer IDs with system UUID convention** (O5) — or document the reasoning.
5. **Consolidate portal agent API calls** (O2) — deduplicate URL construction between `api_proxy.py` and `agent_tools.py`.

### Recommended Agents/Tests for Follow-Up

- **`northstar-safety`** skill — for any changes touching DB writes, safety gates, or extraction
- **`api-contract-safety`** skill — for any changes to router schemas
- **`python-testing`** / **`test-patterns`** skill — for adding integration tests for the full data flow
- **`repository-pattern`** skill — for any DB repository changes
- Run `make test` and `make lint` after any changes

---

## 14. Unknowns

1. **ChromaDB backup/restore reliability** — `scripts/backup.sh` does `cp -a` but doesn't verify ChromaDB consistency after copy.
2. **Neo4j APOC dependency** — `Neo4jRepository.get_entity_graph()` uses `apoc.path.subgraphNodes()` — needs APOC plugin installed. Not documented in setup instructions.
3. **CloakBrowser binary management** — scraper downloads a binary at startup. Who manages versioning/updates?
4. **Conversation store performance at scale** — `conversation.py` has no pagination for messages within a conversation.
5. **Portal CORS allows `localhost:5173`** (Vite dev server) — is this intentional for dev, or should it be configurable?

