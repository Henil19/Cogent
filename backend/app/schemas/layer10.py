"""
Cogent Layer 10: Analytics, Telemetry & Continuous Learning Layer Schemas
Contracts for execution tracing, user feedback attribution, multi-gate evaluation,
calibration drift monitoring, evidence-backed failure diagnosis, adaptive policy
optimization, curated preference dataset synthesis, and A/B experimentation.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Telemetry & Execution Tracing Contracts (BERGEN, EMNLP 2024)
# ---------------------------------------------------------------------------

class TelemetryPacket(BaseModel):
    """Micro-telemetry unit emitted by any layer or sub-engine."""
    packet_id: str = Field(default_factory=lambda: f"pkt_{datetime.now(timezone.utc).timestamp()}")
    execution_id: str
    layer_id: int = Field(ge=1, le=9)
    component_name: str
    event_type: str
    duration_ms: float
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metrics: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LayerExecutionSummary(BaseModel):
    """Consolidated performance snapshot per layer."""
    layer_id: int
    layer_name: str
    status: str = "SUCCESS"
    duration_ms: float = 0.0
    token_usage: int = 0
    sub_component_latencies: Dict[str, float] = Field(default_factory=dict)
    key_metrics: Dict[str, Any] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class CogentExecutionTrace(BaseModel):
    """
    Master container holding full execution context, configuration versions,
    layer artifacts, and telemetry across Layers 1 through 9.
    """
    execution_id: str
    session_id: str
    query_id: str
    raw_query: str
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    total_latency_ms: float = 0.0

    # Decoupled Configuration & Version Hashing (BERGEN)
    config_hash: str = "default_config_hash"
    model_versions: Dict[str, str] = Field(default_factory=lambda: {"llm": "gemini-2.5-flash", "embedder": "mock-dense-384"})
    prompt_versions: Dict[str, str] = Field(default_factory=dict)
    pipeline_parameters: Dict[str, Any] = Field(default_factory=dict)

    # Per-layer execution records
    layer_summaries: Dict[int, LayerExecutionSummary] = Field(default_factory=dict)
    telemetry_packets: List[TelemetryPacket] = Field(default_factory=list)

    # Core artifacts captured from the execution pipeline
    layer1_input: Optional[Dict[str, Any]] = None
    layer2_plan: Optional[Dict[str, Any]] = None
    layer3_corpus_meta: Optional[Dict[str, Any]] = None
    layer4_retrieval_meta: Optional[Dict[str, Any]] = None
    layer5_evidence_meta: Optional[Dict[str, Any]] = None
    layer6_reasoning_meta: Optional[Dict[str, Any]] = None
    layer7_trust_meta: Optional[Dict[str, Any]] = None
    layer8_explanation_meta: Optional[Dict[str, Any]] = None
    layer9_response_payload: Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# 2. User Feedback & Attribution Contracts (Park et al., Thakur et al.)
# ---------------------------------------------------------------------------

class FeedbackType(str, Enum):
    # Explicit User Ratings
    THUMBS_UP = "THUMBS_UP"
    THUMBS_DOWN = "THUMBS_DOWN"
    CLAIM_FLAG = "CLAIM_FLAG"
    FACT_CORRECTION = "FACT_CORRECTION"
    SECTION_RATING = "SECTION_RATING"
    FREEFORM_CRITIQUE = "FREEFORM_CRITIQUE"

    # Implicit Behavioral Signals
    CITATION_CLICK = "CITATION_CLICK"
    CITATION_HOVER = "CITATION_HOVER"
    DAG_NODE_INSPECT = "DAG_NODE_INSPECT"
    COUNTERFACTUAL_DRAG = "COUNTERFACTUAL_DRAG"
    AUDIENCE_TAB_SWITCH = "AUDIENCE_TAB_SWITCH"
    EXPORT_CLICK = "EXPORT_CLICK"
    REGENERATION_REQUEST = "REGENERATION_REQUEST"


class UserFeedbackPayload(BaseModel):
    """
    Structured feedback payload attributing user behavior backwards
    down through presentation to claims, reasoning steps, and evidence.
    """
    feedback_id: str = Field(default_factory=lambda: f"fb_{datetime.now(timezone.utc).timestamp()}")
    execution_id: str
    feedback_type: FeedbackType
    value: Any = None  # Rating float, thumbs boolean, or correction string
    user_comment: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Backward Attribution Pointers
    target_section_id: Optional[str] = None
    target_claim_id: Optional[str] = None
    target_citation_number: Optional[int] = None
    target_evidence_id: Optional[str] = None
    target_reasoning_step_id: Optional[str] = None
    target_document_uri: Optional[str] = None


# ---------------------------------------------------------------------------
# 3. Post-Hoc Multi-Gate Evaluation Contracts (RAGEval, GaRAGe, GroUSE)
# ---------------------------------------------------------------------------

class EvaluationMetricsReport(BaseModel):
    """
    Multi-gate factual, structural, and alignment evaluation report.
    Guarded against verbosity bias (Park et al.) and ungrounded extrapolation.
    """
    report_id: str = Field(default_factory=lambda: f"eval_{datetime.now(timezone.utc).timestamp()}")
    execution_id: str
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # 1. RAGEval Tri-Metrics (Zhu et al., ACL 2025)
    completeness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    hallucination_score: float = Field(default=0.0, ge=0.0, le=1.0)
    irrelevance_score: float = Field(default=0.0, ge=0.0, le=1.0)

    # 2. GaRAGe Human-Aligned Grounding & Citation Metrics (Muller et al., ACL 2025)
    grounding_score: float = Field(default=1.0, ge=0.0, le=1.0)
    citation_precision: float = Field(default=1.0, ge=0.0, le=1.0)
    citation_coverage: float = Field(default=1.0, ge=0.0, le=1.0)

    # 3. Structural Reasoning & Dialectical Verification
    reasoning_soundness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    dialectical_balance_score: float = Field(default=1.0, ge=0.0, le=1.0)

    # 4. Length-Regularized Quality (Park et al., ACL 2024)
    # Penalizes verbose fluff; ensures Quality != Length
    length_regularized_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)

    # 5. Abstention / Unanswerability Quality (GaRAGe / Epistemic Gaps)
    # Measures whether Cogent correctly abstained when evidence was insufficient
    abstention_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)

    # Composite System Score
    composite_quality_score: float = Field(default=1.0, ge=0.0, le=1.0)
    is_high_quality_gold_candidate: bool = True
    evaluation_notes: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# 4. Trust & Calibration Drift Monitoring (SGIC, ACL 2025)
# ---------------------------------------------------------------------------

class CalibrationBin(BaseModel):
    """Reliability diagram confidence interval bin."""
    bin_index: int
    confidence_lower: float
    confidence_upper: float
    average_confidence: float
    empirical_accuracy: float
    sample_count: int


class CalibrationDriftReport(BaseModel):
    """
    Rolling calibration health assessment comparing empirical accuracy
    against predicted confidence to detect overconfidence / underconfidence drift.
    """
    report_id: str = Field(default_factory=lambda: f"cal_{datetime.now(timezone.utc).timestamp()}")
    evaluation_window_size: int
    sample_count: int
    evaluated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    ece: float = Field(ge=0.0, le=1.0, description="Expected Calibration Error")
    brier_score: float = Field(ge=0.0, le=1.0, description="Mean squared probability error")

    baseline_ece: float = 0.08
    drift_threshold: float = Field(default=0.12, description="Configurable experimental drift parameter")
    drift_detected: bool = False

    overconfidence_gap: float = 0.0
    underconfidence_gap: float = 0.0
    reliability_bins: List[CalibrationBin] = Field(default_factory=list)

    recommended_temperature: Optional[float] = None
    calibration_status: str = "CALIBRATED"


# ---------------------------------------------------------------------------
# 5. Evidence-Based Root Cause Failure Diagnosis (GroUSE, Li et al.)
# ---------------------------------------------------------------------------

class FailureCategory(str, Enum):
    NO_FAILURE_DETECTED = "NO_FAILURE_DETECTED"
    L1_AMBIGUITY_MISCLASSIFICATION = "L1_AMBIGUITY_MISCLASSIFICATION"
    L2_DECOMPOSITION_FAILURE = "L2_DECOMPOSITION_FAILURE"
    L3_ACQUISITION_EXTRACTION_FAILURE = "L3_ACQUISITION_EXTRACTION_FAILURE"
    L4_RETRIEVAL_MISS = "L4_RETRIEVAL_MISS"
    L5_VERIFICATION_SELECTION_GAP = "L5_VERIFICATION_SELECTION_GAP"
    L6_REASONING_DEDUCTION_GAP = "L6_REASONING_DEDUCTION_GAP"
    L7_TRUST_MISCALIBRATION = "L7_TRUST_MISCALIBRATION"
    L8_EXPLANATION_FIDELITY_FAILURE = "L8_EXPLANATION_FIDELITY_FAILURE"
    L9_PRESENTATION_INVARIANCE_FAILURE = "L9_PRESENTATION_INVARIANCE_FAILURE"


class FailureSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RootCauseDiagnosis(BaseModel):
    """
    Evidence-backed root cause report identifying exactly where and why
    an execution failed across the 9-layer cognitive stack.
    """
    diagnosis_id: str = Field(default_factory=lambda: f"diag_{datetime.now(timezone.utc).timestamp()}")
    execution_id: str
    failed_layer_id: Optional[int] = None
    failure_category: FailureCategory = FailureCategory.NO_FAILURE_DETECTED
    severity: FailureSeverity = FailureSeverity.LOW
    root_cause_explanation: str
    evidence_ids: List[str] = Field(default_factory=list)
    contributing_factors: List[str] = Field(default_factory=list)
    recommended_action: str
    diagnosed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# 6. Adaptive Policy & Optimization Engine (BERGEN, EMNLP 2024)
# ---------------------------------------------------------------------------

class LearningSignalType(str, Enum):
    L2_ROUTING_OPTIMIZATION = "L2_ROUTING_OPTIMIZATION"
    L4_RETRIEVAL_POLICY_ADAPTATION = "L4_RETRIEVAL_POLICY_ADAPTATION"
    L5_CONTRADICTION_PATTERN_CAPTURE = "L5_CONTRADICTION_PATTERN_CAPTURE"
    L7_CALIBRATION_REWEIGHTING = "L7_CALIBRATION_REWEIGHTING"
    L8_L9_PRESENTATION_POLICY_ADAPTATION = "L8_L9_PRESENTATION_POLICY_ADAPTATION"


class LearningSignal(BaseModel):
    """
    Controlled learning proposal emitted by Layer 10 to inform future configurations.
    Does not apply immediate base model fine-tuning; undergoes offline validation.
    """
    signal_id: str = Field(default_factory=lambda: f"sig_{datetime.now(timezone.utc).timestamp()}")
    source_execution_ids: List[str] = Field(default_factory=list)
    target_layer: int = Field(ge=1, le=9)
    target_component: str
    signal_type: LearningSignalType
    observed_pattern: str
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)
    recommended_change: Dict[str, Any] = Field(default_factory=dict)
    validation_status: str = "PENDING_OFFLINE_VALIDATION"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# 7. Curated Dataset & Preference Synthesis (IUPO, DJPO, Park et al.)
# ---------------------------------------------------------------------------

class DPOPreferencePair(BaseModel):
    """
    Direct Preference Optimization record with strict verbosity regularization.
    Guarantees chosen response is rewarded for grounding, not fluff.
    """
    pair_id: str = Field(default_factory=lambda: f"dpo_{datetime.now(timezone.utc).timestamp()}")
    prompt: str
    chosen_response: str
    rejected_response: str
    rationale: str
    length_ratio: float = 1.0
    verbosity_controlled: bool = True
    grounding_delta: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class RegressionTestCase(BaseModel):
    """Automated regression test generated from historically difficult or failing queries."""
    test_id: str = Field(default_factory=lambda: f"reg_{datetime.now(timezone.utc).timestamp()}")
    query: str
    expected_intent: str
    required_evidence_substrs: List[str] = Field(default_factory=list)
    forbidden_hallucinations: List[str] = Field(default_factory=list)
    minimum_grounding_score: float = 0.85
    created_from_execution_id: str


class DatasetCuratorExport(BaseModel):
    """Curated bundle of ML alignment and regression datasets."""
    export_id: str = Field(default_factory=lambda: f"exp_{datetime.now(timezone.utc).timestamp()}")
    gold_records_count: int = 0
    dpo_pairs: List[DPOPreferencePair] = Field(default_factory=list)
    regression_tests: List[RegressionTestCase] = Field(default_factory=list)
    exported_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# 8. Experimentation & Analytics Hub Contracts (BERGEN, MEMERAG)
# ---------------------------------------------------------------------------

class ExperimentRun(BaseModel):
    """A/B configuration experiment run metadata and delta scores."""
    experiment_id: str = Field(default_factory=lambda: f"exp_run_{datetime.now(timezone.utc).timestamp()}")
    experiment_name: str
    baseline_config_hash: str
    candidate_config_hash: str
    sample_queries_count: int
    baseline_composite_score: float
    candidate_composite_score: float
    grounding_delta: float
    latency_delta_ms: float
    is_candidate_statistically_superior: bool
    status: str = "COMPLETED"
    run_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class Layer10AnalyticsOverview(BaseModel):
    """Executive analytics overview for system monitoring."""
    total_executions: int = 0
    mean_grounding_score: float = 0.0
    mean_citation_precision: float = 0.0
    mean_latency_ms: float = 0.0
    current_ece: float = 0.0
    calibration_status: str = "HEALTHY"
    active_learning_signals_count: int = 0
    curated_dpo_pairs_count: int = 0
    top_failure_categories: Dict[str, int] = Field(default_factory=dict)
    reported_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# 9. FastAPI Request & Response Contracts
# ---------------------------------------------------------------------------

class Layer10DirectRequest(BaseModel):
    """Direct invocation of Layer 10 pipeline on an execution trace."""
    execution_trace: CogentExecutionTrace
    include_failure_diagnosis: bool = True
    include_evaluation: bool = True
    include_learning_signals: bool = True


class Layer10Response(BaseModel):
    """Master response contract emitted by Layer 10."""
    status: str = "SUCCESS"
    execution_id: str
    evaluation_report: Optional[EvaluationMetricsReport] = None
    calibration_report: Optional[CalibrationDriftReport] = None
    failure_diagnosis: Optional[RootCauseDiagnosis] = None
    learning_signals: List[LearningSignal] = Field(default_factory=list)
    processed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
