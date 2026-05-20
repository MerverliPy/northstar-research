# API Test Coverage Audit

**Date**: 2026-05-20
**Scope**: All 3 services (research-agent, research-portal, chat-import-bridge)
**Total endpoints audited**: 58 (agent: 31, bridge: 8, portal: 19)
**Auditor**: API Test Engineer agent

---

## Summary

| Metric | Value |
|--------|-------|
| Endpoint coverage (any test exists) | ~83% (48/58) |
| Endpoints with happy-path test | 47/58 (81%) |
| Endpoints with error-path test | 36/58 (62%) |
| Endpoints with safety-gate test | 100% of gated endpoints (6/6) |
| Overall health score | **C+ / 70%** |

**Grade rationale**: Core CRUD for agent has broad but shallow coverage. Safety gates are well-tested. Portal chat/conversation endpoints, batch promotion, and API proxy paths are untested or minimally tested. Pagination boundaries, invalid-input 422 responses, and error-state coverage are missing across most list endpoints.

---

## Untested Endpoints

### CRITICAL — No test exists at all

| Service | Endpoint | Method | Router | Severity |
|---------|----------|--------|--------|----------|
| Bridge | `/api/v1/promotion/batch` | POST | promotion.py | **CRITICAL** |
| Portal | `/api/chat/orchestrate` | GET (SSE) | chat.py | **CRITICAL** |
| Portal | `/api/chat/conversations` | GET | chat.py | **HIGH** |
| Portal | `/api/chat/conversations` | POST | chat.py | **HIGH** |
| Portal | `/api/chat/conversations/{conv_id}` | GET | chat.py | **HIGH** |
| Portal | `/api/chat/conversations/{conv_id}` | DELETE | chat.py | **HIGH** |
| Portal | `/api/settings` | GET | main.py | **MEDIUM** |
| Portal | `/{full_path:path}` (SPA fallback) | GET | main.py | **MEDIUM** |
| Portal | `/graph/data/{project_id}` (main.py route) | GET | main.py | **MEDIUM** |

### HIGH — Test exists but only verifies status code, not response shape

| Service | Endpoint | Test file | Issue |
|---------|----------|-----------|-------|
| Agent | POST `/api/v1/search/` | test_agent_api.py | Only tests empty results; no non-empty result shape validation |
| Agent | GET `/api/v1/quality/history` | test_agent_api.py | Only checks status_code=200, no response field assertions |
| Agent | POST `/api/v1/scraping/scrape` (extract=True) | test_scraper_api.py | Only checks status_code=201, does not verify extraction was triggered |
| Agent | POST `/api/v1/extraction/extract` (force=True) | test_agent_api.py | Only checks 200, does not verify response fields (extraction_id, status, message) |
| Portal | GET `/dashboard` | test_portal_api.py | Accepts 307 redirect without verifying redirect target |
| Portal | GET `/extraction` | test_portal_api.py | Only verifies page renders, not content correctness |

---

## Missing Error-Path Tests

| Endpoint | Missing Error Test | Severity |
|----------|-------------------|----------|
| DELETE `/api/v1/entities/{entity_id}` | 404 not found | **HIGH** |
| DELETE `/api/v1/claims/{claim_id}` | 404 not found | **HIGH** |
| DELETE `/api/v1/reports/{report_id}` | 404 not found | **HIGH** |
| POST `/api/v1/quality/score` | 422 invalid/missing source_id | **MEDIUM** |
| POST `/api/v1/extraction/extract` | 422 missing source_id, 422 invalid UUID | **MEDIUM** |
| POST `/api/v1/projects/` | 422 invalid body (missing name) | **MEDIUM** |
| POST `/api/v1/sources/` | 422 invalid body | **MEDIUM** |
| GET `/api/v1/sources/` | 422 missing required project_id | **MEDIUM** |
| GET `/api/v1/reports/` | 422 missing required project_id | **MEDIUM** |
| POST `/api/v1/scraping/scrape` | 422 invalid UUID in project_id | **MEDIUM** |
| POST `/api/v1/promotion/{import_id}` | 403 promotion disabled gate | **HIGH** |
| POST `/api/v1/promotion/batch` | 403 promotion disabled gate | **HIGH** |
| POST `/api/v1/scraping/scrape` | 400 ValueError (scraper error) is tested, but 503 RuntimeError (not enabled) is NOT tested via the direct _scraper=None scenario in test_scraper_api.py (the test exists but only passes because of a side-effect) | **LOW** |
| GET `/api/v1/extraction/queue` | Empty queue (no pending extractions) | **LOW** |
| Portal POST `/extraction/trigger/{source_id}` | 404 source not found | **HIGH** |
| Portal POST `/quality/score/{source_id}` | 404 source not found | **HIGH** |
| Portal POST `/api/v1/extraction/extract` (via proxy) | 503 agent unreachable | **MEDIUM** |

---

## Missing Pagination Boundary Tests

No list endpoint across any service has explicit pagination boundary tests. Every list endpoint has `limit` and `offset` query parameters. None of the following are tested:

| Scenario | Example | Severity |
|----------|---------|----------|
| `limit=1` (lower bound) | `GET /api/v1/projects/?limit=1` | **MEDIUM** |
| `limit=1000` (upper bound) | `GET /api/v1/projects/?limit=1000` | **MEDIUM** |
| `limit=0` (below allowed range) | Should return 422 | **MEDIUM** |
| `limit=1001` (above allowed range) | Should return 422 | **MEDIUM** |
| `offset` beyond total results | `GET /api/v1/projects/?offset=9999` | **LOW** |
| Negative `offset` | Should return 422 | **LOW** |

Affected endpoints: All 12 list endpoints across agent + bridge.

---

## Safety Gate Test Coverage

| Gate | Default | Tests for disabled (403) | Tests for enabled | Severity of gaps |
|------|---------|-------------------------|-------------------|------------------|
| `FORCE_GRAPH_EXTRACTION` | false | ✅ 3 tests across test_agent_api.py + test_safety_gates.py + test_portal_api.py | ✅ force=true request param tested | **NONE** |
| `ENABLE_DESTRUCTIVE_CLEANUP` | false | ✅ 4 tests across test_agent_api.py + test_safety_gates.py + test_portal_api.py | ❌ No end-to-end test with gate enabled | **MEDIUM** |
| `PROMOTION_ENABLED` | false | ✅ test_safety_gates.py TestBridgeSafety (structural) | ❌ No API-level test with gate disabled; bridge test uses `patch("...promotion_enabled", True)` | **HIGH** |

**Note on PROMOTION_ENABLED**: The bridge tests patch `config.settings.promotion_enabled = True` in conftest (line 271). This means the 403 gate path of `POST /api/v1/promotion/{import_id}` is NEVER tested at the API level. The only promotion gate check is a structural test in `test_safety_gates.py` that verifies the bridge doesn't depend on `northstar-db`.

**Note on cleanup execute (enabled)**: No API test exercises `POST /api/v1/cleanup/execute` with `ENABLE_DESTRUCTIVE_CLEANUP=true`. The service has good unit tests for the cleanup logic, but there's no integration flow test.

---

## Mock Pattern Issues

### 1. Module-level `pytestmark` in conftest.py (HIGH)

**File**: `tests/conftest.py`, line 16
```python
pytestmark = pytest.mark.asyncio
```

This applies to ALL functions defined in conftest.py including synchronous helpers like `test_settings()`, fake entity classes, and mock service classes. While `pytestmark` on conftest does NOT propagate to test files, it does affect functions within conftest itself. The `event_loop` fixture at line 20 is correctly session-scoped but would inherit the asyncio marker unnecessarily. This does not cause test failures, but it's a lint-level concern and could cause subtle issues with fixture introspection.

**Fix**: Remove the module-level `pytestmark` from conftest.py. Async fixtures in conftest are already handled by pytest-asyncio's auto-detection.

### 2. `mock_scraper` has no `spec` (MEDIUM)

**File**: `tests/conftest.py`, line 224-238
```python
@pytest.fixture
def mock_scraper():
    scraper = AsyncMock()  # No spec=WebScraper
```

All other mocks use `spec=` (e.g., `AsyncMock(spec=LLMService)`, `AsyncMock(spec=PostgresRepository)`). The scraper mock is the only one without a spec, making it impossible to detect if the real `WebScraper` changes its API.

### 3. `_session` mock uses MagicMock wrapping AsyncMock (MEDIUM)

**File**: `tests/conftest.py`, lines 183-190
```python
mock_result = MagicMock()
mock_result.scalar_one_or_none.return_value = FakeExtractionLog()
mock_session_instance = AsyncMock()
mock_session_instance.execute = AsyncMock(return_value=mock_result)
mock_session_cm = AsyncMock()
mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
mock_session_cm.__aexit__ = AsyncMock(return_value=None)
repo._session = MagicMock(return_value=mock_session_cm)
```

The `_session` is returned via `MagicMock` (sync), but its result is an async context manager (`mock_session_cm`). This works because `_session()` returns a sync mock, and the calling code does `async with self._session() as session:`. The `__aenter__` is correctly AsyncMock. However, using `MagicMock` for `repo._session` prevents catching accidental `await` on `_session()` itself (it should be called WITHOUT await: `self._session()` not `await self._session()`). If the code were ever changed to `await self._session()`, this mock would silently accept it instead of raising.

### 4. Scalar mocks return `scalar_one_or_none` on MagicMock (LOW)

**File**: `tests/conftest.py`, line 184
```python
mock_result.scalar_one_or_none.return_value = FakeExtractionLog()
```

The `mock_result` is a plain `MagicMock`, which auto-creates attributes. If sqlalchemy's `Result` object changes its API (e.g., method renamed to `scalar_one`), this mock will silently accept any attribute name and return the fake value. A stricter `AsyncMock(spec=...)` or a dedicated fake class would catch such breakage.

### 5. `Fake*` classes missing `metadata_` field (LOW)

The `FakeSource`, `FakeEntity`, `FakeClaim` etc. in conftest.py do not define a `metadata` or `metadata_` field. The AGENTS.md states SQLAlchemy models have a `metadata_` mapped column. The schemas may validate this, and the tests don't exercise it. If validation in `*Read.model_validate()` ever requires a non-null metadata field, tests would break.

### 6. Portal app mock uses deprecated `__anext__` pattern (LOW)

**File**: `tests/conftest.py`, lines 283-309 (portal_app)

The portal app fixture patches `research_portal.dependencies` and uses `AsyncMock` for the http_client. The `http_client.request` returns `status_code=403` by default. This works for safety gate tests but means any portal test that needs a different agent response must mutate the mock in the test body (as `test_portal_extraction_when_force_enabled` does). This pattern works but could be improved with more targeted per-test mocking.

---

## Async Test Marker Audit

All test files containing async tests have the correct `pytestmark = pytest.mark.asyncio` marker:

| Test file | Marker location | Correct? |
|-----------|----------------|----------|
| test_agent_api.py | module-level (line 6) | ✅ |
| test_safety_gates.py | module-level (line 8) | ✅ |
| test_bridge_api.py | module-level (line 6) | ✅ |
| test_portal_api.py | module-level (line 6) | ✅ |
| test_extraction_service.py | module-level (line 9) | ✅ |
| test_quality_service.py | module-level (line 8) | ✅ |
| test_promotion_service.py | module-level (line 8) | ✅ |
| test_scraper_api.py | module-level (line 6) | ✅ |
| test_scraper_service.py | module-level (line 9) | ✅ |
| test_agent_tools.py | module-level (line 8) | ✅ |
| test_orchestrator.py | module-level (line 8) | ✅ |
| test_db_pg.py | module-level (line 16) | ✅ |
| test_db_neo4j.py | module-level (line 10) | ✅ |
| test_vector.py | per-class (lines 60, 82) | ✅ |
| test_llm.py | per-class (lines 103, 195, 272, 303, 357) | ✅ |
| conftest.py | module-level (line 16) | ⚠️ See Mock Pattern Issue #1 |
| test_conversation.py | NONE (sync tests) | ✅ |
| test_models.py | NONE (sync tests) | ✅ |

**No missing `@pytest.mark.asyncio` decorators found on async test functions.** The per-class approach in `test_llm.py` and `test_vector.py` is preferred because those files mix sync and async test classes.

---

## Test Class Organization vs AGENTS.md Conventions

AGENTS.md states: *"Test classes grouped by feature: TestForceGraphExtraction, TestDestructiveCleanup, etc."*

| Test file | Class organization | Compliant? |
|-----------|-------------------|------------|
| test_agent_api.py | TestHealth, TestProjectsAPI, TestSourcesAPI, TestEntitiesAPI, TestClaimsAPI, TestReportsAPI, TestExtractionAPI, TestQualityAPI, TestCleanupAPI, TestSearchAPI | ✅ Per-resource |
| test_safety_gates.py | TestForceGraphExtraction, TestDestructiveCleanup, TestBridgeSafety, TestSafetyGateDefaults | ✅ Per-gate |
| test_bridge_api.py | TestHealth, TestImportsAPI, TestExportAPI, TestPromotionAPI | ✅ Per-resource |
| test_portal_api.py | TestHealth, TestDashboard, TestQualityPage, TestCleanupPage, TestExtractionPage, TestGraphPage, TestSafetyGates, TestGraphData | ✅ Per-feature |
| test_scraper_api.py | TestScrapingAPI | ✅ |
| test_agent_tools.py | TestAgentToolExecutor, TestToolDefinitions | ✅ |
| test_orchestrator.py | TestOrchestrator | ✅ |

**No organizational issues found.** Class grouping aligns with the documented convention.

---

## conftest.py Audit

### Fixture Completeness

| Fixture | Purpose | Completeness |
|---------|---------|-------------|
| `event_loop` (session) | Async event loop for tests | ✅ |
| `test_settings` | Sets env vars for safety gates | ✅ (but overwritten per-test by patches) |
| `mock_llm_service` | Mocked LLMService | ✅ Good: uses `spec=LLMService` |
| `mock_embedding_service` | Mocked EmbeddingService | ✅ |
| `mock_db` | Mocked PostgresRepository with fake entities | ✅ Comprehensive: all CRUD methods, session chain |
| `mock_neo4j` | Mocked Neo4jRepository | ✅ |
| `mock_vector_store` | Mocked VectorStore | ✅ |
| `mock_scraper` | Mocked WebScraper | ⚠️ No `spec=` (see Mock Issue #2) |
| `agent_app` | FastAPI app with all mocks patched in | ✅ Uses `patch.multiple` on dependencies |
| `agent_client` | httpx.AsyncClient for agent | ✅ |
| `bridge_app` | Bridge FastAPI app | ✅ |
| `bridge_client` | httpx.AsyncClient for bridge | ✅ |
| `portal_app` | Portal FastAPI app | ✅ |
| `portal_client` | httpx.AsyncClient for portal | ✅ |

### Fake Entity Factory Patterns

The `mock_db` fixture creates inner `Fake*` classes (FakeProject, FakeSource, FakeEntity, FakeClaim, FakeReport, FakeAnalysis, FakeExtractionLog). These are simple data classes with fixed UUIDs - adequate for testing read operations but:

- All fakes return the same ID (`test_project_id`, `test_source_id`, etc.)
- No factory function to generate entities with custom attributes
- Missing `project_id` on FakeEntity, FakeClaim (these have `project_id` in the real models, per the extraction service which passes `project_id` to `bulk_create_entities`)

### ASGITransport + AsyncClient Setup

All client fixtures follow the same pattern:
```python
transport = ASGITransport(app=app)
yield AsyncClient(transport=transport, base_url="http://test")
```

The `lifespan` is always patched with `MagicMock()` to prevent real service initialization:
```python
with patch("research_agent.main.lifespan", MagicMock()):
```

This is correct and consistent across all three client fixtures.

**Minor issue**: The `base_url="http://test"` is a bare string without a trailing slash. Since all test URLs use `/api/v1/...` with a leading slash, this is fine - httpx resolves it correctly.

---

## Portal API Proxy Test Coverage

The portal's `api_proxy.py` is a complex catch-all handler (`/{path:path}` with `methods=[GET, POST, PUT, DELETE]`) that contains special-case handling for 6 sub-paths. Each sub-path has multiple HTTP methods with different logic:

| Sub-path | Methods | Tested? |
|----------|---------|---------|
| `projects` | GET | ✅ Via safety gate proxy pass-through |
| `projects` | POST | ❌ Not tested |
| `projects` | PUT | ❌ Returns 501 - not tested |
| `projects` | DELETE | ❌ Returns 501 - not tested |
| `reports` | GET | ❌ Not tested (with project_id filter) |
| `reports` | POST/PUT/DELETE | ❌ Returns 501 - not tested |
| `sources` | GET | ❌ Returns empty paginated response - not tested for response shape |
| `entities` | GET | ❌ Not tested (makes agent call to `/knowledge/entities` which may be wrong) |
| `claims` | GET | ❌ Returns empty paginated response - not tested |
| `graph/data/{project_id}` | GET | ✅ Via test_portal_api.py TestGraphData |
| General proxy | GET/POST/PUT/DELETE | ✅ Safety gate tests use this path |

**Note**: The `entities` proxy calls `{agent_base}/knowledge/entities` which does NOT correspond to any endpoint in the agent's routers (the agent has `/api/v1/entities/`, NOT `/api/v1/knowledge/entities/`). This appears to be a **bug** in the proxy. No test catches this because no test exercises the entities proxy path.

---

## Contract Risks

### 1. Portal proxy entities endpoint calls wrong agent URL (HIGH)

**File**: `apps/research-portal/research_portal/routers/api_proxy.py`, line 143
```python
resp = await client.get(f"{agent_base}/knowledge/entities", ...)
```

The agent exposes entities at `/api/v1/entities/`, not `/api/v1/knowledge/entities/`. This means portal users requesting entities via the API proxy will receive empty results (the proxy catches exceptions and returns `paginated_response([], 0, limit, offset)`).

### 2. Portal `transform_project` maps `name` → `topic` (MEDIUM)

**File**: `apps/research-portal/research_portal/routers/api_proxy.py`, line 22
```python
"name": agent_project.get("topic", ""),
```

In the agent's router, `POST /api/v1/projects/` accepts `{"name": "...", "description": "..."}` but the portal proxy reads the `"topic"` field (not `"name"`) from the agent's response. If the agent returns a `ProjectRead` schema (which has a `name` field, not `topic`), the portal will display an empty project name. This mismatch is untested.

### 3. Portal proxy `transform_report` maps `id` fallback to `report_id` (MEDIUM)

**File**: `apps/research-portal/research_portal/routers/api_proxy.py`, line 33
```python
"id": str(agent_report.get("id", agent_report.get("report_id", ""))),
```

The agent's `ReportRead` schema has an `id` field. The fallback to `report_id` suggests a legacy compatibility path that may no longer be needed.

---

## Quick Wins (low effort, high impact)

| # | Win | Effort | Impact |
|---|-----|--------|--------|
| 1 | Add `delete_entity_not_found`, `delete_claim_not_found`, `delete_report_not_found` tests to test_agent_api.py | 30 min | Closes 3 HIGH-severity gaps |
| 2 | Add `POST /api/v1/promotion/batch` test to test_bridge_api.py | 15 min | Closes the CRITICAL batch promotion gap |
| 3 | Add promotion 403 gate test (PROMOTION_ENABLED=false) to test_bridge_api.py | 15 min | Closes HIGH safety gap |
| 4 | Add 422 tests for invalid payloads on all POST endpoints | 45 min | Catches schema drift early |
| 5 | Add pagination boundary tests (limit=1, limit=1000) for 2 representative list endpoints | 30 min | Validates Query param constraints |

## Structural Issues (higher effort)

| # | Issue | Effort | Impact |
|---|-------|--------|--------|
| 1 | Portal chat API endpoints have zero coverage (5 endpoints, including SSE) | 2-3 hours | Major blind spot - entire chat feature |
| 2 | Portal API proxy paths have minimal coverage; entities proxy has probable bug | 2-3 hours | High risk of broken proxying |
| 3 | Fix `pytestmark` in conftest.py and add `spec=` to mock_scraper | 15 min | Cleanup, prevents future breakage |
| 4 | Add Fake entity factories with parameterized IDs instead of single hardcoded UUIDs | 1 hour | Enables richer test scenarios |
| 5 | Add quality/score endpoint error tests (missing source_id, LLM failure propagation) | 1 hour | Ensures error handling works in API layer |
| 6 | Portal page tests only check HTML rendering, not content correctness | 1-2 hours | Pages could render broken without tests catching it |

---

## Commands Run

```bash
# File discovery and analysis (read-only)
grep -rn "pytest.mark.asyncio\|pytestmark" tests/ --include='*.py'
rd tests/conftest.py
rd tests/test_agent_api.py
rd tests/test_safety_gates.py
rd tests/test_bridge_api.py
rd tests/test_portal_api.py
# ... (all router and test files read)

# No build/test commands run (read-only audit)
```

To reproduce the analysis:
```bash
make test  # Run all tests to see current pass/fail state
make lint  # Check for code quality issues
```

---

## Remaining Test Gaps

1. **No performance/load tests** — No tests measure response times or concurrent request handling.
2. **No end-to-end extraction flow test** — Extraction is tested at the service layer and at the gate layer, but no test verifies the full async background extraction flow (trigger → status polling → completion).
3. **No HTTPX timeout/network error tests for the API layer** — Only service-layer tools (promotion, orchestrator) test network errors. The API routers themselves don't have tests for downstream service failures.
4. **No SSE content validation** — The single SSE endpoint (`/api/chat/orchestrate`) is completely untested.
5. **No OpenAPI schema validation test** — No test verifies that the generated OpenAPI schema matches the actual route handlers.
6. **No CORS header test** — The CORS middleware is configured but never tested.
7. **No auth/security tests** — All endpoints are public; no auth bypass or authorization escalation tests exist.
