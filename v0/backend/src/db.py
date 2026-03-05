import json
from typing import Iterable

import psycopg
from psycopg.rows import dict_row

from src.settings import SETTINGS


CREATE_TABLE_SQL = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    id BIGSERIAL PRIMARY KEY,
    doc_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
    embedding VECTOR({SETTINGS.embedding_dim}) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(doc_name, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunks_doc_name ON chunks(doc_name);
"""


def _vector_literal(values: Iterable[float]) -> str:
    return '[' + ','.join(f'{float(v):.7f}' for v in values) + ']'


def get_conn():
    return psycopg.connect(SETTINGS.pg_dsn, autocommit=True)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(CREATE_TABLE_SQL)


def upsert_chunks(rows):
    if not rows:
        return 0

    sql = """
    INSERT INTO chunks (doc_name, chunk_index, content, metadata, embedding)
    VALUES (%s, %s, %s, %s::jsonb, %s::vector)
    ON CONFLICT (doc_name, chunk_index)
    DO UPDATE SET
      content = EXCLUDED.content,
      metadata = EXCLUDED.metadata,
      embedding = EXCLUDED.embedding,
      updated_at = NOW();
    """

    values = [
        (
            r['doc_name'],
            r['chunk_index'],
            r['content'],
            json.dumps(r['metadata']),
            _vector_literal(r['embedding']),
        )
        for r in rows
    ]

    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, values)

    return len(values)


def search_similar(query_embedding, top_k):
    vec = _vector_literal(query_embedding)
    sql = """
    SELECT
      id,
      doc_name,
      chunk_index,
      content,
      metadata,
      (1 - (embedding <=> %s::vector)) AS score
    FROM chunks
    ORDER BY embedding <=> %s::vector
    LIMIT %s;
    """

    with get_conn() as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql, (vec, vec, int(top_k)))
            rows = cur.fetchall()

    results = []
    for row in rows:
        results.append(
            {
                'id': row['id'],
                'doc_name': row['doc_name'],
                'chunk_index': row['chunk_index'],
                'content': row['content'],
                'metadata': row['metadata'],
                'score': float(row['score']),
            }
        )
    return results


def count_chunks():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM chunks;')
            return int(cur.fetchone()[0])
