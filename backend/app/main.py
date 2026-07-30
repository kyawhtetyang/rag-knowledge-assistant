from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SETTINGS
from app.db import SessionLocal
from app.llm import LLM, redact_sensitive
from app.schemas import (
    AskRequest,
    AskResponse,
    IngestFileResponse,
    IngestJobResponse,
    IngestResponse,
    IngestTextRequest,
    JobStatusResponse,
    EvalRunRequest,
    EvalRunResponse,
    EvalRunSummaryResponse,
)
from app.services.ingest import ingest_text
from app.services.jobs import create_ingestion_job, get_job
from app.services.file_text import extract_text_from_upload
from app.services.retrieval import retrieve
from app.services.eval import get_eval_run_summary, run_eval
from app.worker import process_job_by_id

app = FastAPI(title='RAG Knowledge Assistant API', version='1.0.0')
logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / 'frontend'
ACTIVE_FRONTEND_DIR = FRONTEND_DIR
ACTIVE_STATIC_DIR = ACTIVE_FRONTEND_DIR / 'static'
if ACTIVE_STATIC_DIR.exists():
    app.mount('/static', StaticFiles(directory=ACTIVE_STATIC_DIR), name='static')
elif ACTIVE_FRONTEND_DIR.exists():
    app.mount('/static', StaticFiles(directory=ACTIVE_FRONTEND_DIR), name='static')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=False,
    allow_methods=['*'],
    allow_headers=['*'],
)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


async def process_ingestion_job_inline(job_id: int) -> None:
    async with SessionLocal() as session:
        await process_job_by_id(session, int(job_id))


@app.get('/health')
def health():
    return {
        'status': 'ok',
        'settings': {
            'chunk_size': SETTINGS.chunk_size,
            'chunk_overlap': SETTINGS.chunk_overlap,
            'default_top_k': SETTINGS.default_top_k,
            'embeddings_provider': SETTINGS.embeddings_provider,
            'embedding_model': SETTINGS.embedding_model,
            'embedding_dim': SETTINGS.embedding_dim,
            'retrieval_mode': SETTINGS.retrieval_mode,
            'vector_weight': SETTINGS.vector_weight,
            'fts_weight': SETTINGS.fts_weight,
            'llm_provider': SETTINGS.llm_provider,
            'llm_model': SETTINGS.gemini_model if SETTINGS.llm_provider == 'gemini' else SETTINGS.openai_compat_model,
            'gemini_configured': bool(SETTINGS.gemini_api_key),
            'openai_compat_configured': bool(SETTINGS.openai_compat_api_key or SETTINGS.openai_api_key),
        },
    }


@app.get('/')
def frontend():
    index_path = ACTIVE_FRONTEND_DIR / 'index.html'
    if index_path.exists():
        from fastapi.responses import FileResponse
        return FileResponse(index_path)
    return {'service': 'RAG Knowledge Assistant API', 'docs': '/docs', 'health': '/health'}


@app.post('/api/ingest-text', response_model=IngestResponse)
async def api_ingest_text(payload: IngestTextRequest, db: AsyncSession = Depends(get_db)):
    try:
        doc_id, chunks = await ingest_text(db, source=payload.source, text=payload.text, metadata=payload.metadata)
        await db.commit()
        return IngestResponse(document_id=doc_id, chunks=chunks)
    except Exception as exc:
        await db.rollback()
        return JSONResponse(status_code=500, content={'error': str(exc)})


@app.post('/api/ingest-file', response_model=IngestFileResponse)
async def api_ingest_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await file.read()
        text = extract_text_from_upload(file.filename or 'upload', content)
        doc_id, chunks = await ingest_text(db, source=file.filename or 'upload', text=text, metadata={'filename': file.filename})
        await db.commit()
        return IngestFileResponse(filename=file.filename or 'upload', document_id=doc_id, chunks=chunks)
    except Exception as exc:
        await db.rollback()
        return JSONResponse(status_code=500, content={'error': str(exc)})


@app.post('/api/eval/run', response_model=EvalRunResponse)
async def api_eval_run(payload: EvalRunRequest, db: AsyncSession = Depends(get_db)):
    try:
        run_id = await run_eval(db, eval_set_name=payload.eval_set, top_k=payload.top_k)
        await db.commit()
        return EvalRunResponse(run_id=run_id, status='done')
    except Exception as exc:
        await db.rollback()
        return JSONResponse(status_code=500, content={'error': str(exc)})


@app.get('/api/eval/runs/{run_id}', response_model=EvalRunSummaryResponse)
async def api_eval_run_summary(run_id: int, db: AsyncSession = Depends(get_db)):
    try:
        summary = await get_eval_run_summary(db, int(run_id))
        return EvalRunSummaryResponse(
            run_id=int(summary['run_id']),
            status=str(summary['status']),
            summary=dict(summary['summary'] or {}),
            created_at=summary.get('created_at'),
            finished_at=summary.get('finished_at'),
        )
    except Exception as exc:
        return JSONResponse(status_code=500, content={'error': str(exc)})


@app.post('/api/ingest-file-async', response_model=IngestJobResponse)
async def api_ingest_file_async(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or 'upload'
    try:
        content = await file.read()
        job = await create_ingestion_job(
            db,
            source=filename,
            filename=filename,
            content=content,
            metadata={'filename': filename},
        )
        await db.commit()
        logger.info('ingestion job %s created for %s', job.id, filename)
        await process_ingestion_job_inline(int(job.id))
        await db.refresh(job)
        logger.info('ingestion job %s finished with status=%s', job.id, job.status)
        return IngestJobResponse(job_id=int(job.id), status=job.status)
    except Exception as exc:
        await db.rollback()
        return JSONResponse(status_code=500, content={'error': str(exc)})


@app.get('/api/jobs/{job_id}', response_model=JobStatusResponse)
async def api_job_status(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await get_job(db, int(job_id))
    if job is None:
        return JSONResponse(status_code=404, content={'error': 'job not found'})

    return JobStatusResponse(
        job_id=int(job.id),
        status=job.status,
        source=job.source,
        filename=job.filename,
        error=job.error,
        created_at=str(job.created_at) if job.created_at else None,
        started_at=str(job.started_at) if job.started_at else None,
        finished_at=str(job.finished_at) if job.finished_at else None,
    )


@app.post('/api/ask', response_model=AskResponse)
async def api_ask(payload: AskRequest, db: AsyncSession = Depends(get_db)):
    question = (payload.question or '').strip()
    if not question:
        return JSONResponse(status_code=400, content={'error': "Field 'question' is required."})

    top_k = int(payload.top_k or SETTINGS.default_top_k)

    try:
        chunks = await retrieve(db, question, top_k)
        answer = LLM.answer(question, chunks)
        citations = [
            {
                'source': c['source'],
                'chunk_index': int(c['chunk_index']),
                'score': float(c['score']),
                'preview': redact_sensitive(str(c['content'])[:220]),
            }
            for c in chunks
        ]
        return AskResponse(question=question, answer=answer, top_k=top_k, citations=citations)
    except Exception as exc:
        return JSONResponse(status_code=500, content={'error': str(exc)})
