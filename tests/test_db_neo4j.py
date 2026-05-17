import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from northstar_db.neo4j_repo import GraphError, Neo4jRepository
from northstar_models.models import Claim, Entity
from northstar_models.enums import EntityType

pytestmark = pytest.mark.asyncio


def neo4j_available():
    try:
        import neo4j
        return True
    except ImportError:
        return False


class TestNeo4jInit:
    async def test_uninitialized_raises(self):
        repo = Neo4jRepository(uri="bolt://localhost:7687")
        repo._driver = None
        with pytest.raises(GraphError, match="not initialized"):
            repo._session()

    async def test_initialized_ok(self):
        repo = Neo4jRepository(uri="bolt://localhost:7687")
        repo._driver = MagicMock()
        session = repo._session()
        assert session is not None


class TestNeo4jWithMocks:
    @pytest.fixture
    def repo(self):
        r = Neo4jRepository(uri="bolt://localhost:7687")
        mock_driver = MagicMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()
        mock_session.run = AsyncMock()
        mock_driver.session = MagicMock(return_value=mock_session)
        r._driver = mock_driver
        return r

    async def test_create_entity_node(self, repo):
        entity = Entity(
            id=uuid.uuid4(),
            name="TestOrg",
            entity_type=EntityType.ORGANIZATION,
            source_id=uuid.uuid4(),
            description="A test org",
        )
        await repo.create_entity_node(entity)
        repo._driver.session().run.assert_awaited_once()

    async def test_create_entity_node_no_source(self, repo):
        entity = Entity(
            id=uuid.uuid4(),
            name="Concept",
            entity_type=EntityType.CONCEPT,
            source_id=None,
            description=None,
        )
        await repo.create_entity_node(entity)
        repo._driver.session().run.assert_awaited_once()

    async def test_create_claim_relationship(self, repo):
        claim = Claim(
            id=uuid.uuid4(),
            source_id=uuid.uuid4(),
            entity_id=uuid.uuid4(),
            claim_text="Test claim",
            claim_type="fact",
            confidence=0.9,
        )
        await repo.create_claim_relationship(claim)
        assert repo._driver.session().run.await_count >= 2

    async def test_create_claim_relationship_no_entity(self, repo):
        claim = Claim(
            id=uuid.uuid4(),
            source_id=uuid.uuid4(),
            entity_id=None,
            claim_text="Test claim",
        )
        await repo.create_claim_relationship(claim)
        repo._driver.session().run.assert_awaited_once()

    async def test_link_source_to_entity(self, repo):
        await repo.link_source_to_entity(
            source_id=uuid.uuid4(),
            entity_id=uuid.uuid4(),
            relationship_type="MENTIONS",
        )
        repo._driver.session().run.assert_awaited_once()

    async def test_get_entity_graph(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_run.return_value.single = AsyncMock(return_value=None)
        result = await repo.get_entity_graph(uuid.uuid4())
        assert result["nodes"] == []
        assert result["edges"] == []

    async def test_get_entity_graph_with_data(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_node = MagicMock()
        mock_node.get = lambda k, d=None: {
            "id": str(uuid.uuid4()),
            "name": "Test",
        }.get(k, d)
        mock_node.labels = {"Entity"}
        mock_record = MagicMock()
        mock_record.get = lambda k, d=None: [mock_node]
        mock_run.return_value.single = AsyncMock(return_value=mock_record)
        result = await repo.get_entity_graph(uuid.uuid4())
        assert len(result["nodes"]) > 0

    async def test_delete_entity_node_true(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_record = MagicMock()
        mock_record.get = lambda k, d=None: 1
        mock_run.return_value.single = AsyncMock(return_value=mock_record)
        result = await repo.delete_entity_node(uuid.uuid4())
        assert result is True

    async def test_delete_entity_node_false(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_record = MagicMock()
        mock_record.get = lambda k, d=None: 0
        mock_run.return_value.single = AsyncMock(return_value=mock_record)
        result = await repo.delete_entity_node(uuid.uuid4())
        assert result is False

    async def test_get_project_graph(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_run.return_value.single = AsyncMock(return_value=None)
        result = await repo.get_project_graph(uuid.uuid4())
        assert "project_id" in result

    async def test_get_project_graph_with_data(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_node = MagicMock()
        mock_node.get = lambda k, d=None: str(uuid.uuid4())
        mock_node.labels = {"Source"}
        mock_rel = MagicMock()
        mock_rel.start_node.get = lambda k, d=None: "start"
        mock_rel.end_node.get = lambda k, d=None: "end"
        mock_rel.type = "MENTIONS"
        mock_rel.__iter__ = lambda self: iter({}.items())
        mock_record = MagicMock()
        mock_record.get = lambda k, d=None: {
            "source_nodes": [mock_node],
            "entity_nodes": [],
            "rels": [mock_rel],
        }.get(k, d)
        mock_run.return_value.single = AsyncMock(return_value=mock_record)
        result = await repo.get_project_graph(uuid.uuid4())
        assert len(result["nodes"]) > 0
        assert len(result["edges"]) > 0

    async def test_clear_project_graph(self, repo):
        await repo.clear_project_graph(uuid.uuid4())
        repo._driver.session().__aenter__.return_value.run.assert_awaited_once()

    async def test_get_entity_count(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_record = MagicMock()
        mock_record.get = lambda k, d=None: 42
        mock_run.return_value.single = AsyncMock(return_value=mock_record)
        count = await repo.get_entity_count()
        assert count == 42

    async def test_get_relationship_count(self, repo):
        mock_run = repo._driver.session().__aenter__.return_value.run
        mock_record = MagicMock()
        mock_record.get = lambda k, d=None: 7
        mock_run.return_value.single = AsyncMock(return_value=mock_record)
        count = await repo.get_relationship_count()
        assert count == 7

    async def test_query_entities_by_type(self, repo):
        mock_session = repo._driver.session()
        mock_node = MagicMock()
        mock_node.get = lambda k, d=None: str(uuid.uuid4())
        mock_node.labels = {"Entity"}
        mock_record = MagicMock()
        mock_record.get = lambda k, d=None: mock_node

        class FakeCursor:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration

        mock_session.__aenter__.return_value.run.return_value = FakeCursor()
        repo._driver.session = MagicMock(return_value=mock_session)
        results = await repo.query_entities_by_type("organization")
        assert results == []

    async def test_find_paths(self, repo):
        mock_session = repo._driver.session()
        class FakeCursor:
            def __aiter__(self):
                return self
            async def __anext__(self):
                raise StopAsyncIteration
        mock_session.__aenter__.return_value.run.return_value = FakeCursor()
        repo._driver.session = MagicMock(return_value=mock_session)
        paths = await repo.find_paths(uuid.uuid4(), uuid.uuid4())
        assert paths == []

    async def test_link_entities_with_props(self, repo):
        await repo.link_entities(
            entity_id_1=uuid.uuid4(),
            entity_id_2=uuid.uuid4(),
            relationship_type="RELATES_TO",
            properties={"strength": 0.8},
        )
        repo._driver.session().run.assert_awaited_once()

    async def test_link_entities_without_props(self, repo):
        await repo.link_entities(
            entity_id_1=uuid.uuid4(),
            entity_id_2=uuid.uuid4(),
            relationship_type="RELATES_TO",
        )
        repo._driver.session().run.assert_awaited_once()
