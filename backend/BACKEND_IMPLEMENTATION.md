# Backend Implementation Guide

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Framework | FastAPI | Async, auto-docs, type safety |
| LLM | Google Gemini 2.0 Flash (free API) | Free tier, strong generation |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) | Local, no API cost, 384-dim |
| Vector Store | FAISS (`IndexFlatIP`) | Fast in-memory cosine similarity |
| OCR | Tesseract + PyMuPDF | Tesseract for scanned docs, PyMuPDF for native PDF text |
| Image Processing | Pillow | Pre-processing before OCR |
| Containerization | Docker | Reproducible environment |

---

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, CORS, lifespan, route mounting
│   ├── config.py                  # Settings class (env vars, paths, defaults)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # All API endpoints (single file is fine)
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Pydantic models for request/response
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_processor.py  # OCR, text extraction, cleaning, chunking
│   │   ├── embedding_service.py   # sentence-transformers wrapper
│   │   ├── retrieval_service.py   # FAISS index management + search
│   │   ├── draft_generator.py     # Gemini-powered draft generation
│   │   └── edit_tracker.py        # Edit analysis + improvement rule engine
│   └── utils/
│       ├── __init__.py
│       └── text_utils.py          # Shared text processing helpers
├── sample_documents/              # Pre-generated mock legal docs
│   ├── lease_agreement.pdf
│   ├── handwritten_note.png
│   ├── case_filing.txt
│   ├── property_deed.pdf
│   └── notice_letter.txt
├── scripts/
│   └── generate_samples.py        # Script to create the mock documents
├── tests/
│   ├── __init__.py
│   ├── test_processor.py
│   ├── test_retrieval.py
│   └── test_edit_tracker.py
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## Configuration (`app/config.py`)

A single `Settings` class reads from environment variables with sane defaults.

```python
class Settings:
    # Gemini
    GEMINI_API_KEY: str          # from env, required
    GEMINI_MODEL: str            # default: "gemini-2.0-flash"

    # Embedding
    EMBEDDING_MODEL: str         # default: "all-MiniLM-L6-v2"
    EMBEDDING_DIMENSION: int     # 384 (matches the model)

    # Storage paths (all under /app/data/ in Docker)
    FAISS_INDEX_DIR: str         # persisted FAISS index + metadata JSON
    UPLOAD_DIR: str              # raw uploaded files
    EXTRACTED_DIR: str           # processed JSON per document
    EDITS_DIR: str               # edit analysis records
    PATTERNS_DIR: str            # learned improvement rules

    # Chunking
    CHUNK_SIZE: int              # 500 chars
    CHUNK_OVERLAP: int           # 100 chars

    # Retrieval
    TOP_K: int                   # 5

    def __init__(self):
        # Create all directories on startup
```

The `__init__` should call `Path(d).mkdir(parents=True, exist_ok=True)` for each directory.

---

## Pydantic Schemas (`app/models/schemas.py`)

### Enums

```python
class DraftType(str, Enum):
    CASE_SUMMARY = "case_summary"
    TITLE_REVIEW = "title_review"
    NOTICE_SUMMARY = "notice_summary"
    DOCUMENT_CHECKLIST = "document_checklist"
    INTERNAL_MEMO = "internal_memo"

class EditCategory(str, Enum):
    STRUCTURAL = "structural"
    TONE = "tone"
    FACTUAL_CORRECTION = "factual_correction"
    ADDITION = "addition"
    DELETION = "deletion"
    FORMATTING = "formatting"
    LEGAL_PRECISION = "legal_precision"
```

### Document Processing Models

| Model | Fields | Purpose |
|---|---|---|
| `DocumentMetadata` | doc_id, filename, file_type, page_count, extraction_method, confidence_score, uploaded_at, char_count, word_count | Metadata about a processed document |
| `TextChunk` | chunk_id, doc_id, text, chunk_index, start_char, end_char, page_number | A single chunk of text for embedding |
| `ExtractedContent` | doc_id, raw_text, cleaned_text, metadata, structured_data (dict), chunks (list[TextChunk]) | Full extraction result |
| `DocumentUploadResponse` | doc_id, filename, status, metadata, chunk_count, message | API response after upload |
| `DocumentListItem` | doc_id, filename, file_type, uploaded_at, chunk_count, word_count, confidence_score | For listing documents |

### Retrieval Models

| Model | Fields | Purpose |
|---|---|---|
| `RetrievalResult` | chunk_id, doc_id, text, score, page_number, filename | A single search result |
| `RetrievalRequest` | query, top_k (default 5), doc_ids (optional filter) | Search request |
| `RetrievalResponse` | query, results (list[RetrievalResult]) | Search response |

### Draft Generation Models

| Model | Fields | Purpose |
|---|---|---|
| `DraftRequest` | draft_type, doc_ids (optional), custom_instructions, use_improvements (bool, default True) | Request to generate a draft |
| `Citation` | chunk_id, doc_id, text_snippet, relevance_score, filename | Evidence backing the draft |
| `DraftResponse` | draft_id, draft_type, content, citations, generated_at, improvement_rules_applied | Generated draft with provenance |

### Edit & Improvement Models

| Model | Fields | Purpose |
|---|---|---|
| `EditSubmission` | draft_id, original_content, edited_content, editor_notes | Operator submits their edits |
| `EditDiff` | edit_type (EditCategory), original_segment, edited_segment, context, explanation | One classified change |
| `EditAnalysis` | edit_id, draft_id, draft_type, diffs (list[EditDiff]), summary, analyzed_at | Full analysis of an edit |
| `ImprovementRule` | rule_id, draft_type, category, rule_text, examples (list[dict]), confidence, times_applied, created_from_edit_ids, created_at | A learned pattern |
| `ImprovementDashboard` | total_edits, total_rules, rules_by_category, rules, recent_edits | Dashboard data |

### Health Check

```python
class HealthResponse(BaseModel):
    status: str
    gemini_configured: bool
    documents_loaded: int
    index_size: int
    rules_count: int
```

---

## Service Layer — Detailed Implementation

### 1. Document Processor (`services/document_processor.py`)

This is the **25-point** component. It must handle messy inputs gracefully.

#### Class: `DocumentProcessor`

**Supported file types:**
- `.pdf` → PyMuPDF text extraction, fallback to Tesseract OCR
- `.png`, `.jpg`, `.jpeg`, `.tiff`, `.bmp` → Tesseract OCR
- `.txt`, `.md` → Direct read

**Main method: `async process_document(file_path, original_filename) → ExtractedContent`**

Flow:
1. Detect file type from extension
2. Generate a stable `doc_id` (MD5 hash of file bytes + short UUID)
3. Route to the appropriate extraction method
4. Clean the raw text
5. Extract structured data (regex-based)
6. Chunk the cleaned text
7. Save the result as JSON to `EXTRACTED_DIR/{doc_id}.json`
8. Return `ExtractedContent`

#### PDF Processing: `_process_pdf(path) → (raw_text, page_count, method, confidence)`

This is the most critical method. It uses a **hybrid approach**:

```
For each page in the PDF:
    1. Try PyMuPDF text extraction: page.get_text("text")
    2. If result has > 50 characters → use it (confidence: 0.95)
    3. Else → fall back to OCR:
       a. Render page to pixmap at 300 DPI
       b. Convert to PIL Image
       c. Run pytesseract.image_to_string()
       d. Also run pytesseract.image_to_data() to get per-word confidence
       e. Calculate average confidence from word-level scores
    4. Prepend each page with [Page N] or [Page N] [OCR] marker
```

The `extraction_method` field records whether it was `"text_extraction"`, `"ocr"`, or `"hybrid (text: X pages, OCR: Y pages)"`. This transparency is key for the rubric.

#### Image Processing: `_process_image(path) → (raw_text, page_count, method, confidence)`

```
1. Open with PIL, convert to RGB if needed
2. Run pytesseract.image_to_string()
3. Run pytesseract.image_to_data() for confidence scores
4. Return average confidence
```

#### Text Cleaning: `_clean_text(raw_text) → str`

Apply these fixes in order:
1. **OCR artifact fixes** (regex substitutions):
   - Standalone `l` before lowercase → `I`
   - `0` between lowercase letters → `o`
   - Remove control characters `[\x00-\x08\x0b\x0c\x0e-\x1f]`
2. **Whitespace normalization**:
   - Collapse multiple spaces/tabs to single space
   - Max 2 consecutive newlines
   - Remove blank lines
3. **Sentence repair**:
   - If a line ends with lowercase and next line starts with lowercase, join them (the original line break was probably just line wrapping)

#### Structured Data Extraction: `_extract_structured_data(text) → dict`

Use regexes to pull out legal-specific patterns:

| Pattern | Regex (simplified) | Example Match |
|---|---|---|
| Dates | `\d{1,2}[/-]\d{1,2}[/-]\d{2,4}` and `Month DD, YYYY` | "January 15, 2024" |
| Case numbers | `(Case\|No\.\|Docket\|File)\s*#?\s*[\w-]+` | "Case No. 2024-CV-1234" |
| Parties | `([A-Z]+)\s+v\.?\s+([A-Z]+)` | "SMITH v. JONES" |
| Dollar amounts | `\$[\d,]+(\.\d{2})?` | "$50,000.00" |
| Section headers | `^(SECTION\|Article\|§)\s*.+$` | "SECTION 4.2 – Termination" |

Store results in a dict with keys like `dates_found`, `case_references`, `parties`, `monetary_amounts`, `sections`.

#### Chunking: `_chunk_text(text, doc_id) → list[TextChunk]`

Strategy: **paragraph-aware chunking with overlap**.

```
1. Split text by double newlines (paragraphs)
2. Accumulate paragraphs into chunks up to CHUNK_SIZE (500 chars)
3. When a chunk is full:
   a. Save it
   b. Take the last CHUNK_OVERLAP (100) characters as overlap prefix
   c. Start the next chunk with overlap + new paragraph
4. Each chunk gets an ID: "{doc_id}_chunk_{index}"
5. Track start_char and end_char positions
```

This preserves paragraph boundaries (important for legal docs) while maintaining context overlap.

---

### 2. Embedding Service (`services/embedding_service.py`)

Simple singleton wrapper around `sentence-transformers`.

```python
class EmbeddingService:
    """Singleton. Loads model once, reuses across requests."""

    def __init__(self):
        self._model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Batch embed. Returns shape (n, 384). Normalized for cosine sim."""
        return self._model.encode(texts, normalize_embeddings=True, batch_size=32)

    def embed_query(self, query: str) -> np.ndarray:
        """Single query embed. Returns shape (384,)."""
        return self._model.encode([query], normalize_embeddings=True)[0]
```

**Key design decisions:**
- `normalize_embeddings=True` so we can use `IndexFlatIP` (inner product = cosine similarity on normalized vectors)
- Singleton pattern prevents loading the 80MB model multiple times
- `batch_size=32` for efficient GPU/CPU batching

---

### 3. Retrieval Service (`services/retrieval_service.py`)

FAISS index manager with persistence.

#### Class: `RetrievalService`

**State:**
- `self.index`: `faiss.IndexFlatIP` (inner product search, equivalent to cosine on normalized embeddings)
- `self.chunk_store`: `dict[int, dict]` mapping FAISS integer IDs → chunk metadata (text, doc_id, chunk_id, etc.)
- `self.doc_filenames`: `dict[str, str]` mapping doc_id → filename

**Persistence:**
- FAISS index saved to `{FAISS_INDEX_DIR}/index.faiss`
- Metadata saved to `{FAISS_INDEX_DIR}/metadata.json`
- Load on startup, save after every mutation

#### Methods

**`add_chunks(chunks: list[TextChunk], filename: str)`**
```
1. Extract texts from chunks
2. Batch embed with EmbeddingService
3. Add to FAISS index (index.add(embeddings))
4. Record start_id = index.ntotal before add
5. Map each new FAISS ID to chunk metadata in chunk_store
6. Save index + metadata to disk
```

**`search(query, top_k, doc_ids=None) → list[RetrievalResult]`**
```
1. Embed the query
2. Search FAISS: scores, indices = index.search(query_vec, search_k)
   - If doc_ids filter is set, search 3x top_k to account for filtering
3. For each result:
   - Look up chunk metadata from chunk_store
   - Skip if doc_ids filter is set and this chunk's doc_id isn't in it
   - Build RetrievalResult with score, text, metadata
4. Return top_k results
```

**`remove_document(doc_id)`**
```
1. Filter chunk_store to find entries NOT matching doc_id
2. Rebuild a fresh FAISS index from remaining chunks
3. Re-embed and re-add (FAISS doesn't support deletion natively)
4. Save to disk
```

**`clear()`** — Reset everything. **`get_index_size()`** — Return `index.ntotal`.

---

### 4. Draft Generator (`services/draft_generator.py`)

#### Prompt Templates

Define a dict `DRAFT_PROMPTS: dict[DraftType, str]` with system prompts for each draft type. Each prompt should:

1. Define the role ("You are a legal analyst at a law firm...")
2. Specify the output structure (numbered sections with headers)
3. Include grounding instructions:
   - "Only include information supported by the source documents"
   - "Use [Source N] references to cite specific documents"
   - "If information is unclear, note this explicitly"
   - "Do not make assumptions beyond what the documents state"

**Example structures by type:**

| Draft Type | Sections |
|---|---|
| case_summary | Case Overview → Key Facts → Legal Issues → Current Status |
| title_review | Property ID → Chain of Title → Encumbrances → Issues → Recommendations |
| notice_summary | Notice Type → Parties → Key Dates → Required Actions → Compliance |
| document_checklist | Present → Referenced → Potentially Needed → Completeness Assessment |
| internal_memo | TO/FROM/DATE/RE → Summary → Background → Analysis → Recommendations → Open Questions |

#### Class: `DraftGenerator`

**`__init__`:**
```python
genai.configure(api_key=settings.GEMINI_API_KEY)
self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
```

**`async generate_draft(request, retrieved_chunks, improvement_rules) → DraftResponse`**

Flow:
```
1. Generate draft_id (uuid)
2. Build context string from retrieved chunks:
   "[Source 1] (from: filename, relevance: 0.87)\n{chunk text}\n---\n[Source 2]..."
3. Build citations list from the same chunks
4. Get system prompt for the draft_type
5. If use_improvements=True and rules exist:
   → Append "ADDITIONAL GUIDELINES (learned from previous edits):\n"
   → Format each rule: "1. [tone] Always use formal language..."
   → Include one example per rule if available
6. If custom_instructions set, append those too
7. Build user prompt:
   "Based on the following source documents, generate a {draft_type}.\n\nSOURCE DOCUMENTS:\n{context}"
8. Call Gemini: model.generate_content(full_prompt, generation_config={temperature=0.3, max_output_tokens=4096})
9. Save draft JSON to disk
10. Return DraftResponse with content, citations, rules_applied
```

**Fallback:** If Gemini is not configured or fails, return a message explaining the issue and show the retrieved context so the user can see retrieval is working.

**`_format_improvement_rules(rules) → str`**
```
For each rule:
  "1. [category] rule_text"
  "   Example: 'before text' → 'after text'"
```

---

### 5. Edit Tracker (`services/edit_tracker.py`) ⭐ Most Important for Scoring

This is the **25-point** improvement loop. It has two parts: **EditTracker** (captures and classifies edits) and **ImprovementEngine** (learns rules from edits).

#### Class: `EditTracker`

**`analyze_edit(submission: EditSubmission, draft_type: str) → EditAnalysis`**

Flow:
```
1. Generate edit_id
2. Compute structured diffs using difflib
3. Classify each diff by category
4. Generate a summary
5. Save to disk
6. Return EditAnalysis
```

**`_compute_diffs(original, edited) → list[dict]`**

Use `difflib.SequenceMatcher` to get opcodes:

```python
matcher = difflib.SequenceMatcher(None, original_lines, edited_lines)
for op, i1, i2, j1, j2 in matcher.get_opcodes():
    if op == "equal":
        continue
    diffs.append({
        "operation": op,  # "replace", "insert", "delete"
        "original": "\n".join(original_lines[i1:i2]),
        "edited": "\n".join(edited_lines[j1:j2]),
        "context": "\n".join(original_lines[max(0,i1-2):i1]),  # 2 lines before
    })
```

**`_classify_diff(diff) → EditDiff`**

Heuristic classification based on what changed:

```python
# Check what kind of edit this is:
if diff["operation"] == "insert":
    category = EditCategory.ADDITION
elif diff["operation"] == "delete":
    category = EditCategory.DELETION
elif _is_structural_change(orig, edited):
    # Headers added/changed, sections reordered, bullets ↔ prose
    category = EditCategory.STRUCTURAL
elif _is_tone_change(orig, edited):
    # Similar content but different word choices (formal/informal)
    # Check word overlap ratio is high but exact match is low
    category = EditCategory.TONE
elif _is_factual_correction(orig, edited):
    # Numbers, dates, names changed
    category = EditCategory.FACTUAL_CORRECTION
elif _is_formatting_change(orig, edited):
    # Whitespace, punctuation, capitalization only
    category = EditCategory.FORMATTING
else:
    # Guess based on content
    category = EditCategory.LEGAL_PRECISION
```

Helper detection functions:

| Function | Logic |
|---|---|
| `_is_structural_change` | Check if markdown headers (`#`, `##`) were added/moved, or list markers changed |
| `_is_tone_change` | High word overlap (>60%) but low exact match — means same ideas, different wording |
| `_is_factual_correction` | Regex check for changes in numbers, dates, proper nouns |
| `_is_formatting_change` | After stripping whitespace and punctuation, texts are identical |

---

#### Class: `ImprovementEngine`

This is the heart of the improvement loop.

**State:**
- `self.rules`: `list[ImprovementRule]` — loaded from `{PATTERNS_DIR}/rules.json`
- `self.edit_history`: `list[EditAnalysis]` — loaded from `{EDITS_DIR}/`

**`learn_from_edit(analysis: EditAnalysis) → list[ImprovementRule]`**

This method extracts generalizable patterns from a specific edit:

```
For each diff in analysis.diffs:
    1. Check if an existing rule already covers this type of change
       (same category + similar content → boost confidence)
    2. If existing rule found:
       → Increment times_applied
       → Add this example to the rule's examples list
       → Boost confidence by 0.1 (cap at 1.0)
    3. If no existing rule matches:
       → Generate a new rule:
         - rule_text: Generalize the edit into an instruction
         - category: From the diff classification
         - examples: [{"before": original, "after": edited}]
         - confidence: 0.5 (starting)
         - draft_type: From the analysis
    4. Save rules to disk
```

**Rule generation — `_generate_rule_text(diff) → str`**

This is where the intelligence lives. Pattern-match common edit types:

```python
if diff.edit_type == EditCategory.TONE:
    # Compare formality
    if _is_more_formal(diff.edited_segment, diff.original_segment):
        return "Use formal legal language. Avoid casual phrasing."
    else:
        return "Use plain language. Avoid overly formal or archaic terms."

elif diff.edit_type == EditCategory.STRUCTURAL:
    if "##" in diff.edited_segment and "##" not in diff.original_segment:
        return "Use section headers (##) to organize content."
    elif _has_bullet_points(diff.edited_segment):
        return "Use bullet points for lists of items or conditions."

elif diff.edit_type == EditCategory.ADDITION:
    # Analyze what was added
    added_text = diff.edited_segment
    if re.search(r"jurisdiction|venue|court", added_text, re.I):
        return "Always include jurisdiction and venue information."
    elif re.search(r"date|deadline|timeline", added_text, re.I):
        return "Include relevant dates, deadlines, and timelines."
    elif re.search(r"party|parties|plaintiff|defendant", added_text, re.I):
        return "Explicitly identify all parties with their full names and roles."

elif diff.edit_type == EditCategory.DELETION:
    removed = diff.original_segment
    if re.search(r"may|might|possibly|perhaps", removed, re.I):
        return "Avoid hedging language. State findings directly."

elif diff.edit_type == EditCategory.FACTUAL_CORRECTION:
    return "Double-check all factual claims (dates, amounts, names) against source documents."

elif diff.edit_type == EditCategory.LEGAL_PRECISION:
    return "Use precise legal terminology. Be specific about legal concepts."
```

**`get_applicable_rules(draft_type, max_rules=5) → list[ImprovementRule]`**

```
1. Filter rules where draft_type matches OR draft_type is None (universal)
2. Sort by confidence * times_applied (descending) — most-validated rules first
3. Return top max_rules
```

**Rule matching — `_find_matching_rule(diff, existing_rules) → ImprovementRule | None`**

Check if an existing rule already covers this type of change:
```
For each existing rule:
    1. Same category?
    2. Similar content? (use simple word overlap on rule_text vs diff explanation)
    3. If both → return the rule (it's a match, boost it)
```

**Persistence:**
- Rules saved as JSON array to `{PATTERNS_DIR}/rules.json`
- Load on startup, save after every mutation

---

## API Layer (`app/api/routes.py`)

Use a single `APIRouter` with prefixed groups.

### Endpoints

#### Health & Status

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | System health: Gemini status, doc count, index size, rules count |

#### Document Processing

| Method | Path | Request | Response | Description |
|---|---|---|---|---|
| `POST` | `/api/documents/upload` | `multipart/form-data` with `file` field | `DocumentUploadResponse` | Upload and process a document |
| `GET` | `/api/documents` | — | `list[DocumentListItem]` | List all processed documents |
| `GET` | `/api/documents/{doc_id}` | — | `ExtractedContent` | Get full extracted content for a doc |
| `DELETE` | `/api/documents/{doc_id}` | — | `{status, message}` | Delete a document and its chunks from the index |
| `POST` | `/api/documents/load-samples` | — | `list[DocumentUploadResponse]` | Load pre-generated sample documents |

#### Retrieval

| Method | Path | Request | Response | Description |
|---|---|---|---|---|
| `POST` | `/api/retrieval/search` | `RetrievalRequest` body | `RetrievalResponse` | Search for relevant chunks |

#### Draft Generation

| Method | Path | Request | Response | Description |
|---|---|---|---|---|
| `POST` | `/api/drafts/generate` | `DraftRequest` body | `DraftResponse` | Generate a grounded draft |
| `GET` | `/api/drafts/{draft_id}` | — | `DraftResponse` | Retrieve a previously generated draft |

#### Edit Tracking & Improvement

| Method | Path | Request | Response | Description |
|---|---|---|---|---|
| `POST` | `/api/edits/submit` | `EditSubmission` body | `EditAnalysis` | Submit an edit and get the analysis |
| `GET` | `/api/edits` | — | `list[EditAnalysis]` | List all edit analyses |
| `GET` | `/api/improvements/dashboard` | — | `ImprovementDashboard` | Get improvement rules + stats |
| `DELETE` | `/api/improvements/rules/{rule_id}` | — | `{status}` | Delete a specific rule |
| `POST` | `/api/improvements/reset` | — | `{status}` | Clear all rules |

### Upload Endpoint Detail

```python
@router.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    # 1. Validate file extension against SUPPORTED_TYPES
    # 2. Save to UPLOAD_DIR with original filename
    # 3. Call document_processor.process_document(saved_path, file.filename)
    # 4. Call retrieval_service.add_chunks(extracted.chunks, file.filename)
    # 5. Return DocumentUploadResponse
    # 6. Wrap in try/except and return 400/500 on errors
```

### Draft Endpoint Detail

```python
@router.post("/api/drafts/generate")
async def generate_draft(request: DraftRequest):
    # 1. Build a retrieval query from the draft type:
    #    query = f"{draft_type} relevant information summary"
    #    If doc_ids is specified, pass them to search()
    # 2. retrieved = retrieval_service.search(query, top_k=8, doc_ids=request.doc_ids)
    # 3. If use_improvements: rules = improvement_engine.get_applicable_rules(request.draft_type)
    # 4. draft = await draft_generator.generate_draft(request, retrieved, rules)
    # 5. Return draft
```

### Edit Endpoint Detail

```python
@router.post("/api/edits/submit")
async def submit_edit(submission: EditSubmission):
    # 1. Load the original draft to get its draft_type
    # 2. analysis = edit_tracker.analyze_edit(submission, draft_type)
    # 3. new_rules = improvement_engine.learn_from_edit(analysis)
    # 4. Return analysis (with info about new/updated rules)
```

---

## FastAPI App (`app/main.py`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize services (loads FAISS index, embedding model, rules)
    app.state.document_processor = DocumentProcessor()
    app.state.retrieval_service = RetrievalService()
    app.state.draft_generator = DraftGenerator()
    app.state.edit_tracker = EditTracker()
    app.state.improvement_engine = ImprovementEngine()
    yield
    # Shutdown: save state if needed

app = FastAPI(title="Legal Document Processor", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
```

**Important:** Store service instances in `app.state` and access them in route handlers via `request.app.state.retrieval_service` etc. This avoids circular imports and makes testing easier.

---

## Sample Document Generation (`scripts/generate_samples.py`)

Create 5 realistic mock legal documents to demonstrate the pipeline. Use Python to generate them:

### 1. Lease Agreement (PDF with extractable text)
Use `reportlab` to create a multi-page lease agreement with:
- Parties: "GREENFIELD PROPERTIES LLC" (Landlord) vs "JOHN M. DAVIDSON" (Tenant)
- Property: 742 Evergreen Terrace, Unit 4B
- Terms: Monthly rent $2,450, security deposit $4,900, 12-month term
- Clauses: utilities, maintenance, termination, late fees
- Signatures and date lines

### 2. Handwritten Note (PNG image — simulated)
Use Pillow to create an image with handwritten-style text:
- Add noise, slight rotation, uneven baselines
- Content: short notes from a meeting ("Discussed settlement terms with opposing counsel. They proposed $75,000. Client willing to consider $85,000 minimum. Need to file motion by March 15...")
- Use a handwriting-style font if available, otherwise use text with noise/distortion

### 3. Case Filing (TXT with formatting issues)
Create a messy text file simulating OCR output:
- Mix of proper and garbled text
- Random line breaks mid-sentence
- Some characters replaced (l→1, O→0, etc.)
- Content: civil complaint filing with case number, parties, allegations

### 4. Property Deed (PDF — scanned look)
Use reportlab with intentionally degraded quality:
- Lower DPI, some "scan artifacts" (gray backgrounds, slight skew)
- Content: warranty deed with legal description, parcel number, consideration amount

### 5. Notice Letter (TXT)
Standard text file:
- Breach of contract notice
- From: attorney to opposing party
- References deadlines, cure period, specific contract clauses

---

## Docker Setup

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

# Install system dependencies for Tesseract and PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data directories
RUN mkdir -p /app/data/uploads /app/data/extracted /app/data/faiss_indexes \
    /app/data/edits /app/data/patterns

# Generate sample documents
RUN python scripts/generate_samples.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `requirements.txt`

```
fastapi==0.115.0
uvicorn[standard]==0.30.0
python-multipart==0.0.9
pydantic==2.9.0

# LLM
google-generativeai==0.8.0

# Embeddings & Vector Store
sentence-transformers==3.0.0
faiss-cpu==1.8.0
numpy==1.26.0

# Document Processing
PyMuPDF==1.24.0
pytesseract==0.3.10
Pillow==10.4.0

# PDF Creation (for sample docs)
reportlab==4.2.0

# Utilities
python-dotenv==1.0.0
```

### `.env.example`

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash
```

---

## Testing Strategy (`tests/`)

### `test_processor.py`
- Test PDF text extraction with a simple generated PDF
- Test OCR fallback by creating an image with text
- Test text cleaning (OCR artifact removal, whitespace normalization)
- Test chunking (correct sizes, overlap, boundary handling)
- Test structured data extraction (dates, case numbers, parties regex)

### `test_retrieval.py`
- Test add_chunks + search returns correct results
- Test score ordering (most relevant first)
- Test doc_ids filtering
- Test remove_document rebuilds index correctly
- Test empty index returns empty results

### `test_edit_tracker.py`
- Test diff computation (insert, delete, replace)
- Test edit classification (structural, tone, factual, etc.)
- Test rule generation from different edit types
- Test rule boosting (same edit pattern twice → higher confidence)
- Test get_applicable_rules filters by draft_type

Run with: `pytest tests/ -v`

---

## Key Architecture Decisions & Tradeoffs

| Decision | Rationale | Tradeoff |
|---|---|---|
| Local embeddings, remote LLM | Embeddings are called frequently (every upload); LLM is called less often. Local embeddings = no rate limits on upload. | Gemini free tier has rate limits on generation |
| FAISS IndexFlatIP (brute force) | Simple, no training needed, exact results | O(n) search — fine for <100K chunks, would need IVF for millions |
| Paragraph-aware chunking | Legal docs have meaningful paragraph structure | Some chunks may be shorter than optimal |
| Heuristic edit classification | No ML training needed, works immediately | Less accurate than a fine-tuned classifier |
| Rule-based improvement loop | Interpretable, inspectable, doesn't need training data | Can't learn complex stylistic patterns |
| JSON file persistence | Simple, no database needed | Not suitable for production scale |
