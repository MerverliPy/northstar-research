import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from northstar_db import PostgresRepository
from northstar_models import ReportCreate, ReportRead

from research_agent.dependencies import get_db

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", response_model=list[ReportRead])
async def list_reports(
    project_id: uuid.UUID = Query(...),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = 0,
    db: PostgresRepository = Depends(get_db),
):
    reports = await db.list_reports(project_id=project_id, limit=limit, offset=offset)
    return [ReportRead.model_validate(r) for r in reports]


@router.post("/", response_model=ReportRead, status_code=201)
async def create_report(
    data: ReportCreate,
    db: PostgresRepository = Depends(get_db),
):
    report = await db.create_report(data)
    return ReportRead.model_validate(report)


@router.get("/{report_id}", response_model=ReportRead)
async def get_report(
    report_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    report = await db.get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return ReportRead.model_validate(report)


@router.delete("/{report_id}", status_code=204)
async def delete_report(
    report_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    deleted = await db.delete_report(report_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Report not found")
