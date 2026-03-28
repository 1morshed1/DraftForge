import { useState, useEffect } from "react";
import { Loader2, Trash2, RotateCcw, ChevronDown, ChevronRight } from "lucide-react";
import toast from "react-hot-toast";
import StatusBadge from "./StatusBadge";
import { getImprovementDashboard, deleteRule, resetRules, getEdits } from "../api/client";
import { useApp } from "../context/AppContext";
import { CATEGORY_COLORS, DRAFT_TYPE_LABELS, formatDate } from "../utils/helpers";

export default function ImprovementDashboard() {
  const { checkHealth } = useApp();
  const [dashboard, setDashboard] = useState(null);
  const [edits, setEdits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedEdits, setExpandedEdits] = useState(new Set());

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dashRes, editsRes] = await Promise.all([
        getImprovementDashboard(),
        getEdits(),
      ]);
      setDashboard(dashRes.data);
      setEdits(editsRes.data);
    } catch {
      // silently fail
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleDeleteRule = async (ruleId) => {
    if (!confirm("Delete this rule?")) return;
    try {
      await deleteRule(ruleId);
      toast.success("Rule deleted");
      fetchData();
      checkHealth();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Delete failed");
    }
  };

  const handleReset = async () => {
    if (!confirm("Reset ALL improvement rules? This cannot be undone.")) return;
    try {
      await resetRules();
      toast.success("All rules reset");
      fetchData();
      checkHealth();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Reset failed");
    }
  };

  const toggleEdit = (idx) => {
    setExpandedEdits((prev) => {
      const next = new Set(prev);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Loader2 className="animate-spin text-blue-500" size={24} />
      </div>
    );
  }

  if (!dashboard) {
    return (
      <div className="text-center py-8 text-slate-400 text-sm">
        Failed to load dashboard data.
      </div>
    );
  }

  const categories = dashboard.rules_by_category || {};
  const rules = dashboard.rules || [];
  const maxCategoryCount = Math.max(...Object.values(categories), 1);

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <div className="text-2xl font-bold text-slate-800">{dashboard.total_edits}</div>
          <div className="text-sm text-slate-500">Total Edits</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <div className="text-2xl font-bold text-slate-800">{dashboard.total_rules}</div>
          <div className="text-sm text-slate-500">Active Rules</div>
        </div>
      </div>

      {/* Category breakdown */}
      {Object.keys(categories).length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-5">
          <h4 className="text-sm font-semibold text-slate-700 mb-3">Rules by Category</h4>
          <div className="space-y-2">
            {Object.entries(categories).map(([cat, count]) => (
              <div key={cat} className="flex items-center gap-3">
                <div className="w-32">
                  <StatusBadge type="category" value={cat} />
                </div>
                <div className="flex-1 h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${
                      CATEGORY_COLORS[cat]?.split(" ")[0] || "bg-gray-400"
                    }`}
                    style={{ width: `${(count / maxCategoryCount) * 100}%` }}
                  />
                </div>
                <span className="text-sm text-slate-600 w-8 text-right">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rules list */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <h4 className="text-sm font-semibold text-slate-700">Active Rules</h4>
          {rules.length > 0 && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors"
            >
              <RotateCcw size={12} />
              Reset All
            </button>
          )}
        </div>

        {rules.length === 0 ? (
          <p className="text-sm text-slate-400 py-4 text-center">
            No improvement rules yet. Edit a draft to start learning.
          </p>
        ) : (
          <div className="space-y-3">
            {rules.map((rule) => (
              <div
                key={rule.rule_id}
                className="border border-gray-100 rounded-lg p-4"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 flex-wrap">
                    <StatusBadge type="category" value={rule.category} />
                    <StatusBadge type="confidence" value={rule.confidence} />
                    {rule.times_applied > 0 && (
                      <span className="text-xs text-slate-400">
                        Applied {rule.times_applied}x
                      </span>
                    )}
                  </div>
                  <button
                    onClick={() => handleDeleteRule(rule.rule_id)}
                    className="text-slate-300 hover:text-red-500 transition-colors flex-shrink-0"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
                <p className="text-sm text-slate-700 mt-2">{rule.rule_text}</p>
                {rule.examples?.length > 0 && rule.examples[0]?.original && (
                  <p className="text-xs text-slate-500 mt-1">
                    <span className="line-through">{rule.examples[0].original}</span>
                    {" → "}
                    <span className="text-emerald-600">{rule.examples[0].edited}</span>
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent edits */}
      <div className="bg-white border border-gray-200 rounded-lg p-5">
        <h4 className="text-sm font-semibold text-slate-700 mb-4">Recent Edits</h4>
        {edits.length === 0 ? (
          <p className="text-sm text-slate-400 py-4 text-center">No edits yet.</p>
        ) : (
          <div className="space-y-2">
            {edits.map((edit, idx) => (
              <div key={edit.edit_id} className="border border-gray-100 rounded-lg">
                <button
                  onClick={() => toggleEdit(idx)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50"
                >
                  {expandedEdits.has(idx) ? (
                    <ChevronDown size={14} className="text-slate-400" />
                  ) : (
                    <ChevronRight size={14} className="text-slate-400" />
                  )}
                  <span className="text-sm text-slate-700 flex-1">
                    {edit.draft_type
                      ? DRAFT_TYPE_LABELS[edit.draft_type] || edit.draft_type
                      : "Draft edit"}
                  </span>
                  <span className="text-xs text-slate-400">
                    {edit.diffs?.length || 0} changes
                  </span>
                  {edit.analyzed_at && (
                    <span className="text-xs text-slate-400">
                      {formatDate(edit.analyzed_at)}
                    </span>
                  )}
                </button>
                {expandedEdits.has(idx) && (
                  <div className="px-4 pb-3 text-sm text-slate-600 border-t border-gray-100 pt-3">
                    {edit.summary || "No summary available"}
                    {edit.diffs?.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {edit.diffs.map((diff, di) => (
                          <div key={di} className="flex items-center gap-2 text-xs">
                            <StatusBadge type="category" value={diff.edit_type} />
                            <span>{diff.explanation || `${diff.original_segment} → ${diff.edited_segment}`}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
