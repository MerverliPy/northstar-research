# AUDIT FIX CONTRACT — Northstar Research

**Generated:** deep audit of all 3 services, 4 packages, scripts, tools, tests, configs.
**96 issues → 28 task groups.** Execute top-to-bottom. Mark `[x]` when done.

---

## BAND 1 — IMMEDIATE (SECURITY + CORRECTNESS)

### [x] AF-001 — Remove hardcoded "northstar" password from Neo4j repo default arg
- **Severity:** CRITICAL
- **Files:**
  - `packages/northstar-db/northstar_db/neo4j_repo.py:28`
- **Fix:** Change `password: str = "northstar"` → `password: str = ""` (or remove default entirely).
  Update callers that relied on the default (`research_agent/dependencies.py`, `research_portal/dependencies.py`) to always pass `password` explicitly from settings.
- **Verify:** `rg "password.*northstar" packages/northstar-db/` returns 0 results.

### [x] AF-002 — Fix portal agent proxy: add /api/v1 prefix to all agent URLs
- **Severity:** CRITICAL
- **Files:**
  - `apps/research-portal/research_portal/main.py:170` — `agent_base` construction
  - `apps/research-portal/research_portal/main.py:179,190,212,220,237,276` — URL builders
- **Fix:** Change line ~170 to `agent_base = f"{settings.research_agent_url.rstrip('/')}/api/v1"`. Remove the `/api/v1/` prefix from individual URL paths. Also fix line 190 `/research` → it doesn't exist; should use a valid agent endpoint.
- **Verify:** `grep -n '"projects"' research_portal/main.py` should show the correct path pattern. Start portal, check dashboard loads data.

### [x] AF-003 — Fix path traversal in SPA file serving
- **Severity:** CRITICAL
- **Files:**
  - `apps/research-portal/research_portal/main.py:320-322`
- **Fix:** After constructing `file_path = STATIC_DIR / full_path`, add:
  ```python
  file_path = file_path.resolve()
  if not str(file_path).startswith(str(STATIC_DIR.resolve())):
      raise HTTPException(status_code=404)
  ```
- **Verify:** `curl -s http://localhost:3010/..%2f..%2f..%2f..%2fetc/passwd` returns 404.

### [x] AF-004 — Remove wildcard CORS on SSE chat endpoint
- **Severity:** CRITICAL
- **Files:**
  - `apps/research-portal/research_portal/routers/chat.py:97`
- **Fix:** Delete the `"Access-Control-Allow-Origin": "*",` line (97). The CORS middleware in `main.py` already handles it.
- **Verify:** `rg "Access-Control-Allow-Origin.*\*" apps/research-portal/` returns 0 results.

### [x] AF-005 — Fix LLMResponseCache key: include system_prompt, temperature, max_tokens
- **Severity:** CRITICAL (cache poisoning)
- **Files:**
  - `packages/northstar-llm/northstar_llm/cache.py:18-20` — `_key()` method
- **Fix:** Change `_key(prompt, model)` → `_key(prompt, model, system_prompt, temperature, max_tokens)`. Hash `f"{prompt}|||{model}|||{system_prompt or ''}|||{temperature}|||{max_tokens}"`.
  Update callers in `service.py:47` and `service.py:62` to pass the new args.
- **Verify:** Run `tests/test_llm.py` — tests should pass after updating expected keys.

### [x] AF-006 — Fix VectorStore.health(): replace heartbeat() with real liveness check
- **Severity:** CRITICAL
- **Files:**
  - `packages/northstar-vector/northstar_vector/client.py:332`
- **Fix:** Replace `self._client.heartbeat()` with `len(self._client.list_collections())` or `self._client.get_or_create_collection("__health__")` then `self._client.delete_collection("__health__")`.
- **Verify:** `make test tests/test_vector.py` — the health check test should use the real method, not mock `heartbeat`.

### [x] AF-007 — Add VectorStore.close() and close it in dependencies.shutdown
- **Severity:** CRITICAL (resource leak on every restart)
- **Files:**
  - `packages/northstar-vector/northstar_vector/client.py` — add `async def close(self)` method
  - `apps/research-agent/research_agent/dependencies.py:70-82` — add `_vector_store.close()` call
- **Fix:** In client.py, add `async def close(self): ...` (at minimum `self._client = None`). In dependencies.py `close_services()`, add:
  ```python
  if _vector_store is not None:
      await _vector_store.close()
  ```
- **Verify:** `rg "_vector_store" dependencies.py` shows the close call.

### [x] AF-008 — Fix SearchResult.source_id type mismatch (vector vs northstar-models)
- **Severity:** CRITICAL
- **Files:**
  - `packages/northstar-models/northstar_models/schemas.py:269`
  - `packages/northstar-vector/northstar_vector/schemas.py:18`
- **Fix:** Change northstar-models `SearchResult.source_id` from `uuid.UUID` → `uuid.UUID | None = None`. In vector schemas, change `str | None = None` → `str | None = None` (keep but update `dict`→`dict[str, Any]` on metadata).
- **Verify:** `make test tests/test_vector.py tests/test_agent_api.py`

### [x] AF-009 — Fix doctor.sh: use underscores not hyphens for import checks
- **Severity:** CRITICAL
- **Files:**
  - `scripts/doctor.sh:62`
- **Fix:** Change loop from `northstar-db northstar-llm northstar-models northstar-vector` → `northstar_db northstar_llm northstar_models northstar_vector`.
- **Verify:** `bash scripts/doctor.sh` — package import section passes.

### [x] AF-010 — Add missing updated_at columns in migration (4 tables)
- **Severity:** CRITICAL
- **Files:**
  - `apps/research-agent/migrations/versions/001_initial_schema.py:52-68,69-89,99,106-149`
- **Fix:** Add `sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)` after each `created_at` column in entities (line 62), claims (line 79), analyses (line 116), extraction_logs (line 138).
- **Verify:** `rg "updated_at" migrations/versions/001_initial_schema.py` shows 7 matches (one per table).

### [x] AF-011 — Add ExtractionLogCreate and ExtractionLogUpdate schemas
- **Severity:** HIGH (schema triple violation)
- **Files:**
  - `packages/northstar-models/northstar_models/schemas.py` — add after `ExtractionLogRead`
  - `packages/northstar-models/northstar_models/__init__.py` — export them
- **Fix:** Create the two schemas:
  ```python
  class ExtractionLogCreate(BaseModel):
      source_id: uuid.UUID
      project_id: uuid.UUID
      status: ExtractionStatus = ExtractionStatus.PENDING
      entities_found: int = 0
      metadata: Optional[dict[str, Any]] = None

  class ExtractionLogUpdate(BaseModel):
      status: Optional[ExtractionStatus] = None
      entities_found: Optional[int] = None
      error_message: Optional[str] = None
      metadata: Optional[dict[str, Any]] = None
  ```
- **Verify:** `rg "ExtractionLogCreate" northstar_models/__init__.py` returns a hit.

### [x] AF-012 — Fix portal proxy: unsilence swallowed exceptions
- **Severity:** CRITICAL
- **Files:**
  - `apps/research-portal/research_portal/main.py:153-155,195-196,217-218,257-258,271-273,308-310`
- **Fix:** In every `except Exception: pass` or bare fallback, add `logger.warning("agent proxy failed", exc_info=True)` (or `.error()`). Do NOT remove the catch — just add logging so failures are visible.
- **Verify:** Start portal without agent running, hit dashboard — check logs show a warning, not silence.

---

## BAND 2 — DATA INTEGRITY + PERFORMANCE

### [x] AF-013 — Use embed_batch() in VectorStore.add_documents() instead of serial embed loop
- **Severity:** HIGH (100x perf gain for batch inserts)
- **Files:**
  - `packages/northstar-vector/northstar_vector/client.py:85-93`
- **Fix:** Separate docs into those with/without embeddings. For those without, collect all texts, call `self._embedding_service.embed_batch(texts)` once, then interleave results back. Don't change docs WITH pre-computed embeddings.
- **Verify:** Check `embed_batch` is called (not `embed` in a loop). Run `tests/test_vector.py`.

### [x] AF-014 — Fix score calculation: use correct cosine→similarity formula
- **Severity:** HIGH
- **Files:**
  - `packages/northstar-vector/northstar_vector/client.py:177`
- **Fix:** Replace `score = 1.0 - distances[i]` with:
  ```python
  score = max(0.0, 1.0 - distance / 2.0) if using cosine else max(0.0, 1.0 - distance)
  ```
  Or check ChromaDB metadata for the space type. The division by 2 normalizes cosine distance [0,2] to [0,1] before inverting.
- **Verify:** `tests/test_vector.py` score tests should check values are non-negative.

### [x] AF-015 — Add retry logic to LLMService.generate() (3 retries, exponential backoff)
- **Severity:** CRITICAL
- **Files:**
  - `packages/northstar-llm/northstar_llm/service.py:46-75`
- **Fix:** Wrap each model call in a retry loop: 3 attempts with delays of 1s, 2s, 4s. Only fall through to fallback model if all retries of primary model fail. Catch `httpx.TimeoutException`, `httpx.ConnectError`, `httpx.ReadError` for retry; let unknown errors propagate.
- **Verify:** `tests/test_llm.py` — add a test that verifies retry behavior with a mock that fails twice then succeeds.

### [x] AF-016 — Add timeout to EmbeddingService httpx client
- **Severity:** HIGH
- **Files:**
  - `packages/northstar-llm/northstar_llm/service.py:165`
- **Fix:** Change `httpx.AsyncClient()` → `httpx.AsyncClient(timeout=httpx.Timeout(60.0))`.
- **Verify:** The constructor line reads `timeout=httpx.Timeout(60.0)`.

### [x] AF-017 — Fix N+1 refresh in bulk_create_entities and bulk_create_claims
- **Severity:** HIGH
- **Files:**
  - `packages/northstar-db/northstar_db/pg_repo.py:546-548,568-570`
- **Fix:** Replace the per-item `for m in models: await session.refresh(m)` with a single `await session.flush()` before returning (IDs and timestamps are already set client-side by CommonModel defaults; flush populates server defaults without extra queries).
- **Verify:** `rg "session.refresh" pg_repo.py` returns 0 results.

### [x] AF-018 — Add close() to LLMResponseCache and call from LLMService.close()
- **Severity:** MEDIUM
- **Files:**
  - `packages/northstar-llm/northstar_llm/cache.py` — add `def close(self)`
  - `packages/northstar-llm/northstar_llm/service.py:147-148` — call `self._cache.close()`
- **Fix:** In cache.py add `def close(self): self._cache.close()` (if diskcache supports it) or `self._cache.expire()`. In service.py `close()`, add `if self._cache: self._cache.close()`.
- **Verify:** `grep "cache.close" service.py` returns a hit.

### [x] AF-019 — Fix update_extraction_log status transition logic
- **Severity:** MEDIUM
- **Files:**
  - `packages/northstar-db/northstar_db/pg_repo.py:494-497`
- **Fix:** Only set `started_at = datetime.now(timezone.utc)` when transitioning to `IN_PROGRESS`. Set `completed_at` for `COMPLETED`, `FAILED`, and `SKIPPED`. Never overwrite `completed_at` if already set. Log a warning on invalid transitions.
- **Verify:** Review the logic in `pg_repo.py` — the flow should be clear and correct.

### [x] AF-020 — Add Pydantic Field validators on confidence (0.0–1.0) and quality_score (0.0–1.0)
- **Severity:** MEDIUM
- **Files:**
  - `packages/northstar-models/northstar_models/schemas.py` — all confidence and quality_score fields
- **Fix:** Replace bare `float | None` with `float | None = Field(None, ge=0.0, le=1.0)` on all confidence and quality_score fields across all schemas (EntityCreate/Read/Update, ClaimCreate/Read/Update, AnalysisCreate/Read/Update).
- **Verify:** `make test tests/test_models.py` — add a test that validates a confidence=2.0 raises ValidationError.

---

## BAND 3 — SAFETY + HARDENING

### [x] AF-021 — Fix restore.sh: add confirmation prompt + auto-backup before restore
- **Severity:** CRITICAL
- **Files:**
  - `scripts/restore.sh:23-30`
- **Fix:** Before `pg_restore --clean`, add:
  ```bash
  echo "WARNING: This will DESTROY the current database."
  read -p "Continue? (y/N) " confirm
  [[ "$confirm" != "y" && "$confirm" != "Y" ]] && echo "Aborted." && exit 1
  ```
  Optionally auto-run `./scripts/backup.sh` before restoring.
- **Verify:** `bash scripts/restore.sh` prompts for confirmation.

### [x] AF-022 — Fix check-health.sh: don't curl Neo4j Bolt port (use tcp check or skip)
- **Severity:** HIGH
- **Files:**
  - `scripts/check-health.sh:44-51`
- **Fix:** Replace `curl` to port 7687 with `nc -z 127.0.0.1 7687` or just check port 7474 for HTTP liveness.
- **Verify:** `bash scripts/check-health.sh` works against a running Neo4j container.

### [x] AF-023 — Add prerequisite checks to backup.sh (pg_dump availability)
- **Severity:** HIGH
- **Files:**
  - `scripts/backup.sh` — after the header comment
- **Fix:** Add:
  ```bash
  command -v pg_dump >/dev/null 2>&1 || { echo "ERROR: pg_dump not found."; exit 1; }
  ```
- **Verify:** `bash scripts/backup.sh` with pg_dump not in PATH shows clear error.

### [x] AF-024 — Add safety gate to chat-import-bridge (PROMOTION_ENABLED flag)
- **Severity:** HIGH
- **Files:**
  - `apps/chat-import-bridge/chat_import_bridge/config.py` — add `promotion_enabled: bool = Field(default=False, alias="PROMOTION_ENABLED")`
  - `apps/chat-import-bridge/chat_import_bridge/routers/promotion.py` — check the flag, return 403 if disabled
- **Fix:** Mirror the `FORCE_GRAPH_EXTRACTION` / `ENABLE_DESTRUCTIVE_CLEANUP` pattern from the agent.
- **Verify:** `make test tests/test_bridge_api.py` — add a test for 403 when flag is disabled.

### [x] AF-025 — Prevent Header Injection in Portal's Generic API Proxy
- **Severity:** MEDIUM
- **Files:**
  - `apps/research-portal/research_portal/main.py:280-282`
- **Fix:** Whitelist only safe headers (Accept, Accept-Encoding, User-Agent) instead of forwarding all request headers minus host/content-length.
- **Verify:** Read the proxy code, confirm only safe headers are forwarded.

### [x] AF-026 — Add `USER appuser` to Dockerfile (don't run as root)
- **Severity:** HIGH
- **Files:**
  - `Dockerfile`
- **Fix:** After the final `FROM python:3.11-slim`, add:
  ```dockerfile
  RUN useradd --create-home --shell /bin/bash appuser
  USER appuser
  EXPOSE 8099 3010 3022
  ```
- **Verify:** `docker build .` succeeds. Container runs as non-root.

### [x] AF-027 — Add Neo4j health check to docker-compose
- **Severity:** HIGH
- **Files:**
  - `docker/docker-compose.yml:19-28`
- **Fix:** Add after line 28:
  ```yaml
  healthcheck:
    test: ["CMD-SHELL", "neo4j status || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s
  ```
- **Verify:** `docker compose config` shows the healthcheck block.

---

## BAND 4 — TEST COVERAGE

### [x] AF-028 — Add unit tests for agent_tools.py (13 tool methods)
- **Severity:** CRITICAL
- **Files:**
  - `apps/research-portal/research_portal/services/agent_tools.py` (untested)
  - `tests/test_agent_tools.py` — create
- **Tasks:**
  1. Mock `httpx.AsyncClient` for all 13 `_tool_*` methods
  2. Verify correct URL paths and payloads
  3. Fix `_tool_extract` line 199: un-hardcode `force=true` — make it configurable
  4. Test error handling paths (network error, 4xx, 5xx)
- **Verify:** `make test tests/test_agent_tools.py` — all pass.

### [x] AF-029 — Add unit tests for orchestrator.py
- **Severity:** CRITICAL
- **Files:**
  - `apps/research-portal/research_portal/services/orchestrator.py` (untested)
  - `tests/test_orchestrator.py` — create
- **Tasks:**
  1. Mock `_llm_client.post` for valid plan generation
  2. Test LLM response with valid JSON
  3. Test LLM response with invalid JSON (regex extraction)
  4. Test empty plan
  5. Test tool execution failure mid-plan
  6. Test `_summarize_result` for each tool type
- **Verify:** `make test tests/test_orchestrator.py` — all pass.

### [x] AF-030 — Add unit tests for conversation.py (SQLite chat store)
- **Severity:** HIGH
- **Files:**
  - `apps/research-portal/research_portal/services/conversation.py` (untested)
  - `tests/test_conversation.py` — create
- **Tasks:**
  1. Use `:memory:` SQLite for tests
  2. Test conversation CRUD, message CRUD
  3. Test cascade delete
  4. Test JSON serialization of tool results
- **Verify:** `make test tests/test_conversation.py` — all pass.

### [x] AF-031 — Add unit tests for promotion.py service
- **Severity:** HIGH
- **Files:**
  - `apps/chat-import-bridge/chat_import_bridge/services/promotion.py` (no direct tests)
  - `tests/test_promotion_service.py` — create
- **Tasks:**
  1. Mock `httpx.AsyncClient` and `staging_db`
  2. Test successful promotion
  3. Test already-promoted (idempotency)
  4. Test HTTP error handling
  5. Test network error handling
- **Verify:** `make test tests/test_promotion_service.py` — all pass.

### [x] AF-032 — Un-skip portal page tests (dashboard, quality, cleanup, extraction, graph)
- **Severity:** HIGH
- **Files:**
  - `tests/test_portal_api.py:20,25,30,35,40,53` — remove `pytest.skip`
- **Fix:** Implement mock-based rendering tests. Use `portal_client.get(...)` and assert `response.status_code == 200` and check for key template content strings.
- **Verify:** `make test tests/test_portal_api.py` — all tests either pass or have real assertions (not skipped).

### [x] AF-033 — Un-skip portal safety gate tests (extraction force-enabled, cleanup enabled)
- **Severity:** HIGH
- **Files:**
  - `tests/test_safety_gates.py:40,66` — remove `pytest.skip`
- **Fix:** Mock the portal's inner `httpx.AsyncClient` proxy calls so these tests don't need a live agent.
- **Verify:** `make test tests/test_safety_gates.py` — all tests run.

### [x] AF-034 — Fix test_cleanup_report_never_modifies: actually call the endpoint
- **Severity:** MEDIUM
- **Files:**
  - `tests/test_safety_gates.py:68-70`
- **Fix:** Add `await agent_client.get("/api/v1/cleanup/report")` BEFORE the assert calls.
- **Verify:** `make test tests/test_safety_gates.py::test_cleanup_report_never_modifies`

---

## BAND 5 — HOUSEKEEPING (LOW/MEDIUM)

### [x] AF-035 — Fix `alembic.ini` or `env.py` to include `updated_at` for missing tables via new migration
- **Files:** `apps/research-agent/migrations/alembic.ini`, `apps/research-agent/migrations/env.py`
- **Fix:** Generate a new migration: `alembic revision --autogenerate -m "add_updated_at_columns"` then `alembic upgrade head`.
- **Verify:** Migration applies cleanly.

### [x] AF-036 — Reorder schemas: EntityCreate → EntityRead → EntityUpdate
- **Files:** `packages/northstar-models/northstar_models/schemas.py:84-117`
- **Fix:** Move `EntityRead` (lines 104-117) before `EntityUpdate` (lines 94-101).
- **Verify:** File ordering is Create → Read → Update for all 7 entities.

### [x] AF-037 — Fix Entity.aliases from `dict` → `list[str]` across all 3 layers
- **Files:** `northstar_models/models.py:51`, `northstar_models/schemas.py:88,98,109`, `migrations/001_initial_schema.py:58`
- **Fix:** Change type to `list[str]` (JSON array). Update all schemas and migration.
- **Verify:** `make test tests/test_models.py` — aliases-related tests pass.

### [x] AF-038 — Add `ondelete="CASCADE"` to FK relationships in ORM models
- **Files:** `packages/northstar-models/northstar_models/models.py` — all `ForeignKey(...)` declarations
- **Fix:** Add `ondelete="CASCADE"` to Source→Project, Entity→Source, Entity→Project, Claim→Source, Claim→Project, Claim→Entity, etc.
- **Verify:** `grep "ForeignKey" models.py` — all have `ondelete="CASCADE"`.

### [x] AF-039 — Fix `tools/pyproject.toml` namespace conflict
- **Files:** `tools/pyproject.toml:15-17`
- **Fix:** Either make tools a proper package with `packages = ["tools"]` and entry points, or remove `py-modules` and treat scripts standalone.
- **Verify:** `pip install -e tools/` doesn't pollute global namespace.

### [x] AF-040 — Add `restart: unless-stopped` to docker-compose services
- **Files:** `docker/docker-compose.yml` — both postgres and neo4j services
- **Fix:** Add `restart: unless-stopped` under each service definition.
- **Verify:** `docker compose config` shows restart policy.

### [x] AF-041 — Unify `TEMPLATE_DIR` pattern across portal routers (deduplicate 5 copies)
- **Files:** `apps/research-portal/research_portal/routers/extraction.py,quality.py,cleanup.py,visual.py,dashboard.py`
- **Fix:** Create `apps/research-portal/research_portal/template_utils.py` with a `create_template_env()` factory. Import in all 5 routers.
- **Verify:** `rg "BASE_DIR.*parent" research_portal/routers/` shows only 1 hit (in the new utils file).

### [x] AF-042 — Add `ge=1, le=1000` validation on list endpoint limit query params
- **Files:** All research-agent router `limit: int = Query(...)` parameters
- **Files:** `routers/projects.py`, `sources.py`, `entities.py`, `claims.py`, `reports.py`, `quality.py`
- **Fix:** Change bare `Query(50)` → `Query(50, ge=1, le=1000)`.
- **Verify:** Request with `?limit=99999` returns 422.

### [x] AF-043 — Break monolithic portal `api_v1_handler` into route-delegated proxy modules
- **Files:** `apps/research-portal/research_portal/main.py:164-298`
- **Fix:** Extract the 130-line `api_v1_handler` into `apps/research-portal/research_portal/routers/api_proxy.py` with per-resource proxy functions. Register with the main router.
- **Verify:** Portal dashboard still loads data through the proxy.

---

## STATUS TRACKER

| Band | Tasks | Done |
|------|-------|------|
| BAND 1 — Immediate (Security+Correctness) | AF-001 through AF-012 | 12/12 |
| BAND 2 — Data Integrity+Performance | AF-013 through AF-020 | 8/8 |
| BAND 3 — Safety+Hardening | AF-021 through AF-027 | 7/7 |
| BAND 4 — Test Coverage | AF-028 through AF-034 | 7/7 |
| BAND 5 — Housekeeping | AF-035 through AF-043 | 9/9 |

**Total: 43/43 complete**

---

## EXECUTION NOTES

- Run `make lint && make test` after EVERY task (not batch).
- Commit each task group separately (or 1 task = 1 commit for critical ones).
- Tasks with `CRITICAL` severity should NOT encounter a failure — if they do, fix the failure before moving on (do not skip).
- Use `grep`/`rg` to verify file changes before committing.
- Run from repo root. `.venv` must be active.
