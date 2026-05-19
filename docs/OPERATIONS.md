# Operations

## Daily check

```bash
make health
```

Expected behavior:

- Research Agent health endpoint returns `ok`.
- Portal status endpoint responds locally.
- Watcher reports no eligible projects unless a newly completed project needs graph extraction.
- Quality dashboards show no review-needed projects.

## Local endpoint defaults

| Service | Default local URL |
|---|---|
| Research Agent | `http://127.0.0.1:8099/health` |
| Research Portal | `http://127.0.0.1:3010/` |
| Portal knowledge status | `http://127.0.0.1:3010/api/knowledge/status` |
| Chat Import Bridge | `http://127.0.0.1:3022/chat-import` |

## CLI tools

Three CLI tools live in `tools/`:

### extract
Trigger LLM extraction on a source:

    python tools/extract.py <source-id> [--force] [--agent-url http://localhost:8099]

### query
Search and retrieve research data:

    python tools/query.py projects [--limit 50] [--offset 0]
    python tools/query.py sources --project-id <uuid>
    python tools/query.py entities [--source-id <uuid>]
    python tools/query.py claims [--source-id <uuid>]
    python tools/query.py search --query "text" --project-id <uuid>

### export
Export source data as Markdown or JSON:

    python tools/export.py <source-id> [--format markdown|json] [--output file.md]

See `docs/CLI.md` for full reference.

## Environment variable reference

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_HOST` | `127.0.0.1` | PostgreSQL host |
| `POSTGRES_PORT` | `5432` | PostgreSQL port |
| `POSTGRES_USER` | `northstar` | PostgreSQL user |
| `POSTGRES_PASSWORD` | `northstar` | PostgreSQL password |
| `POSTGRES_DB` | `northstar` | PostgreSQL database name |
| `NEO4J_URI` | `bolt://127.0.0.1:7687` | Neo4j bolt URI |
| `NEO4J_USER` | `neo4j` | Neo4j user |
| `NEO4J_PASSWORD` | *(none)* | Neo4j password — must be explicitly set |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama server URL |
| `PRIMARY_LLM_MODEL` | `qwen3:14b` | Primary LLM model for extraction |
| `FALLBACK_LLM_MODEL` | `llama3.1:8b` | Fallback LLM model |
| `EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model for vector search |
| `CHROMA_PERSIST_DIR` | `~/.cache/northstar/chromadb` | ChromaDB persistence directory |
| `FORCE_GRAPH_EXTRACTION` | `false` | Allow extraction without force flag |
| `ENABLE_DESTRUCTIVE_CLEANUP` | `false` | Allow destructive cleanup operations |
| `PROMOTION_ENABLED` | `false` | Enable chat-import promotion to Agent |
| `LOG_LEVEL` | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |

## Logging configuration

All services use `structlog`. Log level is set via `LOG_LEVEL` env var (default `INFO`).

Logs go to stdout. Structured JSON output can be enabled by setting `STRUCTLOG_FORMAT=json`.

For development, logs are pretty-printed. For production, set `STRUCTLOG_FORMAT=json` for machine parsing.

### Per-service log files

Logs are written to `logs/` at the repo root:
- `logs/research-agent.log`
- `logs/chat-import-bridge.log`
- `logs/research-portal.log`

## Prometheus metrics

Not currently exported. If Prometheus client is added, metrics would be available at `/metrics` on each service port.

## Stop conditions

Stop and inspect before continuing when:

- The agent health endpoint fails.
- The portal process is inactive.
- The watcher reports unknown graph status.
- Quality score falls below the configured minimum.
- Cleanup reports unexpectedly show duplicate or orphan candidates after a clean baseline.
- Any command proposes destructive cleanup without an explicit reviewed migration.
- Any promotion endpoint returns 403 (check `PROMOTION_ENABLED` flag).
- `restore.sh` prompts for confirmation — review before proceeding.

## Docker-compose hardening

Services in `docker/docker-compose.yml`:
- Both PostgreSQL and Neo4j use `restart: unless-stopped`.
- Neo4j has a healthcheck (`neo4j status`) with 30s start period.
- Containers run as non-root where applicable.

## API query limits

All agent list endpoints enforce `limit` values between 1 and 1000. Requests with `limit` outside this range return HTTP 422. Default limit is 50 per endpoint.
