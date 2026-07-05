# Step 2: E2E Pgvector Validation

## Scope
- Validate end-to-end RAG flow with pgvector dependency for `13_RAG/v0`.
- Check DB startup, backend health, and core API routes: `/api/init-db`, `/api/ingest`, `/api/ask`.

## Commands
```bash
# try starting pgvector service
cd /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend
docker compose up -d db

# run API and probe endpoints
cd /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend
PYTHONPATH=. .venv/bin/python main.py > /tmp/rag_v0_step2_api.log 2>&1 &
pid=$!
sleep 1

curl -s http://127.0.0.1:5002/health
curl -s -X POST http://127.0.0.1:5002/api/init-db -H 'Content-Type: application/json' -d '{}'
curl -s -X POST http://127.0.0.1:5002/api/ingest -H 'Content-Type: application/json' -d '{}'
curl -s -X POST http://127.0.0.1:5002/api/ask -H 'Content-Type: application/json' -d '{"question":"What is RAG?","top_k":3}'

kill $pid >/dev/null 2>&1 || true
wait $pid >/dev/null 2>&1 || true

tail -n 60 /tmp/rag_v0_step2_api.log
```

## Verification
```bash
# docker startup result
# -> unable to connect to docker daemon socket

# endpoint responses
# GET /health -> 200 with {"status":"degraded","db_status":"down",...}
# POST /api/init-db -> 500 connection refused (127.0.0.1:5433)
# POST /api/ingest  -> 500 connection refused (127.0.0.1:5433)
# POST /api/ask     -> 500 connection refused (127.0.0.1:5433)

# backend log confirms request handling and DB refusal errors
# -> /tmp/rag_v0_step2_api.log
```

## Result
- Status: needs follow-up
- Notes:
  - Blocking issue: Docker daemon is not running, so pgvector Postgres cannot start.
  - Backend service itself starts successfully, and `/health` degrades cleanly when DB is unavailable.
  - Full E2E retrieval/generation validation is pending DB availability.

## Next
- Step3_e2e_success_after_docker.md: start Docker daemon, run `docker compose up -d db`, then re-run `/api/init-db`, `/api/ingest`, `/api/ask` and capture successful outputs.
