from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from research_portal.config import settings
from research_portal.dependencies import close_services, get_db, get_neo4j, init_services
from research_portal.routers import chat
from research_portal.services.orchestrator import Orchestrator
from research_portal.services.conversation import ConversationStore

logger = structlog.get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


def transform_project(agent_project: dict) -> dict:
    """Map agent project schema to frontend Project type."""
    return {
        "id": str(agent_project.get("id", "")),
        "name": agent_project.get("topic", ""),
        "description": agent_project.get("topic", "")[:200],
        "metadata": {"status": agent_project.get("status", "")},
        "created_at": agent_project.get("created_at", ""),
        "updated_at": agent_project.get("created_at", ""),
    }


def transform_report(agent_report: dict) -> dict:
    """Map agent report schema to frontend Report type."""
    return {
        "id": str(agent_report.get("id", agent_report.get("report_id", ""))),
        "project_id": str(agent_report.get("project_id", "")),
        "title": agent_report.get("title", agent_report.get("topic", "Report")),
        "content": agent_report.get("content", agent_report.get("summary", "")),
        "report_type": agent_report.get("report_type", agent_report.get("type", "summary")),
        "metadata": None,
        "created_at": agent_report.get("created_at", ""),
        "updated_at": agent_report.get("created_at", ""),
    }


def paginated_response(items: list, total: int | None = None, limit: int = 100, offset: int = 0) -> dict:
    return {
        "items": items,
        "total": total if total is not None else len(items),
        "limit": limit,
        "offset": offset,
    }


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_services(settings)

    orchestrator = Orchestrator(
        agent_url=settings.research_agent_url,
        bridge_url=settings.chat_import_bridge_url,
        ollama_url=settings.ollama_base_url,
        llm_model=settings.orchestrator_model,
    )
    await orchestrator.start()
    app.state.orchestrator = orchestrator

    conversation_store = ConversationStore(db_path=settings.conversation_db_path)
    app.state.conversation_store = conversation_store

    app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(60.0))
    app.state.settings = settings
    logger.info("portal_started", host=settings.host, port=settings.port)
    yield

    await orchestrator.close()
    conversation_store.close()
    await app.state.http_client.aclose()
    await close_services()
    logger.info("portal_shutdown")


app = FastAPI(
    title="Northstar Research Console",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR.mkdir(parents=True, exist_ok=True)

if (STATIC_DIR / "assets").exists():
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="spa_assets")
if (STATIC_DIR / "icons").exists():
    app.mount("/icons", StaticFiles(directory=str(STATIC_DIR / "icons")), name="spa_icons")
if (STATIC_DIR / "favicon.svg").exists():
    app.mount("/favicon.svg", StaticFiles(directory=str(STATIC_DIR)), name="spa_favicon")

app.include_router(chat.router, prefix="/api")


@app.get("/api/settings")
async def get_settings_route():
    return {
        "force_graph_extraction": settings.force_graph_extraction,
        "enable_destructive_cleanup": settings.enable_destructive_cleanup,
        "research_agent_url": settings.research_agent_url,
        "chat_import_bridge_url": settings.chat_import_bridge_url,
        "log_level": settings.log_level,
    }


# ── API v1 proxy with path rewriting & data transformation ──

def _query_params(request: Request) -> dict[str, str]:
    """Extract query params as a flat dict."""
    result: dict[str, str] = {}
    for key, values in request.query_params.multi_items():
        result[key] = values
    return result


def _parse_int(val: str | None, default: int = 100) -> int:
    try:
        return int(val) if val else default
    except (ValueError, TypeError):
        return default


async def _agent_get(client: httpx.AsyncClient, url: str, params: dict | None = None) -> list[dict]:
    """GET from agent, returning parsed JSON list. Returns empty list on error."""
    try:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else []
    except Exception:
        pass
    return []


GET  = "GET"
POST = "POST"
PUT  = "PUT"
DELETE = "DELETE"


@app.api_route("/api/v1/{path:path}", methods=[GET, POST, PUT, DELETE])
async def api_v1_handler(request: Request, path: str):
    """Handle all /api/v1/... requests from the SPA frontend.
    Rewrites paths to match research-agent API and transforms data to match frontend types.
    """
    client: httpx.AsyncClient = request.app.state.http_client
    agent_base = settings.research_agent_url.rstrip("/")
    method = request.method
    params = _query_params(request)
    limit = _parse_int(params.get("limit"), 100)
    offset = _parse_int(params.get("offset"), 0)

    # ── Projects ──
    if path.rstrip("/") == "projects":
        if method == GET:
            items_raw = await _agent_get(client, f"{agent_base}/projects")
            items = [transform_project(p) for p in items_raw]
            # Client-side pagination on transformed data
            total = len(items)
            paged = items[offset:offset + limit]
            return paginated_response(paged, total, limit, offset)

        if method == POST:
            body = await request.json()
            topic = body.get("name", body.get("topic", ""))
            try:
                resp = await client.post(f"{agent_base}/research", json={"topic": topic})
                if resp.status_code in (200, 201):
                    agent_proj = resp.json()
                    if isinstance(agent_proj, dict):
                        return transform_project(agent_proj)
            except Exception:
                pass
            return JSONResponse({"detail": "Failed to create project"}, status_code=502)

        if method == PUT:
            return JSONResponse({"detail": "Update not supported via agent"}, status_code=501)

        if method == DELETE:
            return JSONResponse({"detail": "Delete not supported via agent"}, status_code=501)

    # ── Reports ──
    if path.rstrip("/") == "reports":
        if method == GET:
            project_id = params.get("project_id")
            reports: list[dict] = []
            if project_id and project_id != "all":
                try:
                    resp = await client.get(f"{agent_base}/reports")
                    if resp.status_code == 200:
                        all_reports = resp.json()
                        if isinstance(all_reports, list):
                            reports = [r for r in all_reports if str(r.get("project_id", "")) == project_id]
                except Exception:
                    pass
            else:
                reports = await _agent_get(client, f"{agent_base}/reports")
            items = [transform_report(r) for r in reports]
            total = len(items)
            paged = items[offset:offset + limit]
            return paginated_response(paged, total, limit, offset)

        if method in (POST, PUT, DELETE):
            return JSONResponse({"detail": "Reports CRUD not supported via agent"}, status_code=501)

    # ── Sources ── (not directly in agent; return empty)
    if path.rstrip("/") == "sources":
        return paginated_response([], 0, limit, offset)

    # ── Entities ── (via knowledge/entities)
    if path.rstrip("/") == "entities":
        if method == GET:
            try:
                resp = await client.get(f"{agent_base}/knowledge/entities", params={"limit": limit} if not params.get("project_id") else params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("items", data.get("entities", []))
                    if isinstance(items, list):
                        transformed = [
                            {
                                "id": str(e.get("id", "")),
                                "source_id": str(e.get("source_id", "")) if e.get("source_id") else None,
                                "project_id": str(e.get("project_id", "")) if e.get("project_id") else None,
                                "name": e.get("name", e.get("label", "")),
                                "entity_type": e.get("entity_type", e.get("type", "unknown")),
                                "description": e.get("description", ""),
                                "metadata": None,
                                "created_at": e.get("created_at", ""),
                                "updated_at": e.get("created_at", ""),
                            }
                            for e in items
                        ]
                        return paginated_response(transformed)
            except Exception:
                pass
        return paginated_response([], 0, limit, offset)

    # ── Claims ── (not directly in agent; return empty)
    if path.rstrip("/") == "claims":
        return paginated_response([], 0, limit, offset)

    # ── Graph data ── (query Neo4j directly)
    if path.startswith("graph/data/"):
        project_id = path.split("/")[-1]
        try:
            neo4j = await anext(get_neo4j())
            graph_data = await neo4j.get_project_graph(project_id)
            return graph_data
        except Exception:
            return {"nodes": [], "edges": []}

    # ── Generic passthrough for other /api/v1/ paths ──
    target_url = f"{agent_base}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    body_bytes = await request.body() if method in (POST, PUT) else None
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    try:
        resp = await client.request(
            method=method,
            url=target_url,
            headers=headers,
            content=body_bytes,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except httpx.ConnectError:
        return JSONResponse({"detail": "Research agent unavailable"}, status_code=503)


@app.get("/graph/data/{project_id}")
async def get_graph_data(project_id: str):
    """Get graph data for a project from Neo4j."""
    try:
        await anext(get_db())
        neo4j = await anext(get_neo4j())
        graph_data = await neo4j.get_project_graph(project_id)
        return graph_data
    except Exception:
        return {"nodes": [], "edges": []}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "research-portal"}


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return FileResponse(str(BASE_DIR / "templates" / "base.html"))
