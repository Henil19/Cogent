"""
Cogent Master Orchestration Contracts
Typed request/response models and execution metrics for the unified 10-layer cognitive pipeline.
"""

from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.schemas.layer2 import SourceTarget
from app.schemas.layer3 import AcquiredCorpusBatch
from app.schemas.layer8 import ExplanationAudience
from app.schemas.layer9 import UnifiedResponsePayload


class PipelineStatus(str, Enum):
    """Execution status for the Cogent master cognitive pipeline."""
    SUCCESS = "SUCCESS"
    CLARIFICATION_REQUIRED = "CLARIFICATION_REQUIRED"
    INSUFFICIENT_EVIDENCE_QUALIFIED = "INSUFFICIENT_EVIDENCE_QUALIFIED"
    ERROR = "ERROR"


class ExecutionMetrics(BaseModel):
    """Correlated performance and quality metrics across the 10-layer pipeline."""
    total_duration_ms: float = Field(0.0, description="Total pipeline execution latency in milliseconds")
    layer_durations_ms: Dict[int, float] = Field(default_factory=dict, description="Latency breakdown per layer")
    global_trust_index: Optional[float] = Field(None, description="Layer 7 Global Trust Index (GTI)")
    calibrated_confidence: Optional[float] = Field(None, description="Layer 7 claim-level confidence")
    grounding_score: Optional[float] = Field(None, description="Layer 10 post-hoc empirical grounding score")
    candidates_retrieved: int = Field(0, description="Count of Layer 4 retrieved candidate passages")
    evidence_selected: int = Field(0, description="Count of Layer 5 verified non-redundant evidence items")
    claims_synthesized: int = Field(0, description="Count of Layer 6 deductive claims")
    citation_badges_count: int = Field(0, description="Count of Layer 9 rendered interactive citations")


class CogentQueryRequest(BaseModel):
    """Master request payload for executing a full Cogent cognitive inquiry."""
    query: str = Field(..., min_length=1, max_length=2000, description="User research question or natural language query")
    session_id: Optional[str] = Field(None, description="Optional conversation session ID for context continuity")
    target_audience: ExplanationAudience = Field(
        ExplanationAudience.EXECUTIVE,
        description="Multi-fidelity explanation audience: TECHNICAL_RESEARCHER, EXECUTIVE, LAYPERSON, DOMAIN_EXPERT"
    )
    retrieval_target: SourceTarget = Field(
        SourceTarget.HYBRID,
        description="Retrieval source preference: HYBRID, LOCAL_DOCS, LIVE_WEB"
    )
    max_evidence_count: int = Field(
        10, ge=1, le=50,
        description="Maximum verified evidence items selected for reasoning"
    )
    user_id: Optional[str] = Field(None, description="Optional user ID for personalization/logging")
    corpus_batch: Optional[AcquiredCorpusBatch] = Field(
        None,
        description="Optional pre-acquired or local document corpus batch for retrieval"
    )
    ablation_mode: Optional[str] = Field(
        None,
        description="Optional ablation mode: no_l5, no_l6, no_l7, no_l8, dense_only, sparse_only"
    )
    clarification_responses: Optional[Dict[str, str]] = Field(
        None,
        description="Key-value mapping of clarification question IDs or indices to user responses"
    )
    clarification_response: Optional[str] = Field(
        None,
        description="Direct natural language string response to a previous clarification question"
    )


class CogentQueryResponse(BaseModel):
    """Unified response envelope returned by the Cogent master orchestrator."""
    api_version: str = Field("v1", description="API contract version")
    schema_version: str = Field("1.0.0", description="Envelope schema version")
    execution_id: str = Field(..., description="Globally unique execution trace UUID")
    session_id: Optional[str] = Field(None, description="Active research session ID")
    status: PipelineStatus = Field(..., description="Final pipeline execution outcome")
    unified_response: Optional[UnifiedResponsePayload] = Field(
        None,
        description="Presentation-ready Layer 9 response payload (present when status is SUCCESS or INSUFFICIENT_EVIDENCE_QUALIFIED)"
    )
    retrieved_chunk_ids: List[str] = Field(
        default_factory=list,
        description="IDs of retrieved evidence chunks"
    )
    clarification_prompt: Optional[Dict[str, Any]] = Field(
        None,
        description="Targeted clarification questions if status is CLARIFICATION_REQUIRED"
    )
    metrics: ExecutionMetrics = Field(
        default_factory=ExecutionMetrics,
        description="High-resolution execution telemetry and trust metrics"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Non-fatal warning notices accumulated along the pipeline"
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO 8601 response creation timestamp"
    )
