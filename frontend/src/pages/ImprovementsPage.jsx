import ImprovementDashboard from "../components/ImprovementDashboard";

export default function ImprovementsPage() {
  return (
    <div>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-slate-800">Improvements</h2>
        <p className="text-sm text-slate-500 mt-1">
          Track learned rules and editing patterns from your feedback
        </p>
      </div>
      <ImprovementDashboard />
    </div>
  );
}
