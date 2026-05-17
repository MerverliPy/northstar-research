# Repository Root Structure

This root scaffold is designed for a local AI research system with PostgreSQL as the durable record store, Neo4j as the graph visualization layer, and WSL-native operator services.

## Root files

| Path | Purpose |
|---|---|
| `README.md` | Project overview and first-run orientation. |
| `Makefile` | Safe operator shortcuts. Targets avoid destructive actions. |
| `.gitignore` | Prevents secrets, databases, logs, backups, exports, caches, and local runtime state from entering git. |
| `.gitattributes` | Normalizes text files and marks binary/document artifacts. |
| `.editorconfig` | Consistent whitespace and newline rules. |
| `LICENSE.md` | Placeholder all-rights-reserved license until an explicit license is selected. |
| `SECURITY.md` | Security posture and vulnerability reporting. |
| `CONTRIBUTING.md` | Contribution rules oriented around safety gates and local-first development. |
| `CHANGELOG.md` | Human-maintained release notes. |
| `ROADMAP.md` | Near-term implementation plan. |

## Major directories

| Directory | Purpose |
|---|---|
| `apps/` | Service-specific source trees. |
| `config/` | Example-only configuration. Never commit real `.env` files. |
| `docker/` | Docker Compose examples and runtime notes. |
| `docs/` | Operator manual, runbooks, decisions, and API references. |
| `scripts/` | Conservative helper scripts. |
| `sql/` | SQL migrations and schema notes. |
| `systemd/user/` | User service examples for WSL/systemd. |
| `tests/` | Unit/integration tests. |
| `tools/` | Local-only utility scripts. |

## Empty directory policy

Git does not track empty directories, so `.gitkeep` files are included in directories that are part of the intended structure but do not yet contain implementation files.
