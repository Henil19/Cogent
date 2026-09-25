import React, { useState } from "react";
import { GitBranch, Info } from "lucide-react";
import type { ReasoningStep } from "../types/cogent";

interface ReasoningDAGProps {
  steps?: ReasoningStep[];
}

export const ReasoningDAG: React.FC<ReasoningDAGProps> = ({ steps = [] }) => {
  const [selectedStep, setSelectedStep] = useState<ReasoningStep | null>(
    steps.length > 0 ? steps[0] : null
  );
  const [showAllSteps, setShowAllSteps] = useState(false);

  if (!steps || steps.length === 0) {
    return (
      <div className="glass-panel rounded-2xl p-6 border border-slate-800/80 mb-8 text-center text-slate-400 text-xs">
        No formal inference steps required for this direct inquiry.
      </div>
    );
  }

  const cleanStepText = (text: string) => {
    if (!text) return "";
    return text.replace(/syn_leaf_step_leaf_\d+/g, "").replace(/clm_chk_[a-f0-9_]+/g, "evidence claim").trim();
  };

  const cleanPremiseText = (premise: string, idx: number) => {
    if (!premise || premise.includes("syn_leaf_step_leaf_") || premise.startsWith("Premise ")) {
      return `Supporting finding ${idx + 1}`;
    }
    return cleanStepText(premise);
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "VALID":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "CONTINGENT":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "DISPUTED":
        return "bg-rose-500/10 text-rose-400 border-rose-500/30";
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
    }
  };

  // Primary reasoning path (curated 3-4 steps) vs full derivation
  const displayedSteps = showAllSteps ? steps : steps.slice(0, 4);

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-7 border border-slate-800/70 mb-8 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800/60">
        <div className="flex items-center space-x-2.5">
          <GitBranch className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-tight">
              Reasoning & Inference Chain
            </h3>
            <p className="text-xs text-slate-400">
              Traces how verified evidence connects step-by-step to the synthesized conclusion
            </p>
          </div>
        </div>

        <button
          onClick={() => setShowAllSteps(!showAllSteps)}
          className="px-3 py-1 rounded-lg text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors cursor-pointer"
        >
          {showAllSteps ? "Show Summary Path" : `Explore All ${steps.length} Steps →`}
        </button>
      </div>

      {/* Main Reasoning Flowchart / Step Path */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Step Nodes List */}
        <div className="lg:col-span-6 space-y-2.5">
          {displayedSteps.map((step, idx) => {
            const isSelected = selectedStep?.step_id === step.step_id;
            return (
              <div
                key={step.step_id || idx}
                onClick={() => setSelectedStep(step)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? "bg-indigo-950/40 border-indigo-500/50 shadow-md shadow-indigo-500/10"
                    : "bg-slate-900/50 border-slate-800/80 hover:border-slate-700 hover:bg-slate-850"
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center space-x-2">
                    <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      Step {step.step_index ?? idx + 1}
                    </span>
                    <span className="text-[10px] font-medium uppercase px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 border border-indigo-500/20">
                      {step.operation || "Inference"}
                    </span>
                  </div>

                  <span
                    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${getStatusBadge(
                      step.reasoning_status
                    )}`}
                  >
                    {step.reasoning_status}
                  </span>
                </div>

                <p className="text-xs text-slate-200 font-medium line-clamp-2 leading-relaxed">
                  {cleanStepText(step.conclusion)}
                </p>
              </div>
            );
          })}
        </div>

        {/* Selected Step Inspector */}
        <div className="lg:col-span-6">
          {selectedStep ? (
            <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 h-full flex flex-col justify-between space-y-4">
              <div>
                <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800/80">
                  <div className="flex items-center space-x-2">
                    <Info className="w-4 h-4 text-indigo-400" />
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                      Inference Step Inspector
                    </h4>
                  </div>
                  <span
                    className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${getStatusBadge(
                      selectedStep.reasoning_status
                    )}`}
                  >
                    {selectedStep.reasoning_status}
                  </span>
                </div>

                {/* Proposition (Deduced Conclusion) */}
                <div className="mb-3.5 space-y-1">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                    Synthesized Finding:
                  </span>
                  <p className="text-xs font-medium text-slate-100 bg-slate-950/60 p-3 rounded-lg border border-slate-800/80 leading-relaxed">
                    {cleanStepText(selectedStep.conclusion)}
                  </p>
                </div>

                {/* Grounding Premises */}
                <div className="space-y-1.5">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 block">
                    Underlying Evidence Premises:
                  </span>
                  <div className="space-y-1">
                    {selectedStep.premises.map((premise, pIdx) => (
                      <div
                        key={pIdx}
                        className="text-xs text-slate-300 p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 flex items-start space-x-2"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 mt-1.5 shrink-0" />
                        <span className="leading-relaxed">{cleanPremiseText(premise, pIdx)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-2 text-[11px] text-slate-400 border-t border-slate-800/60 flex items-center justify-between">
                <span>Operation: {selectedStep.operation || "Deduction"}</span>
                <span>Grounding: Verified documentary entailment</span>
              </div>
            </div>
          ) : (
            <div className="p-5 rounded-xl border border-slate-800/80 bg-slate-900/30 text-center text-slate-500 text-xs">
              Select a reasoning step to inspect premises and inferential operations.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
