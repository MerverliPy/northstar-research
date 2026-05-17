from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

from research_portal.config import settings
from research_portal.dependencies import close_services, init_services
from research_portal.routers import cleanup, dashboard, extraction, quality, visual

logger = structlog.get_logger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_services(settings)
    app.state.settings = settings
    logger.info("portal_started", host=settings.host, port=settings.port)
    yield
    await close_services()
    logger.info("portal_shutdown")


app = FastAPI(
    title="Northstar Research Portal",
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

STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(dashboard.router)
app.include_router(quality.router, prefix="/quality")
app.include_router(cleanup.router, prefix="/cleanup")
app.include_router(extraction.router, prefix="/extraction")
app.include_router(visual.router, prefix="/graph")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "research-portal"}
