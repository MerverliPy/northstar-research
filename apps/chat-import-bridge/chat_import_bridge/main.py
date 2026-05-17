from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from chat_import_bridge.database import init_staging_db
from chat_import_bridge.routers import export, imports, promotion


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await init_staging_db()
    yield


app = FastAPI(
    title="Chat Import Bridge",
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

app.include_router(imports.router)
app.include_router(export.router)
app.include_router(promotion.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "chat-import-bridge"}
