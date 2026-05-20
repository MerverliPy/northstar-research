# Northstar Data Pipeline Audit Report

**Date:** 2026-05-20
**Auditor:** Data Pipeline Reviewer (AI)
**Scope:** Full data pipeline — Chat Import Bridge, Extraction Pipeline, Data Integrity, Import/Export, Concurrency
**Files inspected:** 45+ files across `apps/`, `packages/`, `scripts/`, `tools/`, `sql/`, `tests/`

---

## Summary: Overall Pipeline Health Score — **47/100 (HIGH RISK)**

The pipeline has 2 CRITICAL bugs that make the extraction pipeline non-functional in production (`bulk_create_entities` and `bulk_create_claims` never commit). The FK cascade configuration has inconsistent gaps between ORM models and the alembic migration. The safety gates are well-implemented and tested, but the core extraction data flow cannot persist entities or claims. The chat import bridge is structurally sound but has one data-integrity concern with auto-generated project IDs. Test coverage is good for the router layer but mocks hide the commit bug with `AsyncMock` returning fake models.

**Overall Risk Level: HIGH** — immediate remediation required for the 2 CRITICAL findings before production use.

---

## Top 5 Findings

| # | Severity | Finding | Location |
|---|----------|---------|----------|
| 1 | **CRITICAL** | `bulk_create_entities` and `bulk_create_claims` use `session.flush()` but never `session.commit()` — entities and claims created during extraction are silently lost | `packages/northstar-db/northstar_db/pg_repo.py:529-567` |
| 2 | **CRITICAL** | Alembic migration `001_initial_schema.py` defines FK constraints WITHOUT `ondelete="CASCADE"`, contradicting ORM models. Analysis.project_id FK in ORM also lacks CASCADE while all other FKs have it | `migrations/versions/001_initial_schema.py`, `models.py:91` |
| 3 | **HIGH** | Extraction scoping: `run_extraction` with `force=False` never writes to Neo4j. Scraping router always passes `force=False` to background extraction, permanently excluding scraped sources from graph | `services/extraction.py:115-119`, `routers/scraping.py:60` |
| 4 | **HIGH** | Promotion auto-generates random `uuid.uuid4()` project_id when none is provided, creating orphaned projects with single sources in PostgreSQL | `services/promotion.py:23` |
| 5 | **MEDIUM** | No idempotency check before extraction — `create_extraction_log` will raise IntegrityError on duplicate (source_id, project_id) but this is not handled at the router level | `routers/extraction.py:38`, `models.py:104-106` |

---

## Pipeline Stage Audit Table

| Stage | Status | Critical Issues | Test Coverage |
|-------|--------|-----------------|---------------|
| SQLite Staging Import | ✅ HEALTHY | LOW: No duplicate detection on title/content; no indexes on status/created_at | Basic (CRUD mocked) |
| Promotion to Agent | ⚠️ DEGRADED | HIGH: Auto-generates random project UUIDs causing orphaned projects | Good (error paths covered) |
| PROMOTION_ENABLED Gate | ✅ HEALTHY | Gate enforced at router level; 403 response tested | Well covered |
| Entity Extraction Flow | 🔴 BROKEN | CRITICAL: `bulk_create_entities` never commits; entities are lost | Mock hides bug |
| Claim Extraction Flow | 🔴 BROKEN | CRITICAL: `bulk_create_claims` never commits + entities not committed = FK violation | Mock hides bug |
| LLM Structured Generation | ✅ HEALTHY | JSON fallback parsing with code-fence extraction works | Covered |
| Quality Scoring Pipeline | ✅ HEALTHY | Persists Analysis records; boundary at 0.3 threshold | Well covered |
| Embedding Generation | ✅ HEALTHY | `EmbeddingService` with 60s timeout; batch embedding supported | Covered |
| Vector Store Sync | ⚠️ DEGRADED | No sync mechanism to reconcile with PostgreSQL; no periodic consistency check | Basic |
| Neo4j Graph Sync | ⚠️ DEGRADED | Only writes when `force=True` at router + service level; scraping never triggers graph | Covered |
| PostgreSQL Write Paths | 🔴 BROKEN | CRITICAL: Bulk methods don't commit; direct create methods do commit | Mock hides bulk bug |
| FK Cascade Behavior | ⚠️ INCONSISTENT | ORM vs Alembic mismatch; Analysis.project_id lacks CASCADE in both | Not tested |
| Backup Script | ✅ HEALTHY | Confirmation prompt; proper env var fallbacks; trap for cleanup | N/A (bash) |
| Restore Script | ✅ HEALTHY | Destructive confirmation prompt; `--clean --if-exists` safe flags | N/A (bash) |
| Export Tool | ✅ HEALTHY | HTTP-based; UUID validation; proper error handling | N/A |
| Concurrency Safety | ⚠️ DEGRADED | Session-per-operation prevents dirty reads but no distributed locking for extraction/cleanup | Not tested |

---

## Detailed Findings

### 1. CRITICAL: Bulk Create Methods Never Commit (`pg_repo.py`)

**File:** `packages/northstar-db/northstar_db/pg_repo.py`, lines 529-567

**Problem:** Both `bulk_create_entities()` and `bulk_create_claims()` use `await session.flush()` to obtain generated IDs but **never call `await session.commit()`**. Every other CRUD method in `PostgresRepository` (22 total) commits explicitly. When the async context manager exits, uncommitted changes are rolled back, causing all extracted entities and claims to be silently lost.

**Root cause:** These two methods were likely rewritten from a shared-session pattern and the `commit()` call was omitted during refactoring.

**Impact chain:**
1. Extraction calls `bulk_create_entities()` → entities flushed, IDs assigned, NOT committed → session closes → entities rolled back
2. Extraction uses entity IDs to build `claim_creates` with entity FKs
3. Extraction calls `bulk_create_claims()` → tries to reference entity IDs that don't exist in DB → **ForeignKeyViolation**

**Fix:** Either: (a) Add `await session.commit()` after `await session.flush()` in both methods, OR (b) Create a single `bulk_create_extraction_results(entities, claims)` method that runs both in one transaction.

---

### 2. CRITICAL: FK CASCADE Inconsistency Between ORM, Alembic, and Internal Models

**Files:**
- `packages/northstar-models/northstar_models/models.py` (ORM definitions)
- `apps/research-agent/migrations/versions/001_initial_schema.py` (Alembic migration)
- `packages/northstar-db/northstar_db/pg_repo.py:51` (`CommonModel.metadata.create_all` init path)

**Problems:**

**(a) Alembic migration lacks all `ondelete="CASCADE"` clauses**

The migration creates FK constraints via `sa.ForeignKeyConstraint([...], [...])` without `ondelete="CASCADE"`. The ORM models define `ondelete="CASCADE"` on 8 of 9 FK columns. This means:
- If DB is initialized via Alembic → no cascade deletes → orphan detection works but deletion of parent rows fails
- If DB is initialized via `metadata.create_all` (used in `PostgresRepository.initialize()`) → cascade works correctly
- Two init paths produce different schemas

**(b) `Analysis.project_id` FK lacks `ondelete="CASCADE"` even in the ORM model**

```python
# models.py line 91 — MISSING ondelete
project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id"), nullable=True)
```

Every other FK in the codebase has `ondelete="CASCADE"`. This means deleting a project that has Analysis rows will fail with a foreign key violation, contradicting the documented architecture claim: "All FK relationships use `ondelete='CASCADE'`" (`docs/ARCHITECTURE.md`).

**Fix:** 
1. Update Alembic migration to include `ondelete="CASCADE"` on all FKs
2. Add `ondelete="CASCADE"` to `Analysis.project_id` FK in models.py
3. Create a new Alembic migration to sync existing DBs
4. Add an integration test that verifies cascade behavior on all tables

---

### 3. HIGH: Extraction Graph Sync Is Gated Behind `force` Flag — Scraping Never Populates Neo4j

**Files:** `services/extraction.py:115-119`, `routers/scraping.py:60`

In `run_extraction()`, Neo4j graph writes are gated behind the `force` parameter:
```python
if force:                           # line 115
    for entity in created_entities:
        await neo4j.create_entity_node(entity)
    for claim in created_claims:
        await neo4j.create_claim_relationship(claim)
```

At the router level, `trigger_extraction` requires either `req.force=True` OR `FORCE_GRAPH_EXTRACTION=true`. However, the **scraping router** hardcodes `force=False`:
```python
# routers/scraping.py line 60
background_tasks.add_task(
    run_extraction, ..., force=False,
)
```

This means: even if `FORCE_GRAPH_EXTRACTION=true` is set, scraped sources with `extract=True` will **NEVER** have their entities/claims synced to Neo4j because the router passes `force=False` to the service. The router checks the setting, but the scraper doesn't respect it.

**Fix:** 
1. `run_extraction` should check `settings.force_graph_extraction` independently of the `force` parameter, OR
2. Scraping router should pass `force=settings.force_graph_extraction` to `run_extraction`

---

### 4. HIGH: Promotion Auto-Generates Random Project UUIDs

**File:** `services/promotion.py:23`

```python
pid = uuid.UUID(project_id) if project_id else uuid.uuid4()
```

When a staged import is promoted without a `project_id`, a **random** UUID is generated for the project. The Source is then created in PostgreSQL with this random project ID. This creates:
- Orphaned projects containing exactly one source
- No way to trace the lineage back to the staging import
- Project names are blank (SourceCreate is sent but no ProjectCreate is sent alongside)

**Fix:** 
1. Require `project_id` for promotion — reject with 400 if not provided
2. OR: Create a named project first, then promote the source into it
3. OR: Use a designated "default import project" with a fixed, well-known UUID

---

### 5. MEDIUM: No Idempotency on Extraction Trigger

**File:** `routers/extraction.py:38`

The extraction router always calls `db.create_extraction_log()` before dispatching the background task. The `extraction_logs` table has a `UniqueConstraint("source_id", "project_id")`. If extraction is triggered twice for the same source, the second call will raise an `IntegrityError` (500) rather than returning a meaningful error or returning the existing extraction log.

Additionally, `run_extraction` uses `db.get_extraction_log(source_id)` which returns the **latest** log (ORDER BY created_at DESC LIMIT 1), so it will pick up the most recent log — but this doesn't handle the case where the first extraction is still in progress.

**Fix:** Check for existing IN_PROGRESS/PENDING extraction logs before creating a new one. Return 409 Conflict with the existing extraction ID.

---

## Data Integrity Findings

### metadata ↔ metadata_ Mapping

✅ **HEALTHY** — The ORM uses `metadata_` mapped to column `"metadata"`. All `update_*` methods in `PostgresRepository` handle the mapping via `update_dict["metadata_"] = update_dict.pop("metadata")`. All `create_*` methods pass `metadata_=data.metadata` correctly. This pattern is consistent across all 9 entity types.

### PG ↔ Neo4j Consistency

⚠️ **DEGRADED** — No periodic reconciliation mechanism. Entity nodes are created with `MERGE` (upsert semantics), which is safe for idempotent writes but doesn't detect stale/deleted entities. The cleanup route (`/cleanup/execute`) manually deletes orphaned entities from Neo4j then PostgreSQL, but this is a manual operation gated behind `ENABLE_DESTRUCTIVE_CLEANUP`.

### PG ↔ Vector Store Consistency

⚠️ **DEGRADED** — `run_extraction()` adds source documents to the vector store unconditionally, even if `force=False` (no Neo4j sync). There is:
- No mechanism to detect vector store entries for deleted sources
- No deduplication check — `add_documents` uses `source_{uuid}` as the document ID, which ChromaDB will upsert by default, but this is implicit behavior
- No health-check that validates vector store entries against PostgreSQL source count

### FK Cascade Summary

| Parent → Child | ORM CASCADE | Alembic CASCADE | Status |
|---|---|---|---|
| Project → Source | ✅ | ❌ | MISMATCH |
| Project → Report | ✅ | ❌ | MISMATCH |
| Project → ExtractionLog | ✅ | ❌ | MISMATCH |
| Project → Analysis | ❌ | ❌ | **MISSING IN BOTH** |
| Source → Entity | ✅ | ❌ | MISMATCH |
| Source → Claim | ✅ | ❌ | MISMATCH |
| Source → Analysis | ✅ | ❌ | MISMATCH |
| Source → ExtractionLog | ✅ | ❌ | MISMATCH |
| Entity → Claim | ✅ | ❌ | MISMATCH |

---

## Concurrency Risk Points

### Session-per-operation Pattern

✅ **HEALTHY** — Every `PostgresRepository` method opens its own session via `async with self._session() as session:`. This prevents dirty reads across operations and avoids shared-state issues.

⚠️ **RISK: No Transactional Scope for Multi-Operation Flows**

`run_extraction()` calls multiple repository methods sequentially, each with its own session. If `bulk_create_entities` succeeded (if it committed), and `bulk_create_claims` failed, the entities would be committed but claims lost — with no rollback mechanism to clean up. A compensating transaction pattern or single-session extraction would be safer.

### Background Task Concurrency

⚠️ **DEGRADED** — Extraction runs as a FastAPI `BackgroundTasks` task. If two extraction requests for the same source arrive concurrently:
1. Both pass the router-level check (no existing log check — see Finding #5)
2. Both succeed at `create_extraction_log` (the `UniqueConstraint` allows the first; second gets IntegrityError)
3. Only the first background task dispatches successfully

This is a partial protection, but the 500 error is not user-friendly.

### No Distributed Locking

⚠️ **LOW RISK for single-instance** — No distributed lock mechanism exists for extraction, cleanup, or promotion. Acceptable for single-instance deployment but would need addressing for horizontal scaling.

---

## Test Coverage Gap Analysis

| Area | Coverage Quality | Gap |
|------|-----------------|-----|
| Router-level API tests | ✅ Good | — |
| Extraction service tests | ⚠️ Mock-hides-bug | AsyncMock never tests commit/flush distinction |
| Quality service tests | ✅ Good | Boundary condition at 0.3 tested |
| Promotion service tests | ✅ Good | Error paths (HTTP error, network error, not found, already promoted) covered |
| Safety gate tests | ✅ Good | All three gates (extraction, cleanup, promotion) tested for default-disabled |
| Bridge isolation tests | ✅ Good | Verifies Bridge never imports `northstar_db` |
| PostgreSQL CRUD tests | ⚠️ Mock-hides-bug | All CRUD tested but mocked; bulk commit bug invisible |
| Neo4j tests | ✅ Adequate | Session management and error paths tested |
| Vector store tests | ✅ Adequate | Schema and basic operations tested |
| FK cascade behavior | ❌ None | No integration test verifies cascade deletes |
| Bulk commit behavior | ❌ None | No integration test for extraction persistence |
| Concurrent extraction | ❌ None | No race condition test |
| Alembic migration validation | ❌ None | No test compares migration schema to ORM model |

---

## Quick Wins (Low Effort, High Impact)

1. **Add `await session.commit()` after `await session.flush()` in `bulk_create_entities` and `bulk_create_claims`** — 2 lines changed, fixes CRITICAL #1
2. **Add `ondelete="CASCADE"` to `Analysis.project_id` FK** — 1 line changed, fixes half of CRITICAL #2
3. **Make `promotion.py` require project_id** — Change `uuid.uuid4()` fallback to raise ValueError, fixes HIGH #4
4. **Add `settings.force_graph_extraction` check in `run_extraction`** — adds environment-based gate inside the service, fixes HIGH #3
5. **Add NOT NULL check or try/except for duplicate extraction logs** — fixes MEDIUM #5
6. **Add indexes on `staged_imports(status)` and `staged_imports(created_at)`** — improves query performance

---

## Structural Issues (Requires Design Discussion)

1. **Single-session extraction transaction**: The entire extraction flow (entities + claims + log update) should run in one DB session for atomicity. Currently uses 4+ separate sessions.
2. **Alembic migration synchronization**: The migration and ORM models need to be kept in sync. Consider generating migrations from ORM models rather than hand-writing them.
3. **Vector store reconciliation**: A periodic reconciler (or at least a health check) that compares PostgreSQL source count to ChromaDB document count would prevent silent drift.
4. **Graph extraction policy**: The current dual-gate (router-level `force` flag + service-level `force` parameter) is confusing. Consider a single `FORCE_GRAPH_EXTRACTION` environment variable that controls both, or split into `EXTRACTION_ENABLED` (entities/claims only) and `GRAPH_SYNC_ENABLED` (Neo4j writes).
5. **Promotion project lifecycle**: When a promoted source receives a random project_id, the project exists with no metadata connecting it to the original import. Consider tracking the `staged_import_id` in the Source metadata for lineage tracing.

---

## Final Risk Level: **HIGH**

**Immediate action required:**
1. Fix `bulk_create_entities` and `bulk_create_claims` — missing commits (CRITICAL, 2 lines)
2. Fix `Analysis.project_id` FK cascade (CRITICAL, 1 line)
3. Sync Alembic migration with ORM cascade behavior (CRITICAL, ~8 lines + new migration)

**Recommended within 1 sprint:**
4. Fix promotion auto-generated project IDs (HIGH)
5. Fix scraping extraction Neo4j exclusion (HIGH)
6. Add extraction idempotency check (MEDIUM)
7. Add integration test for extraction persistence (MEDIUM)
