"""
Layer 9 Pydantic Schemas: Response Generation & Presentation Layer
Standardized typed contracts for the final response assembly, citation registry,
trust visualization badges, dialectical conflict widgets, reasoning DAG explorer UI,
counterfactual simulation controls, multi-fidelity views, and safety validation.
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field

from app.schemas.layer1 import StructuredUserInput
from app.schemas.layer2 import KnowledgeRetrievalPlan
from app.schemas.layer5 import VerifiedEvidenceSet
from app.schemas.layer6 import SynthesizedReasoningTrace
from app.schemas.layer7 import TrustAssessment, ConfidenceTier
from app.schemas.layer8 import (
    ExplanationAudience,
    ExplanationPackage,
    AttributionRole,
    SensitivitySeverity
)


class PresentationFormat(str, Enum):
    """Supported output formats for response serialization."""
    MARKDOWN = "MARKDOWN"
    HTML = "HTML"
    JSON = "JSON"
    PDF_SEMANTIC = "PDF_SEMANTIC"


class ResponseSectionType(str, Enum):
    """Categorization of structured response sections."""
    BLUF_SUMMARY = "BLUF_SUMMARY"
    KEY_FINDINGS = "KEY_FINDINGS"
    DETAILED_REASONING = "DETAILED_REASONING"
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"
    UNCERTAINTY_CAVEATS = "UNCERTAINTY_CAVEATS"
    SENSITIVITY_ANALYSIS = "SENSITIVITY_ANALYSIS"
    REFERENCES_FOOTNOTES = "REFERENCES_FOOTNOTES"


class RenderedSection(BaseModel):
    """Structured section within the rendered document."""
    section_id: str = Field(..., description="Unique section identifier, e.g. sec_bluf")
    section_title: str = Field(..., description="Display title for the section")
    section_type: ResponseSectionType = Field(..., description="Semantic category of section")
    content_markdown: str = Field(..., description="Rendered markdown text for this section")
    referenced_claim_ids: List[str] = Field(default_factory=list, description="IDs of claims addressed in this section")
    citation_badges: List[int] = Field(default_factory=list, description="Sequential citation numbers present in this section")


class CitationBadgeEntry(BaseModel):
    """
    Presentation-ready citation metadata resolving an internal token [C{i}-E{j}]
    into an interactive, clickable footnote or hovercard.
    Research: MIRAGE (EMNLP 2024), CiteBench (ACL 2025).
    """
    citation_number: int = Field(..., description="Display badge number, e.g. 1 for [1]")
    internal_token: str = Field(..., description="Internal upstream token, e.g. [C1-E1]")
    claim_id: str = Field(..., description="Target claim supported by this citation")
    evidence_id: str = Field(..., description="Layer 5 EvidenceItem ID")
    
    # Document Provenance
    document_id: str = Field(..., description="Origin document ID")
    source_title: str = Field(..., description="Title of the source document or paper")
    author: Optional[str] = Field(None, description="Author string if available")
    publication_date: Optional[str] = Field(None, description="Publication date or year")
    source_uri: str = Field(..., description="URL or local path to source")
    source_type: str = Field(..., description="Source classification tier, e.g. PEER_REVIEWED_PAPER")
    
    # Precise Coordinate Grounding
    page_number: Optional[int] = Field(None, description="Page number in origin document")
    section_title: Optional[str] = Field(None, description="Section heading in origin document")
    paragraph_start: Optional[int] = Field(None, description="Starting paragraph index")
    paragraph_end: Optional[int] = Field(None, description="Ending paragraph index")
    quoted_snippet: str = Field(..., description="Verbatim extracted quote from the source")
    attribution_role: AttributionRole = Field(..., description="Role in deduction: DIRECT_SUPPORT, etc.")


class TrustBadgePayload(BaseModel):
    """
    Visual trust presentation data structure for frontend badge rendering.
    Strictly pairs numeric confidence with tier labels to avoid misleading probability overclaims.
    Research: Towards Trustworthy RAG (ACM CSUR 2026).
    """
    confidence_tier: ConfidenceTier = Field(..., description="Calibrated tier: HIGH, MODERATE, LOW, PROVISIONAL")
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated confidence probability")
    trust_index: float = Field(..., ge=0.0, le=1.0, description="Structural Trust Index (Trust != Probability)")
    risk_level: str = Field("LOW", description="Overall risk level: LOW, MEDIUM, HIGH, CRITICAL")
    is_safe_for_decision_support: bool = Field(True, description="True if safe for decision support")
    
    # Uncertainty Dimensions
    uncertainty_breakdown: Dict[str, float] = Field(
        default_factory=dict,
        description="5 separate uncertainty components: coverage, conflict, source, reasoning, temporal"
    )
    dominant_uncertainty: str = Field(..., description="Primary uncertainty driver, e.g. CONFLICTING_EVIDENCE")
    key_caveats: List[str] = Field(default_factory=list, description="Essential epistemic hedges and limits")
    disclaimer_text: str = Field(
        ...,
        description="Standardized epistemic disclaimer clarifying metric interpretation"
    )


class ConflictWidgetPayload(BaseModel):
    """
    Presentation contract for side-by-side dialectical contradiction display.
    Enforces Zero Winner Forcing in the UI.
    Research: ConfRAG (ACL 2026), DeYoung et al. (TACL 2024).
    """
    conflict_id: str = Field(..., description="Unique conflict reconciliation ID")
    aspect: str = Field(..., description="Aspect or metric of disagreement, e.g. Benchmark Accuracy")
    
    # Thesis
    thesis_statement: str = Field(..., description="First viewpoint claim statement")
    thesis_evidence_ids: List[str] = Field(default_factory=list)
    thesis_citation_badges: List[int] = Field(default_factory=list)
    thesis_source_title: str = Field(..., description="Primary source title supporting thesis")
    
    # Antithesis
    antithesis_statement: str = Field(..., description="Opposing viewpoint claim statement")
    antithesis_evidence_ids: List[str] = Field(default_factory=list)
    antithesis_citation_badges: List[int] = Field(default_factory=list)
    antithesis_source_title: str = Field(..., description="Primary source title supporting antithesis")
    
    # Reconciliation Analysis
    contextual_divergence_explanation: str = Field(..., description="Explanation of differing conditions causing divergence")
    resolution_status: str = Field(..., description="Resolution status: CONTEXTUAL_DIFFERENCE, UNRESOLVED, etc.")


class DAGNodeUI(BaseModel):
    """UI node representation for canvas graph renderers (React Flow, D3)."""
    id: str = Field(..., description="ReasoningStepNode ID, e.g. step_01")
    label: str = Field(..., description="Human-readable summary label")
    step_type: str = Field(..., description="Operation type, e.g. MULTI_HOP_INFERENCE")
    intermediate_claim: str = Field(..., description="Synthesized claim or proposition")
    grounding_score: float = Field(1.0, ge=0.0, le=1.0, description="Premise grounding score")
    is_weakest_link: bool = Field(False, description="True if flagged as weakest-link step")
    citation_badges: List[int] = Field(default_factory=list, description="Citations supporting this step")


class DAGEdgeUI(BaseModel):
    """Directed inferential dependency edge for graph visualization."""
    source: str = Field(..., description="Upstream premise node ID")
    target: str = Field(..., description="Downstream deduction node ID")
    label: Optional[str] = Field(None, description="Edge relation label, e.g. entails")


class ReasoningGraphUIPayload(BaseModel):
    """Complete reasoning graph UI contract for interactive tree/DAG exploration."""
    nodes: List[DAGNodeUI] = Field(default_factory=list)
    edges: List[DAGEdgeUI] = Field(default_factory=list)
    root_claim_ids: List[str] = Field(default_factory=list, description="Final synthesized conclusion step IDs")
    leaf_evidence_ids: List[str] = Field(default_factory=list, description="Direct evidence anchor step IDs")
    weakest_link_step_id: Optional[str] = Field(None, description="ID of bottleneck step")


class CounterfactualControlPayload(BaseModel):
    """Interactive premise sensitivity simulation control for frontend toggles."""
    premise_id: str = Field(..., description="Premise or reasoning step ID")
    label: str = Field(..., description="Human-interpretable premise toggle label")
    perturbation_condition: str = Field(..., description="Condition statement: If X were removed/invalidated")
    structural_impact_description: str = Field(..., description="Grounded structural impact on Cogent's deduction chain")
    sensitivity_severity: SensitivitySeverity = Field(..., description="Impact tier: CRITICAL_COLLAPSE, etc.")
    affected_claim_ids: List[str] = Field(default_factory=list)


class MultiFidelityViewsPayload(BaseModel):
    """
    Bundled pre-rendered text views across all 4 audience modes.
    Guarantees Epistemic Invariance during instantaneous client-side tab switching.
    """
    executive: str = Field(..., description="BLUF executive summary with high-level takeaways")
    technical_researcher: str = Field(..., description="Full deductive reasoning breakdown with formal steps")
    layperson: str = Field(..., description="Accessible explanation using intuitive metaphors")
    domain_expert: str = Field(..., description="Formal methodology, bounds, and calibration metrics")


class ResponseValidationReport(BaseModel):
    """
    Lightweight post-generation safety and consistency fact-check audit.
    Research: Provenance (EMNLP 2024 Industry), RAG-Zeval (EMNLP 2025).
    """
    is_safe_for_presentation: bool = Field(True, description="True if no severe ungrounded drift is detected")
    sentence_count: int = Field(0, description="Total sentences in final rendered response")
    attributed_sentence_ratio: float = Field(1.0, ge=0.0, le=1.0, description="Ratio of sentences backed by evidence")
    unsupported_assertions: List[str] = Field(default_factory=list, description="Detected ungrounded assertions")
    orphan_citation_badges: List[int] = Field(default_factory=list, description="Citations missing from registry")
    tone_policy_violations: List[str] = Field(default_factory=list, description="Overconfident phrasing violations")
    validation_score: float = Field(1.0, ge=0.0, le=1.0, description="Overall presentation safety score")


class UnifiedResponsePayload(BaseModel):
    """
    Master Output Contract emitted by Layer 9 and consumed by Frontend client and Layer 10.
    """
    response_id: str = Field(..., description="Unique response UUID")
    session_id: str = Field(..., description="User session UUID")
    plan_id: str = Field(..., description="Layer 2 KnowledgeRetrievalPlan ID")
    query: str = Field(..., description="Original user query")
    
    # Active Presentation Metadata
    active_audience: ExplanationAudience = Field(..., description="Audience mode rendered in primary content")
    response_type: str = Field(..., description="Structural blueprint used: FACTUAL, COMPARATIVE, INSUFFICIENT, etc.")
    format: PresentationFormat = Field(PresentationFormat.MARKDOWN, description="Output presentation format")
    
    # Primary Rendered Output
    rendered_content: str = Field(..., description="Complete assembled and styled markdown/text response")
    sections: List[RenderedSection] = Field(default_factory=list, description="Structured modular sections")
    
    # Interactive UI Contracts
    citation_registry: List[CitationBadgeEntry] = Field(default_factory=list, description="Footnotes and hovercard registry")
    trust_badges: TrustBadgePayload = Field(..., description="Visual confidence and uncertainty UI cards")
    conflict_widgets: List[ConflictWidgetPayload] = Field(default_factory=list, description="Side-by-side dialectical widgets")
    reasoning_graph_ui: ReasoningGraphUIPayload = Field(..., description="Graph contract for React Flow / D3 canvas")
    counterfactual_controls: List[CounterfactualControlPayload] = Field(default_factory=list, description="Interactive premise toggles")
    multi_fidelity_views: MultiFidelityViewsPayload = Field(..., description="Pre-rendered 4-mode audience views")
    
    # Safety & Audit
    validation_report: ResponseValidationReport = Field(..., description="Post-generation fact-check and consistency report")
    presentation_metadata: Dict[str, Any] = Field(default_factory=dict, description="Rendering latency and telemetry")
    processing_time_ms: float = Field(0.0, description="Total Layer 9 processing latency in ms")
    created_at: str = Field(..., description="ISO 8601 creation timestamp")


class Layer9DirectRequest(BaseModel):
    """Typed request payload for direct Layer 9 API execution."""
    explanation_package: ExplanationPackage
    trust_assessment: TrustAssessment
    user_input: Optional[StructuredUserInput] = None
    target_audience: Optional[ExplanationAudience] = None
    presentation_format: Optional[PresentationFormat] = PresentationFormat.MARKDOWN


class Layer9Response(BaseModel):
    """API wrapper response for Layer 9."""
    success: bool = True
    payload: UnifiedResponsePayload
