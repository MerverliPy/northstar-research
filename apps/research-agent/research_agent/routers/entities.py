import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from northstar_db import PostgresRepository
from northstar_models import EntityCreate, EntityRead

from research_agent.dependencies import get_db

router = APIRouter(prefix="/entities", tags=["Entities"])


@router.get("/", response_model=list[EntityRead])
async def list_entities(
    source_id: uuid.UUID | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = 0,
    db: PostgresRepository = Depends(get_db),
):
    entities = await db.list_entities(
        source_id=source_id, project_id=project_id, limit=limit, offset=offset
    )
    return [EntityRead.model_validate(e) for e in entities]


@router.post("/", response_model=EntityRead, status_code=201)
async def create_entity(
    data: EntityCreate,
    db: PostgresRepository = Depends(get_db),
):
    entity = await db.create_entity(data)
    return EntityRead.model_validate(entity)


@router.get("/{entity_id}", response_model=EntityRead)
async def get_entity(
    entity_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    entity = await db.get_entity(entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Entity not found")
    return EntityRead.model_validate(entity)


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(
    entity_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    deleted = await db.delete_entity(entity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entity not found")
