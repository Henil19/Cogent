import React from "react";
import { Users, Activity, SlidersHorizontal } from "lucide-react";
import type { AudienceFidelity } from "../types/cogent";

interface NavbarProps {
  currentSessionTitle: string;
  audience: AudienceFidelity;
  onChangeAudience: (aud: AudienceFidelity) => void;
  isProcessing: boolean;
  statusText?: string;
  onOpenSettings?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentSessionTitle,
  audience,
  onChangeAudience,
  isProcessing,
  statusText,
  onOpenSettings,
}) => {
  return (
    <header className="sticky top-0 z-20 w-full border-b border-slate-800/80 bg-slate-950/85 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-14 flex items-center justify-between">
        {/* Active Session Breadcrumb */}
        <div className="flex items-center space-x-2 truncate">
          <span className="text-xs text-slate-400 font-medium">Session:</span>
          <span className="text-xs font-semibold text-slate-200 truncate max-w-[220px] sm:max-w-sm">
            {currentSessionTitle || "Default Research Session"}
          </span>
        </div>

        {/* Center/Right Controls */}
        <div className="flex items-center space-x-4">
          {/* Audience / Fidelity Mode Selector */}
          <div className="flex items-center space-x-1.5 bg-slate-900/80 border border-slate-800 rounded-lg p-1">
            <Users className="w-3.5 h-3.5 text-indigo-400 ml-1.5" />
            <span className="text-[11px] text-slate-400 hidden sm:inline">Audience:</span>
            <select
              value={audience}
              onChange={(e) => onChangeAudience(e.target.value as AudienceFidelity)}
              className="bg-transparent text-xs font-semibold text-indigo-300 focus:outline-none cursor-pointer pr-2"
              title="Change audience presentation fidelity without mutating underlying facts or evidence"
            >
              <option value="EXECUTIVE" className="bg-slate-900 text-slate-200">
                Executive (BLUF)
              </option>
              <option value="TECHNICAL" className="bg-slate-900 text-slate-200">
                Technical Researcher
              </option>
              <option value="EXPERT" className="bg-slate-900 text-slate-200">
                Domain Expert (DAG)
              </option>
              <option value="LAYPERSON" className="bg-slate-900 text-slate-200">
                Layperson
              </option>
            </select>
          </div>

          {/* Processing Indicator */}
          {isProcessing && (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs font-medium animate-pulse">
              <Activity className="w-3 h-3 animate-spin" />
              <span>{statusText || "Synthesizing..."}</span>
            </div>
          )}

          {onOpenSettings && (
            <button
              onClick={onOpenSettings}
              className="p-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
              title="System Settings"
            >
              <SlidersHorizontal className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
