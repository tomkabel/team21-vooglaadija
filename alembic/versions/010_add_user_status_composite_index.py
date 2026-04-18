"""Add composite index on download_jobs (user_id, status)

Revision ID: 010_add_user_status_composite_index
Revises: 009_add_soft_delete_and_cascade
Create Date: 2026-04-18 08:45:00.000000

This index optimizes the common query pattern:
  SELECT * FROM download_jobs WHERE user_id = ? AND status = ?

Which is used when filtering a user's downloads by status (e.g., showing only
pending or only completed downloads).

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "010_add_user_status_composite_index"
down_revision: str | None = "009b_fix_version_column"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "ix_download_jobs_user_status",
        "download_jobs",
        ["user_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_download_jobs_user_status", "download_jobs")
