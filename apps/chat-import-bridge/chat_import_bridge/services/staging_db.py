import os
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from chat_import_bridge.models import StagingBase


def create_staging_engine(db_path: str):
    expanded = os.path.expanduser(db_path)
    parent = Path(expanded).parent
    parent.mkdir(parents=True, exist_ok=True)
    return create_async_engine(f"sqlite+aiosqlite:///{expanded}")


def create_session_factory(engine):
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db(engine):
    async with engine.begin() as conn:
        await conn.run_sync(StagingBase.metadata.create_all)
