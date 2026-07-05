# RAG Knowledge Assistant

A deployable FastAPI + pgvector RAG system with async ingestion, hybrid retrieval, citations, eval runs, Docker healthchecks, and a minimal web UI.

Internal build name: RAG Knowledge Assistant.

## Repo Layout

- root: current deploy-ready layout for hybrid `Vercel + Render`
- `v1/`: earlier deployable package history preserved from the original repo
- `v0/`: baseline RAG assistant history preserved from the original repo

The active deploy target now lives at the repo root:
- `frontend/` for Vercel
- `backend/` for Render web service and worker
- `docker-compose.yml` for local verification

The base Docker image is VPS-friendly and defaults to hash embeddings. Local SentenceTransformers can be enabled by installing `backend/requirements-ml.txt` and setting `EMBEDDINGS_PROVIDER=sentence_transformers`.

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

## Hybrid Deploy Target

### Vercel frontend
- Root directory: `frontend/`
- Static entrypoint: `frontend/index.html`
- Set `frontend/config.js` during deploy so `window.RAG_CONFIG.apiBaseUrl` points at the Render API origin.
- Leave `apiBaseUrl` empty for local same-origin use.

Example:

```js
window.RAG_CONFIG = {
  apiBaseUrl: "https://rag-knowledge-assistant-api.onrender.com",
};
```

### Render backend
- Root directory / Docker context: `backend/`
- Start command shape: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- The container honors Render's `PORT` automatically.
- Keep `/docs` as the engineering surface and `/api/*` as the product API.

### Render worker
- Use the same backend codebase.
- Start command: `python3 -m app.worker`
- Keep the same environment variables and database connection as the web service.

### Render Postgres
- Use a private Postgres instance for documents, chunks, jobs, eval sets, eval runs, and eval results.
- Point `DATABASE_URL` at the Render Postgres connection string.

## Legacy VPS Notes

The repository history still preserves the older `v1/` VPS-oriented package and the earlier `v0/` baseline. Those remain useful references, but the active deployment direction is now hybrid `Vercel + Render` from the repo root.

## Startup Order

- `db` starts first and must pass `pg_isready`.
- `api` waits for healthy `db`, applies Alembic migrations, then serves FastAPI.
- `worker` waits for healthy `db` and healthy `api`, then starts claiming queued ingestion jobs.

## Recovery

```bash
docker compose ps
docker compose logs api --tail=80
docker compose logs worker --tail=80
docker compose restart api worker
```

## Notes
- This is intentionally small and readable.
- Migrations are handled via Alembic (no init-db endpoint).
- The Vercel frontend uses `frontend/config.js` for the deploy-time API origin and falls back to same-origin locally.

## Smoke Eval

```bash
python3 backend/scripts/eval_smoke.py http://127.0.0.1:8010
```
