from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from chat_import_bridge.database import get_session
from chat_import_bridge.services import staging as svc

router = APIRouter(prefix="/api/v1/imports", tags=["Imports"])


class PasteImportRequest(BaseModel):
    title: str
    content: str
    source_type: str = "paste"


class PasteImportResponse(BaseModel):
    id: int
    title: str
    status: str


class StagedImportResponse(BaseModel):
    id: int
    title: str
    source_type: str
    status: str
    error_message: str | None = None
    created_at: str | None = None
    promoted_at: str | None = None


@router.post("/paste", response_model=PasteImportResponse, status_code=201)
async def import_paste(
    body: PasteImportRequest,
    db: AsyncSession = Depends(get_session),
):
    entry = await svc.add_to_staging(db, body.title, body.content, body.source_type)
    return PasteImportResponse(id=entry.id, title=entry.title, status=entry.status)


@router.get("/", response_model=list[StagedImportResponse])
async def list_imports(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_session),
):
    entries = await svc.list_staged(db, status=status, limit=limit, offset=offset)
    return [
        StagedImportResponse(
            id=e.id,
            title=e.title,
            source_type=e.source_type,
            status=e.status,
            error_message=e.error_message,
            created_at=e.created_at.isoformat() if e.created_at else None,
            promoted_at=e.promoted_at.isoformat() if e.promoted_at else None,
        )
        for e in entries
    ]


@router.get("/{import_id}", response_model=StagedImportResponse)
async def get_import(
    import_id: int,
    db: AsyncSession = Depends(get_session),
):
    entry = await svc.get_staged(db, import_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Import not found")
    return StagedImportResponse(
        id=entry.id,
        title=entry.title,
        source_type=entry.source_type,
        status=entry.status,
        error_message=entry.error_message,
        created_at=entry.created_at.isoformat() if entry.created_at else None,
        promoted_at=entry.promoted_at.isoformat() if entry.promoted_at else None,
    )


@router.delete("/{import_id}", status_code=204)
async def delete_import(
    import_id: int,
    db: AsyncSession = Depends(get_session),
):
    deleted = await svc.delete_staged(db, import_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Import not found")
