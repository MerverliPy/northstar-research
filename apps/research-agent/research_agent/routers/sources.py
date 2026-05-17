import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from northstar_db import PostgresRepository
from northstar_models import SourceCreate, SourceRead

from research_agent.dependencies import get_db

router = APIRouter(prefix="/sources", tags=["Sources"])


@router.get("/", response_model=list[SourceRead])
async def list_sources(
    project_id: uuid.UUID = Query(...),
    limit: int = 50,
    offset: int = 0,
    db: PostgresRepository = Depends(get_db),
):
    sources = await db.list_sources(project_id=project_id, limit=limit, offset=offset)
    return [SourceRead.model_validate(s) for s in sources]


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(
    data: SourceCreate,
    db: PostgresRepository = Depends(get_db),
):
    source = await db.create_source(data)
    return SourceRead.model_validate(source)


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(
    source_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    source = await db.get_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return SourceRead.model_validate(source)


@router.delete("/{source_id}", status_code=204)
async def delete_source(
    source_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    deleted = await db.delete_source(source_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Source not found")
