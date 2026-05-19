from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
import structlog
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from research_portal.config import settings
from research_portal.dependencies import close_services, get_db, get_neo4j, init_services
from research_portal.routers import chat, dashboard, extraction, quality, cleanup, visual, api_proxy
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
    allow_origins=["http://localhost:3010", "http://127.0.0.1:3010", "http://localhost:5173"],
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
app.include_router(api_proxy.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/dashboard")
app.include_router(extraction.router, prefix="/extraction")
app.include_router(quality.router, prefix="/quality")
app.include_router(cleanup.router, prefix="/cleanup")
app.include_router(visual.router, prefix="/visual")


@app.get("/api/settings")
async def get_settings_route():
    return {
        "force_graph_extraction": settings.force_graph_extraction,
        "enable_destructive_cleanup": settings.enable_destructive_cleanup,
        "research_agent_url": settings.research_agent_url,
        "chat_import_bridge_url": settings.chat_import_bridge_url,
        "log_level": settings.log_level,
    }


@app.get("/graph/data/{project_id}")
async def get_graph_data(project_id: str):
    """Get graph data for a project from Neo4j."""
    try:
        await anext(get_db())
        neo4j = await anext(get_neo4j())
        graph_data = await neo4j.get_project_graph(project_id)
        return graph_data
    except Exception:
        logger.warning("agent_proxy_failed", endpoint="graph/data", exc_info=True)
        return {"nodes": [], "edges": []}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "research-portal"}


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = (STATIC_DIR / full_path).resolve()
    if not str(file_path).startswith(str(STATIC_DIR.resolve())):
        raise HTTPException(status_code=404)
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return FileResponse(str(BASE_DIR / "templates" / "base.html"))
