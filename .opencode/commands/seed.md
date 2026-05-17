---
description: Seed PostgreSQL database with test data
---
Seed the PostgreSQL database with test data.

Option 1 (SQL file): `psql $DATABASE_URL -f sql/seed.sql`
Option 2 (using research-agent API): `curl -X POST http://localhost:8099/api/v1/projects` and related endpoints

First check:
- PostgreSQL is running (port 5432)
- Migrations are up to date (`/migrate`)

Report what data was seeded.
