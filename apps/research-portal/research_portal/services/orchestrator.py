"""LLM-based orchestrator that interprets natural language and executes tool calls."""

import json
import re
from collections.abc import AsyncGenerator

import httpx
import structlog

from research_portal.services.agent_tools import (
    TOOL_DEFINITIONS,
    SYSTEM_PROMPT,
    AgentToolExecutor,
)

logger = structlog.get_logger(__name__)


class Orchestrator:
    """Interprets natural language intent and executes platform operations via tools."""

    def __init__(
        self,
        agent_url: str = "http://127.0.0.1:8099",
        bridge_url: str = "http://127.0.0.1:3022",
        ollama_url: str = "http://127.0.0.1:11434",
        llm_model: str = "qwen3:14b",
    ):
        self._agent_url = agent_url.rstrip("/")
        self._bridge_url = bridge_url.rstrip("/")
        self._ollama_url = ollama_url.rstrip("/")
        self._llm_model = llm_model
        self._tool_executor = AgentToolExecutor(agent_url=agent_url, bridge_url=bridge_url)
        self._llm_client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._llm_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
        await self._tool_executor.start()

    async def close(self) -> None:
        if self._llm_client:
            await self._llm_client.aclose()
            self._llm_client = None
        await self._tool_executor.close()

    async def _call_llm(self, prompt: str) -> str:
        """Call Ollama to get the plan."""
        tools_text = json.dumps(TOOL_DEFINITIONS, indent=2)
        system = SYSTEM_PROMPT.format(tools=tools_text)

        r = await self._llm_client.post(
            f"{self._ollama_url}/api/generate",
            json={
                "model": self._llm_model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 2048,
                },
            },
        )
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip()

    @staticmethod
    def _parse_plan(llm_response: str) -> list[dict]:
        """Parse the LLM's JSON plan from the response."""
        cleaned = llm_response.strip()

        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
        if json_match:
            cleaned = json_match.group(1).strip()

        result = json.loads(cleaned)

        if isinstance(result, dict) and "plan" in result:
            return result["plan"]
        if isinstance(result, list):
            return result

        raise ValueError(f"Unexpected LLM response format: {cleaned[:200]}")

    async def orchestrate(self, message: str) -> AsyncGenerator[dict, None]:
        """Stream SSE events: thinking → action → result → done."""
        yield {"event": "thinking", "data": {"text": "Analyzing your request..."}}

        try:
            llm_response = await self._call_llm(message)
        except Exception as e:
            logger.error("llm_call_failed", error=str(e))
            yield {"event": "error", "data": {"message": f"LLM call failed: {str(e)}"}}
            return

        try:
            plan = self._parse_plan(llm_response)
        except Exception as e:
            logger.error("plan_parse_failed", error=str(e), response=llm_response[:200])
            yield {"event": "error", "data": {"message": f"Failed to understand request: {str(e)}"}}
            return

        if not plan:
            yield {"event": "done", "data": {"summary": "I couldn't determine what action to take."}}
            return

        summary_parts = []

        for step in plan:
            tool = step.get("tool", "")
            args = step.get("args", {})

            if tool == "chat":
                yield {"event": "thinking", "data": {"text": args.get("message", "")}}
                continue

            yield {
                "event": "action",
                "data": {"action": tool, "status": "running", "args": args},
            }

            try:
                result = await self._tool_executor.execute(tool, args)
            except Exception as e:
                logger.error("tool_execution_failed", tool=tool, error=str(e))
                yield {
                    "event": "result",
                    "data": {
                        "action": tool,
                        "type": tool,
                        "status": "failed",
                        "data": None,
                        "error": str(e),
                    },
                }
                continue

            yield {
                "event": "result",
                "data": {
                    "action": tool,
                    "type": tool,
                    "status": "completed" if result.get("success", True) else "failed",
                    "data": result.get("data", result),
                    "summary": self._summarize_result(tool, result.get("data", result)),
                },
            }

            summary = self._summarize_result(tool, result.get("data", result))
            if summary:
                summary_parts.append(summary)

        final_summary = " ".join(summary_parts) if summary_parts else "Done."
        yield {"event": "done", "data": {"summary": final_summary}}

    @staticmethod
    def _summarize_result(tool: str, data: dict | None) -> str:
        if data is None:
            return ""
        if tool == "search":
            items = data.get("items", data.get("results", []))
            return f"Found {len(items)} matching results."
        if tool in ("list_projects", "list_sources", "list_entities", "list_claims"):
            total = data.get("total", len(data.get("items", [])))
            return f"Found {total} {tool.replace('list_', '')}."
        if tool == "create_project":
            name = data.get("name", "project")
            return f"Created project '{name}'."
        if tool == "create_source":
            title = data.get("title", "source")
            return f"Created source '{title}'."
        if tool == "extract":
            return "Extraction started successfully."
        if tool == "quality_score":
            score = data.get("score", data)
            return f"Quality score: {score}."
        if tool == "cleanup_report":
            total = data.get("total_orphaned", 0)
            return f"Found {total} orphaned entities."
        if tool == "cleanup_execute":
            return "Cleanup executed."
        if tool == "get_stats":
            return f"Stats: {data.get('projects', 0)} projects, {data.get('sources', 0)} sources, {data.get('entities', 0)} entities, {data.get('claims', 0)} claims."
        return ""
