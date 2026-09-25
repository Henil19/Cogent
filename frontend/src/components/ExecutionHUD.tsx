import React, { useState } from "react";
import {
  CheckCircle2,
  Clock,
  AlertTriangle,
  Activity,
  Layers,
  Search,
  Globe2,
  Scale,
  Sparkles,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import type { CogentExecutionTrace } from "../types/cogent";

interface ExecutionHUDProps {
  trace?: CogentExecutionTrace | null;
  isProcessing: boolean;
  failedLayer?: number | null;
  currentStepDescription?: string;
}

const RESEARCH_STAGES = [
  { id: 1, name: "Understanding", detail: "Resolving inquiry bounds & core definitions" },
  { id: 2, name: "Research Plan", detail: "Formulating multi-angle investigation strategy" },
  { id: 3, name: "Sources", detail: "Acquiring scientific literature & documentary evidence" },
  { id: 4, name: "Search & Fusion", detail: "Dense semantic matching & hybrid retrieval" },
  { id: 5, name: "Evidence & Conflicts", detail: "Extracting findings & mapping disagreements" },
  { id: 6, name: "Reasoning", detail: "Constructing logical inference chains" },
  { id: 7, name: "Trust Calibration", detail: "Quantifying uncertainty & epistemic stability" },
  { id: 8, name: "Robustness", detail: "Assessing dependency on individual studies" },
  { id: 9, name: "Synthesis", detail: "Assembling calibrated, evidence-backed answer" },
  { id: 10, name: "Diagnostics", detail: "Verifying system integrity & telemetry" },
];

export const ExecutionHUD: React.FC<ExecutionHUDProps> = ({
  trace,
  isProcessing,
  failedLayer,
  currentStepDescription,
}) => {
  const [showTechnicalTrace, setShowTechnicalTrace] = useState(false);

  return (
    <div className="w-full glass-panel rounded-2xl p-5 sm:p-6 mb-6 border border-slate-800/80 shadow-2xl space-y-5">
      {/* Header with Pulse & Latency */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800/60">
        <div className="flex items-center space-x-2.5">
          <div className="relative flex items-center justify-center">
            <div
              className={`w-3 h-3 rounded-full ${
                isProcessing
                  ? "bg-indigo-500 animate-ping"
                  : failedLayer
                  ? "bg-rose-500"
                  : "bg-emerald-500"
              }`}
            />
            <div
              className={`absolute w-2.5 h-2.5 rounded-full ${
                isProcessing
                  ? "bg-indigo-400"
                  : failedLayer
                  ? "bg-rose-400"
                  : "bg-emerald-400"
              }`}
            />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              {isProcessing ? "Research Process in Progress" : "Research Process Timeline"}
            </h3>
            <p className="text-[11px] text-slate-400">
              {isProcessing
                ? currentStepDescription || "Actively executing multi-stage research investigation..."
                : failedLayer
                ? `Research pipeline paused at stage ${failedLayer}`
                : "All research phases verified with calibrated evidentiary grounding."}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400">
          {trace && (
            <>
              <span className="font-mono text-indigo-400 font-bold">
                {trace.total_latency_ms ? `${(trace.total_latency_ms / 1000).toFixed(2)}s` : "0.00s"}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase ${
                  trace.execution_status === "SUCCESS"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                    : trace.execution_status === "PARTIAL_EXECUTION"
                    ? "bg-amber-500/10 text-amber-400 border border-amber-500/30"
                    : trace.execution_status === "FAILED"
                    ? "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                    : "bg-indigo-500/10 text-indigo-400 border border-indigo-500/30"
                }`}
              >
                {trace.execution_status === "SUCCESS" ? "Complete" : trace.execution_status}
              </span>
            </>
          )}

          <button
            onClick={() => setShowTechnicalTrace(!showTechnicalTrace)}
            className="flex items-center space-x-1 text-[11px] text-slate-400 hover:text-slate-200 transition-colors"
          >
            <span>{showTechnicalTrace ? "Simple view" : "Technical trace"}</span>
            {showTechnicalTrace ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>
        </div>
      </div>

      {/* Human-first Research Stages */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2.5">
        {RESEARCH_STAGES.map((stage) => {
          const isFailed = failedLayer === stage.id;
          const isFinished =
            trace &&
            (trace.execution_status === "SUCCESS" || trace.execution_status === "PARTIAL_EXECUTION") &&
            !isFailed &&
            (!failedLayer || stage.id < failedLayer);
          const isActive = isProcessing && !trace;

          return (
            <div
              key={stage.id}
              className={`p-3 rounded-xl border transition-all text-left flex flex-col justify-between ${
                isFailed
                  ? "bg-rose-950/30 border-rose-500/40 text-rose-200"
                  : isFinished
                  ? "bg-slate-900/60 border-slate-800 text-slate-200"
                  : isActive
                  ? "bg-indigo-950/30 border-indigo-500/40 text-indigo-200 animate-pulse"
                  : "bg-slate-950/40 border-slate-900 text-slate-500"
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-semibold text-slate-300">
                  {stage.name}
                </span>
                {isFailed ? (
                  <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                ) : isFinished ? (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                ) : isActive ? (
                  <Activity className="w-3.5 h-3.5 text-indigo-400 animate-spin" />
                ) : (
                  <Clock className="w-3.5 h-3.5 text-slate-700" />
                )}
              </div>
              <p className="text-[10px] text-slate-400 leading-tight">
                {stage.detail}
              </p>
            </div>
          );
        })}
      </div>

      {/* Live Pipeline Status Snippet when Processing */}
      {isProcessing && (
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 text-xs space-y-3">
          <div className="flex items-center justify-between text-slate-400 text-[11px]">
            <span className="font-semibold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Active Investigation Streams:</span>
            </span>
            <span className="font-mono text-indigo-400">Live Synthesis</span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-4 gap-2.5">
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center space-x-2 text-slate-300">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <span>Deconstructing sub-questions</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center space-x-2 text-slate-300">
              <Globe2 className="w-3.5 h-3.5 text-cyan-400" />
              <span>Querying academic literature</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center space-x-2 text-slate-300">
              <Search className="w-3.5 h-3.5 text-emerald-400" />
              <span>Ranking evidence passages</span>
            </div>
            <div className="p-2.5 rounded-lg bg-slate-950/70 border border-slate-800 flex items-center space-x-2 text-slate-300">
              <Scale className="w-3.5 h-3.5 text-amber-400" />
              <span>Mapping conflicting positions</span>
            </div>
          </div>
        </div>
      )}

      {/* Optional Technical Details for Researchers */}
      {showTechnicalTrace && trace?.layer_telemetry && (
        <div className="mt-4 pt-4 border-t border-slate-800/60 animate-in fade-in duration-200">
          <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2">
            Technical Subsystem Latencies & Diagnostics
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
            {Object.entries(trace.layer_telemetry).map(([layerKey, item]) => (
              <div
                key={layerKey}
                className="p-2 rounded-lg bg-slate-950/60 border border-slate-850 flex items-center justify-between text-xs"
              >
                <span className="text-slate-400 font-mono text-[11px] truncate mr-1" title={item.layer_name}>
                  {item.layer_name || layerKey}
                </span>
                <span className="text-slate-200 font-mono font-semibold text-[11px] whitespace-nowrap">
                  {typeof item.latency_ms === "number" ? `${item.latency_ms.toFixed(1)}ms` : "0.0ms"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};


