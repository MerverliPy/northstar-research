# BUILD CONTRACT — Northstar Research

## Wave Progress

| Wave | Status | Agents |
|---|---|---|
| 0: Shared Foundation | ❌ Not started | (none yet) |
| 1: Infrastructure | ❌ Not started | foundation, schema, gitops |
| 2: Three Services | ❌ Not started | agent-smith, bridge, portal |
| 3: Tests + Hardening | ❌ Not started | qa, shield |

## Last Completed Wave

None — build has not started.

## Safety Flags

| Flag | Default | Current |
|---|---|---|
| FORCE_GRAPH_EXTRACTION | false | false |
| ENABLE_DESTRUCTIVE_CLEANUP | false | false |

## Port Assignments

| Service | Port |
|---|---|
| Research Agent | 8099 |
| Chat Import Bridge | 3022 |
| Research Portal | 3010 |
| PostgreSQL | 5432 |
| Neo4j | 7687 |

## Model Stack

| Role | Model |
|---|---|
| Primary reasoning | Qwen3:14b |
| Fast fallback | Llama3.1:8b |
| Embeddings | Nomic-embed-text |

## Next Action

Start Wave 0: Build shared foundation packages.
