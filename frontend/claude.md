# DraftForge frontend — instructions for Claude Code

Single project instructions file for **`frontend/`** (React + Vite SPA for the legal document processor). Rename to **`CLAUDE.md`** if your Claude setup only loads that filename.

## Start of session

1. Read **`memory-bank/activeContext.md`** and **`memory-bank/progress.md`** for current state.
2. For UI structure, components, API usage, and Docker/nginx for this app, treat **`FRONTEND_IMPLEMENTATION.md`** as canonical.
3. For how the system behaves end-to-end (API semantics, sample docs, run commands), use **`README.md`** and **`ARCHITECTURE.md`** in this folder.
4. Backend detail lives in **`../backend/`** (see `../backend/BACKEND_IMPLEMENTATION.md` and **`../backend/claude.md`**). OpenAPI when running: **`http://localhost:8000/docs`**.

## Authority and conflicts

- **Canonical frontend layout and UX:** `FRONTEND_IMPLEMENTATION.md` wins over generic advice.
- **Product name in docs:** Prefer **DraftForge**; README may still use legacy path names — fix runbooks when you edit them.
- **API contract:** Match paths and **snake_case** JSON bodies from the implementation guide and `README.md` endpoint table. If a response shape is unclear, confirm against the live backend or Swagger, not assumptions.

## Architecture rules

- **Stack:** React 18, Vite, Tailwind, React Router v6, Axios, Context + **`useReducer`** (no Redux unless the project explicitly changes course).
- **API:** One module **`src/api/client.js`** — shared Axios instance (`VITE_API_URL` or default `http://localhost:8000`, **120s** timeout for slow LLM routes).
- **Shell:** `AppProvider` → `BrowserRouter` → `Layout` → routes: `/`, `/search`, `/drafts`, `/improvements`.
- **Drafts page:** Implement as the **stage machine** in the spec: `configure` → `viewing` → `editing` → `submitted` (not a separate route per stage unless the spec is updated).
- **Dev proxy:** Vite should proxy **`/api`** to the backend (port **8000**) as in the implementation guide.

## UI and quality

- Follow the **legal-office** palette and **`StatusBadge`** behavior from `FRONTEND_IMPLEMENTATION.md`.
- **Loading:** button spinners, skeletons for lists and draft content; draft generation can take **10–30+** seconds.
- **Errors:** try/catch around API calls; prefer **`err.response?.data?.detail`** for toast/message text when present.

## Implementation discipline

- Match naming, imports, and patterns in files you touch. **No drive-by refactors** or unrelated files in the same change set.
- Do **not** add unsolicited markdown files, README sections, or heavy inline comments—only what the task needs.
- Prefer reusing **`src/utils/helpers.js`** and shared components over duplicating formatting logic.

## Verification

When implementation exists:

- **`npm run build`** must succeed after substantive UI changes.
- Run **`npm run dev`** and smoke the four main flows against a running API: documents (upload or load samples), search, draft generate/view/edit/submit, improvements dashboard—per `README.md` / `FRONTEND_IMPLEMENTATION.md`.
- If **`npm run lint`** (or similar) is configured in `package.json`, run it before claiming style-clean work.

## Environment

- **Node:** Use the version implied by the project’s Dockerfile / `package.json` engines when present (spec uses **Node 20** for Docker builds).
- **`VITE_API_URL`:** Optional override for API origin; default in client code targets **`http://localhost:8000`**.

## Monorepo context

- Docker Compose and **`.env` / `GEMINI_API_KEY`** are described in **`README.md`** at repo level; the SPA is usually served on **`http://localhost:3000`** with API on **8000**.
