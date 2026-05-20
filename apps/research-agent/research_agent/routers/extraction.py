import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select

from northstar_db import Neo4jRepository, PostgresRepository
from northstar_llm import LLMService
from northstar_models import ExtractionLogRead, ExtractionRequest, ExtractionResponse, ExtractionStatus
from northstar_models.models import ExtractionLog
from northstar_vector import VectorStore

from research_agent.config import settings
from research_agent.dependencies import get_db, get_llm, get_neo4j, get_vector_store
from research_agent.services.extraction import run_extraction

router = APIRouter(prefix="/extraction", tags=["Extraction"])


@router.post("/extract", response_model=ExtractionResponse)
async def trigger_extraction(
    req: ExtractionRequest,
    background_tasks: BackgroundTasks,
    db: PostgresRepository = Depends(get_db),
    llm: LLMService = Depends(get_llm),
    neo4j: Neo4jRepository = Depends(get_neo4j),
    vector_store: VectorStore = Depends(get_vector_store),
):
    if not settings.force_graph_extraction:
        raise HTTPException(
            status_code=403,
            detail="Extraction is disabled. Set FORCE_GRAPH_EXTRACTION=true to enable.",
        )

    source = await db.get_source(req.source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")

    log = await db.create_extraction_log(source_id=req.source_id, project_id=source.project_id)

    background_tasks.add_task(
        run_extraction,
        source_id=req.source_id,
        llm_service=llm,
        db=db,
        neo4j=neo4j,
        vector_store=vector_store,
        force=req.force,
    )

    return ExtractionResponse(
        extraction_id=log.id,
        status=log.status,
        message="Extraction queued",
        entities_count=0,
    )


@router.get("/status/{extraction_id}", response_model=ExtractionLogRead)
async def get_extraction_status(
    extraction_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    async with db._session() as session:
        result = await session.execute(
            select(ExtractionLog).where(ExtractionLog.id == extraction_id)
        )
        log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=404, detail="Extraction log not found")
    return ExtractionLogRead.model_validate(log)


@router.get("/queue", response_model=list[ExtractionLogRead])
async def list_pending_extractions(
    db: PostgresRepository = Depends(get_db),
):
    async with db._session() as session:
        result = await session.execute(
            select(ExtractionLog)
            .where(ExtractionLog.status.in_([ExtractionStatus.PENDING, ExtractionStatus.IN_PROGRESS]))
            .order_by(ExtractionLog.created_at.desc())
        )
        logs = result.scalars().all()
    return [ExtractionLogRead.model_validate(log) for log in logs]
