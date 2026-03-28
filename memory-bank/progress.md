# Progress

## What exists today

- **Specification:** `frontend/FRONTEND_IMPLEMENTATION.md` — frontend stack, file tree, API client, state, pages, Docker/nginx, E2E workflow.
- **Architecture & ops:** `frontend/ARCHITECTURE.md` — system diagram, document/draft/improvement data flows, key decisions and assumptions. `frontend/README.md` — Docker quick start (`.env` / `.env.example`), API table, sample documents, evaluation criteria, non-Docker commands.
- **Repo state:** The `frontend/` directory in a prior snapshot had documentation only (no `src/`); re-check the tree as implementation lands.

## What works (when implemented per spec)

- Full SPA with four sections and a shared shell.
- Document lifecycle UI, retrieval search, draft pipeline with citations and edit analysis, improvement dashboard.

## What is left to build

- Scaffold the Vite/React/Tailwind app and all listed source files.
- Wire real API responses to the documented UI (loading, empty, and error states).
- Add frontend Docker + nginx config per guide; validate with backend service.

## Known gaps / risks

- **Contract drift:** If backend paths or payloads differ from the guide, `client.js` and types will need adjustment.
- **Env:** Ensure `VITE_API_URL` documented for non-proxy deployments.

## Memory bank

- Lives at `memory-bank/` (repo root). Core sources: `FRONTEND_IMPLEMENTATION.md`, `ARCHITECTURE.md`, `README.md`. Update `activeContext.md` and `progress.md` as code and backend land.
