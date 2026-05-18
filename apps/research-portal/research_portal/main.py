from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from research_portal.config import settings
from research_portal.dependencies import close_services, get_db, get_neo4j, init_services
from research_portal.routers import chat
from research_portal.services.orchestrator import Orchestrator
from research_portal.services.conversation import ConversationStore

logger = structlog.get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"


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


@app.api_route("/api/v1/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_agent(request: Request, path: str):
    """Proxy API requests to the research-agent."""
    client: httpx.AsyncClient = request.app.state.http_client
    target_url = f"{settings.research_agent_url}/api/v1/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    body = await request.body() if request.method in ("POST", "PUT", "PATCH") else None

    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)

    try:
        resp = await client.request(
            method=request.method,
            url=target_url,
            headers=headers,
            content=body,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except httpx.ConnectError:
        return Response(
            content='{"detail": "Research agent unavailable"}',
            status_code=503,
            media_type="application/json",
        )


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
