# DraftForge

An AI-powered system for processing messy legal documents, extracting structured information, generating grounded draft outputs, and continuously improving from operator edits.

Built for the Pearson Specter Litt AI Engineer assessment.

## Quick Start

### Prerequisites
- Docker + Docker Compose
- A free Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### Run

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd DraftForge

# 2. Set your Gemini API key
cp backend/.env.example backend/.env
# Edit backend/.env and add your GEMINI_API_KEY

# 3. Build and run
docker compose up --build

# 4. Open the UI
# Frontend → http://localhost:3000
# Backend API docs → http://localhost:8000/docs
```

### First Steps
1. Click **"Load Sample Documents"** on the Documents page to ingest 5 pre-built mock legal documents
2. Go to **Search** and try: "lease termination clause" — see retrieval in action
3. Go to **Drafts**, select "Internal Memo", check all docs, and click **Generate**
4. Click **Edit This Draft**, make changes (formalize language, add details), and submit
5. Go to **Improvements** to see what rules were learned
6. Generate the same draft type again — notice the improvements

---

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for the full system diagram and data flow.

**Summary:**
- **Document Processing:** PyMuPDF + Tesseract OCR (hybrid), text cleaning, paragraph-aware chunking
- **Retrieval:** sentence-transformers (all-MiniLM-L6-v2) embeddings → FAISS IndexFlatIP
- **Generation:** Google Gemini 2.0 Flash with grounded prompts + citation tracking
- **Improvement Loop:** difflib-based edit analysis → heuristic classification → rule extraction → prompt injection

## Implementation Guides

- [Backend Implementation](./backend/BACKEND_IMPLEMENTATION.md) — service layer, API design, algorithms
- [Frontend Implementation](./frontend/FRONTEND_IMPLEMENTATION.md) — React components, pages, UX flows

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System status |
| `POST` | `/api/documents/upload` | Upload and process a document |
| `GET` | `/api/documents` | List all documents |
| `GET` | `/api/documents/{doc_id}` | Get document details |
| `DELETE` | `/api/documents/{doc_id}` | Remove a document |
| `POST` | `/api/documents/load-samples` | Load sample documents |
| `POST` | `/api/retrieval/search` | Search for relevant chunks |
| `POST` | `/api/drafts/generate` | Generate a grounded draft |
| `GET` | `/api/drafts/{draft_id}` | Get a saved draft |
| `POST` | `/api/edits/submit` | Submit operator edits |
| `GET` | `/api/edits` | List all edit analyses |
| `GET` | `/api/improvements/dashboard` | Get rules + stats |
| `DELETE` | `/api/improvements/rules/{rule_id}` | Delete a rule |
| `POST` | `/api/improvements/reset` | Clear all rules |

Interactive docs available at `http://localhost:8000/docs` (Swagger UI).

---

## How to Evaluate

Below is a walkthrough to verify each capability end-to-end.

### 1. Document Processing (25 pts)

The hybrid extraction pipeline handles native PDFs, scanned images, and raw text files:

```bash
# Upload a sample and inspect the response
curl -X POST http://localhost:8000/api/documents/upload \
  -F "file=@sample_documents/lease_agreement.pdf"
```

| Input type | Expected confidence | Extraction method |
|---|---|---|
| Native PDF | ≥ 0.90 | `text_extraction` |
| Scanned/image | 0.5–0.85 | `ocr` |
| Plain text | 1.0 | `direct_read` |

All documents produce paragraph-aware chunks in the 300–600 character range. Structured metadata (dates, parties, amounts) is available via `GET /api/documents/{doc_id}`.

### 2. Retrieval & Grounding (25 pts)

Semantic search uses L2-normalized MiniLM embeddings with FAISS cosine similarity. Drafts are grounded with `[Source N]` citations linked back to retrieved chunks.

```bash
# Semantic search
curl -X POST http://localhost:8000/api/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{"query": "monthly rent amount", "top_k": 3}'
# → Top results come from the lease agreement, mentioning $2,450

# Generate a grounded draft
curl -X POST http://localhost:8000/api/drafts/generate \
  -H "Content-Type: application/json" \
  -d '{"draft_type": "case_summary"}'
# → Response includes citations with chunk_ids and relevance_scores
```

### 3. Draft Quality (10 pts)

Five draft types are supported (case summary, internal memo, client letter, contract review, compliance report). Each follows a structured template with professional legal tone. Best verified through the UI — generate a draft on the Drafts page and review the output.

### 4. Improvement from Edits (25 pts)

This is the core feedback loop. To see it in action:

1. Generate a `case_summary` draft (no rules exist yet)
2. Click **Edit This Draft**, make changes — formalize language, add jurisdiction info, fix a date
3. Submit the edit
4. Visit the **Improvements** page — new rules appear with categories and confidence scores
5. Generate another `case_summary` — the new draft reflects your edits (more formal tone, jurisdiction included, etc.)

Repeated similar edits boost rule confidence. Rules are injected into the system prompt for future generations.

### 5. Code Quality (10 pts)

- **Modular:** Each service is independent, injected via `app.state` through a lifespan handler
- **Error handling:** Try/except around OCR, Gemini API calls, and file I/O with clear HTTP error responses
- **Type safety:** Pydantic v2 models for all request/response schemas
- **Logging:** Structured logging in each service
- **Clean separation:** API routes → service layer → data/storage layer

### 6. Documentation (5 pts)

- This README with quick start, API reference, and evaluation guide
- [Architecture overview](./ARCHITECTURE.md) with system diagrams and data flow
- Detailed implementation guides for [backend](./backend/BACKEND_IMPLEMENTATION.md) and [frontend](./frontend/FRONTEND_IMPLEMENTATION.md)
- `.env.example` for configuration

---

## Assumptions & Tradeoffs

| Assumption | Tradeoff |
|---|---|
| English-only documents | Simplifies OCR and NLP; would need multilingual models for other languages |
| JSON file storage | Simple and inspectable, but not suitable for production scale |
| Heuristic edit classification | Fast and free, but less accurate than LLM-based classification |
| Free Gemini API | No cost, but 15 RPM rate limit; would use paid tier for production |
| Local embeddings | No rate limits on upload, but requires 80MB model download in Docker |
| Single-user system | No auth complexity; production would need user management |
| Rule-based improvement | Interpretable and inspectable, but can't learn complex patterns |

---

## Running Without Docker

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# System dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# Set up environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Generate sample docs
python scripts/generate_samples.py

# Run
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

---

## Tech Stack Summary

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS, Axios |
| Backend | FastAPI, Python 3.11 |
| LLM | Google Gemini 2.0 Flash (free API) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector Store | FAISS (IndexFlatIP) |
| OCR | Tesseract + PyMuPDF |
| Container | Docker + Docker Compose |
