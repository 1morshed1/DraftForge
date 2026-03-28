import axios from "axios";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000,
});

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
export const generateDraft = (
  draftType,
  docIds = null,
  customInstructions = "",
  useImprovements = true
) =>
  api.post("/api/drafts/generate", {
    draft_type: draftType,
    doc_ids: docIds,
    custom_instructions: customInstructions,
    use_improvements: useImprovements,
  });
export const getDraft = (draftId) => api.get(`/api/drafts/${draftId}`);

// ── Edits ──
export const submitEdit = (
  draftId,
  originalContent,
  editedContent,
  editorNotes = ""
) =>
  api.post("/api/edits/submit", {
    draft_id: draftId,
    original_content: originalContent,
    edited_content: editedContent,
    editor_notes: editorNotes,
  });
export const getEdits = () => api.get("/api/edits");

// ── Improvements ──
export const getImprovementDashboard = () =>
  api.get("/api/improvements/dashboard");
export const deleteRule = (ruleId) =>
  api.delete(`/api/improvements/rules/${ruleId}`);
export const resetRules = () => api.post("/api/improvements/reset");
