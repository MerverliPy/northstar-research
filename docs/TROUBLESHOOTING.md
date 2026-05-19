# Troubleshooting

## Portal route returns HTTP 404

Likely cause: service is running, but the route has not been installed in that app. Check service status and route registration before patching.

## Local HTTP sent to HTTPS tailnet listener

Use HTTPS for Tailscale Serve hostnames and HTTP for `127.0.0.1` inside WSL.

## Docker credential helper failure inside WSL

Symptom:

```text
failed to solve: error getting credentials
A specified logon session does not exist. It may already have been terminated.
```

Conservative repair:

```bash
mkdir -p ~/.docker
[ -f ~/.docker/config.json ] && cp ~/.docker/config.json ~/.docker/config.json.bak.$(date +%Y%m%d-%H%M%S)
printf '{\n  "auths": {}\n}\n' > ~/.docker/config.json
```

## Docker container disappeared after patching

Run from the service directory:

```bash
docker compose up -d --build
docker compose ps
```

## WSL GPU mismatch

In WSL, `lspci` may not show the same GPU state as `nvidia-smi`. Prefer `nvidia-smi` and Docker runtime validation for GPU availability.

## Common startup issues

### Port conflicts

If a service fails to start, check if the port is already in use:

```bash
ss -tlnp | grep -E ':8099|:3022|:3010'
```

Kill the process using the port, or change the port in the service config.

### Missing dependencies

If `ModuleNotFoundError` occurs, verify the virtualenv is activated and packages are installed:

```bash
source .venv/bin/activate
pip install -e packages/northstar-models -e packages/northstar-db -e packages/northstar-llm -e packages/northstar-vector
pip install -e apps/research-agent -e apps/chat-import-bridge -e apps/research-portal
```

### .venv not activated

Services expect to run from the repo root with `.venv` activated. If you see import errors:

```bash
source .venv/bin/activate
```

## Extraction failures

### Ollama not running

Extraction requires Ollama at `http://127.0.0.1:11434`. Check if it's running:

```bash
curl http://127.0.0.1:11434/api/tags
```

Start Ollama if needed:

```bash
ollama serve
```

### Model not pulled

Check which models are available:

```bash
ollama list
```

Pull the required model (default: `qwen3:14b` or `llama3.1:8b`):

```bash
ollama pull qwen3:14b
```

### FORCE_GRAPH_EXTRACTION gate

If extraction returns 403, either set `FORCE_GRAPH_EXTRACTION=true` in `.env` or pass `--force` to `tools/extract.py`:

```bash
python tools/extract.py <source-id> --force
```

### PROMOTION_ENABLED gate

If promotion endpoints return 403, set `PROMOTION_ENABLED=true` in the bridge's environment:

```bash
# In apps/chat-import-bridge/.env:
PROMOTION_ENABLED=true
```

### LLM retries and timeouts

LLMService uses 3-retry exponential backoff for transient errors (TimeoutException, ConnectError, ReadError). If you see repeated `llm_attempt_failed` log warnings:
- Verify Ollama is responsive: `ollama list`
- Check model is pulled: `ollama pull qwen3:14b`
- The service will automatically fall back from primary model (qwen3:14b) to fallback (llama3.1:8b)

### Embedding timeout

EmbeddingService has a 60-second httpx timeout. Large batch operations may need longer. If you see `ReadTimeout` errors on embedding:
- Reduce batch size
- Check Ollama GPU memory availability
- Verify embedding model is pulled: `ollama pull nomic-embed-text`

## Database connection issues

### PostgreSQL unreachable

Verify Postgres is running:

```bash
pg_isready -h 127.0.0.1 -p 5432 -U northstar -d northstar
```

Check Docker container:

```bash
docker ps | grep northstar-pg
docker compose -f docker/docker-compose.yml logs postgres
```

### Neo4j unreachable

Check Neo4j is running:

```bash
curl -I http://127.0.0.1:7474
```

Check Docker container:

```bash
docker ps | grep northstar-neo4j
docker compose -f docker/docker-compose.yml logs neo4j
```

### Neo4j authentication failure

If you see authentication errors, verify the password is explicitly set:
- The Neo4j repo has no hardcoded default — it must be configured.
- Set `NEO4J_PASSWORD` in your `.env` file to match `docker-compose.yml` `NEO4J_AUTH`.
- In `docker-compose.yml`, the default is `neo4j/northstar`.

### REST API 422 on list endpoints

If you receive HTTP 422 on a list endpoint, check the `limit` parameter:
- All list endpoints enforce `limit` between 1 and 1000.
- Values outside this range (including 0 or 99999) return 422.
- Default is 50. Use `?limit=100` or any value in [1, 1000].

## Vector store corruption recovery

If ChromaDB is corrupted, clear and re-seed:

```bash
# Stop services
# Remove ChromaDB data
rm -rf ~/.cache/northstar/chromadb
# Re-run extraction on sources
python tools/extract.py <source-id> --force
```

## How to reset and rebuild from scratch

1. Stop all services.
2. Reset databases:

```bash
docker compose -f docker/docker-compose.yml down -v
docker compose -f docker/docker-compose.yml up -d
```

3. Run migrations:

```bash
cd apps/research-agent
alembic upgrade head
cd ../..
```

4. Clear vector store:

```bash
rm -rf ~/.cache/northstar/chromadb
```

5. Start services.
6. Re-import data and re-run extraction on sources.
