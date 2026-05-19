from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from structlog import get_logger

from northstar_db import Neo4jRepository, PostgresRepository

if TYPE_CHECKING:
    from research_agent.services.scraper import WebScraper
from northstar_llm import EmbeddingService, LLMService
from northstar_vector import VectorStore

from research_agent.config import Settings, settings as app_settings

logger = get_logger(__name__)

_db: PostgresRepository | None = None
_llm: LLMService | None = None
_embedding: EmbeddingService | None = None
_vector_store: VectorStore | None = None
_neo4j: Neo4jRepository | None = None
_scraper: WebScraper | None = None


def _import_scraper() -> type[WebScraper]:
    from research_agent.services.scraper import WebScraper as _WebScraper
    return _WebScraper


async def init_services(settings: Settings) -> None:
    global _db, _llm, _embedding, _vector_store, _neo4j, _scraper

    _db = PostgresRepository(database_url=settings.database_url)
    await _db.initialize()

    _neo4j = Neo4jRepository(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await _neo4j.initialize()

    _embedding = EmbeddingService(
        model=settings.embedding_model,
        ollama_base_url=settings.ollama_base_url,
    )

    _vector_store = VectorStore(
        chroma_persist_dir=settings.chroma_persist_dir,
        embedding_service=_embedding,
    )
    await _vector_store.initialize()

    _llm = LLMService(
        primary_model=settings.primary_llm_model,
        fallback_model=settings.fallback_llm_model,
        ollama_base_url=settings.ollama_base_url,
    )

    if settings.scraper_enabled:
        WebScraperCls = _import_scraper()
        _scraper = WebScraperCls(settings)
        await _scraper.initialize()

    logger.info("services_initialized")


async def close_services() -> None:
    global _db, _llm, _embedding, _vector_store, _neo4j

    if _db is not None:
        await _db.close()
    if _neo4j is not None:
        await _neo4j.close()
    if _llm is not None:
        await _llm.close()
    if _embedding is not None:
        await _embedding.close()
    if _vector_store is not None:
        await _vector_store.close()

    logger.info("services_closed")


async def get_db() -> AsyncGenerator[PostgresRepository, None]:
    if _db is None:
        raise RuntimeError("PostgresRepository not initialized")
    yield _db


async def get_llm() -> AsyncGenerator[LLMService, None]:
    if _llm is None:
        raise RuntimeError("LLMService not initialized")
    yield _llm


async def get_embedding() -> AsyncGenerator[EmbeddingService, None]:
    if _embedding is None:
        raise RuntimeError("EmbeddingService not initialized")
    yield _embedding


async def get_vector_store() -> AsyncGenerator[VectorStore, None]:
    if _vector_store is None:
        raise RuntimeError("VectorStore not initialized")
    yield _vector_store


async def get_neo4j() -> AsyncGenerator[Neo4jRepository, None]:
    if _neo4j is None:
        raise RuntimeError("Neo4jRepository not initialized")
    yield _neo4j


async def get_scraper() -> AsyncGenerator[WebScraper, None]:
    if _scraper is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=503,
            detail="Web scraper not enabled. Set SCRAPER_ENABLED=true and install: pip install research-agent[scraper]",
        )
    yield _scraper


async def get_settings() -> Settings:
    return app_settings
