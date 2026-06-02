from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SETTINGS
from app.llm import LLM
from app.models import EvalItem, EvalResult, EvalRun, EvalSet
from app.services.retrieval import retrieve


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _normalize(s: str) -> str:
    return (s or '').strip().lower()


async def ensure_default_eval_set(session: AsyncSession) -> EvalSet:
    res = await session.execute(select(EvalSet).where(EvalSet.name == 'default'))
    found = res.scalar_one_or_none()
    if found is not None:
        return found

    s = EvalSet(name='default', description='Default tiny eval set (keyword-based).')
    session.add(s)
    await session.flush()

    items = [
        EvalItem(
            eval_set_id=s.id,
            question='What is RAG?',
            expected_contains=['retrieval', 'generation'],
            notes='Should mention retrieval + generation.',
        ),
        EvalItem(
            eval_set_id=s.id,
            question='What is pgvector?',
            expected_contains=['postgres'],
            notes='Should mention PostgreSQL.',
        ),
    ]
    session.add_all(items)
    await session.flush()
    return s


async def run_eval(session: AsyncSession, *, eval_set_name: str = 'default', top_k: int | None = None) -> int:
    # Ensure eval set exists.
    eval_set = await ensure_default_eval_set(session) if eval_set_name == 'default' else None
    if eval_set is None:
        res = await session.execute(select(EvalSet).where(EvalSet.name == eval_set_name))
        eval_set = res.scalar_one_or_none()
        if eval_set is None:
            raise ValueError(f"eval set not found: {eval_set_name}")

    k = int(top_k or SETTINGS.default_top_k)

    run = EvalRun(
        eval_set_id=eval_set.id,
        retrieval_mode=SETTINGS.retrieval_mode,
        top_k=k,
        vector_weight=float(SETTINGS.vector_weight),
        fts_weight=float(SETTINGS.fts_weight),
        embeddings_provider=SETTINGS.embeddings_provider,
        embedding_model=SETTINGS.embedding_model,
        embedding_dim=int(SETTINGS.embedding_dim),
        status='running',
        summary={},
    )
    session.add(run)
    await session.flush()

    res = await session.execute(select(EvalItem).where(EvalItem.eval_set_id == eval_set.id).order_by(EvalItem.id.asc()))
    items = res.scalars().all()

    hits = 0
    total = 0

    for item in items:
        total += 1
        chunks = await retrieve(session, item.question, k)
        answer = LLM.answer(item.question, chunks)

        hay = _normalize(answer + '\n\n' + '\n'.join(str(c.get('content', '')) for c in chunks))
        expected = [str(x) for x in (item.expected_contains or [])]
        missing = [e for e in expected if _normalize(e) not in hay]
        hit = len(missing) == 0
        if hit:
            hits += 1

        citations = [
            {
                'source': c.get('source'),
                'chunk_index': int(c.get('chunk_index', 0)),
                'score': float(c.get('score', 0.0)),
            }
            for c in chunks
        ]

        session.add(
            EvalResult(
                eval_run_id=run.id,
                eval_item_id=item.id,
                question=item.question,
                answer=answer,
                citations=citations,
                hit=bool(hit),
                missing=missing,
            )
        )

    run.status = 'done'
    run.finished_at = _utcnow()
    run.summary = {
        'total': total,
        'hits': hits,
        'hit_rate': (hits / total) if total else 0.0,
    }

    await session.flush()
    return int(run.id)


async def get_eval_run_summary(session: AsyncSession, run_id: int) -> dict:
    res = await session.execute(select(EvalRun).where(EvalRun.id == int(run_id)))
    run = res.scalar_one_or_none()
    if run is None:
        raise ValueError('run not found')

    return {
        'run_id': int(run.id),
        'status': run.status,
        'summary': run.summary,
        'created_at': str(run.created_at),
        'finished_at': str(run.finished_at) if run.finished_at else None,
        'retrieval_mode': run.retrieval_mode,
        'top_k': run.top_k,
        'embeddings_provider': run.embeddings_provider,
        'embedding_model': run.embedding_model,
        'embedding_dim': run.embedding_dim,
    }
