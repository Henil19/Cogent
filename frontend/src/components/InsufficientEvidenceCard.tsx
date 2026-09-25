import React from "react";
import { AlertCircle, CheckCircle2, XCircle, ArrowRight, HelpCircle } from "lucide-react";
import type { InsufficientEvidenceData } from "../types/cogent";

interface InsufficientEvidenceCardProps {
  data?: InsufficientEvidenceData;
  onRefineQuery?: () => void;
}

export const InsufficientEvidenceCard: React.FC<InsufficientEvidenceCardProps> = ({
  data,
  onRefineQuery,
}) => {
  const fallbackData: InsufficientEvidenceData = data || {
    summary:
      "The retrieved documents and live web search did not supply sufficient verified empirical evidence to reach a definitive deductive or inductive conclusion without speculative extrapolation.",
    candidates_found: 2,
    what_we_found: [
      "Peripheral discussions of the target domain and general theoretical definitions.",
      "Fragmentary documentation without explicit quantitative benchmarks or comparative measurements.",
    ],
    what_is_missing: [
      "Direct empirical datasets or published head-to-head evaluation tables.",
      "Corroborating peer-reviewed citations resolving the target trade-off.",
    ],
    what_can_be_concluded:
      "The theoretical motivation is widely recognized, but current corpus coverage cannot establish exact empirical superiority.",
    what_cannot_be_concluded:
      "Definitive claims regarding runtime latency, memory bounds, or empirical error rates under production workloads.",
    suggested_next_steps: [
      "Upload targeted primary source PDFs or technical reports via the Documents manager.",
      "Switch source mode to Live Web or Hybrid to broaden the real-time retrieval scope.",
      "Refine the inquiry to focus on specific documented metrics or benchmark suites.",
    ],
  };

  return (
    <div className="glass-panel rounded-2xl p-6 sm:p-8 border border-amber-500/40 bg-amber-950/10 mb-8 shadow-2xl space-y-6">
      {/* Header Banner */}
      <div className="flex items-start space-x-3.5 pb-4 border-b border-amber-500/20">
        <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400 shrink-0 mt-0.5">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <div className="flex items-center space-x-2 mb-1">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-400">
              Layer 7/9 Epistemic Abstention Protocol Active
            </span>
          </div>
          <h3 className="text-base sm:text-lg font-bold text-slate-100">
            Insufficient Evidence to Form Definite Conclusion
          </h3>
          <p className="text-xs sm:text-sm text-slate-300 mt-1 leading-relaxed">
            {fallbackData.summary}
          </p>
        </div>
      </div>

      {/* 2-Column Comparison: What Found vs What Missing */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* What We Found */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-emerald-400">
            <CheckCircle2 className="w-4 h-4" />
            <span>What We Found ({fallbackData.what_we_found.length} items)</span>
          </div>
          <ul className="space-y-2">
            {fallbackData.what_we_found.map((item, idx) => (
              <li
                key={idx}
                className="text-xs text-slate-300 flex items-start space-x-2 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/60"
              >
                <span className="text-emerald-400 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* What Is Missing */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-rose-400">
            <XCircle className="w-4 h-4" />
            <span>What Is Missing ({fallbackData.what_is_missing.length} gaps)</span>
          </div>
          <ul className="space-y-2">
            {fallbackData.what_is_missing.map((item, idx) => (
              <li
                key={idx}
                className="text-xs text-slate-300 flex items-start space-x-2 bg-slate-950/50 p-2.5 rounded-lg border border-slate-800/60"
              >
                <span className="text-rose-400 font-bold">•</span>
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Definite Boundaries: Concluded vs Cannot Concluded */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-3 text-xs">
        <div className="space-y-1">
          <span className="font-bold text-indigo-300 uppercase tracking-wider text-[11px] block">
            What Can Be Responsibly Concluded:
          </span>
          <p className="text-slate-200 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            {fallbackData.what_can_be_concluded}
          </p>
        </div>

        <div className="space-y-1">
          <span className="font-bold text-amber-300 uppercase tracking-wider text-[11px] block">
            What CANNOT Be Concluded (Abstention Zone):
          </span>
          <p className="text-slate-200 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800">
            {fallbackData.what_cannot_be_concluded}
          </p>
        </div>
      </div>

      {/* Suggested Next Steps */}
      <div className="pt-2">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-300 block mb-2 flex items-center space-x-1.5">
          <HelpCircle className="w-3.5 h-3.5 text-indigo-400" />
          <span>Recommended Next Actions</span>
        </span>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
          {fallbackData.suggested_next_steps.map((step, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg bg-indigo-950/20 border border-indigo-900/30 text-xs text-indigo-200 flex items-start space-x-2"
            >
              <ArrowRight className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
              <span>{step}</span>
            </div>
          ))}
        </div>
      </div>

      {onRefineQuery && (
        <div className="pt-2 flex justify-end">
          <button
            onClick={onRefineQuery}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-amber-500/20 hover:bg-amber-500/30 text-amber-200 border border-amber-500/40 transition-colors"
          >
            Refine Inquiry in Cockpit
          </button>
        </div>
      )}
    </div>
  );
};
