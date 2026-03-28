import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import toast from "react-hot-toast";
import { generateDraft } from "../api/client";
import { useApp } from "../context/AppContext";
import { DRAFT_TYPE_LABELS } from "../utils/helpers";

const DRAFT_TYPES = Object.entries(DRAFT_TYPE_LABELS);

export default function DraftGenerator({ onGenerated }) {
  const { state } = useApp();
  const [draftType, setDraftType] = useState("internal_memo");
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [customInstructions, setCustomInstructions] = useState("");
  const [useImprovements, setUseImprovements] = useState(true);
  const [loading, setLoading] = useState(false);

  const toggleDoc = (docId) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleGenerate = async () => {
    setLoading(true);
    try {
      const docIds = selectedDocIds.length > 0 ? selectedDocIds : null;
      const { data } = await generateDraft(
        draftType,
        docIds,
        customInstructions,
        useImprovements
      );
      onGenerated(data);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Draft generation failed");
    } finally {
      setLoading(false);
    }
  };

  const rulesCount = state.health?.rules_count || 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6 space-y-6">
      <h3 className="text-lg font-semibold text-slate-800">Generate a Draft</h3>

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Draft Type
        </label>
        <div className="space-y-2">
          {DRAFT_TYPES.map(([value, label]) => (
            <label
              key={value}
              className={`flex items-center gap-3 px-4 py-2.5 rounded-lg border cursor-pointer transition-colors ${
                draftType === value
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 hover:border-gray-300"
              }`}
            >
              <input
                type="radio"
                name="draftType"
                value={value}
                checked={draftType === value}
                onChange={(e) => setDraftType(e.target.value)}
                className="text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm text-slate-700">{label}</span>
            </label>
          ))}
        </div>
      </div>

      {state.documents.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-2">
            Source Documents
          </label>
          <div className="space-y-1.5">
            {state.documents.map((doc) => (
              <label
                key={doc.doc_id}
                className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selectedDocIds.includes(doc.doc_id)}
                  onChange={() => toggleDoc(doc.doc_id)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                {doc.filename}
              </label>
            ))}
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Custom Instructions (optional)
        </label>
        <textarea
          value={customInstructions}
          onChange={(e) => setCustomInstructions(e.target.value)}
          rows={3}
          placeholder="e.g. Focus on termination clauses..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
        <input
          type="checkbox"
          checked={useImprovements}
          onChange={(e) => setUseImprovements(e.target.checked)}
          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        Apply learned improvements
        {rulesCount > 0 && (
          <span className="text-xs text-slate-400">({rulesCount} rules)</span>
        )}
      </label>

      <button
        onClick={handleGenerate}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 transition-colors"
      >
        {loading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Sparkles size={18} />
            Generate Draft
          </>
        )}
      </button>

      {loading && (
        <p className="text-xs text-slate-400 text-center">
          This may take 10-30 seconds depending on document size...
        </p>
      )}
    </div>
  );
}
