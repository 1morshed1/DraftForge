# Product Context

## Problem

Legal teams need to move from raw matter documents to structured review artifacts (summaries, memos, checklists) without losing traceability to source text. They also need their editorial preferences to persist and influence future generations.

## How it should work

1. **Ingest:** PDFs, images, and text files are uploaded, chunked, and indexed; extraction quality is surfaced (method, confidence, chunk count).
2. **Explore:** Search lets users sanity-check what evidence exists before drafting.
3. **Draft:** Users pick a draft type (e.g. case fact summary, title review, notice summary, document checklist, internal memo), select documents, optional custom instructions, and whether to apply learned improvement rules. Generation can take 10–30+ seconds; UI must communicate loading clearly.
4. **Review:** Drafts render as markdown with a citations sidebar (source file, score, snippet).
5. **Edit & learn:** Edits are submitted with optional notes; the system returns an analysis (diff, change categories, new rules). Operators can inspect rules and history on the Improvements page.
6. **Iterate:** Regenerating the same draft type should reflect accumulated rules when “apply improvements” is enabled.

## UX goals

- **Trust:** Confidence and citation scores use consistent color language (high/medium/low).
- **Professional tone:** Slate headers, blue actions, light gray surfaces, minimal clutter (per implementation guide).
- **Resilience:** Try/catch on API calls, user-facing messages from `err.response?.data?.detail` when present, toasts for success/failure.
- **Performance feel:** Spinners on buttons, skeletons for lists and draft content, patience for long draft generation.

## Primary personas

- **Operator / reviewer:** Uploads docs, searches, generates drafts, edits, and validates the improvement loop.
- **Demo / evaluator:** Follows the end-to-end checklist in `FRONTEND_IMPLEMENTATION.md` (samples → search → draft → edit → improvements → second draft).

## Sample content (README)

Five mock documents ship with the system to exercise PDF text, OCR, artifacts, scans, and clean text—for example `lease_agreement.pdf`, `handwritten_note.png`, `case_filing.txt`, `property_deed.pdf`, `notice_letter.txt`.

## System assumptions (ARCHITECTURE)

English-only input; tens of documents scale; single operator (no auth); Gemini free-tier limits acceptable; OCR is best-effort; improvement rules persist but are not versioned; **operator edits are ground truth** for what “better” means.
