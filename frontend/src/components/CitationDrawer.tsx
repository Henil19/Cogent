import React from "react";
import { X, ExternalLink, ShieldCheck, FileText, Bookmark, Layers, Hash } from "lucide-react";
import type { CitationReference } from "../types/cogent";

interface CitationDrawerProps {
  citation: CitationReference | null;
  isOpen: boolean;
  onClose: () => void;
}

export const CitationDrawer: React.FC<CitationDrawerProps> = ({
  citation,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !citation) return null;

  const roleColor = (role?: string) => {
    switch (role) {
      case "DIRECT SUPPORT":
        return "bg-emerald-500/10 text-emerald-300 border-emerald-500/30";
      case "CONTEXTUAL":
        return "bg-cyan-500/10 text-cyan-300 border-cyan-500/30";
      case "BACKGROUND":
        return "bg-purple-500/10 text-purple-300 border-purple-500/30";
      default:
        return "bg-indigo-500/10 text-indigo-300 border-indigo-500/30";
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Slide-over Drawer */}
      <div className="relative w-full max-w-md bg-slate-950 border-l border-slate-800 shadow-2xl z-10 flex flex-col h-full transform transition-transform duration-300 ease-out">
        {/* Header */}
        <div className="p-5 border-b border-slate-800/80 flex items-center justify-between bg-slate-900/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-lg bg-indigo-500/20 border border-indigo-500/30 flex items-center justify-center text-xs font-mono font-bold text-indigo-300">
              [{citation.reference_number}]
            </div>
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
                Citation Grounding Inspector
              </h3>
              <p className="text-[11px] text-slate-400">Verifiable Documentary Provenance</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body Content */}
        <div className="p-5 space-y-5 overflow-y-auto flex-1">
          {/* Source Document Card */}
          <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-2.5">
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-slate-800 text-slate-300">
                Documentary Reference
              </span>
              <span
                className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${roleColor(
                  citation.evidence_role
                )}`}
              >
                {citation.evidence_role || "DIRECT SUPPORT"}
              </span>
            </div>

            <h4 className="text-sm font-bold text-slate-100 leading-snug">
              {citation.source_title}
            </h4>

            {citation.source_uri && (
              <a
                href={citation.source_uri}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center space-x-1.5 text-xs text-indigo-400 hover:text-indigo-300 transition-colors break-all"
              >
                <span className="truncate max-w-[280px]">{citation.source_uri}</span>
                <ExternalLink className="w-3 h-3 shrink-0" />
              </a>
            )}

            {/* Document metadata chips */}
            <div className="flex flex-wrap gap-2 pt-1 text-[11px] text-slate-400">
              {citation.page_number && (
                <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800/80 text-slate-300">
                  <Bookmark className="w-3 h-3 text-slate-400" />
                  <span>Page {citation.page_number}</span>
                </span>
              )}
              {citation.section_title && (
                <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-slate-800/80 text-slate-300 truncate max-w-[200px]">
                  <Hash className="w-3 h-3 text-slate-400" />
                  <span className="truncate">{citation.section_title}</span>
                </span>
              )}
            </div>
          </div>

          {/* Verbatim Grounded Passage */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
                <FileText className="w-3.5 h-3.5 text-indigo-400" />
                <span>Verbatim Quoted Passage</span>
              </span>
              <span className="text-[10px] font-mono text-emerald-400 flex items-center space-x-1" title="Layer 5 evidentiary entailment strength">
                <ShieldCheck className="w-3 h-3" />
                <span>Evidence Support Strength: {(citation.confidence_grounding * 100).toFixed(0)}%</span>
              </span>
            </div>
            <div className="p-3.5 rounded-xl bg-indigo-950/20 border border-indigo-900/40 text-xs text-slate-200 leading-relaxed italic">
              "{citation.snippet}"
            </div>
          </div>

          {/* Used In Claims / Reasoning Chains */}
          <div className="space-y-3 pt-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center space-x-1.5">
              <Layers className="w-3.5 h-3.5 text-cyan-400" />
              <span>Attribution in Reasoning Graph</span>
            </span>

            {citation.used_in_claims && citation.used_in_claims.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-semibold text-slate-400">
                  Substantiated Claims:
                </span>
                <div className="space-y-1">
                  {citation.used_in_claims.map((claim, idx) => (
                    <div
                      key={idx}
                      className="p-2 rounded-lg bg-slate-900/60 border border-slate-800/70 text-xs text-slate-300"
                    >
                      • {claim}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {citation.used_in_steps && citation.used_in_steps.length > 0 && (
              <div className="space-y-1.5">
                <span className="text-[11px] font-semibold text-slate-400">
                  Active in Reasoning Steps:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {citation.used_in_steps.map((step, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded bg-slate-800 text-xs font-mono text-indigo-300 border border-slate-700"
                    >
                      Step {step}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/40 flex items-center justify-between text-[11px] text-slate-400">
          <span>Layer 8 Verifiable Provenance</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
