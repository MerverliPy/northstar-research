# Northstar Research

Local AI research system. PostgreSQL source of truth, Neo4j graph layer, self-hosted LLMs via Ollama, ChromaDB vector search.

## Architecture

```
Chat Import         Research            Research
Bridge (:3022) ──▶  Agent (:8099) ──▶  Portal (:3010)
SQLite staging      FastAPI + LLM       Jinja2+HTMX
                        │                    │
                  ┌─────┴──────┐       ┌─────┴──────┐
                  │ PostgreSQL │       │   Neo4j    │
                  │  (source   │       │  (graph,   │
                  │  of truth) │       │  derived)  │
                  └─────┬──────┘       └────────────┘
                        │
                  ┌─────┴──────┐
                  │  ChromaDB  │
                  │   vector   │
                  └────────────┘
```

## Quick start

```bash
# Prerequisites: Docker, Python 3.11+, Ollama with models
git clone <repo-url> northstar-research
cd northstar-research
python3 -m venv .venv
source .venv/bin/activate
make install-all
cp config/.env.example .env

# Start databases
docker compose -f docker/docker-compose.yml up -d

# Run migrations
alembic -c apps/research-agent/migrations/alembic.ini upgrade head

# Start services
uvicorn research_agent.main:app --reload --port 8099 &
uvicorn chat_import_bridge.main:app --reload --port 3022 &
uvicorn research_portal.main:app --reload --port 3010 &
```

## Typical workflow

```
1. Import content ──▶ 2. Extract entities ──▶ 3. Search & query ──▶ 4. View graph
   (paste, URL)         (LLM, optional         (vector search,      (vis.js,
                        graph via Neo4j)       CLI tools)           Portal)
```

### 1. Import content

**Via Portal** — Navigate to the Import section, paste text.

**Via Bridge API:**
```bash
curl -X POST http://localhost:3022/api/v1/imports/paste \
  -H "Content-Type: application/json" \
  -d '{"title": "My Source", "content": "Full text here..."}'
```

**Via CLI:**
```bash
python tools/query.py projects
```

### 2. Promote to Agent

```bash
curl -X POST http://localhost:3022/api/v1/promotion/1
```

This creates a Source in PostgreSQL via the Research Agent API.

### 3. Extract entities and claims

```bash
# Extract (dry-run by default — returns 403 unless --force or FORCE_GRAPH_EXTRACTION=true)
python tools/extract.py <source-id> --force
```

Or via API:
```bash
curl -X POST http://localhost:8099/api/v1/extraction/extract \
  -H "Content-Type: application/json" \
  -d '{"source_id": "<uuid>", "force": true}'
```

### 4. Search

```bash
python tools/query.py search --query "your search terms" --project-id <uuid>
```

### 5. Explore graph

Open https://localhost:3010/graph in the Portal, select a project, explore the vis.js knowledge graph.

## CLI tools

```bash
# List projects
python tools/query.py projects

# List sources for a project
python tools/query.py sources --project-id <uuid>

# Vector search
python tools/query.py search --query "text" --project-id <uuid> --top-k 10

# Trigger extraction
python tools/extract.py <source-id> [--force]

# Export source as Markdown/JSON
python tools/export.py <source-id> --format markdown --output article.md
```

## API endpoints

### Research Agent (:8099)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET/POST | `/api/v1/projects` | List/create projects |
| GET/PUT/DELETE | `/api/v1/projects/{id}` | Get/update/delete project |
| GET/POST | `/api/v1/sources` | List/create sources |
| GET/DELETE | `/api/v1/sources/{id}` | Get/delete source |
| GET/POST | `/api/v1/entities` | List/create entities |
| GET/DELETE | `/api/v1/entities/{id}` | Get/delete entity |
| GET/POST | `/api/v1/claims` | List/create claims |
| GET/DELETE | `/api/v1/claims/{id}` | Get/delete claim |
| GET/POST | `/api/v1/reports` | List/create reports |
| DEL | `/api/v1/reports/{id}` | Delete report |
| POST | `/api/v1/extraction/extract` | Trigger extraction (403 unless force) |
| GET | `/api/v1/extraction/status/{id}` | Extraction status |
| POST | `/api/v1/quality/score` | Score source quality |
| GET | `/api/v1/cleanup/report` | Dry-run cleanup report |
| POST | `/api/v1/cleanup/execute` | Execute cleanup (403 unless flag) |
| POST | `/api/v1/search` | Vector search |

### Chat Import Bridge (:3022)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/imports/paste` | Import content via paste |
| GET | `/api/v1/imports` | List staged imports |
| GET | `/api/v1/imports/{id}` | Get staged import |
| DEL | `/api/v1/imports/{id}` | Delete staged import |
| GET | `/api/v1/export/{id}/markdown` | Export as Markdown |
| POST | `/api/v1/promotion/{id}` | Promote import to Agent |
| POST | `/api/v1/promotion/batch` | Promote all pending |

### Research Portal (:3010)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard |
| GET | `/quality` | Quality scoring page |
| GET/POST | `/cleanup` | Cleanup report/execute |
| GET/POST | `/extraction` | Extraction gate |
| GET | `/graph` | Graph viewer |
| GET | `/graph/data/{project_id}` | Graph JSON (vis.js) |

## Safety doctrine

Non-negotiable defaults (set in `.env`):

| Flag | Default | Effect |
|------|---------|--------|
| `FORCE_GRAPH_EXTRACTION` | `false` | Extraction to Neo4j returns 403 unless true |
| `ENABLE_DESTRUCTIVE_CLEANUP` | `false` | Cleanup execute returns 403 unless true |

- PostgreSQL is source of truth. Neo4j is derived.
- Chat Import Bridge never mutates PG or Neo4j before explicit promotion.
- All destructive actions require backup validation + explicit flag.

## Model stack

| Role | Model | Provider |
|------|-------|----------|
| Primary reasoning | Qwen3:14b | Ollama (native) |
| Fast fallback | Llama3.1:8b | Ollama (native) |
| Embeddings | Nomic-embed-text | Ollama (native) |

Pull models:
```bash
ollama pull qwen3:14b && ollama pull llama3.1:8b && ollama pull nomic-embed-text
```

## Makefile targets

```bash
make doctor        # Preflight dependency check
make health        # Ping all 3 service health endpoints
make lint          # ruff check
make test          # Run test suite (229 tests)
make install       # Install shared packages
make install-all   # Install everything (packages + apps)
make tree          # Show source file tree
```

## Docs

| Document | Contents |
|----------|----------|
| [Setup](docs/SETUP.md) | Full setup guide |
| [Architecture](docs/ARCHITECTURE.md) | System design |
| [Operations](docs/OPERATIONS.md) | Daily operations |
| [Safety](docs/SAFETY.md) | Safety doctrine |
| [CLI](docs/CLI.md) | CLI tool reference |
| [API](docs/API_ENDPOINTS.md) | Full API reference |
| [Bridge](docs/CHAT_IMPORT_BRIDGE.md) | Import workflow |
| [Graph](docs/GRAPH_OPERATIONS.md) | Neo4j operations |
| [Backup](docs/BACKUP_RESTORE.md) | Backup/restore |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common issues |
