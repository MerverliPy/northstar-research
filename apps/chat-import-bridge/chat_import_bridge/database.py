from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from chat_import_bridge.config import settings
from chat_import_bridge.services.staging_db import create_session_factory, create_staging_engine, init_db

_engine: AsyncEngine | None = None

def get_staging_db():
    global _engine
    if _engine is None:
        _engine = create_staging_engine(settings.staging_db_path)
    return _engine


def get_session_factory():
    engine = get_staging_db()
    return create_session_factory(engine)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


async def init_staging_db():
    engine = get_staging_db()
    await init_db(engine)
