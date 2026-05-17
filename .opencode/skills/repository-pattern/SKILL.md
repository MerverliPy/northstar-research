---
name: repository-pattern
description: PostgresRepository and Neo4jRepository patterns for Northstar Research database operations
---
## Repository Pattern

Both `PostgresRepository` and `Neo4jRepository` encapsulate all database operations.

### PostgresRepository (`northstar_db/postgres.py`)

```python
class PostgresRepository:
    def __init__(self, dsn: str):
        ...

    # Session-per-operation pattern
    async def _session(self):
        async with async_sessionmaker(...)() as session:
            yield session

    # CRUD naming convention
    async def create_project(self, session, data: ProjectCreate) -> ProjectRead: ...
    async def get_project(self, project_id: UUID) -> ProjectRead | None: ...
    async def list_projects(self, session, skip=0, limit=100) -> list[ProjectRead]: ...
    async def update_project(self, session, project_id, data: ProjectUpdate) -> ProjectRead: ...
    async def delete_project(self, session, project_id) -> bool: ...
    async def bulk_create_entities(self, session, entities: list[EntityCreate]) -> list[EntityRead]: ...
```

### Neo4jRepository (`northstar_db/neo4j.py`)

```python
class Neo4jRepository:
    # Graph operations
    async def create_graph_node(self, entity: EntityRead) -> None: ...
    async def create_graph_relationship(self, from_id, to_id, rel_type: str) -> None: ...
    async def get_graph_for_project(self, project_id: UUID) -> dict: ...
```

### Usage in Routers

```python
@router.post("/projects", response_model=ProjectRead)
async def create_project(data: ProjectCreate, db: PostgresRepository = Depends(get_db)):
    async with db._session() as session:
        return await db.create_project(session, data)
```

### Test Mocking

```python
mock_db = AsyncMock(spec=PostgresRepository)
mock_db.create_project.return_value = ProjectRead(id=uuid4(), name="test", ...)
```
