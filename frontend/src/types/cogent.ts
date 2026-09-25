/**
 * Cogent Research Platform - Comprehensive Type System
 * Supports 3 Lifecycles: Before Query, During Query, and After Query
 * Adheres strictly to API_VERSION = "v1" and SCHEMA_VERSION = "1.0.0"
 */

export const API_VERSION = "v1";
export const SCHEMA_VERSION = "1.0.0";

export type ExecutionStatus =
  | "IDLE"
  | "PROCESSING"
  | "SUCCESS"
  | "PARTIAL_EXECUTION"
  | "FAILED"
  | "CLARIFICATION_REQUIRED"
  | "INSUFFICIENT_EVIDENCE";

export type SourceMode = "DOCUMENTS" | "LIVE_WEB" | "HYBRID";

export type AudienceFidelity = "EXECUTIVE" | "TECHNICAL" | "LAYPERSON" | "EXPERT";

export type ActiveView = "COCKPIT" | "DOCUMENTS" | "HISTORY" | "ANALYTICS" | "SETTINGS";

export interface AttachedFile {
  id: string;
  name: string;
  size: number;
  type: string;
  status: "UPLOADED" | "INDEXED" | "PROCESSING";
  file?: File;
}

export interface ResearchBrief {
  objective: string;
  information_needed: string[];
  sources: string[];
  constraints: string[];
}

export interface ClarificationQuestion {
  clarification_id: string;
  dimension: string;
  question: string;
  options: string[];
  reason: string;
}

export interface DialecticalContradiction {
  contradiction_id: string;
  topic: string;
  claim_a: string;
  source_a: string;
  confidence_a: number;
  claim_b: string;
  source_b: string;
  confidence_b: number;
  reconciliation_heuristic: string;
  resolution_status:
    | "RECONCILED"
    | "CONTEXTUAL_DIFFERENCE"
    | "PARTIALLY_RECONCILED"
    | "UNRESOLVED"
    | "INSUFFICIENT_EVIDENCE";
  is_empirical_stalemate: boolean;
  contextual_factors?: string[];
}

export interface EvidenceVerificationCard {
  evidence_id: string;
  document_title: string;
  source_uri: string;
  snippet: string;
  relevance_score: number;
  entailment_status: "ENTAILS" | "CONTRADICTS" | "NEUTRAL";
  verification_confidence: number;
  evidence_role?: "DIRECT SUPPORT" | "BACKGROUND" | "CONTEXTUAL";
  provenance_breadcrumbs?: {
    page?: number;
    section?: string;
    hash?: string;
  };
}

export interface ReasoningStep {
  step_id: string;
  step_index: number;
  operation: "DEDUCTION" | "INDUCTION" | "ABDUCTION" | "ANALOGY" | "DECOMPOSITION" | "SYNTHESIS";
  premises: string[];
  conclusion: string;
  supporting_evidence_ids: string[];
  opposing_evidence_ids?: string[];
  reasoning_status: "VALID" | "CONTINGENT" | "DISPUTED" | "UNVERIFIED";
  dependent_steps?: string[];
  caveats?: string;
  notes?: string;
}

export interface EpistemicBounds {
  epistemic_trust_index: number; // 0.0 - 1.0
  evidence_coverage: number;
  source_uncertainty: number;
  temporal_uncertainty: number;
  reasoning_uncertainty: number;
  conflict: number;
  trust_status: "HIGH_CONFIDENCE" | "MODERATE_CONFIDENCE" | "CONDITIONAL" | "UNGROUNDED";
  uncertainty_drivers: string[];
}

export interface MinimalCutSetItem {
  claim_id?: string;
  claim_text: string;
  critical_premises: string[];
  pivotal_sources: string[];
  is_vulnerable_to_single_source_failure: boolean;
  sensitivity_notes?: string;
}

export interface CitationReference {
  citation_id: string;
  reference_number: number;
  source_title: string;
  source_uri: string;
  snippet: string;
  page_number?: number;
  section_title?: string;
  evidence_role?: "DIRECT SUPPORT" | "BACKGROUND" | "CONTEXTUAL";
  used_in_claims?: string[];
  used_in_steps?: string[];
  confidence_grounding: number;
}

export interface ClaimItem {
  claim_id: string;
  text: string;
  status: "ESTABLISHED" | "INFERRED" | "DIALECTICAL" | "CONDITIONAL" | "UNRESOLVED";
  citation_ids: string[];
}

export interface InsufficientEvidenceData {
  summary: string;
  candidates_found: number;
  what_we_found: string[];
  what_is_missing: string[];
  what_can_be_concluded: string;
  what_cannot_be_concluded: string;
  suggested_next_steps: string[];
}

export interface PartialExecutionData {
  completed_layers: { id: number; name: string }[];
  failed_layer: { id: number; name: string; reason: string };
  available_findings_summary: string;
}

export interface CogentExecutionTrace {
  id: string;
  query_id: string;
  execution_status: ExecutionStatus;
  failure_code?: string | null;
  failure_message?: string | null;
  failed_layer?: number | null;
  started_at: string;
  completed_at?: string | null;
  total_latency_ms: number;
  layer_telemetry: Record<
    string,
    {
      layer_name: string;
      latency_ms: number;
      status: string;
      summary?: string;
      details?: Record<string, any>;
    }
  >;
}

export interface CogentQueryResponse {
  api_version: string;
  schema_version: string;
  query_id: string;
  session_id: string;
  query?: string;
  rendered_content: string;
  bluf_summary?: string;
  status: ExecutionStatus;
  research_brief?: ResearchBrief;
  claims?: ClaimItem[];
  clarifications_needed?: ClarificationQuestion[];
  contradictions?: DialecticalContradiction[];
  verified_evidence?: EvidenceVerificationCard[];
  reasoning_chain?: ReasoningStep[];
  epistemic_bounds?: EpistemicBounds;
  minimal_cut_set?: MinimalCutSetItem[];
  citations?: CitationReference[];
  insufficient_evidence?: InsufficientEvidenceData;
  partial_execution?: PartialExecutionData;
  trace?: CogentExecutionTrace;
  error?: {
    code: string;
    message: string;
    failed_layer: number;
  };
}

export interface DocumentRecord {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  status: "ACQUIRED" | "READY_FOR_RETRIEVAL" | "FAILED";
  indexing_status: "PENDING" | "INDEXED" | "FAILED";
  chunk_count: number;
  total_characters?: number;
  upload_date?: string;
}

export interface SessionRecord {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  query_count: number;
  last_query_preview?: string;
}
