"""add_updated_at_columns

Revision ID: 003
Revises: 002
Create Date: 2024-01-01 00:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users", sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    op.add_column(
        "download_jobs",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_column("download_jobs", "updated_at")
    op.drop_column("users", "updated_at")
