# Architecture Overview

## System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                      │
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ ┌───────────────────┐  │
│  │ Documents │ │  Search  │ │    Drafts    │ │   Improvements    │  │
│  │  Upload   │ │  Query   │ │  Generate    │ │   Dashboard       │  │
│  │  List     │ │  Results │ │  View/Edit   │ │   Rules/Edits     │  │
│  │  Detail   │ │          │ │  Diff View   │ │                   │  │
│  └────┬─────┘ └────┬─────┘ └──────┬───────┘ └────────┬──────────┘  │
│       │             │              │                   │             │
└───────┼─────────────┼──────────────┼───────────────────┼─────────────┘
        │             │              │                   │
        ▼             ▼              ▼                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend (REST API)                        │
│                                                                     │
│  ┌─────────────┐  ┌───────────┐  ┌──────────┐  ┌────────────────┐  │
│  │  /documents │  │ /retrieval│  │  /drafts  │  │    /edits      │  │
│  │  /upload    │  │ /search   │  │ /generate │  │    /submit     │  │
│  │  /list      │  │           │  │ /{id}     │  │ /improvements  │  │
│  │  /{id}      │  │           │  │           │  │ /dashboard     │  │
│  └──────┬──────┘  └─────┬─────┘  └─────┬────┘  └───────┬────────┘  │
│         │               │              │                │           │
│  ┌──────▼──────────────▼──────────────▼────────────────▼────────┐  │
│  │                     Service Layer                             │  │
│  │                                                               │  │
│  │  ┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────┐ │  │
│  │  │  Document     │ │  Retrieval  │ │  Draft   │ │  Edit    │ │  │
│  │  │  Processor    │ │  Service    │ │Generator │ │ Tracker  │ │  │
│  │  │              │ │             │ │          │ │          │ │  │
│  │  │ • OCR        │ │ • FAISS     │ │ • Gemini │ │ • Diff   │ │  │
│  │  │ • PyMuPDF    │ │ • Embed     │ │ • Prompt │ │ • Classify│ │  │
│  │  │ • Clean      │ │ • Search    │ │ • Cite   │ │ • Learn  │ │  │
│  │  │ • Chunk      │ │ • Filter    │ │ • Ground │ │ • Rules  │ │  │
│  │  └──────┬───────┘ └──────┬──────┘ └────┬─────┘ └────┬─────┘ │  │
│  └─────────┼────────────────┼─────────────┼────────────┼────────┘  │
│            │                │             │            │            │
│  ┌─────────▼────────────────▼─────────────▼────────────▼────────┐  │
│  │                    Data / Storage Layer                        │  │
│  │                                                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │  │
│  │  │ Uploads  │ │ FAISS    │ │ Extracted│ │ Rules + Edits    │ │  │
│  │  │ (files)  │ │ Index    │ │ JSONs    │ │ (JSON files)     │ │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  External:  ┌────────────────┐   ┌────────────────────────────┐    │
│             │ Tesseract OCR  │   │ Google Gemini API (free)   │    │
│             └────────────────┘   └────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Document Processing Pipeline

```
Raw File (PDF/Image/Text)
    │
    ▼
┌─── File Type Detection ───┐
│                            │
├── PDF ─────────────────────┼──► PyMuPDF text extraction
│                            │       │
│                            │       ├─ text found? → use it (confidence: 0.95)
│                            │       └─ no text?    → OCR fallback (Tesseract @ 300 DPI)
│                            │
├── Image ───────────────────┼──► Tesseract OCR + confidence scoring
│                            │
└── Text ────────────────────┼──► Direct read (confidence: 1.0)
                             │
                             ▼
                    Raw Extracted Text
                             │
                             ▼
                    ┌─── Text Cleaning ───┐
                    │ • Fix OCR artifacts  │
                    │ • Normalize spaces   │
                    │ • Repair line breaks │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼───────────┐
                    │ Structured Extraction │
                    │ • Dates, case numbers │
                    │ • Parties, amounts    │
                    │ • Section headers     │
                    └─────────┬────────────┘
                              │
                    ┌─────────▼──────────────────┐
                    │ Paragraph-Aware Chunking    │
                    │ 500 chars, 100 char overlap │
                    └─────────┬──────────────────┘
                              │
                    ┌─────────▼───────────┐
                    │ Embed (MiniLM-L6-v2) │
                    │ → 384-dim vectors    │
                    └─────────┬───────────┘
                              │
                    ┌─────────▼──────┐
                    │ FAISS Index    │
                    │ (IndexFlatIP)  │
                    └────────────────┘
```

### 2. Draft Generation Pipeline

```
Draft Request (type, doc_ids, custom_instructions, use_improvements)
    │
    ├─── 1. Retrieve ─────────────────────────────┐
    │    Query FAISS with draft-type-aware query   │
    │    Filter by doc_ids if specified            │
    │    Return top-K chunks with scores           │
    │                                              │
    ├─── 2. Load Improvement Rules ───────────────┐│
    │    Filter rules matching this draft_type     ││
    │    Sort by confidence × times_applied        ││
    │    Take top 5                                ││
    │                                              ││
    ├─── 3. Build Prompt ─────────────────────────┤│
    │    System: role + structure + grounding rules││
    │    + Improvement rules (if any)              ││
    │    + Custom instructions (if any)            ││
    │    User: formatted source docs with [Source N]│
    │                                              │
    ├─── 4. Generate (Gemini 2.0 Flash) ──────────┤
    │    temperature: 0.3 (low for factual)        │
    │    max_tokens: 4096                          │
    │                                              │
    └─── 5. Return with Citations ────────────────┘
         Draft content + citation objects
         linking back to source chunks
```

### 3. Improvement Loop

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   Generate Draft ──► Operator Reviews ──► Submits Edits     │
│        ▲                                       │             │
│        │                                       ▼             │
│        │                              ┌─── Diff Engine ──┐  │
│        │                              │ difflib opcodes  │  │
│        │                              │ insert/delete/   │  │
│        │                              │ replace          │  │
│        │                              └───────┬──────────┘  │
│        │                                      │              │
│        │                              ┌───────▼──────────┐  │
│        │                              │ Classifier       │  │
│        │                              │ • structural?    │  │
│        │                              │ • tone?          │  │
│        │                              │ • factual fix?   │  │
│        │                              │ • addition?      │  │
│        │                              │ • deletion?      │  │
│        │                              │ • formatting?    │  │
│        │                              │ • legal precision│  │
│        │                              └───────┬──────────┘  │
│        │                                      │              │
│        │                              ┌───────▼──────────┐  │
│        │                              │ Rule Generator   │  │
│        │                              │ • Match existing │  │
│        │                              │   rule? → boost  │  │
│        │                              │ • New pattern?   │  │
│        │                              │   → create rule  │  │
│        │                              └───────┬──────────┘  │
│        │                                      │              │
│        │         ┌────────────────────────────┘              │
│        │         ▼                                           │
│        │  ┌─── Rules Store ──────────────────────┐          │
│        │  │ rule_id, category, rule_text,         │          │
│        │  │ confidence, times_applied, examples   │          │
│        │  └───────┬──────────────────────────────┘          │
│        │          │                                          │
│        │          │ (injected into next prompt)              │
│        └──────────┘                                          │
│                                                              │
│   The loop: each edit makes future drafts better            │
└──────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### Why Hybrid OCR?
PyMuPDF extracts text from native PDFs perfectly (fast, high accuracy). But scanned PDFs have no embedded text — they're images. The hybrid approach tries text extraction first and only falls back to OCR when needed. This gives the best speed AND coverage.

### Why FAISS IndexFlatIP?
IndexFlatIP does exact nearest-neighbor search using inner product. Since embeddings are L2-normalized, inner product = cosine similarity. It's brute-force O(n), but for our scale (<100K chunks) it's fast enough and gives exact results. No training or quantization needed.

### Why Heuristic Edit Classification (not LLM)?
Using the LLM to classify edits would be more accurate but adds latency, cost, and a dependency on the API for a core feature. Heuristics (word overlap, regex patterns, structural markers) are fast, free, deterministic, and good enough. If you wanted to improve this later, you could use Gemini for classification too.

### Why JSON File Storage (not a Database)?
For a take-home assessment, a database is unnecessary complexity. JSON files are human-readable (reviewers can inspect them), easy to debug, and perfectly sufficient for the expected data volume. In production you'd use PostgreSQL + a proper vector DB.

### Why sentence-transformers Locally (not Gemini Embeddings)?
Embeddings are called on every document upload (per chunk). Using an API for this would eat into rate limits and add latency. all-MiniLM-L6-v2 is only 80MB, runs on CPU, and produces good 384-dim embeddings. The LLM API is reserved for the expensive operation: generation.

## Assumptions

1. Documents are in English
2. Scale: tens of documents, not millions
3. Single user / operator (no auth needed)
4. Gemini free tier rate limits are acceptable (15 RPM / 1M tokens/day)
5. OCR quality is "best effort" — the system should gracefully handle bad OCR
6. Improvement rules are persistent but not versioned
7. The operator's edits are the ground truth for what "better" looks like
