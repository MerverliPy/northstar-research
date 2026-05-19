# API Endpoint Reference

## Research Agent (port 8099)

All routes prefixed with `/api/v1` unless otherwise noted.
All list endpoints enforce `limit` query param with `ge=1, le=1000`.

### Projects
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/projects/` | List projects |
| POST | `/api/v1/projects/` | Create project |
| GET | `/api/v1/projects/{id}` | Get project by ID |
| PUT | `/api/v1/projects/{id}` | Update project |
| DELETE | `/api/v1/projects/{id}` | Delete project |

### Sources
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/sources/` | List sources |
| POST | `/api/v1/sources/` | Create source |
| GET | `/api/v1/sources/{id}` | Get source by ID |
| DELETE | `/api/v1/sources/{id}` | Delete source |

### Entities
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/entities/` | List entities |
| POST | `/api/v1/entities/` | Create entity |
| GET | `/api/v1/entities/{id}` | Get entity by ID |
| PUT | `/api/v1/entities/{id}` | Update entity |
| DELETE | `/api/v1/entities/{id}` | Delete entity |

### Claims
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/claims/` | List claims |
| POST | `/api/v1/claims/` | Create claim |
| GET | `/api/v1/claims/{id}` | Get claim by ID |
| PUT | `/api/v1/claims/{id}` | Update claim |
| DELETE | `/api/v1/claims/{id}` | Delete claim |

### Reports
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/reports/` | List reports |
| POST | `/api/v1/reports/` | Create report |
| DELETE | `/api/v1/reports/{id}` | Delete report |

### Extraction
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/extraction/extract` | Trigger extraction (403 unless FORCE_GRAPH_EXTRACTION=true) |
| GET | `/api/v1/extraction/status/{id}` | Extraction status |

### Quality
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/quality/score` | Score source quality |

### Cleanup
| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/cleanup/report` | Dry-run cleanup report |
| POST | `/api/v1/cleanup/execute` | Execute cleanup (403 unless ENABLE_DESTRUCTIVE_CLEANUP=true) |

### Search
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/search` | Vector search |

### Scraping
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/scraping/scrape` | Scrape URL + optional extraction |

## Chat Import Bridge (port 3022)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/imports/paste` | Import content via paste |
| GET | `/api/v1/imports` | List staged imports |
| GET | `/api/v1/imports/{id}` | Get staged import |
| DELETE | `/api/v1/imports/{id}` | Delete staged import |
| GET | `/api/v1/export/{id}/markdown` | Export as Markdown |
| POST | `/api/v1/promotion/{id}` | Promote import to Agent (403 unless PROMOTION_ENABLED=true) |
| POST | `/api/v1/promotion/batch` | Promote all pending (403 unless PROMOTION_ENABLED=true) |

## Research Portal (port 3010)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/dashboard/` | Dashboard (HTML) |
| GET | `/quality/` | Quality scoring page (HTML) |
| GET/POST | `/cleanup/` | Cleanup report/execute (HTML) |
| GET/POST | `/extraction/` | Extraction gate (HTML) |
| GET | `/visual/` | Graph viewer (vis.js HTML) |
| GET | `/graph/data/{project_id}` | Graph JSON data |
| GET | `/api/settings` | Current safety gate settings |
| POST | `/api/chat` | AI chat orchestrator |
| ALL | `/api/v1/{path}` | API proxy to research-agent (whitelisted headers only) |

## Query Parameters

List endpoints accept:
- `limit`: integer, 1–1000 (default 50). Values outside range return 422.
- `offset`: integer (default 0).

Treat this file as an operator reference. Confirm actual routes against the running app before relying on them in automation.
