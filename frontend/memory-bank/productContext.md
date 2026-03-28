# Product Context — Frontend

## Problem (from the operator’s view)

Legal matter files arrive in messy forms (PDFs, scans, text with noise). The UI must make **ingestion quality** visible, let users **probe retrieval** before drafting, show **citations** beside generated text, and surface **what the system learned** from edits.

## Flow the UI supports

1. **Documents** — Upload or load samples; browse list; open detail for extraction, structure, and chunks.
2. **Search** — Run queries against the index; tune top-k and optional document scope.
3. **Drafts** — Pick draft type, sources, optional instructions, “use improvements”; wait for generation; read rendered markdown with evidence sidebar; edit and submit; inspect diff and classifications.
4. **Improvements** — See rules, stats, history; delete or reset as needed.

## UX expectations (`FRONTEND_IMPLEMENTATION.md`)

- **Trust:** Confidence and scores map to clear badges (high / medium / low).
- **Professional look:** Slate / blue / gray palette; restrained use of amber / emerald / red for states.
- **Long operations:** Draft generation and uploads can take many seconds; use button loading states, skeletons, and patience in copy.
- **Errors:** try/catch around API calls; prefer `err.response?.data?.detail` when showing failures.

## Personas

- **Operator:** Uses all four sections day-to-day.
- **Evaluator / demo:** Follows README / implementation guide checklist (samples → search → internal memo → edit → improvements → second draft).

## Sample content (README)

Five mock documents exercise PDF text, OCR, dirty text, scan-like PDF, and clean text—useful when testing the UI against real API responses.
