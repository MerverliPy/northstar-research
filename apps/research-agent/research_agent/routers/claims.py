import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from northstar_db import PostgresRepository
from northstar_models import ClaimCreate, ClaimRead

from research_agent.dependencies import get_db

router = APIRouter(prefix="/claims", tags=["Claims"])


@router.get("/", response_model=list[ClaimRead])
async def list_claims(
    source_id: uuid.UUID | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    limit: int = 50,
    offset: int = 0,
    db: PostgresRepository = Depends(get_db),
):
    claims = await db.list_claims(
        source_id=source_id, entity_id=entity_id, limit=limit, offset=offset
    )
    return [ClaimRead.model_validate(c) for c in claims]


@router.post("/", response_model=ClaimRead, status_code=201)
async def create_claim(
    data: ClaimCreate,
    db: PostgresRepository = Depends(get_db),
):
    claim = await db.create_claim(data)
    return ClaimRead.model_validate(claim)


@router.get("/{claim_id}", response_model=ClaimRead)
async def get_claim(
    claim_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    claim = await db.get_claim(claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")
    return ClaimRead.model_validate(claim)


@router.delete("/{claim_id}", status_code=204)
async def delete_claim(
    claim_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    deleted = await db.delete_claim(claim_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Claim not found")
