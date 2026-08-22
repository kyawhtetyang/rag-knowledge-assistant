# Release Process

The repository uses Semantic Versioning tags (`vMAJOR.MINOR.PATCH`).

## Branch convention

- `main` — releasable integration branch.
- `release/vX.Y.Z` — temporary stabilization branch for a planned release.
- `feature/*` and `fix/*` — optional scoped development branches.

## Release gate

Before tagging a release:

```bash
cd backend
pytest -q

cd ../frontend
npm ci
npm run lint
npm run build

cd ..
docker build -t rag-knowledge-assistant-backend ./backend
```

For a full local integration check:

```bash
cp .env.example .env
docker compose up -d --build
python3 backend/scripts/first_boot_verify.py http://127.0.0.1:8010
```

All required GitHub CI jobs must pass on the release commit before it is merged and tagged.

## Tagging

After the validated release branch is merged to `main`:

```bash
git switch main
git pull --ff-only origin main
git tag -a vX.Y.Z -m "RAG Knowledge Assistant vX.Y.Z"
git push origin vX.Y.Z
```

Patch releases contain compatible fixes. Minor releases add compatible functionality or significant internal capability. `v1.0.0` is reserved for the first production-stable contract after the v0.9 stabilization line has been validated in deployment.
