"""Change string IDs to native PostgreSQL UUID.

Revision ID: 008_change_ids_to_native_uuid
Revises: 007_add_retry_columns
Create Date: 2026-04-07 05:15:00.000000

"""

from alembic import op
import sqlalchemy as sa


revision: str = "008_change_ids_to_native_uuid"
down_revision: str | None = "007_add_retry_columns"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    # First drop foreign key constraints
    op.execute("ALTER TABLE download_jobs DROP CONSTRAINT IF EXISTS download_jobs_user_id_fkey")
    op.execute("ALTER TABLE outbox DROP CONSTRAINT IF EXISTS outbox_job_id_fkey")

    # Convert columns to UUID
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE download_jobs ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE download_jobs ALTER COLUMN user_id TYPE UUID USING user_id::uuid")
    op.execute("ALTER TABLE outbox ALTER COLUMN id TYPE UUID USING id::uuid")
    op.execute("ALTER TABLE outbox ALTER COLUMN job_id TYPE UUID USING job_id::uuid")

    # Recreate foreign key constraints
    op.execute("""
        ALTER TABLE download_jobs 
        ADD CONSTRAINT download_jobs_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id)
    """)
    op.execute("""
        ALTER TABLE outbox 
        ADD CONSTRAINT outbox_job_id_fkey 
        FOREIGN KEY (job_id) REFERENCES download_jobs(id)
    """)


def downgrade() -> None:
    # Drop foreign key constraints
    op.execute("ALTER TABLE download_jobs DROP CONSTRAINT IF EXISTS download_jobs_user_id_fkey")
    op.execute("ALTER TABLE outbox DROP CONSTRAINT IF EXISTS outbox_job_id_fkey")

    # Convert UUID back to string
    op.execute("ALTER TABLE users ALTER COLUMN id TYPE VARCHAR(36) USING id::text")
    op.execute("ALTER TABLE download_jobs ALTER COLUMN id TYPE VARCHAR(36) USING id::text")
    op.execute(
        "ALTER TABLE download_jobs ALTER COLUMN user_id TYPE VARCHAR(36) USING user_id::text"
    )
    op.execute("ALTER TABLE outbox ALTER COLUMN id TYPE VARCHAR(36) USING id::text")
    op.execute("ALTER TABLE outbox ALTER COLUMN job_id TYPE VARCHAR(36) USING job_id::text")

    # Recreate foreign key constraints
    op.execute("""
        ALTER TABLE download_jobs 
        ADD CONSTRAINT download_jobs_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES users(id)
    """)
    op.execute("""
        ALTER TABLE outbox 
        ADD CONSTRAINT outbox_job_id_fkey 
        FOREIGN KEY (job_id) REFERENCES download_jobs(id)
    """)
