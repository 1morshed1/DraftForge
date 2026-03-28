import { useState } from "react";
import { Loader2, Send } from "lucide-react";
import toast from "react-hot-toast";
import { submitEdit } from "../api/client";

export default function DraftEditor({ draft, onSubmitted, onCancel }) {
  const [editedContent, setEditedContent] = useState(draft.content);
  const [editorNotes, setEditorNotes] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (editedContent === draft.content) {
      toast.error("No changes to submit");
      return;
    }
    setLoading(true);
    try {
      const { data } = await submitEdit(
        draft.draft_id,
        draft.content,
        editedContent,
        editorNotes
      );
      const rulesLearned = data.diffs?.length || 0;
      toast.success(`Edits analyzed! ${rulesLearned} change(s) detected.`);
      onSubmitted(data, editedContent);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Submit failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-800">Edit Draft</h3>
        <div className="flex gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-white border border-gray-300 text-slate-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={16} />
            )}
            {loading ? "Submitting..." : "Submit Edits"}
          </button>
        </div>
      </div>

      <textarea
        value={editedContent}
        onChange={(e) => setEditedContent(e.target.value)}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm font-mono focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-y"
        style={{ minHeight: "400px" }}
      />

      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">
          Editor Notes (optional)
        </label>
        <textarea
          value={editorNotes}
          onChange={(e) => setEditorNotes(e.target.value)}
          rows={2}
          placeholder="e.g. Made it more formal, added dates..."
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
        />
      </div>
    </div>
  );
}
