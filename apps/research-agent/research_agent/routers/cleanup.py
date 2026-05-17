from fastapi import APIRouter, Depends, HTTPException

from northstar_db import Neo4jRepository, PostgresRepository
from northstar_models import CleanupReport

from research_agent.config import settings
from research_agent.dependencies import get_db, get_neo4j

router = APIRouter(prefix="/cleanup", tags=["Cleanup"])


@router.get("/report", response_model=CleanupReport)
async def get_cleanup_report(
    db: PostgresRepository = Depends(get_db),
    neo4j: Neo4jRepository = Depends(get_neo4j),
):
    orphans = []
    suggestions = []
    items_to_review = []

    async with db._session() as session:
        from sqlalchemy import select
        from northstar_models.models import Entity
        result = await session.execute(
            select(Entity).where(Entity.source_id.is_(None))
        )
        orphaned_entities = result.scalars().all()
        for e in orphaned_entities:
            orphans.append(f"Entity '{e.name}' ({e.id}) has no source_id")

    for o in orphans:
        items_to_review.append(o)

    suggestions.append("Review orphaned entities for reattachment or deletion")
    suggestions.append("Run extraction on sources missing entity data")
    suggestions.append(f"Found {len(orphans)} orphaned entities (dry-run only)")

    return CleanupReport(
        summary=f"Cleanup report: {len(orphans)} orphaned entities found. Set ENABLE_DESTRUCTIVE_CLEANUP=true to execute.",
        items_to_review=items_to_review,
        orphans=orphans,
        suggestions=suggestions,
    )


@router.post("/execute", response_model=CleanupReport)
async def execute_cleanup(
    db: PostgresRepository = Depends(get_db),
    neo4j: Neo4jRepository = Depends(get_neo4j),
):
    if not settings.enable_destructive_cleanup:
        raise HTTPException(
            status_code=403,
            detail="Destructive cleanup is disabled. Set ENABLE_DESTRUCTIVE_CLEANUP=true to enable.",
        )

    orphans = []
    items_to_review = []
    deleted_count = 0

    async with db._session() as session:
        from sqlalchemy import delete, select
        from northstar_models.models import Entity
        result = await session.execute(
            select(Entity).where(Entity.source_id.is_(None))
        )
        orphaned_entities = result.scalars().all()
        for e in orphaned_entities:
            orphans.append(f"Entity '{e.name}' ({e.id})")
            await neo4j.delete_entity_node(e.id)
            items_to_review.append(f"Deleted entity '{e.name}' ({e.id})")
            deleted_count += 1

        if orphaned_entities:
            ids = [e.id for e in orphaned_entities]
            await session.execute(
                delete(Entity).where(Entity.id.in_(ids))
            )
            await session.commit()

    suggestions = [
        f"Deleted {deleted_count} orphaned entities",
        "Run extraction on sources missing entity data",
    ]

    return CleanupReport(
        summary=f"Cleanup executed: {deleted_count} orphaned entities deleted.",
        items_to_review=items_to_review,
        orphans=orphans,
        suggestions=suggestions,
    )
