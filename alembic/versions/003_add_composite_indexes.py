"""Add composite indexes for download_jobs

Revision ID: 003_add_composite_indexes
Revises: 002
Create Date: 2026-04-02 15:02:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "003_add_composite_indexes"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_download_jobs_user_created", "download_jobs", ["user_id", "created_at"])
    op.create_index("ix_download_jobs_status_expires", "download_jobs", ["status", "expires_at"])


def downgrade() -> None:
    op.drop_index("ix_download_jobs_status_expires", "download_jobs")
    op.drop_index("ix_download_jobs_user_created", "download_jobs")
