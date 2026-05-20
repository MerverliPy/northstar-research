import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from northstar_models.base import CommonModel
from northstar_models.enums import EntityType, ExtractionStatus, ProjectStatus


class Project(CommonModel):
    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus]
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    sources: Mapped[list["Source"]] = relationship(back_populates="project")
    reports: Mapped[list["Report"]] = relationship(back_populates="project")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="project")
    extraction_logs: Mapped[list["ExtractionLog"]] = relationship(back_populates="project")


class Source(CommonModel):
    __tablename__ = "sources"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str]
    url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_type: Mapped[str]
    raw_content: Mapped[str] = mapped_column(Text)
    cleaned_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="sources")
    entities: Mapped[list["Entity"]] = relationship(back_populates="source")
    claims: Mapped[list["Claim"]] = relationship(back_populates="source")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="source")
    extraction_logs: Mapped[list["ExtractionLog"]] = relationship(back_populates="source")


class Entity(CommonModel):
    __tablename__ = "entities"

    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=True)
    name: Mapped[str]
    entity_type: Mapped[EntityType]
    aliases: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)

    source: Mapped[Optional["Source"]] = relationship(back_populates="entities")
    claims: Mapped[list["Claim"]] = relationship(back_populates="entity")


class Claim(CommonModel):
    __tablename__ = "claims"

    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=True)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("entities.id", ondelete="CASCADE"), nullable=True)
    claim_text: Mapped[str] = mapped_column(Text)
    claim_type: Mapped[Optional[str]] = mapped_column(nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    context: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    source: Mapped[Optional["Source"]] = relationship(back_populates="claims")
    entity: Mapped[Optional["Entity"]] = relationship(back_populates="claims")


class Report(CommonModel):
    __tablename__ = "reports"

    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    title: Mapped[str]
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    report_data: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    project: Mapped["Project"] = relationship(back_populates="reports")


class Analysis(CommonModel):
    __tablename__ = "analyses"

    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=True)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    analysis_type: Mapped[str]
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    model_used: Mapped[Optional[str]] = mapped_column(nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    source: Mapped[Optional["Source"]] = relationship(back_populates="analyses")
    project: Mapped[Optional["Project"]] = relationship(back_populates="analyses")


class ExtractionLog(CommonModel):
    __tablename__ = "extraction_logs"
    __table_args__ = (
        UniqueConstraint("source_id", "project_id", name="uq_extraction_log_source_project"),
    )

    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"))
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    status: Mapped[ExtractionStatus]
    started_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    entities_found: Mapped[int] = mapped_column(default=0)
    metadata_: Mapped[Optional[dict[str, Any]]] = mapped_column("metadata", JSON, nullable=True)

    source: Mapped["Source"] = relationship(back_populates="extraction_logs")
    project: Mapped["Project"] = relationship(back_populates="extraction_logs")
