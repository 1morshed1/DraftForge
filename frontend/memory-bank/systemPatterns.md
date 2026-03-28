# System Patterns — Frontend

## Application shell

- **Entry:** `src/main.jsx` → `App.jsx` wraps `AppProvider` → `BrowserRouter` → `Layout` → `Routes`.
- **Routes:** `/` Documents, `/search` Search, `/drafts` Drafts, `/improvements` Improvements.
- **Layout:** Sidebar `w-64` + main; nav with Lucide icons (e.g. FileText, Search, PenTool, TrendingUp); active route via `useLocation()`; footer summary from health; optional Gemini configuration indicator.

## State management

- **Pattern:** React Context + `useReducer` (no Redux).
- **State:** `documents`, `currentDocument`, `currentDraft`, `editHistory`, `rules`, `health`, `loading` (`documents` | `draft` | `search` | `edit`).
- **Actions:** `SET_*`, `SET_LOADING` with `{ key, value }`, `ADD_DOCUMENT`, `REMOVE_DOCUMENT`, `CLEAR_DRAFT`.
- **Provider:** On mount, refresh documents and health; expose `dispatch`, `refreshDocuments`, `checkHealth`.

## API layer

- **Module:** `src/api/client.js` — single Axios instance, `baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"`, `timeout: 120000`.
- **Dev:** Vite proxies `/api` → `http://localhost:8000` (see `vite.config.js` in spec).

Full function list and payloads: **`FRONTEND_IMPLEMENTATION.md`** (`getHealth`, documents, retrieval, drafts, edits, improvements).

## Page patterns

| Page | Pattern |
|------|---------|
| Documents | Two columns: upload + list left; `DocumentDetail` right when selected. |
| Search | `SearchPanel`: query, doc filter, top-k, result cards with scores. |
| Drafts | Stage machine: `configure` → `viewing` → `editing` → `submitted`; components `DraftGenerator`, `DraftViewer`, `DraftEditor`, `EditDiffView`, `CitationPanel`. |
| Improvements | `ImprovementDashboard`: dashboard API, stats, rules, edits, reset. |

## Shared UI

- **`StatusBadge`:** `confidence` | `category` | `status` with thresholds and colors per implementation guide.
- **Loading:** Spinners on actions; `animate-pulse` skeletons for lists and draft body.
- **Errors:** Toast errors; surface API `detail` when present.

## Deploy (frontend artifact)

- Dockerfile: Node build → nginx serves `dist`; SPA `try_files`; `/api/` proxied to backend with long read timeout.
- Compose: defined at repo root; this service typically exposed on port **3000**.

## Target tree (`FRONTEND_IMPLEMENTATION.md`)

`src/api/client.js`, `context/AppContext.jsx`, `components/*`, `pages/*`, `utils/helpers.js`, plus Vite, Tailwind, PostCSS, Docker/nginx assets at `frontend/` root.

## Backend behavior (what affects the UI)

Only a short reminder—see **`ARCHITECTURE.md`** for diagrams: generation can be slow (Gemini); search scores come from embedding + FAISS; health may reflect index and API status. No need to implement these in the SPA; consume JSON and show honest loading/error states.
