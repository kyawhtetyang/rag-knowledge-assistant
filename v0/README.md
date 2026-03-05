# RAG v0 (Flask + pgvector)

Baseline Retrieval-Augmented Generation project with:

- Document ingestion (`txt`, `md`, `pdf`)
- Embeddings
- Vector storage in PostgreSQL (`pgvector`)
- Similarity retrieval
- Answer generation with citations

## Structure

```text
v0/
  backend/
    src/
    config/
    data/docs/
    tests/
    main.py
    requirements.txt
    Dockerfile
    docker-compose.yml
  frontend/
    index.html
  docs/
    PROJECT_OVERVIEW.md
```

## Quick Start (Local)

1. Start pgvector Postgres:

```bash
cd backend
docker compose up -d db
```

2. Install backend deps and run API:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

3. Open UI:

```bash
cd ../frontend
python -m http.server 5173
```

Then visit `http://127.0.0.1:5173`.

## API Endpoints

- `GET /health`
- `POST /api/init-db`
- `POST /api/ingest`
- `POST /api/ask`

Example ask request:

```json
{ "question": "What is RAG?", "top_k": 5 }
```

## Notes

- Default is `use_mock_llm = true` so the project runs without external LLM credentials.
- To use a real LLM, set `USE_MOCK_LLM=false` and provide `OPENAI_API_KEY`.
