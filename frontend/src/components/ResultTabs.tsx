import React from "react";
import {
  FileText,
  Scale,
  GitBranch,
  ShieldCheck,
  Link2,
  Activity,
} from "lucide-react";

export type ResultTabType =
  | "ANSWER"
  | "EVIDENCE"
  | "REASONING"
  | "TRUST"
  | "PROVENANCE"
  | "TRACE";

interface ResultTabsProps {
  activeTab: ResultTabType;
  onSelectTab: (tab: ResultTabType) => void;
  counts?: {
    evidenceCount?: number;
    reasoningStepCount?: number;
    trustScore?: number;
    cutSetCount?: number;
    latencyMs?: number;
  };
}

export const ResultTabs: React.FC<ResultTabsProps> = ({
  activeTab,
  onSelectTab,
  counts,
}) => {
  const getRobustnessLabel = (cutCount?: number) => {
    if (cutCount === undefined) return "Robust";
    if (cutCount === 0) return "High Robustness";
    if (cutCount <= 3) return "Moderate";
    return "Multi-Dependent";
  };

  const tabs: {
    id: ResultTabType;
    label: string;
    icon: React.FC<{ className?: string }>;
    badge?: string | number;
    badgeColor?: string;
  }[] = [
    {
      id: "ANSWER",
      label: "Main Answer",
      icon: FileText,
    },
    {
      id: "EVIDENCE",
      label: "Evidence Intelligence",
      icon: Scale,
      badge: counts?.evidenceCount,
      badgeColor: "bg-indigo-500/20 text-indigo-300",
    },
    {
      id: "REASONING",
      label: "Reasoning DAG",
      icon: GitBranch,
      badge: counts?.reasoningStepCount ? `${counts.reasoningStepCount} steps` : undefined,
      badgeColor: "bg-slate-800 text-slate-300",
    },
    {
      id: "TRUST",
      label: "Confidence & Trust",
      icon: ShieldCheck,
      badge: counts?.trustScore !== undefined ? `${Math.round(counts.trustScore * 100)}%` : undefined,
      badgeColor: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
    },
    {
      id: "PROVENANCE",
      label: "Sources & Cut-Sets",
      icon: Link2,
      badge: getRobustnessLabel(counts?.cutSetCount),
      badgeColor: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
    },
    {
      id: "TRACE",
      label: "Execution Trace",
      icon: Activity,
      badge: counts?.latencyMs ? `${Math.round(counts.latencyMs)}ms` : undefined,
      badgeColor: "bg-purple-500/15 text-purple-300 border border-purple-500/30",
    },
  ];

  return (
    <div className="flex items-center space-x-1 sm:space-x-2 border-b border-slate-800/60 pb-3 mb-6 overflow-x-auto no-scrollbar">
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onSelectTab(tab.id)}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
              isActive
                ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/40 shadow-sm"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 border border-transparent"
            }`}
          >
            <Icon className={`w-3.5 h-3.5 ${isActive ? "text-indigo-400" : "text-slate-400"}`} />
            <span>{tab.label}</span>
            {tab.badge !== undefined && (
              <span
                className={`ml-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                  tab.badgeColor || "bg-slate-800 text-slate-300"
                }`}
              >
                {tab.badge}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
};
