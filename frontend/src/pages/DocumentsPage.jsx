import { useState } from "react";
import { Loader2, Database } from "lucide-react";
import toast from "react-hot-toast";
import DocumentUploader from "../components/DocumentUploader";
import DocumentList from "../components/DocumentList";
import DocumentDetail from "../components/DocumentDetail";
import { loadSamples } from "../api/client";
import { useApp } from "../context/AppContext";

export default function DocumentsPage() {
  const { refreshDocuments, checkHealth } = useApp();
  const [selectedDocId, setSelectedDocId] = useState(null);
  const [loadingSamples, setLoadingSamples] = useState(false);

  const handleLoadSamples = async () => {
    setLoadingSamples(true);
    try {
      const { data } = await loadSamples();
      toast.success(`Loaded ${data.loaded_count ?? data.length ?? ""} sample documents`);
      refreshDocuments();
      checkHealth();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to load samples");
    } finally {
      setLoadingSamples(false);
    }
  };

  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Documents</h2>
        <p className="text-sm text-slate-500 mt-1">
          Upload and manage legal documents for processing
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <DocumentUploader />

          <button
            onClick={handleLoadSamples}
            disabled={loadingSamples}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50"
          >
            {loadingSamples ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Database size={16} />
            )}
            {loadingSamples ? "Loading..." : "Load Sample Documents"}
          </button>

          <DocumentList onSelect={setSelectedDocId} selectedId={selectedDocId} />
        </div>

        <div>
          <DocumentDetail docId={selectedDocId} />
        </div>
      </div>
    </div>
  );
}
