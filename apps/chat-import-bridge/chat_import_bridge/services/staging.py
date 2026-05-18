from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chat_import_bridge.models import StagedImport


async def add_to_staging(
    db: AsyncSession,
    title: str,
    content: str,
    source_type: str = "paste",
) -> StagedImport:
    entry = StagedImport(
        title=title,
        raw_content=content,
        source_type=source_type,
        status="pending",
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def list_staged(
    db: AsyncSession,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[StagedImport]:
    stmt = select(StagedImport).order_by(StagedImport.created_at.desc())
    if status:
        stmt = stmt.where(StagedImport.status == status)
    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_staged(db: AsyncSession, import_id: int) -> StagedImport | None:
    result = await db.execute(
        select(StagedImport).where(StagedImport.id == import_id)
    )
    return result.scalar_one_or_none()


async def delete_staged(db: AsyncSession, import_id: int) -> bool:
    entry = await get_staged(db, import_id)
    if not entry:
        return False
    await db.delete(entry)
    await db.commit()
    return True


async def update_status(
    db: AsyncSession,
    import_id: int,
    status: str,
    error_message: str | None = None,
) -> StagedImport | None:
    entry = await get_staged(db, import_id)
    if not entry:
        return None
    entry.status = status
    if error_message:
        entry.error_message = error_message
    if status == "promoted":
        entry.promoted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(entry)
    return entry
