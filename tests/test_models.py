import uuid
from datetime import datetime

import pytest

from northstar_models.enums import (
    EntityType,
    ExtractionStatus,
    LLMTask,
    ProjectStatus,
    QualityStatus,
)
from northstar_models.models import (
    Analysis,
    Claim,
    Entity,
    ExtractionLog,
    Project,
    Report,
    Source,
)
from northstar_models.schemas import (
    AnalysisCreate,
    AnalysisRead,
    ClaimCreate,
    ClaimRead,
    CleanupReport,
    EntityCreate,
    EntityRead,
    ExtractionLogRead,
    ExtractionRequest,
    ExtractionResponse,
    PaginatedResponse,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    QualityScoreRequest,
    QualityScoreResponse,
    ReportCreate,
    ReportRead,
    SearchRequest,
    SearchResult,
    SourceCreate,
    SourceRead,
    SourceUpdate,
)


class TestEnums:
    def test_project_status_values(self):
        assert ProjectStatus.DRAFT == "draft"
        assert ProjectStatus.ACTIVE == "active"
        assert ProjectStatus.ARCHIVED == "archived"
        assert len(ProjectStatus) == 3

    def test_extraction_status_values(self):
        assert ExtractionStatus.PENDING == "pending"
        assert ExtractionStatus.IN_PROGRESS == "in_progress"
        assert ExtractionStatus.COMPLETED == "completed"
        assert ExtractionStatus.FAILED == "failed"
        assert ExtractionStatus.SKIPPED == "skipped"
        assert len(ExtractionStatus) == 5

    def test_entity_type_values(self):
        assert EntityType.ORGANIZATION == "organization"
        assert EntityType.PERSON == "person"
        assert EntityType.CONCEPT == "concept"
        assert EntityType.TECHNOLOGY == "technology"
        assert EntityType.LOCATION == "location"
        assert EntityType.EVENT == "event"
        assert EntityType.PRODUCT == "product"
        assert EntityType.DOCUMENT == "document"
        assert EntityType.OTHER == "other"
        assert len(EntityType) == 9

    def test_quality_status_values(self):
        assert QualityStatus.PENDING == "pending"
        assert QualityStatus.IN_PROGRESS == "in_progress"
        assert QualityStatus.ASSESSED == "assessed"
        assert QualityStatus.FAILED == "failed"
        assert len(QualityStatus) == 4

    def test_llm_task_values(self):
        assert LLMTask.EXTRACTION == "extraction"
        assert LLMTask.QUALITY == "quality"
        assert LLMTask.SUMMARIZATION == "summarization"
        assert LLMTask.SEARCH == "search"
        assert LLMTask.CLASSIFICATION == "classification"
        assert len(LLMTask) == 5


class TestPydanticSchemas:
    def test_project_create_defaults(self):
        data = ProjectCreate(name="Test Project")
        assert data.name == "Test Project"
        assert data.description is None
        assert data.status == ProjectStatus.DRAFT
        assert data.metadata is None

    def test_project_create_full(self):
        data = ProjectCreate(
            name="Full Project",
            description="A full project",
            status=ProjectStatus.ACTIVE,
            metadata={"key": "value"},
        )
        assert data.name == "Full Project"
        assert data.description == "A full project"
        assert data.status == ProjectStatus.ACTIVE
        assert data.metadata == {"key": "value"}

    def test_project_read_from_attributes(self):
        now = datetime.now()
        data = ProjectRead(
            id=uuid.uuid4(),
            name="Read Project",
            description="Read desc",
            status=ProjectStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        assert data.name == "Read Project"
        assert data.model_config["from_attributes"] is True

    def test_project_update_empty(self):
        data = ProjectUpdate()
        assert data.name is None
        assert data.description is None
        assert data.status is None

    def test_source_create(self):
        pid = uuid.uuid4()
        data = SourceCreate(
            project_id=pid,
            title="Test Source",
            content_type="text",
            raw_content="some raw content",
        )
        assert data.project_id == pid
        assert data.title == "Test Source"
        assert data.raw_content == "some raw content"

    def test_entity_create(self):
        data = EntityCreate(name="Test Entity", entity_type=EntityType.ORGANIZATION)
        assert data.name == "Test Entity"
        assert data.entity_type == EntityType.ORGANIZATION

    def test_claim_create(self):
        data = ClaimCreate(claim_text="Test claim")
        assert data.claim_text == "Test claim"
        assert data.confidence is None

    def test_report_create(self):
        pid = uuid.uuid4()
        data = ReportCreate(project_id=pid, title="Report 1")
        assert data.project_id == pid
        assert data.title == "Report 1"

    def test_analysis_create(self):
        data = AnalysisCreate(
            analysis_type="quality",
            content={"score": 0.9},
        )
        assert data.analysis_type == "quality"
        assert data.content == {"score": 0.9}

    def test_paginated_response(self):
        data = PaginatedResponse[int](items=[1, 2, 3], total=3, page=1, page_size=10)
        assert data.items == [1, 2, 3]
        assert data.total == 3
        assert data.page == 1

    def test_quality_score_request(self):
        sid = uuid.uuid4()
        data = QualityScoreRequest(
            source_id=sid,
            content="test content",
            criteria={"relevance": "high"},
        )
        assert data.source_id == sid
        assert data.content == "test content"

    def test_quality_score_response(self):
        data = QualityScoreResponse(
            quality_status=QualityStatus.ASSESSED,
            score=0.85,
            reasoning="Good quality",
            model_used="qwen3:14b",
        )
        assert data.score == 0.85
        assert data.quality_status == QualityStatus.ASSESSED

    def test_extraction_request(self):
        sid = uuid.uuid4()
        data = ExtractionRequest(source_id=sid, force=True)
        assert data.source_id == sid
        assert data.force is True

    def test_extraction_response(self):
        eid = uuid.uuid4()
        data = ExtractionResponse(
            extraction_id=eid,
            status=ExtractionStatus.PENDING,
            message="Queued",
            entities_count=0,
        )
        assert data.extraction_id == eid
        assert data.message == "Queued"

    def test_search_request(self):
        pid = uuid.uuid4()
        data = SearchRequest(query="test query", project_id=pid)
        assert data.query == "test query"
        assert data.project_id == pid

    def test_search_result(self):
        sid = uuid.uuid4()
        data = SearchResult(
            content="result content",
            score=0.95,
            metadata={"key": "val"},
            source_id=sid,
        )
        assert data.score == 0.95
        assert data.content == "result content"

    def test_cleanup_report(self):
        data = CleanupReport(
            summary="Test cleanup",
            items_to_review=["item1"],
            orphans=["orphan1"],
            suggestions=["suggestion1"],
        )
        assert data.summary == "Test cleanup"
        assert len(data.items_to_review) == 1

    def test_source_update(self):
        data = SourceUpdate(title="New Title")
        assert data.title == "New Title"
        assert data.url is None

    def test_extraction_log_read_from_attributes(self):
        now = datetime.now()
        data = ExtractionLogRead(
            id=uuid.uuid4(),
            source_id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            status=ExtractionStatus.COMPLETED,
            entities_found=5,
            created_at=now,
            updated_at=now,
        )
        assert data.entities_found == 5

    def test_paginated_response_generic_strings(self):
        data = PaginatedResponse[str](items=["a", "b"], total=2, page=1, page_size=2)
        assert data.items == ["a", "b"]

    def test_entity_read_from_attributes(self):
        now = datetime.now()
        data = EntityRead(
            id=uuid.uuid4(),
            name="Entity",
            entity_type=EntityType.PERSON,
            created_at=now,
        )
        assert data.name == "Entity"

    def test_claim_read_from_attributes(self):
        now = datetime.now()
        data = ClaimRead(
            id=uuid.uuid4(),
            claim_text="Claim",
            created_at=now,
        )
        assert data.claim_text == "Claim"

    def test_report_read_from_attributes(self):
        now = datetime.now()
        data = ReportRead(
            id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            title="Report",
            created_at=now,
            updated_at=now,
        )
        assert data.title == "Report"

    def test_analysis_read_from_attributes(self):
        now = datetime.now()
        data = AnalysisRead(
            id=uuid.uuid4(),
            analysis_type="quality",
            content={"score": 0.8},
            created_at=now,
        )
        assert data.analysis_type == "quality"


class TestSQLAlchemyModels:
    def test_project_defaults(self):
        p = Project(name="Test")
        assert p.name == "Test"
        assert p.description is None
        assert p.metadata_ is None

    def test_source_defaults(self):
        s = Source(project_id=uuid.uuid4(), title="Src", content_type="text", raw_content="raw")
        assert s.cleaned_content is None

    def test_entity_defaults(self):
        e = Entity(name="Ent", entity_type=EntityType.CONCEPT)
        assert e.confidence is None
        assert e.source_id is None

    def test_claim_defaults(self):
        c = Claim(claim_text="text")
        assert c.confidence is None
        assert c.entity_id is None

    def test_report_defaults(self):
        r = Report(project_id=uuid.uuid4(), title="R")
        assert r.summary is None

    def test_analysis_defaults(self):
        a = Analysis(analysis_type="type", content={})
        assert a.quality_score is None

    def test_extraction_log_defaults(self):
        e = ExtractionLog(source_id=uuid.uuid4(), project_id=uuid.uuid4(), status=ExtractionStatus.PENDING)
        assert e.entities_found is None or e.entities_found == 0
        assert e.error_message is None

    def test_project_has_uuid_id(self):
        p = Project(name="UUID Test")
        assert p.id is None or isinstance(p.id, uuid.UUID)

    def test_source_has_timestamps(self):
        s = Source(project_id=uuid.uuid4(), title="S", content_type="t", raw_content="r")
        assert s.created_at is None or s.created_at is not None
