from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from research_portal.services.orchestrator import Orchestrator

pytestmark = pytest.mark.asyncio


def _llm_response(plan: list[dict] | str) -> MagicMock:
    if isinstance(plan, list):
        body = '{"plan": ' + str(plan).replace("'", '"') + '}'
    else:
        body = plan
    resp = MagicMock()
    resp.json = MagicMock(return_value={"response": body})
    resp.raise_for_status = MagicMock()
    return resp


class TestOrchestrator:
    async def test_start_and_close(self):
        orch = Orchestrator()
        await orch.start()
        assert orch._llm_client is not None
        assert orch._tool_executor._client is not None
        await orch.close()
        assert orch._llm_client is None

    async def test_orchestrate_valid_plan(self):
        orch = Orchestrator()
        await orch.start()

        orch._llm_client.post = AsyncMock(
            return_value=_llm_response([{"tool": "list_projects", "args": {}}])
        )
        orch._tool_executor.execute = AsyncMock(
            return_value={"success": True, "data": {"items": [], "total": 3}}
        )

        events = []
        async for event in orch.orchestrate("list my projects"):
            events.append(event)

        event_types = [e["event"] for e in events]
        assert "thinking" in event_types
        assert "action" in event_types
        assert "result" in event_types
        assert "done" in event_types
        await orch.close()

    async def test_orchestrate_llm_failure(self):
        orch = Orchestrator()
        await orch.start()

        orch._llm_client.post = AsyncMock(side_effect=httpx.ConnectError("down"))

        events = []
        async for event in orch.orchestrate("do something"):
            events.append(event)

        assert events[1]["event"] == "error"
        assert "LLM call failed" in events[1]["data"]["message"]
        await orch.close()

    async def test_orchestrate_invalid_json(self):
        orch = Orchestrator()
        await orch.start()

        orch._llm_client.post = AsyncMock(
            return_value=_llm_response("not json at all")
        )

        events = []
        async for event in orch.orchestrate("bad request"):
            events.append(event)

        assert events[1]["event"] == "error"
        await orch.close()

    async def test_orchestrate_json_in_code_block(self):
        orch = Orchestrator()
        await orch.start()

        orch._llm_client.post = AsyncMock(
            return_value=_llm_response(
                '```json\n{"plan": [{"tool": "get_stats", "args": {}}]}\n```'
            )
        )
        orch._tool_executor.execute = AsyncMock(
            return_value={"success": True, "data": {"projects": 1, "sources": 2, "entities": 3, "claims": 4}}
        )

        events = []
        async for event in orch.orchestrate("stats"):
            events.append(event)

        done_events = [e for e in events if e["event"] == "done"]
        assert len(done_events) == 1
        await orch.close()

    async def test_orchestrate_empty_plan(self):
        orch = Orchestrator()
        await orch.start()

        orch._llm_client.post = AsyncMock(
            return_value=_llm_response('{"plan": []}')
        )

        events = []
        async for event in orch.orchestrate("nothing"):
            events.append(event)

        done = [e for e in events if e["event"] == "done"]
        assert len(done) == 1
        await orch.close()

    async def test_orchestrate_tool_failure_mid_plan(self):
        orch = Orchestrator()
        await orch.start()

        orch._llm_client.post = AsyncMock(
            return_value=_llm_response([
                {"tool": "search", "args": {"query": "test"}},
                {"tool": "list_projects", "args": {}},
            ])
        )
        orch._tool_executor.execute = AsyncMock(
            side_effect=[
                {"success": False, "error": "something broke"},
                {"success": True, "data": {"items": []}},
            ]
        )

        events = []
        async for event in orch.orchestrate("multi step"):
            events.append(event)

        results = [e for e in events if e["event"] == "result"]
        assert results[0]["data"]["status"] == "failed"
        assert results[1]["data"]["status"] == "completed"
        await orch.close()

    async def test_chat_tool_yields_thinking(self):
        orch = Orchestrator()
        await orch.start()

        orch._llm_client.post = AsyncMock(
            return_value=_llm_response([{"tool": "chat", "args": {"message": "Hello!"}}])
        )

        events = []
        async for event in orch.orchestrate("say hi"):
            events.append(event)

        thinking = [e for e in events if e["event"] == "thinking"]
        assert len(thinking) >= 2
        await orch.close()

    # ── _summarize_result tests ──

    def test_summarize_search(self):
        summary = Orchestrator._summarize_result("search", {"items": [1, 2, 3]})
        assert "Found 3" in summary

    def test_summarize_list(self):
        for tool in ["list_projects", "list_sources", "list_entities", "list_claims"]:
            summary = Orchestrator._summarize_result(tool, {"total": 5})
            assert "Found 5" in summary

    def test_summarize_create_project(self):
        summary = Orchestrator._summarize_result("create_project", {"name": "Test"})
        assert "Created project 'Test'" in summary

    def test_summarize_create_source(self):
        summary = Orchestrator._summarize_result("create_source", {"title": "Src"})
        assert "Created source 'Src'" in summary

    def test_summarize_extract(self):
        summary = Orchestrator._summarize_result("extract", {})
        assert "Extraction started" in summary

    def test_summarize_quality_score(self):
        summary = Orchestrator._summarize_result("quality_score", {"score": 0.85})
        assert "Quality score" in summary

    def test_summarize_cleanup_report(self):
        summary = Orchestrator._summarize_result("cleanup_report", {"total_orphaned": 3})
        assert "Found 3" in summary

    def test_summarize_cleanup_execute(self):
        summary = Orchestrator._summarize_result("cleanup_execute", {})
        assert "Cleanup executed" in summary

    def test_summarize_get_stats(self):
        summary = Orchestrator._summarize_result("get_stats", {
            "projects": 1, "sources": 2, "entities": 3, "claims": 4,
        })
        assert "Stats" in summary

    def test_summarize_none_data(self):
        summary = Orchestrator._summarize_result("search", None)
        assert summary == ""

    def test_summarize_unknown_tool(self):
        summary = Orchestrator._summarize_result("unknown_tool", {"a": 1})
        assert summary == ""
