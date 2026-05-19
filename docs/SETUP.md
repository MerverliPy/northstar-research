# Setup

This repository is a scaffold for Northstar Research. It is safe to add to a fresh GitHub repository or use as a documentation/ops root for an existing Northstar Research checkout.

## Requirements

- Linux or WSL2
- Docker and Docker Compose
- Python 3.11+
- PostgreSQL client tools (`pg_dump`, `pg_restore`) for backup/restore
- systemd user services enabled if running native WSL services
- Tailscale if exposing local dashboards to a tailnet

## Initial local setup

```bash
git clone <repo-url> northstar-research
cd northstar-research
cp config/.env.example .env
# Edit .env — set NEO4J_PASSWORD, configure safety gates
make doctor
```

## Existing system setup

For an existing local install, copy files selectively:

```bash
rsync -av --exclude '.git' northstar-research/ ~/northstar-research/
cd ~/northstar-research
make doctor
```

Review any file that could overlap with existing scripts or service files before overwriting.

## Configuration

Use `config/.env.example` as the template. Keep real `.env` values local and untracked.

### Required settings

| Variable | Notes |
|---|---|
| `NEO4J_PASSWORD` | Must be explicitly configured (no default). Must match `docker-compose.yml` `NEO4J_AUTH` value. |
| `FORCE_GRAPH_EXTRACTION` | Set to `true` only when intentionally rebuilding graphs. |
| `ENABLE_DESTRUCTIVE_CLEANUP` | Set to `true` only for reviewed cleanup migrations. |
| `PROMOTION_ENABLED` | Set to `true` to enable chat-import promotion to Agent. |

### Container hardening

The Dockerfile runs all services as non-root `appuser`. Docker-compose services use `restart: unless-stopped` with Neo4j healthcheck enabled.
