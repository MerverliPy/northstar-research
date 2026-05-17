from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from research_agent.config import settings
from research_agent.dependencies import close_services, init_services
from research_agent.routers import claims, cleanup, entities, extraction, projects, quality, reports, search, sources

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_services(settings)
    logger.info("research_agent_started", host=settings.host, port=settings.port)
    yield
    await close_services()
    logger.info("research_agent_shutdown")


app = FastAPI(
    title="Northstar Research Agent",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(entities.router, prefix="/api/v1")
app.include_router(claims.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(extraction.router, prefix="/api/v1")
app.include_router(quality.router, prefix="/api/v1")
app.include_router(cleanup.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "research-agent"}
