# Step 3: Backend Recheck And DB Start

## Scope
- Recheck runtime issues reported during local run (`404` on `/`, `500` on API routes).
- Start Docker daemon and pgvector DB service.
- Verify end-to-end API flow works locally.
- Improve backend UX for root path and health clarity.

## Commands
```bash
# inspect backend + config
sed -n '1,260p' /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/src/app.py
sed -n '1,260p' /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/config/config.json

# verify docker daemon state
open -a Docker
docker info

# start db service
cd /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend
docker compose up -d db

docker ps -a --format 'table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Ports}}' | rg 'rag-pgvector|CONTAINER'

# patch backend route behavior
# edited: /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/src/app.py
# - add GET /
# - classify health as not_initialized vs down

# full self-contained smoke check
cd /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend
PYTHONPATH=. .venv/bin/python main.py > /tmp/rag_v0_singlecheck.log 2>&1 &
pid=$!
sleep 1
curl -s http://127.0.0.1:5002/
curl -s http://127.0.0.1:5002/health
curl -s -X POST http://127.0.0.1:5002/api/init-db -H 'Content-Type: application/json' -d '{}'
curl -s -X POST http://127.0.0.1:5002/api/ingest -H 'Content-Type: application/json' -d '{}'
curl -s -X POST http://127.0.0.1:5002/api/ask -H 'Content-Type: application/json' -d '{"question":"What is RAG?","top_k":2}'
kill $pid >/dev/null 2>&1 || true
wait $pid >/dev/null 2>&1 || true
```

## Verification
```bash
# DB container
# rag-pgvector Up ... 0.0.0.0:5433->5432/tcp

# GET /
# -> {"service":"RAG v0 backend", ...}

# GET /health
# -> {"status":"ok","db_status":"ok","chunk_count":...}

# POST /api/init-db
# -> {"status":"ok","message":"Database initialized"}

# POST /api/ingest
# -> {"status":"ok","ingested":{"documents":2,"chunks":2},"total_chunks":2}

# POST /api/ask
# -> returns answer + citations from indexed docs
```

## Result
- Status: done
- Notes:
  - Initial 404 on `/` was backend route mismatch (fixed with explicit root route).
  - Initial 500 errors were DB dependency not running (resolved after Docker + pgvector startup).
  - Project is now runnable end-to-end locally.

## Next
- Step4_frontend_polish_and_eval.md: add retrieval quality evaluation script and improve frontend answer/citation UI.
