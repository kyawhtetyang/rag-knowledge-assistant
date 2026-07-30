from __future__ import annotations

import asyncio
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.services.file_text import extract_text_from_upload
from app.services.ingest import ingest_text
from app.services.jobs import claim_job_by_id, claim_next_job, mark_job_done, mark_job_error


POLL_INTERVAL_SEC = float(os.getenv('WORKER_POLL_INTERVAL', '1.0'))
IDLE_SLEEP_SEC = float(os.getenv('WORKER_IDLE_SLEEP', '1.0'))


async def process_one(session: AsyncSession) -> bool:
    job = await claim_next_job(session)
    if job is None:
        return False

    return await process_claimed_job(session, job)


async def process_job_by_id(session: AsyncSession, job_id: int) -> bool:
    job = await claim_job_by_id(session, int(job_id))
    if job is None or job.status in {'done', 'error'}:
        return False

    return await process_claimed_job(session, job)


async def process_claimed_job(session: AsyncSession, job) -> bool:
    try:
        text = extract_text_from_upload(job.filename, job.content)
        await ingest_text(session, source=job.source, text=text, metadata=job.meta)
        await mark_job_done(session, job.id)
        await session.commit()
        return True
    except Exception as exc:
        await mark_job_error(session, job.id, str(exc))
        await session.commit()
        return True


async def run_loop() -> None:
    while True:
        async with SessionLocal() as session:
            did = await process_one(session)

        if did:
            await asyncio.sleep(POLL_INTERVAL_SEC)
        else:
            await asyncio.sleep(IDLE_SLEEP_SEC)


def main() -> None:
    asyncio.run(run_loop())


if __name__ == '__main__':
    main()
