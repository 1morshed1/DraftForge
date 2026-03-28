# Frontend Implementation Guide

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Framework | React 18 + Vite | Fast dev server, modern tooling |
| Styling | Tailwind CSS | Utility-first, rapid styling |
| HTTP Client | Axios | Clean API integration |
| Routing | React Router v6 | SPA navigation |
| State | React Context + useReducer | Sufficient for this scope, no Redux overhead |
| Icons | Lucide React | Clean, consistent icon set |
| Diff View | react-diff-viewer-continued | For showing edit diffs side-by-side |
| Markdown | react-markdown | Render LLM-generated markdown drafts |
| Notifications | react-hot-toast | Simple toast notifications |

---

## Project Structure

```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── main.jsx                    # React entry point
│   ├── App.jsx                     # Router + layout shell
│   ├── api/
│   │   └── client.js               # Axios instance + all API functions
│   ├── context/
│   │   └── AppContext.jsx           # Global state (documents, drafts, rules)
│   ├── components/
│   │   ├── Layout.jsx              # Sidebar + main content shell
│   │   ├── Sidebar.jsx             # Navigation sidebar
│   │   ├── DocumentUploader.jsx    # Drag-and-drop file upload
│   │   ├── DocumentList.jsx        # List of processed documents
│   │   ├── DocumentDetail.jsx      # Show extraction details for one doc
│   │   ├── SearchPanel.jsx         # Retrieval search interface
│   │   ├── DraftGenerator.jsx      # Draft type selector + generate button
│   │   ├── DraftViewer.jsx         # Rendered draft with citations sidebar
│   │   ├── DraftEditor.jsx         # Editable draft with submit
│   │   ├── EditDiffView.jsx        # Side-by-side diff display
│   │   ├── ImprovementDashboard.jsx # Rules list, stats, category breakdown
│   │   ├── CitationPanel.jsx       # Citations sidebar for draft view
│   │   └── StatusBadge.jsx         # Reusable status/confidence badges
│   ├── pages/
│   │   ├── DocumentsPage.jsx       # Upload + document list + detail
│   │   ├── SearchPage.jsx          # Retrieval search
│   │   ├── DraftsPage.jsx          # Generate + view + edit drafts
│   │   └── ImprovementsPage.jsx    # Edit history + rules dashboard
│   └── utils/
│       └── helpers.js              # Format dates, truncate text, etc.
├── package.json
├── vite.config.js
├── tailwind.config.js
├── postcss.config.js
└── Dockerfile
```

---

## API Client (`src/api/client.js`)

Single file with an Axios instance and exported functions for every endpoint.

```javascript
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min timeout — Gemini can be slow
});
```

### Exported Functions

```javascript
// ── Health ──
export const getHealth = () => api.get("/api/health");

// ── Documents ──
export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return api.post("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};
export const getDocuments = () => api.get("/api/documents");
export const getDocument = (docId) => api.get(`/api/documents/${docId}`);
export const deleteDocument = (docId) => api.delete(`/api/documents/${docId}`);
export const loadSamples = () => api.post("/api/documents/load-samples");

// ── Retrieval ──
export const searchDocuments = (query, topK = 5, docIds = null) =>
  api.post("/api/retrieval/search", { query, top_k: topK, doc_ids: docIds });

// ── Drafts ──
export const generateDraft = (draftType, docIds = null, customInstructions = "", useImprovements = true) =>
  api.post("/api/drafts/generate", {
    draft_type: draftType,
    doc_ids: docIds,
    custom_instructions: customInstructions,
    use_improvements: useImprovements,
  });
export const getDraft = (draftId) => api.get(`/api/drafts/${draftId}`);

// ── Edits ──
export const submitEdit = (draftId, originalContent, editedContent, editorNotes = "") =>
  api.post("/api/edits/submit", {
    draft_id: draftId,
    original_content: originalContent,
    edited_content: editedContent,
    editor_notes: editorNotes,
  });
export const getEdits = () => api.get("/api/edits");

// ── Improvements ──
export const getImprovementDashboard = () => api.get("/api/improvements/dashboard");
export const deleteRule = (ruleId) => api.delete(`/api/improvements/rules/${ruleId}`);
export const resetRules = () => api.post("/api/improvements/reset");
```

---

## Global State (`src/context/AppContext.jsx`)

Use React Context + useReducer for shared state.

### State Shape

```javascript
const initialState = {
  documents: [],         // list of DocumentListItem
  currentDocument: null, // full ExtractedContent for selected doc
  currentDraft: null,    // DraftResponse being viewed/edited
  editHistory: [],       // list of EditAnalysis
  rules: [],             // list of ImprovementRule
  health: null,          // HealthResponse
  loading: {
    documents: false,
    draft: false,
    search: false,
    edit: false,
  },
};
```

### Actions

```javascript
const reducer = (state, action) => {
  switch (action.type) {
    case "SET_DOCUMENTS":
    case "SET_CURRENT_DOCUMENT":
    case "SET_CURRENT_DRAFT":
    case "SET_EDIT_HISTORY":
    case "SET_RULES":
    case "SET_HEALTH":
    case "SET_LOADING":       // payload: { key: "documents", value: true }
    case "ADD_DOCUMENT":      // append to documents list
    case "REMOVE_DOCUMENT":   // filter out by doc_id
    case "CLEAR_DRAFT":
    default: return state;
  }
};
```

### Provider

```jsx
export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  // Fetch documents + health on mount
  useEffect(() => {
    refreshDocuments();
    checkHealth();
  }, []);

  const refreshDocuments = async () => { /* getDocuments() → dispatch */ };
  const checkHealth = async () => { /* getHealth() → dispatch */ };

  return (
    <AppContext.Provider value={{ state, dispatch, refreshDocuments, checkHealth }}>
      {children}
    </AppContext.Provider>
  );
}
```

---

## Layout & Navigation

### `App.jsx`

```jsx
<AppProvider>
  <BrowserRouter>
    <Layout>
      <Routes>
        <Route path="/" element={<DocumentsPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/drafts" element={<DraftsPage />} />
        <Route path="/improvements" element={<ImprovementsPage />} />
      </Routes>
    </Layout>
  </BrowserRouter>
</AppProvider>
```

### `Layout.jsx`

```
┌──────────────────────────────────────────────┐
│  ┌──────────┐  ┌─────────────────────────┐   │
│  │ Sidebar  │  │                         │   │
│  │          │  │    Main Content          │   │
│  │ • Docs   │  │    (routed pages)       │   │
│  │ • Search │  │                         │   │
│  │ • Drafts │  │                         │   │
│  │ • Learn  │  │                         │   │
│  │          │  │                         │   │
│  │ ──────── │  │                         │   │
│  │ Status:  │  │                         │   │
│  │ 3 docs   │  │                         │   │
│  │ 5 rules  │  │                         │   │
│  └──────────┘  └─────────────────────────┘   │
└──────────────────────────────────────────────┘
```

- Sidebar is a fixed-width panel (w-64) with nav links + status summary
- Main content fills remaining space
- Use Tailwind's `flex` layout

### `Sidebar.jsx`

Shows:
1. App title/logo area
2. Navigation links with icons (FileText, Search, PenTool, TrendingUp)
3. Active link highlighting (based on `useLocation()`)
4. Status footer: doc count, index size, rules count (from health check)
5. A small indicator for Gemini API status (green dot = configured, red = missing)

---

## Page Implementations

### 1. Documents Page (`pages/DocumentsPage.jsx`)

**Layout:** Two-column. Left: upload + document list. Right: document detail (when selected).

**Components used:** DocumentUploader, DocumentList, DocumentDetail

**Flow:**
```
1. On mount: fetch documents list from API
2. Show DocumentUploader at top
3. Below: DocumentList showing all processed documents
4. When user clicks a document → fetch full details → show DocumentDetail
5. "Load Samples" button calls loadSamples() API
```

#### `DocumentUploader.jsx`

```
┌─────────────────────────────────────────┐
│                                         │
│     📄 Drop files here or click         │
│     Supports: PDF, PNG, JPG, TXT        │
│                                         │
│     [Browse Files]                      │
│                                         │
└─────────────────────────────────────────┘
```

Implementation details:
- Use `onDragOver`, `onDragLeave`, `onDrop` events on a div
- `onDrop`: extract `e.dataTransfer.files[0]`, call `uploadDocument(file)`
- Also have a hidden `<input type="file">` triggered by the browse button
- Show upload progress state: idle → uploading (spinner) → success (check) → error (message)
- On success: call `refreshDocuments()` and show toast
- Accept: `.pdf, .png, .jpg, .jpeg, .tiff, .bmp, .txt, .md`

#### `DocumentList.jsx`

Renders a list of document cards. Each card shows:

```
┌─────────────────────────────────────────┐
│ 📄 lease_agreement.pdf                  │
│ Type: pdf  │  Pages: 3  │  Words: 1,247│
│ Method: hybrid  │  Confidence: 0.91    │
│ Uploaded: 2024-01-15                    │
│ Chunks: 8                              │
│                          [View] [Delete]│
└─────────────────────────────────────────┘
```

- Confidence displayed as a colored badge:
  - ≥0.9 → green ("High")
  - ≥0.7 → yellow ("Medium")
  - <0.7 → red ("Low")
- Delete button calls `deleteDocument(docId)` with confirmation

#### `DocumentDetail.jsx`

When a document is selected, show its full extraction:

```
┌─────────────────────────────────────────┐
│ 📄 lease_agreement.pdf                  │
│                                         │
│ ┌─── Metadata ─────────────────────┐    │
│ │ Extraction: hybrid               │    │
│ │ Confidence: 0.91                 │    │
│ │ Pages: 3  │  Chars: 5,200       │    │
│ └──────────────────────────────────┘    │
│                                         │
│ ┌─── Structured Data ──────────────┐    │
│ │ Dates: Jan 15, 2024 ...         │    │
│ │ Parties: GREENFIELD v. DAVIDSON │    │
│ │ Amounts: $2,450, $4,900         │    │
│ └──────────────────────────────────┘    │
│                                         │
│ ┌─── Extracted Text ───────────────┐    │
│ │ [Page 1]                         │    │
│ │ RESIDENTIAL LEASE AGREEMENT      │    │
│ │ This lease agreement is entered  │    │
│ │ into as of January 15, 2024...   │    │
│ │                                  │    │
│ │ (scrollable, full text)          │    │
│ └──────────────────────────────────┘    │
│                                         │
│ ┌─── Chunks (8) ───────────────────┐    │
│ │ Chunk 0: "RESIDENTIAL LEASE..."  │    │
│ │ Chunk 1: "The Tenant shall..."   │    │
│ │ (collapsible list)               │    │
│ └──────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

- Tabs or accordion for: Metadata, Structured Data, Full Text, Chunks
- Full text in a scrollable `<pre>` or monospace block
- Chunks shown as a collapsible list (click to expand full text)

---

### 2. Search Page (`pages/SearchPage.jsx`)

**Purpose:** Let users query the retrieval system directly and inspect what evidence is available.

**Layout:** Search bar at top, results below.

#### `SearchPanel.jsx`

```
┌─────────────────────────────────────────┐
│ 🔍 Search documents                     │
│ ┌─────────────────────────────┐ [Search]│
│ │ What are the lease terms?   │         │
│ └─────────────────────────────┘         │
│                                         │
│ Filter by document: [All ▾] Top K: [5] │
│                                         │
│ ─── Results ────────────────────────── │
│                                         │
│ ┌ Result 1 ─ Score: 0.89 ─────────────┐│
│ │ 📄 lease_agreement.pdf               ││
│ │ "The monthly rent shall be $2,450,   ││
│ │ due on the first day of each month.  ││
│ │ Late payment fee of $50 applies..."  ││
│ └──────────────────────────────────────┘│
│                                         │
│ ┌ Result 2 ─ Score: 0.76 ─────────────┐│
│ │ 📄 lease_agreement.pdf               ││
│ │ "Lease term: 12 months beginning     ││
│ │ January 15, 2024..."                 ││
│ └──────────────────────────────────────┘│
│                                         │
│ (more results...)                       │
└─────────────────────────────────────────┘
```

Implementation:
- Text input + Search button
- Optional dropdown to filter by specific document(s) — populated from documents list
- Top K slider or number input (1-20, default 5)
- Results rendered as cards with:
  - Score as a colored bar or percentage
  - Source filename
  - Chunk text (truncated, expandable)
- Call `searchDocuments(query, topK, selectedDocIds)` on submit

---

### 3. Drafts Page (`pages/DraftsPage.jsx`) ⭐ Core Page

**Layout:** Three-stage flow: Configure → View Draft → Edit Draft

Uses a state machine approach:

```
stage: "configure" → "viewing" → "editing" → "submitted"
                        ↑                       │
                        └───────────────────────┘
                          (generate new draft)
```

#### Stage 1: Configure (`DraftGenerator.jsx`)

```
┌─────────────────────────────────────────┐
│ Generate a Draft                        │
│                                         │
│ Draft Type:                             │
│ ┌─────────────────────────────────────┐ │
│ │ ○ Case Fact Summary                 │ │
│ │ ○ Title Review Summary              │ │
│ │ ○ Notice Summary                    │ │
│ │ ○ Document Checklist                │ │
│ │ ● Internal Memo                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Source Documents:                        │
│ ☑ lease_agreement.pdf                   │
│ ☑ case_filing.txt                       │
│ ☐ handwritten_note.png                  │
│                                         │
│ Custom Instructions (optional):         │
│ ┌─────────────────────────────────────┐ │
│ │ Focus on termination clauses        │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ ☑ Apply learned improvements (3 rules) │
│                                         │
│ [Generate Draft]                        │
└─────────────────────────────────────────┘
```

- Radio buttons for draft type (map to DraftType enum values)
- Checkbox list of available documents (fetched from API)
- Textarea for custom instructions
- Checkbox for "Apply learned improvements" with count of applicable rules
- Generate button → calls `generateDraft()` → transitions to "viewing" stage
- Show loading spinner during generation (can take 10-30 seconds)

#### Stage 2: View Draft (`DraftViewer.jsx`)

```
┌─────────────────────────────────────────────────────┐
│ Internal Memo                    Generated just now  │
│ ─────────────────────────────────────────────────── │
│                                                      │
│ ┌─── Draft Content ────────┐ ┌─── Citations ──────┐ │
│ │                          │ │                     │ │
│ │ **TO:** Senior Partner   │ │ [1] lease_agreement │ │
│ │ **FROM:** Legal Analyst  │ │ Score: 0.89        │ │
│ │ **RE:** Lease Review     │ │ "The monthly rent  │ │
│ │                          │ │ shall be $2,450..." │ │
│ │ ## Summary               │ │                     │ │
│ │ The lease agreement      │ │ [2] case_filing.txt │ │
│ │ between Greenfield       │ │ Score: 0.76        │ │
│ │ Properties and Davidson  │ │ "Plaintiff alleges  │ │
│ │ establishes a 12-month   │ │ breach of..."      │ │
│ │ residential tenancy...   │ │                     │ │
│ │                          │ │ [3] ...             │ │
│ │ (rendered markdown)      │ │                     │ │
│ │                          │ │                     │ │
│ └──────────────────────────┘ └─────────────────────┘ │
│                                                      │
│ Rules Applied: "Use formal language", "Include dates"│
│                                                      │
│ [Edit This Draft]    [Generate New]                  │
└─────────────────────────────────────────────────────┘
```

Two-column layout:
- **Left (70%):** Rendered draft content using `react-markdown`
- **Right (30%):** Citation panel showing evidence sources

The citation panel (`CitationPanel.jsx`) shows each citation with:
- Source number [1], [2], etc.
- Filename
- Relevance score (color-coded)
- Text snippet (expandable)

Below the draft: list of improvement rules that were applied (if any).

Buttons: "Edit This Draft" → stage 3, "Generate New" → back to stage 1.

#### Stage 3: Edit Draft (`DraftEditor.jsx`)

```
┌─────────────────────────────────────────┐
│ Edit Draft                              │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │                                     │ │
│ │ (textarea with the draft content,   │ │
│ │  pre-filled with generated draft,   │ │
│ │  fully editable by the operator)    │ │
│ │                                     │ │
│ │                                     │ │
│ │                                     │ │
│ │                                     │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Editor Notes (optional):                │
│ ┌─────────────────────────────────────┐ │
│ │ Made it more formal, added dates    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ [Submit Edits]  [Cancel]                │
└─────────────────────────────────────────┘
```

- Large textarea (min-height: 400px) pre-filled with `currentDraft.content`
- Textarea for optional editor notes
- On submit:
  1. Call `submitEdit(draftId, originalContent, editedContent, notes)`
  2. Show the returned `EditAnalysis` in a diff view
  3. Toast: "Edits analyzed! N new rules learned."

#### After Submit: Diff View (`EditDiffView.jsx`)

```
┌─────────────────────────────────────────────────────┐
│ Edit Analysis                                        │
│                                                      │
│ Summary: 4 changes detected (2 tone, 1 structural,  │
│ 1 addition). Learned 2 new rules.                    │
│                                                      │
│ ┌─── Side-by-Side Diff ───────────────────────────┐ │
│ │ Original              │ Edited                   │ │
│ │ The lease terms...    │ The lease terms...       │ │
│ │ -may be terminated    │ +shall be terminated     │ │
│ │ -at any time          │ +with 30 days notice     │ │
│ │                       │ +as per Section 4.2      │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─── Classified Changes ──────────────────────────┐ │
│ │ 🏷️ TONE: Changed "may be" → "shall be"          │ │
│ │ 🏷️ ADDITION: Added "as per Section 4.2"         │ │
│ │ 🏷️ STRUCTURAL: Added section header             │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [Generate New Draft (with improvements)]             │
└─────────────────────────────────────────────────────┘
```

- Use `react-diff-viewer-continued` for side-by-side diff rendering
- Below the diff: list of classified changes with category badges
- Show the analysis summary
- CTA button to generate a new draft (which will now include the learned rules)

---

### 4. Improvements Page (`pages/ImprovementsPage.jsx`)

**Purpose:** Show the improvement loop working — rules learned, stats, edit history.

#### `ImprovementDashboard.jsx`

```
┌─────────────────────────────────────────────────────┐
│ Improvement Dashboard                                │
│                                                      │
│ ┌─── Stats ───────────────────────────────────────┐ │
│ │ Total Edits: 5  │  Active Rules: 8              │ │
│ │                                                  │ │
│ │ Rules by Category:                              │ │
│ │ ██████████ Tone (3)                             │ │
│ │ ████████   Structural (2)                       │ │
│ │ ██████     Addition (2)                         │ │
│ │ ████       Legal Precision (1)                  │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─── Active Rules ────────────────────────────────┐ │
│ │                                                  │ │
│ │ Rule #1 │ TONE │ Confidence: 0.8 │ Applied: 3x │ │
│ │ "Use formal legal language. Avoid casual          │ │
│ │ phrasing."                                       │ │
│ │ Example: "may be" → "shall be"                   │ │
│ │                                      [Delete]    │ │
│ │ ──────────────────────────────────────────────── │ │
│ │ Rule #2 │ ADDITION │ Confidence: 0.6 │ Applied: │ │
│ │ "Always include jurisdiction and venue info."     │ │
│ │                                      [Delete]    │ │
│ │ ──────────────────────────────────────────────── │ │
│ │ (more rules...)                                  │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ ┌─── Recent Edits ────────────────────────────────┐ │
│ │ Edit #1 │ case_summary │ 3 changes │ Jan 15     │ │
│ │ Edit #2 │ internal_memo │ 5 changes │ Jan 14    │ │
│ │ (expandable to show diffs)                       │ │
│ └──────────────────────────────────────────────────┘ │
│                                                      │
│ [Reset All Rules]                                    │
└─────────────────────────────────────────────────────┘
```

Implementation:
- Fetch from `getImprovementDashboard()` on mount
- Stats section: simple counters + horizontal bar chart for category distribution
- Rules list: each rule card shows category badge, confidence, times applied, rule text, one example
- Delete button per rule → `deleteRule(ruleId)` with confirmation
- Recent edits: collapsible list, expand to see summary and diffs
- Reset button → `resetRules()` with confirmation modal

---

## Component Design Notes

### Color Scheme (Tailwind)

Use a professional legal-office aesthetic:

```
Primary:    slate-800 / slate-700     (dark text, headers)
Secondary:  blue-600 / blue-500       (buttons, links, active states)
Background: gray-50 / white           (page bg / card bg)
Accent:     amber-500                 (warnings, medium confidence)
Success:    emerald-500               (high confidence, success states)
Error:      red-500                   (low confidence, errors)
Border:     gray-200                  (card borders, dividers)
```

### `StatusBadge.jsx`

Reusable badge component:

```jsx
// Usage: <StatusBadge type="confidence" value={0.91} />
//        <StatusBadge type="category" value="tone" />
//        <StatusBadge type="status" value="success" />

// type="confidence":
//   >= 0.9 → green bg, "High"
//   >= 0.7 → amber bg, "Medium"
//   < 0.7  → red bg, "Low"

// type="category" → colored pill with category name
//   structural → purple
//   tone → blue
//   factual_correction → red
//   addition → green
//   deletion → orange
//   formatting → gray
//   legal_precision → indigo
```

### Loading States

Every async operation should show:
1. **Button loading:** Replace text with spinner + "Generating..." / "Uploading..."
2. **Skeleton loaders** for document list and draft content
3. **Progress indication** for long operations (draft generation)

Use a consistent pattern:

```jsx
{loading ? (
  <div className="animate-pulse space-y-4">
    <div className="h-4 bg-gray-200 rounded w-3/4"></div>
    <div className="h-4 bg-gray-200 rounded w-1/2"></div>
  </div>
) : (
  <ActualContent />
)}
```

### Error Handling

Wrap API calls in try/catch:

```jsx
try {
  const { data } = await uploadDocument(file);
  toast.success(`Processed ${data.filename}: ${data.chunk_count} chunks`);
} catch (err) {
  const message = err.response?.data?.detail || "Upload failed";
  toast.error(message);
}
```

---

## Docker Setup

### `Dockerfile`

```dockerfile
FROM node:20-alpine AS build

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

### `nginx.conf`

```nginx
server {
    listen 3000;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_read_timeout 120s;
    }
}
```

### `vite.config.js`

```javascript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

### `package.json` (key dependencies)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.26.0",
    "axios": "^1.7.0",
    "react-markdown": "^9.0.0",
    "react-diff-viewer-continued": "^3.4.0",
    "react-hot-toast": "^2.4.0",
    "lucide-react": "^0.441.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "vite": "^5.4.0",
    "tailwindcss": "^3.4.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0"
  }
}
```

---

## Docker Compose (`docker-compose.yml` — root level)

```yaml
version: "3.9"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GEMINI_MODEL=gemini-2.0-flash
    volumes:
      - app_data:/app/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  app_data:
```

**Run:**
```bash
# Create .env with your Gemini API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Build and start
docker-compose up --build

# Access at http://localhost:3000
```

---

## User Workflow (End to End)

Here's how a reviewer would test the full system:

```
1. Open http://localhost:3000
2. Click "Load Sample Documents" → 5 mock legal docs get processed
   → See confidence scores, extraction methods, structured data
3. Go to Search → query "lease termination clause"
   → See relevant chunks ranked by similarity
4. Go to Drafts → select "Internal Memo", check all docs
   → Click Generate → wait 15-20 seconds
   → See generated memo with citations panel showing evidence
5. Click "Edit This Draft"
   → Make changes: formalize language, add dates, fix a fact
   → Add editor note: "More formal tone, include all deadlines"
   → Submit
6. See diff view showing classified changes
7. Go to Improvements → see learned rules
8. Go back to Drafts → generate same memo type again
   → Notice: "3 improvement rules applied"
   → Draft should reflect the operator's preferences
9. Compare the two drafts — improvement should be visible
```
