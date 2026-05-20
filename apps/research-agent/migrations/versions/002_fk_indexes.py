"""Add FK indexes on all foreign key columns to prevent sequential scans.

Revision ID: 002
Revises: 001
Create Date: 2026-05-20 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_sources_project_id", "sources", ["project_id"])
    op.create_index("ix_entities_source_id", "entities", ["source_id"])
    op.create_index("ix_claims_source_id", "claims", ["source_id"])
    op.create_index("ix_claims_entity_id", "claims", ["entity_id"])
    op.create_index("ix_reports_project_id", "reports", ["project_id"])
    op.create_index("ix_analyses_source_id", "analyses", ["source_id"])
    op.create_index("ix_analyses_project_id", "analyses", ["project_id"])
    op.create_index("ix_extraction_logs_source_id", "extraction_logs", ["source_id"])
    op.create_index("ix_extraction_logs_project_id", "extraction_logs", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_extraction_logs_project_id", "extraction_logs")
    op.drop_index("ix_extraction_logs_source_id", "extraction_logs")
    op.drop_index("ix_analyses_project_id", "analyses")
    op.drop_index("ix_analyses_source_id", "analyses")
    op.drop_index("ix_reports_project_id", "reports")
    op.drop_index("ix_claims_entity_id", "claims")
    op.drop_index("ix_claims_source_id", "claims")
    op.drop_index("ix_entities_source_id", "entities")
    op.drop_index("ix_sources_project_id", "sources")
