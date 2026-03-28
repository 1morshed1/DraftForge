import SearchPanel from "../components/SearchPanel";

export default function SearchPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Search</h2>
        <p className="text-sm text-slate-500 mt-1">
          Query your document knowledge base with semantic search
        </p>
      </div>
      <SearchPanel />
    </div>
  );
}
