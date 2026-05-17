import uuid

from fastapi import APIRouter, Depends, HTTPException

from northstar_db import PostgresRepository
from northstar_models import ProjectCreate, ProjectRead, ProjectUpdate

from research_agent.dependencies import get_db

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectRead])
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    db: PostgresRepository = Depends(get_db),
):
    projects = await db.list_projects(limit=limit, offset=offset)
    return [ProjectRead.model_validate(p) for p in projects]


@router.post("/", response_model=ProjectRead, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: PostgresRepository = Depends(get_db),
):
    project = await db.create_project(data)
    return ProjectRead.model_validate(project)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    project = await db.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project)


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    data: ProjectUpdate,
    db: PostgresRepository = Depends(get_db),
):
    project = await db.update_project(project_id, data)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRead.model_validate(project)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: uuid.UUID,
    db: PostgresRepository = Depends(get_db),
):
    deleted = await db.delete_project(project_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Project not found")
