"""add retry columns to download_jobs

Revision ID: 004
Revises: 003
Create Date: 2024-01-02 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "download_jobs",
        sa.Column("retry_count", sa.Integer(), server_default="0", nullable=False),
    )
    op.add_column(
        "download_jobs",
        sa.Column("max_retries", sa.Integer(), server_default="3", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("download_jobs", "max_retries")
    op.drop_column("download_jobs", "retry_count")
