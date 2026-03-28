import { useState } from "react";
import { Search, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import { searchDocuments } from "../api/client";
import { useApp } from "../context/AppContext";
import StatusBadge from "./StatusBadge";
import { truncateText } from "../utils/helpers";

export default function SearchPanel() {
  const { state } = useApp();
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5);
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [expandedResults, setExpandedResults] = useState(new Set());

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setResults(null);
    try {
      const docIds = selectedDocIds.length > 0 ? selectedDocIds : null;
      const { data } = await searchDocuments(query, topK, docIds);
      setResults(data);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const toggleDoc = (docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const toggleExpand = (idx) => {
    setExpandedResults((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  const scoreColor = (score) => {
    if (score >= 0.8) return "bg-emerald-500";
    if (score >= 0.5) return "bg-amber-500";
    return "bg-red-500";
  };

  return (
    <div className="space-y-6">
      <form onSubmit={handleSearch} className="space-y-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search documents..."
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            Search
          </button>
        </div>

        <div className="flex flex-wrap items-center gap-4 text-sm">
          <div className="flex items-center gap-2">
            <label className="text-slate-500">Top K:</label>
            <input
              type="number"
              min={1}
              max={20}
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-16 px-2 py-1 border border-gray-300 rounded text-sm text-center"
            />
          </div>

          {state.documents.length > 0 && (
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-slate-500">Filter:</span>
              {state.documents.map((doc) => (
                <label
                  key={doc.doc_id}
                  className={`flex items-center gap-1.5 px-2 py-1 rounded text-xs cursor-pointer border transition-colors ${
                    selectedDocIds.includes(doc.doc_id)
                      ? "bg-blue-50 border-blue-300 text-blue-700"
                      : "bg-white border-gray-200 text-slate-600 hover:border-gray-300"
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedDocIds.includes(doc.doc_id)}
                    onChange={() => toggleDoc(doc.doc_id)}
                    className="sr-only"
                  />
                  {doc.filename}
                </label>
              ))}
            </div>
          )}
        </div>
      </form>

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin text-blue-500" size={24} />
        </div>
      )}

      {results && !loading && (
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-slate-600">
            {results.length} result{results.length !== 1 ? "s" : ""}
          </h3>
          {results.length === 0 && (
            <p className="text-sm text-slate-400 py-4">No results found. Try a different query.</p>
          )}
          {results.map((result, idx) => (
            <div
              key={idx}
              className="bg-white border border-gray-200 rounded-lg overflow-hidden"
            >
              <div
                onClick={() => toggleExpand(idx)}
                className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50"
              >
                {expandedResults.has(idx) ? (
                  <ChevronDown size={14} className="text-slate-400" />
                ) : (
                  <ChevronRight size={14} className="text-slate-400" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-slate-700">
                      {result.filename || result.doc_id}
                    </span>
                    {result.page_number != null && (
                      <span className="text-xs text-slate-400">p.{result.page_number}</span>
                    )}
                  </div>
                  {!expandedResults.has(idx) && (
                    <p className="text-xs text-slate-500 mt-0.5 truncate">
                      {truncateText(result.text, 120)}
                    </p>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${scoreColor(result.score)}`}
                      style={{ width: `${Math.min(result.score * 100, 100)}%` }}
                    />
                  </div>
                  <span className="text-xs font-mono text-slate-500 w-10 text-right">
                    {(result.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              {expandedResults.has(idx) && (
                <div className="px-4 pb-4 text-xs text-slate-700 whitespace-pre-wrap font-mono bg-gray-50 border-t border-gray-100">
                  {result.text}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
