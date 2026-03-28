import { useState } from "react";
import DraftGenerator from "../components/DraftGenerator";
import DraftViewer from "../components/DraftViewer";
import DraftEditor from "../components/DraftEditor";
import EditDiffView from "../components/EditDiffView";
import { useApp } from "../context/AppContext";

export default function DraftsPage() {
  const { checkHealth } = useApp();
  // State machine: configure → viewing → editing → submitted
  const [stage, setStage] = useState("configure");
  const [draft, setDraft] = useState(null);
  const [editAnalysis, setEditAnalysis] = useState(null);
  const [originalContent, setOriginalContent] = useState("");
  const [editedContent, setEditedContent] = useState("");

  const handleGenerated = (draftData) => {
    setDraft(draftData);
    setEditAnalysis(null);
    setStage("viewing");
  };

  const handleEdit = () => {
    setStage("editing");
  };

  const handleEditSubmitted = (analysis, edited) => {
    setEditAnalysis(analysis);
    setOriginalContent(draft.content);
    setEditedContent(edited);
    setStage("submitted");
    checkHealth();
  };

  const handleNewDraft = () => {
    setDraft(null);
    setEditAnalysis(null);
    setStage("configure");
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Drafts</h2>
        <p className="text-sm text-slate-500 mt-1">
          Generate, review, and refine legal document drafts
        </p>
      </div>

      {stage === "configure" && (
        <div className="max-w-xl">
          <DraftGenerator onGenerated={handleGenerated} />
        </div>
      )}

      {stage === "viewing" && draft && (
        <DraftViewer
          draft={draft}
          onEdit={handleEdit}
          onNewDraft={handleNewDraft}
        />
      )}

      {stage === "editing" && draft && (
        <DraftEditor
          draft={draft}
          onSubmitted={handleEditSubmitted}
          onCancel={() => setStage("viewing")}
        />
      )}

      {stage === "submitted" && (
        <EditDiffView
          analysis={editAnalysis}
          originalContent={originalContent}
          editedContent={editedContent}
          onNewDraft={handleNewDraft}
        />
      )}
    </div>
  );
}
