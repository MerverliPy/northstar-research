import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from northstar_db import PostgresRepository, Neo4jRepository

from research_portal.dependencies import get_db, get_neo4j
from research_portal.config import settings

router = APIRouter(tags=["Cleanup"])

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


@router.get("/", response_class=HTMLResponse)
async def cleanup_dashboard(
    request: Request,
    db: PostgresRepository = Depends(get_db),
    neo4j: Neo4jRepository = Depends(get_neo4j),
):
    projects = await db.list_projects(limit=50)
    total_sources = 0
    for p in projects:
        sources = await db.list_sources(p.id, limit=9999)
        total_sources += len(sources)

    entity_count = await neo4j.get_entity_count()
    relationship_count = await neo4j.get_relationship_count()

    report = {
        "summary": f"Found {len(projects)} projects, {total_sources} sources, {entity_count} entities, {relationship_count} relationships",
        "projects_count": len(projects),
        "sources_count": total_sources,
        "entities_count": entity_count,
        "relationships_count": relationship_count,
        "read_only": not settings.enable_destructive_cleanup,
    }

    template = env.get_template("cleanup.html")
    content = template.render(
        request=request,
        report=report,
        enable_destructive_cleanup=settings.enable_destructive_cleanup,
    )
    return HTMLResponse(content=content)


@router.post("/execute")
async def execute_cleanup(
    db: PostgresRepository = Depends(get_db),
    neo4j: Neo4jRepository = Depends(get_neo4j),
):
    if not settings.enable_destructive_cleanup:
        raise HTTPException(
            status_code=403,
            detail="Destructive cleanup is disabled. Set ENABLE_DESTRUCTIVE_CLEANUP=true to enable.",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{settings.research_agent_url}/api/v1/cleanup/execute",
            timeout=300.0,
        )
        resp.raise_for_status()
        result = resp.json()

    return {"status": "cleanup_executed", "report": result}
