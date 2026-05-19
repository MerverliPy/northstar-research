from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from chat_import_bridge.config import settings
from chat_import_bridge.database import get_session
from chat_import_bridge.services import staging as svc
from chat_import_bridge.services.promotion import promote_all_pending, promote_to_agent

router = APIRouter(prefix="/api/v1/promotion", tags=["Promotion"])


class PromoteRequest(BaseModel):
    project_id: str | None = None


class PromoteResponse(BaseModel):
    status: str
    source_id: str | None = None
    error: str | None = None


class BatchPromoteResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[dict]


@router.post("/{import_id}", response_model=PromoteResponse)
async def promote_import(
    import_id: int,
    body: PromoteRequest = PromoteRequest(),
    db: AsyncSession = Depends(get_session),
):
    if not settings.promotion_enabled:
        raise HTTPException(status_code=403, detail="Promotion is disabled. Set PROMOTION_ENABLED=true.")
    entry = await svc.get_staged(db, import_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Import not found")

    result = await promote_to_agent(
        settings.research_agent_url,
        import_id,
        db,
        project_id=body.project_id,
    )
    return PromoteResponse(
        status=result["status"],
        source_id=result["source_id"],
        error=result["error"],
    )


@router.post("/batch", response_model=BatchPromoteResponse)
async def promote_batch(
    db: AsyncSession = Depends(get_session),
):
    if not settings.promotion_enabled:
        raise HTTPException(status_code=403, detail="Promotion is disabled. Set PROMOTION_ENABLED=true.")
    result = await promote_all_pending(settings.research_agent_url, db_session=db)
    return BatchPromoteResponse(
        total=result["total"],
        succeeded=result["succeeded"],
        failed=result["failed"],
        results=result["results"],
    )
