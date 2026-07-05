# RAG Knowledge Assistant

A deployable FastAPI + pgvector RAG system with async ingestion, hybrid retrieval, citations, eval runs, Docker healthchecks, and a minimal web UI.

## Active Layout

This repository now uses the repo root as the only active application layout:

- `frontend/`: Vercel static UI
- `backend/`: Render web service and worker codebase
- `docker-compose.yml`: local verification stack
- `.env.example`: local and hosted environment template

## Quickstart

```bash
cp .env.example .env
docker compose up -d --build
open http://127.0.0.1:8010/
```

## First Boot Verification

```bash
docker compose ps
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8010
```

Expected result:
- `db`, `api`, and `worker` are healthy.
- `/health` returns `status=ok`.
- `/` renders the minimal upload/ask UI.
- async ingestion reaches `done`.
- `/api/ask` returns citations.
- eval run creation and summary retrieval both complete.

## Deployment Target

### Vercel
- Root directory: `frontend/`
- Configure `frontend/config.js` so `window.RAG_CONFIG.apiBaseUrl` points at the Render backend.

Example:

```js
window.RAG_CONFIG = {
  apiBaseUrl: "https://rag-knowledge-assistant-api.onrender.com",
};
```

### Render Web Service
- Root directory / Docker context: `backend/`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Public endpoints:
  - `/`
  - `/health`
  - `/docs`
  - `/api/*`

### Render Worker
- Root directory: `backend/`
- Start command: `python3 -m app.worker`

### Render Postgres
- Provide `DATABASE_URL` for the backend and worker.

## Recovery

```bash
docker compose ps
docker compose logs api --tail=80
docker compose logs worker --tail=80
docker compose restart api worker
```

## Notes

- Migrations are handled via Alembic.
- The active deployment direction is hybrid `Vercel + Render`.
- Older layouts are preserved in Git history, not in the working tree.
