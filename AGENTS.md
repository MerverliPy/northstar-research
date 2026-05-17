# Northstar Research

Python 3.11+ monorepo with 3 FastAPI services and 4 shared packages.

## Commands

| Purpose | Command |
|---------|---------|
| Install packages only | `make install` |
| Install packages + apps | `make install-all` |
| Run tests | `make test` |
| Lint | `make lint` |
| Health check | `make health` |
| Secrets scan | `make check-secrets` |
| Doctor check | `make doctor` |

Always run `make lint` and `make test` after making changes. Run from repo root.

## Architecture

```
apps/
  research-agent/     Port 8099 — Core CRUD API + extraction + search + quality
  research-portal/    Port 3010 — Jinja2+HTMX UI dashboards + graph viewer
  chat-import-bridge/ Port 3022 — SQLite staging import, promotion to Agent

packages/
  northstar-models/   Pydantic schemas + SQLAlchemy ORM models + enums (NO deps)
  northstar-llm/      LLMService + EmbeddingService (depends on models)
  northstar-vector/   ChromaDB wrapper with auto-embedding (depends on llm)
  northstar-db/       Async PG repo + Neo4j repo (depends on models)

config/
  .env.example        All env vars documented; apps use pydantic-settings

docker/
  docker-compose.yml  PostgreSQL 16 + Neo4j 5

scripts/             doctor.sh, check-health.sh, backup.sh, restore.sh, verify-no-secrets.sh
tools/               CLI: query.py, extract.py, export.py
tests/               Integration tests (pytest + pytest-asyncio)
```

Editable install order (enforced by `make install-all`): models → llm → vector → db → apps.

## Coding Conventions

- **Async everything** — all services, repos, routers use `async def`
- **4-space indent** for Python, **2-space** for everything else, **tabs** for Makefile
- **LF line endings**, trailing newline required (`.editorconfig`)
- **Ruff linting** — `ruff check packages/ apps/ scripts/` (no config file, uses defaults)
- **Module naming** — directories use hyphens (`northstar-models/`), Python packages use underscores (`northstar_models/`)
- **Type hints** required in all public function signatures

### Schema Triples

Every entity has three Pydantic models:
```python
class XCreate(BaseModel): ...
class XRead(BaseModel):
    model_config = {"from_attributes": True}
class XUpdate(BaseModel): ...
```

SQLAlchemy ORM models in `northstar_models/models.py`. All inherit `CommonModel(DeclarativeBase)` providing UUID `id`, `created_at`, `updated_at`.

### Metadata Column

Pydantic field named `metadata`. SQLAlchemy column named `metadata_`, mapped via `mapped_column("metadata", JSON, nullable=True)`.

### Settings Pattern

Each app has `config.py` with a pydantic-settings `Settings` class. Single module-level `settings = Settings()` instance.

### DI Pattern

`dependencies.py` uses module-level globals initialized at startup via FastAPI `lifespan`, then injected with `Depends(get_db)` etc.

### Repository Pattern

`PostgresRepository` and `Neo4jRepository` encapsulate DB ops. Session-per-operation via `async with self._session()`. Method naming: `create_X`, `get_X`, `list_X`, `update_X`, `delete_X`, `bulk_create_X`.

### API Router Structure

Each resource: `routers/<resource>.py` with `APIRouter(prefix="/<resources>", tags=["..."])`. Included in `main.py` under `/api/v1`.

### Logging

`structlog.get_logger(__name__)` at module level. Structured logging with key-value args.

### Safety Gates

Two env flags default to `false`:
- `FORCE_GRAPH_EXTRACTION` — enables graph extraction endpoints
- `ENABLE_DESTRUCTIVE_CLEANUP` — enables destructive cleanup routes

Destructive routes return 403 unless explicitly enabled.

### Test Patterns

- Heavy mocking with `AsyncMock` for all DB/LLM/Neo4j/VectorStore calls
- Fixtures in `tests/conftest.py` create fake entities with `uuid.uuid4()` IDs
- App clients via `ASGITransport` + `AsyncClient` with `pytest.mark.asyncio`
- Test classes grouped by feature: `TestForceGraphExtraction`, `TestDestructiveCleanup`, etc.

## Container Build (Dockerfile)

3-stage multi-stage build: agent (:8099), bridge (:3022), portal (:3010).

## File Organization

Do not create new top-level directories without updating `ROOT_STRUCTURE.md`. New Python packages go under `packages/`, new services under `apps/`.

## External File References

When referencing architecture details, read:
- `docs/ARCHITECTURE.md` for system design
- `docs/API.md` for endpoint documentation
- `ROOT_STRUCTURE.md` for directory layout rules
- `.opencode/contracts/BUILD_CONTRACT.md` for current build status
