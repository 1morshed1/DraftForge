# Active Context — Frontend

## Focus

Ship the SPA described in **`FRONTEND_IMPLEMENTATION.md`**: `AppContext`, `client.js`, layout, four pages, and shared components with the documented loading/error/visual patterns.

## Current state (2026-03-28)

- **Backend:** Fully implemented and end-to-end verified. Running in Docker on `localhost:8000`. Swagger at `/docs`.
- **Frontend:** Not yet started. No scaffold, no `package.json`, no `src/`. Only documentation exists.
- **Next step:** Scaffold Vite + React + Tailwind project, then build out components per spec.

## This memory bank

- **Location:** `frontend/memory-bank/` (visible when the workspace is `frontend/`).
- **Scope:** Frontend implementation and integration with the REST API only.

## When implementing

1. Align file paths and exports with the guide's tree.
2. Keep Axios in one module; use a 2-minute timeout for generation-heavy routes.
3. Drafts page: preserve the explicit stage machine (`configure` → `viewing` → `editing` → `submitted`).
4. Verify against the live backend (`npm run dev` + API on 8000, or Compose).

## Open checks

- Enum values for **`draft_type`** must match backend (confirm via `localhost:8000/docs`).
- Response shapes: confirm optional fields and nulls against live `/docs` so the UI does not assume too much.
