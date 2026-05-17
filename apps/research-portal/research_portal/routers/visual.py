import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from northstar_db import Neo4jRepository, PostgresRepository

from research_portal.dependencies import get_db, get_neo4j

router = APIRouter(tags=["Graph"])

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = BASE_DIR / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


@router.get("/", response_class=HTMLResponse)
async def graph_viewer(
    request: Request,
    db: PostgresRepository = Depends(get_db),
):
    projects = await db.list_projects(limit=100)
    project_list = [{"id": str(p.id), "name": p.name} for p in projects]

    template = env.get_template("graph_viewer.html")
    content = template.render(
        request=request,
        projects=project_list,
    )
    return HTMLResponse(content=content)


@router.get("/data/{project_id}")
async def graph_data(
    project_id: str,
    neo4j: Neo4jRepository = Depends(get_neo4j),
):
    project_uuid = uuid.UUID(project_id)
    graph = await neo4j.get_project_graph(project_uuid)

    nodes = []
    for n in graph.get("nodes", []):
        props = n.get("properties", {})
        node_id = n.get("id")
        label = props.get("name") or props.get("title") or node_id or "unknown"
        group = "entity"
        labels = n.get("labels", [])
        if "Source" in labels:
            group = "source"
        elif "Entity" in labels:
            group = props.get("entity_type", "entity")

        nodes.append({
            "id": str(node_id) if node_id else "unknown",
            "label": str(label),
            "group": str(group),
        })

    edges = []
    for e in graph.get("edges", []):
        edges.append({
            "from": str(e.get("source", "")),
            "to": str(e.get("target", "")),
            "label": str(e.get("type", "")),
        })

    return {"nodes": nodes, "edges": edges}
