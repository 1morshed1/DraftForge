import ReactMarkdown from "react-markdown";
import CitationPanel from "./CitationPanel";
import { DRAFT_TYPE_LABELS, formatDate } from "../utils/helpers";

export default function DraftViewer({ draft, onEdit, onNewDraft }) {
  if (!draft) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">
            {DRAFT_TYPE_LABELS[draft.draft_type] || draft.draft_type}
          </h3>
          {draft.generated_at && (
            <p className="text-xs text-slate-400 mt-0.5">
              Generated {formatDate(draft.generated_at)}
            </p>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={onEdit}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            Edit This Draft
          </button>
          <button
            onClick={onNewDraft}
            className="px-4 py-2 bg-white border border-gray-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
          >
            Generate New
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-6 prose prose-sm prose-slate max-w-none">
          <ReactMarkdown>{draft.content}</ReactMarkdown>
        </div>

        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <CitationPanel citations={draft.citations} />
        </div>
      </div>

      {draft.improvement_rules_applied?.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <h4 className="text-xs font-semibold text-blue-700 uppercase tracking-wide mb-2">
            Rules Applied
          </h4>
          <ul className="list-disc list-inside text-sm text-blue-800 space-y-1">
            {draft.improvement_rules_applied.map((rule, i) => (
              <li key={i}>{rule}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
