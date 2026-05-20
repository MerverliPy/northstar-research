import uuid
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, delete, and_, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from northstar_models.base import CommonModel
from northstar_models.enums import ExtractionStatus
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
    AnalysisUpdate,
    ClaimCreate,
    ClaimUpdate,
    EntityCreate,
    EntityUpdate,
    ProjectCreate,
    ProjectUpdate,
    ReportCreate,
    ReportUpdate,
    SourceCreate,
    SourceUpdate,
)

logger = structlog.get_logger(__name__)


class PostgresRepository:
    def __init__(
        self,
        database_url: str = "postgresql+asyncpg://localhost:5432/northstar",
        echo: bool = False,
    ):
        self._engine = create_async_engine(
            database_url,
            echo=echo,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def initialize(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(CommonModel.metadata.create_all)
        async with self._session_factory() as session:
            result = await session.execute(select(1))
            result.scalar()
        logger.info("postgres_initialized")

    async def close(self) -> None:
        await self._engine.dispose()
        logger.info("postgres_disposed")

    def _session(self):
        return self._session_factory()

    async def create_project(self, data: ProjectCreate) -> Project:
        async with self._session() as session:
            project = Project(
                name=data.name,
                description=data.description,
                status=data.status,
                metadata_=data.metadata,
            )
            session.add(project)
            await session.commit()
            await session.refresh(project)
            return project

    async def get_project(self, project_id: uuid.UUID) -> Project | None:
        async with self._session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            return result.scalar_one_or_none()

    async def get_project_by_name(self, name: str) -> Project | None:
        async with self._session() as session:
            result = await session.execute(
                select(Project).where(Project.name == name)
            )
            return result.scalar_one_or_none()

    async def list_projects(
        self, limit: int = 50, offset: int = 0
    ) -> list[Project]:
        async with self._session() as session:
            result = await session.execute(
                select(Project).order_by(Project.created_at.desc()).limit(limit).offset(offset)
            )
            return list(result.scalars().all())

    async def update_project(
        self, project_id: uuid.UUID, data: ProjectUpdate
    ) -> Project | None:
        async with self._session() as session:
            result = await session.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()
            if project is None:
                return None
            update_dict = data.model_dump(exclude_unset=True)
            if "metadata" in update_dict:
                update_dict["metadata_"] = update_dict.pop("metadata")
            for field, value in update_dict.items():
                setattr(project, field, value)
            project.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(project)
            return project

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.execute(
                delete(Project).where(Project.id == project_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def count_sources(self, project_id: uuid.UUID) -> int:
        async with self._session() as session:
            result = await session.execute(
                select(func.count(Source.id)).where(Source.project_id == project_id)
            )
            return result.scalar() or 0

    async def count_claims_by_project(self, project_id: uuid.UUID) -> int:
        async with self._session() as session:
            result = await session.execute(
                select(func.count(Claim.id))
                .join(Source, Claim.source_id == Source.id)
                .where(Source.project_id == project_id)
            )
            return result.scalar() or 0

    async def create_source(self, data: SourceCreate) -> Source:
        async with self._session() as session:
            source = Source(
                project_id=data.project_id,
                title=data.title,
                url=data.url,
                content_type=data.content_type,
                raw_content=data.raw_content,
                cleaned_content=data.cleaned_content,
                metadata_=data.metadata,
            )
            session.add(source)
            await session.commit()
            await session.refresh(source)
            return source

    async def get_source(self, source_id: uuid.UUID) -> Source | None:
        async with self._session() as session:
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )
            return result.scalar_one_or_none()

    async def list_sources(
        self, project_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Source]:
        async with self._session() as session:
            result = await session.execute(
                select(Source)
                .where(Source.project_id == project_id)
                .order_by(Source.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def update_source(
        self, source_id: uuid.UUID, data: SourceUpdate
    ) -> Source | None:
        async with self._session() as session:
            result = await session.execute(
                select(Source).where(Source.id == source_id)
            )
            source = result.scalar_one_or_none()
            if source is None:
                return None
            update_dict = data.model_dump(exclude_unset=True)
            if "metadata" in update_dict:
                update_dict["metadata_"] = update_dict.pop("metadata")
            for field, value in update_dict.items():
                setattr(source, field, value)
            source.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(source)
            return source

    async def delete_source(self, source_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.execute(
                delete(Source).where(Source.id == source_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def create_entity(self, data: EntityCreate) -> Entity:
        async with self._session() as session:
            entity = Entity(
                source_id=data.source_id,
                name=data.name,
                entity_type=data.entity_type,
                aliases=data.aliases,
                description=data.description,
                metadata_=data.metadata,
                confidence=data.confidence,
            )
            session.add(entity)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def get_entity(self, entity_id: uuid.UUID) -> Entity | None:
        async with self._session() as session:
            result = await session.execute(
                select(Entity).where(Entity.id == entity_id)
            )
            return result.scalar_one_or_none()

    async def list_entities(
        self,
        source_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Entity]:
        async with self._session() as session:
            query = select(Entity)
            if source_id is not None:
                query = query.where(Entity.source_id == source_id)
            if project_id is not None:
                query = (
                    query.join(Source, Entity.source_id == Source.id)
                    .where(Source.project_id == project_id)
                )
            query = query.order_by(Entity.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_entity(
        self, entity_id: uuid.UUID, data: EntityUpdate
    ) -> Entity | None:
        async with self._session() as session:
            result = await session.execute(
                select(Entity).where(Entity.id == entity_id)
            )
            entity = result.scalar_one_or_none()
            if entity is None:
                return None
            update_dict = data.model_dump(exclude_unset=True)
            if "metadata" in update_dict:
                update_dict["metadata_"] = update_dict.pop("metadata")
            for field, value in update_dict.items():
                setattr(entity, field, value)
            entity.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(entity)
            return entity

    async def delete_entity(self, entity_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.execute(
                delete(Entity).where(Entity.id == entity_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def create_claim(self, data: ClaimCreate) -> Claim:
        async with self._session() as session:
            claim = Claim(
                source_id=data.source_id,
                entity_id=data.entity_id,
                claim_text=data.claim_text,
                claim_type=data.claim_type,
                confidence=data.confidence,
                context=data.context,
                metadata_=data.metadata,
            )
            session.add(claim)
            await session.commit()
            await session.refresh(claim)
            return claim

    async def get_claim(self, claim_id: uuid.UUID) -> Claim | None:
        async with self._session() as session:
            result = await session.execute(
                select(Claim).where(Claim.id == claim_id)
            )
            return result.scalar_one_or_none()

    async def list_claims(
        self,
        source_id: uuid.UUID | None = None,
        entity_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Claim]:
        async with self._session() as session:
            query = select(Claim)
            if source_id is not None:
                query = query.where(Claim.source_id == source_id)
            if entity_id is not None:
                query = query.where(Claim.entity_id == entity_id)
            query = query.order_by(Claim.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def update_claim(
        self, claim_id: uuid.UUID, data: ClaimUpdate
    ) -> Claim | None:
        async with self._session() as session:
            result = await session.execute(
                select(Claim).where(Claim.id == claim_id)
            )
            claim = result.scalar_one_or_none()
            if claim is None:
                return None
            update_dict = data.model_dump(exclude_unset=True)
            if "metadata" in update_dict:
                update_dict["metadata_"] = update_dict.pop("metadata")
            for field, value in update_dict.items():
                setattr(claim, field, value)
            claim.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(claim)
            return claim

    async def delete_claim(self, claim_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.execute(
                delete(Claim).where(Claim.id == claim_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def create_report(self, data: ReportCreate) -> Report:
        async with self._session() as session:
            report = Report(
                project_id=data.project_id,
                title=data.title,
                summary=data.summary,
                report_data=data.report_data,
                metadata_=data.metadata,
            )
            session.add(report)
            await session.commit()
            await session.refresh(report)
            return report

    async def get_report(self, report_id: uuid.UUID) -> Report | None:
        async with self._session() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            return result.scalar_one_or_none()

    async def list_reports(
        self, project_id: uuid.UUID, limit: int = 50, offset: int = 0
    ) -> list[Report]:
        async with self._session() as session:
            result = await session.execute(
                select(Report)
                .where(Report.project_id == project_id)
                .order_by(Report.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return list(result.scalars().all())

    async def update_report(
        self, report_id: uuid.UUID, data: ReportUpdate
    ) -> Report | None:
        async with self._session() as session:
            result = await session.execute(
                select(Report).where(Report.id == report_id)
            )
            report = result.scalar_one_or_none()
            if report is None:
                return None
            update_dict = data.model_dump(exclude_unset=True)
            if "metadata" in update_dict:
                update_dict["metadata_"] = update_dict.pop("metadata")
            for field, value in update_dict.items():
                setattr(report, field, value)
            report.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(report)
            return report

    async def delete_report(self, report_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.execute(
                delete(Report).where(Report.id == report_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def create_analysis(self, data: AnalysisCreate) -> Analysis:
        async with self._session() as session:
            analysis = Analysis(
                source_id=data.source_id,
                project_id=data.project_id,
                analysis_type=data.analysis_type,
                content=data.content,
                model_used=data.model_used,
                quality_score=data.quality_score,
                metadata_=data.metadata,
            )
            session.add(analysis)
            await session.commit()
            await session.refresh(analysis)
            return analysis

    async def get_analysis(self, analysis_id: uuid.UUID) -> Analysis | None:
        async with self._session() as session:
            result = await session.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            return result.scalar_one_or_none()

    async def update_analysis(
        self, analysis_id: uuid.UUID, data: AnalysisUpdate
    ) -> Analysis | None:
        async with self._session() as session:
            result = await session.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            if analysis is None:
                return None
            update_dict = data.model_dump(exclude_unset=True)
            if "metadata" in update_dict:
                update_dict["metadata_"] = update_dict.pop("metadata")
            for field, value in update_dict.items():
                setattr(analysis, field, value)
            analysis.updated_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(analysis)
            return analysis

    async def delete_analysis(self, analysis_id: uuid.UUID) -> bool:
        async with self._session() as session:
            result = await session.execute(
                delete(Analysis).where(Analysis.id == analysis_id)
            )
            await session.commit()
            return result.rowcount > 0

    async def list_analyses(
        self,
        source_id: uuid.UUID | None = None,
        project_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Analysis]:
        async with self._session() as session:
            query = select(Analysis)
            if source_id is not None:
                query = query.where(Analysis.source_id == source_id)
            if project_id is not None:
                query = query.where(Analysis.project_id == project_id)
            query = query.order_by(Analysis.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def latest_analyses_by_source_ids(
        self, source_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, Analysis | None]:
        if not source_ids:
            return {}
        async with self._session() as session:
            subq = (
                select(
                    Analysis.source_id,
                    func.max(Analysis.created_at).label("max_created"),
                )
                .where(Analysis.source_id.in_(source_ids))
                .group_by(Analysis.source_id)
                .subquery()
            )
            result = await session.execute(
                select(Analysis)
                .join(subq, and_(
                    Analysis.source_id == subq.c.source_id,
                    Analysis.created_at == subq.c.max_created,
                ))
            )
            return {a.source_id: a for a in result.scalars().all()}

    async def create_extraction_log(
        self, source_id: uuid.UUID, project_id: uuid.UUID
    ) -> ExtractionLog:
        async with self._session() as session:
            log = ExtractionLog(
                source_id=source_id,
                project_id=project_id,
                status=ExtractionStatus.PENDING,
            )
            session.add(log)
            await session.commit()
            await session.refresh(log)
            return log

    async def update_extraction_log(
        self,
        log_id: uuid.UUID,
        status: ExtractionStatus,
        entities_found: int = 0,
        error_message: str | None = None,
    ) -> ExtractionLog | None:
        async with self._session() as session:
            result = await session.execute(
                select(ExtractionLog).where(ExtractionLog.id == log_id)
            )
            log = result.scalar_one_or_none()
            if log is None:
                return None
            log.status = status
            log.entities_found = entities_found
            if error_message is not None:
                log.error_message = error_message
            if status in (ExtractionStatus.IN_PROGRESS,) and log.status != ExtractionStatus.IN_PROGRESS:
                log.started_at = datetime.now(timezone.utc)
            if status in (ExtractionStatus.COMPLETED, ExtractionStatus.FAILED, ExtractionStatus.SKIPPED):
                if log.completed_at is None:
                    log.completed_at = datetime.now(timezone.utc)
            await session.commit()
            await session.refresh(log)
            return log

    async def get_extraction_log(
        self, source_id: uuid.UUID
    ) -> ExtractionLog | None:
        async with self._session() as session:
            result = await session.execute(
                select(ExtractionLog)
                .where(ExtractionLog.source_id == source_id)
                .order_by(ExtractionLog.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def latest_extraction_logs_by_source_ids(
        self, source_ids: list[uuid.UUID]
    ) -> dict[uuid.UUID, ExtractionLog | None]:
        if not source_ids:
            return {}
        async with self._session() as session:
            subq = (
                select(
                    ExtractionLog.source_id,
                    func.max(ExtractionLog.created_at).label("max_created"),
                )
                .where(ExtractionLog.source_id.in_(source_ids))
                .group_by(ExtractionLog.source_id)
                .subquery()
            )
            result = await session.execute(
                select(ExtractionLog)
                .join(subq, and_(
                    ExtractionLog.source_id == subq.c.source_id,
                    ExtractionLog.created_at == subq.c.max_created,
                ))
            )
            return {e.source_id: e for e in result.scalars().all()}

    async def list_extraction_logs(
        self,
        project_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ExtractionLog]:
        async with self._session() as session:
            query = select(ExtractionLog).order_by(ExtractionLog.created_at.desc())
            if project_id is not None:
                query = query.where(ExtractionLog.project_id == project_id)
            query = query.limit(limit).offset(offset)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def bulk_create_entities(
        self, entities: list[EntityCreate]
    ) -> list[Entity]:
        async with self._session() as session:
            models = [
                Entity(
                    source_id=e.source_id,
                    name=e.name,
                    entity_type=e.entity_type,
                    aliases=e.aliases,
                    description=e.description,
                    metadata_=e.metadata,
                    confidence=e.confidence,
                )
                for e in entities
            ]
            session.add_all(models)
            await session.flush()
            await session.commit()
            return models

    async def bulk_create_claims(
        self, claims: list[ClaimCreate]
    ) -> list[Claim]:
        async with self._session() as session:
            models = [
                Claim(
                    source_id=c.source_id,
                    entity_id=c.entity_id,
                    claim_text=c.claim_text,
                    claim_type=c.claim_type,
                    confidence=c.confidence,
                    context=c.context,
                    metadata_=c.metadata,
                )
                for c in claims
            ]
            session.add_all(models)
            await session.flush()
            await session.commit()
            return models
