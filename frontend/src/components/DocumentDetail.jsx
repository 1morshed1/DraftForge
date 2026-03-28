import { useState, useEffect } from "react";
import { Loader2, ChevronDown, ChevronRight } from "lucide-react";
import StatusBadge from "./StatusBadge";
import { getDocument } from "../api/client";
import { formatDate, formatNumber } from "../utils/helpers";

export default function DocumentDetail({ docId }) {
  const [doc, setDoc] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("metadata");
  const [expandedChunks, setExpandedChunks] = useState(new Set());

  useEffect(() => {
    if (!docId) return;
    setLoading(true);
    getDocument(docId)
      .then(({ data }) => setDoc(data))
      .catch(() => setDoc(null))
      .finally(() => setLoading(false));
  }, [docId]);

  if (!docId) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400 text-sm">
        Select a document to view details
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-blue-500" size={24} />
      </div>
    );
  }

  if (!doc) return null;

  const meta = doc.metadata || {};
  const structured = doc.structured_data || {};
  const chunks = doc.chunks || [];
  const tabs = ["metadata", "structured", "text", "chunks"];

  const toggleChunk = (idx) => {
    setExpandedChunks((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-200">
        <h3 className="font-semibold text-slate-800">{meta.filename}</h3>
      </div>

      <div className="flex border-b border-gray-200">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2.5 text-xs font-medium capitalize transition-colors ${
              activeTab === tab
                ? "text-blue-700 border-b-2 border-blue-700"
                : "text-slate-500 hover:text-slate-700"
            }`}
          >
            {tab === "chunks" ? `Chunks (${chunks.length})` : tab}
          </button>
        ))}
      </div>

      <div className="p-4 max-h-[500px] overflow-auto">
        {activeTab === "metadata" && (
          <dl className="grid grid-cols-2 gap-3 text-sm">
            <dt className="text-slate-500">Extraction</dt>
            <dd className="text-slate-800">{meta.extraction_method}</dd>
            <dt className="text-slate-500">Confidence</dt>
            <dd><StatusBadge type="confidence" value={meta.confidence_score} /></dd>
            <dt className="text-slate-500">Pages</dt>
            <dd className="text-slate-800">{meta.page_count}</dd>
            <dt className="text-slate-500">Characters</dt>
            <dd className="text-slate-800">{formatNumber(meta.char_count)}</dd>
            <dt className="text-slate-500">Words</dt>
            <dd className="text-slate-800">{formatNumber(meta.word_count)}</dd>
            <dt className="text-slate-500">Uploaded</dt>
            <dd className="text-slate-800">{formatDate(meta.uploaded_at)}</dd>
          </dl>
        )}

        {activeTab === "structured" && (
          <div className="space-y-3 text-sm">
            {Object.keys(structured).length === 0 ? (
              <p className="text-slate-400">No structured data extracted</p>
            ) : (
              Object.entries(structured).map(([key, val]) => (
                <div key={key}>
                  <dt className="font-medium text-slate-600 capitalize mb-1">
                    {key.replace(/_/g, " ")}
                  </dt>
                  <dd className="text-slate-800 bg-gray-50 rounded p-2 text-xs">
                    {Array.isArray(val) ? val.join(", ") : String(val)}
                  </dd>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "text" && (
          <pre className="text-xs text-slate-700 whitespace-pre-wrap font-mono leading-relaxed">
            {doc.cleaned_text || doc.raw_text}
          </pre>
        )}

        {activeTab === "chunks" && (
          <div className="space-y-1">
            {chunks.map((chunk, idx) => (
              <div key={chunk.chunk_id} className="border border-gray-100 rounded">
                <button
                  onClick={() => toggleChunk(idx)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-xs text-slate-600 hover:bg-gray-50"
                >
                  {expandedChunks.has(idx) ? (
                    <ChevronDown size={14} />
                  ) : (
                    <ChevronRight size={14} />
                  )}
                  <span className="font-medium">Chunk {chunk.chunk_index}</span>
                  {chunk.page_number != null && (
                    <span className="text-slate-400">Page {chunk.page_number}</span>
                  )}
                </button>
                {expandedChunks.has(idx) && (
                  <div className="px-3 pb-3 text-xs text-slate-700 whitespace-pre-wrap font-mono">
                    {chunk.text}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
