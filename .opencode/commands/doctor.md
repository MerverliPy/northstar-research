---
description: Full project health check
---
Run the full project health check:

1. `make doctor` — environment validation
2. `make health` — service health (PG, Neo4j)
3. `make check-secrets` — secrets scan
4. `make lint` — code quality
5. `make test` — test suite

Report any issues found. If all pass, confirm the project is healthy.
