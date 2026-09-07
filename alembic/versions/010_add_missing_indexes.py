"""add missing single-column indexes

Revision ID: 010
Revises: 009
Create Date: 2026-08-23

Adds single-column indexes on download_jobs.status, download_jobs.user_id,
and download_jobs.created_at, matching the ORM model's ``index=True`` on
those columns (SQLAlchemy's default "ix_<table>_<column>" naming keeps the
model metadata and the migrated schema in sync). users.deleted_at is already
indexed by migration 001 (ix_users_deleted_at); this migration must not add a
second, differently-named index on the same column.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "010"
down_revision: str | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(
                sa.text(
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_download_jobs_status "
                    "ON download_jobs (status)"
                )
            )
            op.execute(
                sa.text(
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_download_jobs_user_id "
                    "ON download_jobs (user_id)"
                )
            )
            op.execute(
                sa.text(
                    "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_download_jobs_created_at "
                    "ON download_jobs (created_at)"
                )
            )
        return

    op.create_index(
        "ix_download_jobs_status",
        "download_jobs",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_download_jobs_user_id",
        "download_jobs",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_download_jobs_created_at",
        "download_jobs",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        with op.get_context().autocommit_block():
            op.execute(sa.text("DROP INDEX CONCURRENTLY IF EXISTS ix_download_jobs_created_at"))
            op.execute(sa.text("DROP INDEX CONCURRENTLY IF EXISTS ix_download_jobs_user_id"))
            op.execute(sa.text("DROP INDEX CONCURRENTLY IF EXISTS ix_download_jobs_status"))
        return

    op.drop_index("ix_download_jobs_created_at", table_name="download_jobs")
    op.drop_index("ix_download_jobs_user_id", table_name="download_jobs")
    op.drop_index("ix_download_jobs_status", table_name="download_jobs")
