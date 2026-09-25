import React from "react";
import { AlertOctagon, RotateCcw } from "lucide-react";
import type { CogentExecutionTrace } from "../types/cogent";

interface FailureCardProps {
  error?: {
    code: string;
    message: string;
    failed_layer: number;
  };
  trace?: CogentExecutionTrace | null;
  onRetry: () => void;
}

export const FailureCard: React.FC<FailureCardProps> = ({
  error,
  trace,
  onRetry,
}) => {
  const failureCode = error?.code || trace?.failure_code || "EXECUTION_EXCEPTION";
  const failureMsg = error?.message || trace?.failure_message || "An unexpected error occurred during pipeline execution.";
  const failedLayer = error?.failed_layer ?? trace?.failed_layer ?? 0;
  const startedAt = trace?.started_at ? new Date(trace.started_at).toLocaleTimeString() : "N/A";
  const completedAt = trace?.completed_at ? new Date(trace.completed_at).toLocaleTimeString() : "N/A";

  return (
    <div className="glass-panel rounded-2xl p-6 border border-red-500/40 bg-red-950/20 mb-8 shadow-xl">
      <div className="flex items-start space-x-3 mb-4">
        <div className="p-2 rounded-xl bg-red-500/20 border border-red-500/40 text-red-400">
          <AlertOctagon className="w-6 h-6" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-red-200 uppercase tracking-wide">
              Pipeline Execution Terminated: {failureCode}
            </h3>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-900">
              Layer {failedLayer} Exception
            </span>
          </div>
          <p className="text-xs text-red-300/90 mt-1">
            {failureMsg}
          </p>
        </div>
      </div>

      {/* Telemetry Trace Timestamps */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-3 rounded-xl bg-slate-950/70 border border-red-900/30 text-xs text-slate-400 mb-4">
        <div>
          <span className="text-[10px] text-slate-500 block uppercase">Failed Layer</span>
          <span className="font-mono text-red-300 font-semibold">Layer {failedLayer}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase">Started At</span>
          <span className="font-mono text-slate-300">{startedAt}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase">Completed At</span>
          <span className="font-mono text-slate-300">{completedAt}</span>
        </div>
        <div>
          <span className="text-[10px] text-slate-500 block uppercase">Telemetry Status</span>
          <span className="font-mono text-red-400 font-semibold">PERSISTED_IN_DB</span>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          onClick={onRetry}
          className="flex items-center space-x-2 px-4 py-2 rounded-lg text-xs font-semibold text-white bg-red-600 hover:bg-red-500 transition-colors shadow-md shadow-red-600/20"
        >
          <RotateCcw className="w-3.5 h-3.5" />
          <span>Retry Research Query</span>
        </button>
      </div>
    </div>
  );
};
