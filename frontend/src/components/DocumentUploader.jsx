import { useState, useRef } from "react";
import { Upload, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { uploadDocument } from "../api/client";
import { useApp } from "../context/AppContext";

const ACCEPT = ".pdf,.png,.jpg,.jpeg,.tiff,.bmp,.txt,.md";

export default function DocumentUploader() {
  const { refreshDocuments, checkHealth } = useApp();
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    setStatus("uploading");
    try {
      const { data } = await uploadDocument(file);
      toast.success(`Processed ${data.filename}: ${data.chunk_count} chunks`);
      setStatus("success");
      refreshDocuments();
      checkHealth();
      setTimeout(() => setStatus("idle"), 2000);
    } catch (err) {
      const message = err.response?.data?.detail || "Upload failed";
      toast.error(message);
      setStatus("error");
      setTimeout(() => setStatus("idle"), 3000);
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragOver(true);
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
        dragOver
          ? "border-blue-400 bg-blue-50"
          : status === "success"
          ? "border-emerald-300 bg-emerald-50"
          : status === "error"
          ? "border-red-300 bg-red-50"
          : "border-gray-300 hover:border-blue-300 hover:bg-gray-50"
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPT}
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />
      <div className="flex flex-col items-center gap-2">
        {status === "uploading" ? (
          <Loader2 size={32} className="text-blue-500 animate-spin" />
        ) : status === "success" ? (
          <CheckCircle size={32} className="text-emerald-500" />
        ) : status === "error" ? (
          <AlertCircle size={32} className="text-red-500" />
        ) : (
          <Upload size={32} className="text-gray-400" />
        )}
        <p className="text-sm font-medium text-slate-700">
          {status === "uploading"
            ? "Processing document..."
            : status === "success"
            ? "Upload complete!"
            : "Drop files here or click to browse"}
        </p>
        <p className="text-xs text-slate-400">
          Supports: PDF, PNG, JPG, TIFF, BMP, TXT, MD
        </p>
      </div>
    </div>
  );
}
