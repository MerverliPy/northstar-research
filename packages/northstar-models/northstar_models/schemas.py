import uuid
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

from northstar_models.enums import (
    EntityType,
    ExtractionStatus,
    ProjectStatus,
    QualityStatus,
)

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: ProjectStatus = ProjectStatus.DRAFT
    metadata: Optional[dict[str, Any]] = None


class ProjectRead(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: ProjectStatus
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    metadata: Optional[dict[str, Any]] = None


class SourceCreate(BaseModel):
    project_id: uuid.UUID
    title: str
    url: Optional[str] = None
    content_type: str
    raw_content: str
    cleaned_content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class SourceRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    url: Optional[str] = None
    content_type: str
    raw_content: str
    cleaned_content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceUpdate(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
    content_type: Optional[str] = None
    raw_content: Optional[str] = None
    cleaned_content: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class EntityCreate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    name: str
    entity_type: EntityType
    aliases: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None


class EntityRead(BaseModel):
    id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    name: str
    entity_type: EntityType
    aliases: Optional[dict[str, Any]] = None
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    confidence: Optional[float] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClaimCreate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    entity_id: Optional[uuid.UUID] = None
    claim_text: str
    claim_type: Optional[str] = None
    confidence: Optional[float] = None
    context: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ClaimRead(BaseModel):
    id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    entity_id: Optional[uuid.UUID] = None
    claim_text: str
    claim_type: Optional[str] = None
    confidence: Optional[float] = None
    context: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportCreate(BaseModel):
    project_id: uuid.UUID
    title: str
    summary: Optional[str] = None
    report_data: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class ReportRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    summary: Optional[str] = None
    report_data: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisCreate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    analysis_type: str
    content: dict[str, Any]
    model_used: Optional[str] = None
    quality_score: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class AnalysisRead(BaseModel):
    id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    analysis_type: str
    content: dict[str, Any]
    model_used: Optional[str] = None
    quality_score: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ExtractionLogRead(BaseModel):
    id: uuid.UUID
    source_id: uuid.UUID
    project_id: uuid.UUID
    status: ExtractionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    entities_found: int = 0
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QualityScoreRequest(BaseModel):
    source_id: uuid.UUID
    content: str
    criteria: dict[str, Any]


class QualityScoreResponse(BaseModel):
    quality_status: QualityStatus
    score: float
    reasoning: str
    model_used: str


class ExtractionRequest(BaseModel):
    source_id: uuid.UUID
    force: bool = False


class ExtractionResponse(BaseModel):
    extraction_id: uuid.UUID
    status: ExtractionStatus
    message: str
    entities_count: int


class SearchRequest(BaseModel):
    query: str
    project_id: uuid.UUID
    top_k: int = 5
    filters: Optional[dict[str, Any]] = None


class SearchResult(BaseModel):
    content: str
    score: float
    metadata: dict[str, Any]
    source_id: uuid.UUID


class CleanupReport(BaseModel):
    summary: str
    items_to_review: list[str]
    orphans: list[str]
    suggestions: list[str]
