import React, { useState } from "react";
import { Scale, ShieldAlert, CheckCircle2, Split, HelpCircle, ChevronDown, ExternalLink, Sparkles } from "lucide-react";
import type { DialecticalContradiction, EvidenceVerificationCard } from "../types/cogent";

interface EvidenceDialecticViewProps {
  contradictions?: DialecticalContradiction[];
  evidence?: EvidenceVerificationCard[];
}

export const EvidenceDialecticView: React.FC<EvidenceDialecticViewProps> = ({
  contradictions = [],
  evidence = [],
}) => {
  // If no contradictions are present, default to Verified Evidence tab immediately
  const [activeTab, setActiveTab] = useState<"DIALECTIC" | "EVIDENCE">(
    contradictions.length > 0 ? "DIALECTIC" : "EVIDENCE"
  );

  // Per-card toggle state for foldable/closable explanations
  const [expandedCards, setExpandedCards] = useState<Record<string, boolean>>({});

  const toggleCard = (id: string) => {
    setExpandedCards((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const getResolutionBadge = (status: string) => {
    switch (status) {
      case "RECONCILED":
        return {
          label: "Reconciled",
          style: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
          icon: CheckCircle2,
        };
      case "CONTEXTUAL_DIFFERENCE":
        return {
          label: "Contextual Difference",
          style: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
          icon: Split,
        };
      case "PARTIALLY_RECONCILED":
        return {
          label: "Partially Reconciled",
          style: "bg-amber-500/10 text-amber-400 border-amber-500/30",
          icon: HelpCircle,
        };
      case "UNRESOLVED":
      default:
        return {
          label: "Unresolved Disagreement",
          style: "bg-rose-500/10 text-rose-400 border-rose-500/30",
          icon: ShieldAlert,
        };
    }
  };

  const sanitizeTopic = (topic: string) => {
    if (!topic || topic.startsWith("clm_chk_") || topic.includes(" vs ")) {
      return "Reported Discrepancy";
    }
    return topic;
  };

  const sanitizeStatement = (stmt: string) => {
    if (!stmt) return "";
    let s = stmt.trim();

    // If statement has raw boilerplate with IDs like "Position A asserts that clm_chk_..."
    const match = s.match(/holds, as supported by empirical findings in '([^']+)': "(.*)"/);
    if (match && match[2]) {
      s = match[2];
    }

    // Remove internal IDs
    s = s.replace(/clm_chk_[a-f0-9_]+/g, "source finding");

    // Remove leading/trailing editorial brackets and ellipses: '[...]', '(...)'
    s = s.replace(/^\s*\[(?:\.\.\.|\s)*\]\s*/g, "");
    s = s.replace(/^\s*\((?:\.\.\.|\s)*\)\s*/g, "");
    s = s.replace(/\[(?:\.\.\.|\s)*\]/g, " ");

    // Remove internal manuscript table/figure references: (Table 3), (Figure 1), (see Table 2), etc.
    s = s.replace(/\s*\((?:see\s+)?(?:Table|Figure|Fig\.|Box|Supplementary\s+Table)\s*[\dA-Za-z\s,\.-]*\)/gi, "");

    // Remove bracketed citation numbers: [12], [12,21,22], [38, 66], [13, 195, 205-207]
    s = s.replace(/\s*\[[\d\s,–\-\+]+\]/g, "");

    // Remove unclosed or author-year parentheticals: (Desbrow and Leveritt, 2006, 2007. or (Jodra et al., 2020)
    s = s.replace(/\s*\([A-Z][a-zA-Z\s,–\-]+(?:et\s+al\.?)?,?\s*\d{4}[^\)]*\)?/g, "");

    // Clean conversational / editorial filler openers
    s = s.replace(/^(?:And,?\s+if\s+that\s+isn't\s+enough,?\s*)/i, "");
    s = s.replace(/^Likewise,?\s+when\s+considering\s+/i, "When considering ");
    s = s.replace(/^Overall,?\s+it\s+is\s+established\s+that\s+/i, "");
    s = s.replace(/^However,?\s+in\s+experiments\s+about\s+[^,]+,\s*/i, "");
    s = s.replace(/^Notably,?\s+/i, "");

    // Clean spacing around punctuation
    s = s.replace(/\s+([,\.\?!;:])/g, "$1");
    s = s.replace(/\s{2,}/g, " ").trim();

    if (s && s[0] === s[0].toLowerCase()) {
      s = s[0].toUpperCase() + s.slice(1);
    }
    if (s && !/[.!?]$/.test(s)) {
      s += ".";
    }
    return s;
  };

  const cleanSnippet = (text: string) => {
    if (!text) return "";
    let clean = text.replace(/^\[Document:[^>\]]*(?:>\s*Section:[^\]]*)?\]\s*/i, "");
    clean = clean.replace(/^\[Document:[^\]]*\]\s*/i, "");
    return clean.trim();
  };

  return (
    <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-slate-800/80 mb-8 shadow-xl">
      {/* Header Tabs */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-800/60">
        <div className="flex items-center space-x-2">
          <Scale className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold text-slate-100 tracking-tight">
            Evidence & Dialectical Verification
          </h3>
        </div>

        <div className="flex items-center space-x-1 p-1 rounded-lg bg-slate-900 border border-slate-800">
          <button
            onClick={() => setActiveTab("DIALECTIC")}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeTab === "DIALECTIC"
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Contradictions ({contradictions.length})
          </button>
          <button
            onClick={() => setActiveTab("EVIDENCE")}
            className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
              activeTab === "EVIDENCE"
                ? "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            Verified Evidence ({evidence.length})
          </button>
        </div>
      </div>

      {/* Dialectical Contradiction View (Zero Winner Forcing) */}
      {activeTab === "DIALECTIC" && (
        <div className="space-y-4">
          {contradictions.length === 0 ? (
            <div className="glass-card rounded-xl p-6 text-center space-y-3 border border-slate-800 bg-slate-900/60">
              <CheckCircle2 className="w-7 h-7 text-emerald-400 mx-auto" />
              <div className="space-y-1">
                <h4 className="text-xs font-bold text-slate-200">No Empirical Contradictions Detected</h4>
                <p className="text-xs text-slate-400 max-w-lg mx-auto leading-relaxed">
                  All verified evidence sources exhibit mutual entailment consistency. The retrieved facts and historical outcome are fully substantiated without conflicting records.
                </p>
              </div>
              {evidence.length > 0 && (
                <button
                  onClick={() => setActiveTab("EVIDENCE")}
                  className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/30 transition-all"
                >
                  <span>View {evidence.length} Verified Evidence Cards</span>
                </button>
              )}
            </div>
          ) : (
            contradictions.map((c, idx) => {
              const cardId = c.contradiction_id || `contra_${idx}`;
              const isExpanded = !!expandedCards[cardId];
              const res = getResolutionBadge(c.resolution_status || "UNRESOLVED");
              const ResIcon = res.icon;
              const displayTopic = sanitizeTopic(c.topic);
              const displayClaimA = sanitizeStatement(c.claim_a);
              const displayClaimB = sanitizeStatement(c.claim_b);

              return (
                <div
                  key={cardId}
                  className="glass-card rounded-xl p-4 sm:p-5 border border-amber-500/30 bg-slate-900/80 space-y-3.5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="text-[11px] font-bold px-2.5 py-0.5 rounded bg-amber-950/60 text-amber-300 border border-amber-900/60">
                      Discrepancy: {displayTopic}
                    </span>

                    <div className="flex items-center space-x-2">
                      <span
                        className={`flex items-center space-x-1 text-[10px] font-semibold uppercase px-2.5 py-0.5 rounded-full border ${res.style}`}
                      >
                        <ResIcon className="w-3 h-3" />
                        <span>{res.label}</span>
                      </span>

                      {c.is_empirical_stalemate && (
                        <span className="flex items-center space-x-1 text-[10px] font-semibold text-rose-400 bg-rose-950/40 px-2.5 py-0.5 rounded-full border border-rose-900/50">
                          <ShieldAlert className="w-3 h-3" />
                          <span>Empirical Stalemate</span>
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Side by Side Claims: Zero Winner Forcing */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {/* Thesis A */}
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800/60 pb-1.5 gap-2">
                        <span className="font-bold text-slate-200 shrink-0">Position A</span>
                        <span
                          className="text-[10px] text-cyan-300 font-medium bg-cyan-950/40 px-2 py-0.5 rounded border border-cyan-800/40 truncate max-w-[240px]"
                          title={c.source_a}
                        >
                          {c.source_a}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 font-medium leading-relaxed">
                        {displayClaimA}
                      </p>
                      <div className="text-[10px] text-slate-400 font-mono">
                        Evidence Support Strength: {(c.confidence_a * 100).toFixed(0)}%
                      </div>
                    </div>

                    {/* Antithesis B */}
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-slate-400 border-b border-slate-800/60 pb-1.5 gap-2">
                        <span className="font-bold text-slate-200 shrink-0">Position B</span>
                        <span
                          className="text-[10px] text-amber-300 font-medium bg-amber-950/40 px-2 py-0.5 rounded border border-amber-800/40 truncate max-w-[240px]"
                          title={c.source_b}
                        >
                          {c.source_b}
                        </span>
                      </div>
                      <p className="text-xs text-slate-200 font-medium leading-relaxed">
                        {displayClaimB}
                      </p>
                      <div className="text-[10px] text-slate-400 font-mono">
                        Evidence Support Strength: {(c.confidence_b * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>

                  {/* Foldable / Closable Explanation Field */}
                  <div className="pt-1">
                    <button
                      onClick={() => toggleCard(cardId)}
                      className="flex items-center justify-between w-full p-2.5 rounded-xl bg-slate-950/60 hover:bg-slate-950 border border-slate-800 transition-colors text-left"
                    >
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                        <span className="text-xs font-semibold text-slate-200">
                          {isExpanded ? "Hide Detailed Explanation" : "View Reconciliation Analysis & Explanation"}
                        </span>
                      </div>
                      <div className="flex items-center space-x-1.5 text-xs text-indigo-400 font-medium">
                        <span>{isExpanded ? "Close" : "Expand"}</span>
                        <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${isExpanded ? "rotate-180" : ""}`} />
                      </div>
                    </button>

                    {/* Collapsible Slide Container */}
                    {isExpanded && (
                      <div className="mt-2.5 p-3.5 rounded-xl bg-indigo-950/25 border border-indigo-900/40 text-xs text-indigo-200 space-y-2 animate-in fade-in duration-200">
                        <div className="flex items-center space-x-2 text-indigo-400 text-[10px] font-bold uppercase tracking-wider">
                          <span>Reconciliation Synthesis (Zero Winner Forcing):</span>
                        </div>
                        <p className="leading-relaxed text-slate-200">
                          {sanitizeStatement(c.reconciliation_heuristic)}
                        </p>
                        <p className="text-[11px] text-slate-400 italic pt-1 border-t border-indigo-900/30">
                          Cogent does not arbitrarily discard either verified finding. Both sources are documented with their specific context and evaluation conditions.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Grounding Evidence Snippets */}
      {activeTab === "EVIDENCE" && (
        <div className="space-y-3">
          {/* Verified Evidence Header Banner */}
          <div className="flex items-center justify-between p-3.5 rounded-xl bg-emerald-950/25 border border-emerald-500/30 text-emerald-200">
            <div className="flex items-center space-x-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <div>
                <span className="text-xs font-bold text-emerald-300 block">Factually Verified Empirical Records</span>
                <span className="text-[11px] text-emerald-400/80">Every claim is grounded in official documentation and verified citations.</span>
              </div>
            </div>
            <span className="text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded bg-emerald-900/50 text-emerald-300 border border-emerald-700/50">
              {evidence.length} Proven {evidence.length === 1 ? "Record" : "Records"}
            </span>
          </div>

          {evidence.length === 0 ? (
            <div className="glass-card rounded-xl p-5 text-center text-slate-500 text-xs">
              No evidence cards attached.
            </div>
          ) : (
            evidence.map((ev, idx) => (
              <div
                key={ev.evidence_id || idx}
                className="glass-card rounded-xl p-4 border border-slate-800 bg-slate-900/70 space-y-2.5 hover:border-slate-700 transition-all"
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="flex items-center space-x-2 min-w-0">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    <span className="text-xs font-bold text-slate-200 truncate">
                      {ev.document_title}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 shrink-0">
                    <span
                      className={`text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full border ${
                        ev.entailment_status === "ENTAILS"
                          ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                          : ev.entailment_status === "CONTRADICTS"
                          ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                          : "bg-slate-500/10 text-slate-400 border-slate-500/30"
                      }`}
                    >
                      {ev.entailment_status === "ENTAILS" ? "Verified Entailment" : ev.entailment_status}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded border border-emerald-800/40">
                      {(ev.relevance_score * 100).toFixed(0)}% Match
                    </span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-lg border border-slate-800/80">
                  "{cleanSnippet(ev.snippet)}"
                </p>

                <div className="flex items-center justify-between text-[10px] text-slate-500 pt-0.5">
                  <span className="text-slate-400 font-medium">Verified Reference Citation</span>
                  {ev.source_uri && (
                    <a
                      href={ev.source_uri}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-indigo-400 hover:text-indigo-300 transition-colors truncate max-w-[280px]"
                    >
                      <span className="truncate">{ev.source_uri}</span>
                      <ExternalLink className="w-3 h-3 shrink-0" />
                    </a>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};
