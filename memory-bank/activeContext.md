# Active Context

## Current focus

The frontend is **specified in detail** in `frontend/FRONTEND_IMPLEMENTATION.md`. The `frontend/` tree currently holds documentation only; implementation should follow that guide when scaffolding `src/`, dependencies, and Docker assets.

**Project framing:** README positions the repo as a Pearson Specter Litt AI Engineer assessment (“Legal Document Processor”); full-stack behavior is summarized in README and detailed in `ARCHITECTURE.md` (pipelines, FAISS/Gemini/heuristics).

## Recent understanding

- **Core user journey:** Documents → Search → Drafts (configure/view/edit/diff) → Improvements → repeat draft with learned rules.
- **Backend contract:** README lists all `/api/...` endpoints; OpenAPI at `/docs` on the backend port.
- **Critical UX:** Long-running draft generation and uploads require clear loading states; API errors should surface backend `detail` when present.
- **Design system:** Legal-office palette (slate, blue, gray, amber/red/emerald for states) and reusable `StatusBadge`.

## Decisions captured from spec

- Axios single client, 2-minute timeout.
- Drafts page implemented as an explicit stage machine rather than nested routes.
- nginx + Docker for production-style static hosting with API proxy.

## Next steps (suggested)

1. Initialize Vite + React app under `frontend/` matching the structure in the implementation guide.
2. Add dependencies from the guide’s `package.json` excerpt; wire Tailwind and `vite.config` proxy.
3. Implement `api/client.js` and `AppContext` first, then Layout and pages in order of dependency (Documents → Search → Drafts → Improvements).
4. Add `Dockerfile`, `nginx.conf`, and verify against root `docker-compose.yml` when backend is available.

## Open questions (none blocking documentation)

- Confirm backend route prefixes and response types match the guide when backend is integrated.
- Align any enums (e.g. `DraftType`) with backend contracts.
