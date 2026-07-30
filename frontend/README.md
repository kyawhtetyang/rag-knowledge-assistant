# RAG Knowledge Assistant Frontend

React + Vite frontend for the RAG Knowledge Assistant demo.

## Purpose
- Keep the public RAG UI aligned with the Kyaw Htet portfolio brand system.
- Preserve the focused upload, ingestion, ask, status, and citation workflow.
- Avoid the portfolio sidebar and multi-tab shell for this single-purpose tool.

## Local Run
```bash
npm install
npm run dev
```

The Vite dev server uses port `3001`.

## Build
```bash
npm run build
```

Vercel should use:
- root directory: `frontend/`
- build command: `npm run build`
- output directory: `dist`

## API Base
- For local development, Vite proxies `/api/*` to `http://127.0.0.1:8010`.
- Leave the in-app API base override empty when using the local Vite proxy.
- For Vercel, set `VITE_API_BASE_URL` to the deployed Render backend URL.
- The in-app API base field can override the Vite env value locally through browser storage.
