import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

pytestmark = pytest.mark.asyncio


class TestHealth:
    async def test_health_endpoint(self, portal_client):
        response = await portal_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "research-portal"


class TestDashboard:
    async def test_dashboard_renders(self, portal_client):
        response = await portal_client.get("/dashboard")
        assert response.status_code in (200, 307)


class TestQualityPage:
    async def test_quality_page_renders(self, portal_client):
        response = await portal_client.get("/quality")
        assert response.status_code == 200
        assert len(response.text) > 0


class TestCleanupPage:
    async def test_cleanup_page_renders(self, portal_client):
        response = await portal_client.get("/cleanup")
        assert response.status_code == 200
        assert len(response.text) > 0


class TestExtractionPage:
    async def test_extraction_page_renders(self, portal_client):
        response = await portal_client.get("/extraction")
        assert response.status_code == 200
        assert len(response.text) > 0


class TestGraphPage:
    async def test_graph_page_renders(self, portal_client):
        response = await portal_client.get("/visual")
        assert response.status_code == 200
        assert len(response.text) > 0


class TestSafetyGates:
    async def test_extraction_trigger_403(self, portal_client):
        sid = uuid.uuid4()
        response = await portal_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid)},
        )
        assert response.status_code == 403

    async def test_extraction_trigger_source_not_found(self, portal_client):
        sid = uuid.uuid4()
        response = await portal_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid)},
        )
        assert response.status_code in (403, 404, 502, 503)

    async def test_cleanup_execute_403(self, portal_client):
        response = await portal_client.post("/api/v1/cleanup/execute")
        assert response.status_code == 403


class TestGraphData:
    async def test_graph_data(self, portal_client):
        pid = uuid.uuid4()
        response = await portal_client.get(f"/graph/data/{pid}")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
