# Database Operations Audit Report

**Date:** 2026-05-20
**Auditor:** AI Agent (deepseek-v4-pro)
**Scope:** Full-stack database audit (PostgreSQL, Neo4j, SQLite, Migrations, Repository Layer, Docker)

---

## Overall DB Health Score: **62/100** (CAUTION)

Three critical data-integrity bugs were found that can cause silent data loss. The schema foundation is solid, but the migration/ORM cascade mismatch and the uncommitted bulk operations are urgent fixes.

| Band | Score | Status |
|------|-------|--------|
| Schema design | 75/100 | Good structure, naming convention applied |
| Migration health | 40/100 | Single migration, out-of-sync with ORM CASCADE |
| Index coverage | 45/100 | No explicit indexes beyond PKs and one unique constraint |
| Repository compliance | 70/100 | Session-per-operation pattern followed, but 2 methods broken |
| Docker setup | 85/100 | Correct volumes, healthchecks, restart policies |
| Neo4j layer | 55/100 | No constraint/index init, APOC dependency unchecked |
| SQLite staging | 65/100 | Works, but no migration system, missing `updated_at` |

---

## 1. CRITICAL Findings

### C1: Alembic Migration Missing `ondelete="CASCADE"` on ALL Foreign Keys

**Severity:** CRITICAL
**File:** `apps/research-agent/migrations/versions/001_initial_schema.py`
**Impact:** Orphaned child rows on parent deletion; FK violations on manual deletes

The single Alembic migration creates 9 `ForeignKeyConstraint` definitions, **none** of which include `ondelete="CASCADE"`. However, 7 of the 9 FKs in the ORM model (`packages/northstar-models/northstar_models/models.py`) specify `ondelete="CASCADE"`.

**Affected FKs (in migration — all missing CASCADE):**
| Child Table | FK Column | Parent Table | ORM has CASCADE? |
|------------|-----------|-------------|-------------------|
| sources | project_id | projects | YES |
| entities | source_id | sources | YES |
| claims | source_id | sources | YES |
| claims | entity_id | entities | YES |
| reports | project_id | projects | YES |
| analyses | source_id | sources | YES |
| analyses | project_id | projects | **NO** |
| extraction_logs | source_id | sources | YES |
| extraction_logs | project_id | projects | YES |

**Consequence:**
- If the database is created via `alembic upgrade head`, PostgreSQL will **reject** `DELETE FROM projects WHERE id = ...` with a foreign key violation because child rows still reference it.
- The ORM's `ondelete="CASCADE"` only takes effect when SQLAlchemy generates DDL via `create_all()`, which is not the path used in production (Alembic is the supported path per the AGENTS.md instructions).

**Fix:** Add `ondelete="CASCADE"` to all FK columns in a new Alembic migration that drops and recreates the constraints, or alters them with `ALTER TABLE ... DROP CONSTRAINT ... ADD CONSTRAINT ... ON DELETE CASCADE`.

---

### C2: `Analysis.project_id` FK Missing `ondelete="CASCADE"` in ORM Model

**Severity:** CRITICAL
**File:** `packages/northstar-models/northstar_models/models.py`, line 91
**Impact:** Deleting a project leaves orphaned Analysis rows

```python
# Line 90-91 — MISSING ondelete="CASCADE"
project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
    ForeignKey("projects.id"), nullable=True  # ← should have ondelete="CASCADE"
)
```

Every other FK in the project uses `ondelete="CASCADE"`. This is the sole exception. Both the migration and the ORM model need fixing.

**Fix:** Change to `ForeignKey("projects.id", ondelete="CASCADE")`.

---

### C3: `bulk_create_entities()` and `bulk_create_claims()` Do Not Commit

**Severity:** CRITICAL
**File:** `packages/northstar-db/northstar_db/pg_repo.py`, lines 529–567
**Impact:** Silent data loss — entities/claims created via bulk methods are never persisted

```python
async def bulk_create_entities(
    self, entities: list[EntityCreate]
) -> list[Entity]:
    async with self._session() as session:
        models = [...]
        session.add_all(models)
        await session.flush()       # ← flushes to get IDs, but...
        return models               # ← session closes, changes ROLLED BACK
```

All other CRUD methods in the repository call `await session.commit()` before returning. The bulk methods only call `await session.flush()`, which assigns IDs but does **not** persist to disk. When the `async with` context manager exits, the session closes and all uncommitted changes are discarded.

**Verification:** This pattern appears in:
- `bulk_create_entities` (line 546)
- `bulk_create_claims` (line 566)

**Fix:** Add `await session.commit()` after `session.flush()`, or after `session.add_all()` and remove the flush.

---

## 2. HIGH Findings

### H1: No Neo4j Constraint or Index Initialization

**Severity:** HIGH
**File:** `packages/northstar-db/northstar_db/neo4j_repo.py`
**Impact:** Duplicate nodes possible; full graph scans on filtered queries

`Neo4jRepository.initialize()` only runs `RETURN 1` for connectivity. There is no code anywhere in the repo that creates:

| What's Missing | Why Needed |
|---|---|
| Unique constraint on `Entity(id)` | `MERGE (e:Entity {id: $id})` can create duplicate Entity nodes if the constraint doesn't exist — MERGE relies on a uniqueness constraint to match existing nodes |
| Unique constraint on `Source(id)` | Same issue for Source nodes created via `create_claim_relationship` |
| Index on `Source(project_id)` | `get_project_graph()` filters `WHERE s.project_id = $project_id` → full label scan without index |
| Index on `Entity(entity_type)` | `query_entities_by_type()` filters `WHERE e.entity_type = $entity_type` → full label scan |

**Fix:** Add constraint/index creation in `Neo4jRepository.initialize()`:
```cypher
CREATE CONSTRAINT entity_id_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT source_id_unique IF NOT EXISTS FOR (s:Source) REQUIRE s.id IS UNIQUE;
CREATE INDEX source_project_id IF NOT EXISTS FOR (s:Source) ON (s.project_id);
CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.entity_type);
```

---

### H2: APOC Plugin Dependency Not Validated

**Severity:** HIGH
**File:** `packages/northstar-db/northstar_db/neo4j_repo.py`, line 168
**Impact:** Runtime failure in `get_entity_graph()` if APOC is not installed

```python
CALL apoc.path.subgraphNodes(e, {
    maxLevel: $depth,
    relationshipFilter: '>'
})
```

APOC is a Neo4j plugin that must be explicitly installed. The Neo4j 5 Community Docker image does not include APOC by default. If `get_entity_graph()` is called without APOC installed, Neo4j returns a Cypher error (procedure not found), which propagates as an unhandled exception.

**Fix Options:**
1. Add a startup check in `initialize()`: `CALL apoc.help('path')` and raise `GraphError` if missing.
2. Replace `apoc.path.subgraphNodes` with native Cypher variable-length path expansion: `MATCH path = (e)-[*0..$depth]->(related)`.
3. Document the APOC dependency in the setup instructions.

---

### H3: SQLite `StagedImport` Missing `updated_at` Column

**Severity:** HIGH
**File:** `apps/chat-import-bridge/chat_import_bridge/models.py`
**Impact:** Breaks the `updated_at` convention established by all 7 PostgreSQL models

The `StagedImport` model has:
- `created_at` — present
- `promoted_at` — present (specific milestone timestamp)
- `updated_at` — **MISSING**

All 7 PostgreSQL models inherit `CommonModel`, which provides `updated_at` with `onupdate`. Every non-import audit trail and change-tracking query that depends on `updated_at` is silently unavailable for staged imports.

**Fix:** Add `updated_at` column with `onupdate` behavior:
```python
updated_at: Mapped[datetime] = mapped_column(
    DateTime,
    default=lambda: datetime.now(timezone.utc),
    onupdate=lambda: datetime.now(timezone.utc),
)
```

---

## 3. MEDIUM Findings

### M1: No Explicit Indexes on High-Frequency Query Columns

**Severity:** MEDIUM
**Files:** `apps/research-agent/migrations/versions/001_initial_schema.py` (no indexes defined)
**Impact:** Sequential scans on large tables for common list/filter operations

PostgreSQL does **not** automatically create indexes on foreign key columns. The only user-defined index in the entire PG schema is the `uq_extraction_log_source_project` unique constraint (which creates an implicit index).

**Columns appearing in WHERE/ORDER BY clauses with no index:**

| Table | Column(s) | Query Pattern |
|-------|-----------|---------------|
| sources | `project_id` | `list_sources()` — WHERE + ORDER BY created_at |
| sources | `(project_id, created_at)` | Compound would benefit sorted list queries |
| entities | `source_id` | `list_entities()` — WHERE |
| entities | `(source_id, created_at)` | Compound for sorted listing |
| claims | `source_id` | `list_claims()` — WHERE |
| claims | `entity_id` | `list_claims()` — WHERE |
| reports | `project_id` | `list_reports()` — WHERE + ORDER BY |
| analyses | `source_id` | `list_analyses()` — WHERE |
| analyses | `project_id` | `list_analyses()` — WHERE |
| analyses | `(project_id, created_at)` | Compound for sorted listing |
| extraction_logs | `source_id` | `get_extraction_log()` — WHERE + ORDER BY + LIMIT 1 |
| extraction_logs | `project_id` | `list_extraction_logs()` — WHERE |
| projects | `name` | `get_project_by_name()` — covered by UNIQUE constraint (implicit index) ✓ |

**Impact:** Currently low (dev-stage data volumes). Will degrade linearly as tables grow.

**Fix:** Create indexes in a new migration. Priority order: `sources(project_id)`, `entities(source_id)`, `claims(source_id)`, `reports(project_id)`, `analyses(project_id)`.

---

### M2: No Migration System for SQLite Staging Database

**Severity:** MEDIUM
**File:** `apps/chat-import-bridge/chat_import_bridge/services/staging_db.py`
**Impact:** Schema evolution requires manual intervention or data loss

The SQLite staging database uses `StagingBase.metadata.create_all` at startup (line 22). There is no Alembic configuration, no migration tracking table, and no versioning. If the `StagedImport` model schema changes, there's no upgrade path — the old database must be deleted or manually altered.

**Fix:** Either:
1. Add a separate Alembic config in `apps/chat-import-bridge/migrations/` for the SQLite database.
2. Use `sqlalchemy-alembic` with a dedicated env pointing at `StagingBase.metadata`.

---

### M3: `get_extraction_log()` Queries by `source_id` Without `project_id`

**Severity:** MEDIUM
**File:** `packages/northstar-db/northstar_db/pg_repo.py`, lines 503–513
**Impact:** Returns wrong project's extraction log if source is shared (currently impossible due to FK, but fragile design)

```python
async def get_extraction_log(self, source_id: uuid.UUID) -> ExtractionLog | None:
    async with self._session() as session:
        result = await session.execute(
            select(ExtractionLog)
            .where(ExtractionLog.source_id == source_id)
            .order_by(ExtractionLog.created_at.desc())
            .limit(1)
        )
```

The unique constraint on extraction_logs is `(source_id, project_id)`, but the query only filters on `source_id`. Currently safe because `source.project_id` is non-nullable, but the method signature doesn't express the constraint.

**Fix:** Add `project_id: uuid.UUID` parameter to the method and include it in the WHERE clause.

---

### M4: `seed.sql` Uses Hardcoded UUIDs — Not Idempotent

**Severity:** MEDIUM
**File:** `sql/seed.sql`
**Impact:** Re-running seed fails with duplicate key violations

```sql
INSERT INTO projects (id, ...) VALUES
  ('a0000000-0000-0000-0000-000000000001', ...),
  ('a0000000-0000-0000-0000-000000000002', ...);
```

No `ON CONFLICT` clause. Re-running the seed after the first run fails.

**Fix:** Add `ON CONFLICT (id) DO UPDATE SET ...` or `ON CONFLICT (id) DO NOTHING`.

---

### M5: `StagedImport.metadata_json` Is Plain `Text` Not JSON

**Severity:** MEDIUM
**File:** `apps/chat-import-bridge/chat_import_bridge/models.py`, line 19
**Impact:** No JSON validation at DB layer; potential for corrupted serialized data

```python
metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
```

All 7 PostgreSQL models store metadata in a native `JSON`/`JSONB` column. The staging model stores serialized JSON as a plain text blob. While SQLite has no native JSON type, modern SQLite (3.38+) supports `JSON` affinity and `->`/`->>` operators.

**Fix:** Consider using SQLAlchemy's `JSON` type (which maps to TEXT in SQLite but provides validation) or at minimum document the convention difference.

---

## 4. LOW Findings

### L1: Docker Compose Uses Hardcoded Credentials in Plaintext

**Severity:** LOW
**File:** `docker/docker-compose.yml`
**Impact:** Minimal (local development only; `.env` passthrough would be better)

```yaml
POSTGRES_USER: northstar
POSTGRES_PASSWORD: northstar
NEO4J_AUTH: neo4j/northstar
```

**Fix:** Use `${VAR:-default}` syntax to pull from environment or a `.env` file.

---

### L2: `models.py` Metadata Column — `aliases` Uses Bare `list` Type

**Severity:** LOW
**File:** `packages/northstar-models/northstar_models/models.py`, line 51
**Impact:** No runtime validation of list element types

```python
aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
```

This is typed as plain `list` rather than `list[str]`. The Pydantic schema correctly uses `Optional[list[str]]` (schemas.py line 88), so API-level validation catches this, but ORM-level it's untyped.

**Fix:** Change to `Mapped[Optional[list[str]]]`.

---

### L3: `PgRepository.initialize()` Runs `create_all` — Redundant With Alembic

**Severity:** LOW
**File:** `packages/northstar-db/northstar_db/pg_repo.py`, lines 50–56
**Impact:** If Alembic manages migrations, `create_all` should not run (risk of skipping migrations)

```python
async def initialize(self) -> None:
    async with self._engine.begin() as conn:
        await conn.run_sync(CommonModel.metadata.create_all)  # ← bypasses Alembic
```

If the operator runs `alembic upgrade head` to apply migrations, then starts the app which calls `initialize()`, the `create_all` call is a no-op (tables already exist). But if a new developer starts the app without running Alembic, `create_all` creates tables without the migration history — making future Alembic runs potentially problematic.

**Fix:** Either remove `create_all` from `initialize()` (relying solely on Alembic) or guard it behind a flag like `auto_create_tables: bool = False`.

---

## 5. Schema Audit Table

### 5.1 PostgreSQL Tables (7 tables, all inherit CommonModel)

| Table | PK | created_at | updated_at | metadata JSON | FK Count | CASCADE Count | Indexes |
|-------|-----|-----------|-----------|---------------|----------|---------------|---------|
| projects | UUID ✓ | ✓ | ✓ | ✓ | 0 | — | 1 (name UNIQUE) |
| sources | UUID ✓ | ✓ | ✓ | ✓ | 1 | 0 (ORM: 1) | 0 |
| entities | UUID ✓ | ✓ | ✓ | ✓ | 1 | 0 (ORM: 1) | 0 |
| claims | UUID ✓ | ✓ | ✓ | ✓ | 2 | 0 (ORM: 2) | 0 |
| reports | UUID ✓ | ✓ | ✓ | ✓ | 1 | 0 (ORM: 1) | 0 |
| analyses | UUID ✓ | ✓ | ✓ | ✓ | 2 | 0 (ORM: 1) | 0 |
| extraction_logs | UUID ✓ | ✓ | ✓ | ✓ | 2 | 0 (ORM: 2) | 1 (uq source+project) |

**Key:** ✓ = present, ORM = value in model definition vs. actual DB migration

### 5.2 Neo4j Graph

| Label | Properties | Constraints | Indexes |
|-------|-----------|-------------|---------|
| Entity | id, name, entity_type, source_id, description, updated_at | **NONE** | **NONE** |
| Source | id, project_id (implied) | **NONE** | **NONE** |

| Relationship Type | From | To | Properties |
|-------------------|------|----|------------|
| MAKES_CLAIM | Source | Entity | claim_id, claim_text, claim_type, confidence |
| MENTIONS (and 9 others) | Source/Entity | Entity | configurable via `link_entities`/`link_source_to_entity` |

**Validated relationship types (allowlist):** MENTIONS, RELATES_TO, MAKES_CLAIM, CITES, REFERENCES, SUPPORTS, CONTRADICTS, ASSOCIATED_WITH, PART_OF, LEADS_TO (10 total)

### 5.3 SQLite Staging

| Table | PK | created_at | updated_at | Metadata |
|-------|-----|-----------|-----------|----------|
| staged_imports | INTEGER autoincrement | ✓ | **MISSING** | TEXT (not JSON) |

---

## 6. Repository Pattern Compliance

### 6.1 `PostgresRepository` — 7 entity types

| Method Pattern | Project | Source | Entity | Claim | Report | Analysis | ExtractionLog |
|---------------|---------|--------|--------|-------|--------|----------|----------------|
| create_X | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| get_X | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| list_X | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| update_X | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | special |
| delete_X | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| bulk_create_X | ✗ | ✗ | ⚠ BROKEN | ⚠ BROKEN | ✗ | ✗ | ✗ |
| get_by_alt_key | ✓ (name) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |

**Compliance issues:**
- `bulk_create_*` methods don't commit (C3)
- `update_extraction_log` has a non-standard signature (positional params vs. data object)
- No `delete_extraction_log` method exists
- No `list_claims` support for global/unfiltered listing
- No `get_source_by_url` or `get_entity_by_name` lookup methods

### 6.2 `Neo4jRepository` — Graph operations

| Category | Methods | Compliance |
|----------|---------|------------|
| Node CRUD | create_entity_node, delete_entity_node | Partial — no update, no get single |
| Relationships | create_claim_relationship, link_source_to_entity, link_entities | ✓ |
| Graph queries | get_entity_graph, get_project_graph, find_paths | ✓ |
| Utility | query_entities_by_type, get_entity_count, get_relationship_count | ✓ |
| Cleanup | clear_project_graph | ✓ |
| Init/constraints | **MISSING** | ✗ (see H1) |

### 6.3 Session Management

| Aspect | PostgreSQL | Neo4j | SQLite |
|--------|-----------|-------|--------|
| Pattern | `async with self._session()` | `async with self._session()` | FastAPI Depends → yield |
| Session-per-op | ✓ | ✓ | ✗ (session injected) |
| `expire_on_commit` | `False` | N/A | `False` |
| Connection pooling | SQLAlchemy engine pool | Neo4j driver pool | Per-engine default |
| Graceful close | `dispose()` | `driver.close()` | N/A (lifespan-scoped) |

---

## 7. Migration Health

### 7.1 Alembic Configuration

| Aspect | Status | Notes |
|--------|--------|-------|
| Config location | `apps/research-agent/migrations/` | Standard, colocated with app |
| Version table | Default (`alembic_version`) | OK |
| Async support | ✓ | Uses `async_engine_from_config` + `asyncio.run` |
| Offline mode | ✓ | `run_migrations_offline()` implemented |
| Environment variable override | ✓ | `DATABASE_URL` env var respected |
| `target_metadata` | `CommonModel.metadata` | Correct — covers all 7 tables |
| Naming convention | Defined in `base.py` | 5 conventions (ix, uq, ck, fk, pk) |

### 7.2 Migration Files

| File | Status | Issues |
|------|--------|--------|
| `001_initial_schema.py` | Active | **Missing `ondelete="CASCADE"` on all 9 FKs** (C1) |
| `alembic.ini` | Active | Hardcoded URL (overridden in env.py) |
| `env.py` | Active | Correct async pattern |
| `script.py.mako` | Template | Standard Alembic template |

### 7.3 Migration Count

- **Migrations:** 1 (initial schema)
- **Unmigrated model changes:** 0 (models match migration minus CASCADE issue)
- **Pending autogenerate:** Migration would produce no new columns, only CASCADE constraint changes

---

## 8. Quick Wins (1–2 hours total)

| # | Fix | Effort | Impact |
|---|-----|--------|--------|
| 1 | Add `await session.commit()` to `bulk_create_entities` and `bulk_create_claims` | 5 min | Fixes silent data loss (C3) |
| 2 | Add `ondelete="CASCADE"` to `Analysis.project_id` FK in ORM model | 2 min | Aligns with all other FKs (C2) |
| 3 | Add `updated_at` to `StagedImport` model | 10 min | Convention compliance (H3) |
| 4 | Add Neo4j constraint/index creation to `initialize()` | 15 min | Prevents duplicate nodes, improves performance (H1) |
| 5 | Add APOC availability check to `initialize()` | 10 min | Fails fast with clear error (H2) |
| 6 | Add `ON CONFLICT DO NOTHING` to `seed.sql` | 2 min | Idempotent seeding (M4) |

---

## 9. Structural Issues (4–8 hours)

| # | Fix | Effort | Impact |
|---|-----|--------|--------|
| 1 | Create Alembic migration to add `ondelete="CASCADE"` to all 9 FKs | 2 hrs | Fixes CASCADE at DB level (C1) — requires careful ordering of DROP/ADD CONSTRAINT |
| 2 | Create Alembic migration adding indexes on FK columns used in WHERE clauses | 1 hr | Performance baseline (M1) — 6–8 indexes across 5 tables |
| 3 | Set up Alembic for SQLite staging DB | 2 hrs | Migration system for staging (M2) |
| 4 | Add `project_id` parameter to `get_extraction_log()` | 30 min | Query correctness (M3) |
| 5 | Consider removing `create_all` from `PgRepository.initialize()` or gating it | 30 min | Migration integrity (L3) |

---

## 10. Appendix: Docker Database Configuration Review

```yaml
# docker/docker-compose.yml — reviewed
postgres:
  image: postgres:16-alpine          ✓ Latest 16, Alpine for small footprint
  restart: unless-stopped            ✓ Resilient
  environment:
    POSTGRES_DB: northstar           ✓
    POSTGRES_USER: northstar         ⚠ Hardcoded (L1)
    POSTGRES_PASSWORD: northstar     ⚠ Hardcoded (L1)
  ports: ["5432:5432"]              ✓ Standard
  volumes:
    - northstar-pg-data:/var/lib/... ✓ Named volume, data persists
  healthcheck:
    test: pg_isready                 ✓ Correct
    interval: 5s                     ✓ Reasonable

neo4j:
  image: neo4j:5-community           ✓ Matches Bolt driver expectations
  restart: unless-stopped            ✓
  environment:
    NEO4J_AUTH: neo4j/northstar      ⚠ Hardcoded (L1)
  ports: ["7687:7687", "7474:7474"] ✓ Bolt + HTTP
  volumes:
    - northstar-neo4j-data:/data     ✓ Named volume
  healthcheck:
    test: neo4j status               ✓ Correct
    interval: 10s                    ✓
    start_period: 30s                ✓ Generous for first boot

volumes:
  northstar-pg-data:                 ✓ Named, managed by Docker
  northstar-neo4j-data:              ✓ Named, managed by Docker
```

**Docker Score: 85/100**
- Volume persistence: correct
- Healthchecks: correct
- Image selection: correct
- Deductions: hardcoded credentials (-10), no resource limits configured (-5)

---

*End of audit report.*
