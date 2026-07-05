# RAG Knowledge Assistant

A deployable FastAPI + pgvector RAG system with async ingestion, hybrid retrieval, citations, eval runs, Docker healthchecks, and a minimal web UI.

Internal build name: RAG Knowledge Assistant.

The frontend shell now lives in `frontend/` for Vercel, while the backend, worker, and Postgres stack stay together on Render. Locally, the backend serves the root shell and the frontend resolves the API base from the same origin by default.

The base Docker image is VPS-friendly and defaults to hash embeddings. Local SentenceTransformers can be enabled by installing `backend/requirements-ml.txt` and setting `EMBEDDINGS_PROVIDER=sentence_transformers`.

## Quickstart

```bash
cd ~/execution/06_Data_and_AI/09_RAG_Knowledge_Assistant/v0
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
- The container now honors Render's `PORT` automatically.
- Keep `/docs` as the engineering surface and `/api/*` as the product API.

### Render worker
- Use the same backend codebase.
- Start command: `python3 -m app.worker`
- Keep the same environment variables and database connection as the web service.

### Render Postgres
- Use a private Postgres instance for documents, chunks, jobs, eval sets, eval runs, and eval results.
- Point `DATABASE_URL` at the Render Postgres connection string.

## Legacy VPS Deploy Runbook

```bash
sudo mkdir -p /opt/rag_knowledge_assistant
sudo chown -R "$USER:$USER" /opt/rag_knowledge_assistant
rsync -a --delete ./ /opt/rag_knowledge_assistant/

cd /opt/rag_knowledge_assistant
cp .env.example .env
$EDITOR .env
docker compose up -d --build
docker compose ps
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8010
```

For a small VPS, keep:

```text
API_HOST_PORT=8020
EMBEDDINGS_PROVIDER=hash
```

Use `sentence_transformers` only on a machine where the extra ML dependency weight is acceptable.

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
