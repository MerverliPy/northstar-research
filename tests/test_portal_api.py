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
        pytest.skip("Dashboard needs template rendering with real DB data")


class TestQualityPage:
    async def test_quality_page_renders(self, portal_client):
        pytest.skip("Quality page needs template rendering with real DB data")


class TestCleanupPage:
    async def test_cleanup_page_renders(self, portal_client):
        pytest.skip("Cleanup page needs template rendering with real DB data")


class TestExtractionPage:
    async def test_extraction_page_renders(self, portal_client):
        pytest.skip("Extraction page needs template rendering with real DB data")


class TestGraphPage:
    async def test_graph_page_renders(self, portal_client):
        pytest.skip("Graph page needs template rendering with real DB data")


class TestSafetyGates:
    async def test_extraction_trigger_403(self, portal_client):
        sid = uuid.uuid4()
        response = await portal_client.post(f"/extraction/trigger/{sid}")
        assert response.status_code == 403

    async def test_extraction_trigger_source_not_found(self, portal_client):
        pytest.skip("Extraction trigger needs httpx real call to agent")

    async def test_cleanup_execute_403(self, portal_client):
        response = await portal_client.post("/cleanup/execute")
        assert response.status_code == 403


class TestGraphData:
    async def test_graph_data(self, portal_client):
        pid = uuid.uuid4()
        response = await portal_client.get(f"/graph/data/{pid}")
        assert response.status_code == 200
        data = response.json()
        assert "nodes" in data
        assert "edges" in data
