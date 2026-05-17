---
description: Start Docker Compose services (PG + Neo4j)
---
Start the Docker Compose services (PostgreSQL 16 + Neo4j 5):

```
docker compose -f docker/docker-compose.yml up -d
```

Then verify:
- PostgreSQL is running on port 5432
- Neo4j is running on ports 7474 (HTTP) and 7687 (Bolt)

Report service status after startup.
