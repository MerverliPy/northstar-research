# Northstar Research — Build Plan

> Local AI research system. PostgreSQL source of truth. Neo4j graph layer. Self-hosted LLMs via Ollama. ChromaDB vector search.

---

## What We're Building

Three Python microservices, two databases, one vector store — orchestrated for research workflows.

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ Chat Import  │───▶│ Research     │───▶│ Research     │
│ Bridge       │    │ Agent        │    │ Portal       │
│ port 3022    │    │ port 8099    │    │ port 3010    │
│ SQLite       │    │ LLM + Embed  │    │ Jinja2+HTMX  │
└──────────────┘    └──┬──────┬────┘    └──────────────┘
                       │      │
                       v      v
               ┌────────┐  ┌────────┐
               │Postgres│  │ Neo4j  │
               │5432    │  │7687    │
               └────────┘  └────────┘
                       │
                       v
               ┌────────────┐
               │ ChromaDB   │
               │ vector     │
               │ store      │
               └────────────┘
```

### Model Stack

| Role | Model | Provider |
|---|---|---|
| Primary reasoning | Qwen3:14b | Ollama (native) |
| Fast fallback | Llama3.1:8b | Ollama (native) |
| Embeddings | Nomic-embed-text | Ollama (native) |

---

## Tech Stack

| Layer | Choice | Rationale |
|---|---|---|
| Framework | FastAPI + uvicorn | Async, auto-docs, Pydantic validation |
| ORM | SQLAlchemy + Alembic + asyncpg | Async PG access, migration support |
| Vector store | ChromaDB (file-backed) | Python-native, no Docker, persistent |
| LLM integration | `ollama` Python lib + custom fallback chain | Qwen3 → Llama3.1 auto-fallback |
| Background tasks | FastAPI BackgroundTasks + polling | No Redis needed for v1 |
| UI | Jinja2 + HTMX + Alpine.js | Reactive dashboards, no build step |
| Caching | diskcache | TTL-based LLM response cache |
| Logging | structlog | Structured JSON logs |
| Testing | pytest + httpx + testcontainers | PG + Neo4j + ChromaDB containers |
| Python | 3.11 | Most stable with deps |
| Ollama | Native install (not Docker) | GPU passthrough simpler |
| Packaging | Local editable (`pip install -e`) | No PyPI publish |

---

## Build Sequence — 4 Waves, 10 Agent Turns

### Wave 0: Shared Foundation

Create shared packages the services depend on.

| Package | Contents |
|---|---|
| `northstar-models` | Pydantic schemas, SQLAlchemy models, enums (`ProjectStatus`, `ExtractionStatus`, `EntityType`, `QualityStatus`, `LLMTask`) |
| `northstar-llm` | `LLMService` with Qwen3→Llama3.1 fallback chain, `EmbeddingService` for nomic-embed-text |
| `northstar-vector` | ChromaDB client wrapper, auto-embedding pipeline |
| `northstar-db` | Async PG + Neo4j repository pattern |

### Wave 1: Infrastructure (3 parallel agents)

| Agent | Creates |
|---|---|
| **foundation** | `docker-compose.yml` (PG 16 + Neo4j 5), `.env.example` (with model vars), systemd service files, updated shell scripts |
| **schema** | Alembic migrations (7 tables), init scripts, seed data scripts |
| **gitops** | Dockerfiles per app, `pyproject.toml` per package, CI workflow, Makefile targets |

### Wave 2: Three Services (3 parallel agents)

| Service | Port | Agent | Key Endpoints |
|---|---|---|---|
| **Research Agent** | 8099 | `agent-smith` | Project/source/report CRUD, extraction (BackgroundTasks + polling), quality scoring (Llama3.1), cleanup reporting (dry-run), vector search |
| **Chat Import Bridge** | 3022 | `bridge` | Paste import, SQLite staging queue, Markdown export, promotion (→Agent API) |
| **Research Portal** | 3010 | `portal` | Dashboard, quality/cleanup pages, extraction gate UI, watcher, graph viewer (vis.js) |

### Wave 3: Tests + Hardening (2 parallel agents)

| Agent | Scope |
|---|---|
| **qa** | Unit + integration + E2E, 80% coverage minimum, safety gate verification |
| **shield** | Live backup/restore scripts, extraction CLI tools, docs sync, CI finalization |

---

## Safety Doctrine

Compiled into every layer of the system:

1. **PostgreSQL** is source of truth. Neo4j is derived.
2. `FORCE_GRAPH_EXTRACTION=false` by default — extraction returns 403 unless explicitly enabled
3. `ENABLE_DESTRUCTIVE_CLEANUP=false` by default — cleanup is read-only/dry-run
4. `PROMOTION_ENABLED=false` by default — chat-import promotion returns 403 unless enabled
5. Existing graphs are skipped by default
6. Chat Import Bridge never mutates PG or Neo4j before explicit promotion
7. All destructive actions require backup validation + explicit flag
8. Docker containers run as non-root `appuser`
9. Docker-compose services use `restart: unless-stopped` with Neo4j healthcheck
10. `restore.sh` prompts for confirmation; `backup.sh` checks for `pg_dump` availability

---

## File Map

```
northstar-research/
├── apps/
│   ├── research-agent/           # FastAPI, LLM, extraction
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── dependencies.py
│   │   │   ├── routers/          # projects, sources, reports, entities, claims, quality, cleanup, extraction, search
│   │   │   └── services/         # project, extraction, quality, cleanup, embedding
│   │   ├── migrations/
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   ├── research-portal/          # Jinja2+HTMX dashboards
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── config.py
│   │   │   ├── routers/          # dashboard, quality, cleanup, extraction, visual
│   │   │   └── templates/        # 7 HTML pages (base, dashboard, quality, cleanup, extraction, watcher, graph_viewer)
│   │   ├── Dockerfile
│   │   └── pyproject.toml
│   └── chat-import-bridge/       # SQLite staging
│       ├── app/
│       │   ├── main.py
│       │   ├── config.py
│       │   ├── models.py
│       │   ├── routers/          # imports
│       │   ├── services/         # staging, export, promotion
│       │   └── templates/
│       ├── Dockerfile
│       └── pyproject.toml
├── packages/
│   ├── northstar-models/         # Shared schemas
│   ├── northstar-llm/            # Ollama abstraction
│   ├── northstar-vector/         # ChromaDB
│   └── northstar-db/             # PG + Neo4j repos
├── docker/
│   └── docker-compose.yml        # PG + Neo4j (no Ollama/ChromaDB containers)
├── config/
│   └── .env.example              # All env vars including models
├── scripts/                      # Health, backup, extraction CLIs
├── tests/                        # Unit, integration, E2E
├── systemd/user/                 # Service units
└── docs/                         # Runbooks + this plan
```

---

## Agent Handoff Protocol

Each build wave passes a contract to the next. Contracts contain exact port numbers, route paths, model names, and safety flag values. No agent proceeds without reading the contract.

| Handoff | From | To | Contents |
|---|---|---|---|
| Sync A | conductor | all Wave 1 agents | BUILD_CONTRACT.md + shared package exports |
| Sync B | foundation/schema/gitops | all Wave 2 agents | Infra paths, table schemas, Dockerfile paths |
| Sync C | agent-smith/bridge/portal | all Wave 3 agents | API route contracts for all 3 services |
| Sync D | qa/shield | conductor | Test results + hardening verification |

---

## Execution Timeline

```
Wave 0: Shared Foundation       ~2 agent turns
Wave 1: Infrastructure           ~2 agent turns (3 parallel)
Wave 2: Three Services           ~4 agent turns (3 parallel)
Wave 3: Tests + Hardening        ~2 agent turns (2 parallel)
─────────────────────────────────────────────────
Total:                           ~10 agent turns
```

---

## Appendix: Environment Variables

```ini
# Services
RESEARCH_AGENT_HOST=127.0.0.1
RESEARCH_AGENT_PORT=8099
RESEARCH_PORTAL_HOST=127.0.0.1
RESEARCH_PORTAL_PORT=3010
CHAT_IMPORT_BRIDGE_HOST=127.0.0.1
CHAT_IMPORT_BRIDGE_PORT=3022

# Databases
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=northstar_research
POSTGRES_USER=northstar
POSTGRES_PASSWORD=change-me
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=change-me

# Models
OLLAMA_HOST=http://127.0.0.1:11434
OLLAMA_PRIMARY_MODEL=qwen3:14b
OLLAMA_FALLBACK_MODEL=llama3.1:8b
OLLAMA_EMBED_MODEL=nomic-embed-text

# Vector Store
VECTOR_STORE_PATH=./data/chromadb
EMBEDDING_DIMENSION=768

# Task → Model Routing
LLM_TASK_EXTRACTION_MODEL=qwen3:14b
LLM_TASK_SUMMARIZATION_MODEL=qwen3:14b
LLM_TASK_QUALITY_SCORING_MODEL=llama3.1:8b
LLM_TASK_CLASSIFICATION_MODEL=llama3.1:8b

# Safety
FORCE_GRAPH_EXTRACTION=false
ENABLE_DESTRUCTIVE_CLEANUP=false
PROMOTION_ENABLED=false
```
