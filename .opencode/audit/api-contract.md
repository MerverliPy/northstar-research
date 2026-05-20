# API Contract Safety Audit

**Date:** 2026-05-20
**Auditor:** Automated deep-audit pass
**Scope:** Full-stack contract review — Agent routers, Portal proxy, Models/schemas, Chat Import Bridge, Safety gates
**Overall Health Score:** **62/100** (moderate risk — 2 CRITICAL proxy bugs render portal unusable for projects/reports)

---

## Summary

The core Research Agent API is well-structured with consistent CRUD patterns, validated query parameters, correct status codes, and proper safety-gate enforcement. The Pydantic schema triple pattern is faithfully followed. However, the **Portal API proxy layer has two critical bugs** that cause it to return empty/incorrect data for projects and reports, and **several CRUD routers are missing UPDATE endpoints** despite having the schemas and repository methods available. The Chat Import Bridge is clean but has response schemas defined locally rather than in the shared `northstar-models` package.

---

## Overall Findings Matrix

| # | Severity | Category | Location | Description |
|---|----------|----------|----------|-------------|
| C1 | **CRITICAL** | Proxy mismatch | `api_proxy.py:19-27` | `transform_project` reads `topic` field that does not exist in `ProjectRead` — returns empty `name`/`description` |
| C2 | **CRITICAL** | Proxy mismatch | `api_proxy.py:30-40` | `transform_report` reads `content`/`report_type`/`type` fields not in `ReportRead` — returns empty content |
| H1 | **HIGH** | Schema mismatch | `search.py:28-34` | `SearchResult` schema declares `source_id: uuid.UUID \| None` but actual vector-store result is `str \| None` |
| H2 | **HIGH** | Missing endpoints | `sources.py`, `claims.py`, `entities.py`, `reports.py` | PUT update routes missing despite `*Update` schemas and repo methods existing |
| H3 | **HIGH** | Proxy mismatch | `api_proxy.py:141-142` | Entities proxy calls `/api/v1/knowledge/entities` — endpoint does not exist on Agent (should be `/api/v1/entities`) |
| M1 | **MEDIUM** | Safety gate | `extraction.py:28` | `force: true` request body bypasses `FORCE_GRAPH_EXTRACTION` gate (per-request override) |
| M2 | **MEDIUM** | Proxy stub | `api_proxy.py:166-167` | Claims proxy always returns empty list (hardcoded `paginated_response([], 0, limit, offset)`) |
| M3 | **MEDIUM** | Proxy stub | `api_proxy.py:136-137` | Sources proxy always returns empty list (hardcoded `paginated_response([], 0, limit, offset)`) |
| M4 | **MEDIUM** | Docs mismatch | `API_ENDPOINTS.md:32,41` | Documents PUT for entities & claims but routers don't implement them |
| M5 | **MEDIUM** | Undocumented route | `extraction.py:73-84` | `/api/v1/extraction/queue` endpoint not in `API_ENDPOINTS.md` |
| L1 | **LOW** | Schema location | `chat-import-bridge/routers/*` | Bridge response schemas are local Pydantic models, not in shared `northstar-models` |
| L2 | **LOW** | Offset validation | Agent routers | `offset` parameter lacks `ge=0` validator (only Chat Bridge validates it) |
| L3 | **LOW** | Trailing slash | Agent routers | All list routes use `@router.get("/")` producing trailing-slash paths (e.g. `/api/v1/projects/`) |
| L4 | **LOW** | Score validation | `schemas.py:256` | `QualityScoreResponse.score` has no `Field(ge=0.0, le=1.0)` constraint |
| L5 | **LOW** | Fallback field | `api_proxy.py:32` | `transform_report` falls back to `report_id` — field does not exist in `ReportRead` |
| L6 | **LOW** | Full-content proxy | `api_proxy.py:179-202` | Fall-through proxy forwards all response headers from agent to client (potential info leak) |

---

## 1. Contract Violation Table

### 1.1 Portal Proxy Transformation Bugs

#### C1: `transform_project` — wrong field names
**File:** `apps/research-portal/research_portal/routers/api_proxy.py:19-27`
```python
def transform_project(agent_project: dict) -> dict:
    return {
        "id": str(agent_project.get("id", "")),
        "name": agent_project.get("topic", ""),         # BUG: ProjectRead has "name" not "topic"
        "description": agent_project.get("topic", "")[:200],  # BUG: should be "description"
        ...
    }
```
**Impact:** Portal project listing always shows empty `name` and `description` for all projects.
**Fix:** Change `topic` → `name` on line 22, `topic` → `description` on line 23.

#### C2: `transform_report` — wrong field names
**File:** `apps/research-portal/research_portal/routers/api_proxy.py:30-40`
```python
def transform_report(agent_report: dict) -> dict:
    return {
        ...
        "content": agent_report.get("content", agent_report.get("summary", "")),
        "report_type": agent_report.get("report_type", agent_report.get("type", "summary")),
        ...
    }
```
**Impact:** Portal report list always shows empty `content` since `ReportRead` has `summary` and `report_data`, not `content`/`report_type`/`type`.
**Fix:** Map `content` → `summary` (or `report_data`), remove references to nonexistent fields.

### 1.2 Proxy Endpoint URL Mismatches

#### H3: Entities endpoint URL wrong
**File:** `api_proxy.py:142`
```python
resp = await client.get(f"{agent_base}/knowledge/entities", ...)
```
Agent route is `/api/v1/entities` (router prefix `/entities`). No `/knowledge/entities` endpoint exists.
**Impact:** Portal entity listing always returns empty data.
**Fix:** Change to `{agent_base}/entities`.

#### M2/M3: Sources and Claims proxy stubs
**File:** `api_proxy.py:136-137` (sources), `api_proxy.py:166-167` (claims)
Both return hardcoded empty lists instead of proxying to agent:
```python
if path.rstrip("/") == "sources":
    return paginated_response([], 0, limit, offset)
# ...
if path.rstrip("/") == "claims":
    return paginated_response([], 0, limit, offset)
```
**Impact:** Portal source and claim listing never returns data.
**Fix:** Implement proxy logic or remove stubs and let fall-through proxy handle them.

### 1.3 SearchResult Schema vs Runtime Type

#### H1: `source_id` type mismatch
**File:** `apps/research-agent/research_agent/routers/search.py:28-34`
```python
SearchResultSchema(
    content=r.text,
    score=r.score,
    metadata=r.metadata,
    source_id=r.source_id,  # r.source_id is str | None (vector_store schemas.py:18)
)
```
Schema declares `source_id: uuid.UUID | None = None` (`schemas.py:284`) but vector store returns `str | None`.
**Impact:** Pydantic may silently coerce or validate-fail depending on string format. Type-unsafe.
**Fix:** Either change `SearchResult.source_id` to `str | None` or convert `r.source_id` to UUID.

---

## 2. Schema Compliance Table

| Entity | Create | Read | Read `from_attributes` | Update | Update Router? | Metadata naming |
|--------|--------|------|----------------------|--------|----------------|-----------------|
| Project | ✅ | ✅ | ✅ `True` | ✅ | ✅ PUT | ✅ `metadata` schema / `metadata_` ORM |
| Source | ✅ | ✅ | ✅ `True` | ✅ | ❌ No PUT | ✅ Repo handles mapping |
| Entity | ✅ | ✅ | ✅ `True` | ✅ | ❌ No PUT | ✅ Repo handles mapping |
| Claim | ✅ | ✅ | ✅ `True` | ✅ | ❌ No PUT | ✅ Repo handles mapping |
| Report | ✅ | ✅ | ✅ `True` | ✅ | ❌ No PUT | ✅ Repo handles mapping |
| Analysis | ✅ (no router) | ✅ | ✅ `True` | ✅ (no router) | N/A | ✅ |
| ExtractionLog | ✅ | ✅ | ✅ `True` | ✅ | N/A (status only) | ✅ |

**Schema triple compliance:** All entities have Create/Read/Update triple. `from_attributes = True` present on all Read models. Field validators (`ge=0.0, le=1.0`) present on all `confidence` and `quality_score` fields.

**Exception:** `QualityScoreResponse.score` (line 256) has no `Field(ge=0.0, le=1.0)` constraint.

### Metadata Column Audit
SQLAlchemy column: `metadata_` mapped to DB column `"metadata"` (JSON, nullable) — correct.
Pydantic field: `metadata` — correct.
Repository creates: `metadata_=data.metadata` — correct, all 7 create methods verified.
Repository updates: `update_dict["metadata_"] = update_dict.pop("metadata")` — correct, all 6 update methods verified.

---

## 3. Proxy Transformation Audit

### 3.1 Endpoint mapping table

| Agent Path | Portal Path | Method | Status |
|------------|-------------|--------|--------|
| `/api/v1/projects/` | `/api/v1/projects` | GET | ⚠️ Transform returns empty fields (C1) |
| `/api/v1/projects/` | `/api/v1/projects` | POST | ⚠️ Only maps `name` from body |
| `/api/v1/projects/{id}` | — | PUT | ❌ 501 "Update not supported" |
| `/api/v1/projects/{id}` | — | DELETE | ❌ 501 "Delete not supported" |
| `/api/v1/reports/` | `/api/v1/reports` | GET | ⚠️ Transform returns empty fields (C2) |
| `/api/v1/reports/` | — | POST/PUT/DELETE | ❌ 501 |
| `/api/v1/sources/` | `/api/v1/sources` | ALL | ❌ Always empty (M3) |
| `/api/v1/entities/` | — | GET | ❌ Wrong URL `/knowledge/entities` (H3) |
| `/api/v1/claims/` | `/api/v1/claims` | ALL | ❌ Always empty (M2) |
| `/api/v1/search/` | fall-through | POST | ✅ Pass-through |
| `/api/v1/quality/score` | fall-through | POST | ✅ Pass-through |
| `/api/v1/extraction/extract` | fall-through | POST | ✅ Pass-through |
| `/graph/data/{id}` | `/api/v1/graph/data/{id}` | GET | ✅ Direct Neo4j query |
| `*` | `/api/v1/{path}` | ALL | ✅ Generic pass-through |

### 3.2 Proxy header handling
**File:** `api_proxy.py:184-189`
Whitelist: `accept`, `accept-encoding`, `user-agent` — ✅ per ARCHITECTURE.md spec.
For POST/PUT: adds `content-type` from request — ✅.

### 3.3 Error handling
- Agent unreachable → `503 {"detail": "Research agent unavailable"}` ✅
- Proxied 4xx/5xx pass through with original status ✅
- Proxy exceptions logged as `warning` ✅

**Concern L6:** Fall-through proxy at line 198-202 forwards all agent response headers to client. This could leak internal headers like `server`, `x-*` headers from the agent. Consider stripping non-whitelisted response headers.

---

## 4. Safety Gate Enforcement Audit

### 4.1 `FORCE_GRAPH_EXTRACTION` (Agent)

| Endpoint | Check | Correct? |
|----------|-------|----------|
| `POST /api/v1/extraction/extract` | `extraction.py:28` | ⚠️ `force: true` body param bypasses gate |
| `POST /extraction/trigger/{id}` (Portal) | `extraction.py:51` | ✅ Checks `settings.force_graph_extraction` |

**Issue M1:** Agent extraction endpoint allows per-request `force` field to bypass the environment gate. The portal extraction trigger also sets `"force": true` in its agent call, meaning portal bypasses agent gate too. This is partially intentional (per ARCHITECTURE.md: "Set force=true or FORCE_GRAPH_EXTRACTION=true") but creates a dual-gate situation where the portal checks its own flag but then sends `force: true` anyway.

### 4.2 `ENABLE_DESTRUCTIVE_CLEANUP`

| Endpoint | Check | Correct? |
|----------|-------|----------|
| `POST /api/v1/cleanup/execute` (Agent) | `cleanup.py:51` | ✅ Returns 403 if disabled |
| `POST /cleanup/execute` (Portal) | `cleanup.py:52` | ✅ Double-checks before forwarding |

### 4.3 `PROMOTION_ENABLED` (Chat Bridge)

| Endpoint | Check | Correct? |
|----------|-------|----------|
| `POST /api/v1/promotion/{id}` | `promotion.py:36` | ✅ Returns 403 if disabled |
| `POST /api/v1/promotion/batch` | `promotion.py:59` | ✅ Returns 403 if disabled |

**Summary:** All three safety gates function correctly at the enforcement level. The `force` body parameter on extraction adds a per-request override path but is architecturally documented.

---

## 5. Chat Import Bridge API Audit

### 5.1 Endpoint consistency

| Endpoint | Prefix | Limiter | Status codes | Delete |
|----------|--------|---------|-------------|--------|
| `POST /api/v1/imports/paste` | self-contained in router | N/A | 201 ✅ | N/A |
| `GET /api/v1/imports/` | self-contained | `limit: 1-500, offset: ≥0` ✅ | — | — |
| `GET /api/v1/imports/{id}` | self-contained | N/A | 404 ✅ | — |
| `DELETE /api/v1/imports/{id}` | self-contained | N/A | 204 ✅ | ✅ |
| `GET /api/v1/export/{id}/markdown` | self-contained | N/A | 404 ✅ | — |
| `POST /api/v1/promotion/{id}` | self-contained | N/A | 403/404 ✅ | — |
| `POST /api/v1/promotion/batch` | self-contained | N/A | 403 ✅ | — |

All paths use `/api/v1/` in their own router prefixes and are mounted without additional prefix in main.py — ✅ consistent.

### 5.2 Response schema location (L1)
Chat Bridge response schemas (`PasteImportResponse`, `StagedImportResponse`, `PromoteResponse`, `BatchPromoteResponse`) are defined locally in router files. They are not in the shared `northstar-models` package. This creates fragmentation risk if the bridge is consumed by other services.

### 5.3 `offset` validation (L2)
Chat Bridge validates `offset=Query(0, ge=0)` (imports.py:46). Agent routers do not validate `offset` range, only default it to `0`.

---

## 6. Status Code Correctness

| Pattern | Expected | Actual | Verdict |
|---------|----------|--------|---------|
| Create resource | 201 | 201 (all POST routes) | ✅ |
| Get resource | 200 | 200 (default) | ✅ |
| Update resource | 200 | 200 (projects.py) | ✅ |
| Delete resource | 204 | 204 (all DELETE routes) | ✅ |
| Not found | 404 | 404 (all get/delete) | ✅ |
| Forbidden (gate) | 403 | 403 (all gates) | ✅ |
| Validation error | 422 | 422 (Pydantic/FastAPI default) | ✅ |
| Bad request | 400 | 400 (scraping.py:32) | ✅ |
| Service unavailable | 503 | 503 (scraping.py:33, proxy.py:203-204) | ✅ |
| Not implemented | 501 | 501 (proxy.py:108,111,134) | ✅ |

**All status codes are correct and consistent.**

---

## 7. Error Response Patterns

| Route type | Error pattern | Consistency |
|------------|---------------|-------------|
| Resource not found | `HTTPException(status_code=404, detail="{Type} not found")` | ✅ Uniform across all routers |
| Gate disabled | `HTTPException(status_code=403, detail="... Set FLAG=true ...")` | ✅ Descriptive messages |
| Scraper ValueError | `HTTPException(status_code=400, detail=str(exc))` | ✅ |
| Scraper RuntimeError | `HTTPException(status_code=503, detail=str(exc))` | ✅ |
| Proxy agent unreachable | `JSONResponse({"detail": "Research agent unavailable"}, status_code=503)` | ✅ |
| Service init failure | `HTTPException(status_code=503, detail="... not enabled ...")` | ✅ (scraper dependency) |

---

## 8. Quick Wins (30 min or less each)

1. **Fix `transform_project` (C1):** Change `topic` → `name`, `topic` → `description` in `api_proxy.py:22-23` — 2 lines
2. **Fix `transform_report` (C2):** Remove `content`/`report_type`/`type` fallbacks, use `summary`/`report_data` — ~5 lines
3. **Fix entities proxy URL (H3):** Change `/knowledge/entities` → `/entities` on line 142 — 1 line
4. **Implement claims/sources proxy stubs (M2/M3):** Replace hardcoded empty returns with `_agent_get` calls — ~10 lines
5. **Add `Field(ge=0.0, le=1.0)` to `QualityScoreResponse.score` (L4):** 1 line in schemas.py
6. **Add `offset: int = Query(0, ge=0)` to all agent list endpoints (L2):** 10 routers × 1 line

---

## 9. Structural Issues (need design discussion)

### SI-1: Missing UPDATE routes (H2)
**Problem:** `SourceUpdate`, `EntityUpdate`, `ClaimUpdate`, `ReportUpdate` schemas exist and repository `update_*` methods exist, but no routers expose PUT/PATCH endpoints for sources, claims, entities, or reports. Only projects has PUT.

**Options:**
1. Implement PUT routes following the project pattern
2. Remove the unused schemas if update is intentionally not exposed
3. Document it as "immutable after creation" if that is the intent

### SI-2: Portal proxy dual-layer architecture
**Problem:** The Portal implements both specific path handlers (`if path.rstrip("/") == "projects"`) and a generic fall-through proxy. This creates a maintenance burden where adding a new agent route may require portal changes. The specific handlers also transform response shapes inconsistently (some return paginated, some don't).

**Recommendation:** Either:
- Make ALL paths use the generic fall-through and handle pagination uniformly
- Or explicitly enumerate every handled path and reject unknown ones

### SI-3: SearchResult `source_id` type (H1)
**Problem:** Vector store returns `source_id` as `str` but the shared `SearchResult` schema declares it as `uuid.UUID`. This is a fundamental type system conflict between the vector layer (string identifiers) and the relational layer (UUID identifiers).

**Recommendation:** Change `SearchResult.source_id` to `str | None` or add explicit conversion layer in the search router.

### SI-4: Schema location for Chat Bridge (L1)
**Problem:** Chat Bridge defines response schemas locally in router files rather than in the shared `northstar-models` package. If another service needs to consume bridge APIs, schema duplication is inevitable.

**Recommendation:** Move bridge response schemas to `northstar_models/schemas.py` or create a dedicated `northstar_models/bridge_schemas.py`.

### SI-5: API documentation drift (M4)
**Problem:** `API_ENDPOINTS.md` documents PUT routes for entities and claims that don't exist in code. Also missing documentation for `/api/v1/extraction/queue` and `/api/v1/scraping/scrape`.

**Recommendation:** Regenerate or manually sync `API_ENDPOINTS.md` with current router state.

---

## 10. Files Reviewed

| File | Lines | Issues Found |
|------|-------|-------------|
| `apps/research-agent/research_agent/routers/projects.py` | 62 | None |
| `apps/research-agent/research_agent/routers/sources.py` | 51 | Missing PUT |
| `apps/research-agent/research_agent/routers/entities.py` | 54 | Missing PUT |
| `apps/research-agent/research_agent/routers/claims.py` | 54 | Missing PUT |
| `apps/research-agent/research_agent/routers/reports.py` | 51 | Missing PUT |
| `apps/research-agent/research_agent/routers/extraction.py` | 84 | M1 (force bypass), M5 (undocumented) |
| `apps/research-agent/research_agent/routers/cleanup.py` | 91 | None |
| `apps/research-agent/research_agent/routers/search.py` | 35 | H1 (type mismatch) |
| `apps/research-agent/research_agent/routers/quality.py` | 44 | None |
| `apps/research-agent/research_agent/routers/scraping.py` | 70 | None |
| `apps/research-agent/research_agent/main.py` | 52 | None |
| `apps/research-agent/research_agent/config.py` | 29 | None |
| `apps/research-agent/research_agent/dependencies.py` | 129 | None |
| `apps/research-agent/research_agent/services/extraction.py` | 150 | None |
| `apps/research-portal/research_portal/routers/api_proxy.py` | 204 | C1, C2, H3, M2, M3, L5, L6 |
| `apps/research-portal/research_portal/routers/extraction.py` | 71 | None (gate enforced) |
| `apps/research-portal/research_portal/routers/cleanup.py` | 66 | None (gate enforced) |
| `apps/research-portal/research_portal/routers/quality.py` | 66 | None |
| `apps/research-portal/research_portal/routers/visual.py` | 64 | None |
| `apps/research-portal/research_portal/main.py` | 123 | None |
| `apps/research-portal/research_portal/config.py` | 25 | None |
| `apps/chat-import-bridge/chat_import_bridge/routers/imports.py` | 90 | L1 (local schemas) |
| `apps/chat-import-bridge/chat_import_bridge/routers/promotion.py` | 67 | L1 (local schemas) |
| `apps/chat-import-bridge/chat_import_bridge/routers/export.py` | 20 | None |
| `apps/chat-import-bridge/chat_import_bridge/main.py` | 38 | None |
| `apps/chat-import-bridge/chat_import_bridge/config.py` | 15 | None |
| `packages/northstar-models/northstar_models/schemas.py` | 327 | L4 (missing constraint) |
| `packages/northstar-models/northstar_models/models.py` | 118 | None |
| `packages/northstar-models/northstar_models/base.py` | 32 | None |
| `packages/northstar-models/northstar_models/enums.py` | 42 | None |
| `packages/northstar-vector/northstar_vector/schemas.py` | 25 | H1 (type source) |
| `packages/northstar-db/northstar_db/pg_repo.py` | 567 | None (metadata mapping correct) |
| `docs/API_ENDPOINTS.md` | 112 | M4, M5 |

**Total:** 33 files, ~2,727 lines reviewed.

---

## 11. Recommended Follow-Up Tests

1. **Unit test `transform_project`** with actual `ProjectRead` dict to catch field name mismatch
2. **Unit test `transform_report`** with actual `ReportRead` dict
3. **Integration test portal proxy** against a running agent to verify all passthrough paths
4. **Pydantic validation test** for `SearchResult` with string `source_id` to verify coercion behavior
5. **Contract test** for PUT endpoints on sources/entities/claims/reports
6. **Gate enforcement test** verifying 403 on extraction/cleanup when flags are disabled
7. **API docs regeneration test** to catch documentation drift
