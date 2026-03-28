# Legal Document Processor

An AI-powered system for processing messy legal documents, extracting structured information, generating grounded draft outputs, and continuously improving from operator edits.

Built for the Pearson Specter Litt AI Engineer assessment.

## Quick Start

### Prerequisites
- Docker + Docker Compose
- A free Google Gemini API key ([get one here](https://aistudio.google.com/apikey))

### Run

```bash
# 1. Clone and enter the project
cd legal-doc-processor

# 2. Set your Gemini API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Build and run
docker-compose up --build

# 4. Open the UI
# → http://localhost:3000
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

- [Backend Implementation](./BACKEND_IMPLEMENTATION.md) — service layer, API design, algorithms
- [Frontend Implementation](./FRONTEND_IMPLEMENTATION.md) — React components, pages, UX flows

---

## Sample Documents

The system ships with 5 mock legal documents demonstrating different input challenges:

| Document | Type | Challenge |
|---|---|---|
| `lease_agreement.pdf` | PDF with extractable text | Multi-page, structured legal language |
| `handwritten_note.png` | Scanned image | Simulated handwriting, noise, low quality |
| `case_filing.txt` | Text with OCR artifacts | Garbled characters, broken line breaks |
| `property_deed.pdf` | PDF (scanned look) | Degraded quality, scan artifacts |
| `notice_letter.txt` | Clean text | Baseline — tests direct text reading |

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

## Evaluation Approach & Results

### 1. Document Processing (25 pts)

**What we test:**
- PDF text extraction accuracy (compare extracted text to known content)
- OCR fallback triggers correctly for image-only pages
- Text cleaning removes artifacts without losing content
- Structured data extraction catches dates, case numbers, parties, amounts
- Chunking produces reasonable sizes with proper overlap

**How to verify:**
```bash
# Upload a sample and check extraction
curl -X POST http://localhost:8000/api/documents/upload -F "file=@sample_documents/lease_agreement.pdf"
# → Check confidence_score, extraction_method, word_count in response

# Inspect structured data
curl http://localhost:8000/api/documents/{doc_id}
# → Check structured_data.dates_found, parties, monetary_amounts
```

**Expected results:**
- Native PDFs: confidence ≥ 0.90, method = "text_extraction"
- Scanned/image docs: confidence 0.5-0.85, method = "ocr"
- Text files: confidence = 1.0, method = "direct_read"
- All documents produce chunks in the 300-600 character range

### 2. Retrieval & Grounding (25 pts)

**What we test:**
- Relevant chunks rank highest for domain queries
- Irrelevant chunks score low
- doc_ids filtering works correctly
- Generated drafts cite specific sources with [Source N] references
- No hallucinated information in drafts

**How to verify:**
```bash
# Search for a specific topic
curl -X POST http://localhost:8000/api/retrieval/search \
  -H "Content-Type: application/json" \
  -d '{"query": "monthly rent amount", "top_k": 3}'
# → Top result should be from lease_agreement, mentioning $2,450

# Generate a draft and check citations
curl -X POST http://localhost:8000/api/drafts/generate \
  -H "Content-Type: application/json" \
  -d '{"draft_type": "case_summary"}'
# → Response includes citations array with chunk_ids and relevance_scores
# → Draft content uses [Source N] references
```

**Expected results:**
- Top-3 results for "rent amount" should all come from the lease agreement
- Draft citations match the chunks used for context
- No claims in the draft without a corresponding source

### 3. Draft Quality (10 pts)

**What we test:**
- Output follows the requested structure (sections match draft type)
- Content is relevant to the documents
- Language is appropriate for legal context
- Draft is usable as a first-pass document

**How to verify:**
- Generate each of the 5 draft types
- Check that section headers match the expected structure
- Verify key facts from source documents appear in the draft
- Read for coherence and professional tone

### 4. Improvement from Edits (25 pts)

**What we test:**
- Edit diffs are computed correctly
- Edit categories are classified reasonably
- Rules are generated from edits
- Repeated similar edits boost rule confidence
- Future drafts actually change when rules are applied

**How to verify — the "before and after" test:**
```
Step 1: Generate a case_summary draft (no rules yet)
Step 2: Edit it — make it more formal, add jurisdiction info, fix a date
Step 3: Submit the edit
Step 4: Check /api/improvements/dashboard → should show new rules
Step 5: Generate another case_summary draft (rules now applied)
Step 6: Compare — the new draft should reflect the edits:
        - More formal tone
        - Jurisdiction included
        - Dates more carefully cited
```

This is the most important test. The before/after comparison should show visible improvement.

### 5. Code Quality (10 pts)

- **Modular:** Each service is independent, injected via app.state
- **Error handling:** Try/except around OCR, API calls, file operations
- **Type safety:** Pydantic models for all request/response schemas
- **Logging:** Structured logging in each service
- **Clean separation:** API routes → services → data layer

### 6. Documentation (5 pts)

- This README
- Architecture overview with diagrams
- Detailed implementation guides for backend and frontend
- Inline code comments for non-obvious logic
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
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# System dependencies (Ubuntu/Debian)
sudo apt-get install tesseract-ocr tesseract-ocr-eng poppler-utils

# Generate sample docs
python scripts/generate_samples.py

# Run
GEMINI_API_KEY=your_key uvicorn app.main:app --reload --port 8000
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
