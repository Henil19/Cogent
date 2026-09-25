import React, { useState } from "react";
import { Link2, AlertTriangle, ShieldCheck, RefreshCw, EyeOff, FileText } from "lucide-react";
import type { MinimalCutSetItem, CitationReference } from "../types/cogent";

interface ProvenanceCardProps {
  cutSet?: MinimalCutSetItem[];
  citations?: CitationReference[];
  onOpenCitation?: (refNum: number) => void;
}

export const ProvenanceCard: React.FC<ProvenanceCardProps> = ({
  cutSet = [],
  citations = [],
  onOpenCitation,
}) => {
  const [disabledSources, setDisabledSources] = useState<string[]>([]);

  // Collect unique sources from citations and cutSet
  const allSources = Array.from(
    new Set([
      ...citations.map((c) => c.source_title),
      ...cutSet.flatMap((item) => item.pivotal_sources),
    ])
  ).filter(Boolean);

  const toggleSource = (source: string) => {
    setDisabledSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    );
  };

  const resetSimulation = () => {
    setDisabledSources([]);
  };

  // Robustness calculation
  const fragileCount = cutSet.filter((c) => c.is_vulnerable_to_single_source_failure).length;
  const overallRobustness = fragileCount === 0 ? "HIGH" : fragileCount <= 3 ? "MODERATE" : "SINGLE-SOURCE DEPENDENT";

  const cleanClaimLabel = (text: string, idx: number) => {
    if (!text || text.includes("syn_leaf_step_leaf_") || text.startsWith("step_leaf_")) {
      return `Evidentiary Conclusion ${idx + 1}`;
    }
    return text.replace(/syn_leaf_step_leaf_\d+/g, "").trim();
  };

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-7 border border-slate-800/70 mb-8 shadow-xl space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800/60">
        <div className="flex items-center space-x-2.5">
          <Link2 className="w-5 h-5 text-indigo-400" />
          <div>
            <h3 className="text-sm font-bold text-slate-100 tracking-tight">
              Sources & Evidentiary Robustness
            </h3>
            <p className="text-xs text-slate-400">
              Evaluates how strongly conclusions depend on individual research sources
            </p>
          </div>
        </div>

        <span
          className={`px-3 py-1 rounded-full text-xs font-semibold uppercase border ${
            overallRobustness === "HIGH"
              ? "bg-emerald-500/10 text-emerald-300 border-emerald-500/30"
              : overallRobustness === "MODERATE"
              ? "bg-amber-500/10 text-amber-300 border-amber-500/30"
              : "bg-rose-500/10 text-rose-300 border-rose-500/30"
          }`}
        >
          {overallRobustness} ROBUSTNESS
        </span>
      </div>

      {/* Robustness Summary Card */}
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
          Source Dependency Summary
        </h4>
        <p className="text-xs sm:text-sm text-slate-200 leading-relaxed">
          {fragileCount === 0
            ? "All conclusions remain verified across multiple independent studies. No single document acts as a critical failure point."
            : `Most key findings are backed by multiple peer documents. However, ${fragileCount} secondary claim(s) rely primarily on single studies.`}
        </p>
      </div>

      {/* Interactive Source Resilience Simulator (What-If Analysis) */}
      <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800/80 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <RefreshCw className="w-4 h-4 text-indigo-400" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              Source Resilience Simulator: "What if a source is questioned?"
            </h4>
          </div>
          {disabledSources.length > 0 && (
            <button
              onClick={resetSimulation}
              className="text-xs text-indigo-400 hover:text-indigo-300 font-semibold underline cursor-pointer"
            >
              Reset ({disabledSources.length} removed)
            </button>
          )}
        </div>

        <p className="text-xs text-slate-400">
          Click any study to simulate removing it and see which conclusions retain independent support:
        </p>

        <div className="flex flex-wrap gap-2 pt-1">
          {allSources.length === 0 ? (
            <span className="text-xs text-slate-500 italic">No registered sources to simulate.</span>
          ) : (
            allSources.map((source) => {
              const isDisabled = disabledSources.includes(source);
              return (
                <button
                  key={source}
                  onClick={() => toggleSource(source)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all flex items-center space-x-1.5 cursor-pointer ${
                    isDisabled
                      ? "bg-rose-950/40 text-rose-300 border-rose-500/50 line-through opacity-80"
                      : "bg-slate-800/80 hover:bg-slate-800 text-slate-200 border-slate-700"
                  }`}
                >
                  {isDisabled && <EyeOff className="w-3 h-3 text-rose-400" />}
                  <span className="truncate max-w-[240px]" title={source}>
                    {source}
                  </span>
                </button>
              );
            })
          )}
        </div>

        {disabledSources.length > 0 && (
          <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-900/40 text-xs text-rose-200 flex items-start space-x-2 mt-2">
            <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Resilience Impact: </span>
              {cutSet.filter((c) => c.pivotal_sources.some((s) => disabledSources.includes(s))).length}{" "}
              conclusion(s) lose direct evidentiary grounding if [{disabledSources.join(", ")}] are excluded.
            </div>
          </div>
        )}
      </div>

      {/* Two Column Grid: Citations & Claims */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Verified Studies List */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>Referenced Research Literature</span>
            </h4>
            <span className="text-[10px] text-slate-400 font-mono">
              {allSources.length} distinct source(s) · {citations.length} passages
            </span>
          </div>

          <div className="space-y-2">
            {citations.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-900/40 text-center text-slate-500 text-xs border border-slate-800">
                No citations recorded.
              </div>
            ) : (
              citations.map((c) => (
                <div
                  key={c.reference_number}
                  className="p-3.5 rounded-xl bg-slate-900/50 border border-slate-800/80 hover:border-slate-700 transition-all space-y-1.5"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-500/40 text-indigo-300 text-[11px] font-mono font-bold">
                        [{c.reference_number}]
                      </span>
                      <span className="text-xs font-semibold text-slate-200 truncate max-w-[240px]">
                        {c.source_title}
                      </span>
                    </div>

                    <button
                      onClick={() => onOpenCitation && onOpenCitation(c.reference_number)}
                      className="text-[11px] text-indigo-400 hover:text-indigo-300 cursor-pointer font-medium shrink-0"
                    >
                      Inspect &rarr;
                    </button>
                  </div>
                  {c.snippet && (
                    <p className="text-[11px] text-slate-400 line-clamp-2 italic">
                      "{c.snippet}"
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Claim Dependency Cards */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Conclusion Grounding</span>
            </h4>
            <span className="text-[10px] text-slate-400 font-mono">
              {cutSet.length} conclusions
            </span>
          </div>

          <div className="space-y-2">
            {cutSet.length === 0 ? (
              <div className="p-4 rounded-xl bg-slate-900/40 text-center text-slate-500 text-xs border border-slate-800">
                All conclusions backed by consensus across sources.
              </div>
            ) : (
              cutSet.slice(0, 5).map((item, idx) => {
                const isCompromised = item.pivotal_sources.some((s) => disabledSources.includes(s));

                return (
                  <div
                    key={idx}
                    className={`p-3.5 rounded-xl border transition-all space-y-1.5 ${
                      isCompromised
                        ? "bg-rose-950/30 border-rose-500/50"
                        : item.is_vulnerable_to_single_source_failure
                        ? "bg-amber-950/15 border-amber-500/30"
                        : "bg-slate-900/50 border-slate-800/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-200">
                        {cleanClaimLabel(item.claim_text, idx)}
                      </span>
                      {isCompromised ? (
                        <span className="text-[10px] font-bold text-rose-300 bg-rose-500/20 px-2 py-0.5 rounded-full border border-rose-500/40">
                          Grounding Lost
                        </span>
                      ) : item.is_vulnerable_to_single_source_failure ? (
                        <span className="text-[10px] font-medium text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/30">
                          Single Source
                        </span>
                      ) : (
                        <span className="text-[10px] font-medium text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
                          Multi-Source
                        </span>
                      )}
                    </div>
                    {item.sensitivity_notes && (
                      <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                        {item.sensitivity_notes}
                      </p>
                    )}
                    <div className="text-[10px] text-slate-500 pt-0.5 flex items-center space-x-1.5">
                      <span className="font-semibold text-slate-400">Pivotal:</span>
                      <span className="italic truncate max-w-xs">{item.pivotal_sources.join(", ")}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
