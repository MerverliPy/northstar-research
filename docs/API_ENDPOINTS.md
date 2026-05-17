# API Endpoint Reference

## Research Agent

```text
GET /health
GET /knowledge/quality/report
GET /knowledge/quality/project/{project_id}/report
GET /knowledge/cleanup/report
GET /knowledge/cleanup/project/{project_id}/report
```

## Research Portal

```text
GET /knowledge/dashboard
GET /knowledge/quality
GET /knowledge/cleanup
GET /knowledge/auto-extract
GET /knowledge/auto-extract/watcher
GET /knowledge/visual2/project/{project_id}
GET /api/knowledge/status
```

## Chat Import Bridge

```text
GET  /health
GET  /chat-import
POST /api/chat-imports
GET  /api/chat-imports
GET  /api/chat-imports/{id}
GET  /api/chat-imports/{id}/export
POST /api/chat-imports/{id}/status
```

Treat this file as an operator reference. Confirm actual routes against the running app before relying on them in automation.
