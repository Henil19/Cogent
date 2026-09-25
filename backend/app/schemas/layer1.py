"""
Layer 1 Pydantic Schemas
Contracts for User Interaction Module inputs, outputs, and intermediate states.
Research basis:
- CLAMBER (ACL 2024): 5-type ambiguity taxonomy
- IntentSim (NAACL 2025): sufficiency and utility gating
- ASK (ACL 2025): aspect-based clarification
- SpeakRL (arXiv 2025): ask-vs-act round balance
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class IntentCategory(str, Enum):
    FACTUAL = "factual"
    COMPARATIVE = "comparative"
    EXPLORATORY = "exploratory"
    PROCEDURAL = "procedural"
    SYNTHESIS = "synthesis"
    VERIFICATION = "verification"
    OPINION_SEEKING = "opinion_seeking"
    UNKNOWN = "unknown"


class QueryTypeCategory(str, Enum):
    SINGLE_HOP = "single_hop"
    MULTI_HOP = "multi_hop"
    SYNTHESIS = "synthesis"
    HYPOTHESIS_TESTING = "hypothesis_testing"


class Layer1Status(str, Enum):
    SUFFICIENT_PROCEED = "SUFFICIENT_PROCEED"
    CLARIFICATION_NEEDED = "CLARIFICATION_NEEDED"
    MAX_CLARIFICATION_PROCEED = "MAX_CLARIFICATION_PROCEED"
    REJECTED_INVALID = "REJECTED_INVALID"


class Layer1Request(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000, description="Raw user query or research request")
    conversation_id: Optional[str] = Field(None, description="Optional conversation UUID for multi-turn sessions")
    clarification_response: Optional[str] = Field(None, description="User answer to previous clarification questions")


class AmbiguityReport(BaseModel):
    overall_ambiguity_score: float = Field(..., ge=0.0, le=1.0, description="Aggregate ambiguity 0.0=unambiguous to 1.0=fully ambiguous")
    ambiguity_types: Dict[str, float] = Field(
        default_factory=lambda: {
            "lexical": 0.0,
            "syntactic": 0.0,
            "semantic": 0.0,
            "pragmatic": 0.0,
            "vagueness": 0.0,
        },
        description="CLAMBER 5-type taxonomy scores"
    )
    primary_ambiguity_type: Optional[str] = None
    missing_elements: List[str] = Field(default_factory=list, description="Missing essential query facets (scope, timeframe, target, etc.)")
    completeness_score: float = Field(1.0, ge=0.0, le=1.0, description="Completeness of query components (0.0 to 1.0)")
    coherence_score: float = Field(1.0, ge=0.0, le=1.0, description="Logical and temporal coherence (0.0 to 1.0)")
    ambiguity_details: str = Field("", description="Diagnostic explanation of ambiguity")


class SufficiencyReport(BaseModel):
    is_sufficient: bool = Field(..., description="Whether the query contains sufficient detail to proceed to Layer 2")
    sufficiency_score: float = Field(..., ge=0.0, le=1.0, description="Sufficiency confidence score")
    uncertainty_score: float = Field(..., ge=0.0, le=1.0, description="Calibrated entropy / uncertainty")
    decision_reason: str = Field(..., description="Explanation of gate decision")


class ClarificationPlan(BaseModel):
    needs_clarification: bool = False
    round_number: int = Field(0, description="Current clarification round (max 2)")
    clarification_questions: List[str] = Field(default_factory=list, description="Targeted clarification questions")
    aspects_to_clarify: List[str] = Field(default_factory=list, description="Aspects needing clarification per ASK framework")
    suggested_options: List[str] = Field(default_factory=list, description="Concrete selectable choices for the user")

    @property
    def question(self) -> Optional[str]:
        return self.clarification_questions[0] if self.clarification_questions else None

    @property
    def target_aspect(self) -> Optional[str]:
        return self.aspects_to_clarify[0] if self.aspects_to_clarify else None

    @property
    def options(self) -> List[str]:
        return self.suggested_options


class Layer1Response(BaseModel):
    status: Layer1Status
    original_query: str
    processed_query: str
    conversation_id: str
    turn_number: int = 1
    intent: IntentCategory = IntentCategory.UNKNOWN
    query_type: QueryTypeCategory = QueryTypeCategory.SINGLE_HOP
    entities: List[str] = Field(default_factory=list)
    key_concepts: List[str] = Field(default_factory=list)
    ambiguity: AmbiguityReport
    sufficiency: SufficiencyReport
    clarification: Optional[ClarificationPlan] = None
    contract_for_layer2: Optional[Dict[str, Any]] = Field(
        None, description="Standardized contract payload passed to Layer 2 (Query Understanding)"
    )
    processing_time_ms: float = Field(..., description="Execution time in milliseconds")


class StructuredUserInput(BaseModel):
    """
    Standardized typed contract outputted by Layer 1 (Sub-Module 1.7)
    and consumed directly by Layer 2 (Query Understanding Layer).
    """
    original_query: str
    processed_query: str
    resolved_query: str
    intent: IntentCategory
    query_type: QueryTypeCategory
    entities: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    conversation_context: Dict[str, Any] = Field(default_factory=dict)
    session_id: str
    turn_number: int
    ambiguity_report: AmbiguityReport
    sufficiency_score: float
    interpretation_entropy: Optional[float] = None
    clarification_history: List[Dict[str, Any]] = Field(default_factory=list)
    was_clarified: bool = False
    clarification_rounds: int = 0
    proceed_mode: str = "STANDARD"
    preprocessing_time_ms: float

