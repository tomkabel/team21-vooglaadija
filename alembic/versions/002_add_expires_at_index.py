"""Add index on download_jobs.expires_at

Revision ID: 002
Revises: 001
Create Date: 2026-03-25 14:20:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_download_jobs_expires_at", "download_jobs", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_download_jobs_expires_at", "download_jobs")
