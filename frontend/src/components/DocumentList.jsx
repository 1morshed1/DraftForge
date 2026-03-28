import { FileText, Trash2 } from "lucide-react";
import toast from "react-hot-toast";
import StatusBadge from "./StatusBadge";
import { deleteDocument } from "../api/client";
import { useApp } from "../context/AppContext";
import { formatDate, formatNumber } from "../utils/helpers";

export default function DocumentList({ onSelect, selectedId }) {
  const { state, refreshDocuments, checkHealth } = useApp();
  const { documents, loading } = state;

  const handleDelete = async (e, docId) => {
    e.stopPropagation();
    if (!confirm("Delete this document?")) return;
    try {
      await deleteDocument(docId);
      toast.success("Document deleted");
      refreshDocuments();
      checkHealth();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Delete failed");
    }
  };

  if (loading.documents) {
    return (
      <div className="space-y-3">
        {[1, 2, 3].map((i) => (
          <div key={i} className="animate-pulse bg-white rounded-lg border p-4">
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2" />
            <div className="h-3 bg-gray-200 rounded w-1/2" />
          </div>
        ))}
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-8 text-slate-400 text-sm">
        No documents yet. Upload a file or load samples.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {documents.map((doc) => (
        <div
          key={doc.doc_id}
          onClick={() => onSelect(doc.doc_id)}
          className={`bg-white rounded-lg border p-4 cursor-pointer transition-colors hover:border-blue-300 ${
            selectedId === doc.doc_id ? "border-blue-500 ring-1 ring-blue-200" : "border-gray-200"
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <FileText size={16} className="text-slate-400 flex-shrink-0" />
              <span className="font-medium text-sm text-slate-800 truncate">
                {doc.filename}
              </span>
            </div>
            <button
              onClick={(e) => handleDelete(e, doc.doc_id)}
              className="text-slate-300 hover:text-red-500 transition-colors flex-shrink-0"
            >
              <Trash2 size={14} />
            </button>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
            <span className="uppercase">{doc.file_type}</span>
            <span>&middot;</span>
            <span>{formatNumber(doc.word_count)} words</span>
            <span>&middot;</span>
            <span>{doc.chunk_count} chunks</span>
            <StatusBadge type="confidence" value={doc.confidence_score} />
          </div>
          <div className="mt-1 text-xs text-slate-400">{formatDate(doc.uploaded_at)}</div>
        </div>
      ))}
    </div>
  );
}
