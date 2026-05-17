import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from northstar_db import PostgresRepository
from northstar_llm import LLMService
from northstar_models import AnalysisRead, QualityScoreRequest, QualityScoreResponse, QualityStatus

from research_agent.dependencies import get_db, get_llm
from research_agent.services.quality import score_quality

router = APIRouter(prefix="/quality", tags=["Quality"])


@router.post("/score", response_model=QualityScoreResponse)
async def score_source_quality(
    req: QualityScoreRequest,
    db: PostgresRepository = Depends(get_db),
    llm: LLMService = Depends(get_llm),
):
    result = await score_quality(
        source_id=req.source_id,
        content=req.content,
        criteria=req.criteria,
        llm_service=llm,
        db=db,
    )
    return result


@router.get("/history", response_model=list[AnalysisRead])
async def list_quality_history(
    source_id: uuid.UUID | None = Query(None),
    limit: int = 50,
    offset: int = 0,
    db: PostgresRepository = Depends(get_db),
):
    analyses = await db.list_analyses(
        source_id=source_id,
        project_id=None,
        limit=limit,
        offset=offset,
    )
    return [AnalysisRead.model_validate(a) for a in analyses]
