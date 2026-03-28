# System Patterns

## Full-stack context (ARCHITECTURE)

Frontend talks to a **FastAPI** REST API. High-level backend flow:

- **Document pipeline:** File-type routing → PyMuPDF text path with **OCR fallback** (Tesseract) for image/scanned PDFs → cleaning → structured extraction (dates, parties, amounts, headers) → **paragraph-aware chunking** (~500 chars, ~100 overlap) → **sentence-transformers** (`all-MiniLM-L6-v2`, 384-d) → **FAISS IndexFlatIP** (L2-normalized ≈ cosine via inner product).
- **Draft generation:** Draft-type-aware retrieval (optional `doc_ids` filter) → load improvement rules for that draft type, sort by confidence × times applied, **top 5** → grounded prompt (`[Source N]` context) → **Gemini 2.0 Flash** (temperature **0.3**, max_tokens **4096**) → draft text + citation objects.
- **Improvement loop:** `difflib` opcodes → **heuristic** change classifier (structural, tone, factual, addition, deletion, formatting, legal precision) → rule merge/boost or create → JSON-backed rules store → injected on later generations.

Design intent (see ARCHITECTURE for rationale): hybrid OCR for speed + coverage; local embeddings to avoid upload-time API limits; IndexFlatIP for exact NN at assessment scale; JSON storage for inspectability; heuristics over LLM for classification cost/latency.

## Application shell

- **Bootstrap:** `main.jsx` entry, `App.jsx` wraps `AppProvider` → `BrowserRouter` → `Layout` → `Routes`.
- **Routes:** `/` Documents, `/search` Search, `/drafts` Drafts, `/improvements` Improvements.
- **Layout:** Fixed sidebar (`w-64`) + flexible main; sidebar shows nav (with icons: FileText, Search, PenTool, TrendingUp), active state via `useLocation()`, footer stats (doc count, index/rules hints from health), Gemini configured indicator.

## State management

- **Pattern:** React Context + `useReducer` (no Redux).
- **Initial state:** `documents`, `currentDocument`, `currentDraft`, `editHistory`, `rules`, `health`, `loading` keys (`documents`, `draft`, `search`, `edit`).
- **Actions:** `SET_*`, `SET_LOADING` with `{ key, value }`, `ADD_DOCUMENT`, `REMOVE_DOCUMENT`, `CLEAR_DRAFT`.
- **Provider effects:** On mount, `refreshDocuments()` and `checkHealth()`; expose `dispatch`, `refreshDocuments`, `checkHealth` on context.

## API integration

- **Single module:** `src/api/client.js` — one Axios instance (`baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000"`, `timeout: 120000`).
- **Groups:** Health, documents (upload, list, get, delete, load samples), retrieval search, drafts (generate, get), edits (submit, list), improvements (dashboard, delete rule, reset).
- **Dev proxy:** Vite dev server proxies `/api` → `http://localhost:8000`.

## Feature-area patterns

### Documents page

Two columns: upload + list left; detail right when selected. Uploader uses drag/drop + hidden file input; accepted extensions per spec; progress states; toast + `refreshDocuments` on success.

### Search page

Search panel: query, optional doc filter from list, top K (e.g. 1–20, default 5), results as cards with score and expandable chunk text.

### Drafts page (state machine)

Stages: `configure` → `viewing` → `editing` → `submitted` (with path back to configure for new drafts).

- **Configure:** `DraftGenerator` — draft type radios, document checkboxes, custom instructions, “apply improvements” with rule count.
- **View:** `DraftViewer` — markdown + `CitationPanel`; show applied rules; actions to edit or start new.
- **Edit:** `DraftEditor` — large textarea, notes, `submitEdit` then transition to analysis.
- **Submitted:** `EditDiffView` — side-by-side diff (`react-diff-viewer-continued`), summary, classified changes, CTA to generate again.

### Improvements page

`ImprovementDashboard` loads dashboard API; stats, category bars, rule cards with delete, recent edits (expandable), reset with confirmation.

## Shared UI

- **`StatusBadge`:** `type` = `confidence` | `category` | `status` with mappings per spec (thresholds and category colors).
- **Loading:** Button spinners, skeleton `animate-pulse` blocks for list/draft.
- **Errors:** try/catch + `toast.error` with API detail when available.

## Deployment pattern (frontend)

- Multi-stage Docker: Node build → nginx serves `dist`.
- **nginx:** SPA `try_files`, `/api/` proxied to backend with extended read timeout (120s).
- **Compose:** Frontend :3000 depends on backend :8000; backend uses Gemini env and volume for data.

## File organization (target)

Under `frontend/src/`: `api/client.js`, `context/AppContext.jsx`, `components/*`, `pages/*`, `utils/helpers.js`, plus root config files (`vite.config.js`, Tailwind, PostCSS, `Dockerfile`).
