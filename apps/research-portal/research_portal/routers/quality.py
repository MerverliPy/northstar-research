import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from northstar_db import PostgresRepository

from research_portal.dependencies import get_db
from research_portal.config import settings

router = APIRouter(tags=["Quality"])

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


@router.get("/", response_class=HTMLResponse)
async def quality_dashboard(
    request: Request,
    db: PostgresRepository = Depends(get_db),
):
    projects = await db.list_projects(limit=50)
    sources_with_scores = []

    for p in projects:
        sources = await db.list_sources(p.id, limit=50)
        for s in sources:
            analyses = await db.list_analyses(source_id=s.id, limit=1)
            quality_score = None
            if analyses:
                quality_score = analyses[0].quality_score
            sources_with_scores.append({
                "id": str(s.id),
                "title": s.title,
                "project_name": p.name,
                "quality_score": quality_score,
                "needs_review": quality_score is None or (quality_score is not None and quality_score < 0.5),
            })

    template = env.get_template("quality.html")
    content = template.render(
        request=request,
        sources=sources_with_scores,
    )
    return HTMLResponse(content=content)


@router.post("/score/{source_id}")
async def score_source(
    source_id: str,
    db: PostgresRepository = Depends(get_db),
):
    import uuid
    source_uuid = uuid.UUID(source_id)
    source = await db.get_source(source_uuid)
    if source is None:
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "Source not found"}, status_code=404)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.research_agent_url}/api/v1/quality/score",
            json={"source_id": source_id, "content": source.raw_content[:10000], "criteria": {}},
            timeout=120.0,
        )
        resp.raise_for_status()
        result = resp.json()

    return {"status": "scored", "score": result.get("score"), "reasoning": result.get("reasoning")}
