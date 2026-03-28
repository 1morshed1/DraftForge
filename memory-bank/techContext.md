# Tech Context

## Stack overview (README + ARCHITECTURE)

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, Tailwind, Axios (see FRONTEND_IMPLEMENTATION for full list) |
| Backend | FastAPI, Python 3.11 |
| LLM | Google Gemini **2.0 Flash** (free API; README notes ~**15 RPM** limits) |
| Embeddings | sentence-transformers **all-MiniLM-L6-v2** (~80MB, CPU) |
| Vector store | **FAISS** IndexFlatIP |
| OCR / PDF | Tesseract + PyMuPDF |
| Ops | Docker + Docker Compose |

## Frontend stack

| Area        | Choice                        | Notes                                      |
|------------|-------------------------------|--------------------------------------------|
| Runtime    | Node 20 (Docker build)        | Alpine-based images in spec                |
| Framework  | React 18                      | With Vite                                  |
| Build      | Vite 5 + `@vitejs/plugin-react` | Dev server port 3000, `/api` proxy       |
| Styling    | Tailwind CSS 3 + PostCSS      | Utility-first                              |
| Routing    | React Router v6               | `BrowserRouter`                            |
| HTTP       | Axios 1.x                     | 120s timeout for slow LLM routes           |
| State      | Context + useReducer          | See `systemPatterns.md`                    |
| Icons      | Lucide React                  |                                            |
| Markdown   | react-markdown                | Draft rendering                            |
| Diff       | react-diff-viewer-continued   | Post-edit analysis                         |
| Toasts     | react-hot-toast               |                                            |

## Environment & configuration

- **Root:** README expects `cp .env.example .env` and **`GEMINI_API_KEY`** for Compose (backend).
- **`VITE_API_URL`:** Optional for frontend builds; client default `http://localhost:8000`.
- **Local dev:** Vite proxies `/api` → `http://localhost:8000`.
- **Docker / nginx:** Browser hits same origin; nginx proxies `/api/` to `http://backend:8000`.
- **Interactive API:** Swagger UI at `http://localhost:8000/docs` (README).

## Backend touchpoints (contract)

All paths are under `/api`:

- `GET /api/health`
- Documents: upload, list, get by id, delete, load samples
- `POST /api/retrieval/search` — body: `query`, `top_k`, optional `doc_ids`
- Drafts: `POST .../generate`, `GET .../:id`
- Edits: `POST .../submit`, `GET .../` (list)
- Improvements: dashboard, `DELETE .../rules/:id`, `POST .../reset`

Payload shapes follow naming in `FRONTEND_IMPLEMENTATION.md` (snake_case in JSON).

## Monorepo / ops

- **Compose:** Root `docker-compose.yml` — `backend` and `frontend` services, shared volume `app_data`, Gemini env on backend.
- **URLs:** UI `http://localhost:3000`; API `http://localhost:8000`.

## Running without Docker (README)

- **Backend:** `cd backend` → venv → `pip install -r requirements.txt`; system packages **tesseract-ocr**, **poppler-utils**; `GEMINI_API_KEY=... uvicorn app.main:app --reload --port 8000` (after sample generation script as documented).
- **Frontend:** `cd frontend` → `npm install` → `npm run dev` → port 3000.

## Related docs in repo

- `frontend/FRONTEND_IMPLEMENTATION.md` — UI and frontend API usage
- `frontend/ARCHITECTURE.md` — diagrams, pipelines, design decisions
- `frontend/README.md` — quick start, endpoint table, evaluation rubric, tradeoffs
- `backend/BACKEND_IMPLEMENTATION.md` — backend implementation detail
