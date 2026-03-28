export function formatDate(dateStr) {
  if (!dateStr) return "";
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatNumber(n) {
  if (n == null) return "0";
  return n.toLocaleString();
}

export function truncateText(text, maxLen = 200) {
  if (!text || text.length <= maxLen) return text || "";
  return text.slice(0, maxLen) + "...";
}

export function confidenceLabel(score) {
  if (score >= 0.9) return "High";
  if (score >= 0.7) return "Medium";
  return "Low";
}

export function confidenceColor(score) {
  if (score >= 0.9) return "bg-emerald-100 text-emerald-800";
  if (score >= 0.7) return "bg-amber-100 text-amber-800";
  return "bg-red-100 text-red-800";
}

export const DRAFT_TYPE_LABELS = {
  case_summary: "Case Fact Summary",
  title_review: "Title Review Summary",
  notice_summary: "Notice Summary",
  document_checklist: "Document Checklist",
  internal_memo: "Internal Memo",
};

export const CATEGORY_COLORS = {
  structural: "bg-purple-100 text-purple-800",
  tone: "bg-blue-100 text-blue-800",
  factual_correction: "bg-red-100 text-red-800",
  addition: "bg-emerald-100 text-emerald-800",
  deletion: "bg-orange-100 text-orange-800",
  formatting: "bg-gray-100 text-gray-800",
  legal_precision: "bg-indigo-100 text-indigo-800",
};
