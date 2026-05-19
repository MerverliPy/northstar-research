# Chat Import Bridge

## Purpose

The Chat Import Bridge stages useful AI chat transcripts before they are promoted into durable research projects.

Safe v1 workflow:

```text
AI chat transcript
  -> manual paste/import
  -> staged import queue
  -> Markdown export packet
  -> reviewed promotion into a research project
```

## Design boundaries

The bridge should not:

- Automatically scrape every chat.
- Automatically promote every staged chat.
- Mutate PostgreSQL or Neo4j before an explicit promotion step.
- Run graph extraction directly.

## Known v1 shape

| Item | Value |
|---|---|
| Service | `chat-import-bridge` |
| Default port | `3022` |
| UI route | `/chat-import` |
| Health route | `/health` |
| Staging storage | SQLite or local file-backed queue |
| Export format | Markdown |

## Core routes

```text
GET  /health
GET  /chat-import
POST /api/chat-imports
GET  /api/chat-imports
GET  /api/chat-imports/{id}
GET  /api/chat-imports/{id}/export
POST /api/chat-imports/{id}/status
```

## Promotion safety gate

Promotion endpoints (`/api/v1/promotion/{id}` and `/api/v1/promotion/batch`) are gated behind the `PROMOTION_ENABLED` environment variable (defaults to `false`). When disabled, both endpoints return HTTP 403.

To enable promotion:

```bash
export PROMOTION_ENABLED=true
# or set in apps/chat-import-bridge/.env:
PROMOTION_ENABLED=true
```

## Promotion guardrails

Before a staged transcript becomes a research project:

- Confirm the transcript is worth preserving.
- Enable `PROMOTION_ENABLED=true` in the bridge configuration.
- Add a clear topic and notes.
- Generate a Markdown export packet.
- Promote into PostgreSQL through an explicit reviewed path.
- Use the watcher and controlled gate for graph extraction after research completion.
