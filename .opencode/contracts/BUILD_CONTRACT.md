# BUILD CONTRACT — Northstar Research

## Wave Progress

| Wave | Status | Agents |
|---|---|---|
| 0: Shared Foundation | ✅ Completed | models, llm, vector, db |
| 1: Infrastructure | ❌ Not started | foundation, schema, gitops |
| 2: Three Services | ❌ Not started | agent-smith, bridge, portal |
| 3: Tests + Hardening | ❌ Not started | qa, shield |

## Last Completed Wave

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

Start Wave 1: Build infrastructure (docker-compose, .env, migrations, Dockerfiles, CI, Makefile targets).
