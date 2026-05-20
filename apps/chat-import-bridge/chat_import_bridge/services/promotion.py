import uuid

import httpx
from northstar_models.schemas import SourceCreate
from sqlalchemy.ext.asyncio import AsyncSession

from chat_import_bridge.services import staging as svc


async def promote_to_agent(
    research_agent_url: str,
    import_id: int,
    db_session: AsyncSession,
    project_id: str | None = None,
) -> dict:
    staged = await svc.get_staged(db_session, import_id)
    if not staged:
        return {"status": "failed", "source_id": None, "error": "Import not found"}

    if staged.status == "promoted":
        return {"status": "skipped", "source_id": None, "error": "Already promoted"}

    if not project_id:
        return {"status": "failed", "source_id": None, "error": "project_id is required"}
    pid = uuid.UUID(project_id)

    payload = SourceCreate(
        project_id=pid,
        title=staged.title,
        content_type=staged.source_type,
        raw_content=staged.raw_content,
        cleaned_content=staged.cleaned_content,
    )

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{research_agent_url}/api/v1/sources",
                json=payload.model_dump(mode="json"),
            )
            resp.raise_for_status()
            data = resp.json()
            source_id = data.get("id")
            await svc.update_status(db_session, import_id, "promoted")
            return {"status": "promoted", "source_id": source_id, "error": None}
    except httpx.HTTPError as e:
        err_msg = str(e)
        await svc.update_status(db_session, import_id, "failed", err_msg)
        return {"status": "failed", "source_id": None, "error": err_msg}


async def promote_all_pending(
    research_agent_url: str,
    db_session: AsyncSession,
) -> dict:
    pending = await svc.list_staged(db_session, status="pending", limit=1000, offset=0)
    results = []
    succeeded = 0
    failed = 0

    for entry in pending:
        result = await promote_to_agent(research_agent_url, entry.id, db_session=db_session)
        results.append({"import_id": entry.id, **result})
        if result["status"] == "promoted":
            succeeded += 1
        else:
            failed += 1

    return {
        "total": len(pending),
        "succeeded": succeeded,
        "failed": failed,
        "results": results,
    }
