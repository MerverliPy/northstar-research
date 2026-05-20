# Operations Reliability Audit

**Date:** 2026-05-20
**Auditor:** Ops Reliability Reviewer (automated)
**Scope:** Docker, scripts, systemd, config, logging, startup/shutdown

---

## Overall Ops Health Score: **62/100 (MEDIUM RISK)**

The codebase has solid architectural foundations — safety gates, restart policies, backup scripts, and reproducible builds. However, several structural gaps exist: the Dockerfile likely fails to build due to permissions, logging is never configured, the chat-import-bridge leaks connections on shutdown, and restore scripts lack pre-destruction safety backups.

---

## Summary — Top 5 Findings

| # | Severity | Finding |
|---|----------|---------|
| 1 | **CRITICAL** | Dockerfile `USER appuser` before `pip install -e` will fail — appuser cannot write to root-owned system site-packages |
| 2 | **CRITICAL** | Chat-import-bridge SQLite async engine is never disposed on shutdown; no `close()` in lifespan |
| 3 | **HIGH** | `structlog` is imported everywhere but **never configured** — `log_level` settings in all three configs are dead code |
| 4 | **HIGH** | `restore.sh` destroys the current database without offering a pre-restore backup option |
| 5 | **HIGH** | Health endpoints return hardcoded `{"status":"ok"}` without verifying DB connectivity; Dockerfile has no `HEALTHCHECK` |

---

## Docker Audit

### docker-compose.yml

| Check | Status | Notes |
|-------|--------|-------|
| Service definitions | PASS | Postgres + Neo4j defined with container names |
| Healthcheck — Postgres | PASS | `pg_isready` with 5s interval, 3s timeout, 5 retries |
| Healthcheck — Neo4j | **WARN** | Uses `neo4j status` which is deprecated in Neo4j 5.x; may work but fragile |
| Restart policies | PASS | Both use `restart: unless-stopped` |
| Volume mounts — Postgres | PASS | Named volume `northstar-pg-data` at correct path |
| Volume mounts — Neo4j | PASS | Named volume `northstar-neo4j-data` at `/data` |
| Volume definitions | PASS | Both volumes declared |
| Depends on (startup order) | **FAIL** | No `depends_on` with `condition: service_healthy` — apps could race DB startup |
| Resource limits | **LOW** | No `mem_limit`, `cpus`, or `mem_reservation` defined |
| Image pinning | **MEDIUM** | `postgres:16-alpine` and `neo4j:5-community` are floating tags, no digest pinning |
| Network config | **LOW** | No explicit network defined (falls back to default bridge) |
| Secrets exposure | **MEDIUM** | Credentials hardcoded as env vars (visible in `docker inspect`) |
| Neo4j start_period | PASS | 30s start_period on healthcheck is appropriate |

### Dockerfile (3-stage multi-stage build)

| Check | Status | Notes |
|-------|--------|-------|
| Non-root user | **CRITICAL** | `USER appuser` declared BEFORE `pip install -e`. The `COPY` commands run as root (files owned by root). `pip install -e` (editable installs) must write `.pth`/`.egg-link` files to `/usr/local/lib/python3.11/site-packages/` which is **root-owned**. This build will **fail** at every `pip install -e` step after `USER appuser`. Fix: run all `pip install` as root BEFORE `USER appuser`, or use `--user`, or `chown` site-packages, or use a venv in `/home/appuser`. |
| Layer caching | **MEDIUM** | Package COPY happens before pip install, but in correct dependency order (models → llm → vector → db → apps). Good. However, all COPYs are inline — no separate `COPY requirements.txt` for pip dependency resolution caching. |
| Base stage `uv` install | **LOW** | `pip install uv` is installed but never used — all child stages use plain `pip`. Either remove `uv` or switch to `uv pip install`. |
| Chromium deps (agent stage) | PASS | Installs necessary headless browser system deps, cleans apt cache |
| Entrypoint/CMD | PASS | Each stage has correct `uvicorn` CMD with host/port |
| `.dockerignore` | PASS | Exists and covers `.venv`, `__pycache__`, databases, `.env`, logs, backups |
| Build context safety | PASS | `.dockerignore` prevents most large/secret files from entering context |
| HEALTHCHECK (Docker) | **FAIL** | No `HEALTHCHECK` instruction in any stage. Without it, orchestrators can't verify container health independently of the app health endpoint. |
| Multi-stage naming | PASS | `FROM base AS agent/bridge/portal` — clean stage separation |

---

## Script Safety Audit

### doctor.sh

| Check | Status | Notes |
|-------|--------|-------|
| Shell safety | PASS | `set -euo pipefail` |
| Tools checked | PASS | git, bash, curl, docker, docker compose, python3, .venv |
| Package importability | PASS | Tests `import northstar_db`, `northstar_llm`, `northstar_models`, `northstar_vector` |
| Config files | PASS | Checks pyproject.toml, main.py, templates, alembic.ini |
| Docker compose validation | PASS | Runs `docker compose config --quiet` |
| Ollama check | PASS | Warns (not fails) if unreachable — appropriate for optional dependency |
| Missing checks | **MEDIUM** | Does not check: `pg_dump` availability, `psql` availability, disk space on DB volumes, Neo4j connectivity, ChromaDB directory existence |
| `.env` check | **LOW** | Warns if `.env` exists (good) but fails if absent — `.env.example` is committed so the deprecation warning and failure are misleading. Should check for `.env.example` as the canonical reference. |

### check-health.sh

| Check | Status | Notes |
|-------|--------|-------|
| Shell safety | PASS | `set -euo pipefail` |
| Endpoint coverage | PASS | Checks all 3 services: agent (:8099), bridge (:3022), portal (:3010) |
| DB checks | PASS | Checks PostgreSQL connectivity via `psql`, Neo4j via curl/nc |
| Health check depth | **HIGH** | Only checks HTTP 200 — doesn't verify the services are actually healthy (DB connectivity, etc.). The health endpoints themselves are passthrough (`{"status":"ok"}`). |
| Neo4j fallback | PASS | Falls back to Bolt port (7687) nc check if HTTP (7474) fails |
| Timeout | PASS | 10s timeout on curl calls |
| Error reporting | PASS | Reports HTTP status code on failure |

### backup.sh

| Check | Status | Notes |
|-------|--------|-------|
| Shell safety | PASS | `set -euo pipefail`, trap for tmpdir cleanup |
| Prerequisite check | PASS | Checks `pg_dump` availability |
| PostgreSQL backup | PASS | Uses `pg_dump -F c` (custom format, suitable for `pg_restore`) |
| ChromaDB backup | PASS | Copies ChromaDB directory if it exists |
| Archive creation | PASS | Creates dated tar.gz |
| Integrity verification | **HIGH** | No post-backup verification — does not test `tar -tzf` or `pg_restore --list` on the created archive. A silent corruption would go undetected. |
| Sensible defaults | PASS | `OUTPUT_DIR` defaults to `$HOME/northstar-backups` |
| Environment handling | PASS | Uses `${VAR:-default}` pattern for all DB connection params |

### restore.sh

| Check | Status | Notes |
|-------|--------|-------|
| Shell safety | PASS | `set -euo pipefail`, trap for tmpdir cleanup |
| Confirmation prompt | PASS | Explicit `(y/N)` prompt with destructive warning |
| File existence check | PASS | Validates backup file exists before proceeding |
| Pre-restore backup | **HIGH** | **No pre-restore safety backup.** The script destroys the current database without offering to back it up first. A mistaken confirmation or wrong backup file selection is irreversible. |
| pg_restore flags | PASS | Uses `--clean --if-exists` (appropriate for full restore) |
| ChromaDB restore | **MEDIUM** | Uses `rm -rf "$CHROMA_DIR"` before restore — no confirmation on ChromaDB destruction. If PG restore fails, ChromaDB is already gone. |
| Rollback capability | **FAIL** | No rollback mechanism. Once confirmed, the restore proceeds with no undo path. |
| Partial failure handling | **MEDIUM** | If PG restore fails after ChromaDB is restored, state is inconsistent (new ChromaDB + old PG). |

### verify-no-secrets.sh

| Check | Status | Notes |
|-------|--------|-------|
| Git context check | PASS | Skips if not in git worktree |
| Blocked patterns | PASS | Blocks: `.env`, `.env.*`, `*.sqlite*`, `*.db`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, archives, `backups/*`, `data/*`, `exports/*`, `logs/*` |
| `.gitkeep` exclusion | PASS | Allows `data/.gitkeep`, `exports/.gitkeep`, `logs/.gitkeep` |
| Pre-commit readiness | PASS | Designed as a pre-commit hook (checks `git diff --cached`) |
| Missing checks | **LOW** | Does not scan file contents for hardcoded API keys, tokens, or passwords in committed source code files |

---

## Config Audit

### research-agent (config.py)

| Check | Status | Notes |
|-------|--------|-------|
| Defaults | PASS | Sensible localhost defaults |
| Safety gates | PASS | `force_graph_extraction=False`, `enable_destructive_cleanup=False` |
| env_prefix | PASS | Uses `""` (no prefix) — consistent with `.env.example` |
| case_sensitive | PASS | `False` for flexibility |
| DB URL | **MEDIUM** | Hardcoded credentials in default `database_url` |
| Neo4j auth | **MEDIUM** | Hardcoded credentials in defaults |
| Scraper config | PASS | Disabled by default, requires explicit `SCRAPER_ENABLED=true` |
| LLM models | PASS | Primary + fallback models configured |
| log_level | **HIGH** | `log_level="INFO"` is defined but **never applied** — no structlog configuration uses it |

### research-portal (config.py)

| Check | Status | Notes |
|-------|--------|-------|
| Defaults | PASS | Sensible localhost defaults |
| Service URLs | PASS | agent, bridge, ollama URLs all correct |
| Safety gates | PASS | `force_graph_extraction=False`, `enable_destructive_cleanup=False` |
| Conversation DB | **LOW** | Uses synchronous `sqlite3` (not async) — OK for single-user but no concurrency guard |
| log_level | **HIGH** | Same dead-code `log_level` as agent |

### chat-import-bridge (config.py)

| Check | Status | Notes |
|-------|--------|-------|
| Defaults | PASS | Correct staging DB path, agent URL |
| Promotion gate | PASS | `promotion_enabled=False` — proper safety default |
| log_level | **HIGH** | Same dead-code `log_level`; additionally, bridge has **zero logging imports** |
| Missing settings | **LOW** | No max import size, rate limiting, or session cleanup TTL |

### alembic.ini

| Check | Status | Notes |
|-------|--------|-------|
| Hardcoded DB URL | **MEDIUM** | `sqlalchemy.url = postgresql+asyncpg://northstar:northstar@127.0.0.1:5432/northstar` — hardcoded credentials |
| logging config | PASS | Partial overrides for sqlalchemy/alembic loggers |

---

## Logging Review

| Check | Status | Notes |
|-------|--------|-------|
| structlog imports | PASS | Used consistently across research-agent (5 modules), research-portal (5 modules), and packages (4 modules) |
| structlog configuration | **HIGH** | **Never called anywhere.** No `structlog.configure()`, no `logging.basicConfig()`, no processor chain setup. Default structlog uses stdlib `logging` which defaults to `WARNING` level — `log_level="INFO"` in config is dead code. Log format is unstructured stdlib output, not structured key-value. |
| Chat-import-bridge logging | **HIGH** | **Zero logging.** No `structlog`, no `logging`, no `print` statements for operational observability. The bridge operates silently — failures during import/promotion/export are invisible. |
| Sensitive data | **LOW** | No obvious password/token logging, but `exc_info=True` in exception handlers could leak DB connection strings if exceptions occur during connection setup |
| Log levels | **MEDIUM** | Configs set `INFO` but since structlog isn't configured, all services run at Python default `WARNING`. Debugging production issues will be hard. |
| Structured logging | PASS | Code uses structured key-value style (`logger.info("event_name", key=value)`) — **but** without configuration, the default renderer loses this benefit. |

---

## Startup/Shutdown Audit

### research-agent (main.py)

| Check | Status | Notes |
|-------|--------|-------|
| Lifespan pattern | PASS | `@asynccontextmanager` with proper init/yield/close |
| Service init | PASS | `init_services()` initializes PG, Neo4j, Embedding, VectorStore, LLM, (optional) Scraper |
| Service close | PASS | `close_services()` properly disposes PG engine and Neo4j driver |
| Graceful shutdown | PASS | Lifespan yield + close pattern handles FastAPI's SIGTERM properly |
| Module-level globals | **MEDIUM** | `_db`, `_llm`, etc. are module-level globals — works for single-worker but not for multi-worker (gunicorn). Fine for local/uvicorn. |
| Health endpoint | **HIGH** | `/health` returns `{"status":"ok","service":"research-agent"}` without verifying PG or Neo4j connectivity. Cannot detect DB failures. |

### research-portal (main.py)

| Check | Status | Notes |
|-------|--------|-------|
| Lifespan pattern | PASS | Proper init (services + orchestrator + conversation + http client) / yield / close sequence |
| Service cleanup | PASS | Calls orchestrator.close(), conversation_store.close(), http_client.aclose(), close_services() |
| Orchestrator | PASS | Started and stopped in lifespan |
| Static file serving | **LOW** | `STATIC_DIR.mkdir()` runs at module import time — no-op if exists but unusual pattern |
| Path traversal protection | PASS | SPA catch-all validates `full_path` resolves within STATIC_DIR |
| Health endpoint | **HIGH** | Same passthrough as agent — no dependency verification |
| Module-level globals | **MEDIUM** | `_db`, `_neo4j` are module-level globals in dependencies.py |

### chat-import-bridge (main.py)

| Check | Status | Notes |
|-------|--------|-------|
| Lifespan pattern | PASS | `@asynccontextmanager` with init_staging_db() |
| Engine disposal | **CRITICAL** | **`_engine` in `database.py` is never disposed.** The `lifespan` calls `init_staging_db()` which creates the async engine, but there is no `close_staging_db()`, no `await engine.dispose()`, and no lifespan cleanup. SQLite connections leak on every shutdown. |
| Service init | PASS | `init_staging_db()` creates engine + tables |
| Health endpoint | **HIGH** | passthrough `{"status":"ok"}` — doesn't verify staging DB is accessible |
| Zero observability | **HIGH** | As noted in logging section — no logs at all |

---

## Systemd Audit

### research-portal-native.service

| Check | Status | Notes |
|-------|--------|-------|
| Unit description | PASS | Clearly describes service purpose |
| After dependency | PASS | `network-online.target northstar-pg.service` — waits for network and (attempts) PG |
| Type | PASS | `simple` is correct for uvicorn |
| WorkingDirectory | PASS | `%h/northstar-research` |
| EnvironmentFile | **MEDIUM** | Points to `apps/research-portal/.env` — this file is **gitignored** and may not exist. Startup will silently proceed without it. |
| ExecStart | PASS | Direct uvicorn invocation with host/port |
| Restart | **LOW** | `Restart=on-failure` — no `RestartSec` defined (defaults to 100ms). No `StartLimitBurst` or `StartLimitIntervalSec` to prevent rapid restart loops. |
| Install target | PASS | `WantedBy=default.target` |
| Missing | **MEDIUM** | No `ExecStop`, no `TimeoutStopSec` — relies on SIGTERM default. No `SyslogIdentifier`. No `StandardOutput`/`StandardError` config for journald. |

### phase1-daily-use.service

| Check | Status | Notes |
|-------|--------|-------|
| Type | **MEDIUM** | `Type=oneshot` with `RemainAfterExit=yes` — correct for starting Docker containers, but: |
| ExecStop missing | **HIGH** | **No `ExecStop` defined.** `systemctl --user stop phase1-daily-use` will record the unit as inactive but **will not stop the Docker containers**. They keep running orphaned. Must define `ExecStop=docker compose -f %h/northstar-research/docker/docker-compose.yml down` or similar. |
| After dependency | **LOW** | Only `network-online.target` — no dependency on `docker.service` or `docker.socket`. |
| Restart | N/A | oneshot services don't restart |
| Install target | PASS | `WantedBy=default.target` |

---

## Quick Wins (low effort, high impact)

1. **Fix Dockerfile permissions**: Move all `pip install -e` before `USER appuser`, then `USER appuser` before CMD only. (~5 lines changed in Dockerfile)
2. **Dispose bridge engine**: Add `close_staging_db()` that calls `await _engine.dispose()` and call it in lifespan shutdown. (~10 lines in database.py + main.py)
3. **Configure structlog**: Add a `logging_config.py` in each app's package root that calls `structlog.configure(...)` reading from `settings.log_level`. (~15 lines per app)
4. **Add pre-restore backup option**: In `restore.sh`, offer to run `backup.sh` first before proceeding. (~5 lines)
5. **Add Docker HEALTHCHECK**: Add `HEALTHCHECK --interval=15s --timeout=5s --retries=3 CMD curl -f http://localhost:<port>/health || exit 1` to each stage. (~3 lines per stage)

## Structural Issues (higher effort, important)

1. **Deepen health endpoints**: All three `/health` endpoints should verify their dependencies (PG, Neo4j, SQLite staging DB) and return detailed status. Currently, a service could be running but dead to its database.
2. **Add `depends_on` with health conditions**: In docker-compose, add `depends_on: postgres: {condition: service_healthy}` and `depends_on: neo4j: {condition: service_healthy}` for any future app services.
3. **Add podman/systemd health integration**: Use `ExecStartPost` or health check wrapper scripts that block until services are truly ready.
4. **Add observability to chat-import-bridge**: Add structlog logging to all routers and services, especially around import/promotion operations.
5. **Backup integrity verification**: Add `pg_restore --list` check after `pg_dump` to verify the backup is restorable before declaring success.
6. **Database password management**: Move from hardcoded defaults in config.py and alembic.ini to environment variables only (no defaults containing real passwords).

## Resource Limits Recommendation

```
# Add to docker-compose.yml:
services:
  postgres:
    mem_limit: 512m
    mem_reservation: 256m
  neo4j:
    mem_limit: 1g
    mem_reservation: 512m
```

## Connection Pool Recommendation

```python
# In PostgresRepository.__init__:
self._engine = create_async_engine(
    database_url,
    echo=echo,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)
```

---

## Final Risk Assessment

| Category | Score | Notes |
|----------|-------|-------|
| Build reliability | **40/100** | Dockerfile likely broken due to permissions |
| Runtime reliability | **65/100** | Graceful shutdown mostly works, but bridge leaks connections |
| Observability | **35/100** | Logging is never configured; bridge has zero logging |
| Backup/restore safety | **55/100** | Good foundations but no pre-restore backup or integrity verification |
| Configuration hygiene | **60/100** | Safety gates work, but hardcoded creds + dead `log_level` |
| Systemd integration | **50/100** | Portal service OK, Docker service has no stop command |
| **Overall** | **62/100** | **MEDIUM RISK** — Safe for local dev with manual intervention; not production-ready without the CRITICAL and HIGH findings addressed |

---

## Rollback Notes

- **Dockerfile fix is backward-compatible**: Moving `pip install` before `USER` doesn't change runtime behavior.
- **Bridge engine disposal is additive**: Adding `close_staging_db()` has no impact on existing behavior.
- **Structlog configuration is safe to add incrementally**: Each app can be configured independently.
- **`restore.sh` pre-backup is additive**: Doesn't change existing restore behavior, only adds an option.
- **Health endpoint deepening is non-breaking**: Adding checks to existing responses doesn't break consumers.
