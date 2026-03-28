# Tech Context — Frontend

## Stack (`FRONTEND_IMPLEMENTATION.md`)

| Area | Choice |
|------|--------|
| Framework | React 18 + Vite 5 |
| Styling | Tailwind CSS 3, PostCSS, Autoprefixer |
| Routing | react-router-dom v6 |
| HTTP | axios (120s timeout) |
| State | React Context + useReducer |
| Icons | lucide-react |
| Markdown | react-markdown |
| Diff | react-diff-viewer-continued |
| Toasts | react-hot-toast |

## Environment

| Variable | Role |
|----------|------|
| `VITE_API_URL` | Optional. If unset, client uses `http://localhost:8000`. |
| (repo root) `GEMINI_API_KEY` | Backend only; required for draft generation when running stack via Compose. |

Local dev: run **`npm run dev`** in `frontend/`; ensure API is on **8000** or set `VITE_API_URL`. Vite should proxy **`/api`** to the backend per spec.

## API surface (consumer view)

All requests use prefix **`/api`** (see **`README.md`** for full table):

- `GET /api/health`
- Documents: upload, list, get by id, delete, load-samples
- `POST /api/retrieval/search` — `query`, `top_k`, optional `doc_ids`
- `POST /api/drafts/generate`, `GET /api/drafts/{id}`
- `POST /api/edits/submit`, `GET /api/edits`
- `GET /api/improvements/dashboard`, `DELETE /api/improvements/rules/{id}`, `POST /api/improvements/reset`

Request/response field names: **snake_case** in JSON as in **`FRONTEND_IMPLEMENTATION.md`**. Swagger for exploration: `http://localhost:8000/docs` when backend is running.

## Running this package

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000 (per README / spec)
```

Docker build for this app: see **`FRONTEND_IMPLEMENTATION.md`** (multi-stage Node + nginx).

## Related docs (same folder)

- `FRONTEND_IMPLEMENTATION.md` — primary implementation spec
- `README.md` — monorepo quick start and endpoint list
- `ARCHITECTURE.md` — why some calls are slow or what fields mean conceptually
