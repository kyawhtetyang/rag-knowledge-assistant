from pathlib import Path

from flask import Flask, jsonify, request

from src.db import count_chunks, init_db
from src.ingest import ingest_default_docs, ingest_paths
from src.llm import LLM
from src.retriever import retrieve
from src.settings import SETTINGS

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    return response


@app.route('/', methods=['GET'])
def root():
    return jsonify(
        {
            'service': 'RAG v0 backend',
            'message': 'Backend is running. Use /health and /api/* endpoints.',
            'endpoints': ['/health', '/api/init-db', '/api/ingest', '/api/ask'],
        }
    )


@app.route('/health', methods=['GET'])
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
        payload['hint'] = "Run POST /api/init-db before ingestion."

    if db_error:
        payload['db_error'] = db_error

    return jsonify(payload)


@app.route('/api/init-db', methods=['POST', 'OPTIONS'])
def api_init_db():
    if request.method == 'OPTIONS':
        return ('', 204)

    try:
        init_db()
        return jsonify({'status': 'ok', 'message': 'Database initialized'})
    except Exception as exc:
        return jsonify({'error': str(exc)}), 500


@app.route('/api/ingest', methods=['POST', 'OPTIONS'])
def api_ingest():
    if request.method == 'OPTIONS':
        return ('', 204)

    payload = request.get_json(silent=True) or {}
    paths = payload.get('paths')

    try:
        init_db()
        if paths:
            resolved = [Path(p).resolve() for p in paths]
            result = ingest_paths(resolved, SETTINGS.chunk_size, SETTINGS.chunk_overlap)
        else:
            result = ingest_default_docs()
        return jsonify({'status': 'ok', 'ingested': result, 'total_chunks': count_chunks()})
    except Exception as exc:
        return jsonify({'error': f'Ingestion failed: {exc}'}), 500


@app.route('/api/ask', methods=['POST', 'OPTIONS'])
def api_ask():
    if request.method == 'OPTIONS':
        return ('', 204)

    payload = request.get_json(silent=True) or {}
    question = str(payload.get('question', '')).strip()
    top_k = int(payload.get('top_k') or SETTINGS.default_top_k)

    if not question:
        return jsonify({'error': "Field 'question' is required."}), 400

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
        return jsonify(
            {
                'question': question,
                'answer': answer,
                'top_k': top_k,
                'citations': citations,
            }
        )
    except Exception as exc:
        return jsonify({'error': f'Query failed: {exc}'}), 500
