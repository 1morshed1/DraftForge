import { NavLink } from "react-router-dom";
import { FileText, Search, PenTool, TrendingUp } from "lucide-react";
import { useApp } from "../context/AppContext";

const navItems = [
  { to: "/", icon: FileText, label: "Documents" },
  { to: "/search", icon: Search, label: "Search" },
  { to: "/drafts", icon: PenTool, label: "Drafts" },
  { to: "/improvements", icon: TrendingUp, label: "Improvements" },
];

export default function Sidebar() {
  const { state } = useApp();
  const health = state.health;

  return (
    <aside className="w-64 bg-white border-r border-gray-200 flex flex-col min-h-screen">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-slate-800">DraftForge</h1>
        <p className="text-xs text-slate-500 mt-1">Legal Document Processor</p>
      </div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-slate-600 hover:bg-gray-50 hover:text-slate-800"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200 text-xs text-slate-500 space-y-1.5">
        {health ? (
          <>
            <div className="flex items-center gap-2">
              <span
                className={`w-2 h-2 rounded-full ${
                  health.gemini_configured ? "bg-emerald-500" : "bg-red-500"
                }`}
              />
              Gemini {health.gemini_configured ? "Connected" : "Not configured"}
            </div>
            <div>{health.documents_loaded} documents</div>
            <div>{health.index_size} indexed chunks</div>
            <div>{health.rules_count} improvement rules</div>
          </>
        ) : (
          <div className="text-red-500">Backend unreachable</div>
        )}
      </div>
    </aside>
  );
}
