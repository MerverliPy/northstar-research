import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health_endpoint(self, agent_client):
        response = await agent_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "research-agent"


class TestProjectsAPI:
    async def test_list_projects(self, agent_client):
        response = await agent_client.get("/api/v1/projects/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_create_project(self, agent_client):
        response = await agent_client.post(
            "/api/v1/projects/",
            json={"name": "Test Project", "description": "A test project"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data

    async def test_get_project(self, agent_client):
        pid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/projects/{pid}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    async def test_get_project_not_found(self, agent_client, mock_db):
        mock_db.get_project.return_value = None
        pid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/projects/{pid}")
        assert response.status_code == 404

    async def test_update_project(self, agent_client):
        pid = uuid.uuid4()
        response = await agent_client.put(
            f"/api/v1/projects/{pid}",
            json={"name": "Updated", "status": "active"},
        )
        assert response.status_code == 200

    async def test_update_project_not_found(self, agent_client, mock_db):
        mock_db.update_project.return_value = None
        pid = uuid.uuid4()
        response = await agent_client.put(
            f"/api/v1/projects/{pid}",
            json={"name": "Updated"},
        )
        assert response.status_code == 404

    async def test_delete_project(self, agent_client):
        pid = uuid.uuid4()
        response = await agent_client.delete(f"/api/v1/projects/{pid}")
        assert response.status_code == 204

    async def test_delete_project_not_found(self, agent_client, mock_db):
        mock_db.delete_project.return_value = False
        pid = uuid.uuid4()
        response = await agent_client.delete(f"/api/v1/projects/{pid}")
        assert response.status_code == 404


class TestSourcesAPI:
    async def test_list_sources(self, agent_client):
        pid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/sources/?project_id={pid}")
        assert response.status_code == 200

    async def test_create_source(self, agent_client):
        pid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/sources/",
            json={
                "project_id": str(pid),
                "title": "Test Source",
                "content_type": "text",
                "raw_content": "content",
            },
        )
        assert response.status_code == 201

    async def test_get_source(self, agent_client):
        sid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/sources/{sid}")
        assert response.status_code == 200

    async def test_get_source_not_found(self, agent_client, mock_db):
        mock_db.get_source.return_value = None
        sid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/sources/{sid}")
        assert response.status_code == 404

    async def test_delete_source(self, agent_client):
        sid = uuid.uuid4()
        response = await agent_client.delete(f"/api/v1/sources/{sid}")
        assert response.status_code == 204

    async def test_delete_source_not_found(self, agent_client, mock_db):
        mock_db.delete_source.return_value = False
        sid = uuid.uuid4()
        response = await agent_client.delete(f"/api/v1/sources/{sid}")
        assert response.status_code == 404


class TestExtractionAPI:
    async def test_extraction_gate_403(self, agent_client, mock_db):
        sid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid), "force": False},
        )
        assert response.status_code == 403

    async def test_extraction_with_force(self, agent_client):
        sid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid), "force": True},
        )
        assert response.status_code == 403

    async def test_extraction_source_not_found(self, agent_client, mock_db):
        mock_db.get_source.return_value = None
        sid = uuid.uuid4()
        with patch("research_agent.config.settings.force_graph_extraction", True):
            response = await agent_client.post(
                "/api/v1/extraction/extract",
                json={"source_id": str(sid), "force": True},
            )
        assert response.status_code == 404

    async def test_extraction_status(self, agent_client):
        eid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/extraction/status/{eid}")
        assert response.status_code == 200

    async def test_extraction_status_not_found(self, agent_client, mock_db):
        mock_db._session.return_value.__aenter__.return_value.execute.return_value.scalar_one_or_none.return_value = None
        eid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/extraction/status/{eid}")
        assert response.status_code == 404

    async def test_extraction_queue(self, agent_client):
        response = await agent_client.get("/api/v1/extraction/queue")
        assert response.status_code == 200


class TestQualityAPI:
    async def test_score_quality(self, agent_client, mock_llm_service):
        mock_llm_service.generate_structured.return_value = MagicMock(score=0.85, reasoning="good")
        sid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/quality/score",
            json={
                "source_id": str(sid),
                "content": "test content",
                "criteria": {"relevance": "high"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "score" in data

    async def test_quality_history(self, agent_client):
        sid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/quality/history?source_id={sid}")
        assert response.status_code == 200


class TestCleanupAPI:
    async def test_cleanup_report(self, agent_client):
        response = await agent_client.get("/api/v1/cleanup/report")
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data

    async def test_cleanup_execute_403(self, agent_client):
        response = await agent_client.post("/api/v1/cleanup/execute")
        assert response.status_code == 403


class TestSearchAPI:
    async def test_search(self, agent_client, mock_vector_store):
        mock_vector_store.search.return_value = []
        pid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/search/",
            json={"query": "test", "project_id": str(pid)},
        )
        assert response.status_code == 200
        assert response.json() == []


class TestEntitiesAPI:
    async def test_list_entities(self, agent_client):
        response = await agent_client.get("/api/v1/entities/")
        assert response.status_code == 200

    async def test_create_entity(self, agent_client):
        response = await agent_client.post(
            "/api/v1/entities/",
            json={"name": "Test Entity", "entity_type": "organization"},
        )
        assert response.status_code == 201

    async def test_get_entity(self, agent_client):
        eid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/entities/{eid}")
        assert response.status_code == 200

    async def test_get_entity_not_found(self, agent_client, mock_db):
        mock_db.get_entity.return_value = None
        eid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/entities/{eid}")
        assert response.status_code == 404

    async def test_delete_entity(self, agent_client):
        eid = uuid.uuid4()
        response = await agent_client.delete(f"/api/v1/entities/{eid}")
        assert response.status_code == 204


class TestClaimsAPI:
    async def test_list_claims(self, agent_client):
        response = await agent_client.get("/api/v1/claims/")
        assert response.status_code == 200

    async def test_create_claim(self, agent_client):
        response = await agent_client.post(
            "/api/v1/claims/",
            json={"claim_text": "Test claim"},
        )
        assert response.status_code == 201

    async def test_get_claim(self, agent_client):
        cid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/claims/{cid}")
        assert response.status_code == 200

    async def test_get_claim_not_found(self, agent_client, mock_db):
        mock_db.get_claim.return_value = None
        cid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/claims/{cid}")
        assert response.status_code == 404

    async def test_delete_claim(self, agent_client):
        cid = uuid.uuid4()
        response = await agent_client.delete(f"/api/v1/claims/{cid}")
        assert response.status_code == 204


class TestReportsAPI:
    async def test_list_reports(self, agent_client):
        pid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/reports/?project_id={pid}")
        assert response.status_code == 200

    async def test_create_report(self, agent_client):
        pid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/reports/",
            json={"project_id": str(pid), "title": "Test Report"},
        )
        assert response.status_code == 201

    async def test_get_report(self, agent_client):
        rid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/reports/{rid}")
        assert response.status_code == 200

    async def test_get_report_not_found(self, agent_client, mock_db):
        mock_db.get_report.return_value = None
        rid = uuid.uuid4()
        response = await agent_client.get(f"/api/v1/reports/{rid}")
        assert response.status_code == 404

    async def test_delete_report(self, agent_client):
        rid = uuid.uuid4()
        response = await agent_client.delete(f"/api/v1/reports/{rid}")
        assert response.status_code == 204
