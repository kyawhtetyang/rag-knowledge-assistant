# RAG Knowledge Assistant

A deployable Retrieval-Augmented Generation system built with FastAPI, PostgreSQL/pgvector, Docker Compose, async ingestion workers, hybrid retrieval, citations, eval runs, and a minimal web UI.

## Versions

- `v0/`: baseline RAG assistant history.
- `v1/`: deployment-ready package for `rag.kyawhtet.com`.

## v1 Quick Start

```bash
cd v1
cp .env.example .env
docker compose up -d --build
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8010
```

Open:

- UI: `http://127.0.0.1:8010/`
- API docs: `http://127.0.0.1:8010/docs`

## v1 Highlights

- FastAPI API and static UI in one deployable container.
- PostgreSQL + pgvector for document and chunk storage.
- Async ingestion worker for file processing.
- Hybrid retrieval with vector search and Postgres full-text search.
- Citation display for retrieved chunks.
- Stored eval runs for retrieval quality checks.
- Docker healthchecks for `db`, `api`, and `worker`.
- VPS deployment notes for `rag.kyawhtet.com`.
