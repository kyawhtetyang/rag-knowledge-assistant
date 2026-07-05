from __future__ import annotations

import hashlib

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunking import chunk_text
from app.config import SETTINGS
from app.embeddings import EMBEDDINGS
from app.models import Chunk, Document


def checksum_text(text: str) -> str:
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


async def ingest_text(session: AsyncSession, *, source: str, text: str, metadata: dict) -> tuple[int, int]:
    raw = (text or '').strip()
    if not raw:
        raise ValueError('text is empty')

    checksum = checksum_text(raw)

    existing = await session.execute(
        select(Document).where(Document.source == source, Document.checksum == checksum)
    )
    doc = existing.scalar_one_or_none()

    if doc is None:
        doc = Document(source=source, checksum=checksum, meta=metadata or {})
        session.add(doc)
        await session.flush()
    else:
        doc.meta = metadata or {}

    await session.execute(delete(Chunk).where(Chunk.document_id == doc.id))

    chunks = chunk_text(raw, SETTINGS.chunk_size, SETTINGS.chunk_overlap)
    vectors = EMBEDDINGS.embed_texts(chunks)

    for idx, (content, emb) in enumerate(zip(chunks, vectors)):
        session.add(
            Chunk(
                document_id=doc.id,
                chunk_index=idx,
                content=content,
                meta={
                    'source': source,
                    'chunk_size': SETTINGS.chunk_size,
                    'chunk_overlap': SETTINGS.chunk_overlap,
                },
                embedding=emb,
            )
        )

    await session.flush()
    return int(doc.id), len(chunks)
