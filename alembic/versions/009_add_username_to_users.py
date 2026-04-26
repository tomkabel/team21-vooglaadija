"""Add username field to users table.

Revision ID: 009_add_username_to_users
Revises: 008_change_ids_to_native_uuid
Create Date: 2026-04-13 18:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009_add_username_to_users"
down_revision: str | None = "cb2699335d57"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("username", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "username")
