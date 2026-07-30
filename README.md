# RAG Knowledge Assistant

A deployable FastAPI + pgvector RAG system with async ingestion, hybrid retrieval, citations, eval runs, Docker healthchecks, and a React web UI.

## Active Layout

This repository now uses the repo root as the only active application layout:

- `frontend/`: Vercel React + Vite UI
- `backend/`: Render web service and worker codebase
- `docker-compose.yml`: local verification stack
- `.env.example`: local and hosted environment template

## Quickstart

```bash
cp .env.example .env
docker compose up -d --build
```

API:
- `http://127.0.0.1:8010/health`
- `http://127.0.0.1:8010/docs`

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:3001/`. Local Vite proxies `/api/*` to `http://127.0.0.1:8010`, so the in-app API base override can stay empty for local testing.

## First Boot Verification

```bash
docker compose ps
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8010
```

Expected result:
- `db`, `api`, and `worker` are healthy.
- `/health` returns `status=ok`.
- The React frontend runs from Vite locally or from Vercel in production.
- async ingestion reaches `done`.
- `/api/ask` returns citations.
- eval run creation and summary retrieval both complete.

## Deployment Target

### Vercel
- Root directory: `frontend/`
- Build command: `npm run build`
- Output directory: `dist`
- Set `VITE_API_BASE_URL` to the Render backend URL when deploying frontend and backend separately.

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

## LLM Provider Setup

Default mode is safe local fallback:

```bash
LLM_PROVIDER=local
```

Recommended recruiter-demo mode:

```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash
```

Optional OpenAI-compatible mode for OpenAI, OpenRouter, Groq, DeepSeek, Qwen-compatible endpoints, or Kimi/Moonshot:

```bash
LLM_PROVIDER=openai_compatible
OPENAI_COMPAT_API_KEY=your_key_here
OPENAI_COMPAT_BASE_URL=https://openrouter.ai/api/v1
OPENAI_COMPAT_MODEL=openrouter/free
```

If the configured provider fails or no key is present, the backend falls back to a conservative local answer path that only answers from retrieved context and says when information is missing.

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
