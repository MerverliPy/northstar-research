import httpx
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from northstar_db import PostgresRepository

from research_portal.dependencies import get_db
from research_portal.config import settings
from research_portal.template_utils import env

router = APIRouter(tags=["Quality"])


@router.get("/", response_class=HTMLResponse)
async def quality_dashboard(
    request: Request,
    db: PostgresRepository = Depends(get_db),
):
    projects = await db.list_projects(limit=50)
    all_source_ids = []
    source_map: dict = {}
    for p in projects:
        sources = await db.list_sources(p.id, limit=50)
        for s in sources:
            all_source_ids.append(s.id)
            source_map[s.id] = {"source": s, "project_name": p.name}

    analyses_map = await db.latest_analyses_by_source_ids(all_source_ids)
    sources_with_scores = []

    for source_id, info in source_map.items():
        s = info["source"]
        analysis = analyses_map.get(source_id)
        quality_score = analysis.quality_score if analysis else None
        sources_with_scores.append({
            "id": str(s.id),
            "title": s.title,
            "project_name": info["project_name"],
            "quality_score": quality_score,
            "needs_review": quality_score is None or quality_score < 0.5,
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
