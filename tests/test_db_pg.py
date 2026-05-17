import uuid

import pytest

from northstar_models.enums import EntityType, ExtractionStatus, ProjectStatus
from northstar_models.schemas import (
    AnalysisCreate,
    ClaimCreate,
    EntityCreate,
    ProjectCreate,
    ProjectUpdate,
    ReportCreate,
    SourceCreate,
)

pytestmark = pytest.mark.asyncio


def pg_available():
    try:
        import sqlalchemy
        import asyncpg
        return True
    except ImportError:
        return False


class TestProjectCRUD:
    async def test_create_project(self, mock_db):
        data = ProjectCreate(name="Test Project", description="Test", status=ProjectStatus.ACTIVE)
        project = await mock_db.create_project(data)
        assert project.name == "Test Project"
        mock_db.create_project.assert_awaited_once_with(data)

    async def test_get_project(self, mock_db):
        pid = uuid.uuid4()
        project = await mock_db.get_project(pid)
        assert project is not None
        mock_db.get_project.assert_awaited_once_with(pid)

    async def test_get_project_not_found(self, mock_db):
        mock_db.get_project.return_value = None
        result = await mock_db.get_project(uuid.uuid4())
        assert result is None

    async def test_list_projects(self, mock_db):
        projects = await mock_db.list_projects(limit=10, offset=0)
        assert len(projects) > 0
        mock_db.list_projects.assert_awaited_once_with(limit=10, offset=0)

    async def test_update_project(self, mock_db):
        pid = uuid.uuid4()
        data = ProjectUpdate(name="Updated")
        project = await mock_db.update_project(pid, data)
        assert project is not None
        mock_db.update_project.assert_awaited_once_with(pid, data)

    async def test_update_project_not_found(self, mock_db):
        mock_db.update_project.return_value = None
        result = await mock_db.update_project(uuid.uuid4(), ProjectUpdate())
        assert result is None

    async def test_delete_project(self, mock_db):
        pid = uuid.uuid4()
        result = await mock_db.delete_project(pid)
        assert result is True
        mock_db.delete_project.assert_awaited_once_with(pid)

    async def test_delete_project_not_found(self, mock_db):
        mock_db.delete_project.return_value = False
        result = await mock_db.delete_project(uuid.uuid4())
        assert result is False

    async def test_get_project_by_name(self, mock_db):
        project = await mock_db.get_project_by_name("Test")
        assert project is not None


class TestSourceCRUD:
    async def test_create_source(self, mock_db):
        data = SourceCreate(
            project_id=uuid.uuid4(),
            title="Source 1",
            content_type="text",
            raw_content="content",
        )
        source = await mock_db.create_source(data)
        assert source is not None

    async def test_get_source(self, mock_db):
        sid = uuid.uuid4()
        source = await mock_db.get_source(sid)
        assert source is not None

    async def test_get_source_not_found(self, mock_db):
        mock_db.get_source.return_value = None
        result = await mock_db.get_source(uuid.uuid4())
        assert result is None

    async def test_list_sources(self, mock_db):
        sources = await mock_db.list_sources(project_id=uuid.uuid4())
        assert len(sources) > 0

    async def test_delete_source(self, mock_db):
        sid = uuid.uuid4()
        result = await mock_db.delete_source(sid)
        assert result is True

    async def test_delete_source_not_found(self, mock_db):
        mock_db.delete_source.return_value = False
        result = await mock_db.delete_source(uuid.uuid4())
        assert result is False


class TestEntityCRUD:
    async def test_create_entity(self, mock_db):
        data = EntityCreate(name="Entity 1", entity_type=EntityType.ORGANIZATION)
        entity = await mock_db.create_entity(data)
        assert entity is not None

    async def test_get_entity(self, mock_db):
        eid = uuid.uuid4()
        entity = await mock_db.get_entity(eid)
        assert entity is not None

    async def test_get_entity_not_found(self, mock_db):
        mock_db.get_entity.return_value = None
        result = await mock_db.get_entity(uuid.uuid4())
        assert result is None

    async def test_list_entities(self, mock_db):
        entities = await mock_db.list_entities(source_id=uuid.uuid4())
        assert len(entities) > 0

    async def test_delete_entity(self, mock_db):
        eid = uuid.uuid4()
        result = await mock_db.delete_entity(eid)
        assert result is True

    async def test_bulk_create_entities(self, mock_db):
        entities = [
            EntityCreate(name="E1", entity_type=EntityType.PERSON),
            EntityCreate(name="E2", entity_type=EntityType.ORGANIZATION),
        ]
        results = await mock_db.bulk_create_entities(entities)
        assert len(results) == 1


class TestClaimCRUD:
    async def test_create_claim(self, mock_db):
        data = ClaimCreate(claim_text="Claim 1")
        claim = await mock_db.create_claim(data)
        assert claim is not None

    async def test_get_claim(self, mock_db):
        cid = uuid.uuid4()
        claim = await mock_db.get_claim(cid)
        assert claim is not None

    async def test_get_claim_not_found(self, mock_db):
        mock_db.get_claim.return_value = None
        result = await mock_db.get_claim(uuid.uuid4())
        assert result is None

    async def test_list_claims(self, mock_db):
        claims = await mock_db.list_claims(source_id=uuid.uuid4())
        assert len(claims) > 0

    async def test_delete_claim(self, mock_db):
        cid = uuid.uuid4()
        result = await mock_db.delete_claim(cid)
        assert result is True

    async def test_bulk_create_claims(self, mock_db):
        claims = [
            ClaimCreate(claim_text="C1"),
            ClaimCreate(claim_text="C2"),
        ]
        results = await mock_db.bulk_create_claims(claims)
        assert len(results) == 1


class TestReportCRUD:
    async def test_create_report(self, mock_db):
        data = ReportCreate(project_id=uuid.uuid4(), title="Report 1")
        report = await mock_db.create_report(data)
        assert report is not None

    async def test_get_report(self, mock_db):
        rid = uuid.uuid4()
        report = await mock_db.get_report(rid)
        assert report is not None

    async def test_get_report_not_found(self, mock_db):
        mock_db.get_report.return_value = None
        result = await mock_db.get_report(uuid.uuid4())
        assert result is None

    async def test_list_reports(self, mock_db):
        reports = await mock_db.list_reports(project_id=uuid.uuid4())
        assert len(reports) > 0

    async def test_delete_report(self, mock_db):
        rid = uuid.uuid4()
        result = await mock_db.delete_report(rid)
        assert result is True


class TestAnalysisCRUD:
    async def test_create_analysis(self, mock_db):
        data = AnalysisCreate(analysis_type="quality", content={"score": 0.9})
        analysis = await mock_db.create_analysis(data)
        assert analysis is not None

    async def test_list_analyses(self, mock_db):
        analyses = await mock_db.list_analyses(source_id=uuid.uuid4())
        assert len(analyses) > 0

    async def test_list_analyses_by_project(self, mock_db):
        analyses = await mock_db.list_analyses(project_id=uuid.uuid4())
        assert len(analyses) > 0


class TestExtractionLog:
    async def test_create_extraction_log(self, mock_db):
        log = await mock_db.create_extraction_log(source_id=uuid.uuid4(), project_id=uuid.uuid4())
        assert log is not None

    async def test_get_extraction_log(self, mock_db):
        log = await mock_db.get_extraction_log(source_id=uuid.uuid4())
        assert log is not None

    async def test_update_extraction_log(self, mock_db):
        log = await mock_db.update_extraction_log(
            log_id=uuid.uuid4(),
            status=ExtractionStatus.COMPLETED,
            entities_found=5,
        )
        assert log is not None

    async def test_update_extraction_log_not_found(self, mock_db):
        mock_db.update_extraction_log.return_value = None
        result = await mock_db.update_extraction_log(
            log_id=uuid.uuid4(),
            status=ExtractionStatus.FAILED,
        )
        assert result is None
