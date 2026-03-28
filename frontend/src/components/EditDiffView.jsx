import ReactDiffViewer from "react-diff-viewer-continued";
import StatusBadge from "./StatusBadge";

export default function EditDiffView({ analysis, originalContent, editedContent, onNewDraft }) {
  if (!analysis) return null;

  const diffs = analysis.diffs || [];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-800">Edit Analysis</h3>
        <button
          onClick={onNewDraft}
          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          Generate New Draft (with improvements)
        </button>
      </div>

      {analysis.summary && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-slate-700">
          {analysis.summary}
        </div>
      )}

      {originalContent && editedContent && (
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <ReactDiffViewer
            oldValue={originalContent}
            newValue={editedContent}
            splitView={true}
            leftTitle="Original"
            rightTitle="Edited"
            useDarkTheme={false}
            styles={{
              contentText: { fontSize: "12px", lineHeight: "1.5" },
            }}
          />
        </div>
      )}

      {diffs.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-3">
            Classified Changes ({diffs.length})
          </h4>
          <div className="space-y-2">
            {diffs.map((diff, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg text-sm"
              >
                <StatusBadge type="category" value={diff.edit_type} />
                <div className="flex-1 min-w-0">
                  {diff.explanation && (
                    <p className="text-slate-700">{diff.explanation}</p>
                  )}
                  {diff.original_segment && diff.edited_segment && (
                    <p className="text-xs text-slate-500 mt-1">
                      <span className="line-through text-red-500">
                        {diff.original_segment}
                      </span>
                      {" → "}
                      <span className="text-emerald-600">{diff.edited_segment}</span>
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
