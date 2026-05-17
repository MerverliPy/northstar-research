from collections.abc import AsyncGenerator

from fastapi import Depends, Request
from structlog import get_logger

from northstar_db import Neo4jRepository, PostgresRepository

from research_portal.config import Settings, settings as app_settings

logger = get_logger(__name__)

_db: PostgresRepository | None = None
_neo4j: Neo4jRepository | None = None


async def init_services(settings: Settings) -> None:
    global _db, _neo4j

    _db = PostgresRepository(database_url=settings.database_url)
    await _db.initialize()

    _neo4j = Neo4jRepository(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
    )
    await _neo4j.initialize()

    logger.info("portal_services_initialized")


async def close_services() -> None:
    global _db, _neo4j

    if _db is not None:
        await _db.close()
    if _neo4j is not None:
        await _neo4j.close()

    logger.info("portal_services_closed")


async def get_db() -> AsyncGenerator[PostgresRepository, None]:
    if _db is None:
        raise RuntimeError("PostgresRepository not initialized")
    yield _db


async def get_neo4j() -> AsyncGenerator[Neo4jRepository, None]:
    if _neo4j is None:
        raise RuntimeError("Neo4jRepository not initialized")
    yield _neo4j


async def get_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_settings_dep() -> Settings:
    return app_settings
