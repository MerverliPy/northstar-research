import uuid
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field

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
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class EntityRead(BaseModel):
    id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    name: str
    entity_type: EntityType
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class EntityUpdate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    name: Optional[str] = None
    entity_type: Optional[EntityType] = None
    aliases: Optional[list[str]] = None
    description: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class ClaimCreate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    entity_id: Optional[uuid.UUID] = None
    claim_text: str
    claim_type: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    context: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ClaimUpdate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    entity_id: Optional[uuid.UUID] = None
    claim_text: Optional[str] = None
    claim_type: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    context: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


class ClaimRead(BaseModel):
    id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    entity_id: Optional[uuid.UUID] = None
    claim_text: str
    claim_type: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    context: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReportCreate(BaseModel):
    project_id: uuid.UUID
    title: str
    summary: Optional[str] = None
    report_data: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


class ReportUpdate(BaseModel):
    title: Optional[str] = None
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
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[dict[str, Any]] = None


class AnalysisUpdate(BaseModel):
    source_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    analysis_type: Optional[str] = None
    content: Optional[dict[str, Any]] = None
    model_used: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[dict[str, Any]] = None


class AnalysisRead(BaseModel):
    id: uuid.UUID
    source_id: Optional[uuid.UUID] = None
    project_id: Optional[uuid.UUID] = None
    analysis_type: str
    content: dict[str, Any]
    model_used: Optional[str] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    metadata: Optional[dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExtractionLogCreate(BaseModel):
    source_id: uuid.UUID
    project_id: uuid.UUID
    status: ExtractionStatus = ExtractionStatus.PENDING
    entities_found: int = 0
    metadata: Optional[dict[str, Any]] = None


class ExtractionLogUpdate(BaseModel):
    status: Optional[ExtractionStatus] = None
    entities_found: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None


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
    source_id: uuid.UUID | None = None


class CleanupReport(BaseModel):
    summary: str
    items_to_review: list[str]
    orphans: list[str]
    suggestions: list[str]


class ScraperProxy(BaseModel):
    server: str
    username: Optional[str] = None
    password: Optional[str] = None


class ScraperFingerprint(BaseModel):
    seed: Optional[int] = None
    platform: Optional[str] = None
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    hardware_concurrency: Optional[int] = None
    user_agent: Optional[str] = None


class ScrapeRequest(BaseModel):
    project_id: uuid.UUID
    url: str
    title: Optional[str] = None
    proxy: Optional[ScraperProxy] = None
    fingerprint: Optional[ScraperFingerprint] = None
    extract: bool = False
    headless: bool = True
    wait_until: str = "networkidle"
    max_content_length: int = 10000


class ScrapeResponse(BaseModel):
    source: SourceRead
    title: str
    url: str
    word_count: int
    fingerprint_seed: Optional[int] = None
    took_ms: int
