"""add_correlation_id_to_outbox

Revision ID: 013_add_correlation_id_to_outbox
Revises: 012_fix_version_column
Create Date: 2026-04-18 17:30:00.000000

Adds correlation_id column to outbox table for distributed tracing
across API requests, outbox sync, and worker processing.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "013_add_correlation_id_to_outbox"
down_revision: str | None = "011_add_archived_download_jobs_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "outbox",
        sa.Column("correlation_id", sa.String(50), nullable=True, index=True),
    )


def downgrade() -> None:
    op.drop_column("outbox", "correlation_id")
