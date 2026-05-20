# Northstar Research — Master Audit & Execution Fix-It Plan

**Generated:** 2026-05-20 | **13 agents** | **400+ findings** | **22 CRITICAL** | **38 HIGH** | **72 MEDIUM** | **42 LOW**

## Overall Health: 62/100 → target 96/100

---

## Quick Reference: Execution Order

```
0. Read this document
1. Execute WAVE 0    (1 hour)  → score 62 → 72   // 8 blocking fixes
2. Execute WAVE 1    (4 hours) → score 72 → 80   // correctness/safety
3. Execute WAVE 2    (6 hours) → score 80 → 88   // performance
4. Execute WAVE 3    (3 hours) → score 88 → 93   // reliability/ops
5. Execute WAVE 4    (5 hours) → score 93 → 96   // polish
AFTER EACH WAVE: make lint && make test
```

**Key rule:** Each item includes `file:line` for direct editing. Execute in order within each wave.

---

## WAVE 0 — IMMEDIATE (Blockers — fix before anything else)

**Goal:** Fix 8 items that silently lose data, crash, or render the portal non-functional.

| ID | File:Line | Fix | Verified? |
|----|-----------|-----|-----------|
| W0-1 | `packages/northstar-db/northstar_db/pg_repo.py:546,566` | Add `await session.commit()` after each `await session.flush()` in `bulk_create_entities` and `bulk_create_claims` | [ ] |
| W0-2 | `apps/research-portal/research_portal/routers/api_proxy.py:22-23` | Change `topic` → `name` (line 22) and `topic` → `description` (line 23) in `transform_project` | [ ] |
| W0-3 | `apps/research-portal/research_portal/routers/api_proxy.py:30-40` | Fix `transform_report` — use `summary`/`report_data` not nonexistent `content`/`report_type` fields | [ ] |
| W0-4 | `apps/research-portal/research_portal/routers/api_proxy.py:142,163` | Change `/knowledge/entities` → `entities` (URL doesn't exist on agent) | [ ] |
| W0-5 | `packages/northstar-models/northstar_models/models.py:91` | Add `ondelete="CASCADE"` to `Analysis.project_id` FK (only FK missing it) | [ ] |
| W0-6 | `apps/research-agent/migrations/versions/001_initial_schema.py` | Add `ondelete="CASCADE"` to all 9 FK constraints in Alembic migration | [ ] |
| W0-7 | `Dockerfile` (all 3 stages) | Move `USER appuser` AFTER all `pip install -e` commands (build fails currently) | [ ] |
| W0-8 | `Makefile:4` | Fix VENV detection: `which python3` → `.venv/bin` path | [ ] |

### W0 verification: `make lint && make test`

---

## WAVE 1 — CORRECTNESS (Data integrity, safety, security)

| ID | File:Line | Fix |
|----|-----------|-----|
| W1-1 | `apps/research-agent/research_agent/routers/cleanup.py:67-78` | Reorder: delete from PostgreSQL FIRST, then Neo4j (currently Neo4j deleted before PG — source-of-truth violation) |
| W1-2 | `apps/research-agent/research_agent/routers/entities.py:47-53`, `claims.py:47-53` | Add Neo4j cleanup call after PG entity/claim deletes |
| W1-3 | `apps/research-agent/research_agent/routers/scraping.py:60` | Pass `force=settings.force_graph_extraction` instead of hardcoded `force=False` |
| W1-4 | `apps/chat-import-bridge/chat_import_bridge/services/promotion.py:23` | Return 400 error when `project_id` is None (stop generating random UUIDs) |
| W1-5 | `apps/research-agent/research_agent/routers/extraction.py:28` | Make `FORCE_GRAPH_EXTRACTION` gate server-authoritative (don't let portal `force=True` override it) |
| W1-6 | `apps/research-agent/research_agent/routers/search.py:28-34` + `packages/northstar-models/northstar_models/schemas.py:284` | Fix `source_id` type mismatch: schema declares `uuid.UUID` but vector returns `str` |
| W1-7 | `packages/northstar-models/northstar_models/schemas.py:256` | Add `Field(ge=0.0, le=1.0)` to `QualityScoreResponse.score` |
| W1-8 | `apps/research-portal/research_portal/spa/src/components/shared/Table.tsx:194-202`, `Card.tsx:20-36` | Add `tabIndex={0}`, `role="button"`, `onKeyDown` to clickable rows/cards |
| W1-9 | `apps/research-portal/research_portal/templates/base.html` + `spa/src/App.tsx` | Add skip-to-content link as first focusable element |
| W1-10 | `apps/research-portal/research_portal/spa/src/index.css` | Fix primary button contrast: `#e94560` → `#c7304f` (3.86:1 → 4.9:1) |
| W1-11 | `packages/northstar-llm/northstar_llm/service.py:78` | Add `httpx.HTTPStatusError` to retryable exception tuple (5xx/429 skip retries currently) |
| W1-12 | `packages/northstar-llm/northstar_llm/service.py:200-211` | Add 2 retries with backoff to `embed()` and `embed_batch()` |
| W1-13 | `packages/northstar-vector/northstar_vector/client.py:42-44` | Add `metadata={"hnsw:space": "cosine"}` to collection creation (currently defaults to L2) |
| W1-14 | `apps/research-agent/research_agent/services/extraction.py` | Add `MIN_CONFIDENCE` threshold (default 0.3) filtering for entities/claims |
| W1-15 | `apps/chat-import-bridge/chat_import_bridge/database.py` + `main.py` | Add `close_staging_db()` calling `await engine.dispose()` in lifespan shutdown |
| W1-16 | `apps/research-portal/research_portal/routers/api_proxy.py:166-167` | Replace hardcoded empty returns for claims/sources proxy with actual agent calls |

### W1 verification: `make lint && make test`

---

## WAVE 2 — PERFORMANCE (Indexes, N+1 queries, pools)

| ID | File:Line | Fix |
|----|-----------|-----|
| W2-1 | New migration | Create 9 FK indexes on: `sources(project_id)`, `entities(source_id)`, `claims(source_id, entity_id)`, `reports(project_id)`, `analyses(source_id, project_id)`, `extraction_logs(source_id, project_id)` |
| W2-2 | `apps/research-portal/research_portal/routers/dashboard.py:21-30` | Replace N+1 pattern (projects→sources→claims) with batch repo method using JOINs |
| W2-3 | `apps/research-portal/research_portal/routers/quality.py:22-35` | Replace N+1 pattern (projects→sources→analyses) |
| W2-4 | `apps/research-portal/research_portal/routers/extraction.py:24-35` | Replace N+1 pattern (projects→sources→extraction_logs) |
| W2-5 | `apps/research-portal/research_portal/routers/cleanup.py:21-24`, `dashboard.py:21` | Cap `limit=9999` → `limit=1000` |
| W2-6 | `packages/northstar-db/northstar_db/neo4j_repo.py` (`initialize()`) | Add 4 Cypher indexes + 2 unique constraints |
| W2-7 | `packages/northstar-db/northstar_db/pg_repo.py:43` | Configure pool: `pool_size=20`, `max_overflow=10`, `pool_pre_ping=True`, `pool_recycle=3600` |
| W2-8 | `apps/research-portal/research_portal/routers/api_proxy.py:90-91` | Delegate pagination to agent instead of in-memory slice |
| W2-9 | `packages/northstar-db/northstar_db/neo4j_repo.py:211-222` | Fix `get_project_graph()` unbounded OPTIONAL MATCH |
| W2-10 | `packages/northstar-llm/northstar_llm/cache.py:15` | Add `size_limit=1_000_000_000` to `Cache()` |
| W2-11 | `packages/northstar-db/northstar_db/neo4j_repo.py` (`initialize()`) | Add APOC availability check with clear error message |
| W2-12 | `apps/research-portal/research_portal/routers/dashboard.py` | Replace `sum(len(await db.list_sources(p.id, limit=9999)))` with `COUNT` query |

### W2 verification: `make lint && make test`

---

## WAVE 3 — RELIABILITY (Ops, logging, observability)

| ID | File:Line | Fix |
|----|-----------|-----|
| W3-1 | All 3 `config.py` + new `logging_config.py` per app | Call `structlog.configure()` at startup reading `settings.log_level` |
| W3-2 | Entire `apps/chat-import-bridge/` | Add structlog logging to all routers and services |
| W3-3 | All 3 `main.py` `/health` endpoints | Add PG/Neo4j/SQLite connectivity checks to health responses |
| W3-4 | `Dockerfile` (all 3 stages) | Add `HEALTHCHECK` instruction |
| W3-5 | `scripts/restore.sh` | Offer pre-restore backup option before destroying current DB |
| W3-6 | `scripts/backup.sh` | Add `pg_restore --list` verification after `pg_dump` |
| W3-7 | `systemd/user/phase1-daily-use.service` | Add `ExecStop=docker compose down` |
| W3-8 | `apps/chat-import-bridge/chat_import_bridge/models.py` | Add `updated_at` column to `StagedImport` |
| W3-9 | `sql/seed.sql` | Add `ON CONFLICT DO NOTHING` for idempotent seeding |
| W3-10 | `tests/test_agent_tools.py`, `tests/test_orchestrator.py` | Remove `@pytest.mark.asyncio` from 12 sync test helpers |
| W3-11 | `apps/chat-import-bridge/chat_import_bridge/config.py` | Add `max_import_size`, rate limiting config |

### W3 verification: `make doctor && make lint && make test`

---

## WAVE 4 — POLISH (UX, accessibility, UI)

| ID | File:Line | Fix |
|----|-----------|-----|
| W4-1 | Portal routing | Resolve Jinja2/SPA route collision at `/dashboard`, `/quality`, etc. |
| W4-2 | `spa/src/components/shared/Button.tsx`, `Card.tsx`, all views | Replace hardcoded hex (`bg-[#16213e]`) with CSS variable refs (`var(--color-northstar-*)`) |
| W4-3 | `templates/extraction.html`, `quality.html`, `cleanup.html` | Add `hx-indicator` spinners to HTMX async buttons |
| W4-4 | `templates/graph_viewer.html`, `spa/src/components/graph/GraphViewer.tsx` | Add `aria-label`/`role="img"`/text fallback to vis-network canvas |
| W4-5 | All HTMX templates | Add `aria-live="polite"` wrapper regions for dynamic content updates |
| W4-6 | `templates/base.html`, all HTMX templates | Fix heading hierarchy — add `<h1>` (currently starts with `<h2>`) |
| W4-7 | `templates/base.html` | Change `div.container` → `<main id="main-content" class="container">` |
| W4-8 | `spa/public/` + `vite.config.ts` | Add 512×512 maskable icon for Android |
| W4-9 | `vite.config.ts` Workbox config | Add `navigateFallback` for offline deep-link navigation |
| W4-10 | `spa/src/components/chat/ChatView.tsx` | Add `aria-live="polite"` region for SSE streaming chat |
| W4-11 | `spa/src/components/chat/ThinkingDots.tsx` | Add `role="status" aria-label="AI is thinking..."` |
| W4-12 | `spa/src/components/Sidebar.tsx` | Add `aria-current="page"` to active nav link |
| W4-13 | `spa/src/components/shared/Table.tsx` | Add `aria-busy="true"` during loading, `aria-hidden="true"` on skeleton rows |
| W4-14 | `spa/src/index.css` | Fix muted text contrast: `#8888aa` → `#9696b9` (4.3:1 → 4.5:1) |
| W4-15 | `templates/base.html` | Add `<header>`, `<footer>` landmarks |
| W4-16 | `templates/base.html` | Add `integrity` hashes to CDN scripts |

### W4 verification: `make lint && make test`

---

## Audit Reports Reference

All 13 detailed audit reports in `.opencode/audit/`:

| File | Area | Score |
|------|------|-------|
| `accessibility.md` | Portal accessibility | 46 |
| `api-contract.md` | API contract consistency | 62 |
| `api-test-coverage.md` | Test coverage | 70 |
| `codebase-cartography.md` | Architecture & dependencies | 78 |
| `data-pipeline.md` | Data pipeline integrity | 47 |
| `database-operations.md` | DB schema & migrations | 62 |
| `db-performance.md` | Query performance | 62 |
| `llm-extraction.md` | LLM & extraction pipeline | 62 |
| `ops-reliability.md` | Docker, scripts, logging | 62 |
| `pwa.md` | PWA compliance | 72 |
| `qa-verification.md` | Build/test/lint health | 88 |
| `safety.md` | Security & safety gates | 56 |
| `ui-polish.md` | UI/UX design | 62 |

## Agent Instructions

For each fix:
1. Read the source file at the listed line
2. Apply the exact change described
3. Verify: `make lint`
4. Mark complete in checklist above
5. Proceed to next item in wave

After each wave is complete, run `make test` for full verification.
