---
name: test-patterns
description: Pytest patterns, fixtures, and mocking conventions for Northstar Research tests
---
## Test Structure

All tests in `tests/` directory. Run with `make test` (calls `pytest tests/ -v`).

## Fixtures (`tests/conftest.py`)

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_db():
    db = AsyncMock(spec=PostgresRepository)
    db.get_project.return_value = ProjectRead(id=uuid4(), ...)
    return db

@pytest.fixture
def mock_llm_service():
    svc = AsyncMock(spec=LLMService)
    svc.extract_entities.return_value = [EntityCreate(...)]
    return svc

@pytest.fixture
def mock_neo4j():
    neo4j = AsyncMock(spec=Neo4jRepository)
    return neo4j

@pytest.fixture
def mock_vector_store():
    store = AsyncMock(spec=VectorStore)
    return store
```

## App Clients

```python
from httpx import AsyncClient, ASGITransport
from research_agent.main import app

@pytest.fixture
async def agent_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
```

## Test Class Pattern

```python
import pytest

class TestProjectAPI:
    """Tests for /api/v1/projects endpoints."""

    @pytest.mark.asyncio
    async def test_create_project(self, mock_db, agent_client):
        # Arrange
        mock_db.create_project.return_value = ProjectRead(id=uuid4(), ...)
        # Act
        response = await agent_client.post("/api/v1/projects", json={...})
        # Assert
        assert response.status_code == 201
```

## Safety Gate Tests

```python
class TestSafetyGateDefaults:
    @pytest.mark.asyncio
    async def test_destructive_cleanup_disabled_by_default(self, agent_client):
        response = await agent_client.delete("/api/v1/cleanup/sources")
        assert response.status_code == 403
```

## Mocking Rules

- Always use `AsyncMock` for async dependencies (DB, LLM, Neo4j, VectorStore)
- Use `spec=` for type-aware mocks
- Use `uuid.uuid4()` for test IDs
- Don't duplicate implementation logic in tests
- Test behavior, not implementation details
