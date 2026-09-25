"""
Layer 6 Data Contracts: Transparent Reasoning & Synthesis
Research Basis:
- TRACE (EMNLP Findings 2024): Knowledge-grounded reasoning chains
- Dalvi et al. (EMNLP 2021) & Bostrom et al. (ACL 2022): Entailment Trees (P1 + P2 => IC)
- SR-RAG (ACL Findings 2026): Verifiable symbolic reasoning steps
- MAGIC (EMNLP Findings 2025) & ConfRAG (ACL 2026): Dialectical conflict reconciliation & Zero Winner Forcing
- S2G-RAG (ACL 2026): Epistemic gap bounding and insufficiency hedges
- ROSCOE (ICLR 2023) & Weakest Link (ACL 2026): Objective step diagnostics exported to Layer 7
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.schemas.layer1 import StructuredUserInput
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet, ConflictSeverity


class ReasoningStepType(str, Enum):
    """Classification of inferential transition operations in the reasoning trace."""
    EVIDENCE_LINK = "EVIDENCE_LINK"                    # Direct anchoring of atomic claim to sub-query
    CLAIM_COMBINATION = "CLAIM_COMBINATION"            # Conjunction of atomic claims
    MULTI_HOP_INFERENCE = "MULTI_HOP_INFERENCE"        # Entailment deduction (P1 + P2 => Intermediate Conclusion)
    COMPARISON = "COMPARISON"                          # Multi-attribute comparison across entities
    CAUSAL_ANALYSIS = "CAUSAL_ANALYSIS"                # Cause -> Mechanism -> Effect deduction
    CONFLICT_ANALYSIS = "CONFLICT_ANALYSIS"            # Diagnosing origin of contradiction
    CONFLICT_RECONCILIATION = "CONFLICT_RECONCILIATION"# Dialectical synthesis explaining discrepancy
    TRADEOFF_ANALYSIS = "TRADEOFF_ANALYSIS"            # Pareto / multi-criteria trade-off evaluation
    EPISTEMIC_HEDGE = "EPISTEMIC_HEDGE"                # Explicit boundary / missing information caveat
    CONCLUSION = "CONCLUSION"                          # Final synthesized derivation


class ResolutionStatus(str, Enum):
    """Outcome status of dialectical conflict reconciliation (MAGIC 2025)."""
    RECONCILED = "RECONCILED"                          # Discrepancy fully explained by differing conditions
    CONTEXTUAL_DIFFERENCE = "CONTEXTUAL_DIFFERENCE"     # Differing benchmark, dataset, or environment
    TEMPORAL_SUPERSEDENCE = "TEMPORAL_SUPERSEDENCE"     # Later empirical finding supersedes earlier one
    PARTIALLY_RECONCILED = "PARTIALLY_RECONCILED"       # Partial explanation; residual variance persists
    GENUINE_CONTRADICTION = "GENUINE_CONTRADICTION"     # Unresolved empirical disagreement (Zero Winner Forcing)
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"     # Not enough metadata to diagnose cause


class SynthesisStatus(str, Enum):
    """Derivation state of a synthesized claim."""
    GROUNDED_DEDUCTION = "GROUNDED_DEDUCTION"          # Strictly entailed by grounded premises
    DIALECTICAL_SYNTHESIS = "DIALECTICAL_SYNTHESIS"    # Reconciled synthesis of opposing views
    CONDITIONAL_CONCLUSION = "CONDITIONAL_CONCLUSION"  # Valid under specific condition / criterion
    EPISTEMIC_HEDGE = "EPISTEMIC_HEDGE"                # Explicit statement of what cannot be concluded


class ReasoningStepNode(BaseModel):
    """
    Symbolic node in the Entailment Reasoning DAG (Dalvi et al. 2021, SR-RAG 2026).
    Represents an explicit inferential step connecting premises to an intermediate conclusion.
    """
    step_id: str = Field(..., description="Unique step identifier, e.g. step_0, step_1")
    step_index: int = Field(..., description="Topological execution order index")
    step_type: ReasoningStepType = Field(..., description="Inferential operation type")
    sub_query_id: Optional[str] = Field(None, description="Associated Layer 2 sub-query ID if applicable")
    premise_claim_ids: List[str] = Field(default_factory=list, description="IDs of Layer 5 AtomicClaims acting as premises")
    evidence_ids: List[str] = Field(default_factory=list, description="IDs of Layer 5 EvidenceItems supporting this step")
    dependent_step_ids: List[str] = Field(default_factory=list, description="IDs of preceding ReasoningStepNodes required by this step")
    reasoning_operation: str = Field(..., description="Formal description of inference operation performed")
    intermediate_claim: str = Field(..., description="The deduced factual or synthesized proposition")
    supporting_claim_ids: List[str] = Field(default_factory=list, description="Claim IDs corroborating this step")
    opposing_claim_ids: List[str] = Field(default_factory=list, description="Claim IDs contradicting this step")
    unresolved_issues: List[str] = Field(default_factory=list, description="Caveats or unverified assumptions")
    step_grounding_score: float = Field(1.0, ge=0.0, le=1.0, description="Minimum premise grounding score (Weakest Link)")


class SynthesizedClaim(BaseModel):
    """
    A verified, logically synthesized claim derived from multiple premises.
    Maintains zero-winner-forcing attribution to both supporting and opposing evidence.
    """
    claim_id: str = Field(..., description="Unique synthesized claim ID, e.g. syn_clm_1")
    statement: str = Field(..., description="Clear proposition statement")
    status: SynthesisStatus = Field(..., description="Status of the synthesized claim")
    source_claim_ids: List[str] = Field(default_factory=list, description="Layer 5 AtomicClaim IDs used in derivation")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Layer 5 EvidenceItem IDs supporting claim")
    opposing_evidence_ids: List[str] = Field(default_factory=list, description="Layer 5 EvidenceItem IDs contradicting claim")
    derivation_step_ids: List[str] = Field(default_factory=list, description="ReasoningStepNode IDs leading to this claim")
    caveats: List[str] = Field(default_factory=list, description="Condition bounds, dataset limits, or temporal notes")


class ConflictReconciliation(BaseModel):
    """
    Structured dialectical resolution of a contradiction detected by Layer 5 (MAGIC 2025, ConfRAG 2026).
    Enforces strict Zero Winner Forcing.
    """
    reconciliation_id: str = Field(..., description="Unique reconciliation ID, e.g. rec_1")
    conflict_edge_id: str = Field(..., description="Layer 5 ConflictEdge ID")
    claim_a_id: str = Field(..., description="ID of first conflicting atomic claim")
    claim_b_id: str = Field(..., description="ID of second conflicting atomic claim")
    claim_a_text: str = Field(..., description="Text of Claim A")
    claim_b_text: str = Field(..., description="Text of Claim B")
    severity: ConflictSeverity = Field(..., description="Severity inherited from Layer 5")
    resolution_status: ResolutionStatus = Field(..., description="Diagnostic resolution category")
    contextual_factors: List[str] = Field(default_factory=list, description="Identified conditions explaining discrepancy (datasets, metrics, dates)")
    reconciliation_analysis: str = Field(..., description="Dialectical explanation of why claims diverge without picking a winner")
    supporting_evidence_ids: List[str] = Field(default_factory=list, description="Evidence IDs backing Claim A and Claim B")
    source_a_title: Optional[str] = Field(None, description="Actual publication title or domain for Position A")
    source_b_title: Optional[str] = Field(None, description="Actual publication title or domain for Position B")


class ComparativeDimension(BaseModel):
    """Evaluation cell in an Entity x Criterion comparison matrix (Zhou et al. 2023)."""
    criterion: str = Field(..., description="Comparison dimension, e.g. 'Latency', 'Accuracy', 'Memory'")
    entity_evaluations: Dict[str, str] = Field(default_factory=dict, description="Entity name -> extracted metric/finding")
    tradeoff_summary: str = Field(..., description="Comparative deduction along this criterion")
    supporting_claim_ids: List[str] = Field(default_factory=list)


class ReasoningIntegrityMetrics(BaseModel):
    """
    Raw structural diagnostics exported strictly for Layer 7 Trust Intelligence (ROSCOE 2023, Weakest Link 2026).
    NOTE: These are diagnostic signals, NOT proof of truth or user-facing confidence scores.
    """
    total_reasoning_steps: int = Field(0, description="Total steps in reasoning graph")
    premises_grounded_ratio: float = Field(1.0, ge=0.0, le=1.0, description="Grounded premises / total premises")
    claim_support_ratio: float = Field(1.0, ge=0.0, le=1.0, description="Supporting claims / (supporting + opposing) - evidence balance diagnostic")
    conflict_reconciliation_ratio: float = Field(1.0, ge=0.0, le=1.0, description="Reconciled conflicts / total conflicts")
    weakest_link_score: float = Field(1.0, ge=0.0, le=1.0, description="Minimum premise grounding score in the derivation DAG")
    epistemic_gap_count: int = Field(0, description="Number of unresolved information gaps identified")
    logical_chain_depth: int = Field(1, description="Longest topological path in the reasoning DAG")
    has_unresolved_contradictions: bool = Field(False, description="Whether irreconcilable contradictions remain")


class SynthesizedReasoningTrace(BaseModel):
    """
    Standardized typed contract outputted by Layer 6 and consumed by Layer 7 (Trust Intelligence).
    Contains the complete proof-like reasoning graph and dialectical synthesis.
    """
    reasoning_trace_id: str = Field(..., description="Unique reasoning trace UUID")
    plan_id: str = Field(..., description="Layer 2 KnowledgeRetrievalPlan ID")
    session_id: str = Field(..., description="User session UUID")
    evidence_set_id: str = Field(..., description="Layer 5 VerifiedEvidenceSet ID")
    query_intent: str = Field(..., description="User intent from Layer 1 (e.g. FACTUAL, COMPARATIVE)")
    
    # 1. Structural Reasoning DAG & Steps
    reasoning_steps: List[ReasoningStepNode] = Field(default_factory=list, description="Topological sequence of reasoning steps")
    synthesized_claims: List[SynthesizedClaim] = Field(default_factory=list, description="Derived and reconciled claims")
    
    # 2. Conflict Handling (Zero Winner Forcing)
    conflict_reconciliations: List[ConflictReconciliation] = Field(default_factory=list, description="Dialectical explanations of all Layer 5 conflicts")
    has_conflicts: bool = Field(False, description="Whether conflicts were present in evidence")
    
    # 3. Comparative Matrix (for Comparative / Decision queries)
    comparative_matrix: List[ComparativeDimension] = Field(default_factory=list, description="Entity x Criterion matrix")
    
    # 4. Epistemic Gap Hedges
    unresolved_hedges: List[str] = Field(default_factory=list, description="Explicit caveats bounding what cannot be derived")
    unresolved_information_gaps: List[str] = Field(default_factory=list, description="Information gaps inherited from Layer 5")
    
    # 5. Synthesis Summary & Diagnostics
    final_synthesis_statement: str = Field(..., description="Formal logical derivation statement (for Layer 7/8, not final UI report)")
    is_reasoning_complete: bool = Field(True, description="Whether reasoning is logically complete or hedged")
    integrity_metrics: ReasoningIntegrityMetrics = Field(..., description="Raw structural diagnostics for Layer 7")
    processing_time_ms: float = Field(..., description="Total Layer 6 latency in ms")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Layer6DirectRequest(BaseModel):
    """Direct invocation payload for Layer 6 API."""
    evidence_set: VerifiedEvidenceSet = Field(..., description="Layer 5 VerifiedEvidenceSet")
    plan: KnowledgeRetrievalPlan = Field(..., description="Layer 2 KnowledgeRetrievalPlan")
    user_input: Optional[StructuredUserInput] = Field(None, description="Layer 1 StructuredUserInput")


class Layer6Response(BaseModel):
    """API response envelope for Layer 6 endpoints."""
    status: str = "SUCCESS"
    reasoning_trace: SynthesizedReasoningTrace
    warnings: List[str] = Field(default_factory=list)
