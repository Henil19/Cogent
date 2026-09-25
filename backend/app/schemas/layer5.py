"""
Layer 5 Pydantic Schemas
Contracts for Evidence Intelligence & Conflict Resolution Layer.
Research basis:
- Alt et al. (EACL 2026): User-Centric Evidence Ranking & sufficiency vs. redundancy
- Lee et al. (SetR, ACL 2025): Set-wise collective evidence selection
- Malviya & Katsigiannis (EMNLP 2024): Multi-stage cross-encoder evidence reranking
- Lu et al. (ACL 2025) & Hu et al. (NAACL 2025): Proposition atomicity & quality gating
- Ye et al. (ACL 2026) & Huang et al. (RLSeek, ACL 2026): Grounded NLI verification & quote extraction
- Verma et al. (ReflectiveRAG, EACL 2026): 4-tier deduplication & redundancy reduction
- Yuan et al. (ConfRAG, ACL 2026) & Ge et al. (CONFACT, IJCAI 2025): Contradiction detection & conflict graphs with Zero Winner Forcing
- S2G-RAG (ACL 2026): Structured sufficiency & missing information gap diagnostics
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer3 import SourceType
from app.schemas.layer4 import RetrievedCandidate, RetrievedCandidateSet


class GroundingStatus(str, Enum):
    """NLI-style grounding state for claims and evidence."""
    ENTAILMENT = "ENTAILMENT"
    NEUTRAL = "NEUTRAL"
    CONTRADICTION = "CONTRADICTION"


class DuplicateType(str, Enum):
    """4-tier evidence redundancy classification."""
    EXACT = "EXACT"
    NEAR = "NEAR"
    SEMANTIC = "SEMANTIC"
    OVERLAPPING_CHUNK = "OVERLAPPING_CHUNK"


class ConflictSeverity(str, Enum):
    """Categorization of evidence contradiction severity."""
    DIRECT_FACTUAL = "DIRECT_FACTUAL"          # Direct opposing claims, e.g. 92% vs 88%
    TEMPORAL_DIVERGENCE = "TEMPORAL_DIVERGENCE" # Difference caused by different dates
    METHODOLOGICAL = "METHODOLOGICAL"           # Different benchmarks or test setups
    PARTIAL_DISAGREEMENT = "PARTIAL_DISAGREEMENT"


class AtomicClaim(BaseModel):
    """
    Independently verifiable proposition extracted from a retrieved candidate passage.
    Research: Lu et al. (ACL 2025), Hu et al. (NAACL 2025), FActScore (Min et al. 2023).
    """
    claim_id: str = Field(..., description="Unique claim identifier, e.g. clm_abc123_1")
    parent_chunk_id: str = Field(..., description="Parent chunk UUID from Layer 3/4")
    candidate_id: str = Field(..., description="Parent candidate identifier from Layer 4")
    claim_text: str = Field(..., description="Decontextualized, standalone proposition text")
    
    # Grounding & Verification (Ye et al. 2026, RLSeek 2026)
    grounding_status: GroundingStatus = Field(GroundingStatus.NEUTRAL, description="ENTAILMENT, NEUTRAL, CONTRADICTION")
    grounding_score: float = Field(0.0, ge=0.0, le=1.0, description="Verification confidence score")
    quote_span: Optional[str] = Field(None, description="Exact verbatim supporting quote from chunk")
    is_atomic: bool = Field(True, description="Passed atomicity quality gate")
    
    # Proposition Triplet Components (FActScore EMNLP 2023)
    subject: Optional[str] = None
    predicate: Optional[str] = None
    target_value: Optional[str] = None


class EvidenceItem(BaseModel):
    """
    Structured evidence unit selected and verified by Layer 5.
    Preserves all provenance breadcrumbs for Layer 7 Trust Intelligence.
    """
    evidence_id: str = Field(..., description="Unique evidence UUID, e.g. ev_1a2b3c")
    candidate_id: str = Field(..., description="Source candidate identifier from Layer 4")
    chunk_id: str = Field(..., description="Corpus chunk ID from Layer 3")
    document_id: str = Field(..., description="Origin document ID from Layer 3")
    sub_query_id: str = Field(..., description="Target sub-query from Layer 2 plan")

    content: str = Field(..., description="Cleaned chunk text content")
    title: str = Field(..., description="Document or section title")
    source_uri: str = Field(..., description="Source URL or file path")
    source_type: SourceType = Field(..., description="Source category (e.g. LOCAL_PDF, LIVE_WEB)")

    # Scoring & Reranking (Malviya & Katsigiannis 2024)
    similarity_score: float = Field(..., description="Layer 4 dense/fused similarity score")
    rerank_score: float = Field(..., ge=0.0, le=1.0, description="Layer 5 cross-encoder deep relevance score")

    # Atomic Grounding
    atomic_claims: List[AtomicClaim] = Field(default_factory=list, description="Extracted atomic propositions")
    overall_grounding: GroundingStatus = Field(GroundingStatus.NEUTRAL, description="Aggregated chunk grounding status")

    # Deduplication & Conflict Participation
    duplicate_group_id: Optional[str] = Field(None, description="Group ID if part of a duplicate cluster")
    conflict_group_ids: List[str] = Field(default_factory=list, description="Conflict IDs if involved in contradictions")

    # TROVE Provenance Breadcrumbs (preserved for Layer 7 Trust Intelligence)
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    paragraph_start: Optional[int] = None
    paragraph_end: Optional[int] = None
    has_table: bool = False
    has_equation: bool = False
    document_hash: str = Field(..., description="SHA-256 hash of original document")
    content_hash: str = Field(..., description="SHA-256 hash of chunk content")
    retrieved_at: str = Field(..., description="ISO 8601 acquisition timestamp")
    author: Optional[str] = None
    publication_date: Optional[str] = None


class ConflictEdge(BaseModel):
    """
    Explicit edge in the contradiction graph between two opposing claims/evidence items.
    Research: ConfRAG (ACL 2026), CONFACT (IJCAI 2025).
    Zero Winner Forcing: Both sides are preserved without premature pruning.
    """
    conflict_id: str = Field(..., description="Unique conflict UUID, e.g. cfl_xyz789")
    claim_a_id: str = Field(..., description="First conflicting claim ID")
    claim_b_id: str = Field(..., description="Second conflicting claim ID")
    evidence_a_id: str = Field(..., description="First conflicting evidence ID")
    evidence_b_id: str = Field(..., description="Second conflicting evidence ID")
    conflict_description: str = Field(..., description="Explanation of contradiction")
    severity: ConflictSeverity = Field(ConflictSeverity.DIRECT_FACTUAL, description="Direct, temporal, or methodological")
    conflicting_aspect: str = Field(..., description="Focal parameter in conflict (e.g. accuracy, latency, date)")


class EvidenceGroup(BaseModel):
    """
    Consolidated group of duplicate or redundant evidence items.
    Research: Alt et al. (EACL 2026), ReflectiveRAG (EACL 2026).
    """
    group_id: str = Field(..., description="Unique duplicate group UUID")
    canonical_evidence_id: str = Field(..., description="Primary reference evidence item in group")
    member_evidence_ids: List[str] = Field(default_factory=list, description="All duplicate evidence IDs in cluster")
    duplicate_type: DuplicateType = Field(..., description="EXACT, NEAR, SEMANTIC, or OVERLAPPING_CHUNK")
    claim_summary: str = Field(..., description="Summary of the shared proposition")


class CoverageDimension(BaseModel):
    """Status of an individual information need dimension from Layer 2 plan."""
    dimension_name: str = Field(..., description="Target dimension, entity, or criterion")
    is_covered: bool = Field(False, description="True if verified evidence addresses this dimension")
    covering_evidence_ids: List[str] = Field(default_factory=list, description="Evidence items addressing dimension")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="Evidence sufficiency confidence")


class VerifiedEvidenceSet(BaseModel):
    """
    Standardized typed contract outputted by Layer 5
    and consumed directly by Layer 6 (Transparent Reasoning & Synthesis).
    """
    evidence_set_id: str = Field(..., description="Unique evidence set UUID")
    plan_id: str = Field(..., description="Associated Layer 2 plan ID")
    session_id: str = Field(..., description="User session UUID")

    # Selected High-Utility Evidence Items (SetR, ACL 2025)
    selected_evidence: List[EvidenceItem] = Field(default_factory=list, description="Verified non-redundant evidence")
    total_candidates_evaluated: int = Field(0, description="Total candidates received from Layer 4")
    selected_evidence_count: int = Field(0, description="Number of items selected for reasoning")

    # Structured Conflict Graph (ConfRAG, ACL 2026 - Zero Winner Forcing)
    conflict_edges: List[ConflictEdge] = Field(default_factory=list, description="Contradiction edges")
    has_conflicts: bool = Field(False, description="True if at least one contradiction was detected")

    # Deduplication Consolidation (Alt et al. 2026)
    duplicate_groups: List[EvidenceGroup] = Field(default_factory=list, description="Consolidated duplicate clusters")

    # Coverage & Gap Analysis (S2G-RAG, ACL 2026)
    coverage_map: Dict[str, CoverageDimension] = Field(default_factory=dict, description="Per-dimension coverage map")
    overall_coverage_ratio: float = Field(1.0, ge=0.0, le=1.0, description="Fraction of dimensions covered")
    unresolved_information_gaps: List[str] = Field(default_factory=list, description="Missing evidence dimensions")
    is_sufficient_for_reasoning: bool = Field(True, description="True if coverage meets minimum sufficiency")

    # Performance & Lineage
    processing_time_ms: float = Field(..., description="Layer 5 total duration in ms")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Layer5DirectRequest(BaseModel):
    """Direct request payload for invoking Layer 5."""
    candidate_set: RetrievedCandidateSet = Field(..., description="Layer 4 RetrievedCandidateSet")
    plan: KnowledgeRetrievalPlan = Field(..., description="Layer 2 KnowledgeRetrievalPlan for context")
    max_evidence_count: int = Field(10, ge=1, le=50, description="Maximum evidence items to select")
    rerank_threshold: float = Field(0.30, ge=0.0, le=1.0, description="Minimum cross-encoder rerank score")


class Layer5Response(BaseModel):
    """Response envelope for Layer 5 API endpoints."""
    status: str = "SUCCESS"
    evidence_set: VerifiedEvidenceSet
    warnings: List[str] = Field(default_factory=list)
