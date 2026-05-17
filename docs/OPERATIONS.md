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

## Stop conditions

Stop and inspect before continuing when:

- The agent health endpoint fails.
- The portal process is inactive.
- The watcher reports unknown graph status.
- Quality score falls below the configured minimum.
- Cleanup reports unexpectedly show duplicate or orphan candidates after a clean baseline.
- Any command proposes destructive cleanup without an explicit reviewed migration.
