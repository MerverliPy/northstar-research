import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from northstar_db import PostgresRepository

from research_portal.dependencies import get_db
from research_portal.config import settings
from research_portal.template_utils import env

router = APIRouter(tags=["Extraction"])


@router.get("/", response_class=HTMLResponse)
async def extraction_gate(
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
            source_map[s.id] = {"source": s, "project_name": p.name, "project_id": str(p.id)}

    extraction_logs_map = await db.latest_extraction_logs_by_source_ids(all_source_ids)
    pending_sources = []

    for source_id, info in source_map.items():
        s = info["source"]
        extraction_log = extraction_logs_map.get(source_id)
        status = extraction_log.status.value if extraction_log else "pending"
        pending_sources.append({
            "id": str(s.id),
            "title": s.title,
            "project_name": info["project_name"],
            "project_id": info["project_id"],
            "status": status,
        })

    template = env.get_template("extraction.html")
    content = template.render(
        request=request,
        pending_sources=pending_sources,
        force_graph_extraction=settings.force_graph_extraction,
    )
    return HTMLResponse(content=content)


@router.post("/trigger/{source_id}")
async def trigger_extraction(
    source_id: str,
    db: PostgresRepository = Depends(get_db),
):
    if not settings.force_graph_extraction:
        raise HTTPException(
            status_code=403,
            detail="Graph extraction is disabled. Set FORCE_GRAPH_EXTRACTION=true to enable.",
        )

    source_uuid = uuid.UUID(source_id)
    source = await db.get_source(source_uuid)
    if source is None:
        return JSONResponse({"error": "Source not found"}, status_code=404)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.research_agent_url}/api/v1/extraction/extract",
            json={"source_id": source_id, "force": True},
            timeout=300.0,
        )
        resp.raise_for_status()
        result = resp.json()

    return {"status": "extraction_triggered", "extraction_id": result.get("extraction_id"), "message": result.get("message")}
