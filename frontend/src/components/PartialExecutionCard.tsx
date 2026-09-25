import React from "react";
import { AlertTriangle, CheckCircle2, XCircle, ArrowDown } from "lucide-react";
import type { PartialExecutionData } from "../types/cogent";

interface PartialExecutionCardProps {
  data?: PartialExecutionData;
}

export const PartialExecutionCard: React.FC<PartialExecutionCardProps> = ({ data }) => {
  const fallbackData: PartialExecutionData = data || {
    completed_layers: [
      { id: 1, name: "L1: Ambiguity Clarification" },
      { id: 2, name: "L2: Cognitive Planning" },
      { id: 3, name: "L3: Knowledge Acquisition" },
      { id: 4, name: "L4: Hybrid Retrieval" },
      { id: 5, name: "L5: Dialectical Evidence Intelligence" },
    ],
    failed_layer: {
      id: 6,
      name: "L6: Entailment Reasoning DAG",
      reason: "Reasoning graph synthesis timed out or encountered unresolvable premise cyclicity.",
    },
    available_findings_summary:
      "All upstream evidence, documents, and dialectical contradictions were successfully acquired and verified. The reasoning synthesis layer was interrupted, but empirical artifacts remain available for inspection below.",
  };

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-7 border border-amber-500/50 bg-amber-950/15 mb-8 shadow-2xl space-y-5">
      {/* Header Badge */}
      <div className="flex items-center justify-between pb-3 border-b border-amber-500/30">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
            <AlertTriangle className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold font-mono uppercase bg-amber-500/20 text-amber-300 border border-amber-500/40">
                PARTIAL_EXECUTION
              </span>
              <span className="text-xs text-slate-400">Graceful Layer Degradation</span>
            </div>
            <h3 className="text-sm sm:text-base font-bold text-slate-100 mt-0.5">
              Pipeline Partially Executed — Prior Layer Findings Preserved
            </h3>
          </div>
        </div>
      </div>

      {/* Two Column Grid: Completed Layers vs Unavailable Layer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Completed Layers */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
            <span>Completed Layers ({fallbackData.completed_layers.length})</span>
          </div>
          <div className="space-y-1.5">
            {fallbackData.completed_layers.map((layer) => (
              <div
                key={layer.id}
                className="flex items-center space-x-2 text-xs text-slate-300 bg-slate-950/60 p-2 rounded-lg border border-slate-800/80"
              >
                <span className="text-emerald-400 font-mono font-bold">✓</span>
                <span className="font-medium">{layer.name}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Unavailable Layer */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-rose-500/30 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-rose-400">
            <XCircle className="w-4 h-4" />
            <span>Unavailable Layer</span>
          </div>
          <div className="bg-rose-950/30 border border-rose-900/50 p-3 rounded-lg space-y-1.5">
            <div className="flex items-center space-x-2 text-xs font-bold text-rose-300">
              <span className="font-mono">✗</span>
              <span>{fallbackData.failed_layer.name}</span>
            </div>
            <p className="text-[11px] text-rose-200/80 leading-relaxed pl-4">
              {fallbackData.failed_layer.reason}
            </p>
          </div>

          <div className="text-[11px] text-slate-400 pt-2 flex items-center space-x-1.5 pl-1">
            <ArrowDown className="w-3.5 h-3.5 text-amber-400 animate-bounce" />
            <span>Available findings and intermediate artifacts are rendered below.</span>
          </div>
        </div>
      </div>

      {/* Available Findings Summary */}
      <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-300">
        <span className="font-bold text-indigo-300 uppercase tracking-wider text-[11px] block mb-1">
          Execution Recovery Notice:
        </span>
        <p>{fallbackData.available_findings_summary}</p>
      </div>
    </div>
  );
};
