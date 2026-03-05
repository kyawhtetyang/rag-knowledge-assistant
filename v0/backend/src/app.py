from pathlib import Path

from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from src.db import count_chunks, init_db
from src.ingest import ingest_default_docs, ingest_paths
from src.llm import LLM
from src.retriever import retrieve
from src.settings import SETTINGS

app = FastAPI(title='RAG v0 API', version='0.1.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


class IngestRequest(BaseModel):
    paths: list[str] | None = None


class AskRequest(BaseModel):
    question: str = ''
    top_k: int | None = None


@app.get('/')
def root():
    return {
        'service': 'RAG v0 backend',
        'message': 'Backend is running. Use /health and /api/* endpoints.',
        'endpoints': ['/health', '/api/init-db', '/api/ingest', '/api/ask'],
    }


@app.get('/health')
def health():
    db_status = 'ok'
    chunk_count = 0
    db_error = None

    try:
        chunk_count = count_chunks()
    except Exception as exc:
        db_error = str(exc)
        if 'relation "chunks" does not exist' in db_error:
            db_status = 'not_initialized'
        else:
            db_status = 'down'

    payload = {
        'status': 'ok' if db_status == 'ok' else 'degraded',
        'db_status': db_status,
        'chunk_count': chunk_count,
        'settings': {
            'embedding_dim': SETTINGS.embedding_dim,
            'chunk_size': SETTINGS.chunk_size,
            'chunk_overlap': SETTINGS.chunk_overlap,
            'default_top_k': SETTINGS.default_top_k,
            'use_mock_llm': SETTINGS.use_mock_llm,
        },
    }

    if db_status == 'not_initialized':
        payload['hint'] = 'Run POST /api/init-db before ingestion.'
    if db_error:
        payload['db_error'] = db_error

    return payload


@app.post('/api/init-db')
def api_init_db():
    try:
        init_db()
        return {'status': 'ok', 'message': 'Database initialized'}
    except Exception as exc:
        return JSONResponse(status_code=500, content={'error': str(exc)})


@app.post('/api/ingest')
def api_ingest(payload: IngestRequest | None = Body(default=None)):
    paths = payload.paths if payload else None

    try:
        init_db()
        if paths:
            resolved = [Path(p).resolve() for p in paths]
            result = ingest_paths(resolved, SETTINGS.chunk_size, SETTINGS.chunk_overlap)
        else:
            result = ingest_default_docs()
        return {'status': 'ok', 'ingested': result, 'total_chunks': count_chunks()}
    except Exception as exc:
        return JSONResponse(status_code=500, content={'error': f'Ingestion failed: {exc}'})


@app.post('/api/ask')
def api_ask(payload: AskRequest):
    question = str(payload.question or '').strip()
    top_k = int(payload.top_k or SETTINGS.default_top_k)

    if not question:
        return JSONResponse(status_code=400, content={'error': "Field 'question' is required."})

    try:
        chunks = retrieve(question, top_k)
        answer = LLM.answer(question, chunks)
        citations = [
            {
                'source': c['doc_name'],
                'chunk_index': c['chunk_index'],
                'score': round(c['score'], 4),
                'preview': c['content'][:220],
            }
            for c in chunks
        ]
        return {
            'question': question,
            'answer': answer,
            'top_k': top_k,
            'citations': citations,
        }
    except Exception as exc:
        return JSONResponse(status_code=500, content={'error': f'Query failed: {exc}'})
