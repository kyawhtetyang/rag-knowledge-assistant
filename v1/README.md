# RAG Knowledge Assistant

A deployable FastAPI + pgvector RAG system with async ingestion, hybrid retrieval, citations, eval runs, Docker healthchecks, and a minimal web UI.

Internal build name: Mini RAGFlow.

## Quickstart

```bash
cd ~/execution/06_Data_and_AI/09_Mini_RAGFlow/v0
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

## VPS Deploy Runbook

```bash
sudo mkdir -p /opt/mini-ragflow
sudo chown -R "$USER:$USER" /opt/mini-ragflow
rsync -a --delete ./ /opt/mini-ragflow/

cd /opt/mini-ragflow
cp .env.example .env
$EDITOR .env
docker compose up -d --build
docker compose ps
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8010
```

Recommended nginx site:

```nginx
server {
    listen 80;
    server_name rag.kyawhtet.com;

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

After DNS points at the VPS:

```bash
sudo ln -s /etc/nginx/sites-available/mini-ragflow /etc/nginx/sites-enabled/mini-ragflow
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d rag.kyawhtet.com
```

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

## Smoke Eval

```bash
python3 backend/scripts/eval_smoke.py http://127.0.0.1:8010
```
