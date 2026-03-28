# Project Brief — DraftForge

## Purpose

**DraftForge** (workspace/repo) is a full-stack **legal document processor**: ingest messy legal files, extract structure, retrieve evidence with embeddings, generate **grounded** drafts (Gemini) with citations, and **learn** from operator edits via a rules loop. The product is documented in `frontend/README.md` as the Pearson Specter Litt AI Engineer assessment project.

## Documentation map

| Doc | Role |
|-----|------|
| `frontend/README.md` | Quick start (Docker, `.env`), API table, sample docs, evaluation notes, non-Docker run |
| `frontend/ARCHITECTURE.md` | System diagram, document/draft/improvement pipelines, backend design decisions & assumptions |
| `frontend/FRONTEND_IMPLEMENTATION.md` | Authoritative **frontend** structure, components, UX, client API |
| `backend/BACKEND_IMPLEMENTATION.md` | Backend services, API design, algorithms (see README “Implementation Guides”) |

## Frontend scope (authoritative for UI)

Planned frontend structure and behavior: `frontend/FRONTEND_IMPLEMENTATION.md` (routes, components, API usage, global state, Docker/nginx for the SPA, E2E workflow).

## Goals

- **Documents:** Upload (drag/drop + file input), list with confidence and metadata, detail view with extraction, structured data, full text, and chunks; optional sample load.
- **Search:** Query retrieval with optional document filter and top-k; show scored evidence cards.
- **Drafts:** Configure draft type and sources → generate → view markdown with citations → edit → submit edits → diff and classified changes → optional new generation with learned rules.
- **Improvements:** Dashboard for rules, stats, category breakdown, edit history, per-rule delete, reset all rules.

## Non-goals (system, from architecture README)

- Single-user, no auth; English-only docs; JSON file storage (assessment-scale, not production DB).
- Heuristic edit classification (not LLM) for speed and determinism.

## Non-goals (frontend)

- No Redux; state is Context + `useReducer` per spec.
- Frontend integrates via `VITE_API_URL` (default `http://localhost:8000`) and `/api/*` paths.

## Success criteria

Operators can run the documented workflow: samples → search → draft → edit → see improvements applied on the next draft, with consistent loading, error toasts, and legal-office visual language (slate/blue/gray palette per spec).
