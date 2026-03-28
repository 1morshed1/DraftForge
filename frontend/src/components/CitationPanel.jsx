import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import StatusBadge from "./StatusBadge";

export default function CitationPanel({ citations = [] }) {
  const [expanded, setExpanded] = useState(new Set());

  if (citations.length === 0) {
    return (
      <div className="text-sm text-slate-400 text-center py-4">No citations</div>
    );
  }

  const toggle = (idx) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  return (
    <div className="space-y-2">
      <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
        Citations ({citations.length})
      </h4>
      {citations.map((cit, idx) => (
        <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
          <button
            onClick={() => toggle(idx)}
            className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-gray-50"
          >
            {expanded.has(idx) ? (
              <ChevronDown size={14} className="text-slate-400" />
            ) : (
              <ChevronRight size={14} className="text-slate-400" />
            )}
            <span className="text-xs font-medium text-blue-600">[{idx + 1}]</span>
            <span className="text-xs text-slate-700 truncate flex-1">
              {cit.filename || cit.doc_id}
            </span>
            <StatusBadge type="confidence" value={cit.relevance_score} />
          </button>
          {expanded.has(idx) && (
            <div className="px-3 pb-3 text-xs text-slate-600 whitespace-pre-wrap font-mono bg-gray-50 border-t border-gray-100">
              {cit.text_snippet}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
