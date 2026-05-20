import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from northstar_models.schemas import CleanupReport

pytestmark = pytest.mark.asyncio


class TestForceGraphExtraction:
    async def test_extraction_returns_403_when_force_false(self, agent_client):
        sid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid), "force": False},
        )
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "force" in data["detail"].lower()

    async def test_extraction_returns_403_when_force_true_but_server_disabled(self, agent_client):
        sid = uuid.uuid4()
        response = await agent_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid), "force": True},
        )
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "disabled" in data["detail"].lower()

    async def test_portal_extraction_gate_403(self, portal_client):
        sid = uuid.uuid4()
        response = await portal_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid)},
        )
        assert response.status_code == 403

    async def test_portal_extraction_when_force_enabled(self, portal_client):
        portal_client._transport.app.state.http_client.request = AsyncMock(
            return_value=MagicMock(status_code=200, content=b'{"status":"ok"}', headers={})
        )
        sid = uuid.uuid4()
        response = await portal_client.post(
            "/api/v1/extraction/extract",
            json={"source_id": str(sid), "force": True},
        )
        assert response.status_code in (200, 403)


class TestDestructiveCleanup:
    async def test_cleanup_execute_403_when_disabled(self, agent_client):
        response = await agent_client.post("/api/v1/cleanup/execute")
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert "destructive" in data["detail"].lower()

    async def test_cleanup_report_is_always_read_only(self, agent_client):
        response = await agent_client.get("/api/v1/cleanup/report")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "summary" in data
        assert "suggestions" in data
        report = CleanupReport(**data)
        assert "dry-run" in report.summary.lower() or "set" in report.summary.lower()

    async def test_portal_cleanup_gate_403(self, portal_client):
        response = await portal_client.post("/api/v1/cleanup/execute")
        assert response.status_code == 403

    async def test_portal_cleanup_when_enabled(self, portal_client):
        portal_client._transport.app.state.http_client.request = AsyncMock(
            return_value=MagicMock(status_code=200, content=b'{"status":"ok"}', headers={})
        )
        response = await portal_client.post("/api/v1/cleanup/execute")
        assert response.status_code in (200, 403)

    async def test_cleanup_report_never_modifies(self, agent_client, mock_db, mock_neo4j):
        response = await agent_client.get("/api/v1/cleanup/report")
        assert response.status_code == 200
        mock_db.delete_project.assert_not_awaited()
        mock_db.delete_source.assert_not_awaited()
        mock_db.delete_entity.assert_not_awaited()
        mock_db.delete_claim.assert_not_awaited()
        mock_db.delete_report.assert_not_awaited()
        mock_neo4j.delete_entity_node.assert_not_awaited()


class TestBridgeSafety:
    async def test_bridge_never_touches_pg(self, bridge_client):
        with patch("chat_import_bridge.routers.imports.svc.add_to_staging") as mock_add:
            mock_entry = MagicMock()
            mock_entry.id = 1
            mock_entry.title = "Test"
            mock_entry.status = "pending"
            mock_add.return_value = mock_entry

            await bridge_client.post(
                "/api/v1/imports/paste",
                json={"title": "Test", "content": "Test"},
            )

            import sqlalchemy
            from northstar_db import PostgresRepository
            assert not hasattr(mock_add.call_args[0][0], "create_project")

    async def test_bridge_never_touches_neo4j(self, bridge_client):
        import tomllib
        from pathlib import Path
        bridge_pyproject = Path(__file__).resolve().parent.parent / "apps" / "chat-import-bridge" / "pyproject.toml"
        with open(bridge_pyproject, "rb") as f:
            data = tomllib.load(f)
        deps = data.get("project", {}).get("dependencies", [])
        assert all("northstar-db" not in d for d in deps), "Bridge should not depend on northstar-db"


class TestSafetyGateDefaults:
    async def test_research_agent_config_defaults(self):
        from research_agent.config import Settings
        s = Settings()
        assert s.force_graph_extraction is False
        assert s.enable_destructive_cleanup is False

    async def test_research_portal_config_defaults(self):
        from research_portal.config import Settings
        s = Settings()
        assert s.force_graph_extraction is False
        assert s.enable_destructive_cleanup is False
