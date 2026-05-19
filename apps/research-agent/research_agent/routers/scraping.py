from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from northstar_db import Neo4jRepository, PostgresRepository
from northstar_llm import LLMService
from northstar_models import ScrapeRequest, ScrapeResponse, SourceCreate, SourceRead
from northstar_vector import VectorStore

from research_agent.dependencies import get_db, get_llm, get_neo4j, get_scraper, get_vector_store
from research_agent.services.extraction import run_extraction
from research_agent.services.scraper import WebScraper

router = APIRouter(prefix="/scraping", tags=["Scraping"])


@router.post("/scrape", response_model=ScrapeResponse, status_code=201)
async def scrape_url(
    req: ScrapeRequest,
    background_tasks: BackgroundTasks,
    scraper: WebScraper = Depends(get_scraper),
    db: PostgresRepository = Depends(get_db),
    llm: LLMService = Depends(get_llm),
    neo4j: Neo4jRepository = Depends(get_neo4j),
    vector_store: VectorStore = Depends(get_vector_store),
):
    project = await db.get_project(req.project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        result = await scraper.scrape(req)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    source = await db.create_source(
        SourceCreate(
            project_id=req.project_id,
            title=result.title or req.title or req.url,
            url=req.url,
            content_type="web",
            raw_content=result.content,
            metadata={
                "fingerprint_seed": result.fingerprint_seed,
                "took_ms": result.took_ms,
                "word_count": result.word_count,
                "headless": req.headless,
            },
        )
    )

    if req.extract:
        background_tasks.add_task(
            run_extraction,
            source_id=source.id,
            llm_service=llm,
            db=db,
            neo4j=neo4j,
            vector_store=vector_store,
            force=False,
        )

    return ScrapeResponse(
        source=SourceRead.model_validate(source),
        title=result.title,
        url=req.url,
        word_count=result.word_count,
        fingerprint_seed=result.fingerprint_seed,
        took_ms=result.took_ms,
    )
