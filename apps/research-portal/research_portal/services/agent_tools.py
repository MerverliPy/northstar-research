"""Tool definitions the orchestrator LLM can invoke via the research-agent API."""

import httpx
import structlog

logger = structlog.get_logger(__name__)

TOOL_DEFINITIONS = [
    {
        "name": "search",
        "description": "Perform vector semantic search across research documents",
        "parameters": {
            "query": "search query text",
            "project_id": "optional project UUID to filter by",
            "top_k": 5,
        },
    },
    {
        "name": "list_projects",
        "description": "List all research projects",
        "parameters": {},
    },
    {
        "name": "list_sources",
        "description": "List sources for a project",
        "parameters": {"project_id": "project UUID"},
    },
    {
        "name": "list_entities",
        "description": "List entities, optionally filtered by project or source",
        "parameters": {"project_id": "optional project UUID", "source_id": "optional source UUID"},
    },
    {
        "name": "list_claims",
        "description": "List claims, optionally filtered by source or entity",
        "parameters": {"source_id": "optional source UUID", "entity_id": "optional entity UUID"},
    },
    {
        "name": "create_project",
        "description": "Create a new research project",
        "parameters": {"name": "project name", "description": "optional description"},
    },
    {
        "name": "create_source",
        "description": "Add a source to a project",
        "parameters": {
            "project_id": "project UUID",
            "title": "source title",
            "content": "source content text",
            "source_type": "manual",
        },
    },
    {
        "name": "extract",
        "description": "Extract entities and claims from a source using LLM",
        "parameters": {"source_id": "source UUID to extract from"},
    },
    {
        "name": "quality_score",
        "description": "Score the quality of source content",
        "parameters": {"source_id": "source UUID to score"},
    },
    {
        "name": "cleanup_report",
        "description": "Get orphaned entity cleanup report (read-only, always safe)",
        "parameters": {},
    },
    {
        "name": "cleanup_execute",
        "description": "Execute destructive cleanup of orphaned entities (requires safety gate enabled)",
        "parameters": {},
    },
    {
        "name": "promote_import",
        "description": "Promote a staged import from the chat import bridge to a source",
        "parameters": {"import_id": "staged import UUID"},
    },
    {
        "name": "get_stats",
        "description": "Get system statistics (project/source/entity counts)",
        "parameters": {},
    },
]

SYSTEM_PROMPT = """You are the Northstar Research orchestrator. Your job is to analyze the user's request and determine which research platform operations to execute.

Available tools:
{tools}

Respond with ONLY a JSON object containing a "plan" array of tool calls to execute in order. Each tool call must have "tool" (the tool name) and "args" (the parameters object).

Example response:
{{"plan": [{{"tool": "search", "args": {{"query": "quantum computing", "top_k": 5}}}}, {{"tool": "quality_score", "args": {{"source_id": "<id>"}}}}]}}

If the user asks a question that doesn't map to any tool, respond with a plan containing a single "chat" tool with the answer in args.message.
If the user wants to do something impossible or you don't understand, respond with a plan containing a single "chat" tool explaining what you can do.

Always return valid JSON only — no other text."""


class AgentToolExecutor:
    """Executes tool calls by making HTTP requests to the research-agent and chat-import-bridge."""

    def __init__(self, agent_url: str = "http://127.0.0.1:8099", bridge_url: str = "http://127.0.0.1:3022"):
        self._agent_url = agent_url.rstrip("/")
        self._bridge_url = bridge_url.rstrip("/")
        self._client: httpx.AsyncClient | None = None

    async def start(self) -> None:
        self._client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("AgentToolExecutor not started")
        return self._client

    async def execute(self, tool: str, args: dict) -> dict:
        handler = getattr(self, f"_tool_{tool}", None)
        if handler is None:
            return {"error": f"Unknown tool: {tool}"}
        try:
            result = await handler(args)
            return {"success": True, "data": result}
        except Exception as e:
            logger.error("tool_execution_failed", tool=tool, error=str(e))
            return {"success": False, "error": str(e), "data": None}

    async def _tool_search(self, args: dict) -> dict:
        payload = {
            "query": args["query"],
            "top_k": args.get("top_k", 5),
        }
        if args.get("project_id"):
            payload["project_id"] = args["project_id"]
        r = await self.client.post(f"{self._agent_url}/api/v1/search/", json=payload)
        r.raise_for_status()
        return r.json()

    async def _tool_list_projects(self, args: dict) -> dict:
        r = await self.client.get(f"{self._agent_url}/api/v1/projects/?limit=50")
        r.raise_for_status()
        return r.json()

    async def _tool_list_sources(self, args: dict) -> dict:
        project_id = args["project_id"]
        r = await self.client.get(f"{self._agent_url}/api/v1/sources/?project_id={project_id}&limit=50")
        r.raise_for_status()
        return r.json()

    async def _tool_list_entities(self, args: dict) -> dict:
        params = []
        if args.get("project_id"):
            params.append(f"project_id={args['project_id']}")
        if args.get("source_id"):
            params.append(f"source_id={args['source_id']}")
        params.append("limit=50")
        r = await self.client.get(f"{self._agent_url}/api/v1/entities/?{'&'.join(params)}")
        r.raise_for_status()
        return r.json()

    async def _tool_list_claims(self, args: dict) -> dict:
        params = []
        if args.get("source_id"):
            params.append(f"source_id={args['source_id']}")
        if args.get("entity_id"):
            params.append(f"entity_id={args['entity_id']}")
        params.append("limit=50")
        r = await self.client.get(f"{self._agent_url}/api/v1/claims/?{'&'.join(params)}")
        r.raise_for_status()
        return r.json()

    async def _tool_create_project(self, args: dict) -> dict:
        payload = {"name": args["name"]}
        if args.get("description"):
            payload["description"] = args["description"]
        r = await self.client.post(f"{self._agent_url}/api/v1/projects/", json=payload)
        r.raise_for_status()
        return r.json()

    async def _tool_create_source(self, args: dict) -> dict:
        payload = {
            "project_id": args["project_id"],
            "title": args["title"],
            "content": args["content"],
            "source_type": args.get("source_type", "manual"),
        }
        r = await self.client.post(f"{self._agent_url}/api/v1/sources/", json=payload)
        r.raise_for_status()
        return r.json()

    async def _tool_extract(self, args: dict) -> dict:
        force = args.get("force", False)
        r = await self.client.post(
            f"{self._agent_url}/api/v1/extraction/extract?force={'true' if force else 'false'}",
            json={"source_id": args["source_id"]},
        )
        r.raise_for_status()
        return r.json()

    async def _tool_quality_score(self, args: dict) -> dict:
        r = await self.client.post(
            f"{self._agent_url}/api/v1/quality/score",
            json={"source_id": args["source_id"]},
        )
        r.raise_for_status()
        return r.json()

    async def _tool_cleanup_report(self, args: dict) -> dict:
        r = await self.client.get(f"{self._agent_url}/api/v1/cleanup/report")
        r.raise_for_status()
        return r.json()

    async def _tool_cleanup_execute(self, args: dict) -> dict:
        r = await self.client.post(f"{self._agent_url}/api/v1/cleanup/execute")
        r.raise_for_status()
        return r.json()

    async def _tool_promote_import(self, args: dict) -> dict:
        r = await self.client.post(f"{self._bridge_url}/api/v1/promotion/{args['import_id']}")
        r.raise_for_status()
        return r.json()

    async def _tool_get_stats(self, args: dict) -> dict:
        proj_r = await self.client.get(f"{self._agent_url}/api/v1/projects/?limit=1")
        proj_r.raise_for_status()
        proj_data = proj_r.json()
        sources_r = await self.client.get(f"{self._agent_url}/api/v1/sources/?project_id=all&limit=1")
        sources_r.raise_for_status()
        sources_data = sources_r.json()
        entities_r = await self.client.get(f"{self._agent_url}/api/v1/entities/?limit=1")
        entities_r.raise_for_status()
        entities_data = entities_r.json()
        claims_r = await self.client.get(f"{self._agent_url}/api/v1/claims/?limit=1")
        claims_r.raise_for_status()
        claims_data = claims_r.json()
        return {
            "projects": proj_data.get("total", 0),
            "sources": sources_data.get("total", 0),
            "entities": entities_data.get("total", 0),
            "claims": claims_data.get("total", 0),
        }
