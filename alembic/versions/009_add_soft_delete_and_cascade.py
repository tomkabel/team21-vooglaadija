"""Add soft delete to users and cascade FK to download_jobs.

Revision ID: 009_add_soft_delete_and_cascade
Revises: 008_change_ids_to_native_uuid
Create Date: 2026-04-17 07:44:00.000000

"""

from alembic import op

revision: str = "009_add_soft_delete_and_cascade"
down_revision: str | None = "008_change_ids_to_native_uuid"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    import sqlalchemy as sa

    # Add deleted_at column to users table for soft delete support
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Create index on deleted_at for efficient soft delete queries
    op.create_index(
        "ix_users_deleted_at",
        "users",
        ["deleted_at"],
        unique=False,
    )

    # Drop existing FK constraint on download_jobs.user_id
    op.execute("ALTER TABLE download_jobs DROP CONSTRAINT IF EXISTS download_jobs_user_id_fkey")

    # Recreate FK with CASCADE ON DELETE
    op.execute("""
        ALTER TABLE download_jobs 
        ADD CONSTRAINT download_jobs_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    """)


def downgrade() -> None:
    # Drop FK constraint
    op.execute("ALTER TABLE download_jobs DROP CONSTRAINT IF EXISTS download_jobs_user_id_fkey")

    # Recreate FK without cascade
    op.execute("""
        ALTER TABLE download_jobs 
        ADD CONSTRAINT download_jobs_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id)
    """)

    # Drop index first
    op.drop_index("ix_users_deleted_at", table_name="users")

    # Drop deleted_at column
    op.drop_column("users", "deleted_at")
