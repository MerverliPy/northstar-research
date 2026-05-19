from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from northstar_db import PostgresRepository, Neo4jRepository

from research_portal.dependencies import get_db, get_neo4j
from research_portal.template_utils import env

router = APIRouter(tags=["Dashboard"])


@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: PostgresRepository = Depends(get_db),
    neo4j: Neo4jRepository = Depends(get_neo4j),
):
    projects = await db.list_projects(limit=10)
    project_count = len(projects)

    source_count = sum(len(await db.list_sources(p.id, limit=9999)) for p in projects)

    entity_count = await neo4j.get_entity_count()

    claim_count = 0
    for p in projects:
        sources = await db.list_sources(p.id, limit=9999)
        for s in sources:
            claims = await db.list_claims(source_id=s.id, limit=9999)
            claim_count += len(claims)

    recent_projects = [
        {
            "id": str(p.id),
            "name": p.name,
            "status": p.status.value if hasattr(p.status, 'value') else str(p.status),
            "created_at": p.created_at.isoformat() if hasattr(p.created_at, 'isoformat') else str(p.created_at),
        }
        for p in projects
    ]

    template = env.get_template("dashboard.html")
    content = template.render(
        request=request,
        project_count=project_count,
        source_count=source_count,
        entity_count=entity_count,
        claim_count=claim_count,
        recent_projects=recent_projects,
    )
    return HTMLResponse(content=content)
