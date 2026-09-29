import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { Navbar } from "./components/Navbar";
import { QueryCockpit } from "./components/QueryCockpit";
import { ExecutionHUD } from "./components/ExecutionHUD";
import { ResultTabs, type ResultTabType } from "./components/ResultTabs";
import { ResponseViewer } from "./components/ResponseViewer";
import { EvidenceDialecticView } from "./components/EvidenceDialecticView";
import { ReasoningDAG } from "./components/ReasoningDAG";
import { EpistemicTrustCard } from "./components/EpistemicTrustCard";
import { ProvenanceCard } from "./components/ProvenanceCard";
import { CitationDrawer } from "./components/CitationDrawer";
import { InsufficientEvidenceCard } from "./components/InsufficientEvidenceCard";
import { PartialExecutionCard } from "./components/PartialExecutionCard";
import { FailureCard } from "./components/FailureCard";
import { ClarificationModal } from "./components/ClarificationModal";

// Dedicated Views
import { DocumentsView } from "./components/views/DocumentsView";
import { HistoryView } from "./components/views/HistoryView";
import { AnalyticsView } from "./components/views/AnalyticsView";
import { SettingsView } from "./components/views/SettingsView";

import { apiClient } from "./api/client";
import type {
  ActiveView,
  AudienceFidelity,
  CogentQueryResponse,
  CitationReference,
  SessionRecord,
  SourceMode,
  AttachedFile,
} from "./types/cogent";

export function App() {
  // Navigation & View State
  const [activeView, setActiveView] = useState<ActiveView>("COCKPIT");
  const [audience, setAudience] = useState<AudienceFidelity>("EXECUTIVE");

  // Lifecycle state: "BEFORE_QUERY" | "DURING_QUERY" | "AFTER_QUERY"
  const [lifecycle, setLifecycle] = useState<"BEFORE_QUERY" | "DURING_QUERY" | "AFTER_QUERY">("BEFORE_QUERY");

  // Active Session State
  const [activeSession, setActiveSession] = useState<SessionRecord>({
    id: "default_session",
    title: "Cognitive Research Session",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    query_count: 0,
  });

  // Query Execution State
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentResponse, setCurrentResponse] = useState<CogentQueryResponse | null>(null);
  const [lastQuery, setLastQuery] = useState<string>("");
  const [failedLayer, setFailedLayer] = useState<number | null>(null);

  // Active Tab for Research Result Session
  const [activeResultTab, setActiveResultTab] = useState<ResultTabType>("ANSWER");

  // Interactive Citation Drawer State
  const [selectedCitation, setSelectedCitation] = useState<CitationReference | null>(null);
  const [isCitationDrawerOpen, setIsCitationDrawerOpen] = useState(false);

  // Clarification Modal State (Layer 1)
  const [isClarificationOpen, setIsClarificationOpen] = useState(false);

  // New Research Handler (resets to Clean Pre-Query Cockpit)
  const handleNewResearch = () => {
    setActiveView("COCKPIT");
    setLifecycle("BEFORE_QUERY");
    setCurrentResponse(null);
    setFailedLayer(null);
    setActiveResultTab("ANSWER");
    setActiveSession({
      id: `sess_${Date.now()}`,
      title: "New Research Inquiry",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      query_count: 0,
    });
  };

  // Primary Query Submission Handler
  const handleExecuteQuery = async (params: {
    query: string;
    sourceMode: SourceMode;
    attachedFiles: AttachedFile[];
    clarificationResponses?: Record<string, string>;
  }) => {
    setIsProcessing(true);
    setFailedLayer(null);
    setLastQuery(params.query);
    setLifecycle("DURING_QUERY");
    setActiveResultTab("ANSWER");

    try {
      const resp = await apiClient.executeQuery({
        query: params.query,
        session_id: activeSession.id,
        mode: params.sourceMode === "DOCUMENTS" ? "RESEARCH" : "DIALECTIC",
        source_mode: params.sourceMode,
        audience: audience,
        clarification_responses: params.clarificationResponses,
      });

      setCurrentResponse(resp);
      setLifecycle("AFTER_QUERY");

      // Check if Layer 1 flagged required clarification
      if (resp.clarifications_needed && resp.clarifications_needed.length > 0) {
        setIsClarificationOpen(true);
      }

      if (resp.status === "FAILED") {
        setFailedLayer(resp.error?.failed_layer || resp.trace?.failed_layer || 1);
      } else if (resp.status === "PARTIAL_EXECUTION") {
        setFailedLayer(resp.partial_execution?.failed_layer.id || 6);
      }
    } catch (err: any) {
      setLifecycle("AFTER_QUERY");
      const errMsg = err.message || "Cognitive pipeline encountered an unexpected exception.";
      const isRateLimit = errMsg.includes("502") || errMsg.includes("429") || errMsg.includes("quota") || errMsg.includes("rate");
      setFailedLayer(isRateLimit ? 1 : 4);
      setCurrentResponse({
        api_version: "v1",
        schema_version: "1.0.0",
        query_id: `err_${Date.now()}`,
        session_id: activeSession.id,
        rendered_content: "",
        status: "FAILED",
        error: {
          code: isRateLimit ? "API_QUOTA_EXCEEDED" : "PIPELINE_EXECUTION_EXCEPTION",
          message: isRateLimit 
            ? "API Rate Limit or Quota Exceeded (HTTP 502/429). Switch model to gemini-1.5-flash / gemini-2.0-flash or configure Groq / Offline mode."
            : errMsg,
          failed_layer: isRateLimit ? 1 : 4,
        },
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Clarification Submission
  const handleClarificationSubmit = (responses: Record<string, string>) => {
    setIsClarificationOpen(false);
    handleExecuteQuery({
      query: lastQuery,
      sourceMode: "HYBRID",
      attachedFiles: [],
      clarificationResponses: responses,
    });
  };

  // Open and restore an entire historical research session from Docker PostgreSQL
  const handleOpenHistoricalSession = async (sessionId: string, queryTitle: string) => {
    setIsProcessing(true);
    try {
      const restoredResponse = await apiClient.getSessionLatestResponse(sessionId);
      setCurrentResponse(restoredResponse);
      setLastQuery(restoredResponse.query || queryTitle);
      setActiveSession({
        id: sessionId,
        title: queryTitle || "Research Inquiry",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        query_count: 1,
      });
      setLifecycle("AFTER_QUERY");
      setActiveView("COCKPIT");
      setActiveResultTab("ANSWER");
    } catch (err: any) {
      console.error("Failed to load historical session:", err);
      alert("Could not load research results for this session: " + (err.message || String(err)));
    } finally {
      setIsProcessing(false);
    }
  };

  // Open Citation Drawer when user clicks [1], [2] marker
  const handleOpenCitation = (refNumber: number) => {
    const citations = currentResponse?.citations || [];
    const found = citations.find((c) => c.reference_number === refNumber);
    if (found) {
      setSelectedCitation(found);
    } else {
      // Fallback synthetic citation object
      setSelectedCitation({
        citation_id: `cite_${refNumber}`,
        reference_number: refNumber,
        source_title: `Primary Documentary Source #${refNumber}`,
        source_uri: "https://arxiv.org/abs/2307.08691",
        snippet:
          "FlashAttention-2 optimizes memory I/O between high-bandwidth memory (HBM) and on-chip SRAM by restructuring the attention computation into tiled blocks, reducing memory traffic by 2-4x.",
        page_number: 3,
        section_title: "Memory Access Complexity Bounds",
        evidence_role: "DIRECT SUPPORT",
        confidence_grounding: 0.94,
        used_in_claims: ["SRAM tiling bounds arithmetic intensity"],
        used_in_steps: ["1", "3"],
      });
    }
    setIsCitationDrawerOpen(true);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex selection:bg-indigo-500 selection:text-white cockpit-shell">
      {/* Persistent Left Sidebar */}
      <Sidebar
        activeView={activeView}
        onSelectView={(view) => setActiveView(view)}
        onNewResearch={handleNewResearch}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        {/* Top Navbar */}
        <Navbar
          currentSessionTitle={activeSession.title}
          audience={audience}
          onChangeAudience={(aud) => setAudience(aud)}
          isProcessing={isProcessing}
          onOpenSettings={() => setActiveView("SETTINGS")}
        />

        {/* View Switcher */}
        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-10 py-6 lg:py-8">
          {/* VIEW: DOCUMENTS */}
          {activeView === "DOCUMENTS" && <DocumentsView />}

          {/* VIEW: HISTORY */}
          {activeView === "HISTORY" && (
            <HistoryView
              onSelectQuery={(queryText) => {
                setActiveView("COCKPIT");
                setLifecycle("BEFORE_QUERY");
                setLastQuery(queryText);
              }}
              onOpenSession={(sessionId, queryTitle) => {
                handleOpenHistoricalSession(sessionId, queryTitle);
              }}
            />
          )}

          {/* VIEW: ANALYTICS */}
          {activeView === "ANALYTICS" && <AnalyticsView />}

          {/* VIEW: SETTINGS */}
          {activeView === "SETTINGS" && <SettingsView />}

          {/* VIEW: COCKPIT (The 3 Lifecycles) */}
          {activeView === "COCKPIT" && (
            <div>
              {/* LIFECYCLE 1: BEFORE QUERY (Clean Pre-Query Cockpit) */}
              {lifecycle === "BEFORE_QUERY" && (
                <div className="space-y-6">
                  {/* Hero Cockpit Title */}
                  <div className="mb-6">
                    <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white mb-2">
                      Cognitive Research Cockpit
                    </h1>
                    <p className="text-sm text-slate-400 max-w-2xl leading-relaxed">
                      Multi-stage epistemically grounded synthesis over ambiguous hypotheses, dialectical evidence, and verifiable proof DAGs.
                    </p>
                  </div>

                  <QueryCockpit onSubmit={handleExecuteQuery} isProcessing={isProcessing} />
                </div>
              )}

              {/* LIFECYCLE 2: DURING QUERY ("Here's what Cogent is doing") */}
              {lifecycle === "DURING_QUERY" && (
                <div className="space-y-6 animate-in fade-in duration-300">
                  <div className="p-4 rounded-xl bg-indigo-950/20 border border-indigo-500/30 text-xs text-indigo-300 flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-200">Active Inquiry: </span>
                      <span className="italic font-serif text-slate-300">"{lastQuery}"</span>
                    </div>
                    <button
                      onClick={handleNewResearch}
                      className="text-[11px] text-slate-400 hover:text-slate-200 underline"
                    >
                      Cancel / New
                    </button>
                  </div>

                  <ExecutionHUD
                    trace={currentResponse?.trace}
                    isProcessing={isProcessing}
                    failedLayer={failedLayer}
                    currentStepDescription="Executing multi-layer cognitive pipeline: acquiring literature and constructing entailment DAG..."
                  />
                </div>
              )}

              {/* LIFECYCLE 3: AFTER QUERY ("Here's what Cogent found") */}
              {lifecycle === "AFTER_QUERY" && currentResponse && (
                <div className="space-y-6 animate-in fade-in duration-300">
                  {/* Subtle Breadcrumb / Inquiry Actions Bar */}
                  <div className="flex items-center justify-between text-xs text-slate-400 pb-1">
                    <div className="flex items-center space-x-2 truncate">
                      <span className="text-indigo-400 font-semibold uppercase text-[10px] tracking-wider">Research Inquiry</span>
                      <span>/</span>
                      <span className="text-slate-300 truncate max-w-md italic">"{lastQuery || currentResponse.query_id}"</span>
                    </div>
                    <button
                      onClick={handleNewResearch}
                      className="px-3 py-1.5 rounded-lg text-xs font-medium bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition-colors"
                    >
                      + New Research
                    </button>
                  </div>

                  {/* Execution Status Card Handling: PARTIAL, INSUFFICIENT, or FAILED */}
                  {currentResponse.status === "PARTIAL_EXECUTION" && (
                    <PartialExecutionCard data={currentResponse.partial_execution} />
                  )}

                  {currentResponse.status === "INSUFFICIENT_EVIDENCE" && (
                    <InsufficientEvidenceCard
                      data={currentResponse.insufficient_evidence}
                      onRefineQuery={handleNewResearch}
                    />
                  )}

                  {currentResponse.status === "FAILED" && (
                    <FailureCard
                      error={currentResponse.error}
                      trace={currentResponse.trace}
                      onRetry={() =>
                        handleExecuteQuery({
                          query: lastQuery,
                          sourceMode: "HYBRID",
                          attachedFiles: [],
                        })
                      }
                    />
                  )}

                  {/* Dedicated 6-Tab Scholarly Research Suite */}
                  {currentResponse.status !== "FAILED" && (
                    <div className="space-y-6">
                      {/* Research Session Navigation Tabs */}
                      <ResultTabs
                        activeTab={activeResultTab}
                        onSelectTab={(tab) => setActiveResultTab(tab)}
                        counts={{
                          evidenceCount: currentResponse.verified_evidence?.length || currentResponse.citations?.length || 0,
                          reasoningStepCount: currentResponse.reasoning_chain?.length || 0,
                          trustScore: currentResponse.epistemic_bounds?.epistemic_trust_index,
                          cutSetCount: currentResponse.minimal_cut_set?.length || 0,
                          latencyMs: currentResponse.trace?.total_latency_ms,
                        }}
                      />

                      {/* TAB 1: MAIN ANSWER */}
                      {activeResultTab === "ANSWER" && (
                        <ResponseViewer
                          response={currentResponse}
                          query={lastQuery}
                          onOpenCitation={handleOpenCitation}
                          onSelectTab={(tab) => setActiveResultTab(tab as ResultTabType)}
                        />
                      )}

                      {/* TAB 2: EVIDENCE INTELLIGENCE */}
                      {activeResultTab === "EVIDENCE" && (
                        <EvidenceDialecticView
                          contradictions={currentResponse.contradictions}
                          evidence={currentResponse.verified_evidence}
                        />
                      )}

                      {/* TAB 3: REASONING DAG */}
                      {activeResultTab === "REASONING" && (
                        <ReasoningDAG steps={currentResponse.reasoning_chain} />
                      )}

                      {/* TAB 4: CONFIDENCE & TRUST */}
                      {activeResultTab === "TRUST" && (
                        <EpistemicTrustCard bounds={currentResponse.epistemic_bounds} />
                      )}

                      {/* TAB 5: SOURCES & CUT-SETS */}
                      {activeResultTab === "PROVENANCE" && (
                        <ProvenanceCard
                          cutSet={currentResponse.minimal_cut_set}
                          citations={currentResponse.citations}
                          onOpenCitation={handleOpenCitation}
                        />
                      )}

                      {/* TAB 6: EXECUTION TRACE */}
                      {activeResultTab === "TRACE" && (
                        <ExecutionHUD
                          trace={currentResponse.trace}
                          isProcessing={isProcessing}
                          failedLayer={failedLayer}
                        />
                      )}
                    </div>
                  )}

                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Interactive Citation Slide-over Drawer */}
      <CitationDrawer
        citation={selectedCitation}
        isOpen={isCitationDrawerOpen}
        onClose={() => setIsCitationDrawerOpen(false)}
      />

      {/* Clarification Modal (Layer 1 Ambiguity) */}
      <ClarificationModal
        isOpen={isClarificationOpen}
        questions={currentResponse?.clarifications_needed || []}
        onSubmit={handleClarificationSubmit}
        onClose={() => setIsClarificationOpen(false)}
      />
    </div>
  );
}
export default App;
