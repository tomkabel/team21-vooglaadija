"""Add retry columns to download_jobs table.

Revision ID: 007_add_retry_columns
Revises: 006
Create Date: 2026-04-07 05:08:34.000000

"""

from alembic import op
import sqlalchemy as sa
from alembic import context


revision = "007_add_retry_columns"
down_revision = "006"
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = inspector.get_columns(table_name)
    return any(col["name"] == column_name for col in columns)


def upgrade() -> None:
    # Only add retry_count if it doesn't already exist
    if not column_exists("download_jobs", "retry_count"):
        op.add_column(
            "download_jobs",
            sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        )

    # Only add max_retries if it doesn't already exist
    if not column_exists("download_jobs", "max_retries"):
        op.add_column(
            "download_jobs",
            sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        )

    # Always add next_retry_at (new column)
    op.add_column(
        "download_jobs", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    # Drop all three columns added in this migration
    if column_exists("download_jobs", "next_retry_at"):
        op.drop_column("download_jobs", "next_retry_at")

    if column_exists("download_jobs", "retry_count"):
        op.drop_column("download_jobs", "retry_count")

    if column_exists("download_jobs", "max_retries"):
        op.drop_column("download_jobs", "max_retries")
