# Project Brief — Frontend (DraftForge)

This **memory bank** lives in `frontend/memory-bank/` and documents **frontend-only** scope. For full-stack or backend detail, see `../memory-bank/` at repo root (if present) or `README.md` / `ARCHITECTURE.md` in this folder.

## Purpose (UI)

The SPA lets operators: upload and inspect documents, run retrieval search, generate grounded drafts with citations, submit edits, and review learned improvement rules. Behavior and file structure are specified in **`FRONTEND_IMPLEMENTATION.md`** (authoritative for this workspace).

## Docs in this directory

| File | Use |
|------|-----|
| `FRONTEND_IMPLEMENTATION.md` | Routes, components, state, API client, UX, Vite/Docker/nginx for the SPA |
| `ARCHITECTURE.md` | End-to-end system context (helps interpret API responses and timings) |
| `README.md` | Run instructions, API endpoint table, sample documents |

Backend implementation detail: `../backend/BACKEND_IMPLEMENTATION.md` (monorepo sibling).

## Frontend goals

- **Documents:** Upload (drag/drop + file input), list, detail (metadata, structured data, full text, chunks); load samples.
- **Search:** Query + optional doc filter + top-k; scored result cards.
- **Drafts:** Configure → generate → view markdown + citations → edit → submit → diff / classified changes → generate again.
- **Improvements:** Dashboard (stats, rules, edits), delete rule, reset rules.

## Non-goals (frontend)

- No Redux; use React Context + `useReducer` per spec.
- Integrate with backend via `VITE_API_URL` (default `http://localhost:8000`) and `/api/*` (see `techContext.md`).

## Success criteria

End-to-end flow works in the UI: samples → search → draft → edit → improvements visible on the next generation; consistent loading, errors via toasts (`detail` when available), legal-office styling per implementation guide.
