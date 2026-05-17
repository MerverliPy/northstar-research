---
description: Run Alembic migrations for research-agent
---
Run Alembic migrations for the research-agent:

1. `cd apps/research-agent && alembic upgrade head`

If that fails, check:
- PostgreSQL is running (docker compose up -d)
- DATABASE_URL env var is set
- Migration files exist in `apps/research-agent/migrations/versions/`

To create a new migration:
`cd apps/research-agent && alembic revision --autogenerate -m "$ARGUMENTS"`
