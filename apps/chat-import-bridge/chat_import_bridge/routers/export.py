from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from chat_import_bridge.database import get_session
from chat_import_bridge.services import staging as svc
from chat_import_bridge.services.export import to_markdown

router = APIRouter(prefix="/api/v1/export", tags=["Export"])


@router.get("/{import_id}/markdown")
async def export_markdown(
    import_id: int,
    db: AsyncSession = Depends(get_session),
):
    entry = await svc.get_staged(db, import_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Import not found")

    return await to_markdown(entry)
