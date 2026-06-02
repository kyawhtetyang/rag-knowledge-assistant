from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import IngestionJob


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def create_ingestion_job(
    session: AsyncSession,
    *,
    source: str,
    filename: str,
    content: bytes,
    metadata: dict,
) -> IngestionJob:
    job = IngestionJob(
        status='queued',
        source=source,
        filename=filename,
        content=content,
        meta=metadata or {},
    )
    session.add(job)
    await session.flush()
    return job


async def get_job(session: AsyncSession, job_id: int) -> IngestionJob | None:
    res = await session.execute(select(IngestionJob).where(IngestionJob.id == int(job_id)))
    return res.scalar_one_or_none()


async def claim_next_job(session: AsyncSession) -> IngestionJob | None:
    # Use a single statement with SKIP LOCKED so multiple workers can run safely.
    sql = text(
        """
        WITH next_job AS (
          SELECT id
          FROM ingestion_jobs
          WHERE status = 'queued'
          ORDER BY created_at ASC
          FOR UPDATE SKIP LOCKED
          LIMIT 1
        )
        UPDATE ingestion_jobs j
        SET status = 'running', started_at = COALESCE(started_at, NOW()), updated_at = NOW()
        FROM next_job
        WHERE j.id = next_job.id
        RETURNING j.id;
        """
    )
    row = (await session.execute(sql)).first()
    if not row:
        return None

    job_id = int(row[0])
    res = await session.execute(select(IngestionJob).where(IngestionJob.id == job_id))
    return res.scalar_one()


async def mark_job_done(session: AsyncSession, job_id: int) -> None:
    sql = text(
        """
        UPDATE ingestion_jobs
        SET status = 'done', finished_at = NOW(), updated_at = NOW(), error = NULL
        WHERE id = :id;
        """
    )
    await session.execute(sql, {'id': int(job_id)})


async def mark_job_error(session: AsyncSession, job_id: int, error: str) -> None:
    sql = text(
        """
        UPDATE ingestion_jobs
        SET status = 'error', finished_at = NOW(), updated_at = NOW(), error = :err
        WHERE id = :id;
        """
    )
    await session.execute(sql, {'id': int(job_id), 'err': str(error)})
