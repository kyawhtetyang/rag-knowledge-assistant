# Step 6: FastAPI Migration

## Scope
- Replace Flask API layer with FastAPI in `v0/backend`.
- Keep existing endpoint contract: `/`, `/health`, `/api/init-db`, `/api/ingest`, `/api/ask`.
- Update runtime dependencies and docs references.

## Commands
```bash
# inspect current backend files
sed -n '1,320p' /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/src/app.py
sed -n '1,260p' /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/main.py
sed -n '1,260p' /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend/requirements.txt

# update files
# edited: v0/backend/src/app.py
# edited: v0/backend/main.py
# edited: v0/backend/requirements.txt
# edited: v0/README.md
# edited: v0/docs/PROJECT_OVERVIEW.md

# install fastapi runtime deps for validation
cd /Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend
.venv/bin/pip install fastapi uvicorn

# run tests
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv/bin/pytest -q -p no:cacheprovider

# syntax check (project files only)
python - <<'PY'
from pathlib import Path
base = Path('/Users/kyawhtet/Documents/EDU/CS/CSP4_GIT/13_RAG/v0/backend')
paths = [base / 'main.py']
paths += sorted((base / 'src').rglob('*.py'))
paths += sorted((base / 'tests').rglob('*.py'))
for p in paths:
    compile(p.read_text(encoding='utf-8'), str(p), 'exec')
print('syntax ok')
PY

# endpoint validation with FastAPI TestClient
PYTHONPATH=. .venv/bin/python - <<'PY'
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)
print('root', client.get('/').status_code)
print('health', client.get('/health').status_code)
print('init', client.post('/api/init-db', json={}).status_code)
print('ingest', client.post('/api/ingest', json={}).status_code)
print('ask', client.post('/api/ask', json={'question':'What is RAG?', 'top_k':2}).status_code)
PY
```

## Verification
```bash
# pytest
# -> 3 passed

# syntax
# -> syntax ok

# test client checks
# root 200
# health 200
# init 200
# ingest 200
# ask 200
```

## Result
- Status: done
- Notes:
  - FastAPI migration completed with CORS middleware and Pydantic request models.
  - Endpoint JSON behavior preserved for frontend compatibility.
  - FastAPI docs are available at `/docs` when running backend.

## Next
- Step7_fastapi_push.md: commit and push FastAPI migration changes to GitHub.
