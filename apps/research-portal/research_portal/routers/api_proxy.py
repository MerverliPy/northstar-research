import httpx
import structlog
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from research_portal.config import settings
from research_portal.dependencies import get_neo4j

logger = structlog.get_logger(__name__)

router = APIRouter()

GET = "GET"
POST = "POST"
PUT = "PUT"
DELETE = "DELETE"


def transform_project(agent_project: dict) -> dict:
    return {
        "id": str(agent_project.get("id", "")),
        "name": agent_project.get("topic", ""),
        "description": agent_project.get("topic", "")[:200],
        "metadata": {"status": agent_project.get("status", "")},
        "created_at": agent_project.get("created_at", ""),
        "updated_at": agent_project.get("created_at", ""),
    }


def transform_report(agent_report: dict) -> dict:
    return {
        "id": str(agent_report.get("id", agent_report.get("report_id", ""))),
        "project_id": str(agent_report.get("project_id", "")),
        "title": agent_report.get("title", agent_report.get("topic", "Report")),
        "content": agent_report.get("content", agent_report.get("summary", "")),
        "report_type": agent_report.get("report_type", agent_report.get("type", "summary")),
        "metadata": None,
        "created_at": agent_report.get("created_at", ""),
        "updated_at": agent_report.get("created_at", ""),
    }


def paginated_response(items: list, total: int | None = None, limit: int = 100, offset: int = 0) -> dict:
    return {
        "items": items,
        "total": total if total is not None else len(items),
        "limit": limit,
        "offset": offset,
    }


def _query_params(request: Request) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, values in request.query_params.multi_items():
        result[key] = values
    return result


def _parse_int(val: str | None, default: int = 100) -> int:
    try:
        return int(val) if val else default
    except (ValueError, TypeError):
        return default


async def _agent_get(client: httpx.AsyncClient, url: str, params: dict | None = None) -> list[dict]:
    try:
        resp = await client.get(url, params=params)
        if resp.status_code == 200:
            data = resp.json()
            return data if isinstance(data, list) else []
    except Exception:
        logger.warning("agent_proxy_failed", url=url, exc_info=True)
    return []


@router.api_route("/{path:path}", methods=[GET, POST, PUT, DELETE])
async def api_v1_handler(request: Request, path: str):
    client: httpx.AsyncClient = request.app.state.http_client
    agent_base = f"{settings.research_agent_url.rstrip('/')}/api/v1"
    method = request.method
    params = _query_params(request)
    limit = _parse_int(params.get("limit"), 100)
    offset = _parse_int(params.get("offset"), 0)

    if path.rstrip("/") == "projects":
        if method == GET:
            items_raw = await _agent_get(client, f"{agent_base}/projects")
            items = [transform_project(p) for p in items_raw]
            total = len(items)
            paged = items[offset:offset + limit]
            return paginated_response(paged, total, limit, offset)

        if method == POST:
            body = await request.json()
            topic = body.get("name", body.get("topic", ""))
            try:
                resp = await client.post(f"{agent_base}/projects", json={"name": topic})
                if resp.status_code in (200, 201):
                    agent_proj = resp.json()
                    if isinstance(agent_proj, dict):
                        return transform_project(agent_proj)
            except Exception:
                logger.warning("agent_proxy_failed", endpoint="/projects", exc_info=True)
            return JSONResponse({"detail": "Failed to create project"}, status_code=502)

        if method == PUT:
            return JSONResponse({"detail": "Update not supported via agent"}, status_code=501)

        if method == DELETE:
            return JSONResponse({"detail": "Delete not supported via agent"}, status_code=501)

    if path.rstrip("/") == "reports":
        if method == GET:
            project_id = params.get("project_id")
            reports: list[dict] = []
            if project_id and project_id != "all":
                try:
                    resp = await client.get(f"{agent_base}/reports")
                    if resp.status_code == 200:
                        all_reports = resp.json()
                        if isinstance(all_reports, list):
                            reports = [r for r in all_reports if str(r.get("project_id", "")) == project_id]
                except Exception:
                    logger.warning("agent_proxy_failed", endpoint="/reports", exc_info=True)
            else:
                reports = await _agent_get(client, f"{agent_base}/reports")
            items = [transform_report(r) for r in reports]
            total = len(items)
            paged = items[offset:offset + limit]
            return paginated_response(paged, total, limit, offset)

        if method in (POST, PUT, DELETE):
            return JSONResponse({"detail": "Reports CRUD not supported via agent"}, status_code=501)

    if path.rstrip("/") == "sources":
        return paginated_response([], 0, limit, offset)

    if path.rstrip("/") == "entities":
        if method == GET:
            try:
                resp = await client.get(f"{agent_base}/knowledge/entities", params={"limit": limit} if not params.get("project_id") else params)
                if resp.status_code == 200:
                    data = resp.json()
                    items = data if isinstance(data, list) else data.get("items", data.get("entities", []))
                    if isinstance(items, list):
                        transformed = [
                            {
                                "id": str(e.get("id", "")),
                                "source_id": str(e.get("source_id", "")) if e.get("source_id") else None,
                                "project_id": str(e.get("project_id", "")) if e.get("project_id") else None,
                                "name": e.get("name", e.get("label", "")),
                                "entity_type": e.get("entity_type", e.get("type", "unknown")),
                                "description": e.get("description", ""),
                                "metadata": None,
                                "created_at": e.get("created_at", ""),
                                "updated_at": e.get("created_at", ""),
                            }
                            for e in items
                        ]
                        return paginated_response(transformed)
            except Exception:
                logger.warning("agent_proxy_failed", endpoint="/knowledge/entities", exc_info=True)
        return paginated_response([], 0, limit, offset)

    if path.rstrip("/") == "claims":
        return paginated_response([], 0, limit, offset)

    if path.startswith("graph/data/"):
        project_id = path.split("/")[-1]
        try:
            neo4j = await anext(get_neo4j())
            graph_data = await neo4j.get_project_graph(project_id)
            return graph_data
        except Exception:
            logger.warning("agent_proxy_failed", endpoint="graph/data", exc_info=True)
            return {"nodes": [], "edges": []}

    target_url = f"{agent_base}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    body_bytes = await request.body() if method in (POST, PUT) else None
    headers = {}
    for key in ("accept", "accept-encoding", "user-agent"):
        if key in dict(request.headers):
            headers[key] = request.headers[key]
    if method in (POST, PUT):
        headers["content-type"] = request.headers.get("content-type", "application/json")

    try:
        resp = await client.request(
            method=method,
            url=target_url,
            headers=headers,
            content=body_bytes,
        )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except httpx.ConnectError:
        return JSONResponse({"detail": "Research agent unavailable"}, status_code=503)
