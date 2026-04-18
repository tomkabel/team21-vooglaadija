"""Fix alembic_version column to VARCHAR(64)

Revision ID: 009b_fix_version_column
Revises: 009_add_soft_delete_and_cascade
Create Date: 2026-04-18 23:52:00.000000

Fix the alembic_version table column from VARCHAR(32) to VARCHAR(64) to support
longer revision IDs.

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "009b_fix_version_column"
down_revision: str | None = "009_add_soft_delete_and_cascade"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Alter the alembic_version table column to VARCHAR(64)
    op.alter_column(
        "alembic_version",
        "version_num",
        type_=sa.String(length=64),
        existing_type=sa.String(length=32),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Revert back to VARCHAR(32)
    op.alter_column(
        "alembic_version",
        "version_num",
        type_=sa.String(length=32),
        existing_type=sa.String(length=64),
        existing_nullable=False,
    )
