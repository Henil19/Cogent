"""
Pydantic Schemas and Contracts for Layer 8: Dynamic Explainability & Attribution Layer
Defines data structures for claim attribution, citation mapping, DAG narrative steps,
counterfactual sensitivity, uncertainty explanations, multi-fidelity narratives,
explanation validation, and the final ExplanationPackage.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ExplanationAudience(str, Enum):
    EXECUTIVE = "EXECUTIVE"
    TECHNICAL_RESEARCHER = "TECHNICAL_RESEARCHER"
    LAYPERSON = "LAYPERSON"
    DOMAIN_EXPERT = "DOMAIN_EXPERT"


class AttributionRole(str, Enum):
    DIRECT_SUPPORT = "DIRECT_SUPPORT"
    METHODOLOGICAL_QUALIFIER = "METHODOLOGICAL_QUALIFIER"
    OPPOSING_CONTRADICTION = "OPPOSING_CONTRADICTION"
    BACKGROUND_CONTEXT = "BACKGROUND_CONTEXT"


class ExplanationFidelityStatus(str, Enum):
    FULLY_FAITHFUL = "FULLY_FAITHFUL"
    MINOR_QUALIFIER_MISMATCH = "MINOR_QUALIFIER_MISMATCH"
    UNFAITHFUL_DETECTED = "UNFAITHFUL_DETECTED"


class SensitivitySeverity(str, Enum):
    CRITICAL_COLLAPSE = "CRITICAL_COLLAPSE"
    MODERATE_REVISION = "MODERATE_REVISION"
    LOCALIZED_REDUCTION = "LOCALIZED_REDUCTION"
    INSENSITIVE = "INSENSITIVE"


class EvidenceAttribution(BaseModel):
    """
    Fine-grained attribution connecting a claim to a specific evidence chunk and TROVE provenance.
    """
    evidence_id: str
    claim_id: str
    source_id: str
    document_id: str
    source_title: str
    source_uri: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    paragraph_start: Optional[int] = None
    paragraph_end: Optional[int] = None
    citation_token: str                      # e.g., "[C1-E1]"
    verbatim_quote: str                      # Exact grounded quote span
    attribution_role: AttributionRole
    relevance_score: float = 1.0


class NarrativeStep(BaseModel):
    """
    A single structured reasoning step in the explanation narrative,
    strictly corresponding to a node in the Layer 6 reasoning DAG.
    """
    step_index: int
    node_id: str
    step_type: str                           # e.g., "PREMISE_LEAF", "MULTI_HOP_DEDUCTION"
    headline: str
    narrative_text: str
    premise_node_ids: List[str] = []
    cited_evidence_ids: List[str] = []
    citation_tokens: List[str] = []
    epistemic_qualifier: str = "ESTABLISHED" # e.g. "ESTABLISHED", "INFERRED", "CONDITIONAL"


class ClaimExplanation(BaseModel):
    """
    Comprehensive explanation for an individual synthesized claim.
    """
    claim_id: str
    statement: str
    why_this_claim: str
    supporting_evidence_ids: List[str] = []
    opposing_evidence_ids: List[str] = []
    citation_tokens: List[str] = []
    reasoning_path_summary: str
    trust_explanation: str
    uncertainty_explanation: str
    counterfactual_sensitivity: str
    limitations: List[str] = []


class ConflictExplanation(BaseModel):
    """
    Dual-perspective explanation of an empirical conflict adhering to Zero Winner Forcing.
    """
    conflict_id: str
    claim_a: str
    claim_b: str
    thesis_explanation: str
    antithesis_explanation: str
    contextual_distinction: str
    resolution_status: str                   # e.g., "TEMPORAL_SUPERSEDENCE", "CONTEXTUAL_DIFFERENCE", "UNRESOLVED"
    why_no_winner_forced: str
    aspect: Optional[str] = None
    thesis_statement: Optional[str] = None
    antithesis_statement: Optional[str] = None
    thesis_evidence_id: Optional[str] = None
    antithesis_evidence_id: Optional[str] = None
    contextual_divergence_explanation: Optional[str] = None
    thesis_source_title: Optional[str] = None
    antithesis_source_title: Optional[str] = None


class CounterfactualExplanation(BaseModel):
    """
    Describes the structural effect of perturbing or removing an evidence dependency
    from Cogent's explicit reasoning graph.
    """
    claim_id: str
    critical_premises: List[str]
    critical_evidence_ids: List[str]
    perturbation_condition: str              # e.g., "If Evidence E1 were removed or shown invalid..."
    expected_structural_effect: str          # e.g., "The intermediate inference IC1 would lose support, weakening the final claim."
    sensitivity_severity: SensitivitySeverity


class MultiFidelityNarrative(BaseModel):
    """
    Multi-audience narratives generated from identical epistemic facts.
    """
    executive_summary: str                   # Bottom-line upfront, key bullet takeaways, strategic caveats
    researcher_narrative: str                # Full deductive steps, methodological caveats, trade-off matrix
    layperson_narrative: str                 # Intuitive analogies, clear prose, minimal jargon
    domain_expert_narrative: str             # High technical density, precision metrics, empirical qualifications


class ExplanationValidation(BaseModel):
    """
    Results of the 6-Gate Programmatic Integrity Audit.
    """
    is_faithful: bool
    fidelity_status: ExplanationFidelityStatus
    unsupported_claims: List[str] = []
    citation_mismatches: List[str] = []
    reasoning_mismatches: List[str] = []
    confidence_hedging_mismatches: List[str] = []
    conflict_omissions: List[str] = []
    topological_inversions: List[str] = []
    validation_score: float                  # [0.0, 1.0]
    validation_summary: str


class ExplanationPackage(BaseModel):
    """
    The master output contract of Layer 8 passed to Layer 9.
    """
    explanation_id: str
    session_id: str
    plan_id: str
    reasoning_trace_id: str
    trust_assessment_id: str
    primary_audience: ExplanationAudience
    narrative_steps: List[NarrativeStep]     # DAG structural correspondence
    multi_fidelity: MultiFidelityNarrative
    claim_explanations: List[ClaimExplanation]
    evidence_attributions: List[EvidenceAttribution]
    citation_map: Dict[str, EvidenceAttribution]
    conflict_explanations: List[ConflictExplanation]
    uncertainty_narrative: str
    counterfactual_explanations: List[CounterfactualExplanation]
    limitations: List[str]
    validation: ExplanationValidation
    generated_at: str
    processing_time_ms: float


class Layer8DirectRequest(BaseModel):
    """
    Direct API request payload for Layer 8.
    """
    reasoning_trace: Dict[str, Any]
    trust_assessment: Dict[str, Any]
    evidence_set: Dict[str, Any]
    audience: Optional[ExplanationAudience] = ExplanationAudience.TECHNICAL_RESEARCHER
    user_context: Optional[Dict[str, Any]] = None


class Layer8Response(BaseModel):
    """
    Direct API response payload from Layer 8.
    """
    status: str
    explanation_package: ExplanationPackage
    message: str = "Explanation package successfully synthesized and validated."
