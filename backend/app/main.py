from __future__ import annotations

import logging
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import SETTINGS
from app.db import SessionLocal
from app.llm import LLM, redact_sensitive
from app.models import Document, IngestionJob
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
from app.services.eval import get_eval_run_summary, run_eval
from app.services.file_text import extract_text_from_upload
from app.services.ingest import ingest_text
from app.services.jobs import create_ingestion_job, get_job
from app.services.retrieval import retrieve

app = FastAPI(title='RAG Knowledge Assistant API', version=SETTINGS.app_version)
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
    allow_origins=SETTINGS.cors_origins,
    allow_credentials=False,
    allow_methods=['GET', 'POST', 'DELETE', 'OPTIONS'],
    allow_headers=['Content-Type', 'X-Admin-Key'],
)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


def safe_server_error(operation: str, exc: Exception) -> JSONResponse:
    logger.exception('%s failed', operation, exc_info=exc)
    return JSONResponse(status_code=500, content={'error': 'internal server error'})


def require_admin(x_admin_key: str | None = Header(default=None)) -> None:
    if not SETTINGS.admin_api_key:
        raise HTTPException(status_code=404, detail='not found')
    if x_admin_key != SETTINGS.admin_api_key:
        raise HTTPException(status_code=403, detail='forbidden')


async def read_upload_with_limit(file: UploadFile) -> bytes:
    content = await file.read(SETTINGS.max_upload_bytes + 1)
    if len(content) > SETTINGS.max_upload_bytes:
        raise HTTPException(status_code=413, detail='uploaded file is too large')
    return content


@app.get('/health')
def health():
    return {
        'status': 'ok',
        'version': SETTINGS.app_version,
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
    if len(payload.text or '') > SETTINGS.max_text_chars:
        raise HTTPException(status_code=413, detail='text payload is too large')
    try:
        doc_id, chunks = await ingest_text(db, source=payload.source, text=payload.text, metadata=payload.metadata)
        await db.commit()
        return IngestResponse(document_id=doc_id, chunks=chunks)
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        return safe_server_error('text ingestion', exc)


@app.post('/api/ingest-file', response_model=IngestFileResponse)
async def api_ingest_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    try:
        content = await read_upload_with_limit(file)
        text = extract_text_from_upload(file.filename or 'upload', content)
        doc_id, chunks = await ingest_text(db, source=file.filename or 'upload', text=text, metadata={'filename': file.filename})
        await db.commit()
        return IngestFileResponse(filename=file.filename or 'upload', document_id=doc_id, chunks=chunks)
    except HTTPException:
        raise
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        return safe_server_error('file ingestion', exc)


@app.post('/api/eval/run', response_model=EvalRunResponse)
async def api_eval_run(payload: EvalRunRequest, db: AsyncSession = Depends(get_db)):
    try:
        run_id = await run_eval(db, eval_set_name=payload.eval_set, top_k=payload.top_k)
        await db.commit()
        return EvalRunResponse(run_id=run_id, status='done')
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        return safe_server_error('eval run', exc)


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
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        return safe_server_error('eval summary', exc)


@app.post('/api/ingest-file-async', response_model=IngestJobResponse, status_code=202)
async def api_ingest_file_async(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    filename = file.filename or 'upload'
    try:
        content = await read_upload_with_limit(file)
        # Validate format before persisting a queued job; the worker owns actual ingestion.
        extract_text_from_upload(filename, content)
        job = await create_ingestion_job(
            db,
            source=filename,
            filename=filename,
            content=content,
            metadata={'filename': filename},
        )
        await db.commit()
        logger.info('ingestion job %s queued for %s', job.id, filename)
        return IngestJobResponse(job_id=int(job.id), status=job.status)
    except HTTPException:
        raise
    except ValueError as exc:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        await db.rollback()
        return safe_server_error('async file ingestion', exc)


@app.get('/api/jobs/{job_id}', response_model=JobStatusResponse)
async def api_job_status(job_id: int, db: AsyncSession = Depends(get_db)):
    job = await get_job(db, int(job_id))
    if job is None:
        raise HTTPException(status_code=404, detail='job not found')

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


@app.get('/api/documents/summary')
async def api_documents_summary(db: AsyncSession = Depends(get_db)):
    try:
        document_count = await db.scalar(select(func.count()).select_from(Document))
        return {'document_count': int(document_count or 0)}
    except Exception as exc:
        return safe_server_error('document summary', exc)


@app.delete('/api/demo-data', dependencies=[Depends(require_admin)])
async def api_clear_demo_data(db: AsyncSession = Depends(get_db)):
    try:
        document_count = await db.scalar(select(func.count()).select_from(Document))
        job_count = await db.scalar(select(func.count()).select_from(IngestionJob))
        await db.execute(delete(IngestionJob))
        await db.execute(delete(Document))
        await db.commit()
        return {
            'status': 'cleared',
            'documents_deleted': int(document_count or 0),
            'jobs_deleted': int(job_count or 0),
        }
    except Exception as exc:
        await db.rollback()
        return safe_server_error('demo-data cleanup', exc)


@app.post('/api/ask', response_model=AskResponse)
async def api_ask(payload: AskRequest, db: AsyncSession = Depends(get_db)):
    question = (payload.question or '').strip()
    if not question:
        raise HTTPException(status_code=400, detail="Field 'question' is required.")

    document_count = await db.scalar(select(func.count()).select_from(Document))
    if not int(document_count or 0):
        raise HTTPException(
            status_code=400,
            detail='Please upload a document first, then ask your question. This assistant answers only from uploaded documents.',
        )

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
        return safe_server_error('ask', exc)
