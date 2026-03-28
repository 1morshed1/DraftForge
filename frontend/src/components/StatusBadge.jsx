import { confidenceLabel, confidenceColor, CATEGORY_COLORS } from "../utils/helpers";

export default function StatusBadge({ type, value }) {
  let classes = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
  let label = "";

  if (type === "confidence") {
    classes += ` ${confidenceColor(value)}`;
    label = `${confidenceLabel(value)} (${(value * 100).toFixed(0)}%)`;
  } else if (type === "category") {
    const color = CATEGORY_COLORS[value] || "bg-gray-100 text-gray-800";
    classes += ` ${color}`;
    label = value?.replace(/_/g, " ") || "";
  } else if (type === "status") {
    const statusStyles = {
      success: "bg-emerald-100 text-emerald-800",
      warning: "bg-amber-100 text-amber-800",
      error: "bg-red-100 text-red-800",
      info: "bg-blue-100 text-blue-800",
    };
    classes += ` ${statusStyles[value] || statusStyles.info}`;
    label = value;
  }

  return <span className={classes}>{label}</span>;
}
