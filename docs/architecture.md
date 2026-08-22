# Architecture

## Runtime ownership

The system has four runtime responsibilities:

1. `frontend/` — React/Vite client deployed to Vercel.
2. `backend/app/main.py` — FastAPI request boundary deployed as the Render web service.
3. `backend/app/worker.py` — background ingestion owner deployed as a Render worker.
4. PostgreSQL + pgvector — canonical persistence for documents, chunks, jobs, and eval runs.

## Async ingestion

`POST /api/ingest-file-async` validates upload size and file type, persists a `queued` ingestion job, and returns `202` with its job ID. It does not process the document inline.

The worker is the sole owner of queued job execution. It claims jobs with PostgreSQL row locking (`FOR UPDATE SKIP LOCKED`), performs extraction/chunking/embedding, then marks each job `done` or `error`.

## Retrieval

Retrieval supports `vector`, `fts`, and `hybrid` modes. Hybrid search combines pgvector similarity with PostgreSQL full-text rank using configured weights.

## Answer generation

Retrieved chunks are passed to the configured LLM provider. Provider failures fall back to another configured provider and ultimately to the local grounded extraction path. Answers are constrained to retrieved context.

## Security boundaries

Production deployments must configure explicit `ALLOWED_ORIGINS`. Upload and text request sizes are bounded. `DELETE /api/demo-data` is unavailable unless `ADMIN_API_KEY` is configured and the matching `X-Admin-Key` header is supplied.
