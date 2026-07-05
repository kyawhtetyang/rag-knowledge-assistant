from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SETTINGS
from app.embeddings import EMBEDDINGS


async def retrieve(session: AsyncSession, question: str, top_k: int) -> list[dict]:
    mode = (SETTINGS.retrieval_mode or 'hybrid').strip().lower()
    if mode not in {'vector', 'fts', 'hybrid'}:
        raise ValueError("retrieval_mode must be one of: vector|fts|hybrid")

    query_text = (question or '').strip()
    if not query_text:
        return []

    qvec = None
    if mode in {'vector', 'hybrid'}:
        query_vec = EMBEDDINGS.embed_query(query_text)
        qvec = '[' + ','.join(f'{float(v):.7f}' for v in query_vec) + ']'

    if mode == 'vector':
        sql = text(
            """
            SELECT
              d.source AS source,
              c.chunk_index AS chunk_index,
              c.content AS content,
              (1 - (c.embedding <=> CAST(:qvec AS vector))) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            ORDER BY c.embedding <=> CAST(:qvec AS vector)
            LIMIT :k;
            """
        )
        rows = (
            await session.execute(sql, {'qvec': qvec, 'k': int(top_k)})
        ).mappings().all()
        return [dict(r) for r in rows]

    if mode == 'fts':
        sql = text(
            """
            SELECT
              d.source AS source,
              c.chunk_index AS chunk_index,
              c.content AS content,
              ts_rank_cd(c.content_tsv, plainto_tsquery('english', :qtext)) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.content_tsv @@ plainto_tsquery('english', :qtext)
            ORDER BY score DESC
            LIMIT :k;
            """
        )
        rows = (
            await session.execute(sql, {'qtext': query_text, 'k': int(top_k)})
        ).mappings().all()
        return [dict(r) for r in rows]

    # hybrid
    sql = text(
        """
        SELECT
          d.source AS source,
          c.chunk_index AS chunk_index,
          c.content AS content,
          (
            (:vw * (1 - (c.embedding <=> CAST(:qvec AS vector))))
            + (:fw * ts_rank_cd(c.content_tsv, plainto_tsquery('english', :qtext)))
          ) AS score
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        ORDER BY score DESC
        LIMIT :k;
        """
    )

    rows = (
        await session.execute(
            sql,
            {
                'qvec': qvec,
                'qtext': query_text,
                'vw': float(SETTINGS.vector_weight),
                'fw': float(SETTINGS.fts_weight),
                'k': int(top_k),
            },
        )
    ).mappings().all()
    return [dict(r) for r in rows]
