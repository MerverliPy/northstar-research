# Northstar Database Performance Audit

**Date:** 2026-05-20
**Auditor:** DB Performance Reviewer (AI)
**Scope:** Full PostgreSQL, SQLAlchemy, Neo4j, Cache, Vector, and Migration audit

---

## Overall Performance Health Score: **62/100**

| Dimension | Score | Explanation |
|-----------|-------|-------------|
| SQLAlchemy query safety | 85/100 | All queries use ORM; no raw SQL injection risks. Good parameterization. |
| N+1 query prevention | 30/100 | Multiple critical N+1 patterns in portal dashboard, quality, extraction, and cleanup pages. |
| Index coverage | 25/100 | Almost no indexes beyond PKs. Missing indexes on every FK column and all filter columns. |
| Connection pooling | 40/100 | Default asyncpg pool (10 connections); no pool tuning for concurrent background extraction + web requests. |
| Bulk operation efficiency | 70/100 | `bulk_create` uses `add_all`+`flush`; good for insert perf but lacks commit boundary. |
| Transaction boundaries | 65/100 | Session-per-operation pattern is clean but creates overhead for N+1 scenarios. |
| Neo4j index/constraint coverage | 10/100 | No Cypher indexes or constraints declared anywhere. Full graph scans for basic operations. |
| Neo4j query efficiency | 55/100 | Most queries are well-parameterized. `get_project_graph` has cartesian explosion risk. |
| Cache design | 60/100 | Key design is sound, but no eviction policy, no size limit, no selective invalidation. |
| Vector store batching | 65/100 | Batch embedding exists but no chunking for large document sets. |
| Pagination patterns | 45/100 | All list endpoints use offset/limit. No cursor-based pagination. `PaginatedResponse` schema unused. |
| Migration safety | 55/100 | Missing CASCADE in migration DDLs; no index creation. Downgrade is correct. |

---

## Query Anti-Patterns Table

| # | Severity | Location | Pattern | Impact |
|---|----------|----------|---------|--------|
| A1 | **CRITICAL** | `research_portal/routers/dashboard.py:21-30` | N+1: For each of N projects → fetch all sources → for each source fetch all claims | O(P × S × C) queries |
| A2 | **CRITICAL** | `research_portal/routers/quality.py:22-35` | N+1: For each of N projects → fetch sources → for each source fetch analyses | O(P × S × A) queries |
| A3 | **CRITICAL** | `research_portal/routers/extraction.py:24-35` | N+1: For each of N projects → fetch sources → for each source fetch extraction log | O(P × S) queries |
| A4 | **CRITICAL** | `research_portal/routers/cleanup.py:21-24` | N+1: For each project → fetch sources with `limit=9999` for counting | O(P) queries, unbounded per-project limit |
| A5 | **HIGH** | `research_portal/routers/cleanup.py:21-24` | Unbounded `limit=9999` on source listing | Memory ballooning if projects have >10K sources |
| A6 | **HIGH** | `pg_repo.py:43` | No pool tuning on `create_async_engine` | Default 10-connection pool shared by web + background tasks |
| A7 | **HIGH** | `pg_repo.py:228-231` | `list_entities` with `project_id` filter joins without index support | Seq scan on `sources` for `project_id` filter |
| A8 | **HIGH** | `neo4j_repo.py:211-222` | `get_project_graph` uses unbounded `OPTIONAL MATCH (s)-[r]-(e:Entity)` | Cartesian product explosion for multi-source projects |
| A9 | **HIGH** | `001_initial_schema.py` (entire file) | Migration creates zero indexes beyond PKs | All FK joins and filter columns are unindexed |
| A10 | **MEDIUM** | `pg_repo.py:97,157,232,300,358,458,525` | All `list_*` methods use offset/limit pagination | High offsets trigger sequential scan of skipped rows |
| A11 | **MEDIUM** | `pg_repo.py:529-547, 549-567` | `bulk_create_*` uses `flush()` without `commit()` | Uncommitted models returned; caller must manage session lifecycle |
| A12 | **MEDIUM** | `neo4j_repo.py` (entire file) | No Cypher `CREATE CONSTRAINT` or `CREATE INDEX` statements | Every `WHERE id = $id` match triggers full label scan |
| A13 | **MEDIUM** | `cleanup.py:67-70` (agent) | Orphan entity cleanup calls `neo4j.delete_entity_node()` per entity via N+1 | One Neo4j write per orphan |
| A14 | **LOW** | `pg_repo.py:525` | `list_extraction_logs` applies `order_by` before `where` clause | Opened query may trigger unnecessary sort before filter (query optimizer may handle this) |
| A15 | **LOW** | `api_proxy.py:90-91` | In-memory pagination with `items[offset:offset+limit]` | All items fetched from agent, then sliced in memory |

---

## N+1 Query Locations

### Critical: Portal Dashboard (`research_portal/routers/dashboard.py:21-30`)

```python
# Line 21: Fetches ALL sources for EVERY project (N queries)
source_count = sum(len(await db.list_sources(p.id, limit=9999)) for p in projects)

# Lines 26-30: For each project → for each source → fetch claims (N×S queries)
for p in projects:
    sources = await db.list_sources(p.id, limit=9999)
    for s in sources:
        claims = await db.list_claims(source_id=s.id, limit=9999)
```

**Query count:** For 10 projects with 5 sources each = 10 + (10 × 5) = **60 queries** just for dashboard.

### Critical: Portal Quality Dashboard (`research_portal/routers/quality.py:22-35`)

```python
for p in projects:                      # N projects
    sources = await db.list_sources(p.id, limit=50)  # N queries
    for s in sources:                   # For each source (S)
        analyses = await db.list_analyses(source_id=s.id, limit=1)  # N×S queries
```

### Critical: Portal Extraction Gate (`research_portal/routers/extraction.py:24-35`)

```python
for p in projects:
    sources = await db.list_sources(p.id, limit=50)    # N queries
    for s in sources:
        extraction_log = await db.get_extraction_log(s.id)  # N×S queries
```

### Critical: Portal Cleanup Dashboard (`research_portal/routers/cleanup.py:21-24`)

```python
for p in projects:
    sources = await db.list_sources(p.id, limit=9999)  # N queries, unbounded
```

### Medium: Extraction Cleanup (`cleanup.py:61-79`)

```python
for e in orphaned_entities:              # O orphans
    await neo4j.delete_entity_node(e.id)  # O Neo4j write transactions
```

---

## Missing Index Recommendations

### PostgreSQL Indexes (CRITICAL)

These indexes are missing from both the ORM model (no `Index()` declarations) and the Alembic migration:

```sql
-- Foreign key indexes (required for every FK used in JOINs or WHERE filters)
CREATE INDEX ix_sources_project_id ON sources (project_id);
CREATE INDEX ix_entities_source_id ON entities (source_id);
CREATE INDEX ix_claims_source_id ON claims (source_id);
CREATE INDEX ix_claims_entity_id ON claims (entity_id);
CREATE INDEX ix_reports_project_id ON reports (project_id);
CREATE INDEX ix_analyses_source_id ON analyses (source_id);
CREATE INDEX ix_analyses_project_id ON analyses (project_id);
CREATE INDEX ix_extraction_logs_source_id ON extraction_logs (source_id);
CREATE INDEX ix_extraction_logs_project_id ON extraction_logs (project_id);

-- Composite index for entity listing by project (via JOIN)
CREATE INDEX ix_entities_source_id_name ON entities (source_id, name);

-- Filter column indexes
CREATE INDEX ix_projects_status ON projects (status);
CREATE INDEX ix_extraction_logs_status ON extraction_logs (status);

-- Extraction log lookup by source (ordered by created_at)
CREATE INDEX ix_extraction_logs_source_created ON extraction_logs (source_id, created_at DESC);

-- Project name lookup (already has UNIQUE constraint, but verify)
-- (Already covered by uq_projects_name from migration)
```

### Neo4j Indexes (CRITICAL)

**None exist anywhere in the codebase.** The following must be created during Neo4j initialization:

```cypher
-- Node label indexes (for WHERE clause filtering)
CREATE INDEX entity_id IF NOT EXISTS FOR (e:Entity) ON (e.id);
CREATE INDEX source_id IF NOT EXISTS FOR (s:Source) ON (s.id);
CREATE INDEX source_project_id IF NOT EXISTS FOR (s:Source) ON (s.project_id);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entity_type);

-- Constraints (enforce uniqueness of ID)
CREATE CONSTRAINT entity_unique_id IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT source_unique_id IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE;

-- Composite index for project graph traversal
CREATE INDEX entity_updated IF NOT EXISTS FOR (e:Entity) ON (e.updated_at);
```

---

## Cache Review

### LLMResponseCache (`packages/northstar-llm/northstar_llm/cache.py`)

| Aspect | Finding | Severity |
|--------|---------|----------|
| **Key design** | SHA256 of `prompt|||model|||system_prompt|||temperature|||max_tokens` — correct per architecture spec | ✅ Good |
| **Cache backend** | `diskcache.Cache` with file-backed persistence at `~/.cache/northstar/llm` | ✅ Good |
| **Eviction** | TTL-based only (86400s = 24h). No LRU/LFU size limit. | **MEDIUM** |
| **Size limit** | Not configured. Cache grows unboundedly on disk. | **MEDIUM** |
| **Invalidation** | No selective invalidation. `clear()` wipes everything. No mechanism to invalidate by model or prompt prefix. | **MEDIUM** |
| **Concurrent access** | `diskcache` is thread-safe but not process-safe for writes. Single FastAPI worker is fine. | ✅ OK |
| **`generate_structured` coverage** | Calls `generate()` with defaults (temperature=0.7, max_tokens=4096). All structured extractions share the same cache parameters regardless of content. | **LOW** |
| **Cache poisoning risk** | Key includes all variables that affect output. Correct. | ✅ Safe |

**Recommendations:**
1. Add `size_limit=int(1e9)` (1GB) to the `Cache()` constructor to prevent unbounded growth.
2. Add per-model invalidation: `invalidate_by_model(model: str)` that scans and deletes keys matching `|||{model}|||`.
3. Consider shorter TTL for extraction prompts (3600s) vs report summarization (86400s).
4. Add cache hit/miss rate metrics for observability.

---

## Connection Pool Configuration

### Current State (CRITICAL gap)

```python
# pg_repo.py:43
self._engine = create_async_engine(database_url, echo=echo)
```

This uses asyncpg defaults:
- `pool_size=10`
- `max_overflow=10`
- `pool_recycle=-1` (never recycle)
- No `pool_pre_ping`

### Risk Assessment

The Research Agent runs:
- **Web requests** (CRUD endpoints) consuming connections
- **Background extraction tasks** (`run_extraction`) consuming connections during long-running LLM calls
- **Portal proxy requests** (additional connection load from portal)

With only 10 connections and no overflow, concurrent extraction tasks can starve web requests.

**Recommended configuration:**

```python
self._engine = create_async_engine(
    database_url,
    echo=echo,
    pool_size=20,
    max_overflow=10,
    pool_recycle=3600,       # Recycle connections after 1 hour
    pool_pre_ping=True,      # Verify connections before use
    connect_args={
        "command_timeout": 30,           # 30s query timeout
        "server_settings": {
            "application_name": "northstar-agent",
        }
    },
)
```

**Additionally**, the Chat Import Bridge SQLite engine (`staging_db.py:13`) has no pool configuration either, but SQLite with `aiosqlite` has different pooling semantics (single-writer). The `NullPool` approach from Alembic migrations should be used for SQLite if concurrent access grows.

---

## Migration Audit

### `001_initial_schema.py` Issues

| Issue | Severity | Detail |
|-------|----------|--------|
| Missing `ondelete="CASCADE"` on all FKs | **HIGH** | The ORM models specify `ondelete="CASCADE"` but the migration DDL uses bare `sa.ForeignKeyConstraint()` without `ondelete`. If someone runs this migration without using `metadata.create_all`, orphans will result. |
| Zero indexes created | **CRITICAL** | See index recommendations above. |
| Enum type drops in downgrade | ✅ OK | Drops enum types after tables, correct order. |
| `server_default=sa.text("0")` on `entities_found` | ✅ OK | Migration and model agree. |

### Migration Safety

- **Upgrade:** Creates 7 tables in dependency order. Cannot roll back mid-migration (single transaction).
- **Downgrade:** Drops all tables in reverse order, then drops enum types. Safe.
- **Offline mode:** Supported via `run_migrations_offline()` in `env.py`.
- **`ondelete` gap:** If tables were created via `metadata.create_all` (sqlalchemy ORM), CASCADE is applied. If created via this raw migration, CASCADE is NOT applied. This is a divergence between ORM model declarations and migration DDL.

---

## Neo4j Query Patterns Review

### Detailed Analysis

#### `get_project_graph()` — Cartestian Risk (HIGH)

```cypher
MATCH (s:Source)
WHERE s.project_id = $project_id
OPTIONAL MATCH (s)-[r]-(e:Entity)
WITH collect(DISTINCT s) AS source_nodes,
     collect(DISTINCT e) AS entity_nodes,
     collect(DISTINCT r) AS rels
RETURN source_nodes, entity_nodes, rels
```

**Problems:**
1. No index on `Source.project_id` → full label scan for `MATCH (s:Source)`.
2. `OPTIONAL MATCH (s)-[r]-(e:Entity)` fetches ALL relationships for ALL matched sources. For a project with 100 sources and 500 entities, this produces up to 100 × 500 = 50,000 path evaluations.
3. `collect(DISTINCT ...)` deduplicates in Cypher memory, not at the match level.

**Fix:** Add `project_id` index and use relationship direction + limit:

```cypher
MATCH (s:Source {project_id: $project_id})
OPTIONAL MATCH (s)-[r]->(e:Entity)
RETURN ...
```

#### `get_entity_graph()` — Requires APOC (LOW)

This method correctly parameterizes depth. However, it requires the APOC plugin which may not be installed on all Neo4j instances. Consider a fallback using native Cypher variable-length patterns.

#### `clear_project_graph()` — Correct but no index (MEDIUM)

```cypher
MATCH (n)
WHERE n.project_id = $project_id
DETACH DELETE n
```

Without an index on `project_id` for all labels (Source, Entity), this triggers a full graph scan.

---

## Vector/Embedding Operations

| Aspect | Finding | Severity |
|--------|---------|----------|
| **Batch embedding** | `EmbeddingService.embed_batch()` sends all texts to Ollama in one request. No chunking for batches >100 documents. | **MEDIUM** |
| **`add_documents()`** | Properly separates pre-embedded docs from those needing embedding. Uses batch embed for texts needing embeddings. Good pattern. | ✅ Good |
| **Async pattern** | Wraps ChromaDB calls in `asyncio.to_thread()` for non-blocking operation. | ✅ Good |
| **Score normalization** | `max(0.0, 1.0 - distances[i] / 2.0)` — cosine distance to similarity transformation. Per architecture spec. | ✅ Good |
| **Search filters** | `where={}` dict passed directly to ChromaDB `collection.query()`. No sanitization beyond ChromaDB's built-in filter parsing. | **LOW** |
| **No embedding dimension validation** | `add_documents()` doesn't verify that provided embeddings match the collection's expected dimension. | **LOW** |
| **Health check** | Uses real `list_collections()` call. Good liveness check per architecture spec. | ✅ Good |

---

## Pagination Patterns

| Endpoint | Pattern | Status |
|----------|---------|--------|
| All agent `list_*` routers | `offset`/`limit` (default 50, max 1000) | **OK for current scale** |
| Portal API proxy | In-memory `items[offset:offset+limit]` after fetching ALL items | **MEDIUM** — fetches all then slices |
| Portal dashboard | `limit=9999` with in-memory `sum(len(...))` | **HIGH** — unbounded memory |
| Portal cleanup | `limit=9999` on source listing | **HIGH** — unbounded memory |
| Chat import staging | `offset`/`limit` (default 50, max 1000) | **OK for SQLite** |
| `PaginatedResponse` schema | Defined but unused by any endpoint | **LOW** |

---

## Quick Wins (under 1 hour each)

1. **Add PostgreSQL FK indexes** — Run the 9 FK index creation statements listed above. Largest impact for least effort.
2. **Add Neo4j indexes** — Run the 5 Cypher index statements during `initialize()`. Eliminates full label scans.
3. **Fix `ondelete` in migration** — Update migration `ForeignKeyConstraint` calls to include `ondelete="CASCADE"` matching the ORM models.
4. **Add `pool_pre_ping=True`** — One-line change to `pg_repo.py:43` to prevent stale connection errors.
5. **Add cache size limit** — `Cache(resolved, size_limit=1_000_000_000)` in `cache.py:15`.
6. **Replace `limit=9999` with `limit=1000`** in portal dashboard/cleanup — prevents unbounded memory for large projects.

## Structural Issues (require design changes)

1. **Portal N+1 queries** — Rewrite dashboard, quality, extraction, and cleanup pages to use batch-loaded JOINs instead of per-entity fetches. Options:
   - Add repository methods like `get_project_stats(project_id)` that return counts via single SQL queries.
   - Add `list_sources_with_analyses_by_project()` using SQLAlchemy JOINs with `selectinload`.
   - Or add grouped aggregate queries (COUNT, MAX, AVG) to the repository.

2. **Cursor-based pagination** — For list endpoints expected to grow beyond 10K records, add `keyset` pagination using `(created_at, id)` as cursor to avoid offset-based scans.

3. **Connection pool tuning** — Configure `pool_size`, `max_overflow`, and `pool_recycle` based on expected concurrent background extraction tasks.

4. **Neo4j constraint enforcement** — Add `CREATE CONSTRAINT` for entity and source uniqueness during `initialize()` so MERGE operations benefit from index-backed lookups.

5. **Batch Neo4j cleanup** — Replace per-entity `delete_entity_node()` calls in cleanup with a single Cypher query:
   ```cypher
   MATCH (e:Entity) WHERE e.id IN $ids DETACH DELETE e
   ```

6. **Embedding batch chunking** — Add 100-document chunking to `add_documents()` to prevent Ollama payload overflow for large source imports.

---

## Tests/Benchmarks to Run

1. **EXPLAIN ANALYZE on `list_entities` with `project_id` filter** — Verify the JOIN on `sources.project_id` uses index scan not seq scan.
2. **Load test on dashboard endpoint** — Simulate 10 projects × 20 sources each, verify < 5 queries total (currently ~210 queries).
3. **Neo4j `get_project_graph` with 100+ sources** — Verify response time < 2s.
4. **`bulk_create_entities` with 1000 entities** — Verify batch insert time < 500ms.
5. **Cache hit rate over 100 extraction runs** — Verify > 50% cache hit rate for repeated source content.
6. **Connection pool exhaustion test** — Simulate 5 concurrent extraction tasks + 20 web requests; verify no `QueuePool limit` errors.

---

## Summary of Top 5 Findings

| Rank | Finding | Severity | Impact |
|------|---------|----------|--------|
| 1 | **Zero PostgreSQL indexes on FK columns** — Every JOIN and WHERE filter on FK columns triggers sequential scans | **CRITICAL** | 10-100x slower queries on all list endpoints as data grows |
| 2 | **Triple-nested N+1 in portal dashboard** — `projects → sources → claims` creates O(P×S×C) query explosion | **CRITICAL** | Dashboard unusable with >5 projects |
| 3 | **No Neo4j indexes or constraints** — Every Cypher MATCH on entity/source IDs triggers full label scan | **CRITICAL** | Graph queries degrade linearly with node count |
| 4 | **Unbounded `limit=9999` in portal pages** — cleanup and dashboard fetch ALL sources for ALL projects into memory | **HIGH** | OOM risk with large projects |
| 5 | **Default connection pool (10) shared by web + background tasks** — Extraction tasks hold connections during 30-120s LLM calls | **HIGH** | Connection starvation under concurrent extraction load |

---

## Final Risk Level: **HIGH**

The system is functionally correct for small-scale single-user operation (the intended deployment model). However, even at this scale, the lack of indexes means every query performs full table scans. The N+1 patterns in the portal cause hundreds of sequential queries per page load. As the data grows (more projects, more sources), response times will degrade linearly-to-quadratically.

**The index gap alone justifies immediate remediation before any production use.** Adding the 9 FK indexes will dramatically improve all query performance with zero code changes. The N+1 patterns should be addressed in the next development sprint.
