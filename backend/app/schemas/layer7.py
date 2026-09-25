"""
Layer 7: Trust Intelligence Layer Schemas
Grounded in 20 research papers across EMNLP 2025, ACL 2024-2026, IJCAI 2025, ACM Surveys 2026, Springer Sept 2026.
Defines typed contracts for source credibility, evidence reliability, reasoning chain trust,
separately tracked uncertainty components, calibrated confidence, and hallucination risk detection.
"""

from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace


class SourceTier(str, Enum):
    """
    Initial heuristic source classification tier.
    Research: RA-RAG (EMNLP 2025), Metzger & Flanagin (2013).
    """
    PEER_REVIEWED_PAPER = "PEER_REVIEWED_PAPER"
    PREPRINT = "PREPRINT"
    GOVERNMENT_OFFICIAL = "GOVERNMENT_OFFICIAL"
    TECHNICAL_DOCUMENTATION = "TECHNICAL_DOCUMENTATION"
    INSTITUTIONAL_REPORT = "INSTITUTIONAL_REPORT"
    NEWS_MEDIA = "NEWS_MEDIA"
    BLOG_POST = "BLOG_POST"
    FORUM_DISCUSSION = "FORUM_DISCUSSION"
    UNKNOWN = "UNKNOWN"


class UncertaintyCategory(str, Enum):
    """
    Categories of epistemic and observed uncertainty drivers.
    Research: FRANQ (ACL 2026), S2G-RAG (ACL 2026), Geng et al. (NAACL 2024).
    """
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    OUTDATED_EVIDENCE = "OUTDATED_EVIDENCE"
    WEAK_SOURCE = "WEAK_SOURCE"
    MISSING_PREMISE = "MISSING_PREMISE"
    LONG_REASONING_CHAIN = "LONG_REASONING_CHAIN"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    UNVERIFIED_INFERENCE = "UNVERIFIED_INFERENCE"


class HallucinationRiskType(str, Enum):
    """
    Taxonomy of hallucination and ungrounded overextension risks.
    Research: RAGTruth (ACL 2024), Evidence-Aligned Entity Verification (ACL 2026), RECV (ACL 2025).
    """
    EVIDENCE_OVEREXTENSION = "EVIDENCE_OVEREXTENSION"
    CITATION_MISMATCH = "CITATION_MISMATCH"
    REASONING_LEAP = "REASONING_LEAP"
    CONFLICT_IGNORED = "CONFLICT_IGNORED"
    UNSUPPORTED_GENERALIZATION = "UNSUPPORTED_GENERALIZATION"


class ConfidenceTier(str, Enum):
    """Categorized confidence rating for human interpretability."""
    HIGH = "HIGH"                  # >= 0.80
    MODERATE = "MODERATE"          # 0.60 - 0.79
    LOW = "LOW"                    # 0.40 - 0.59
    PROVISIONAL = "PROVISIONAL"    # < 0.40


class SourceCredibilityAssessment(BaseModel):
    """
    Source credibility assessment score based on predefined provenance and authority features.
    Research: RA-RAG (EMNLP 2025), CONFACT (IJCAI 2025).
    """
    source_id: str = Field(..., description="Unique source document or URI identifier")
    source_uri: str = Field(..., description="Source URL or file path")
    source_type: SourceTier = Field(..., description="Categorized source tier")
    domain: str = Field(..., description="Extracted domain or publisher authority")
    authority_score: float = Field(..., ge=0.0, le=1.0, description="Heuristic provenance and venue authority score")
    recency_score: float = Field(..., ge=0.0, le=1.0, description="Domain-aware temporal decay score exp(-lambda * delta_t)")
    corroboration_score: float = Field(0.0, ge=0.0, le=1.0, description="Cross-source consensus/corroboration fraction")
    overall_credibility: float = Field(..., ge=0.0, le=1.0, description="Composite source credibility assessment score")
    credibility_factors: List[str] = Field(default_factory=list, description="Descriptive rationale for credibility scoring")


class EvidenceReliabilityAssessment(BaseModel):
    """
    Evidence reliability audit evaluating claim-to-evidence faithfulness vs factuality.
    Research: FRANQ (ACL 2026), AwF (IJCNLP 2025), RLSeek (ACL 2026).
    """
    evidence_id: str = Field(..., description="Layer 5 EvidenceItem ID")
    claim_id: str = Field(..., description="Target claim ID being audited")
    directness_score: float = Field(..., ge=0.0, le=1.0, description="Directness vs circumstantial extrapolation score")
    alignment_score: float = Field(..., ge=0.0, le=1.0, description="Verbatim quote-span entailment alignment score")
    overall_reliability: float = Field(..., ge=0.0, le=1.0, description="Composite evidence reliability score")
    is_faithful: bool = Field(True, description="Whether claim is strictly entailed by retrieved evidence")
    unfaithfulness_details: Optional[str] = Field(None, description="Explanation of scope divergence if unfaithful")


class StepTrustScore(BaseModel):
    """
    Structural trust score for an individual reasoning step node in the Layer 6 DAG.
    Research: Confidence over Time (ACL 2026), RLSeek (ACL 2026).
    """
    step_id: str = Field(..., description="Layer 6 ReasoningStepNode ID")
    step_type: str = Field(..., description="Operation type, e.g. MULTI_HOP_INFERENCE, CONFLICT_RECONCILIATION")
    step_grounding_score: float = Field(..., ge=0.0, le=1.0, description="Premise grounding score from Layer 6")
    source_credibility_weight: float = Field(..., ge=0.0, le=1.0, description="Aggregated source credibility of step premises")
    computed_step_trust: float = Field(..., ge=0.0, le=1.0, description="Calibrated trust in this derivation step")
    dependency_vulnerability: float = Field(0.0, ge=0.0, le=1.0, description="Risk inherited from upstream dependent steps")


class ReasoningTrustAssessment(BaseModel):
    """
    Structural trust analysis across the entire Layer 6 reasoning DAG.
    Research: Confidence over Time (ACL 2026), Weakest Link (ACL 2026).
    """
    step_trust_scores: List[StepTrustScore] = Field(default_factory=list)
    weakest_link_step_id: str = Field(..., description="ID of the weakest step in the derivation graph")
    weakest_link_score: float = Field(..., ge=0.0, le=1.0, description="Minimum step trust along derivation DAG")
    average_chain_trust: float = Field(..., ge=0.0, le=1.0, description="Mean trust across all reasoning steps")
    path_trust_score: float = Field(..., ge=0.0, le=1.0, description="Longest derivation path trust discounted by depth decay")
    is_chain_intact: bool = Field(True, description="True if all necessary inferential dependencies hold")


class ClaimConfidenceAssessment(BaseModel):
    """
    Granular, claim-level calibrated confidence assessment.
    Research: CLAIM-CAL (Springer Sept 2026), APRICOT (ACL 2024).
    """
    claim_id: str = Field(..., description="Layer 6 SynthesizedClaim ID or Layer 5 AtomicClaim ID")
    statement: str = Field(..., description="Verbatim claim proposition statement")
    raw_confidence: float = Field(..., ge=0.0, le=1.0, description="Uncalibrated feature-weighted confidence score")
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0, description="Estimated calibrated confidence probability")
    confidence_tier: ConfidenceTier = Field(..., description="Human-interpretable tier: HIGH, MODERATE, LOW, PROVISIONAL")
    primary_trust_drivers: List[str] = Field(default_factory=list, description="Key factors elevating confidence")
    primary_uncertainty_drivers: List[str] = Field(default_factory=list, description="Key factors depressing confidence")


class HallucinationRiskAssessment(BaseModel):
    """
    Audit for evidence overextension, ungrounded universal claims, and reasoning leaps.
    Research: RAGTruth (ACL 2024), Evidence-Aligned Entity Verification (ACL 2026).
    """
    has_hallucination_risk: bool = Field(False, description="True if any overextension or ungrounded leap is flagged")
    risk_level: str = Field("NONE", description="NONE, LOW, MEDIUM, HIGH, CRITICAL")
    detected_risks: List[HallucinationRiskType] = Field(default_factory=list)
    risk_explanations: List[str] = Field(default_factory=list)


class UncertaintyAssessment(BaseModel):
    """
    Tracking of five separate uncertainty components.
    Research: FRANQ (ACL 2026), S2G-RAG (ACL 2026).
    """
    overall_uncertainty: float = Field(..., ge=0.0, le=1.0, description="Composite aggregate uncertainty metric")
    active_uncertainties: List[UncertaintyCategory] = Field(default_factory=list, description="All identified active uncertainty drivers")
    epistemic_uncertainty_ratio: float = Field(..., ge=0.0, le=1.0, description="Fraction stemming from missing/insufficient evidence")
    aleatoric_uncertainty_ratio: float = Field(..., ge=0.0, le=1.0, description="Fraction stemming from observed variability/divergence")
    explanation_of_uncertainty: str = Field(..., description="Diagnostic explanation of why uncertainty exists")


class TrustAssessment(BaseModel):
    """
    Master Output Contract emitted by Layer 7 (Trust Intelligence) and consumed by Layer 8 (Explainability & Attribution).
    Research: Towards Trustworthy RAG Survey (Ni et al., ACM Computing Surveys 2026).
    """
    assessment_id: str = Field(..., description="Unique trust assessment UUID")
    plan_id: str = Field(..., description="Layer 2 KnowledgeRetrievalPlan ID")
    session_id: str = Field(..., description="User session UUID")
    reasoning_trace_id: str = Field(..., description="Layer 6 SynthesizedReasoningTrace ID")
    
    global_trust_index: float = Field(
        ..., ge=0.0, le=1.0,
        description="Overall structural trust assessment index based on provenance, reasoning integrity, and evidence reliability (Trust Index != Confidence Probability)"
    )
    global_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Estimated global confidence bounded by weakest link"
    )
    confidence_tier: Optional[ConfidenceTier] = Field(None, description="Global confidence tier")
    is_safe_for_decision_support: Optional[bool] = Field(None, description="Safety flag for downstream consumers")
    
    claim_assessments: List[ClaimConfidenceAssessment] = Field(default_factory=list, description="Claim-level confidence assessments")
    source_assessments: List[SourceCredibilityAssessment] = Field(default_factory=list, description="Source credibility evaluations")
    evidence_assessments: List[EvidenceReliabilityAssessment] = Field(default_factory=list, description="Evidence faithfulness audits")
    reasoning_assessment: ReasoningTrustAssessment = Field(..., description="Reasoning DAG trust evaluation")
    uncertainty_assessment: UncertaintyAssessment = Field(..., description="Separately tracked uncertainty components")
    hallucination_assessment: HallucinationRiskAssessment = Field(..., description="Hallucination and scope overextension audit")
    
    key_trust_strengths: List[str] = Field(default_factory=list, description="Summary of positive trust factors")
    key_limitations: List[str] = Field(default_factory=list, description="Summary of caveats, gaps, and risks")
    processing_time_ms: float = Field(..., description="Total Layer 7 latency in ms")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Layer7DirectRequest(BaseModel):
    """Direct invocation request payload for Layer 7 API."""
    reasoning_trace: SynthesizedReasoningTrace = Field(..., description="Layer 6 SynthesizedReasoningTrace")
    evidence_set: VerifiedEvidenceSet = Field(..., description="Layer 5 VerifiedEvidenceSet")
    plan: KnowledgeRetrievalPlan = Field(..., description="Layer 2 KnowledgeRetrievalPlan")


class Layer7Response(BaseModel):
    """API response envelope for Layer 7 endpoints."""
    status: str = "SUCCESS"
    trust_assessment: TrustAssessment
    warnings: List[str] = Field(default_factory=list)
