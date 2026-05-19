import asyncio
import os
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, ASGITransport

from northstar_db import PostgresRepository, Neo4jRepository
from northstar_llm import LLMService, EmbeddingService
from northstar_vector import VectorStore

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings():
    os.environ["FORCE_GRAPH_EXTRACTION"] = "false"
    os.environ["ENABLE_DESTRUCTIVE_CLEANUP"] = "false"
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:15432/northstar_test"
    os.environ["NEO4J_URI"] = "bolt://localhost:17687"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:21434"
    return {
        "force_graph_extraction": False,
        "enable_destructive_cleanup": False,
    }


@pytest.fixture
def temp_chroma_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_llm_service():
    service = AsyncMock(spec=LLMService)
    service.generate = AsyncMock(return_value="mock response")
    service.generate_structured = AsyncMock()
    service.is_available = AsyncMock(return_value=True)
    service._primary_model = "qwen3:14b"
    service._fallback_model = "llama3.1:8b"
    yield service


@pytest.fixture
def mock_embedding_service():
    service = AsyncMock(spec=EmbeddingService)
    service.embed = AsyncMock(return_value=[0.1] * 768)
    service.embed_batch = AsyncMock(return_value=[[0.1] * 768])
    service.embed_dimension = AsyncMock(return_value=768)
    yield service


@pytest.fixture
def mock_db():
    repo = AsyncMock(spec=PostgresRepository)
    test_project_id = uuid.uuid4()
    test_source_id = uuid.uuid4()
    test_entity_id = uuid.uuid4()
    test_claim_id = uuid.uuid4()
    test_report_id = uuid.uuid4()

    _now = datetime.now(timezone.utc)

    class FakeProject:
        id = test_project_id
        name = "Test Project"
        description = "A test project"
        status = "active"
        created_at = _now
        updated_at = _now

    class FakeSource:
        id = test_source_id
        project_id = test_project_id
        title = "Test Source"
        content_type = "text"
        raw_content = "Test content"
        cleaned_content = None
        url = None
        created_at = _now
        updated_at = _now

    class FakeEntity:
        id = test_entity_id
        source_id = test_source_id
        name = "Test Entity"
        entity_type = "organization"
        description = "A test entity"
        confidence = 0.95
        created_at = _now
        updated_at = _now

    class FakeClaim:
        id = test_claim_id
        source_id = test_source_id
        entity_id = test_entity_id
        claim_text = "Test claim"
        claim_type = "fact"
        confidence = 0.9
        context = None
        created_at = _now
        updated_at = _now

    class FakeReport:
        id = test_report_id
        project_id = test_project_id
        title = "Test Report"
        summary = "A test report"
        created_at = _now
        updated_at = _now

    class FakeAnalysis:
        id = uuid.uuid4()
        source_id = test_source_id
        project_id = test_project_id
        analysis_type = "quality_score"
        content = {"score": 0.85, "reasoning": "good"}
        quality_score = 0.85
        model_used = "qwen3:14b"
        created_at = _now
        updated_at = _now

    class FakeExtractionLog:
        id = uuid.uuid4()
        source_id = test_source_id
        project_id = test_project_id
        status = "pending"
        entities_found = 0
        error_message = None
        started_at = None
        completed_at = None
        created_at = _now
        updated_at = _now

    repo.get_project = AsyncMock(return_value=FakeProject())
    repo.get_project_by_name = AsyncMock(return_value=FakeProject())
    repo.list_projects = AsyncMock(return_value=[FakeProject()])
    repo.create_project = AsyncMock(return_value=FakeProject())
    repo.update_project = AsyncMock(return_value=FakeProject())
    repo.delete_project = AsyncMock(return_value=True)

    repo.get_source = AsyncMock(return_value=FakeSource())
    repo.list_sources = AsyncMock(return_value=[FakeSource()])
    repo.create_source = AsyncMock(return_value=FakeSource())
    repo.delete_source = AsyncMock(return_value=True)

    repo.get_entity = AsyncMock(return_value=FakeEntity())
    repo.list_entities = AsyncMock(return_value=[FakeEntity()])
    repo.create_entity = AsyncMock(return_value=FakeEntity())
    repo.delete_entity = AsyncMock(return_value=True)
    repo.bulk_create_entities = AsyncMock(return_value=[FakeEntity()])

    repo.get_claim = AsyncMock(return_value=FakeClaim())
    repo.list_claims = AsyncMock(return_value=[FakeClaim()])
    repo.create_claim = AsyncMock(return_value=FakeClaim())
    repo.delete_claim = AsyncMock(return_value=True)
    repo.bulk_create_claims = AsyncMock(return_value=[FakeClaim()])

    repo.get_report = AsyncMock(return_value=FakeReport())
    repo.list_reports = AsyncMock(return_value=[FakeReport()])
    repo.create_report = AsyncMock(return_value=FakeReport())
    repo.delete_report = AsyncMock(return_value=True)

    repo.create_analysis = AsyncMock(return_value=FakeAnalysis())
    repo.list_analyses = AsyncMock(return_value=[FakeAnalysis()])

    repo.create_extraction_log = AsyncMock(return_value=FakeExtractionLog())
    repo.get_extraction_log = AsyncMock(return_value=FakeExtractionLog())
    repo.update_extraction_log = AsyncMock(return_value=FakeExtractionLog())

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = FakeExtractionLog()
    mock_session_instance = AsyncMock()
    mock_session_instance.execute = AsyncMock(return_value=mock_result)
    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__ = AsyncMock(return_value=mock_session_instance)
    mock_session_cm.__aexit__ = AsyncMock(return_value=None)
    repo._session = MagicMock(return_value=mock_session_cm)

    yield repo


@pytest.fixture
def mock_neo4j():
    repo = AsyncMock(spec=Neo4jRepository)
    repo.create_entity_node = AsyncMock()
    repo.create_claim_relationship = AsyncMock()
    repo.link_source_to_entity = AsyncMock()
    repo.get_entity_graph = AsyncMock(return_value={"nodes": [], "edges": [], "root_id": str(uuid.uuid4())})
    repo.get_project_graph = AsyncMock(return_value={"nodes": [], "edges": [], "project_id": str(uuid.uuid4())})
    repo.delete_entity_node = AsyncMock(return_value=True)
    repo.get_entity_count = AsyncMock(return_value=0)
    repo.get_relationship_count = AsyncMock(return_value=0)
    yield repo


@pytest.fixture
def mock_vector_store():
    store = AsyncMock(spec=VectorStore)
    store.initialize = AsyncMock()
    store.add_documents = AsyncMock(return_value=["doc1", "doc2"])
    store.search = AsyncMock(return_value=[])
    store.list_collections = AsyncMock(return_value=[])
    store.collection_count = AsyncMock(return_value=0)
    store.delete_collection = AsyncMock()
    store.delete_documents = AsyncMock()
    store.health = AsyncMock(return_value=True)
    yield store


@pytest.fixture
def mock_scraper():
    scraper = AsyncMock()
    scraper.scrape = AsyncMock(
        return_value=MagicMock(
            url="https://example.com",
            title="Mock Page",
            content="Mock extracted text content",
            word_count=5,
            fingerprint_seed=None,
            took_ms=100,
        )
    )
    scraper._enabled = True
    scraper._initialized = True
    yield scraper


@pytest.fixture
def agent_app(mock_db, mock_llm_service, mock_neo4j, mock_vector_store, mock_scraper, test_settings):
    with patch.multiple(
        "research_agent.dependencies",
        _db=mock_db,
        _llm=mock_llm_service,
        _neo4j=mock_neo4j,
        _vector_store=mock_vector_store,
        _scraper=mock_scraper,
    ), patch("research_agent.config.settings.force_graph_extraction", False), patch(
        "research_agent.config.settings.enable_destructive_cleanup", False
    ):
        from research_agent.main import app
        app.state.settings = MagicMock()
        app.state.settings.force_graph_extraction = False
        app.state.settings.enable_destructive_cleanup = False
        yield app


@pytest.fixture
def agent_client(agent_app):
    with patch("research_agent.main.lifespan", MagicMock()):
        transport = ASGITransport(app=agent_app)
        yield AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def bridge_app(test_settings):
    with patch("chat_import_bridge.database._engine", None), patch(
        "chat_import_bridge.database.init_staging_db", AsyncMock()
    ):
        from chat_import_bridge.main import app
        yield app


@pytest.fixture
def bridge_client(bridge_app):
    with patch("chat_import_bridge.main.lifespan", MagicMock()):
        transport = ASGITransport(app=bridge_app)
        yield AsyncClient(transport=transport, base_url="http://test")


@pytest.fixture
def portal_app(mock_db, mock_neo4j, test_settings):
    with patch.multiple(
        "research_portal.dependencies",
        _db=mock_db,
        _neo4j=mock_neo4j,
    ), patch("research_portal.config.settings.force_graph_extraction", False), patch(
        "research_portal.config.settings.enable_destructive_cleanup", False
    ):
        from research_portal.main import app

        templates_dir = Path(__file__).parent.parent / "apps" / "research-portal" / "research_portal" / "templates"
        if not templates_dir.exists():
            templates_dir.mkdir(parents=True, exist_ok=True)
            for tpl in ["dashboard.html", "quality.html", "cleanup.html", "extraction.html", "graph_viewer.html"]:
                tpl_path = templates_dir / tpl
                if not tpl_path.exists():
                    tpl_path.write_text(f"<html><body><h1>{tpl}</h1></body></html>")

        http_client = AsyncMock()
        http_client.request = AsyncMock(return_value=MagicMock(status_code=403, content=b'{"detail":"Forbidden"}', headers={}))

        app.state.settings = MagicMock()
        app.state.settings.force_graph_extraction = False
        app.state.settings.enable_destructive_cleanup = False
        app.state.settings.research_agent_url = "http://127.0.0.1:8099"
        app.state.http_client = http_client
        yield app


@pytest.fixture
def portal_client(portal_app):
    with patch("research_portal.main.lifespan", MagicMock()):
        transport = ASGITransport(app=portal_app)
        yield AsyncClient(transport=transport, base_url="http://test")
