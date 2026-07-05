# Step 1: RAG v0 Scaffold And Smoke

## Scope
- Create and validate initial `13_RAG/v0` scaffold (backend, frontend, docs, sample data).
- Apply syntax fixes found during smoke checks.
- Ensure health endpoint behavior is explicit when DB is unavailable.

## Commands
```bash
# locate and read instruction rules
find .. -name instruction.md | rg '__install/instruction\.md$'
sed -n '1,260p' /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/__install/instruction.md

# scaffold project structure and files
mkdir -p ../13_RAG/v0/{backend/src,backend/config,backend/data/docs,backend/tests,frontend,docs}
python - <<'PY'
# wrote scaffold files for backend/frontend/docs
PY

# inspect generated files
find ../13_RAG/v0 -maxdepth 4 -type f | sort

# create local test env and run tests
python -m venv .venv
.venv/bin/pip install pytest numpy python-dotenv PyPDF2
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/pytest -q -p no:cacheprovider

# install runtime deps and smoke start API
.venv/bin/pip install Flask 'psycopg[binary]' pgvector
PYTHONPATH=. .venv/bin/python main.py
curl -s -i http://127.0.0.1:5002/health

# debug and fix syntax issues
nl -ba /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/src/ingest.py | sed -n '1,220p'
cat > /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/src/ingest.py <<'EOF2'
# patched file content
EOF2

nl -ba /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/src/llm.py | sed -n '1,260p'
cat > /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/src/llm.py <<'EOF2'
# patched file content
EOF2

# syntax + test verification after fixes
python - <<'PY'
# compile all backend .py files
PY
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/pytest -q -p no:cacheprovider

# harden /health response when DB is down
python - <<'PY'
# patched backend/src/app.py health route
PY

# verify degraded health response without DB
PYTHONPATH=. .venv/bin/python main.py > /tmp/rag_v0_api.log 2>&1 &
curl -s http://127.0.0.1:5002/health
```

## Verification
```bash
# unit/smoke tests
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/pytest -q -p no:cacheprovider
# -> 3 passed

# syntax compile check
python - <<'PY'
from pathlib import Path
for p in sorted(Path('/Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend').rglob('*.py')):
    compile(p.read_text(encoding='utf-8'), str(p), 'exec')
print('syntax ok')
PY
# -> syntax ok

# health endpoint when DB not running
curl -s http://127.0.0.1:5002/health
# -> {"status":"degraded","db_status":"down",...}
```

## Result
- Status: done
- Notes:
  - `backend/src/ingest.py` and `backend/src/llm.py` syntax errors were fixed.
  - `backend/src/app.py` health route now returns degraded JSON instead of 500 when Postgres is unavailable.
  - Docker daemon was unavailable during this step, so DB-backed ingest/query endpoints were not fully e2e-verified.

## Next
- Step2_e2e_pgvector_validation.md: start Docker DB, run `/api/init-db`, `/api/ingest`, and `/api/ask` end-to-end.
