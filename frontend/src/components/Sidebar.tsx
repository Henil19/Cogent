import React from "react";
import {
  Sparkles,
  Plus,
  Home,
  FolderOpen,
  History,
  BarChart3,
  Settings,
  Circle,
} from "lucide-react";
import type { ActiveView } from "../types/cogent";

interface SidebarProps {
  activeView: ActiveView;
  onSelectView: (view: ActiveView) => void;
  onNewResearch: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeView,
  onSelectView,
  onNewResearch,
}) => {
  const primaryMenuItems: { id: ActiveView; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: "COCKPIT", label: "Research Cockpit", icon: Home },
    { id: "DOCUMENTS", label: "Documents & Corpus", icon: FolderOpen },
    { id: "HISTORY", label: "Research History", icon: History },
  ];

  return (
    <aside className="w-64 shrink-0 bg-slate-950 border-r border-slate-800/60 flex flex-col justify-between select-none h-screen sticky top-0 z-30">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800/60 flex items-center space-x-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-indigo-400" />
          </div>
          <div>
            <span className="font-bold tracking-tight text-slate-100 text-sm block">COGENT</span>
            <p className="text-[10px] text-slate-400">Research Intelligence</p>
          </div>
        </div>

        {/* Primary Action: New Research */}
        <div className="p-3.5 pb-2">
          <button
            onClick={onNewResearch}
            className="w-full flex items-center justify-center space-x-2 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 border border-indigo-500/40 shadow-sm transition-all active:scale-[0.98]"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>+ New Research</span>
          </button>
        </div>

        {/* Primary Navigation Menu */}
        <nav className="p-2.5 space-y-1">
          {primaryMenuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectView(item.id)}
                className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                  isActive
                    ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 font-semibold"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? "text-indigo-400" : "text-slate-500"}`} />
                <span>{item.label}</span>
              </button>
            );
          })}

          {/* ADVANCED Section Divider */}
          <div className="pt-4 pb-1 px-3">
            <span className="text-[10px] font-semibold tracking-wider text-slate-300 uppercase">
              Advanced
            </span>
          </div>

          <button
            onClick={() => onSelectView("ANALYTICS")}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
              activeView === "ANALYTICS"
                ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
            }`}
          >
            <BarChart3 className={`w-4 h-4 ${activeView === "ANALYTICS" ? "text-indigo-400" : "text-slate-500"}`} />
            <span>Telemetry & Analytics</span>
          </button>

          <button
            onClick={() => onSelectView("SETTINGS")}
            className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
              activeView === "SETTINGS"
                ? "bg-indigo-600/15 text-indigo-300 border border-indigo-500/30 font-semibold"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent"
            }`}
          >
            <Settings className={`w-4 h-4 ${activeView === "SETTINGS" ? "text-indigo-400" : "text-slate-500"}`} />
            <span>Settings</span>
          </button>
        </nav>
      </div>

      {/* Bottom Footer & System Status Panel */}
      <div className="p-3.5 border-t border-slate-800/60 space-y-2.5">
        <div className="px-3 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800/60 space-y-1.5 text-[11px]">
          <div className="flex items-center justify-between text-slate-400">
            <span>AI Provider</span>
            <div className="flex items-center space-x-1 text-emerald-400">
              <Circle className="w-1.5 h-1.5 fill-current" />
              <span className="text-[10px]">Configured</span>
            </div>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Web Research</span>
            <div className="flex items-center space-x-1 text-emerald-400">
              <Circle className="w-1.5 h-1.5 fill-current" />
              <span className="text-[10px]">Configured</span>
            </div>
          </div>
          <div className="flex items-center justify-between text-slate-400">
            <span>Database</span>
            <div className="flex items-center space-x-1 text-emerald-400">
              <Circle className="w-1.5 h-1.5 fill-current" />
              <span className="text-[10px]">Connected</span>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};
