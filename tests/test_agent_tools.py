from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from research_portal.services.agent_tools import AgentToolExecutor, TOOL_DEFINITIONS

pytestmark = pytest.mark.asyncio


def _mock_response(json_data, status_code=200):
    resp = MagicMock()
    resp.json = MagicMock(return_value=json_data)
    resp.raise_for_status = MagicMock()
    resp.status_code = status_code
    return resp


class TestAgentToolExecutor:
    async def test_start_and_close(self):
        tool = AgentToolExecutor()
        await tool.start()
        assert tool._client is not None
        await tool.close()
        assert tool._client is None

    async def test_client_not_started_raises(self):
        tool = AgentToolExecutor()
        with pytest.raises(RuntimeError, match="not started"):
            _ = tool.client

    async def test_unknown_tool_returns_error(self):
        tool = AgentToolExecutor()
        await tool.start()
        result = await tool.execute("nonexistent", {})
        assert "error" in result
        assert "Unknown tool" in result["error"]
        await tool.close()

    # ── Tool-specific tests ──

    async def test_tool_search(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"results": [{"id": "1"}]}))
        result = await tool.execute("search", {"query": "test", "project_id": "p1"})
        assert result["success"] is True
        tool._client.post.assert_called_once()
        call_args = tool._client.post.call_args
        assert "search" in call_args[0][0]
        assert call_args[1]["json"]["query"] == "test"
        assert call_args[1]["json"]["project_id"] == "p1"
        await tool.close()

    async def test_tool_list_projects(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.get = AsyncMock(return_value=_mock_response({"items": [], "total": 0}))
        result = await tool.execute("list_projects", {})
        assert result["success"] is True
        tool._client.get.assert_called_once()
        await tool.close()

    async def test_tool_list_sources(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.get = AsyncMock(return_value=_mock_response({"items": [], "total": 0}))
        result = await tool.execute("list_sources", {"project_id": "p1"})
        assert result["success"] is True
        tool._client.get.assert_called_once()
        await tool.close()

    async def test_tool_list_entities(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.get = AsyncMock(return_value=_mock_response({"items": [], "total": 0}))
        result = await tool.execute("list_entities", {"project_id": "p1"})
        assert result["success"] is True
        await tool.close()

    async def test_tool_list_claims(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.get = AsyncMock(return_value=_mock_response({"items": [], "total": 0}))
        result = await tool.execute("list_claims", {"source_id": "s1"})
        assert result["success"] is True
        await tool.close()

    async def test_tool_create_project(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"id": "new-id", "name": "Test"}))
        result = await tool.execute("create_project", {"name": "Test", "description": "Desc"})
        assert result["success"] is True
        await tool.close()

    async def test_tool_create_source(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"id": "s-id"}))
        result = await tool.execute("create_source", {
            "project_id": "p1", "title": "Src", "content": "text",
        })
        assert result["success"] is True
        await tool.close()

    async def test_tool_extract(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"status": "completed"}))
        result = await tool.execute("extract", {"source_id": "s1", "force": True})
        assert result["success"] is True
        call_url = tool._client.post.call_args[0][0]
        assert "force=true" in call_url
        await tool.close()

    async def test_tool_extract_force_defaults_false(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"status": "completed"}))
        result = await tool.execute("extract", {"source_id": "s1"})
        assert result["success"] is True
        call_url = tool._client.post.call_args[0][0]
        assert "force=false" in call_url
        await tool.close()

    async def test_tool_quality_score(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"score": 0.85}))
        result = await tool.execute("quality_score", {"source_id": "s1"})
        assert result["success"] is True
        await tool.close()

    async def test_tool_cleanup_report(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.get = AsyncMock(return_value=_mock_response({"summary": "ok"}))
        result = await tool.execute("cleanup_report", {})
        assert result["success"] is True
        await tool.close()

    async def test_tool_cleanup_execute(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"status": "done"}))
        result = await tool.execute("cleanup_execute", {})
        assert result["success"] is True
        await tool.close()

    async def test_tool_promote_import(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.post = AsyncMock(return_value=_mock_response({"status": "promoted"}))
        result = await tool.execute("promote_import", {"import_id": "123"})
        assert result["success"] is True
        assert "123" in tool._client.post.call_args[0][0]
        await tool.close()

    async def test_tool_get_stats(self):
        tool = AgentToolExecutor()
        await tool.start()
        paginated = {"items": [], "total": 5}
        tool._client.get = AsyncMock(return_value=_mock_response(paginated))
        result = await tool.execute("get_stats", {})
        assert result["success"] is True
        data = result["data"]
        assert data["projects"] == 5
        assert data["sources"] == 5
        assert data["entities"] == 5
        assert data["claims"] == 5
        await tool.close()

    # ── Error handling tests ──

    async def test_http_error_yields_failure(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
            "error", request=MagicMock(), response=MagicMock(status_code=500)
        ))
        result = await tool.execute("list_projects", {})
        assert result["success"] is False
        assert result["error"]
        await tool.close()

    async def test_network_error_yields_failure(self):
        tool = AgentToolExecutor()
        await tool.start()
        tool._client.get = AsyncMock(side_effect=httpx.ConnectError("no connection"))
        result = await tool.execute("list_projects", {})
        assert result["success"] is False
        await tool.close()


class TestToolDefinitions:
    def test_all_13_tools_defined(self):
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        assert len(tool_names) == 13
        assert "search" in tool_names
        assert "extract" in tool_names
        assert "get_stats" in tool_names
        assert "promote_import" in tool_names
