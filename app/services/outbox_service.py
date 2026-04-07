import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.outbox import Outbox


async def write_job_to_outbox(
    db: AsyncSession,
    job_id: UUID,
    event_type: str = "enqueue_download",
    payload: str | None = None,
) -> Outbox:
    """Write a job to the outbox in the same transaction as the main entity.

    This ensures atomicity - if the transaction commits, the outbox entry exists.
    The worker will process this entry and mark it as processed.
    """
    outbox_entry = Outbox(
        id=uuid.uuid4(),
        job_id=job_id,
        event_type=event_type,
        payload=payload,
        status="pending",
    )
    db.add(outbox_entry)
    return outbox_entry
